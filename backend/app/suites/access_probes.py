"""Suite 3: access-control probes, adversarial by design.

Four procedures share one set of live HTTP exchanges against the target
service (`probe_access_exchanges`, registered as evidence `probe_exchanges`
in `evidence_sources.py`): ownership override, boundary/type-confusion
bypass, log visibility, and stale-credential reuse. A happy-path probe would
prove only that the obvious case works; these probe the cases a reviewer
scanning for logic errors would not think to check.

Fixed principals and customer ids, not drawn from the seeded estate: the
adversarial cases (S2-S4) live in `target_service/defects.py` against a
small fixed cast, and pinning them is what makes a run reproducible.
"""

from __future__ import annotations

import json
import math
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

# Tokens the target service's fixture data recognises. [target_service/app.py]
TOK_OPS_DESK = "tok_ops_desk"          # internal staff, unrestricted
TOK_VERIFYKART = "tok_verifykart"      # KYC vendor, assigned 1001-1003 only
TOK_ECHOSCRIBE = "tok_echoscribe"      # 425 days stale, still active
SPEND_CAP = 50_000.0


def probe_access_exchanges(client: httpx.Client) -> dict[str, Any]:
    """Run every adversarial exchange once and read back what the target
    service logged as a result, so the log-visibility check sees exactly
    the attempts the other three checks made -- not a second, separate run
    that could disagree with the first."""
    client.post("/_probe/reset")

    ownership = _probe_ownership(client)
    refused = _probe_legitimately_refused(client)
    input_validation = _probe_input_validation(client)
    stale_credential = _probe_stale_credential(client)
    access_log = client.get("/_probe/access-log").json()

    return {
        "ownership": ownership,
        "refused": refused,
        "input_validation": input_validation,
        "stale_credential": stale_credential,
        "access_log_entries": access_log.get("entries", []),
    }


def _probe_ownership(client: httpx.Client) -> list[dict[str, Any]]:
    """DPDP-06-02: VerifyKart holds read:customers and is assigned only
    1001-1003. 1004 is outside its assignment -- an ownership override if
    the response is 200."""
    attempts = []
    for customer_id, is_assigned in ((1001, True), (1004, False)):
        response = client.get(
            f"/customers/{customer_id}",
            headers={"Authorization": f"Bearer {TOK_VERIFYKART}"},
        )
        attempts.append({
            "principal": "VerifyKart KYC",
            "customer_id": customer_id,
            "is_assigned": is_assigned,
            "status_code": response.status_code,
            "allowed": response.status_code == 200,
        })
    return attempts


def _probe_legitimately_refused(client: httpx.Client) -> dict[str, Any]:
    """DPDP-06-04's own probe: a refusal that the S2 defect never produces.

    Every ownership attempt above is allowed -- that IS the S2 defect --
    so none of them can show whether a refusal gets logged. EchoScribe
    holds no read:customers scope at all, so this refusal is genuine and
    has nothing to do with S2: it is refused by the scope check, which
    works correctly, before ownership is ever reached."""
    response = client.get(
        "/customers/1001",
        headers={"Authorization": f"Bearer {TOK_ECHOSCRIBE}"},
    )
    return {
        "principal": "EchoScribe Transcription",
        "customer_id": 1001,
        "status_code": response.status_code,
        "allowed": response.status_code == 200,
    }


def _probe_input_validation(client: httpx.Client) -> list[dict[str, Any]]:
    """DPDP-06-03: NaN defeats a `value > cap` guard because every ordered
    comparison with NaN is false. A finite in-range value and a finite
    overflow value are run alongside it as the comparison cases -- both
    should behave correctly, which is what makes the NaN case a defect
    rather than the check simply not working at all."""
    cases = (
        ("nan", math.nan, False),
        ("in_range", 10_000.0, True),
        ("overflow", 1e400, False),
    )
    attempts = []
    for label, value, should_be_accepted in cases:
        # httpx's `json=` parameter serialises with `allow_nan=False` and
        # raises rather than send a non-finite value -- exactly the
        # well-behaved-client assumption this probe exists to test past.
        # The stdlib's own `json.dumps` has no such restriction.
        body = json.dumps({"spend_cap": value}).encode("utf-8")
        response = client.post(
            "/customers/1001/spend-cap",
            content=body,
            headers={
                "Authorization": f"Bearer {TOK_OPS_DESK}",
                "Content-Type": "application/json",
            },
        )
        attempts.append({
            "case": label,
            "value_sent": str(value),
            "should_be_accepted": should_be_accepted,
            "status_code": response.status_code,
            "accepted": response.status_code == 200,
        })
    return attempts


def _probe_stale_credential(client: httpx.Client) -> dict[str, Any]:
    """DPDP-TP-02: EchoScribe's credential has not been used in 425 days.
    A working transcript read means a dormant processor key still opens
    the door."""
    response = client.get(
        "/transcripts/MFS-TRANSCRIPT-01",
        headers={"Authorization": f"Bearer {TOK_ECHOSCRIBE}"},
    )
    return {
        "principal": "EchoScribe Transcription",
        "days_since_last_use": 425,
        "status_code": response.status_code,
        "accepted": response.status_code == 200,
    }


@register("access.authorisation_probes")
class AuthorisationProbes:
    """DPDP-06-02: scope answers "may you read customers"; ownership
    answers "may you read this one". Only the first is checked."""

    evidence_contract = EvidenceContract(
        required=(EvidenceRequirement("probe_exchanges", EvidenceKind.HTTP_PROBE),),
    )

    def execute(self, evidence: EvidenceBundle, config: dict[str, Any]) -> RawResult:
        attempts = evidence.payload("probe_exchanges", {}).get("ownership", [])
        exceptions = [a for a in attempts if not a["is_assigned"] and a["allowed"]]

        return RawResult(
            outcome=Verdict.FAIL if exceptions else Verdict.PASS,
            inference_mode=InferenceMode.CENSUS,
            sample_frame=SampleFrame.CENSUS,
            sample_size=len(attempts),
            population_size=len(attempts),
            successes=len(attempts) - len(exceptions),
            detail={
                "attempts": attempts,
                "exceptions": exceptions,
                "finding": (
                    "VerifyKart, assigned only customers 1001-1003, read "
                    "customer 1004 -- scope was checked, ownership was not."
                    if exceptions else None
                ),
            },
        )


@register("access.input_validation_probes")
class InputValidationProbes:
    """DPDP-06-03: NaN passes a naive `value > cap` guard, since every
    ordered comparison with NaN is false in IEEE-754."""

    evidence_contract = EvidenceContract(
        required=(EvidenceRequirement("probe_exchanges", EvidenceKind.HTTP_PROBE),),
    )

    def execute(self, evidence: EvidenceBundle, config: dict[str, Any]) -> RawResult:
        attempts = evidence.payload("probe_exchanges", {}).get("input_validation", [])
        exceptions = [
            a for a in attempts if not a["should_be_accepted"] and a["accepted"]
        ]

        return RawResult(
            outcome=Verdict.FAIL if exceptions else Verdict.PASS,
            inference_mode=InferenceMode.CENSUS,
            sample_frame=SampleFrame.CENSUS,
            sample_size=len(attempts),
            population_size=len(attempts),
            successes=len(attempts) - len(exceptions),
            detail={
                "attempts": attempts,
                "exceptions": exceptions,
                "finding": (
                    f"spend_cap={SPEND_CAP} accepted a value of NaN: every "
                    "ordered comparison with NaN is false, so `value > cap` "
                    "never rejects it."
                    if exceptions else None
                ),
            },
        )


@register("access.log_visibility")
class LogVisibility:
    """DPDP-06-04: the control on the control. A refusal that leaves no
    log entry can never be reviewed for a pattern."""

    evidence_contract = EvidenceContract(
        required=(EvidenceRequirement("probe_exchanges", EvidenceKind.HTTP_PROBE),),
    )

    def execute(self, evidence: EvidenceBundle, config: dict[str, Any]) -> RawResult:
        exchange = evidence.payload("probe_exchanges", {})
        ownership_attempts = exchange.get("ownership", [])
        refused = exchange.get("refused", {})
        log_entries = exchange.get("access_log_entries", [])
        logged_actions = {
            (e.get("actor_ref"), e.get("action")) for e in log_entries
        }

        # Every attempt this run made -- refused or allowed -- should have
        # produced a log entry. The refused one is the point: access
        # control held, but nothing recorded that it was tested.
        checked = [
            {
                **a,
                "was_logged": (
                    "VerifyKart KYC", f"READ customer {a['customer_id']}"
                ) in logged_actions,
            }
            for a in ownership_attempts
        ]
        checked.append({
            **refused,
            "was_logged": (
                refused.get("principal"),
                f"READ customer {refused.get('customer_id')}",
            ) in logged_actions,
        })
        exceptions = [a for a in checked if not a["was_logged"]]

        return RawResult(
            outcome=Verdict.FAIL if exceptions else Verdict.PASS,
            inference_mode=InferenceMode.CENSUS,
            sample_frame=SampleFrame.CENSUS,
            sample_size=len(checked),
            population_size=len(checked),
            successes=len(checked) - len(exceptions),
            detail={
                "attempts_checked": checked,
                "exceptions": exceptions,
                "log_entries_observed": len(log_entries),
            },
        )


@register("access.stale_credential_probe")
class StaleCredentialProbe:
    """DPDP-TP-02: existence and the active flag are checked; days since
    last use is not, so a processor's key outlives the relationship."""

    evidence_contract = EvidenceContract(
        required=(
            EvidenceRequirement("probe_exchanges", EvidenceKind.HTTP_PROBE),
            EvidenceRequirement("third_parties", EvidenceKind.DB_QUERY),
        ),
    )

    def execute(self, evidence: EvidenceBundle, config: dict[str, Any]) -> RawResult:
        attempt = evidence.payload("probe_exchanges", {}).get("stale_credential", {})
        is_exception = bool(attempt.get("accepted"))

        return RawResult(
            outcome=Verdict.FAIL if is_exception else Verdict.PASS,
            inference_mode=InferenceMode.CENSUS,
            sample_frame=SampleFrame.CENSUS,
            sample_size=1,
            population_size=1,
            successes=0 if is_exception else 1,
            detail={
                "attempt": attempt,
                "finding": (
                    f"{attempt.get('principal')}'s credential, unused for "
                    f"{attempt.get('days_since_last_use')} days, still "
                    "authenticated."
                    if is_exception else None
                ),
            },
        )
