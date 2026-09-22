"""The Evidence Sufficiency Gate.

Each rule is tested in isolation, so a failure names the rule rather than
"the gate is broken". The composite behaviours -- ordering, collection, census
exemption -- are tested separately, because those are where a plausible
implementation goes subtly wrong.
"""

from __future__ import annotations

import dataclasses

import pytest

from app.engine.gate import (
    GateReason,
    InferenceMode,
    RawResult,
    SampleFrame,
    Verdict,
    apply,
)
from app.engine.thresholds import DEFAULT_THRESHOLDS, Thresholds

T = DEFAULT_THRESHOLDS


def sound(**overrides: object) -> RawResult:
    """A result with evidence good enough to conclude from.

    Every test below starts here and breaks exactly one thing, so a firing
    gate can only be attributed to what that test changed.
    """
    base = {
        "outcome": Verdict.PASS,
        "sample_size": 400,
        "population_size": 1_000,
        "successes": 396,
        "evidence_age_days": 5,
        "sample_frame": SampleFrame.RANDOM,
    }
    return RawResult(**{**base, **overrides})  # type: ignore[arg-type]


def test_the_baseline_passes_cleanly() -> None:
    """Without this, every test below could pass for the wrong reason."""
    outcome = apply(sound(), T)

    assert outcome.verdict is Verdict.PASS
    assert outcome.gate_fired is False
    assert outcome.reasons == ()


def test_a_failing_control_still_fails() -> None:
    """The gate is not a filter that turns everything into uncertainty. Good
    evidence of a broken control is a FAIL, and must survive."""
    outcome = apply(sound(outcome=Verdict.FAIL, successes=12), T)

    assert outcome.verdict is Verdict.FAIL
    assert outcome.gate_fired is False


# --- Each rule in isolation -------------------------------------------------


def test_g1_sample_below_minimum() -> None:
    outcome = apply(
        sound(sample_size=10, population_size=20, successes=10), T
    )

    assert GateReason.G1_MIN_SAMPLE in outcome.reasons
    assert outcome.verdict is Verdict.INSUFFICIENT_EVIDENCE


def test_g2_interval_too_wide() -> None:
    """Twelve of twelve: a perfect score that cannot support a conclusion.

    Population is set so coverage passes, isolating the width rule.
    """
    outcome = apply(
        sound(sample_size=12, population_size=40, successes=12), T
    )

    assert GateReason.G2_CI_WIDTH in outcome.reasons
    assert GateReason.G3_COVERAGE not in outcome.reasons


def test_g3_coverage_below_threshold() -> None:
    """Sample size and coverage disagree: 400 items is a real sample and
    0.4% of 100,000."""
    outcome = apply(sound(sample_size=400, population_size=100_000), T)

    assert GateReason.G3_COVERAGE in outcome.reasons
    assert GateReason.G1_MIN_SAMPLE not in outcome.reasons, "n=400 is ample"


def test_g4_missing_required_evidence() -> None:
    outcome = apply(sound(missing_required_evidence=("access_logs",)), T)

    assert GateReason.G4_MISSING_ARTIFACT in outcome.reasons
    assert "access_logs" in " ".join(outcome.explanations)


def test_g4_attestation_alone_is_never_enough() -> None:
    """The failure mode of every questionnaire-based compliance tool.

    Someone confirming a control exists is evidence *about* the control. It is
    not evidence that the control operated, and a tool that treats the two as
    interchangeable produces a green dashboard over an untested estate.
    """
    outcome = apply(sound(attestation_only=True), T)

    assert GateReason.G4_MISSING_ARTIFACT in outcome.reasons
    assert outcome.verdict is Verdict.INSUFFICIENT_EVIDENCE


def test_g5_stale_evidence() -> None:
    outcome = apply(sound(evidence_age_days=200), T)

    assert GateReason.G5_STALE_EVIDENCE in outcome.reasons


def test_g5_boundary_is_inclusive() -> None:
    """Evidence exactly at the limit is still current. An off-by-one here
    would gate a control tested on the ninetieth day."""
    assert apply(sound(evidence_age_days=90), T).gate_fired is False
    assert apply(sound(evidence_age_days=91), T).gate_fired is True


@pytest.mark.parametrize(
    "frame", [SampleFrame.CONVENIENCE, SampleFrame.FILTERED]
)
def test_g6_non_representative_frame(frame: SampleFrame) -> None:
    """Testing only active accounts says nothing about dormant ones -- and
    dormant accounts are exactly where retention failures live."""
    outcome = apply(sound(sample_frame=frame), T)

    assert GateReason.G6_NON_REPRESENTATIVE in outcome.reasons


@pytest.mark.parametrize(
    "frame", [SampleFrame.RANDOM, SampleFrame.STRATIFIED, SampleFrame.CENSUS]
)
def test_representative_frames_do_not_fire(frame: SampleFrame) -> None:
    assert apply(sound(sample_frame=frame), T).gate_fired is False


def test_g7_unverified_source() -> None:
    """The product applies its own honesty rule to itself: a control whose
    legal basis could not be verified does not get to assert a result."""
    outcome = apply(sound(source_status="UNVERIFIED"), T)

    assert GateReason.G7_SOURCE_UNVERIFIED in outcome.reasons


def test_g8_target_unreachable_never_passes() -> None:
    """The most dangerous failure this product could have.

    If the target is down and the gate did not fire, every access-control
    probe would report PASS -- a confidently green assurance report produced
    by testing nothing at all.
    """
    outcome = apply(
        sound(outcome=Verdict.PASS, target_unreachable=True), T
    )

    assert GateReason.G8_TARGET_UNREACHABLE in outcome.reasons
    assert outcome.verdict is Verdict.INSUFFICIENT_EVIDENCE
    assert outcome.verdict is not Verdict.PASS


# --- Composite behaviour ---------------------------------------------------


def test_all_reasons_are_collected_not_short_circuited() -> None:
    """Fixing one of four problems would leave the verdict unchanged. A
    reader shown only the first reason would not understand why."""
    outcome = apply(
        sound(
            sample_size=5,
            population_size=10_000,
            successes=5,
            evidence_age_days=400,
            sample_frame=SampleFrame.CONVENIENCE,
        ),
        T,
    )

    assert {
        GateReason.G1_MIN_SAMPLE,
        GateReason.G2_CI_WIDTH,
        GateReason.G3_COVERAGE,
        GateReason.G5_STALE_EVIDENCE,
        GateReason.G6_NON_REPRESENTATIVE,
    } <= set(outcome.reasons)


def test_structural_reasons_come_before_statistical_ones() -> None:
    """A control with no evidence should be reported as having none, not as
    having too small a sample. Different problems, different remedies -- and
    the first reason shown is the one a reader acts on."""
    outcome = apply(
        sound(
            sample_size=2, population_size=9_000, successes=2,
            target_unreachable=True,
        ),
        T,
    )

    assert outcome.reasons[0] is GateReason.G8_TARGET_UNREACHABLE


def test_every_reason_carries_an_explanation_and_a_remedy() -> None:
    """A gate that cannot say how to clear it is an excuse."""
    outcome = apply(
        sound(sample_size=3, population_size=9_000, successes=3), T
    )

    assert len(outcome.explanations) == len(outcome.reasons)
    assert len(outcome.remedies) == len(outcome.reasons)
    assert all(e.strip() for e in outcome.explanations)
    assert all(r.strip() for r in outcome.remedies)


def test_the_remedy_is_actionable_not_generic() -> None:
    """It should name the number that would clear the gate."""
    outcome = apply(sound(sample_size=400, population_size=100_000), T)

    coverage_remedy = next(
        r for reason, r in zip(outcome.reasons, outcome.remedies, strict=True)
        if reason is GateReason.G3_COVERAGE
    )
    assert "10,000" in coverage_remedy


# --- Census ----------------------------------------------------------------


def test_census_skips_the_sampling_rules() -> None:
    """The probe set IS the population. Gating a complete census for being
    too small would make the access-control suite permanently ungradable."""
    outcome = apply(
        RawResult(
            outcome=Verdict.FAIL,
            inference_mode=InferenceMode.CENSUS,
            sample_size=8,
            population_size=8,
            successes=6,
            sample_frame=SampleFrame.CENSUS,
        ),
        T,
    )

    assert outcome.gate_fired is False
    assert outcome.verdict is Verdict.FAIL


def test_census_still_honours_structural_rules() -> None:
    """A census of nothing is still nothing. G8 must apply."""
    outcome = apply(
        RawResult(
            outcome=Verdict.PASS,
            inference_mode=InferenceMode.CENSUS,
            target_unreachable=True,
            sample_frame=SampleFrame.CENSUS,
        ),
        T,
    )

    assert outcome.verdict is Verdict.INSUFFICIENT_EVIDENCE
    assert GateReason.G8_TARGET_UNREACHABLE in outcome.reasons


# --- Statistics carried with the verdict -----------------------------------


def test_statistics_travel_with_the_result() -> None:
    """A conclusion has to be reproducible from its own record."""
    outcome = apply(sound(sample_size=400, population_size=1_000, successes=396), T)

    assert outcome.sample_size == 400
    assert outcome.population_size == 1_000
    assert outcome.coverage_pct == pytest.approx(40.0)
    assert outcome.point_estimate == pytest.approx(0.99, abs=1e-4)
    assert outcome.ci_method == "wilson_95"
    assert 0 < outcome.ci_lower < outcome.ci_upper <= 1  # type: ignore[operator]


def test_raw_outcome_is_preserved_when_the_gate_overrides() -> None:
    """"Would have passed, but coverage was 0.4%" is a different statement
    from "failed", and the workpaper needs to make that distinction."""
    outcome = apply(sound(sample_size=400, population_size=100_000), T)

    assert outcome.verdict is Verdict.INSUFFICIENT_EVIDENCE
    assert outcome.raw_outcome is Verdict.PASS


# --- Threshold overrides ---------------------------------------------------


def test_an_override_is_recorded_not_silent() -> None:
    """Quietly widening a bound to turn INSUFFICIENT_EVIDENCE into PASS is the
    one manoeuvre that would hollow this product out. It is made loud: the
    change travels on the result and is printed in the workpaper."""
    outcome = apply(
        sound(sample_size=400, population_size=100_000),
        T,
        overrides={"min_coverage_pct": 0.1},
    )

    assert outcome.verdict is Verdict.PASS
    assert outcome.threshold_overrides == {
        "min_coverage_pct": {"default": 10.0, "override": 0.1}
    }


def test_an_override_matching_the_default_is_not_recorded_as_a_change() -> None:
    outcome = apply(sound(), T, overrides={"min_coverage_pct": 10.0})

    assert outcome.threshold_overrides == {}


def test_an_unknown_override_raises_rather_than_being_ignored() -> None:
    """A typo would otherwise leave the default silently in place, and the
    workpaper would report a threshold that was never applied."""
    with pytest.raises(ValueError, match="unknown threshold override"):
        apply(sound(), T, overrides={"min_covrage_pct": 1.0})


def test_thresholds_applied_are_recorded_in_full() -> None:
    outcome = apply(sound(), T)

    assert outcome.thresholds_applied["min_sample_n"] == 30
    assert outcome.thresholds_applied["max_ci_width"] == 0.20
    assert outcome.thresholds_applied["fairness_ratio_threshold"] == 0.80


def test_thresholds_are_immutable() -> None:
    """An override produces a new instance, so a threshold cannot change
    part-way through a run."""
    with pytest.raises(dataclasses.FrozenInstanceError):
        T.min_sample_n = 5  # type: ignore[misc]


def test_overrides_do_not_leak_between_calls() -> None:
    apply(sound(), T, overrides={"min_sample_n": 1})
    outcome = apply(sound(sample_size=5, population_size=10, successes=5), T)

    assert GateReason.G1_MIN_SAMPLE in outcome.reasons


# --- Degenerate inputs -----------------------------------------------------


def test_no_evidence_at_all_gates_rather_than_crashing() -> None:
    outcome = apply(RawResult(outcome=Verdict.PASS), Thresholds())

    assert outcome.verdict is Verdict.INSUFFICIENT_EVIDENCE
    assert GateReason.G1_MIN_SAMPLE in outcome.reasons


def test_not_applicable_is_left_alone() -> None:
    """A control scoped out on legal applicability is not an evidence
    question, and the gate must not convert it into one."""
    outcome = apply(
        RawResult(
            outcome=Verdict.NOT_APPLICABLE,
            inference_mode=InferenceMode.CENSUS,
            sample_frame=SampleFrame.CENSUS,
        ),
        T,
    )

    assert outcome.verdict is Verdict.NOT_APPLICABLE


# --- Impossible measurements -----------------------------------------------


def test_more_successes_than_trials_is_rejected_at_construction() -> None:
    """Caught where it is produced, so the error names the broken procedure
    rather than surfacing inside the interval calculation."""
    with pytest.raises(ValueError, match="impossible"):
        RawResult(outcome=Verdict.PASS, sample_size=10, successes=11)


def test_sample_larger_than_population_is_rejected() -> None:
    with pytest.raises(ValueError, match="exceeds population_size"):
        RawResult(outcome=Verdict.PASS, sample_size=100, population_size=10)
