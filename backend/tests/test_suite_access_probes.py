"""Suite 3 against the live target service: access-control probes.

Unlike the other suites' unit tests, these go through `run_suites` with the
real HTTP broker rather than a hand-built evidence bundle -- the whole point
of this suite is that its evidence is a live request/response pair, so a
test that fakes the probe payload would prove nothing about whether the
probe itself still finds the defect.

The acceptance bar: S2 (ownership override), S3 (NaN bypasses the spend-cap
guard), the log-visibility gap (a refusal that is not recorded), and S4
(EchoScribe's 425-day-stale credential) are all found by the suite actually
running against `target_service`, not asserted from a mock.
"""

from __future__ import annotations

from typing import Any

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import suites as _suites  # noqa: F401  registers procedures
from app.engine.collectors import default_broker
from app.engine.gate import Verdict
from app.engine.runner import run_suites
from app.models.control import Control, Engagement
from app.models.results import TestResult

pytestmark = pytest.mark.usefixtures("seeded_estate")


def _run(seeded_estate: Session, engagement_id: int) -> dict[str, TestResult]:
    run = run_suites(
        seeded_estate, engagement_id, ["access_probes"],
        seed=42, broker=default_broker(), engine_version="test",
    )
    seeded_estate.flush()

    rows = seeded_estate.scalars(
        select(TestResult).where(TestResult.run_id == run.id)
    ).all()
    controls = {c.id: c.ref for c in seeded_estate.scalars(select(Control)).all()}
    return {controls[r.control_id]: r for r in rows}


def _detail(result: TestResult) -> dict[str, Any]:
    return result.detail


def test_s2_ownership_override_is_found(seeded_estate: Session) -> None:
    """VerifyKart is assigned only 1001-1003; scope is checked, ownership
    of 1004 is not."""
    engagement = seeded_estate.scalar(select(Engagement).order_by(Engagement.id).limit(1))
    assert engagement is not None
    results = _run(seeded_estate, engagement.id)

    result = results["DPDP-06-02"]
    assert result.verdict == Verdict.FAIL.value
    exception = _detail(result)["exceptions"][0]
    assert exception["customer_id"] == 1004
    assert exception["allowed"] is True

    seeded_estate.rollback()


def test_s3_nan_bypasses_the_spend_cap_guard(seeded_estate: Session) -> None:
    engagement = seeded_estate.scalar(select(Engagement).order_by(Engagement.id).limit(1))
    assert engagement is not None
    results = _run(seeded_estate, engagement.id)

    result = results["DPDP-06-03"]
    assert result.verdict == Verdict.FAIL.value
    detail = _detail(result)
    assert detail["exceptions"][0]["case"] == "nan"
    # The comparison cases must behave correctly, or this is not a defect --
    # it is the check simply doing nothing.
    by_case = {a["case"]: a for a in detail["attempts"]}
    assert by_case["in_range"]["accepted"] is True
    assert by_case["overflow"]["accepted"] is False

    seeded_estate.rollback()


def test_a_refusal_the_defect_never_produces_is_still_checked_for_a_log(
    seeded_estate: Session,
) -> None:
    """The S2 defect means every ownership attempt is ALLOWED, so this
    control's own probe (a principal with no read:customers scope at all)
    is what actually exercises the log-visibility gap: refused, but never
    logged."""
    engagement = seeded_estate.scalar(select(Engagement).order_by(Engagement.id).limit(1))
    assert engagement is not None
    results = _run(seeded_estate, engagement.id)

    result = results["DPDP-06-04"]
    assert result.verdict == Verdict.FAIL.value
    exceptions = _detail(result)["exceptions"]
    assert any(e.get("principal") == "EchoScribe Transcription" for e in exceptions)
    assert all(not e["was_logged"] for e in exceptions)

    seeded_estate.rollback()


def test_s4_a_425_day_stale_credential_still_authenticates(seeded_estate: Session) -> None:
    engagement = seeded_estate.scalar(select(Engagement).order_by(Engagement.id).limit(1))
    assert engagement is not None
    results = _run(seeded_estate, engagement.id)

    result = results["DPDP-TP-02"]
    assert result.verdict == Verdict.FAIL.value
    attempt = _detail(result)["attempt"]
    assert attempt["days_since_last_use"] == 425
    assert attempt["accepted"] is True

    seeded_estate.rollback()
