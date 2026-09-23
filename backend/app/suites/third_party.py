"""Suite 4: third-party access.

Two procedures:

* `third_party.access_posture` -- DPDP-TP-01. For every processor in the
  inventory: is there a processor agreement, are the granted scopes the ones
  actually used, is the credential current and in use, and is access gone
  where the relationship has ended.
* `retention.processor_erasure_cascade` -- DPDP-08-02. Erasure at the
  fiduciary must reach every processor that received the data.

Both read the estate only. Neither calls the target service.
"""

from __future__ import annotations

import datetime as dt
from typing import Any

from app.engine.evidence import (
    EvidenceBundle,
    EvidenceContract,
    EvidenceKind,
    EvidenceRequirement,
)
from app.engine.gate import InferenceMode, RawResult, SampleFrame, Verdict
from app.engine.runner import register
from app.engine.thresholds import Thresholds
from app.seed.generator import EPOCH

# Read from the engagement defaults rather than restated here, so the value in
# the workpaper and the value the check used cannot drift apart.
_DEFAULTS = Thresholds()
STALE_ACCESS_DAYS = _DEFAULTS.stale_access_days
MAX_CREDENTIAL_AGE_DAYS = _DEFAULTS.max_credential_age_days

HOME_JURISDICTION = "IN"

# Relative weight of each issue, used ONLY to order the processor list so the
# worst sits at the top of a client conversation. It is a sort key, not a
# score, and is never shown as a number. Live access after the relationship
# ended leads because it is access with no business purpose left at all.
ISSUE_WEIGHT = {
    "access_after_offboarding": 4,
    "no_processor_agreement": 3,
    "stale_credential": 3,
    "excess_scope": 2,
    "credential_not_rotated": 1,
}


def _age_days(moment: dt.datetime | None) -> int | None:
    # Measured against the estate's fixed epoch, not today, so the same seed
    # gives the same result next month. [Day 3 determinism]
    return None if moment is None else (EPOCH - moment).days


def assess_processor(tp: dict[str, Any]) -> dict[str, Any]:
    """Every issue on one processor, collected rather than short-circuited.

    Stopping at the first failure would under-report exactly the processor
    that matters most: EchoScribe fails four separate checks, and each one has
    a different owner and a different fix.
    """
    issues: list[dict[str, Any]] = []
    ended = tp.get("relationship_ended_at") is not None
    live = bool(tp.get("is_active"))

    if ended and live:
        issues.append({
            "check": "access_after_offboarding",
            "detail": "Relationship has ended but the credential is still active.",
        })

    if live:
        if not tp.get("dpa_reference"):
            issues.append({
                "check": "no_processor_agreement",
                "detail": "No processor agreement reference on file (Act s.8(2)).",
            })

        unused = sorted(set(tp.get("granted_scopes") or [])
                        - set(tp.get("exercised_scopes") or []))
        if unused:
            issues.append({
                "check": "excess_scope",
                "detail": f"Granted but not exercised: {', '.join(unused)}.",
                "unused_scopes": unused,
            })

        idle = _age_days(tp.get("last_used_at"))
        if idle is not None and idle > STALE_ACCESS_DAYS:
            issues.append({
                "check": "stale_credential",
                "detail": f"Unused for {idle} days (limit {STALE_ACCESS_DAYS}) "
                          f"and still active.",
                "days_since_last_use": idle,
            })

        issued = _age_days(tp.get("credential_issued_at"))
        if issued is not None and issued > MAX_CREDENTIAL_AGE_DAYS:
            issues.append({
                "check": "credential_not_rotated",
                "detail": f"Credential issued {issued} days ago "
                          f"(rotation period {MAX_CREDENTIAL_AGE_DAYS}).",
                "credential_age_days": issued,
            })

    return {
        "processor": tp["name"],
        "category": tp.get("category"),
        "status": "offboarded" if ended and not live else "live",
        "issues": issues,
        "rank_weight": sum(ISSUE_WEIGHT[i["check"]] for i in issues),
    }


@register("third_party.access_posture")
class AccessPosture:
    """DPDP-TP-01: processor access is contracted, proportionate and current.

    Every processor in the inventory is examined, so this is a census of the
    inventory and the sampling gates do not apply. What it cannot see is a
    processor that is missing from the inventory altogether -- that limit is
    recorded on the result rather than assumed away.
    """

    evidence_contract = EvidenceContract(
        required=(
            EvidenceRequirement(
                "third_parties", EvidenceKind.DB_QUERY, defines_population=True
            ),
        )
    )

    def execute(self, evidence: EvidenceBundle, config: dict[str, Any]) -> RawResult:
        processors = evidence.payload("third_parties", [])
        assessed = [assess_processor(tp) for tp in processors]

        # Worst first, then by name so ties are stable between runs.
        assessed.sort(key=lambda a: (-a["rank_weight"], a["processor"]))
        failing = [a for a in assessed if a["issues"]]

        # Rule 15 lets the Central Government restrict transfers to places it
        # names by order. No such order has been issued (SOURCES D5), so there
        # is nothing to test a transfer against. Offshore processors are
        # listed so the question is visible; they are not counted as failures.
        cross_border = [
            {"processor": tp["name"], "country": tp.get("country")}
            for tp in sorted(processors, key=lambda t: t["name"])
            if tp.get("country") and tp["country"] != HOME_JURISDICTION
            and tp.get("is_active")
        ]

        return RawResult(
            outcome=Verdict.FAIL if failing else Verdict.PASS,
            inference_mode=InferenceMode.CENSUS,
            sample_frame=SampleFrame.CENSUS,
            sample_size=len(assessed),
            population_size=len(assessed),
            successes=len(assessed) - len(failing),
            detail={
                "processors_examined": len(assessed),
                "processors_with_issues": len(failing),
                "ranked": assessed,
                "issue_counts": {
                    check: sum(
                        1 for a in assessed for i in a["issues"] if i["check"] == check
                    )
                    for check in ISSUE_WEIGHT
                },
                "cross_border_observations": cross_border,
                "cross_border_note": (
                    "Recorded, not failed. Rule 15 restricts transfers only to "
                    "places named in a Central Government order, and none has "
                    "been issued. See SOURCES D5."
                ),
                "thresholds": {
                    "stale_access_days": STALE_ACCESS_DAYS,
                    "max_credential_age_days": MAX_CREDENTIAL_AGE_DAYS,
                    "measured_against": EPOCH.date().isoformat(),
                },
                "inventory_limit": (
                    "A census of the processor inventory. A processor the "
                    "inventory does not list is outside what this can see."
                ),
            },
        )


@register("retention.processor_erasure_cascade")
class ProcessorErasureCascade:
    """DPDP-08-02: erasure reaches every processor that received the data.

    The unit tested is the pair (erased principal, processor holding customer
    data). A pair passes only with an instruction AND a confirmation: an
    instruction nobody confirmed is an erasure nobody knows happened.

    Against Meridian's estate this never executes. No record of erasure
    instructions exists, nothing is registered to collect one, and the
    control gates on G4 before reaching here. The logic is still built and
    tested, so that when the record exists the control runs rather than
    having to be written then.
    """

    evidence_contract = EvidenceContract(
        required=(
            EvidenceRequirement(
                "erased_principals", EvidenceKind.DB_QUERY, defines_population=True
            ),
            EvidenceRequirement("third_parties", EvidenceKind.DB_QUERY),
            EvidenceRequirement("processor_erasure_instructions", EvidenceKind.DB_QUERY),
        )
    )

    def execute(self, evidence: EvidenceBundle, config: dict[str, Any]) -> RawResult:
        principals = evidence.payload("erased_principals", [])
        processors = evidence.payload("third_parties", [])
        instructions = evidence.payload("processor_erasure_instructions", [])

        # Processors that received customer data: those granted customer read
        # access. A processor that never held the data has nothing to erase.
        recipients = sorted(
            tp["name"] for tp in processors
            if "read:customers" in (tp.get("granted_scopes") or [])
        )

        confirmed = {
            (i["principal_id"], i["processor"])
            for i in instructions
            if i.get("instructed_at") is not None and i.get("confirmed_at") is not None
        }
        instructed = {(i["principal_id"], i["processor"]) for i in instructions}

        exceptions: list[dict[str, Any]] = []
        complete = 0
        for p in principals:
            gaps = [
                {
                    "processor": name,
                    "state": "instructed, not confirmed"
                    if (p["id"], name) in instructed else "never instructed",
                }
                for name in recipients
                if (p["id"], name) not in confirmed
            ]
            if gaps:
                exceptions.append({"principal": p["external_ref"], "gaps": gaps})
            else:
                complete += 1

        return RawResult(
            outcome=Verdict.FAIL if exceptions else Verdict.PASS,
            inference_mode=InferenceMode.CENSUS,
            sample_frame=SampleFrame.CENSUS,
            sample_size=len(principals),
            population_size=len(principals),
            successes=complete,
            detail={
                "erased_principals": len(principals),
                "recipient_processors": recipients,
                "principals_with_gaps": len(exceptions),
                # Enough to act on without writing thousands of rows into
                # every result.
                "exceptions_sample": exceptions[:20],
            },
        )
