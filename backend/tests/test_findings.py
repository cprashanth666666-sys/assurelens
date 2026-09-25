"""FindingService. [Day 8]

Unit tests for the pure helpers first (severity banding, likelihood,
description), then the service against the seeded estate: idempotent raise,
ref allocation, and the acceptance bar itself -- a full run of the suites
that exist today raises findings from executed tests only, none seeded.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import suites as _suites  # noqa: F401  registers procedures
from app.engine import findings as svc
from app.engine.collectors import default_broker
from app.engine.runner import run_suites
from app.models.control import Control, Engagement
from app.models.findings import Finding, FindingHistory
from app.models.results import TestResult

pytestmark = pytest.mark.usefixtures("seeded_estate")


def result(**overrides: object) -> TestResult:
    """An unpersisted TestResult for exercising the pure helpers. Only
    attribute access is used, so no session or flush is needed."""
    defaults: dict[str, object] = dict(
        sample_size=None, population_size=None, successes=None,
        point_estimate=None, coverage_pct=None, detail={},
    )
    defaults.update(overrides)
    return TestResult(**defaults)  # type: ignore[arg-type]


def control(domain: str, **overrides: object) -> Control:
    defaults: dict[str, object] = dict(
        ref="X", title="A control", objective="Do the thing.", domain=domain,
    )
    defaults.update(overrides)
    return Control(**defaults)  # type: ignore[arg-type]


# --- Severity banding --------------------------------------------------------


@pytest.mark.parametrize(("score", "expected"), [
    (25, "CRITICAL"), (20, "CRITICAL"),
    (19, "HIGH"), (12, "HIGH"),
    (11, "MEDIUM"), (6, "MEDIUM"),
    (5, "LOW"), (1, "LOW"),
])
def test_severity_bands_match_the_schema(score: int, expected: str) -> None:
    """20-25 CRITICAL / 12-19 HIGH / 6-11 MEDIUM / 1-5 LOW. [SCHEMA 3.5]"""
    assert svc.band_severity(score) == expected


# --- Likelihood ----------------------------------------------------------------


@pytest.mark.parametrize(("point_estimate", "expected"), [
    # point_estimate is the compliance rate; exception_rate = 1 - it. Bands
    # are >= on exception_rate, so the boundary value belongs to the HIGHER
    # band: point_estimate 0.25 -> exception_rate exactly 0.75 -> still 5.
    (Decimal("0.00"), 5),  # exception_rate 1.00
    (Decimal("0.24"), 5),  # 0.76
    (Decimal("0.25"), 5),  # 0.75, the >=0.75 boundary itself
    (Decimal("0.26"), 4),  # 0.74, just inside the next band down
    (Decimal("0.49"), 4),  # 0.51
    (Decimal("0.50"), 4),  # 0.50, the >=0.50 boundary itself
    (Decimal("0.51"), 3),  # 0.49
    (Decimal("0.74"), 3),  # 0.26
    (Decimal("0.75"), 3),  # 0.25, the >=0.25 boundary itself
    (Decimal("0.76"), 2),  # 0.24
    (Decimal("0.94"), 2),  # 0.06
    (Decimal("0.95"), 2),  # 0.05, the >=0.05 boundary itself
    (Decimal("0.96"), 1),  # 0.04
    (Decimal("1.00"), 1),  # 0.00
])
def test_likelihood_bands_from_the_measured_exception_rate(
    point_estimate: Decimal, expected: int,
) -> None:
    likelihood, note = svc._likelihood(result(point_estimate=point_estimate))
    assert likelihood == expected
    assert note is None


def test_likelihood_falls_back_with_an_explicit_note_when_no_rate_exists() -> None:
    """A procedure that reports no proportion (today: the AI suite's census
    checks) never gets a silent, false-neutral midpoint."""
    likelihood, note = svc._likelihood(result(point_estimate=None))
    assert likelihood == svc.NO_RATE_LIKELIHOOD
    assert note is not None and "held at" in note


# --- Impact --------------------------------------------------------------------


def test_impact_is_domain_based_and_documented() -> None:
    impact, note = svc._impact(control("SECURITY_SAFEGUARDS"))
    assert impact == 5
    assert "editorial judgement" in note


def test_impact_has_a_fallback_for_an_unmapped_domain() -> None:
    impact, _ = svc._impact(control("SOME_FUTURE_DOMAIN"))
    assert impact == svc.DEFAULT_IMPACT


def test_every_domain_in_use_has_an_explicit_impact_weight() -> None:
    """A silent fallback for a real, in-use domain would mean two unrelated
    findings share a weight for no stated reason."""
    for domain in (
        "NOTICE_CONSENT", "SECURITY_SAFEGUARDS", "RETENTION_ERASURE",
        "PRINCIPAL_RIGHTS", "THIRD_PARTY_TRANSFER", "AI_GOVERNANCE",
        "BREACH_RESPONSE", "GOVERNANCE_ACCOUNTABILITY",
    ):
        assert domain in svc.DOMAIN_IMPACT


# --- Description ---------------------------------------------------------------


def test_description_uses_the_measured_proportion_when_one_exists() -> None:
    r = result(sample_size=14, successes=7, population_size=14, coverage_pct=Decimal("100.0"))
    text = svc._describe(control("THIRD_PARTY_TRANSFER"), r)
    assert text == "7 of 14 tested show the exception."


def test_description_names_the_population_when_it_differs_from_the_sample() -> None:
    r = result(
        sample_size=3200, successes=0, population_size=24000,
        coverage_pct=Decimal("13.333"),
    )
    text = svc._describe(control("RETENTION_ERASURE"), r)
    assert "3,200 of 3,200" in text and "13.3% of the 24,000-item population" in text


def test_description_reads_a_list_of_ready_made_sentences() -> None:
    r = result(detail={"exceptions": ["Feature x drifted.", "No monitoring exists."]})
    text = svc._describe(control("AI_GOVERNANCE"), r)
    assert text == "Feature x drifted. No monitoring exists."


def test_description_reads_a_structured_exception_dict_not_its_repr() -> None:
    """The bug this guards: a list of dicts must never be stringified into
    its Python repr in a reader-facing sentence."""
    r = result(detail={"exceptions": [
        {"dimension": "steps", "finding": "withdrawal requires 3 steps against 1"}
    ]})
    text = svc._describe(control("NOTICE_CONSENT"), r)
    assert text == "withdrawal requires 3 steps against 1."
    assert "{" not in text and "'dimension'" not in text


def test_description_reads_the_fairness_shape() -> None:
    r = result(detail={"fairness": {
        "groups": [{"group": "A"}],
        "selection_rate_ratio": 0.7, "lowest_group": "C",
        "highest_group": "A", "threshold": 0.8,
    }})
    text = svc._describe(control("AI_GOVERNANCE"), r)
    assert "0.7" in text and "group C against group A" in text and "0.8" in text


def test_description_falls_back_to_the_control_objective_with_nothing_measurable() -> None:
    c = control("GOVERNANCE_ACCOUNTABILITY", objective="A specific, real objective.")
    assert svc._describe(c, result()) == "A specific, real objective."


# --- Ref allocation --------------------------------------------------------------


def test_ref_allocation_continues_past_the_highest_existing_number(
    seeded_estate: Session,
) -> None:
    assert svc._next_ref(seeded_estate) == "F-001"
    seeded_estate.add(Finding(
        ref="F-001", engagement_id=1, control_id=1, title="t", description="d",
        likelihood=1, impact=1, severity="LOW",
    ))
    seeded_estate.flush()
    assert svc._next_ref(seeded_estate) == "F-002"
    seeded_estate.rollback()


# --- Against the seeded estate --------------------------------------------------


def _run(db: Session, engagement_id: int) -> None:
    run_suites(
        db, engagement_id,
        ["consent", "pii_retention", "access_probes", "third_party", "ai_assurance"],
        seed=42, broker=default_broker(), engine_version="test",
    )
    db.flush()


def test_a_full_run_raises_findings_from_executed_tests_only(
    seeded_estate: Session,
) -> None:
    engagement = seeded_estate.scalar(select(Engagement).order_by(Engagement.id).limit(1))
    assert engagement is not None
    _run(seeded_estate, engagement.id)

    raised = seeded_estate.scalars(
        select(Finding).where(Finding.engagement_id == engagement.id)
    ).all()
    # 12 today: 12 FAILs across all five suites. DPDP-08-02 (the processor
    # erasure cascade) stays INSUFFICIENT_EVIDENCE -- Meridian keeps no
    # erasure-instruction record, so it genuinely has nothing to conclude
    # from, and DPDP-08-04 is correctly NOT_APPLICABLE -- neither raises.
    assert len(raised) == 12
    assert all(f.description for f in raised)
    for f in raised:
        assert 1 <= f.likelihood <= 5
        assert 1 <= f.impact <= 5
        assert f.risk_score == f.likelihood * f.impact
        assert f.severity == svc.band_severity(f.risk_score)
        assert f.status == "OPEN"
    seeded_estate.rollback()


def test_no_finding_is_raised_for_a_passing_or_gated_control(
    seeded_estate: Session,
) -> None:
    """Only a clean FAIL raises. A PASS raises nothing; an
    INSUFFICIENT_EVIDENCE result (the erasure cascade, gated because
    Meridian keeps no erasure-instruction record) raises nothing either --
    the gate's own explanation is not re-narrated as a finding."""
    engagement = seeded_estate.scalar(select(Engagement).order_by(Engagement.id).limit(1))
    assert engagement is not None
    run_suites(
        seeded_estate, engagement.id, ["third_party"], seed=42,
        broker=default_broker(), engine_version="test",
    )
    seeded_estate.flush()

    from app.models.results import TestResult as ResultRow  # local import: test-only
    results = seeded_estate.scalars(select(ResultRow)).all()
    non_fail_control_ids = {r.control_id for r in results if r.verdict != "FAIL"}
    raised_control_ids = {
        f.control_id for f in seeded_estate.scalars(select(Finding)).all()
    }
    assert not (non_fail_control_ids & raised_control_ids)
    seeded_estate.rollback()


def test_a_second_failing_run_refreshes_the_open_finding_not_duplicates_it(
    seeded_estate: Session,
) -> None:
    engagement = seeded_estate.scalar(select(Engagement).order_by(Engagement.id).limit(1))
    assert engagement is not None
    _run(seeded_estate, engagement.id)
    first_pass_count = len(seeded_estate.scalars(select(Finding)).all())

    _run(seeded_estate, engagement.id)
    second_pass = seeded_estate.scalars(select(Finding)).all()

    assert len(second_pass) == first_pass_count
    tp01 = next(
        f for f in second_pass
        if seeded_estate.get(Control, f.control_id).ref == "DPDP-TP-01"  # type: ignore[union-attr]
    )
    assert tp01.origin_result_id is not None
    history = seeded_estate.scalars(
        select(FindingHistory).where(FindingHistory.finding_id == tp01.id)
    ).all()
    assert any(h.field == "origin_result_id" for h in history)
    seeded_estate.rollback()


def test_a_closed_finding_is_not_reopened_by_a_later_failure(
    seeded_estate: Session,
) -> None:
    """A status change a human made is not something a re-run overwrites."""
    engagement = seeded_estate.scalar(select(Engagement).order_by(Engagement.id).limit(1))
    assert engagement is not None
    _run(seeded_estate, engagement.id)

    tp01_finding = next(
        f for f in seeded_estate.scalars(select(Finding)).all()
        if seeded_estate.get(Control, f.control_id).ref == "DPDP-TP-01"  # type: ignore[union-attr]
    )
    original_ref = tp01_finding.ref
    tp01_finding.status = "CLOSED"
    seeded_estate.flush()

    _run(seeded_estate, engagement.id)

    all_findings = seeded_estate.scalars(select(Finding)).all()
    tp01_findings = [
        f for f in all_findings
        if seeded_estate.get(Control, f.control_id).ref == "DPDP-TP-01"  # type: ignore[union-attr]
    ]
    closed = next(f for f in tp01_findings if f.ref == original_ref)
    assert closed.status == "CLOSED"
    # A fresh, separate finding was opened for the new occurrence.
    assert any(f.status == "OPEN" and f.ref != original_ref for f in tp01_findings)
    seeded_estate.rollback()
