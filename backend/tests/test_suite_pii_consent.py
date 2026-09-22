"""Suites 1 and 2 against the real estate.

The Day 5 acceptance criteria, executable. Each seeded defect must be found
by a procedure actually running -- and a clean estate must produce no
findings, because a suite that cries wolf is worse than none.
"""

from __future__ import annotations

from typing import Any

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

import app.suites  # noqa: F401  registers procedures and evidence sources
from app.engine.evidence import EvidenceBundle, EvidenceItem, EvidenceKind
from app.engine.gate import InferenceMode, Verdict
from app.engine.runner import get_procedure
from app.models.estate import DataAsset
from app.suites.evidence_sources import (
    collect_access_logs,
    collect_asset_records,
    collect_consent_records,
    collect_data_assets,
    collect_data_principals,
    collect_processing_activities,
)

pytestmark = pytest.mark.usefixtures("seeded_estate")

import datetime as dt  # noqa: E402


def bundle(**payloads: Any) -> EvidenceBundle:
    now = dt.datetime.now(dt.UTC)
    return EvidenceBundle(
        items={
            name: EvidenceItem(
                name, EvidenceKind.DB_QUERY, name, payload, now, "hash"
            )
            for name, payload in payloads.items()
        }
    )


# --- S9: undeclared, unencrypted identifiers -------------------------------


def test_s9_undeclared_pan_in_an_unencrypted_asset_is_found(
    seeded_estate: Session,
) -> None:
    """call_transcripts declares only transcript text and holds PANs spoken
    aloud on recorded calls, in a store with no encryption at rest."""
    context = {"db": seeded_estate}
    result = get_procedure("pii.discovery_and_protection").execute(  # type: ignore[union-attr]
        bundle(
            data_assets=collect_data_assets(context),
            asset_records=collect_asset_records(context),
        ),
        {},
    )

    assert result.outcome is Verdict.FAIL
    findings = result.detail["findings"]
    assets = {f["asset"] for f in findings}
    assert "call_transcripts" in assets

    undeclared = next(
        f for f in findings
        if f["asset"] == "call_transcripts" and f["issue"] == "undeclared_identifiers"
    )
    assert "pan" in undeclared["undeclared"]
    assert undeclared["occurrences"]["pan"] > 0


def test_a_positive_finding_is_definitive_regardless_of_coverage(
    seeded_estate: Session,
) -> None:
    """Presence and absence are not symmetrical.

    One record proves an identifier is there; no amount of unscanned data
    weakens that. Absence is the claim that needs coverage. Reporting the two
    the same way is how a 3% scan becomes a clean bill of health.
    """
    context = {"db": seeded_estate}
    result = get_procedure("pii.discovery_and_protection").execute(  # type: ignore[union-attr]
        bundle(
            data_assets=collect_data_assets(context),
            asset_records=collect_asset_records(context),
        ),
        {},
    )

    assert result.outcome is Verdict.FAIL
    assert result.inference_mode is InferenceMode.CENSUS, (
        "a positive finding must not be gated for thin coverage"
    )


def test_a_correctly_declared_asset_is_not_flagged(
    seeded_estate: Session,
) -> None:
    """kyc_documents declares aadhaar and pan and holds them, encrypted. If
    it appeared in the findings the suite would be reporting the norm."""
    context = {"db": seeded_estate}
    result = get_procedure("pii.discovery_and_protection").execute(  # type: ignore[union-attr]
        bundle(
            data_assets=collect_data_assets(context),
            asset_records=collect_asset_records(context),
        ),
        {},
    )

    flagged = {f["asset"] for f in result.detail["findings"]}
    assert "kyc_documents" not in flagged


def test_account_numbers_are_not_reported_as_aadhaar(
    seeded_estate: Session,
) -> None:
    """The false positive that made this suite unusable: 87 of 800 customer
    records reported as holding a national identity number they do not."""
    context = {"db": seeded_estate}
    result = get_procedure("pii.discovery_and_protection").execute(  # type: ignore[union-attr]
        bundle(
            data_assets=collect_data_assets(context),
            asset_records=collect_asset_records(context),
        ),
        {},
    )

    crm = [
        f for f in result.detail["findings"]
        if f["asset"] == "crm_customers" and f["issue"] == "undeclared_identifiers"
    ]
    assert not crm, f"false positive returned: {crm}"


# --- S5: retention without a recorded basis --------------------------------


def test_s5_records_held_without_a_legal_basis(seeded_estate: Session) -> None:
    context = {"db": seeded_estate}
    result = get_procedure("retention.erasure_on_purpose_cessation").execute(  # type: ignore[union-attr]
        bundle(
            data_principals=collect_data_principals(context),
            processing_activities=collect_processing_activities(context),
        ),
        {},
    )

    assert result.outcome is Verdict.FAIL
    assert result.detail["retained_without_basis"] == 11_400


def test_lawfully_held_records_are_not_counted_against_the_client(
    seeded_estate: Session,
) -> None:
    """The Act illustrates its own carve-out with a bank retaining client
    identity records for ten years. A control that flagged those would be
    confidently wrong about most of a bank's estate."""
    context = {"db": seeded_estate}
    result = get_procedure("retention.erasure_on_purpose_cessation").execute(  # type: ignore[union-attr]
        bundle(
            data_principals=collect_data_principals(context),
            processing_activities=collect_processing_activities(context),
        ),
        {},
    )

    assert result.detail["lawfully_retained"] > 0
    assert result.detail["legal_hold_without_recorded_basis"] == 0


# --- S6: logs purged below the statutory floor -----------------------------


def test_s6_log_retention_below_one_year(seeded_estate: Session) -> None:
    context = {"db": seeded_estate}
    result = get_procedure("retention.minimum_log_retention").execute(  # type: ignore[union-attr]
        bundle(
            processing_activities=collect_processing_activities(context),
            access_logs=collect_access_logs(context),
        ),
        {},
    )

    assert result.outcome is Verdict.FAIL
    below = result.detail["below_statutory_floor"]
    assert len(below) == 1
    assert below[0]["configured_days"] == 90
    assert below[0]["required_days"] == 365


def test_both_directions_of_rule_8_are_tested(seeded_estate: Session) -> None:
    """Erasure and retention pull against each other. A system that deletes
    on schedule but purges logs at ninety days breaches the floor while
    looking maximally privacy-friendly, and most tools look only one way."""
    context = {"db": seeded_estate}

    erasure = get_procedure("retention.erasure_on_purpose_cessation").execute(  # type: ignore[union-attr]
        bundle(
            data_principals=collect_data_principals(context),
            processing_activities=collect_processing_activities(context),
        ),
        {},
    )
    retention = get_procedure("retention.minimum_log_retention").execute(  # type: ignore[union-attr]
        bundle(
            processing_activities=collect_processing_activities(context),
            access_logs=collect_access_logs(context),
        ),
        {},
    )

    assert erasure.detail["retained_without_basis"] > 0, "under-deletion found"
    assert retention.detail["below_statutory_floor"], "over-deletion found"


# --- S1: withdrawal that does not reach the downstream ---------------------


def test_s1_withdrawal_lag_is_a_distribution_not_a_binary(
    seeded_estate: Session,
) -> None:
    """"No propagation control observed" is a weak finding a client can argue
    with. A measured median and worst case is not."""
    context = {"db": seeded_estate}
    result = get_procedure("consent.withdrawal_propagation").execute(  # type: ignore[union-attr]
        bundle(
            consent_records=collect_consent_records(context),
            downstream_segment={"still_in_segment_after_withdrawal": True},
        ),
        {},
    )

    assert result.outcome is Verdict.FAIL
    detail = result.detail
    assert detail["classification"]["LAGGED"] == 3_200
    assert detail["classification"]["PROPAGATED"] == 0
    assert 8 < detail["median_latency_hours"] < 14
    assert 20 < detail["worst_latency_hours"] <= 24


def test_the_consent_record_alone_would_look_compliant(
    seeded_estate: Session,
) -> None:
    """Why the suite probes the downstream system rather than reading the
    store: every withdrawal is recorded correctly and promptly."""
    context = {"db": seeded_estate}
    records = collect_consent_records(context)
    withdrawn = [r for r in records if r["status"] == "WITHDRAWN"]

    assert withdrawn
    assert all(r["withdrawn_at"] is not None for r in withdrawn)


# --- s.6(6): withdrawal harder than granting -------------------------------


def test_withdrawal_effort_parity_is_measured_not_asserted() -> None:
    """An "ease" requirement becomes testable once both journeys are
    published: steps, fields and channels are countable."""
    result = get_procedure("consent.withdrawal_effort_parity").execute(  # type: ignore[union-attr]
        EvidenceBundle(
            items={
                "grant_journey": EvidenceItem(
                    "grant_journey", EvidenceKind.HTTP_PROBE, "probe",
                    {"steps": 1, "required_fields": ["ref"], "channels": ["web", "app", "ivr"]},
                    dt.datetime.now(dt.UTC), "h",
                ),
                "withdrawal_journey": EvidenceItem(
                    "withdrawal_journey", EvidenceKind.HTTP_PROBE, "probe",
                    {
                        "steps": 3,
                        "required_fields": ["ref", "account", "reason"],
                        "channels": ["web"],
                    },
                    dt.datetime.now(dt.UTC), "h",
                ),
            }
        ),
        {},
    )

    assert result.outcome is Verdict.FAIL
    dimensions = {e["dimension"] for e in result.detail["exceptions"]}
    assert dimensions == {"steps", "required_fields", "channels"}


def test_equal_journeys_pass() -> None:
    """The contrast case. Without it the control could be satisfied by an
    implementation that fails everything."""
    same = {"steps": 1, "required_fields": ["ref"], "channels": ["web", "app"]}
    now = dt.datetime.now(dt.UTC)
    result = get_procedure("consent.withdrawal_effort_parity").execute(  # type: ignore[union-attr]
        EvidenceBundle(
            items={
                "grant_journey": EvidenceItem(
                    "grant_journey", EvidenceKind.HTTP_PROBE, "p", same, now, "h"
                ),
                "withdrawal_journey": EvidenceItem(
                    "withdrawal_journey", EvidenceKind.HTTP_PROBE, "p", same, now, "h"
                ),
            }
        ),
        {},
    )

    assert result.outcome is Verdict.PASS
    assert result.detail["exceptions"] == []


# --- No false alarms on a clean estate -------------------------------------


def test_a_clean_asset_set_produces_no_findings(seeded_estate: Session) -> None:
    """A suite that cries wolf is worse than no suite: the client stops
    reading it, and the real finding goes with the noise."""
    assets = [
        {
            "id": 1,
            "name": "tidy_store",
            "declared_identifier_classes": ["email", "mobile"],
            "encryption_at_rest": True,
            "record_count": 2,
        }
    ]
    records = [
        {"asset_id": 1, "content": {"email": "a@example.test", "mobile": "9876543210"}},
        {"asset_id": 1, "content": {"email": "b@example.test", "mobile": "9876543211"}},
    ]

    result = get_procedure("pii.discovery_and_protection").execute(  # type: ignore[union-attr]
        bundle(data_assets=assets, asset_records=records), {}
    )

    assert result.outcome is Verdict.PASS
    assert result.detail.get("findings", []) == []
    del seeded_estate


def test_the_estate_still_matches_what_the_suite_expects(
    seeded_estate: Session,
) -> None:
    """Pins the fixture the acceptance criteria are written against, so a
    change to the generator fails here rather than silently changing what
    'S9 detected' means."""
    assets = {
        a.name: a for a in seeded_estate.scalars(select(DataAsset)).all()
    }

    assert assets["call_transcripts"].encryption_at_rest is False
    assert "pan" not in assets["call_transcripts"].declared_identifier_classes
    assert assets["kyc_documents"].encryption_at_rest is True
