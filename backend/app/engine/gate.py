"""The Evidence Sufficiency Gate.

Every control result is Pass, Fail, or **Insufficient Evidence**, and the
third is a designed verdict rather than an error. The gate is what makes that
real: it runs *after* a test procedure has reported what it measured, and it
can override the outcome when the evidence cannot carry a conclusion.

The separation is deliberate. A procedure reports observations; it never
decides whether those observations are enough. Keeping the two apart is what
stops a suite author quietly widening a bound to make a control pass, because
the bound is not theirs to widen.

Two design choices worth stating:

**Structural reasons are evaluated before statistical ones.** A control with
no evidence at all should be reported as having no evidence, not as having
too small a sample. Different problems, different remedies.

**Every reason is collected, never short-circuited.** A control can be short
on sample *and* stale *and* narrow in coverage, and the reader needs all
three -- fixing one would leave the verdict unchanged and the reader puzzled.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from app.engine.stats import interval_width, wilson_interval
from app.engine.thresholds import Thresholds


class Verdict(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class GateReason(StrEnum):
    """Structured codes, never prose, so they can be counted and filtered."""

    G1_MIN_SAMPLE = "G1_MIN_SAMPLE"
    G2_CI_WIDTH = "G2_CI_WIDTH"
    G3_COVERAGE = "G3_COVERAGE"
    G4_MISSING_ARTIFACT = "G4_MISSING_ARTIFACT"
    G5_STALE_EVIDENCE = "G5_STALE_EVIDENCE"
    G6_NON_REPRESENTATIVE = "G6_NON_REPRESENTATIVE"
    G7_SOURCE_UNVERIFIED = "G7_SOURCE_UNVERIFIED"
    G8_TARGET_UNREACHABLE = "G8_TARGET_UNREACHABLE"


class InferenceMode(StrEnum):
    # Inference from a sample: the sampling rules apply.
    POPULATION = "POPULATION"
    # The probe set IS the population, so sample size, interval width and
    # coverage are not meaningful questions. Applying them would gate a
    # complete census for being "too small".
    CENSUS = "CENSUS"


class SampleFrame(StrEnum):
    RANDOM = "RANDOM"
    STRATIFIED = "STRATIFIED"
    CENSUS = "CENSUS"
    # Whatever was to hand. Says nothing about the rest of the population.
    CONVENIENCE = "CONVENIENCE"
    # Deliberately filtered, e.g. active accounts only. A clean result says
    # nothing about the dormant ones that were excluded.
    FILTERED = "FILTERED"


NON_REPRESENTATIVE_FRAMES = frozenset({SampleFrame.CONVENIENCE, SampleFrame.FILTERED})


@dataclass(frozen=True)
class RawResult:
    """What a procedure measured. Deliberately has no verdict field beyond
    the outcome it observed -- sufficiency is not its decision."""

    outcome: Verdict
    inference_mode: InferenceMode = InferenceMode.POPULATION

    sample_size: int | None = None
    population_size: int | None = None
    successes: int | None = None

    sample_frame: SampleFrame = SampleFrame.RANDOM
    evidence_age_days: int | None = None
    missing_required_evidence: tuple[str, ...] = ()
    attestation_only: bool = False
    target_unreachable: bool = False
    source_status: str = "VERIFIED"

    # Size of each subgroup a procedure compared, e.g. applicant groups in a
    # fairness test. Reported, not judged: the gate decides which are too
    # small to conclude from, against the (possibly overridden) threshold.
    subgroup_sizes: dict[str, int] = field(default_factory=dict)

    detail: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Reject impossible measurements where they are constructed.

        A procedure reporting more successes than trials, or a sample larger
        than its population, is broken. Letting that through would surface
        later as an obscure error inside the interval calculation, pointing at
        the statistics rather than at the suite that produced nonsense.
        """
        if self.sample_size is not None and self.sample_size < 0:
            raise ValueError(f"sample_size={self.sample_size} is negative")
        if (
            self.successes is not None
            and self.sample_size is not None
            and self.successes > self.sample_size
        ):
            raise ValueError(
                f"successes={self.successes} exceeds sample_size="
                f"{self.sample_size}; the procedure measured something impossible"
            )
        if (
            self.sample_size is not None
            and self.population_size is not None
            and self.sample_size > self.population_size
        ):
            raise ValueError(
                f"sample_size={self.sample_size} exceeds population_size="
                f"{self.population_size}"
            )


@dataclass(frozen=True)
class GateOutcome:
    """The gate's decision, carrying everything the UI and workpaper need to
    explain it. A gate that cannot say why is just a shrug."""

    verdict: Verdict
    raw_outcome: Verdict
    gate_fired: bool
    reasons: tuple[GateReason, ...]
    explanations: tuple[str, ...]
    remedies: tuple[str, ...]

    sample_size: int | None = None
    population_size: int | None = None
    successes: int | None = None
    coverage_pct: float | None = None
    point_estimate: float | None = None
    ci_lower: float | None = None
    ci_upper: float | None = None
    ci_method: str | None = None

    thresholds_applied: dict[str, Any] = field(default_factory=dict)
    threshold_overrides: dict[str, Any] = field(default_factory=dict)


def _statistics(raw: RawResult) -> dict[str, Any]:
    """Point estimate and interval, where the shape of the result supports
    one. A census of probes has no proportion to estimate."""
    stats: dict[str, Any] = {
        "sample_size": raw.sample_size,
        "population_size": raw.population_size,
        "successes": raw.successes,
        "coverage_pct": None,
        "point_estimate": None,
        "ci_lower": None,
        "ci_upper": None,
        "ci_method": None,
    }

    if raw.sample_size and raw.population_size:
        stats["coverage_pct"] = round(
            (raw.sample_size / raw.population_size) * 100.0, 3
        )

    if raw.successes is not None and raw.sample_size:
        lower, upper = wilson_interval(raw.successes, raw.sample_size)
        stats["point_estimate"] = round(raw.successes / raw.sample_size, 5)
        stats["ci_lower"] = round(lower, 5)
        stats["ci_upper"] = round(upper, 5)
        stats["ci_method"] = "wilson_95"

    return stats


def apply(
    raw: RawResult,
    thresholds: Thresholds,
    overrides: dict[str, Any] | None = None,
) -> GateOutcome:
    """Decide the verdict.

    Returns the procedure's own outcome when the evidence supports it, and
    INSUFFICIENT_EVIDENCE with reasons when it does not.
    """
    effective, applied_overrides = thresholds.with_overrides(overrides or {})

    reasons: list[GateReason] = []
    explanations: list[str] = []
    remedies: list[str] = []

    def note(reason: GateReason, why: str, how: str) -> None:
        reasons.append(reason)
        explanations.append(why)
        remedies.append(how)

    # --- Structural first --------------------------------------------------
    # These describe the absence of usable evidence. Reporting a missing
    # artifact as "sample too small" would send the reader to fix the wrong
    # thing.

    if raw.target_unreachable:
        note(
            GateReason.G8_TARGET_UNREACHABLE,
            "The system under test could not be reached, so no probe executed.",
            "Restore the target service and re-run. Absence of evidence is not "
            "evidence of a working control.",
        )

    if raw.missing_required_evidence:
        missing = ", ".join(raw.missing_required_evidence)
        note(
            GateReason.G4_MISSING_ARTIFACT,
            f"Required evidence was not obtained: {missing}.",
            f"Obtain {missing} from the evidence owner and re-run.",
        )

    if raw.attestation_only:
        note(
            GateReason.G4_MISSING_ARTIFACT,
            "The only evidence is an attestation that the control exists. An "
            "attestation is evidence about a control, not evidence that it "
            "operated.",
            "Obtain an artifact showing the control operating: a log, an "
            "exercise record, or a sampled population.",
        )

    if raw.source_status == "UNVERIFIED":
        note(
            GateReason.G7_SOURCE_UNVERIFIED,
            "The clause this control rests on could not be verified against "
            "its source instrument.",
            "Verify the clause text, or narrow the control to an obligation "
            "that is verified.",
        )

    if raw.evidence_age_days is not None and (
        raw.evidence_age_days > effective.max_evidence_age_days
    ):
        note(
            GateReason.G5_STALE_EVIDENCE,
            f"Newest evidence is {raw.evidence_age_days} days old, beyond the "
            f"{effective.max_evidence_age_days}-day limit.",
            "Re-perform the test to obtain current evidence. A control that "
            "operated last quarter is not evidence about this one.",
        )

    if raw.sample_frame in NON_REPRESENTATIVE_FRAMES:
        note(
            GateReason.G6_NON_REPRESENTATIVE,
            f"The sample frame is {raw.sample_frame.value.lower()}, so the "
            f"result does not extend to the population.",
            "Re-sample at random, or restate the control's scope to match the "
            "population actually tested.",
        )

    # --- Undersized subgroups ----------------------------------------------
    # A comparison across groups can only speak for the groups large enough
    # to support it. Applied only when the procedure found no exception:
    #
    # * a PASS would otherwise vouch for a group nobody could assess, so it
    #   gates, and says which group and why;
    # * a FAIL established among adequately sized groups stands. Gating it
    #   because some *other* group was small would hide a proven disparity
    #   behind a group that played no part in finding it.
    #
    # Either way the small group is never reported AS a disparity: the
    # procedure excludes it from the comparison and lists it as unassessed.
    undersized = sorted(
        (name, size) for name, size in raw.subgroup_sizes.items()
        if size < effective.min_group_n
    )
    if undersized and raw.outcome is Verdict.PASS:
        listed = ", ".join(f"{name} (n={size})" for name, size in undersized)
        note(
            GateReason.G1_MIN_SAMPLE,
            f"No conclusion can be drawn for {listed}: below the minimum group "
            f"size of {effective.min_group_n}. The other groups were compared.",
            f"Obtain at least {effective.min_group_n} decisions for each listed "
            f"group, or record why the group is out of scope.",
        )

    # --- Statistical -------------------------------------------------------
    # Only for controls inferring about a population from a sample. A census
    # has no sampling error to bound.

    if raw.inference_mode is InferenceMode.POPULATION:
        n = raw.sample_size or 0

        if n < effective.min_sample_n:
            note(
                GateReason.G1_MIN_SAMPLE,
                f"Sample size {n} is below the minimum of "
                f"{effective.min_sample_n} for a population conclusion.",
                f"Test at least {effective.min_sample_n} items.",
            )

        if n > 0 and raw.successes is not None:
            width = interval_width(raw.successes, n)
            if width > effective.max_ci_width:
                lower, upper = wilson_interval(raw.successes, n)
                note(
                    GateReason.G2_CI_WIDTH,
                    f"The 95% confidence interval spans {lower:.1%} to {upper:.1%} "
                    f"(width {width:.2f}), wider than the {effective.max_ci_width:.2f} "
                    f"limit. A result that broad does not distinguish a working "
                    f"control from a failing one.",
                    "Increase the sample until the interval narrows.",
                )

        if raw.population_size:
            coverage = (n / raw.population_size) * 100.0
            if coverage < effective.min_coverage_pct:
                needed = int(
                    (effective.min_coverage_pct / 100.0) * raw.population_size
                )
                note(
                    GateReason.G3_COVERAGE,
                    f"Tested {n:,} of {raw.population_size:,} items "
                    f"({coverage:.2f}% coverage), below the "
                    f"{effective.min_coverage_pct:.0f}% threshold.",
                    f"Sample at least {needed:,} items, or narrow the control's "
                    f"scope to a defined subpopulation and restate the objective.",
                )

    stats = _statistics(raw)
    fired = bool(reasons)

    return GateOutcome(
        verdict=Verdict.INSUFFICIENT_EVIDENCE if fired else raw.outcome,
        raw_outcome=raw.outcome,
        gate_fired=fired,
        reasons=tuple(reasons),
        explanations=tuple(explanations),
        remedies=tuple(remedies),
        thresholds_applied=effective.as_dict(),
        threshold_overrides=applied_overrides,
        **stats,
    )
