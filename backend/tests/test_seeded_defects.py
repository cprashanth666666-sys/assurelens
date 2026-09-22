"""Every planted defect must be findable, and every clean control must pass.

This is the executable form of PRD 8.1 and the test that lets the README state
a detection rate as a measured number rather than a claim.

Two halves matter equally. A suite that finds all nine defects but also flags
clean controls is unusable — an assurance tool that cries wolf gets ignored,
which is worse than not existing.
"""

from __future__ import annotations

import datetime as dt

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.estate import (
    ConsentEvent,
    ConsentRecord,
    DataAsset,
    DataPrincipal,
    ModelPrediction,
    ModelRegistry,
    ProcessingActivity,
    ThirdParty,
)
from app.seed.generator import EPOCH

# The s.8(8) window after which a purpose is deemed no longer served. Three
# years matches the period the Rules use elsewhere; it is a documented,
# arguable default, not a figure the Act prescribes for a bank.
PURPOSE_CESSATION_DAYS = 1095

# Rule 8(3): personal data, traffic data and logs for a minimum of one year.
MINIMUM_LOG_RETENTION_DAYS = 365

# TRD 5.3 defaults, asserted here so a change to either end shows up as a
# failing test rather than as a quietly different demo.
PROPAGATION_SLA_SECONDS = 300
STALE_ACCESS_DAYS = 180
FAIRNESS_RATIO_THRESHOLD = 0.80
MIN_GROUP_N = 30

pytestmark = pytest.mark.usefixtures("seeded_estate")


# --- S5: held past purpose cessation with no recorded legal basis ----------


def test_s5_records_held_without_a_legal_basis_are_findable(
    seeded_estate: Session,
) -> None:
    """Restated after the Day 2 correction.

    The Third Schedule's timetable binds only e-commerce, online gaming and
    social media intermediaries above user thresholds; a BFSI captive GCC is
    none of them. What binds Meridian is Act s.8(7)(a), whose carve-out the
    Act illustrates with a bank. So the query is not "how old" but "is there
    anything on file justifying still holding this".
    """
    cutoff = EPOCH - dt.timedelta(days=PURPOSE_CESSATION_DAYS)

    overdue = seeded_estate.scalar(
        select(func.count())
        .select_from(DataPrincipal)
        .where(
            DataPrincipal.erased_at.is_(None),
            DataPrincipal.legal_hold.is_(False),
            DataPrincipal.last_contact_at < cutoff,
        )
    )

    assert overdue == 11_400


def test_lawfully_held_records_are_not_findings_however_old(
    seeded_estate: Session,
) -> None:
    """The Act's Illustration (II) case: a bank holding client identity
    records for ten years under a statutory duty is compliant, not overdue.
    A control that flagged these would be wrong, and loudly so."""
    cutoff = EPOCH - dt.timedelta(days=PURPOSE_CESSATION_DAYS)

    held = seeded_estate.scalars(
        select(DataPrincipal).where(
            DataPrincipal.legal_hold.is_(True),
            DataPrincipal.last_contact_at < cutoff,
        )
    ).all()

    assert held, "expected some lawfully-held old records as the contrast case"
    assert all(p.legal_hold_basis for p in held), (
        "a legal hold with no recorded basis is itself the finding"
    )


# --- S6: processing logs purged below the one-year floor -------------------


def test_s6_log_retention_below_the_statutory_floor_is_findable(
    seeded_estate: Session,
) -> None:
    """Rule 8(3) is drafted generally, with no class restriction, so unlike
    Rule 8(1) it does bind Meridian."""
    offending = seeded_estate.scalars(
        select(ProcessingActivity).where(
            ProcessingActivity.log_retention_days < MINIMUM_LOG_RETENTION_DAYS
        )
    ).all()

    assert len(offending) == 1
    assert offending[0].log_retention_days == 90


def test_over_deletion_and_under_deletion_are_both_testable(
    seeded_estate: Session,
) -> None:
    """Rule 8(3) pulls against s.8(7): a system that deletes personal data on
    schedule but purges its logs at 90 days breaches 8(3) while looking
    maximally privacy-friendly. Most tools only look in one direction."""
    activities = seeded_estate.scalars(select(ProcessingActivity)).all()

    assert any(a.log_retention_days < MINIMUM_LOG_RETENTION_DAYS for a in activities)
    assert any(a.log_retention_days >= MINIMUM_LOG_RETENTION_DAYS for a in activities)


# --- S1: consent withdrawal does not reach the downstream system -----------


def test_s1_withdrawal_propagation_lag_is_measurable(
    seeded_estate: Session,
) -> None:
    """The finding is a latency distribution, not a binary.

    "No propagation control observed" is a weak finding a client can argue
    with. "Median 11 hours, worst case 22" is not.
    """
    lags = seeded_estate.scalars(
        select(ConsentEvent.latency_ms).where(
            ConsentEvent.event == "DOWNSTREAM_SYNC"
        )
    ).all()

    assert len(lags) == 3_200
    beyond_sla = [ms for ms in lags if ms and ms > PROPAGATION_SLA_SECONDS * 1000]
    assert len(beyond_sla) == 3_200, "every withdrawal should breach the SLA"

    worst_hours = max(lags) / 3_600_000
    assert 20 < worst_hours <= 24, "a nightly batch should cap out near 24h"


def test_the_consent_record_itself_looks_compliant(
    seeded_estate: Session,
) -> None:
    """Why suite 2 probes the downstream system rather than reading the store.

    Every withdrawal is recorded correctly and promptly. A tool that audits
    the consent table finds nothing wrong, which is exactly how this failure
    survives in production.
    """
    withdrawn = seeded_estate.scalars(
        select(ConsentRecord).where(ConsentRecord.status == "WITHDRAWN").limit(500)
    ).all()

    assert withdrawn
    assert all(c.withdrawn_at is not None for c in withdrawn)
    assert all(
        c.downstream_synced_at > c.withdrawn_at  # type: ignore[operator]
        for c in withdrawn
    ), "the downstream always lags, never leads"


# --- S4: processor access stale, over-scoped, and uncontracted -------------


def test_s4_processor_without_an_agreement_is_findable(
    seeded_estate: Session,
) -> None:
    """Act s.8(2) permits engaging a processor only under a valid contract."""
    uncontracted = seeded_estate.scalars(
        select(ThirdParty).where(ThirdParty.dpa_reference.is_(None))
    ).all()

    assert len(uncontracted) == 1
    assert uncontracted[0].name == "EchoScribe Transcription"


def test_s4_stale_credential_still_active_is_findable(
    seeded_estate: Session,
) -> None:
    cutoff = EPOCH - dt.timedelta(days=STALE_ACCESS_DAYS)

    stale = seeded_estate.scalars(
        select(ThirdParty).where(
            ThirdParty.is_active.is_(True), ThirdParty.last_used_at < cutoff
        )
    ).all()

    assert len(stale) == 1
    assert stale[0].name == "EchoScribe Transcription"


def test_over_scoped_processors_are_findable(seeded_estate: Session) -> None:
    """Granted scopes that exceed what was exercised in the period."""
    processors = seeded_estate.scalars(select(ThirdParty)).all()

    over_scoped = [
        p for p in processors
        if set(p.granted_scopes) - set(p.exercised_scopes)
    ]
    assert over_scoped, "expected proportionality failures to be present"


def test_cross_border_processors_are_identifiable(
    seeded_estate: Session,
) -> None:
    """Rule 15 exposure is real even though no order exists to test against,
    which is why the control gates on G7 rather than inventing a standard."""
    outside_india = seeded_estate.scalars(
        select(ThirdParty).where(ThirdParty.country != "IN")
    ).all()

    assert len(outside_india) >= 2


# --- S9: unmasked identifiers in an unencrypted, undeclared asset ----------


def test_s9_asset_holds_undeclared_identifiers_unencrypted(
    seeded_estate: Session,
) -> None:
    """A detector reading only structured columns never finds this, which is
    why suite 1 scans free text."""
    asset = seeded_estate.scalar(
        select(DataAsset).where(DataAsset.name == "call_transcripts")
    )

    assert asset is not None
    assert asset.encryption_at_rest is False
    assert "pan" not in asset.declared_identifier_classes


def test_encrypted_assets_are_the_norm(seeded_estate: Session) -> None:
    """The contrast case. If everything were unencrypted the finding would be
    about the estate, not about one asset."""
    assets = seeded_estate.scalars(select(DataAsset)).all()
    unencrypted = [a for a in assets if not a.encryption_at_rest]

    assert len(unencrypted) == 1


# --- S7 and S8: the model ---------------------------------------------------


def test_s8_model_has_no_drift_monitoring(seeded_estate: Session) -> None:
    model = seeded_estate.scalar(select(ModelRegistry))

    assert model is not None
    assert model.has_drift_monitoring is False
    assert model.is_consequential is True
    assert model.training_snapshot, "no baseline means drift is not computable"


def test_s7_selection_rate_ratio_fails_four_fifths(
    seeded_estate: Session,
) -> None:
    """Computed over groups large enough to support a conclusion.

    Including the undersized group would change the answer, which is exactly
    the error the sufficiency gate exists to prevent.
    """
    rows = seeded_estate.execute(
        select(
            DataPrincipal.group_attribute,
            func.count(ModelPrediction.id),
            # FILTER rather than a cast: it reads as what it is, and lets
            # PostgreSQL count the approvals in the same pass.
            func.count(ModelPrediction.id).filter(
                ModelPrediction.decision == "APPROVE"
            ),
        )
        .join(DataPrincipal, ModelPrediction.principal_id == DataPrincipal.id)
        .group_by(DataPrincipal.group_attribute)
    ).all()

    rates = {
        group: approved / total
        for group, total, approved in rows
        if total >= MIN_GROUP_N
    }

    assert len(rates) == 3, "three groups should be large enough to conclude from"
    ratio = min(rates.values()) / max(rates.values())
    assert ratio < FAIRNESS_RATIO_THRESHOLD, f"ratio {ratio:.3f} should fail"


def test_the_small_group_is_too_small_to_conclude_from(
    seeded_estate: Session,
) -> None:
    """The fairness trap, and the demo's strongest thirty seconds.

    A naive tool reports a dramatic disparity from 22 observations. The
    correct answer is that 22 observations cannot support the claim.
    """
    counts = dict(
        seeded_estate.execute(
            select(DataPrincipal.group_attribute, func.count(ModelPrediction.id))
            .join(DataPrincipal, ModelPrediction.principal_id == DataPrincipal.id)
            .group_by(DataPrincipal.group_attribute)
        ).all()
    )

    assert counts["D"] == 22
    assert counts["D"] < MIN_GROUP_N
    assert all(n >= MIN_GROUP_N for g, n in counts.items() if g != "D")


def test_ground_truth_exists_for_only_part_of_the_population(
    seeded_estate: Session,
) -> None:
    """Which is what makes equal opportunity computable on a subset and not
    on the whole, and therefore subject to its own coverage question."""
    total = seeded_estate.scalar(
        select(func.count()).select_from(ModelPrediction)
    )
    known = seeded_estate.scalar(
        select(func.count())
        .select_from(ModelPrediction)
        .where(ModelPrediction.ground_truth.is_not(None))
    )

    assert 0 < known < total


# --- Coverage: why the sufficiency gate will fire for real reasons ---------


def test_a_typical_sample_falls_below_the_coverage_threshold(
    seeded_estate: Session,
) -> None:
    """G3 has to fire because the arithmetic says so, not because the fixture
    was rigged to make it fire."""
    population = seeded_estate.scalar(
        select(func.count()).select_from(DataPrincipal)
    )

    assert population == 24_000
    assert (200 / population) * 100 < 10.0
