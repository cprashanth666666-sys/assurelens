"""Every threshold the gate applies, in one place, each with its basis.

Two properties matter here and both are about honesty rather than tuning.

A threshold with no stated basis is a number someone picked. Each constant
below says where it came from and, where it is a convention rather than a
requirement, says so plainly -- the four-fifths rule in particular is a US
employment-law convention adopted as a documented default, not anything the
DPDP Act prescribes.

And loosening a threshold must never be invisible. Overrides are carried on
the result, printed in the workpaper's threshold register, and written to the
audit log. Quietly widening a bound to turn INSUFFICIENT_EVIDENCE into PASS is
the one manoeuvre that would hollow this product out, so it is made loud.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from typing import Any


@dataclass(frozen=True)
class Thresholds:
    """Gate thresholds. Frozen: an override produces a new instance, so a
    threshold cannot be mutated part-way through a run."""

    # --- G1: minimum sample ------------------------------------------------
    # Below roughly thirty observations the Wilson interval is too wide for a
    # population claim almost regardless of what was observed. Twelve of
    # twelve -- a perfect score -- spans 0.76 to 1.00.
    min_sample_n: int = 30

    # --- G2: interval width ------------------------------------------------
    # A "compliance rate somewhere between 60% and 95%" is not a finding. The
    # bound is on the 95% Wilson width, so it constrains precision directly
    # rather than via sample size, which is what actually matters.
    max_ci_width: float = 0.20

    # --- G3: coverage ------------------------------------------------------
    # Sample size and coverage disagree in the direction that matters: 200
    # records is a respectable-sounding sample and 0.83% of 24,000. Testing
    # 200 of 2.4M proves nothing about the 2.4M however clean the 200 are.
    min_coverage_pct: float = 10.0

    # --- G5: evidence age --------------------------------------------------
    # A control that operated in March is not evidence about September. Ninety
    # days is a quarter, matching the usual re-performance cycle.
    max_evidence_age_days: int = 90

    # --- Suite-specific ----------------------------------------------------
    # Act s.6(6) requires withdrawal to be as easy as giving consent. It sets
    # no latency, so this is an engagement-level service level, stated as an
    # assumption rather than presented as a legal requirement.
    propagation_sla_seconds: int = 300

    # A processor credential unused for half a year is an uncontrolled access
    # path whatever the contract says.
    stale_access_days: int = 180
    max_credential_age_days: int = 365

    # Rule 8(3): personal data, traffic data and logs for a minimum of one
    # year. This one IS a statutory figure, not a convention.
    min_log_retention_days: int = 365

    # --- Fairness ----------------------------------------------------------
    # The four-fifths rule is a US EEOC convention. It is NOT a DPDP
    # requirement, and the product says so wherever it is applied rather than
    # implying legal force it does not have.
    fairness_ratio_threshold: float = 0.80

    # A group below this size cannot support a disparity claim. Reporting one
    # anyway is the classic fairness-audit error: noise from twenty-two
    # observations reads as dramatic bias.
    min_group_n: int = 30

    # --- Drift -------------------------------------------------------------
    # Conventional PSI bands: below 0.10 stable, 0.10-0.25 moderate, above
    # 0.25 significant. Widely used in credit-risk monitoring; again a
    # convention, not a requirement.
    psi_moderate: float = 0.10
    psi_significant: float = 0.25

    # --- Validation --------------------------------------------------------
    # Near-perfect correlation with the label usually means the feature
    # encodes the outcome. Reported as SUSPECTED leakage requiring review,
    # never as a certainty -- a legitimate feature can be strongly predictive.
    leakage_corr_threshold: float = 0.95
    max_null_rate: float = 0.05

    def with_overrides(self, overrides: dict[str, Any]) -> tuple[Thresholds, dict[str, Any]]:
        """Apply per-control overrides, returning the new thresholds and a
        record of exactly what was changed from what.

        The record travels with the result so the workpaper can print it. A
        threshold loosened for one control must be visible in the deliverable,
        not buried in a config file.
        """
        if not overrides:
            return self, {}

        known = {f.name for f in fields(self)}
        unknown = set(overrides) - known
        if unknown:
            raise ValueError(
                f"unknown threshold override(s): {sorted(unknown)}. "
                f"A typo here would silently leave the default in place."
            )

        applied = {
            name: {"default": getattr(self, name), "override": value}
            for name, value in overrides.items()
            if getattr(self, name) != value
        }
        return type(self)(**{**self.as_dict(), **overrides}), applied

    def as_dict(self) -> dict[str, Any]:
        return {f.name: getattr(self, f.name) for f in fields(self)}


DEFAULT_THRESHOLDS = Thresholds()
