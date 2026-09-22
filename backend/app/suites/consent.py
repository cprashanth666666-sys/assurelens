"""Suite 2: consent withdrawal.

Both procedures test outcomes rather than records, because this is where
privacy tooling most often fails silently. The consent store updates the
instant someone withdraws; the marketing segment refreshes overnight. The
record looks perfect and the principal keeps being marketed to, so a tool
that audits the consent table finds nothing wrong -- which is exactly how the
failure survives in production.
"""

from __future__ import annotations

from typing import Any

import httpx

from app.engine.evidence import (
    EvidenceBundle,
    EvidenceContract,
    EvidenceKind,
    EvidenceRequirement,
)
from app.engine.gate import InferenceMode, RawResult, SampleFrame, Verdict
from app.engine.runner import register

# Act s.6(6) sets no latency, so this is an engagement service level recorded
# as an assumption rather than presented as a legal requirement.
PROPAGATION_SLA_SECONDS = 300

PROPAGATED = "PROPAGATED"
LAGGED = "LAGGED"
NOT_PROPAGATED = "NOT_PROPAGATED"


@register("consent.withdrawal_propagation")
class WithdrawalPropagation:
    """Does withdrawing consent actually stop downstream processing?

    Reported as a latency distribution, not a binary. "No propagation control
    observed" is a weak finding a client can argue with; "median eleven
    hours, worst case twenty-two, on every one of 3,200 withdrawals" is not.
    """

    evidence_contract = EvidenceContract(
        required=(
            EvidenceRequirement(
                "consent_records", EvidenceKind.DB_QUERY, defines_population=True
            ),
            EvidenceRequirement("downstream_segment", EvidenceKind.HTTP_PROBE),
        ),
        max_age_days=30,
    )

    def execute(self, evidence: EvidenceBundle, config: dict[str, Any]) -> RawResult:
        records = evidence.payload("consent_records", [])
        probe = evidence.payload("downstream_segment", {}) or {}

        withdrawn = [r for r in records if r["status"] == "WITHDRAWN"]
        classified: dict[str, int] = {PROPAGATED: 0, LAGGED: 0, NOT_PROPAGATED: 0}
        latencies: list[float] = []

        for record in withdrawn:
            synced = record.get("downstream_synced_at")
            if synced is None:
                classified[NOT_PROPAGATED] += 1
                continue

            seconds = (synced - record["withdrawn_at"]).total_seconds()
            latencies.append(seconds)
            classified[LAGGED if seconds > PROPAGATION_SLA_SECONDS else PROPAGATED] += 1

        latencies.sort()
        median = latencies[len(latencies) // 2] if latencies else None
        worst = latencies[-1] if latencies else None

        # The live probe is corroboration, not the measurement: it shows the
        # downstream system's current belief about one principal, which is
        # what makes the stored latency more than an internal claim.
        live_disagreement = probe.get("still_in_segment_after_withdrawal")

        return RawResult(
            outcome=(
                Verdict.PASS
                if classified[PROPAGATED] == len(withdrawn) and withdrawn
                else Verdict.FAIL
            ),
            inference_mode=InferenceMode.POPULATION,
            sample_frame=SampleFrame.CENSUS,
            sample_size=len(withdrawn),
            population_size=len(records),
            successes=classified[PROPAGATED],
            detail={
                "withdrawals_examined": len(withdrawn),
                "classification": classified,
                "sla_seconds": PROPAGATION_SLA_SECONDS,
                "median_latency_hours": (
                    round(median / 3600, 2) if median is not None else None
                ),
                "worst_latency_hours": (
                    round(worst / 3600, 2) if worst is not None else None
                ),
                "live_probe_disagrees": live_disagreement,
                "why_outcome_not_record": (
                    "Every withdrawal is recorded correctly and promptly in the "
                    "consent store. The downstream segment refreshes on a batch, "
                    "so the record looks compliant while processing continues."
                ),
            },
        )


@register("consent.withdrawal_effort_parity")
class WithdrawalEffortParity:
    """Act s.6(6): withdrawal must be as easy as granting.

    Publishing both journeys makes an "ease" requirement testable rather than
    arguable: step count, required fields and available channels are
    countable, and a withdrawal that needs more of any of them is an
    exception nobody can debate.
    """

    evidence_contract = EvidenceContract(
        required=(
            EvidenceRequirement("grant_journey", EvidenceKind.HTTP_PROBE),
            EvidenceRequirement("withdrawal_journey", EvidenceKind.HTTP_PROBE),
        )
    )

    def execute(self, evidence: EvidenceBundle, config: dict[str, Any]) -> RawResult:
        grant = evidence.payload("grant_journey", {}) or {}
        withdraw = evidence.payload("withdrawal_journey", {}) or {}

        comparisons = [
            ("steps", grant.get("steps", 0), withdraw.get("steps", 0), "more"),
            (
                "required_fields",
                len(grant.get("required_fields", [])),
                len(withdraw.get("required_fields", [])),
                "more",
            ),
            (
                "channels",
                len(grant.get("channels", [])),
                len(withdraw.get("channels", [])),
                "fewer",
            ),
        ]

        exceptions = [
            {
                "dimension": name,
                "granting": g,
                "withdrawing": w,
                "finding": (
                    f"withdrawal requires {w} {name.replace('_', ' ')} "
                    f"against {g} for granting"
                ),
            }
            for name, g, w, direction in comparisons
            if (w > g if direction == "more" else w < g)
        ]

        return RawResult(
            outcome=Verdict.FAIL if exceptions else Verdict.PASS,
            inference_mode=InferenceMode.CENSUS,
            sample_frame=SampleFrame.CENSUS,
            sample_size=len(comparisons),
            population_size=len(comparisons),
            successes=len(comparisons) - len(exceptions),
            detail={
                "exceptions": exceptions,
                "grant_journey": grant,
                "withdrawal_journey": withdraw,
                "basis": (
                    "Act s.6(6): the right to withdraw consent at any time, "
                    "with the ease of doing so being comparable to the ease "
                    "with which consent was given."
                ),
            },
        )


# --- Probes ----------------------------------------------------------------


def probe_journey(client: httpx.Client, action: str) -> dict[str, Any]:
    response = client.get(f"/consent/journey/{action}")
    response.raise_for_status()
    return dict(response.json())


def probe_downstream(client: httpx.Client, external_ref: str) -> dict[str, Any]:
    """Withdraw consent, then ask the downstream system what it believes.

    The point is the second question. A consent endpoint returning 200 says
    the store was updated; only the segment can say whether processing
    actually stopped.
    """
    client.post("/_probe/reset")

    before = client.get(f"/marketing/segment/{external_ref}").json()
    client.post(f"/consent/{external_ref}/withdraw").raise_for_status()
    after = client.get(f"/marketing/segment/{external_ref}").json()
    consent = client.get(f"/consent/{external_ref}").json()

    return {
        "external_ref": external_ref,
        "in_segment_before": before.get("in_segment"),
        "in_segment_after": after.get("in_segment"),
        "consent_store_status": consent.get("status"),
        "still_in_segment_after_withdrawal": bool(after.get("in_segment")),
    }
