"""Suite 1: PII discovery and retention.

Three procedures:

* `pii.discovery_and_protection` -- what each asset actually holds, against
  what its inventory declares and how it is protected.
* `retention.erasure_on_purpose_cessation` -- Act s.8(7)(a).
* `retention.minimum_log_retention` -- Rule 8(3).

The last two pull against each other on purpose. s.8(7)(a) compels erasure
once a purpose ends; Rule 8(3) compels a one-year floor on processing logs.
A system that deletes everything on schedule breaches the second while
looking maximally privacy-friendly, and most tools only look in one
direction.
"""

from __future__ import annotations

import datetime as dt
from typing import Any

from app.engine.detectors import classes_present, detect_in_record
from app.engine.evidence import (
    EvidenceBundle,
    EvidenceContract,
    EvidenceKind,
    EvidenceRequirement,
)
from app.engine.gate import InferenceMode, RawResult, SampleFrame, Verdict
from app.engine.runner import register

# Act s.8(8): a purpose is deemed no longer served once the principal has
# neither approached the fiduciary nor exercised rights for a prescribed
# period. No period is prescribed for a bank, so three years is taken from
# the window the Rules use elsewhere and recorded as an assumption, not
# presented as a statutory figure.
PURPOSE_CESSATION_DAYS = 1095

# Rule 8(3). This one IS statutory.
MINIMUM_LOG_RETENTION_DAYS = 365

# Timestamps in the estate hang off a fixed epoch so retention results do not
# drift from one day to the next.
from app.seed.generator import EPOCH  # noqa: E402


@register("pii.discovery_and_protection")
class DiscoveryAndProtection:
    """What an asset holds, against what it declares and how it is protected.

    Rule 6(1)(a) requires encryption, obfuscation, masking or tokenisation of
    personal data. An asset holding an identifier class its inventory never
    mentioned is a finding twice over: the protection is wrong, and nobody
    knew to apply it.

    The inference mode is chosen per result, which matters. Finding an
    identifier PROVES it is there -- one record is enough, and the conclusion
    is definitive regardless of how little was scanned. Finding none proves
    nothing unless coverage was good. Presence and absence are not
    symmetrical, and reporting them as though they were is how a 3% scan
    becomes a clean bill of health.
    """

    evidence_contract = EvidenceContract(
        required=(
            EvidenceRequirement("data_assets", EvidenceKind.DB_QUERY),
            EvidenceRequirement(
                "asset_records", EvidenceKind.DB_QUERY, defines_population=True
            ),
        )
    )

    def execute(self, evidence: EvidenceBundle, config: dict[str, Any]) -> RawResult:
        assets = evidence.payload("data_assets", [])
        records = evidence.payload("asset_records", [])

        by_asset: dict[int, list[dict[str, Any]]] = {}
        for record in records:
            by_asset.setdefault(record["asset_id"], []).append(record["content"])

        findings: list[dict[str, Any]] = []
        scanned = 0
        declared_population = 0

        for asset in assets:
            contents = by_asset.get(asset["id"], [])
            scanned += len(contents)
            declared_population += asset.get("record_count") or 0
            if not contents:
                continue

            found = classes_present(contents)
            declared = set(asset.get("declared_identifier_classes") or [])
            undeclared = sorted(set(found) - declared)

            if undeclared:
                sample = next(
                    (
                        d
                        for c in contents
                        for d in detect_in_record(c)
                        if d.identifier_class in undeclared
                    ),
                    None,
                )
                findings.append(
                    {
                        "asset": asset["name"],
                        "issue": "undeclared_identifiers",
                        "undeclared": undeclared,
                        "declared": sorted(declared),
                        "encryption_at_rest": asset["encryption_at_rest"],
                        "occurrences": {k: found[k] for k in undeclared},
                        "example_field": sample.field if sample else None,
                        "scanned": len(contents),
                        "asset_population": asset.get("record_count"),
                    }
                )

            if found and not asset["encryption_at_rest"]:
                findings.append(
                    {
                        "asset": asset["name"],
                        "issue": "unencrypted_personal_data",
                        "classes_present": sorted(found),
                        "scanned": len(contents),
                    }
                )

        if findings:
            # Definitive: the identifiers were observed. How much was left
            # unscanned does not weaken a positive finding.
            return RawResult(
                outcome=Verdict.FAIL,
                inference_mode=InferenceMode.CENSUS,
                sample_frame=SampleFrame.CENSUS,
                sample_size=len(assets),
                population_size=len(assets),
                successes=len(assets) - len({f["asset"] for f in findings}),
                detail={
                    "findings": findings,
                    "assets_examined": len(assets),
                    "records_scanned": scanned,
                },
            )

        # Nothing found. Whether that means anything depends entirely on how
        # much was looked at, so the sampling rules apply and the gate
        # decides.
        return RawResult(
            outcome=Verdict.PASS,
            inference_mode=InferenceMode.POPULATION,
            sample_size=scanned,
            population_size=declared_population or None,
            successes=scanned,
            detail={"assets_examined": len(assets), "records_scanned": scanned},
        )


@register("retention.erasure_on_purpose_cessation")
class ErasureOnPurposeCessation:
    """Act s.8(7)(a): erase once the purpose ends, unless the law requires
    retention.

    The test is for a RECORDED BASIS, not for age. The Act illustrates its own
    carve-out with a bank holding client identity records for ten years under
    a statutory duty -- so for this engagement "old" and "non-compliant" are
    different things, and a control that flagged every old record would be
    confidently wrong about the majority of a bank's estate.
    """

    evidence_contract = EvidenceContract(
        required=(
            EvidenceRequirement(
                "data_principals", EvidenceKind.DB_QUERY, defines_population=True
            ),
            EvidenceRequirement("processing_activities", EvidenceKind.DB_QUERY),
        )
    )

    def execute(self, evidence: EvidenceBundle, config: dict[str, Any]) -> RawResult:
        principals = evidence.payload("data_principals", [])
        cutoff = EPOCH - dt.timedelta(days=PURPOSE_CESSATION_DAYS)

        ceased = [
            p for p in principals
            if p["last_contact_at"] and p["last_contact_at"] < cutoff
        ]
        without_basis = [
            p for p in ceased
            if p["erased_at"] is None and not p["legal_hold"]
        ]
        lawfully_held = [p for p in ceased if p["legal_hold"]]

        missing_basis = [
            p for p in lawfully_held if not p.get("legal_hold_basis")
        ]

        compliant = len(ceased) - len(without_basis) - len(missing_basis)

        return RawResult(
            outcome=Verdict.FAIL if (without_basis or missing_basis) else Verdict.PASS,
            inference_mode=InferenceMode.POPULATION,
            sample_frame=SampleFrame.CENSUS,
            sample_size=len(ceased),
            population_size=len(principals),
            successes=max(0, compliant),
            detail={
                "purpose_ceased": len(ceased),
                "retained_without_basis": len(without_basis),
                "lawfully_retained": len(lawfully_held),
                "legal_hold_without_recorded_basis": len(missing_basis),
                "cessation_window_days": PURPOSE_CESSATION_DAYS,
                "basis_note": (
                    "Retention is lawful where a legal obligation requires it "
                    "(Act s.8(7)(a)). Records held with a recorded basis are "
                    "compliant however old."
                ),
            },
        )


@register("retention.minimum_log_retention")
class MinimumLogRetention:
    """Rule 8(3): personal data, traffic data and processing logs for at
    least one year.

    The counterweight to erasure. Over-deletion is a finding, and a system
    that purges logs at ninety days breaches this while looking like a
    privacy success.
    """

    evidence_contract = EvidenceContract(
        required=(
            EvidenceRequirement(
                "processing_activities",
                EvidenceKind.DB_QUERY,
                defines_population=True,
            ),
            EvidenceRequirement("access_logs", EvidenceKind.DB_QUERY),
        )
    )

    def execute(self, evidence: EvidenceBundle, config: dict[str, Any]) -> RawResult:
        activities = evidence.payload("processing_activities", [])
        logs = evidence.payload("access_logs", [])

        below_floor = [
            a for a in activities
            if (a.get("log_retention_days") or 0) < MINIMUM_LOG_RETENTION_DAYS
        ]

        oldest = min((entry["occurred_at"] for entry in logs), default=None)
        observed_days = (EPOCH - oldest).days if oldest else None

        return RawResult(
            outcome=Verdict.FAIL if below_floor else Verdict.PASS,
            inference_mode=InferenceMode.CENSUS,
            sample_frame=SampleFrame.CENSUS,
            sample_size=len(activities),
            population_size=len(activities),
            successes=len(activities) - len(below_floor),
            detail={
                "activities_examined": len(activities),
                "below_statutory_floor": [
                    {
                        "purpose": a["purpose"],
                        "configured_days": a.get("log_retention_days"),
                        "required_days": MINIMUM_LOG_RETENTION_DAYS,
                    }
                    for a in below_floor
                ],
                "oldest_log_age_days": observed_days,
            },
        )
