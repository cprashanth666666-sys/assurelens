"""Statistics the sufficiency gate depends on.

Implemented by hand rather than delegated to a library, deliberately. This is
an assurance tool: a reviewer has to be able to read the arithmetic that
decided whether a conclusion was supportable. A call into scipy would move
that decision somewhere nobody looks.

Which means these have to be right, and provably so. The tests check the
bounds against published values *and* against the equation they are supposed
to solve, so a plausible-looking wrong answer cannot pass.
"""

from __future__ import annotations

import math

# 1.959963985 is the two-sided 95% normal quantile. Spelled out rather than
# rounded to 1.96, because the fourth decimal moves interval bounds enough to
# matter when comparing against published tables.
Z_95 = 1.959963985


def wilson_interval(successes: int, trials: int, z: float = Z_95) -> tuple[float, float]:
    """Wilson score interval for a binomial proportion.

    Chosen over the Wald (normal-approximation) interval because Wald
    collapses to zero width at p=0 and p=1 -- exactly where an assurance tool
    must not claim certainty. "Thirty of thirty passed" is the moment a naive
    interval reports (1.0, 1.0) and a sound one reports (0.886, 1.0).

    The bounds are the two roots of

        |p_hat - p| / sqrt(p(1-p)/n) = z

    solved for p, which is what `test_bounds_solve_the_score_equation`
    verifies independently of this implementation.
    """
    if trials <= 0:
        raise ValueError("wilson_interval is undefined for n <= 0")
    if not 0 <= successes <= trials:
        raise ValueError(f"successes={successes} outside 0..{trials}")

    p_hat = successes / trials
    denominator = 1 + z * z / trials
    centre = (p_hat + z * z / (2 * trials)) / denominator
    margin = (z / denominator) * math.sqrt(
        p_hat * (1 - p_hat) / trials + z * z / (4 * trials * trials)
    )

    lower = max(0.0, centre - margin)
    upper = min(1.0, centre + margin)

    # Exact at the extremes, not clamped for tidiness. When p_hat is 0 the
    # margin equals the centre algebraically, so the lower bound is exactly 0;
    # symmetrically for p_hat = 1. Floating point leaves a residue around
    # 1e-17, which would put the point estimate outside its own interval.
    if successes == 0:
        lower = 0.0
    if successes == trials:
        upper = 1.0

    return lower, upper


def interval_width(successes: int, trials: int, z: float = Z_95) -> float:
    lower, upper = wilson_interval(successes, trials, z)
    return upper - lower


def coverage_percent(sample_size: int, population_size: int) -> float:
    """What share of the population the sample actually covers.

    Distinct from sample size, and the two disagree in the direction that
    matters: 200 records is a respectable-sounding sample and 0.8% of 24,000.
    """
    if population_size <= 0:
        raise ValueError("coverage is undefined for an empty population")
    return (sample_size / population_size) * 100.0


# --- Population Stability Index -------------------------------------------

# Added to every bin proportion before the logarithm. Without it a bin that is
# empty in one distribution makes PSI infinite, and an infinite drift score is
# not a measurement -- it is a division by zero wearing a number's clothes.
PSI_EPSILON = 1e-6


def population_stability_index(
    expected: list[float], actual: list[float], epsilon: float = PSI_EPSILON
) -> float:
    """PSI between two binned distributions.

        PSI = sum (actual_i - expected_i) * ln(actual_i / expected_i)

    Inputs are counts or proportions per bin; both are normalised here, so a
    caller cannot get a wrong answer by passing one of each.
    """
    if len(expected) != len(actual):
        raise ValueError(
            f"bin counts differ: expected has {len(expected)}, actual has {len(actual)}"
        )
    if not expected:
        raise ValueError("population_stability_index needs at least one bin")
    if any(v < 0 for v in (*expected, *actual)):
        raise ValueError("bin values must not be negative")

    expected_total = sum(expected)
    actual_total = sum(actual)
    if expected_total <= 0 or actual_total <= 0:
        raise ValueError("both distributions must contain observations")

    psi = 0.0
    for e_raw, a_raw in zip(expected, actual, strict=True):
        e = e_raw / expected_total + epsilon
        a = a_raw / actual_total + epsilon
        psi += (a - e) * math.log(a / e)

    return psi


def quantile_bin_edges(values: list[float], bins: int = 10) -> list[float]:
    """Bin edges at evenly spaced quantiles of `values`.

    Quantile bins rather than equal-width: an equal-width binning of a skewed
    feature puts almost everything in one bin, and PSI then reports stability
    because the binning has hidden the movement.
    """
    if bins < 2:
        raise ValueError("at least two bins are required")
    if not values:
        raise ValueError("cannot derive bin edges from no observations")

    ordered = sorted(values)
    n = len(ordered)
    edges = [ordered[0]]
    for i in range(1, bins):
        position = i * n / bins
        lower = math.floor(position)
        if lower >= n - 1:
            edges.append(ordered[-1])
            continue
        fraction = position - lower
        edges.append(ordered[lower] + fraction * (ordered[lower + 1] - ordered[lower]))
    edges.append(ordered[-1])
    return edges


def bin_counts(values: list[float], edges: list[float]) -> list[int]:
    """Count values falling in each bin defined by `edges`.

    Half-open bins `[lo, hi)` with the last bin closed, so every observation
    lands in exactly one bin and the totals reconcile.
    """
    if len(edges) < 2:
        raise ValueError("need at least two edges to form a bin")

    counts = [0] * (len(edges) - 1)
    last = len(counts) - 1
    for value in values:
        if value <= edges[0]:
            counts[0] += 1
            continue
        if value >= edges[-1]:
            counts[last] += 1
            continue
        for i in range(last + 1):
            if edges[i] <= value < edges[i + 1]:
                counts[i] += 1
                break
    return counts


# --- Fairness --------------------------------------------------------------


def selection_rate_ratio(rates: dict[str, float]) -> float:
    """Lowest group selection rate divided by the highest.

    The caller is responsible for excluding groups too small to support a
    conclusion. Including them is the classic fairness-audit error: a group of
    twenty-two produces a dramatic-looking ratio that measures nothing but
    sampling noise.
    """
    if not rates:
        raise ValueError("no groups supplied")
    highest = max(rates.values())
    if highest <= 0:
        raise ValueError("highest selection rate is zero; ratio is undefined")
    return min(rates.values()) / highest
