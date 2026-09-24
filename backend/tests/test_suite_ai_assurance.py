"""Suite 5, AI assurance. [Day 7]

Acceptance, restated as tests:

* S7 detected: the lowest group's selection rate is under four-fifths of the
  highest (designed at 0.71; measured 0.6955 at seed 42).
* S8 detected: exactly two features drift past PSI 0.25, and nothing
  monitors drift.
* The 22-member group is reported as too small to conclude from, never as a
  disparity.
* Leakage is only ever "suspected", and never decides the verdict.

Unit tests first (no database), then the procedures against the seeded estate.
"""

from __future__ import annotations

import datetime as dt
import math
import random
from typing import Any

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import suites as _suites  # noqa: F401  registers procedures
from app.engine import gate as gate_module
from app.engine.collectors import default_broker
from app.engine.evidence import EvidenceBundle, EvidenceItem, EvidenceKind
from app.engine.gate import GateReason, InferenceMode, RawResult, SampleFrame, Verdict
from app.engine.runner import get_procedure, run_suites
from app.engine.thresholds import Thresholds
from app.models.control import Engagement
from app.models.estate import ModelAssessment
from app.models.results import TestResult
from app.suites.ai_assurance import (
    baseline_edges,
    drift_report,
    fairness_report,
    psi_band,
    validation_report,
)
from app.suites.evidence_sources import collect_model_predictions, collect_model_registry

T = Thresholds()


def rows(
    group: str, n: int, approved: int, qualified: int = 0, qualified_approved: int = 0
) -> list[dict[str, Any]]:
    """`n` decisions for one group: `approved` approvals in total, of which
    `qualified_approved` go to the first `qualified` rows (those with a
    REPAID ground truth) and the rest to rows without one."""
    out = []
    for i in range(n):
        in_qualified = i < qualified_approved
        in_rest = qualified <= i < qualified + approved - qualified_approved
        out.append({
            "group": group,
            "decision": "APPROVE" if in_qualified or in_rest else "DECLINE",
            "ground_truth": "REPAID" if i < qualified else None,
            "principal_id": f"{group}{i}",
        })
    return out


# --- Fairness (unit) -----------------------------------------------------------


def test_ratio_is_lowest_over_highest_among_adequately_sized_groups() -> None:
    preds = rows("A", 100, 60) + rows("B", 100, 42)
    report = fairness_report(preds)
    assert report["selection_rate_ratio"] == pytest.approx(0.42 / 0.60, abs=1e-4)
    assert report["lowest_group"] == "B" and report["highest_group"] == "A"
    assert report["demographic_parity_difference"] == pytest.approx(0.18, abs=1e-4)


def test_a_small_group_is_never_part_of_the_comparison() -> None:
    # Group D would produce a dramatic ratio (0.05 / 0.60) if it were counted.
    preds = rows("A", 100, 60) + rows("B", 100, 57) + rows("D", 20, 1)
    report = fairness_report(preds)
    d = next(g for g in report["groups"] if g["group"] == "D")
    assert d["status"] == "too small to conclude"
    assert report["unassessed_groups"] == ["D"]
    assert report["selection_rate_ratio"] == pytest.approx(0.95, abs=1e-4)
    # It still gets an interval, so the reader can see how wide it is.
    assert d["ci_lower"] is not None and d["ci_upper"] - d["ci_lower"] > 0.15


def test_a_group_at_exactly_the_minimum_is_compared() -> None:
    report = fairness_report(rows("A", 30, 15) + rows("B", 30, 15))
    assert all(g["status"] == "compared" for g in report["groups"])


def test_equal_opportunity_uses_only_applicants_with_known_good_outcomes() -> None:
    preds = rows("A", 200, 120, qualified=100, qualified_approved=90) + rows(
        "B", 200, 120, qualified=100, qualified_approved=60
    )
    eo = fairness_report(preds)["equal_opportunity"]
    assert eo["difference"] == pytest.approx(0.30, abs=1e-4)


def test_equal_opportunity_is_not_computable_without_ground_truth() -> None:
    eo = fairness_report(rows("A", 50, 25) + rows("B", 50, 25))["equal_opportunity"]
    assert eo["difference"] is None
    assert "not computable" in eo["basis"]


def test_missing_group_is_reported_as_unrecorded_not_dropped() -> None:
    preds = [*rows("A", 40, 20), {"group": None, "decision": "APPROVE", "ground_truth": None}]
    labels = [g["group"] for g in fairness_report(preds)["groups"]]
    assert "unrecorded" in labels


# --- The gate's subgroup rule (unit) --------------------------------------------


def _raw(outcome: Verdict, sizes: dict[str, int]) -> RawResult:
    return RawResult(outcome=outcome, inference_mode=InferenceMode.CENSUS,
                     sample_frame=SampleFrame.CENSUS, sample_size=100,
                     population_size=100, subgroup_sizes=sizes)


def test_a_pass_that_would_vouch_for_a_small_group_is_gated() -> None:
    outcome = gate_module.apply(_raw(Verdict.PASS, {"A": 500, "D": 22}), T)
    assert outcome.verdict is Verdict.INSUFFICIENT_EVIDENCE
    assert outcome.reasons == (GateReason.G1_MIN_SAMPLE,)
    assert "D (n=22)" in outcome.explanations[0]


def test_a_disparity_proven_among_sized_groups_is_not_hidden_by_a_small_one() -> None:
    outcome = gate_module.apply(_raw(Verdict.FAIL, {"A": 500, "C": 400, "D": 22}), T)
    assert outcome.verdict is Verdict.FAIL
    assert not outcome.gate_fired


def test_all_groups_sized_passes_untouched() -> None:
    outcome = gate_module.apply(_raw(Verdict.PASS, {"A": 500, "B": 400}), T)
    assert outcome.verdict is Verdict.PASS


def test_the_group_minimum_follows_an_override() -> None:
    outcome = gate_module.apply(_raw(Verdict.PASS, {"A": 500, "D": 22}), T, {"min_group_n": 20})
    assert outcome.verdict is Verdict.PASS
    assert outcome.threshold_overrides == {"min_group_n": {"default": 30, "override": 20}}


# --- Drift (unit) ----------------------------------------------------------------


def test_baseline_edges_split_the_training_distribution_into_deciles() -> None:
    edges = baseline_edges(10.0, 2.0)
    assert len(edges) == 11 and edges[0] == -math.inf and edges[-1] == math.inf
    assert edges[5] == pytest.approx(10.0)


def test_data_drawn_from_the_baseline_is_stable() -> None:
    rng = random.Random(7)
    preds = [{"features": {"x": rng.gauss(50, 10)}} for _ in range(5000)]
    report = drift_report(preds, {"features": {"x": {"mean": 50, "sd": 10}}})
    assert report["features"][0]["band"] == "stable"
    assert report["significant"] == []


def test_a_shifted_distribution_is_significant() -> None:
    rng = random.Random(7)
    preds = [{"features": {"x": rng.gauss(65, 10)}} for _ in range(5000)]
    report = drift_report(preds, {"features": {"x": {"mean": 50, "sd": 10}}})
    assert report["significant"] == ["x"]


def test_a_feature_with_no_baseline_is_named_not_assumed_stable() -> None:
    preds = [{"features": {"x": 1.0, "new_input": 2.0}} for _ in range(10)]
    report = drift_report(preds, {"features": {"x": {"mean": 1, "sd": 1}}})
    assert report["without_baseline"] == ["new_input"]


def test_psi_bands_follow_the_thresholds() -> None:
    assert psi_band(0.05) == "stable"
    assert psi_band(0.10) == "moderate"
    assert psi_band(0.25) == "moderate"
    assert psi_band(0.26) == "significant"


# --- Validation and leakage (unit) ---------------------------------------------


def test_a_feature_that_encodes_the_outcome_is_suspected_not_convicted() -> None:
    rng = random.Random(3)
    preds = []
    for i in range(400):
        repaid = rng.random() < 0.8
        preds.append({
            "principal_id": i,
            "ground_truth": "REPAID" if repaid else "DEFAULTED",
            "features": {"days_past_due_after_decision": 0.0 if repaid else 90.0,
                         "income_band": rng.gauss(6, 2)},
        })
    screen = validation_report(preds)["leakage_screen"]
    assert screen["suspected"] == ["days_past_due_after_decision"]
    assert "review" in screen["note"]


def test_null_rates_and_duplicates_are_counted() -> None:
    preds = [{"principal_id": 1, "features": {"x": 1.0}},
             {"principal_id": 1, "features": {"x": None}},
             {"principal_id": 2, "features": {}}]
    report = validation_report(preds)
    assert report["features_over_null_limit"] == ["x"]
    assert report["duplicate_principals"] == 1


def test_missing_training_baseline_is_missing_evidence_not_stability() -> None:
    now = dt.datetime.now(dt.UTC)
    bundle = EvidenceBundle(items={
        "model_predictions": EvidenceItem("model_predictions", EvidenceKind.DB_QUERY, "q",
                                          [{"model_id": 1, "features": {"x": 1.0}}], now, "h"),
        "model_registry": EvidenceItem("model_registry", EvidenceKind.DB_QUERY, "q",
                                       [{"id": 1, "name": "M", "is_consequential": True,
                                         "training_snapshot": None}], now, "h"),
    })
    raw = get_procedure("ai.input_drift_psi").execute(bundle, {})  # type: ignore[union-attr]
    outcome = gate_module.apply(raw, T)
    assert outcome.verdict is Verdict.INSUFFICIENT_EVIDENCE
    assert outcome.reasons == (GateReason.G4_MISSING_ARTIFACT,)


# --- Against the seeded estate -------------------------------------------------


def _bundle(db: Session) -> EvidenceBundle:
    now = dt.datetime.now(dt.UTC)
    ctx = {"db": db}
    return EvidenceBundle(items={
        "model_predictions": EvidenceItem("model_predictions", EvidenceKind.DB_QUERY, "q",
                                          collect_model_predictions(ctx), now, "h"),
        "model_registry": EvidenceItem("model_registry", EvidenceKind.DB_QUERY, "q",
                                       collect_model_registry(ctx), now, "h"),
    })


@pytest.mark.usefixtures("seeded_estate")
def test_s7_selection_rate_ratio_below_four_fifths(seeded_estate: Session) -> None:
    raw = get_procedure("ai.fairness_selection_rate").execute(_bundle(seeded_estate), {})  # type: ignore[union-attr]
    report = raw.detail["fairness"]
    assert raw.outcome is Verdict.FAIL
    assert report["lowest_group"] == "C" and report["highest_group"] == "A"
    # Designed at 0.44 / 0.62 = 0.71; the seed draws each decision, so the
    # measured ratio is what the result reports.
    assert report["selection_rate_ratio"] == pytest.approx(0.6955, abs=1e-4)
    assert gate_module.apply(raw, T).verdict is Verdict.FAIL


@pytest.mark.usefixtures("seeded_estate")
def test_the_22_member_group_gates_rather_than_reporting_a_disparity(
    seeded_estate: Session,
) -> None:
    raw = get_procedure("ai.fairness_selection_rate").execute(_bundle(seeded_estate), {})  # type: ignore[union-attr]
    d = next(g for g in raw.detail["fairness"]["groups"] if g["group"] == "D")
    assert d["n"] == 22
    assert d["status"] == "too small to conclude"
    assert raw.detail["fairness"]["unassessed_groups"] == ["D"]
    assert raw.subgroup_sizes["D"] == 22


@pytest.mark.usefixtures("seeded_estate")
def test_s8_exactly_two_features_drift_and_nothing_monitors_them(seeded_estate: Session) -> None:
    raw = get_procedure("ai.input_drift_psi").execute(_bundle(seeded_estate), {})  # type: ignore[union-attr]
    drift = raw.detail["drift"]
    assert raw.outcome is Verdict.FAIL
    assert sorted(drift["significant"]) == ["enquiries_6m", "utilisation_ratio"]
    assert all(f["psi"] > 0.25 for f in drift["features"] if f["feature"] in drift["significant"])
    assert raw.detail["has_drift_monitoring"] is False
    assert any("No drift monitoring" in e for e in raw.detail["exceptions"])
    # The clean features really are clean: this is not a test that fails everything.
    assert {f["feature"] for f in drift["features"] if f["band"] == "stable"} == {
        "income_band", "months_at_address"}


@pytest.mark.usefixtures("seeded_estate")
def test_no_leakage_is_suspected_in_the_seeded_model(seeded_estate: Session) -> None:
    raw = get_procedure("ai.input_drift_psi").execute(_bundle(seeded_estate), {})  # type: ignore[union-attr]
    assert raw.detail["validation"]["leakage_screen"]["suspected"] == []


@pytest.mark.usefixtures("seeded_estate")
def test_a_run_persists_model_assessments_with_group_sizes(seeded_estate: Session) -> None:
    engagement = seeded_estate.scalar(select(Engagement).order_by(Engagement.id).limit(1))
    assert engagement is not None
    run = run_suites(seeded_estate, engagement.id, ["ai_assurance"], seed=42,
                     broker=default_broker(), engine_version="test")
    seeded_estate.flush()

    # Every run also records scoped-out controls (DPDP-08-04) as not
    # applicable; only the two model controls are under test here.
    results = [
        r for r in seeded_estate.scalars(select(TestResult).where(TestResult.run_id == run.id))
        if r.detail.get("model") == "MFS-CPS-v3"
    ]
    assert len(results) == 2
    assert {r.verdict for r in results} == {"FAIL"}

    rows = seeded_estate.scalars(
        select(ModelAssessment).where(ModelAssessment.result_id.in_([r.id for r in results]))
    ).all()
    d = next(r for r in rows if r.metric == "selection_rate" and r.group_label == "D")
    assert d.group_n == 22
    assert {r.feature for r in rows if r.metric == "psi"} == {
        "enquiries_6m", "income_band", "months_at_address", "utilisation_ratio"}
