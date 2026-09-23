"""Suite 4 against the real estate: third-party access posture and the
erasure cascade.

The Day 6 acceptance criterion for this suite is S4 -- EchoScribe, stale and
without a processor agreement -- found by the procedure actually running.
"""

from __future__ import annotations

import datetime as dt
from typing import Any

import pytest
from sqlalchemy.orm import Session

from app import suites as _suites  # noqa: F401  registers procedures
from app.engine import gate as gate_module
from app.engine.collectors import default_broker
from app.engine.evidence import (
    EvidenceBundle,
    EvidenceContract,
    EvidenceItem,
    EvidenceKind,
    EvidenceRequirement,
)
from app.engine.gate import GateReason, InferenceMode, Verdict
from app.engine.runner import get_procedure
from app.engine.thresholds import Thresholds
from app.seed.generator import EPOCH
from app.suites.evidence_sources import collect_erased_principals, collect_third_parties

pytestmark = pytest.mark.usefixtures("seeded_estate")


def bundle(**payloads: Any) -> EvidenceBundle:
    now = dt.datetime.now(dt.UTC)
    return EvidenceBundle(
        items={
            name: EvidenceItem(name, EvidenceKind.DB_QUERY, name, payload, now, "h")
            for name, payload in payloads.items()
        }
    )


def posture(db: Session) -> Any:
    return get_procedure("third_party.access_posture").execute(  # type: ignore[union-attr]
        bundle(third_parties=collect_third_parties({"db": db})), {}
    )


# --- S4 --------------------------------------------------------------------


def test_s4_echoscribe_is_stale_and_uncontracted(seeded_estate: Session) -> None:
    result = posture(seeded_estate)
    assert result.outcome is Verdict.FAIL

    echo = next(a for a in result.detail["ranked"]
                if a["processor"] == "EchoScribe Transcription")
    checks = {i["check"] for i in echo["issues"]}

    assert {"no_processor_agreement", "stale_credential"} <= checks
    stale = next(i for i in echo["issues"] if i["check"] == "stale_credential")
    assert stale["days_since_last_use"] == 425


def test_every_issue_is_collected_not_just_the_first(seeded_estate: Session) -> None:
    """EchoScribe fails four checks with four different owners. Stopping at
    the first would hide three of them."""
    echo = next(a for a in posture(seeded_estate).detail["ranked"]
                if a["processor"] == "EchoScribe Transcription")
    assert {i["check"] for i in echo["issues"]} == {
        "no_processor_agreement", "stale_credential",
        "excess_scope", "credential_not_rotated",
    }


def test_the_worst_processor_is_ranked_first(seeded_estate: Session) -> None:
    ranked = posture(seeded_estate).detail["ranked"]
    assert ranked[0]["processor"] == "EchoScribe Transcription"


# --- Statistics --------------------------------------------------------------


def test_a_full_inventory_is_a_census_and_is_not_gated_for_size(
    seeded_estate: Session,
) -> None:
    """Fourteen processors is below any minimum sample, but it is every
    processor. Gating it on G1 would call a complete examination too small."""
    result = posture(seeded_estate)
    assert result.inference_mode is InferenceMode.CENSUS
    assert result.sample_size == result.population_size == 14

    outcome = gate_module.apply(result, Thresholds())
    assert not outcome.gate_fired
    assert outcome.verdict is Verdict.FAIL


# --- No false alarms -------------------------------------------------------


def test_a_correctly_offboarded_processor_is_not_flagged(seeded_estate: Session) -> None:
    quill = next(a for a in posture(seeded_estate).detail["ranked"]
                 if a["processor"] == "Quillmark Surveys")
    assert quill["status"] == "offboarded"
    assert quill["issues"] == []


def test_offshore_processors_are_recorded_but_not_failed(seeded_estate: Session) -> None:
    """No Rule 15 order exists to test a transfer against, so an offshore
    processor is an observation, not an exception."""
    result = posture(seeded_estate)
    offshore = {o["processor"] for o in result.detail["cross_border_observations"]}
    assert "Reachpoint Marketing" in offshore

    reachpoint = next(a for a in result.detail["ranked"]
                      if a["processor"] == "Reachpoint Marketing")
    assert reachpoint["issues"] == []


def test_a_clean_processor_passes() -> None:
    """The contrast case. Without it the control could be satisfied by an
    implementation that fails everything."""
    clean = {
        "name": "Tidy Processor", "category": "x", "dpa_reference": "DPA-1",
        "granted_scopes": ["read:x"], "exercised_scopes": ["read:x"],
        "credential_issued_at": EPOCH - dt.timedelta(days=30),
        "last_used_at": EPOCH - dt.timedelta(days=1),
        "is_active": True, "relationship_ended_at": None, "country": "IN",
    }
    result = get_procedure("third_party.access_posture").execute(  # type: ignore[union-attr]
        bundle(third_parties=[clean]), {}
    )
    assert result.outcome is Verdict.PASS


def test_live_access_after_offboarding_is_an_exception() -> None:
    ended = {
        "name": "Former Vendor", "dpa_reference": "DPA-2",
        "granted_scopes": [], "exercised_scopes": [],
        "credential_issued_at": EPOCH - dt.timedelta(days=30),
        "last_used_at": EPOCH - dt.timedelta(days=1),
        "is_active": True,
        "relationship_ended_at": EPOCH - dt.timedelta(days=60),
        "country": "IN",
    }
    result = get_procedure("third_party.access_posture").execute(  # type: ignore[union-attr]
        bundle(third_parties=[ended]), {}
    )
    assert result.outcome is Verdict.FAIL
    assert result.detail["ranked"][0]["issues"][0]["check"] == "access_after_offboarding"


def test_the_estate_still_matches_what_the_suite_expects(seeded_estate: Session) -> None:
    """Pins the fixture so a generator change fails here rather than quietly
    changing what 'S4 detected' means."""
    result = posture(seeded_estate)
    assert result.detail["processors_with_issues"] == 7


# --- Evidence hygiene ------------------------------------------------------


def test_credential_tokens_never_enter_evidence(seeded_estate: Session) -> None:
    """The first rows of each payload are persisted. A token read into
    evidence would be written into the results table."""
    rows = collect_third_parties({"db": seeded_estate})
    assert rows
    assert all("credential_token" not in r for r in rows)


# --- DPDP-08-02: the erasure cascade ---------------------------------------


def test_the_cascade_gates_on_missing_instruction_records(seeded_estate: Session) -> None:
    """No record of erasure instructions exists, so the control cannot
    conclude either way -- and must say so rather than report a result."""
    contract = EvidenceContract(required=(
        EvidenceRequirement("erased_principals", EvidenceKind.DB_QUERY, True),
        EvidenceRequirement("third_parties", EvidenceKind.DB_QUERY),
        EvidenceRequirement("processor_erasure_instructions", EvidenceKind.DB_QUERY),
    ))
    collected = default_broker().collect(contract, {"db": seeded_estate})
    assert collected.missing == ("processor_erasure_instructions",)

    outcome = gate_module.apply(
        gate_module.RawResult(
            outcome=Verdict.PASS, missing_required_evidence=collected.missing
        ),
        Thresholds(),
    )
    assert outcome.verdict is Verdict.INSUFFICIENT_EVIDENCE
    assert GateReason.G4_MISSING_ARTIFACT in outcome.reasons


def test_erased_principals_are_only_the_erased(seeded_estate: Session) -> None:
    rows = collect_erased_principals({"db": seeded_estate})
    assert all(r["erased_at"] is not None for r in rows)


def _cascade(instructions: list[dict[str, Any]]) -> Any:
    return get_procedure("retention.processor_erasure_cascade").execute(  # type: ignore[union-attr]
        bundle(
            erased_principals=[{"id": 1, "external_ref": "MFS000001", "erased_at": EPOCH}],
            third_parties=[
                {"name": "HoldsData", "granted_scopes": ["read:customers"]},
                {"name": "NeverHeld", "granted_scopes": ["read:kyc"]},
            ],
            processor_erasure_instructions=instructions,
        ),
        {},
    )


def test_a_confirmed_cascade_passes() -> None:
    now = EPOCH
    result = _cascade([{"principal_id": 1, "processor": "HoldsData",
                        "instructed_at": now, "confirmed_at": now}])
    assert result.outcome is Verdict.PASS
    # A processor that never received the data has nothing to erase.
    assert result.detail["recipient_processors"] == ["HoldsData"]


def test_an_unconfirmed_instruction_is_still_a_gap() -> None:
    """An instruction nobody confirmed is an erasure nobody knows happened."""
    result = _cascade([{"principal_id": 1, "processor": "HoldsData",
                        "instructed_at": EPOCH, "confirmed_at": None}])
    assert result.outcome is Verdict.FAIL
    gap = result.detail["exceptions_sample"][0]["gaps"][0]
    assert gap["state"] == "instructed, not confirmed"


def test_a_missing_instruction_is_a_gap() -> None:
    result = _cascade([])
    assert result.outcome is Verdict.FAIL
    assert result.detail["exceptions_sample"][0]["gaps"][0]["state"] == "never instructed"
