"""Deterministic generator for Meridian's synthetic estate.

Two rules govern everything here.

**Determinism.** The same seed must produce a byte-identical estate, because
reproducible runs are an audit requirement, not a convenience [PRD P4]. So:
all randomness comes from `numpy.random.default_rng(seed)`, never the `random`
module; every timestamp is relative to a fixed `EPOCH` rather than `now()`, so
retention results do not drift day to day; and iteration order is always
explicit.

**Defects are planted in data, not asserted by fixtures.** Each one is a
condition a test has to actually find by querying. If a test would pass
because a fixture told it the answer, the test proves nothing.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from app.seed.identifiers import (
    synthetic_aadhaar,
    synthetic_account_number,
    synthetic_email,
    synthetic_mobile,
    synthetic_pan,
)

# Every relative date hangs off this. Using `now()` would make the retention
# suite's results change silently from one day to the next, which would make
# a "reproducible" run reproducible only within a calendar day.
EPOCH = dt.datetime(2026, 9, 1, 0, 0, 0, tzinfo=dt.UTC)

# --- Estate shape ---------------------------------------------------------
# Sized so the demo tells a clear story and the sufficiency gate fires for
# real statistical reasons rather than contrived ones. [SCHEMA 5]

PRINCIPAL_COUNT = 24_000
PREDICTION_COUNT = 12_000

# Purpose ceased and no legal basis recorded: defect S5, restated after the
# Day 2 correction. The Third Schedule timetable does not bind a BFSI GCC, so
# what is testable is Act s.8(7)(a) -- held past purpose cessation with no
# recorded basis for holding it.
OVERDUE_ERASURE_COUNT = 11_400

# A 200-record sample of 24,000 is 0.83%, comfortably under the 10% coverage
# threshold, so G3 fires because the arithmetic says so.
WITHDRAWN_CONSENT_COUNT = 3_200

# The fairness trap. Four groups, the smallest with 22 members -- below
# MIN_GROUP_N. A naive tool reports a dramatic disparity from 22 observations;
# the correct answer is that the group is too small to conclude from.
GROUP_WEIGHTS = {"A": 0.46, "B": 0.33, "C": 0.20, "D": 0.0}
SMALL_GROUP_LABEL = "D"
SMALL_GROUP_SIZE = 22

# Defect S7: selection-rate ratio 0.71, below the four-fifths threshold.
GROUP_APPROVAL_RATE = {"A": 0.62, "B": 0.58, "C": 0.44, "D": 0.50}

CONSENT_PURPOSES = (
    "marketing_communications",
    "credit_prescreening",
    "service_operations",
)

# Defect S1: the consent store updates instantly, the marketing segment
# refreshes nightly, so a withdrawn principal stays marketable for up to 22h.
NIGHTLY_BATCH_LAG_HOURS = 22


@dataclass
class GeneratedEstate:
    """Plain rows, ready to persist. The generator does no I/O."""

    assets: list[dict[str, Any]] = field(default_factory=list)
    activities: list[dict[str, Any]] = field(default_factory=list)
    principals: list[dict[str, Any]] = field(default_factory=list)
    consents: list[dict[str, Any]] = field(default_factory=list)
    consent_events: list[dict[str, Any]] = field(default_factory=list)
    third_parties: list[dict[str, Any]] = field(default_factory=list)
    access_logs: list[dict[str, Any]] = field(default_factory=list)
    models: list[dict[str, Any]] = field(default_factory=list)
    predictions: list[dict[str, Any]] = field(default_factory=list)
    # Free-text records carrying unmasked identifiers: defect S9. Held on the
    # asset rather than in its own table, because the finding is about the
    # asset's protection, not about the transcripts themselves.
    transcripts: list[dict[str, Any]] = field(default_factory=list)
    # Rows of actual asset content, which is what suite 1 scans.
    asset_records: list[dict[str, Any]] = field(default_factory=list)


def _days(n: float) -> dt.timedelta:
    return dt.timedelta(days=n)


def generate_assets() -> list[dict[str, Any]]:
    """Nine assets. One holds identifiers it does not declare, unencrypted."""
    return [
        {
            "name": "crm_customers",
            "system": "Salesforce (India instance)",
            "classification": "Confidential - personal data",
            "declared_identifier_classes": ["name", "email", "mobile", "account_number"],
            "encryption_at_rest": True,
            "record_count": PRINCIPAL_COUNT,
            "hosted_region": "ap-south-1",
        },
        {
            "name": "kyc_documents",
            "system": "Internal document store",
            "classification": "Restricted - identity documents",
            "declared_identifier_classes": ["aadhaar", "pan", "name"],
            "encryption_at_rest": True,
            "record_count": PRINCIPAL_COUNT,
            "hosted_region": "ap-south-1",
        },
        {
            # Defect S9. Declared to hold only transcript text; actually holds
            # PAN-format identifiers spoken by customers, and unencrypted.
            "name": "call_transcripts",
            "system": "Transcription vendor bucket",
            "classification": "Internal",
            "declared_identifier_classes": ["transcript_text"],
            "encryption_at_rest": False,
            "record_count": 4_800,
            "hosted_region": "ap-south-1",
        },
        {
            "name": "transaction_ledger",
            "system": "Core banking",
            "classification": "Confidential",
            "declared_identifier_classes": ["account_number"],
            "encryption_at_rest": True,
            "record_count": 1_920_000,
            "hosted_region": "ap-south-1",
        },
        {
            "name": "marketing_segments",
            "system": "Marketing automation platform",
            "classification": "Internal",
            "declared_identifier_classes": ["email", "mobile"],
            "encryption_at_rest": True,
            "record_count": 18_400,
            "hosted_region": "us-east-1",
        },
        {
            "name": "credit_scoring_features",
            "system": "Model feature store",
            "classification": "Confidential",
            "declared_identifier_classes": ["account_number"],
            "encryption_at_rest": True,
            "record_count": PREDICTION_COUNT,
            "hosted_region": "ap-south-1",
        },
        {
            "name": "grievance_register",
            "system": "Service desk",
            "classification": "Internal",
            "declared_identifier_classes": ["name", "email"],
            "encryption_at_rest": True,
            "record_count": 640,
            "hosted_region": "ap-south-1",
        },
        {
            "name": "consent_store",
            "system": "Internal consent service",
            "classification": "Confidential",
            "declared_identifier_classes": ["account_number"],
            "encryption_at_rest": True,
            "record_count": PRINCIPAL_COUNT,
            "hosted_region": "ap-south-1",
        },
        {
            "name": "group_reporting_extract",
            "system": "Parent bank data warehouse",
            "classification": "Confidential",
            "declared_identifier_classes": ["account_number"],
            "encryption_at_rest": True,
            "record_count": 24_000,
            # Cross-border to the US parent: Rule 15 exposure is real even
            # though no order exists yet to test against.
            "hosted_region": "us-east-1",
        },
    ]


def generate_activities(asset_ids: dict[str, int]) -> list[dict[str, Any]]:
    """Twelve activities. One purges logs at 90 days: defect S6."""
    rows = [
        ("Customer relationship management", "Consent", "crm_customers", 3650, 400),
        ("KYC and identity verification", "Legal obligation", "kyc_documents", 3650, 3650),
        # Defect S6: 90 days is below the Rule 8(3) one-year floor. The rule
        # is drafted generally, so unlike the Third Schedule it does bind.
        ("Call quality monitoring", "Consent", "call_transcripts", 730, 90),
        ("Transaction processing", "Contract", "transaction_ledger", 3650, 3650),
        ("Marketing communications", "Consent", "marketing_segments", 730, 400),
        ("Credit pre-screening", "Consent", "credit_scoring_features", 1825, 400),
        ("Grievance redressal", "Legal obligation", "grievance_register", 1825, 400),
        ("Consent lifecycle management", "Legal obligation", "consent_store", 3650, 2555),
        ("Group regulatory reporting", "Legal obligation", "group_reporting_extract", 3650, 3650),
        ("Fraud monitoring", "Legitimate use", "transaction_ledger", 3650, 3650),
        ("Product analytics", "Consent", "crm_customers", 730, 400),
        ("Service operations", "Contract", "crm_customers", 3650, 400),
    ]
    return [
        {
            "purpose": purpose,
            "lawful_basis": basis,
            "asset_id": asset_ids.get(asset),
            "retention_days": retention,
            "log_retention_days": log_retention,
        }
        for purpose, basis, asset, retention, log_retention in rows
    ]


def _assign_groups(rng: np.random.Generator, count: int) -> list[str]:
    """Group labels, with the smallest fixed at exactly SMALL_GROUP_SIZE.

    The size is pinned rather than sampled so the fairness gate demonstration
    is reproducible: a sampled small group would drift above or below the
    minimum from seed to seed.
    """
    labels = [SMALL_GROUP_LABEL] * SMALL_GROUP_SIZE
    remaining = count - SMALL_GROUP_SIZE

    weighted = {k: v for k, v in GROUP_WEIGHTS.items() if v > 0}
    total = sum(weighted.values())
    names = sorted(weighted)
    probabilities = [weighted[n] / total for n in names]

    labels.extend(rng.choice(names, size=remaining, p=probabilities).tolist())
    rng.shuffle(labels)
    return labels


def generate_principals(rng: np.random.Generator) -> list[dict[str, Any]]:
    """24,000 principals, of which 11,400 are held past purpose cessation
    with no recorded legal basis.

    Restated from the original spec after the Day 2 legal correction: the
    Third Schedule's three-year timetable binds only e-commerce, online
    gaming and social media intermediaries above user thresholds, and a BFSI
    captive GCC is none of them. What binds Meridian is Act s.8(7)(a), whose
    carve-out the Act illustrates with a bank. So the defect is not "old" --
    it is "held with nothing on file justifying holding it".
    """
    groups = _assign_groups(rng, PRINCIPAL_COUNT)
    rows: list[dict[str, Any]] = []

    # Contact recency in days before EPOCH. Those beyond the purpose-cessation
    # window are candidates for erasure.
    ages = rng.integers(1, 2200, size=PRINCIPAL_COUNT)
    order = np.argsort(-ages)  # oldest first, so the overdue set is the oldest

    overdue_positions = set(order[:OVERDUE_ERASURE_COUNT].tolist())

    for i in range(PRINCIPAL_COUNT):
        age_days = int(ages[i])
        last_contact = EPOCH - _days(age_days)
        overdue = i in overdue_positions

        if overdue:
            # Purpose ceased, nothing erased, and no basis recorded. Finding.
            legal_hold, basis, erased_at = False, None, None
        elif age_days > 1095:
            # Old, but lawfully held: the Act's Illustration (II) case.
            legal_hold, erased_at = True, None
            basis = "PMLA / RBI KYC record-keeping obligation"
        else:
            legal_hold, basis, erased_at = False, None, None

        rows.append(
            {
                "external_ref": f"MFS{i:06d}",
                "last_contact_at": last_contact,
                "erased_at": erased_at,
                "legal_hold": legal_hold,
                "legal_hold_basis": basis,
                # No pre-erasure notice mechanism exists anywhere in the
                # estate. Rule 8(2) does not bind Meridian, so this is
                # recorded but not raised as a finding -- the control that
                # would raise it is scoped out with a written reason.
                "pre_erasure_notice_at": None,
                "group_attribute": groups[i],
                "is_minor": False,
                "aadhaar": synthetic_aadhaar(rng),
                "pan": synthetic_pan(rng),
                "mobile": synthetic_mobile(rng),
                "email": synthetic_email(rng, f"MFS{i:06d}"),
                "account_number": synthetic_account_number(rng),
            }
        )

    return rows


def generate_consents(
    rng: np.random.Generator, principal_refs: list[str]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """One consent per principal for marketing, plus withdrawal events.

    Defect S1 lives in the gap between `withdrawn_at` and
    `downstream_synced_at`: the consent record is updated the instant the
    principal withdraws, but the marketing segment only refreshes overnight.
    The record looks compliant; the principal keeps being marketed to.
    """
    consents: list[dict[str, Any]] = []
    events: list[dict[str, Any]] = []

    withdrawn_idx = set(
        rng.choice(
            len(principal_refs), size=WITHDRAWN_CONSENT_COUNT, replace=False
        ).tolist()
    )

    for i, ref in enumerate(principal_refs):
        granted_at = EPOCH - _days(int(rng.integers(200, 1800)))
        withdrawn = i in withdrawn_idx
        withdrawn_at: dt.datetime | None = None
        synced_at: dt.datetime | None = None

        if withdrawn:
            withdrawn_at = granted_at + _days(int(rng.integers(30, 180)))
            lag_hours = float(rng.uniform(0.5, NIGHTLY_BATCH_LAG_HOURS))
            synced_at = withdrawn_at + dt.timedelta(hours=lag_hours)
            status = "WITHDRAWN"
        else:
            lag_hours = 0.0
            status = "ACTIVE"

        consents.append(
            {
                "external_ref": ref,
                "purpose": CONSENT_PURPOSES[0],
                "status": status,
                "granted_at": granted_at,
                "withdrawn_at": withdrawn_at,
                "downstream_synced_at": synced_at,
            }
        )

        events.append(
            {"external_ref": ref, "event": "GRANT", "occurred_at": granted_at,
             "latency_ms": None}
        )
        if withdrawn and withdrawn_at and synced_at:
            events.append(
                {"external_ref": ref, "event": "WITHDRAW",
                 "occurred_at": withdrawn_at, "latency_ms": 0}
            )
            events.append(
                {"external_ref": ref, "event": "DOWNSTREAM_SYNC",
                 "occurred_at": synced_at,
                 "latency_ms": int(lag_hours * 3_600_000)}
            )

    return consents, events


def generate_third_parties(rng: np.random.Generator) -> list[dict[str, Any]]:
    """Fourteen processors. One is stale with no agreement on file: defect S4."""
    specs = [
        # name, category, has_dpa, granted, exercised, issued_days_ago,
        # last_used_days_ago, active, country
        ("Cloudspan Hosting", "Infrastructure", True,
         ["read:customers", "write:customers"], ["read:customers", "write:customers"],
         180, 1, True, "IN"),
        ("VerifyKart KYC", "Identity verification", True,
         ["read:customers", "read:kyc"], ["read:kyc"], 300, 2, True, "IN"),
        # Defect S4: no DPA reference, credential unused for 14 months, still
        # active. Two failures on one processor.
        ("EchoScribe Transcription", "Call transcription", False,
         ["read:transcripts", "read:customers"], ["read:transcripts"],
         760, 425, True, "IN"),
        ("Reachpoint Marketing", "Marketing automation", True,
         ["read:customers", "write:segments"], ["read:customers", "write:segments"],
         210, 1, True, "US"),
        ("Northgate BPO", "Operations outsourcing", True,
         ["read:customers"], ["read:customers"], 400, 3, True, "IN"),
        ("Ledgerline Reconciliation", "Finance operations", True,
         ["read:transactions"], ["read:transactions"], 150, 2, True, "IN"),
        ("SentinelWatch Fraud", "Fraud analytics", True,
         ["read:transactions"], ["read:transactions"], 190, 1, True, "IN"),
        ("Pinnacle Analytics", "Business intelligence", True,
         ["read:customers", "read:transactions"], ["read:transactions"],
         220, 9, True, "IN"),
        ("Courierly Dispatch", "Physical mail", True,
         ["read:customers"], ["read:customers"], 340, 14, True, "IN"),
        ("Meridian Group DW", "Parent reporting", True,
         ["read:customers", "read:transactions"],
         ["read:customers", "read:transactions"], 500, 1, True, "US"),
        ("Meridian EU Subsidiary", "Group entity", True,
         ["read:customers"], ["read:customers"], 500, 4, True, "DE"),
        ("HelpNest Service Desk", "Customer support", True,
         ["read:customers", "write:grievances"],
         ["read:customers", "write:grievances"], 170, 1, True, "IN"),
        ("Archivault Storage", "Records archival", True,
         ["read:kyc"], ["read:kyc"], 600, 30, True, "IN"),
        ("Quillmark Surveys", "Customer research", True,
         ["read:customers"], [], 290, 120, False, "IN"),
    ]

    rows: list[dict[str, Any]] = []
    for index, (
        name, category, has_dpa, granted, exercised,
        issued_ago, used_ago, active, country,
    ) in enumerate(specs):
        rows.append(
            {
                "name": name,
                "category": category,
                # Sequential, never hash(). Python randomises string hashing
                # per process unless PYTHONHASHSEED is pinned, so a hash here
                # would have quietly broken determinism between runs.
                "dpa_reference": f"DPA-{2000 + index:04d}" if has_dpa else None,
                "granted_scopes": granted,
                "exercised_scopes": exercised,
                "credential_issued_at": EPOCH - _days(issued_ago),
                "last_used_at": EPOCH - _days(used_ago),
                "is_active": active,
                "relationship_ended_at": None if active else EPOCH - _days(120),
                "country": country,
                "credential_token": (
                    f"svc_{name.split()[0].lower()}_"
                    f"{int(rng.integers(10**6, 10**7))}"
                ),
            }
        )
    return rows


def generate_predictions(
    rng: np.random.Generator, principals: list[dict[str, Any]]
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """MFS-CPS-v3 and 12,000 scored applications.

    Two defects. S7: the lowest group's selection rate is 0.71 of the
    highest, under the four-fifths threshold. S8: two features have drifted
    materially from the training distribution, and no drift monitoring
    exists to have noticed.
    """
    # Every member of the undersized group is scored, so the group appears in
    # the prediction set at exactly SMALL_GROUP_SIZE. Sampling it like the
    # others would leave a group whose size drifts seed to seed, and the point
    # of this group is that its size is known and deliberately too small.
    small_group = [
        i for i, p in enumerate(principals)
        if p["group_attribute"] == SMALL_GROUP_LABEL
    ]
    others = [
        i for i, p in enumerate(principals)
        if p["group_attribute"] != SMALL_GROUP_LABEL
    ]
    chosen_others = rng.choice(
        np.array(others), size=PREDICTION_COUNT - len(small_group), replace=False
    )
    sample_idx = np.concatenate([np.array(small_group), chosen_others])
    rng.shuffle(sample_idx)

    # Training baseline. Deciles for each feature, captured at training time.
    training_snapshot = {
        "features": {
            "income_band": {"mean": 6.0, "sd": 2.0},
            "months_at_address": {"mean": 48.0, "sd": 24.0},
            # Drifted since training: defect S8.
            "utilisation_ratio": {"mean": 0.35, "sd": 0.12},
            "enquiries_6m": {"mean": 1.8, "sd": 1.1},
        },
        "captured_at": (EPOCH - _days(540)).isoformat(),
    }

    model = {
        "name": "MFS-CPS-v3",
        "purpose": "Credit pre-screening of retail loan enquiries",
        "deployed_at": EPOCH - _days(480),
        "training_snapshot": training_snapshot,
        # Defect S8's second half: nothing was watching.
        "has_drift_monitoring": False,
        "is_consequential": True,
    }

    rows: list[dict[str, Any]] = []
    for position, idx in enumerate(sample_idx.tolist()):
        principal = principals[idx]
        group = principal["group_attribute"]

        features = {
            "income_band": float(rng.normal(6.0, 2.0)),
            "months_at_address": float(rng.normal(48.0, 24.0)),
            # Shifted distribution: mean 0.35 -> 0.58 drives PSI past 0.25.
            "utilisation_ratio": float(rng.normal(0.58, 0.14)),
            # Shifted distribution: mean 1.8 -> 3.4.
            "enquiries_6m": float(rng.normal(3.4, 1.3)),
        }

        approved = bool(rng.random() < GROUP_APPROVAL_RATE[group])
        decision = "APPROVE" if approved else "DECLINE"

        # Ground truth known for roughly a third, which is what makes equal
        # opportunity computable on a subset rather than the whole.
        has_truth = bool(rng.random() < 0.34)
        ground_truth = None
        if has_truth:
            ground_truth = "REPAID" if rng.random() < 0.82 else "DEFAULTED"

        rows.append(
            {
                "external_ref": principal["external_ref"],
                "features": features,
                "score": round(float(rng.random()), 6),
                "decision": decision,
                "ground_truth": ground_truth,
                "predicted_at": EPOCH - _days(float(rng.integers(1, 180))),
                "_group": group,
                "_position": position,
            }
        )

    return model, rows


def generate_transcripts(
    rng: np.random.Generator, principals: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Call transcripts, a tenth of which carry an unmasked PAN: defect S9.

    The identifier sits in free text inside an asset that declares no
    identifier classes and is unencrypted at rest. A detector that only reads
    structured columns never finds it, which is precisely why suite 1 scans
    free text.
    """
    rows: list[dict[str, Any]] = []
    sample_idx = rng.choice(len(principals), size=4_800, replace=False)

    for idx in sample_idx.tolist():
        principal = principals[idx]
        leaks_pan = bool(rng.random() < 0.10)
        if leaks_pan:
            body = (
                "Agent: Could you confirm your PAN for verification? "
                f"Customer: Yes, it is {principal['pan']}. "
                "Agent: Thank you, that matches our records."
            )
        else:
            body = (
                "Agent: How can I help today? Customer: I would like to check "
                "my statement. Agent: I can help with that."
            )
        rows.append({"external_ref": principal["external_ref"], "body": body})

    return rows


def generate_access_logs(
    rng: np.random.Generator, third_parties: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Access log entries, deliberately incomplete.

    Rule 6(1)(c) requires "visibility on the accessing of such personal data,
    through appropriate logs, monitoring and review". The gap seeded here is
    the one that matters: a slice of UNAUTHORISED access attempts produce no
    log entry at all. Probe P-08 tests the control on the control -- if an
    unauthorised access is refused but not recorded, Rule 6(1)(c) fails even
    though access control itself held.
    """
    rows: list[dict[str, Any]] = []
    actors = [tp["name"] for tp in third_parties] + [
        "svc_batch_reconciliation", "user_ops_desk", "svc_model_scoring",
    ]

    for _ in range(18_000):
        actor = actors[int(rng.integers(0, len(actors)))]
        authorised = bool(rng.random() < 0.985)

        # The defect: roughly a third of unauthorised attempts are never
        # written to the log, so they are invisible to review.
        if not authorised and rng.random() < 0.34:
            continue

        rows.append(
            {
                "actor_ref": actor,
                "asset_name": ("crm_customers", "kyc_documents",
                               "transaction_ledger", "call_transcripts")[
                    int(rng.integers(0, 4))
                ],
                "action": ("READ", "WRITE", "EXPORT")[int(rng.integers(0, 3))],
                "occurred_at": EPOCH - dt.timedelta(
                    minutes=int(rng.integers(1, 525_600))
                ),
                "was_authorised": authorised,
            }
        )

    rows.sort(key=lambda r: (r["occurred_at"], r["actor_ref"], r["action"]))
    return rows


# How many records are stored per sampled asset. Deliberately far below the
# asset's declared record_count: scanning 800 of 24,000 cannot establish that
# the other 23,200 are clean, and the gate should say so. Full coverage is
# kept only for call_transcripts, which is small enough to scan entirely --
# so the finding there is definitive rather than merely suggestive.
SAMPLED_RECORDS_PER_ASSET = 800


def generate_asset_records(
    rng: np.random.Generator,
    principals: list[dict[str, Any]],
    transcripts: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Rows of asset content for the assets suite 1 scans.

    Only a sample of the large assets is stored, on purpose. A scan that
    covers 3% of an estate and reports it clean has established very little,
    and making that visible is more useful than a convenient full copy.
    """
    rows: list[dict[str, Any]] = []
    sample = rng.choice(
        len(principals), size=SAMPLED_RECORDS_PER_ASSET, replace=False
    ).tolist()

    for idx in sample:
        p = principals[idx]
        rows.append(
            {
                "asset_name": "crm_customers",
                "external_ref": p["external_ref"],
                "content": {
                    "name": f"Customer {p['external_ref']}",
                    "email": p["email"],
                    "mobile": p["mobile"],
                    "account_number": p["account_number"],
                },
            }
        )
        # Declares aadhaar and pan, and holds them. The honest case, kept so
        # a finding elsewhere reads as a finding rather than as the norm.
        rows.append(
            {
                "asset_name": "kyc_documents",
                "external_ref": p["external_ref"],
                "content": {
                    "name": f"Customer {p['external_ref']}",
                    "aadhaar": p["aadhaar"],
                    "pan": p["pan"],
                },
            }
        )

    # Every transcript, because the asset is small enough to scan entirely.
    # Defect S9 lives in the ten per cent whose body carries a PAN the asset
    # never declared, in a store with no encryption at rest.
    for transcript in transcripts:
        rows.append(
            {
                "asset_name": "call_transcripts",
                "external_ref": transcript["external_ref"],
                "content": {"body": transcript["body"]},
            }
        )

    return rows


def generate_estate(seed: int) -> GeneratedEstate:
    """Build the whole estate from one seed. No I/O, no clock reads."""
    rng = np.random.default_rng(seed)

    estate = GeneratedEstate()
    estate.assets = generate_assets()
    estate.principals = generate_principals(rng)

    refs = [p["external_ref"] for p in estate.principals]
    estate.consents, estate.consent_events = generate_consents(rng, refs)
    estate.third_parties = generate_third_parties(rng)

    model, predictions = generate_predictions(rng, estate.principals)
    estate.models = [model]
    estate.predictions = predictions

    estate.access_logs = generate_access_logs(rng, estate.third_parties)
    estate.transcripts = generate_transcripts(rng, estate.principals)
    estate.asset_records = generate_asset_records(
        rng, estate.principals, estate.transcripts
    )
    return estate
