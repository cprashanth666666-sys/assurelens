"""Suite 5: AI model assurance. [TRD 4.5, PRD S7/S8]

Rule 13(3) asks a Significant Data Fiduciary to verify that algorithmic
software it adopts is not likely to pose a risk to Data Principals' rights.
These two procedures are how that due diligence is evidenced for a credit
pre-screening model:

* `ai.fairness_selection_rate` -- DPDP-13-02 (NIST AI RMF MEASURE 2.11).
  Selection rate per applicant group with a Wilson interval, the ratio of
  lowest to highest, demographic parity difference, and equal opportunity
  (true-positive-rate) difference where ground truth exists.
* `ai.input_drift_psi` -- DPDP-13-03 (MEASURE 2.4). Population Stability
  Index per input feature against the training baseline, whether anything
  monitors drift at all, and input validation: null rates, duplicates, and a
  screen for suspected target leakage.

Two rules carry the suite's honesty:

1. A group too small to support a conclusion is never reported as a
   disparity. It is left out of the comparison, listed as unassessed, and its
   size is handed to the gate, which decides what that means for the verdict.
2. Suspected leakage is reported for review and never changes the verdict. A
   feature strongly correlated with the outcome can be legitimately
   predictive; the test can raise the question, not settle it.

The four-fifths ratio and the PSI bands are conventions (US EEOC and credit
risk practice respectively), not DPDP requirements, and every result says so.
"""

from __future__ import annotations

import math
import statistics
from collections import Counter, defaultdict
from typing import Any

from app.engine.evidence import (
    EvidenceBundle,
    EvidenceContract,
    EvidenceKind,
    EvidenceRequirement,
)
from app.engine.gate import InferenceMode, RawResult, SampleFrame, Verdict
from app.engine.runner import register
from app.engine.stats import bin_counts, population_stability_index, wilson_interval
from app.engine.thresholds import Thresholds

_DEFAULTS = Thresholds()

FAVOURABLE_DECISION = "APPROVE"
# The ground-truth label for an applicant who would have been a good decision
# to approve. Equal opportunity compares approval rates among these.
QUALIFIED_LABEL = "REPAID"
UNRECORDED_GROUP = "unrecorded"
PSI_BINS = 10

FAIRNESS_CONVENTION_NOTE = (
    "The four-fifths ratio is a US EEOC convention, adopted as a documented and "
    "arguable default. DPDP Rule 13(3) sets no numeric test."
)
PSI_CONVENTION_NOTE = (
    "PSI bands (below 0.10 stable, 0.10 to 0.25 moderate, above 0.25 "
    "significant) are credit-risk convention, not a DPDP requirement."
)


def _r(value: float | None, places: int = 4) -> float | None:
    return None if value is None else round(value, places)


# --- Fairness ----------------------------------------------------------------


def _rate_row(label: str, trials: int, successes: int, min_n: int) -> dict[str, Any]:
    lower, upper = wilson_interval(successes, trials) if trials else (0.0, 1.0)
    return {
        "group": label,
        "n": trials,
        "selected": successes,
        "rate": _r(successes / trials) if trials else None,
        "ci_lower": _r(lower),
        "ci_upper": _r(upper),
        "status": "compared" if trials >= min_n else "too small to conclude",
    }


def fairness_report(
    predictions: list[dict[str, Any]], thresholds: Thresholds = _DEFAULTS
) -> dict[str, Any]:
    """Selection rates, parity and equal opportunity across groups.

    Pure: takes prediction rows, returns numbers. Groups below
    `min_group_n` get an interval (so the reader sees how wide it is) but are
    excluded from every comparison.
    """
    min_n = thresholds.min_group_n
    by_group: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for p in predictions:
        by_group[p.get("group") or UNRECORDED_GROUP].append(p)

    groups = []
    tpr_groups = []
    for label in sorted(by_group):
        rows = by_group[label]
        selected = sum(1 for p in rows if p.get("decision") == FAVOURABLE_DECISION)
        groups.append(_rate_row(label, len(rows), selected, min_n))

        qualified = [p for p in rows if p.get("ground_truth") == QUALIFIED_LABEL]
        if qualified:
            approved = sum(1 for p in qualified if p.get("decision") == FAVOURABLE_DECISION)
            tpr_groups.append(_rate_row(label, len(qualified), approved, min_n))

    compared = [g for g in groups if g["status"] == "compared"]
    ratio = lowest = highest = parity_difference = None
    if len(compared) >= 2:
        lowest = min(compared, key=lambda g: g["rate"])
        highest = max(compared, key=lambda g: g["rate"])
        if highest["rate"] > 0:
            ratio = lowest["rate"] / highest["rate"]
        parity_difference = highest["rate"] - lowest["rate"]

    tpr_compared = [g for g in tpr_groups if g["status"] == "compared"]
    eo_difference = None
    if len(tpr_compared) >= 2:
        eo_difference = (
            max(g["rate"] for g in tpr_compared) - min(g["rate"] for g in tpr_compared)
        )

    return {
        "groups": groups,
        "selection_rate_ratio": _r(ratio),
        "lowest_group": lowest["group"] if lowest else None,
        "highest_group": highest["group"] if highest else None,
        "demographic_parity_difference": _r(parity_difference),
        "equal_opportunity": {
            "groups": tpr_groups,
            "difference": _r(eo_difference),
            "basis": (
                f"Equal opportunity compares approval rates among the "
                f"{sum(g['n'] for g in tpr_groups):,} of {len(predictions):,} "
                f"applicants known to have {QUALIFIED_LABEL.lower()}."
                if tpr_groups else "No ground truth recorded; not computable."
            ),
        },
        "unassessed_groups": [g["group"] for g in groups if g["status"] != "compared"],
        "threshold": thresholds.fairness_ratio_threshold,
        "min_group_n": min_n,
        "convention_note": FAIRNESS_CONVENTION_NOTE,
    }


# --- Drift -------------------------------------------------------------------


def baseline_edges(mean: float, sd: float, bins: int = PSI_BINS) -> list[float]:
    """Quantile bin edges of the training distribution.

    The snapshot records each feature's mean and standard deviation, so the
    edges are the deciles of that distribution and every bin holds exactly
    one tenth of the training population by construction. Open-ended outer
    bins catch values beyond anything seen in training.
    """
    dist = statistics.NormalDist(mean, sd)
    inner = [dist.inv_cdf(i / bins) for i in range(1, bins)]
    return [-math.inf, *inner, math.inf]


def psi_band(psi: float, thresholds: Thresholds = _DEFAULTS) -> str:
    if psi > thresholds.psi_significant:
        return "significant"
    if psi >= thresholds.psi_moderate:
        return "moderate"
    return "stable"


def _numeric(values: list[Any]) -> list[float]:
    out = []
    for v in values:
        if isinstance(v, bool) or v is None:
            continue
        if isinstance(v, int | float) and math.isfinite(v):
            out.append(float(v))
    return out


def drift_report(
    predictions: list[dict[str, Any]],
    snapshot: dict[str, Any] | None,
    thresholds: Thresholds = _DEFAULTS,
) -> dict[str, Any]:
    """PSI per feature against the training baseline."""
    baseline = (snapshot or {}).get("features") or {}
    observed = sorted({k for p in predictions for k in (p.get("features") or {})})

    features = []
    for name in sorted(set(observed) | set(baseline)):
        base = baseline.get(name)
        values = _numeric([(p.get("features") or {}).get(name) for p in predictions])
        if not base or "mean" not in base or not base.get("sd"):
            features.append({"feature": name, "psi": None, "band": "no baseline",
                             "n": len(values)})
            continue
        if not values:
            features.append({"feature": name, "psi": None, "band": "no observations",
                             "n": 0})
            continue
        counts = bin_counts(values, baseline_edges(base["mean"], base["sd"]))
        psi = population_stability_index([1.0] * PSI_BINS, [float(c) for c in counts])
        features.append({
            "feature": name,
            "psi": _r(psi),
            "band": psi_band(psi, thresholds),
            "n": len(values),
            "baseline_mean": base["mean"],
            "observed_mean": _r(statistics.fmean(values)),
            "bin_share": [_r(c / len(values), 4) for c in counts],
        })

    return {
        "features": features,
        "significant": [f["feature"] for f in features if f["band"] == "significant"],
        "moderate": [f["feature"] for f in features if f["band"] == "moderate"],
        "without_baseline": [f["feature"] for f in features if f["band"] == "no baseline"],
        "baseline_captured_at": (snapshot or {}).get("captured_at"),
        "bins": PSI_BINS,
        "thresholds": {"moderate": thresholds.psi_moderate,
                       "significant": thresholds.psi_significant},
        "convention_note": PSI_CONVENTION_NOTE,
    }


# --- Input validation ---------------------------------------------------------


def validation_report(
    predictions: list[dict[str, Any]], thresholds: Thresholds = _DEFAULTS
) -> dict[str, Any]:
    """Nulls, duplicates, and a leakage screen. [TRD 4.5c]"""
    n = len(predictions)
    names = sorted({k for p in predictions for k in (p.get("features") or {})})

    null_rates = []
    for name in names:
        present = _numeric([(p.get("features") or {}).get(name) for p in predictions])
        rate = 1 - len(present) / n if n else 0.0
        null_rates.append({"feature": name, "null_rate": _r(rate),
                           "exceeds": rate > thresholds.max_null_rate})

    principal_counts = Counter(p.get("principal_id") for p in predictions
                               if p.get("principal_id") is not None)
    duplicates = sum(c - 1 for c in principal_counts.values() if c > 1)

    # Leakage screen: correlation of each feature with the known outcome.
    labelled = [p for p in predictions if p.get("ground_truth") is not None]
    label = [1.0 if p["ground_truth"] == QUALIFIED_LABEL else 0.0 for p in labelled]
    correlations = []
    for name in names:
        pairs = [((p.get("features") or {}).get(name), y)
                 for p, y in zip(labelled, label, strict=True)]
        xs = [float(x) for x, _ in pairs if isinstance(x, int | float) and not isinstance(x, bool)]
        ys = [y for x, y in pairs if isinstance(x, int | float) and not isinstance(x, bool)]
        try:
            r = statistics.correlation(xs, ys) if len(xs) >= 3 else None
        except statistics.StatisticsError:
            # A constant feature or constant label has no correlation to report.
            r = None
        correlations.append({
            "feature": name,
            "correlation_with_outcome": _r(r),
            "suspected_leakage": r is not None and abs(r) > thresholds.leakage_corr_threshold,
        })

    return {
        "null_rates": null_rates,
        "features_over_null_limit": [x["feature"] for x in null_rates if x["exceeds"]],
        "duplicate_principals": duplicates,
        "out_of_range": (
            "Not tested: the model registry declares no input schema, so there "
            "is no declared range to test against."
        ),
        "leakage_screen": {
            "labelled_rows": len(labelled),
            "correlations": correlations,
            "suspected": [c["feature"] for c in correlations if c["suspected_leakage"]],
            "threshold": thresholds.leakage_corr_threshold,
            "note": (
                "Suspected leakage requires review. A feature can be strongly "
                "predictive for legitimate reasons, so this never decides the verdict."
            ),
        },
        "max_null_rate": thresholds.max_null_rate,
    }


# --- Procedures ---------------------------------------------------------------


def _model_for(
    predictions: list[dict[str, Any]], registry: list[dict[str, Any]]
) -> dict[str, Any] | None:
    """The consequential model the predictions belong to. Meridian runs one;
    with several, the most-predicted consequential model is assessed and the
    rest are listed, rather than silently averaged together."""
    counts = Counter(p.get("model_id") for p in predictions)
    candidates = [m for m in registry if m.get("is_consequential")]
    candidates.sort(key=lambda m: (-counts.get(m["id"], 0), m["id"]))
    return candidates[0] if candidates else None


_CONTRACT = EvidenceContract(
    required=(
        EvidenceRequirement("model_predictions", EvidenceKind.DB_QUERY, defines_population=True),
        EvidenceRequirement("model_registry", EvidenceKind.DB_QUERY),
    )
)


@register("ai.fairness_selection_rate")
class FairnessSelectionRate:
    """DPDP-13-02: model outcomes do not disadvantage a group.

    Every decision the model made is examined, so this is a census of its
    decisions: sampling gates do not apply. Group size still matters, and is
    handed to the gate as `subgroup_sizes`.
    """

    evidence_contract = _CONTRACT

    def execute(self, evidence: EvidenceBundle, config: dict[str, Any]) -> RawResult:
        registry = evidence.payload("model_registry", [])
        model = _model_for(evidence.payload("model_predictions", []), registry)
        predictions = [p for p in evidence.payload("model_predictions", [])
                       if model is None or p.get("model_id") == model["id"]]
        report = fairness_report(predictions)

        ratio = report["selection_rate_ratio"]
        failing = ratio is not None and ratio < report["threshold"]

        assessments = [
            {"metric": "selection_rate", "group_label": g["group"], "value": g["rate"],
             "group_n": g["n"]}
            for g in report["groups"]
        ] + [
            {"metric": "true_positive_rate", "group_label": g["group"], "value": g["rate"],
             "group_n": g["n"]}
            for g in report["equal_opportunity"]["groups"]
        ] + [
            {"metric": metric, "value": value}
            for metric, value in (
                ("selection_rate_ratio", ratio),
                ("demographic_parity_difference", report["demographic_parity_difference"]),
                ("equal_opportunity_difference", report["equal_opportunity"]["difference"]),
            ) if value is not None
        ]

        return RawResult(
            outcome=Verdict.FAIL if failing else Verdict.PASS,
            inference_mode=InferenceMode.CENSUS,
            sample_frame=SampleFrame.CENSUS,
            sample_size=len(predictions),
            population_size=len(predictions),
            subgroup_sizes={g["group"]: g["n"] for g in report["groups"]},
            detail={
                "model": model["name"] if model else None,
                "model_id": model["id"] if model else None,
                "fairness": report,
                "model_assessments": assessments,
            },
        )


@register("ai.input_drift_psi")
class InputDriftPsi:
    """DPDP-13-03: inputs are monitored for drift from the training baseline.

    Fails on any feature with significant PSI, and on the absence of drift
    monitoring, which the control treats as an exception in its own right.
    Without a training snapshot drift cannot be measured at all, and that is
    reported as missing evidence rather than as stability.
    """

    evidence_contract = _CONTRACT

    def execute(self, evidence: EvidenceBundle, config: dict[str, Any]) -> RawResult:
        registry = evidence.payload("model_registry", [])
        all_predictions = evidence.payload("model_predictions", [])
        model = _model_for(all_predictions, registry)
        predictions = [p for p in all_predictions
                       if model is None or p.get("model_id") == model["id"]]

        if model is None or not (model.get("training_snapshot") or {}).get("features"):
            name = model["name"] if model else "the consequential model"
            return RawResult(
                outcome=Verdict.PASS,
                inference_mode=InferenceMode.CENSUS,
                sample_frame=SampleFrame.CENSUS,
                sample_size=len(predictions),
                population_size=len(predictions),
                missing_required_evidence=(f"training baseline for {name}",),
                detail={"model": model["name"] if model else None},
            )

        drift = drift_report(predictions, model["training_snapshot"])
        validation = validation_report(predictions)

        exceptions = []
        for feature in drift["significant"]:
            psi = next(f["psi"] for f in drift["features"] if f["feature"] == feature)
            exceptions.append(f"{feature}: PSI {psi:.3f} is above {_DEFAULTS.psi_significant}.")
        if not model.get("has_drift_monitoring"):
            exceptions.append("No drift monitoring is in place for this model.")
        for feature in validation["features_over_null_limit"]:
            exceptions.append(f"{feature}: null rate above {_DEFAULTS.max_null_rate:.0%}.")
        if validation["duplicate_principals"]:
            exceptions.append(
                f"{validation['duplicate_principals']} duplicate applicant record(s)."
            )

        assessments = [
            {"metric": "psi", "feature": f["feature"], "value": f["psi"]}
            for f in drift["features"] if f["psi"] is not None
        ] + [
            {"metric": "null_rate", "feature": x["feature"], "value": x["null_rate"]}
            for x in validation["null_rates"]
        ] + [
            {"metric": "outcome_correlation", "feature": c["feature"],
             "value": c["correlation_with_outcome"]}
            for c in validation["leakage_screen"]["correlations"]
            if c["correlation_with_outcome"] is not None
        ]

        return RawResult(
            outcome=Verdict.FAIL if exceptions else Verdict.PASS,
            inference_mode=InferenceMode.CENSUS,
            sample_frame=SampleFrame.CENSUS,
            sample_size=len(predictions),
            population_size=len(predictions),
            detail={
                "model": model["name"],
                "model_id": model["id"],
                "has_drift_monitoring": bool(model.get("has_drift_monitoring")),
                "exceptions": exceptions,
                "drift": drift,
                "validation": validation,
                "model_assessments": assessments,
            },
        )
