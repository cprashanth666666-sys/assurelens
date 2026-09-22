"""The arithmetic the gate's verdicts rest on.

Two independent checks on the Wilson interval, because "it matches what I
computed" is circular when I wrote both sides:

1. Against published values.
2. Against the score equation the bounds are defined to solve. This one does
   not depend on the implementation at all -- it substitutes the returned
   bounds back into the definition and checks they satisfy it.

A wrong implementation would have to be wrong in a way that still solves the
equation, which is to say it would have to be right.
"""

from __future__ import annotations

import math

import pytest

from app.engine.stats import (
    PSI_EPSILON,
    Z_95,
    bin_counts,
    coverage_percent,
    interval_width,
    population_stability_index,
    quantile_bin_edges,
    selection_rate_ratio,
    wilson_interval,
)

# --- Check 1: published values ---------------------------------------------


@pytest.mark.parametrize(
    ("successes", "trials", "lower", "upper"),
    [
        # The case Wald gets catastrophically wrong: it reports (0, 0) and
        # claims certainty from ten observations.
        (0, 10, 0.0000, 0.2775),
        (10, 10, 0.7225, 1.0000),
        (5, 10, 0.2366, 0.7634),
        (1, 20, 0.0089, 0.2361),
        (50, 100, 0.4038, 0.5962),
    ],
)
def test_wilson_matches_published_values(
    successes: int, trials: int, lower: float, upper: float
) -> None:
    got_lower, got_upper = wilson_interval(successes, trials)

    assert got_lower == pytest.approx(lower, abs=5e-5)
    assert got_upper == pytest.approx(upper, abs=5e-5)


# --- Check 2: the bounds solve the equation that defines them --------------


@pytest.mark.parametrize(
    ("successes", "trials"),
    [(1, 10), (3, 17), (5, 10), (12, 40), (99, 200), (7, 31)],
)
def test_bounds_solve_the_score_equation(successes: int, trials: int) -> None:
    """A Wilson bound p satisfies |p_hat - p| / sqrt(p(1-p)/n) = z.

    Substituting the returned bounds back into that definition is a check on
    the result, not on the code that produced it.
    """
    p_hat = successes / trials
    lower, upper = wilson_interval(successes, trials)

    for bound in (lower, upper):
        assert 0 < bound < 1, "this case should not be at a boundary"
        standard_error = math.sqrt(bound * (1 - bound) / trials)
        assert abs(p_hat - bound) / standard_error == pytest.approx(Z_95, abs=1e-9)


def test_interval_contains_the_point_estimate() -> None:
    for trials in (5, 10, 30, 100):
        for successes in range(trials + 1):
            lower, upper = wilson_interval(successes, trials)
            assert lower <= successes / trials <= upper


def test_interval_narrows_as_evidence_grows() -> None:
    """The property the whole gate depends on: more observations, tighter
    conclusion. If this failed, sample size would carry no information."""
    widths = [interval_width(n // 2, n) for n in (10, 40, 160, 640)]

    assert widths == sorted(widths, reverse=True)


def test_extremes_never_collapse_to_zero_width() -> None:
    """The reason Wald was rejected. At p=0 and p=1 the normal approximation
    reports a point, which is a claim of certainty from finite evidence."""
    for trials in (5, 10, 30, 100, 1000):
        assert interval_width(0, trials) > 0
        assert interval_width(trials, trials) > 0


# --- The two cases the gate's thresholds turn on ---------------------------


def test_twelve_of_twelve_is_not_a_conclusion() -> None:
    """A perfect score on twelve observations looks conclusive and is not.

    This is the single example that justifies the interval-width rule, so the
    number is pinned here: if it ever drifts below the 0.20 threshold the gate
    silently stops catching this case.
    """
    lower, upper = wilson_interval(12, 12)

    assert upper == 1.0
    assert lower == pytest.approx(0.7575, abs=5e-5)
    assert interval_width(12, 12) == pytest.approx(0.2425, abs=5e-5)
    assert interval_width(12, 12) > 0.20, "must fail the width threshold"


def test_thirty_of_thirty_is_a_conclusion() -> None:
    """The contrast case. Without it, the width rule could be satisfied by an
    implementation that simply rejects everything."""
    assert interval_width(30, 30) == pytest.approx(0.1135, abs=5e-5)
    assert interval_width(30, 30) < 0.20


def test_zero_trials_raises_rather_than_returning_something() -> None:
    """No observations is not a wide interval; it is the absence of one.

    Returning (0, 1) here would let a control with no evidence at all flow
    into the statistical rules and be judged merely imprecise.
    """
    with pytest.raises(ValueError):
        wilson_interval(0, 0)


def test_successes_above_trials_raises() -> None:
    with pytest.raises(ValueError):
        wilson_interval(11, 10)


# --- Coverage --------------------------------------------------------------


def test_coverage_is_not_sample_size() -> None:
    """200 records sounds like a real sample and is 0.83% of the estate."""
    assert coverage_percent(200, 24_000) == pytest.approx(0.8333, abs=1e-4)
    assert coverage_percent(24_000, 24_000) == 100.0


def test_coverage_of_an_empty_population_raises() -> None:
    with pytest.raises(ValueError):
        coverage_percent(0, 0)


# --- PSI -------------------------------------------------------------------


def test_identical_distributions_have_zero_drift() -> None:
    counts = [10.0, 20.0, 30.0, 25.0, 15.0]

    assert population_stability_index(counts, counts) == pytest.approx(0.0, abs=1e-9)


def test_psi_is_scale_invariant() -> None:
    """Counts and proportions must give the same answer, so a caller cannot
    produce a wrong number by mixing the two."""
    counts = [10.0, 20.0, 30.0, 40.0]
    proportions = [0.1, 0.2, 0.3, 0.4]
    shifted = [40.0, 30.0, 20.0, 10.0]

    assert population_stability_index(counts, shifted) == pytest.approx(
        population_stability_index(proportions, shifted), abs=1e-9
    )


def test_psi_grows_with_divergence() -> None:
    base = [25.0, 25.0, 25.0, 25.0]
    mild = [30.0, 25.0, 22.0, 23.0]
    severe = [70.0, 20.0, 7.0, 3.0]

    assert (
        population_stability_index(base, base)
        < population_stability_index(base, mild)
        < population_stability_index(base, severe)
    )


def test_an_empty_bin_does_not_produce_infinity() -> None:
    """Without smoothing this is a division by zero wearing a number's
    clothes: ln(0) diverges and PSI reports infinite drift, which reads as a
    dramatic finding and measures nothing."""
    expected = [50.0, 50.0, 0.0]
    actual = [40.0, 40.0, 20.0]

    psi = population_stability_index(expected, actual)

    assert math.isfinite(psi)
    assert psi > 0


def test_smoothing_is_small_enough_not_to_distort() -> None:
    """The epsilon must rescue the degenerate case without moving ordinary
    answers. Compared against a run with a far smaller epsilon."""
    expected = [30.0, 40.0, 30.0]
    actual = [25.0, 45.0, 30.0]

    with_default = population_stability_index(expected, actual)
    with_tiny = population_stability_index(expected, actual, epsilon=1e-12)

    assert with_default == pytest.approx(with_tiny, abs=1e-5)
    assert PSI_EPSILON < 1e-4


def test_mismatched_bin_counts_raise() -> None:
    with pytest.raises(ValueError):
        population_stability_index([1.0, 2.0], [1.0, 2.0, 3.0])


def test_empty_distribution_raises() -> None:
    with pytest.raises(ValueError):
        population_stability_index([0.0, 0.0], [1.0, 1.0])


# --- Binning ---------------------------------------------------------------


def test_quantile_bins_spread_a_skewed_feature() -> None:
    """Equal-width bins on a skewed feature put nearly everything in one bin,
    and PSI then reports stability because the binning hid the movement."""
    skewed = [1.0] * 90 + [100.0] * 10
    edges = quantile_bin_edges(skewed, bins=5)
    counts = bin_counts(skewed, edges)

    assert sum(counts) == len(skewed)
    assert len(counts) == 5


def test_every_observation_lands_in_exactly_one_bin() -> None:
    values = [float(v) for v in range(100)]
    edges = quantile_bin_edges(values, bins=10)

    assert sum(bin_counts(values, edges)) == len(values)


def test_values_outside_the_training_range_are_not_dropped() -> None:
    """Drift is exactly the case where live values fall outside the range seen
    at training. Silently discarding them would hide the drift being measured."""
    edges = quantile_bin_edges([float(v) for v in range(10)], bins=4)
    beyond = [-50.0, 999.0]

    assert sum(bin_counts(beyond, edges)) == len(beyond)


# --- Fairness --------------------------------------------------------------


def test_selection_rate_ratio() -> None:
    assert selection_rate_ratio({"A": 0.62, "B": 0.58, "C": 0.44}) == pytest.approx(
        0.44 / 0.62
    )


def test_ratio_of_one_when_all_groups_match() -> None:
    assert selection_rate_ratio({"A": 0.5, "B": 0.5}) == 1.0


def test_ratio_with_no_selections_anywhere_raises() -> None:
    """Zero over zero is not parity; it is no evidence."""
    with pytest.raises(ValueError):
        selection_rate_ratio({"A": 0.0, "B": 0.0})
