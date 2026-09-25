"""How the suites obtain the evidence they declared.

Kept apart from the procedures on purpose. A procedure says what it needs and
what it concludes; this module says where the bytes come from. Separating
them means a suite can be read as assurance logic without wading through SQL,
and a query can be changed without touching a verdict.
"""

from __future__ import annotations

from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.engine.collectors import register_probe, register_query
from app.models.estate import (
    AccessLog,
    AssetRecord,
    ConsentRecord,
    DataAsset,
    DataPrincipal,
    ModelPrediction,
    ModelRegistry,
    ProcessingActivity,
    ThirdParty,
)
from app.suites.access_probes import probe_access_exchanges
from app.suites.consent import probe_downstream, probe_journey

# Caps on what a single run pulls into memory. Large enough that coverage is
# a real question rather than a rigged one, small enough that a free-tier
# instance does not fall over.
MAX_PRINCIPALS = 24_000
MAX_RECORDS = 8_000
MAX_LOGS = 20_000


def _db(context: dict[str, Any]) -> Session:
    """The session the runner is executing in.

    Cast rather than typed on the context: the evidence context is a plain
    mapping the engine passes through untouched, so that suites can carry
    whatever they need without the engine knowing about it.
    """
    session = context["db"]
    assert isinstance(session, Session)
    return session


@register_query("data_assets")
def collect_data_assets(context: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "id": a.id,
            "name": a.name,
            "declared_identifier_classes": list(a.declared_identifier_classes),
            "encryption_at_rest": a.encryption_at_rest,
            "record_count": a.record_count,
            "hosted_region": a.hosted_region,
        }
        for a in _db(context).scalars(select(DataAsset).order_by(DataAsset.id)).all()
    ]


@register_query("asset_records")
def collect_asset_records(context: dict[str, Any]) -> list[dict[str, Any]]:
    """Ordered by id so a run is reproducible: an unordered LIMIT would
    return a different slice each time and quietly change the result."""
    return [
        {"asset_id": r.asset_id, "content": r.content}
        for r in _db(context)
        .scalars(select(AssetRecord).order_by(AssetRecord.id).limit(MAX_RECORDS))
        .all()
    ]


@register_query("data_principals")
def collect_data_principals(context: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "id": p.id,
            "external_ref": p.external_ref,
            "last_contact_at": p.last_contact_at,
            "erased_at": p.erased_at,
            "legal_hold": p.legal_hold,
            "legal_hold_basis": p.legal_hold_basis,
        }
        for p in _db(context)
        .scalars(
            select(DataPrincipal).order_by(DataPrincipal.id).limit(MAX_PRINCIPALS)
        )
        .all()
    ]


@register_query("processing_activities")
def collect_processing_activities(context: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "id": a.id,
            "purpose": a.purpose,
            "lawful_basis": a.lawful_basis,
            "retention_days": a.retention_days,
            "log_retention_days": a.log_retention_days,
        }
        for a in _db(context)
        .scalars(select(ProcessingActivity).order_by(ProcessingActivity.id))
        .all()
    ]


@register_query("access_logs")
def collect_access_logs(context: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "actor_ref": entry.actor_ref,
            "action": entry.action,
            "occurred_at": entry.occurred_at,
            "was_authorised": entry.was_authorised,
        }
        for entry in _db(context)
        .scalars(select(AccessLog).order_by(AccessLog.occurred_at).limit(MAX_LOGS))
        .all()
    ]


@register_query("consent_records")
def collect_consent_records(context: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "principal_id": c.principal_id,
            "purpose": c.purpose,
            "status": c.status,
            "granted_at": c.granted_at,
            "withdrawn_at": c.withdrawn_at,
            "downstream_synced_at": c.downstream_synced_at,
        }
        for c in _db(context).scalars(select(ConsentRecord)).all()
    ]


@register_query("third_parties")
def collect_third_parties(context: dict[str, Any]) -> list[dict[str, Any]]:
    """The processor inventory.

    `credential_token` is deliberately not selected. The first rows of every
    evidence payload are persisted as its summary, so a token read here would
    be written into the results table -- an assurance tool leaking the very
    credential it is assessing.
    """
    return [
        {
            "id": t.id,
            "name": t.name,
            "category": t.category,
            "dpa_reference": t.dpa_reference,
            "granted_scopes": list(t.granted_scopes or []),
            "exercised_scopes": list(t.exercised_scopes or []),
            "credential_issued_at": t.credential_issued_at,
            "last_used_at": t.last_used_at,
            "is_active": t.is_active,
            "relationship_ended_at": t.relationship_ended_at,
            "country": t.country,
        }
        for t in _db(context).scalars(select(ThirdParty).order_by(ThirdParty.id)).all()
    ]


@register_query("erased_principals")
def collect_erased_principals(context: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {"id": p.id, "external_ref": p.external_ref, "erased_at": p.erased_at}
        for p in _db(context)
        .scalars(
            select(DataPrincipal)
            .where(DataPrincipal.erased_at.is_not(None))
            .order_by(DataPrincipal.id)
        )
        .all()
    ]


@register_query("model_registry")
def collect_model_registry(context: dict[str, Any]) -> list[dict[str, Any]]:
    """Every registered model, with the training baseline drift is measured
    against. A model with no snapshot is returned too: its absence is a
    finding, not a reason to leave the model out."""
    return [
        {
            "id": m.id,
            "name": m.name,
            "purpose": m.purpose,
            "deployed_at": m.deployed_at,
            "training_snapshot": m.training_snapshot,
            "has_drift_monitoring": m.has_drift_monitoring,
            "is_consequential": m.is_consequential,
        }
        for m in _db(context).scalars(select(ModelRegistry).order_by(ModelRegistry.id)).all()
    ]


@register_query("model_predictions")
def collect_model_predictions(context: dict[str, Any]) -> list[dict[str, Any]]:
    """Every scored application, with the applicant's group.

    The group comes from the principal record, not from the model's inputs:
    the model never sees it, which is exactly why its outcomes have to be
    checked against it. Principal identity is reduced to the internal id,
    enough to detect duplicates without carrying names into evidence.
    """
    rows = _db(context).execute(
        select(
            ModelPrediction.id,
            ModelPrediction.model_id,
            ModelPrediction.principal_id,
            ModelPrediction.features,
            ModelPrediction.decision,
            ModelPrediction.ground_truth,
            DataPrincipal.group_attribute,
        )
        .join(DataPrincipal, DataPrincipal.id == ModelPrediction.principal_id, isouter=True)
        .order_by(ModelPrediction.id)
    ).all()
    return [
        {
            "id": r.id,
            "model_id": r.model_id,
            "principal_id": r.principal_id,
            "features": r.features,
            "decision": r.decision,
            "ground_truth": r.ground_truth,
            "group": r.group_attribute,
        }
        for r in rows
    ]


# Deliberately NOT registered: processor_erasure_instructions. Meridian keeps
# no record of erasure instructions sent to processors, so there is nothing
# to read, and DPDP-08-02 gates on G4. Registering a query that returned []
# would turn "no evidence" into "evidence of nothing", and the control would
# report every principal as a gap on the strength of a table that does not
# exist.


# --- Probes ----------------------------------------------------------------


@register_probe("grant_journey")
def probe_grant(context: dict[str, Any], client: httpx.Client) -> dict[str, Any]:
    return probe_journey(client, "grant")


@register_probe("withdrawal_journey")
def probe_withdrawal(context: dict[str, Any], client: httpx.Client) -> dict[str, Any]:
    return probe_journey(client, "withdraw")


@register_probe("downstream_segment")
def probe_segment(context: dict[str, Any], client: httpx.Client) -> dict[str, Any]:
    """Uses a fixed principal the target service knows about.

    The probe corroborates the stored latency against the downstream system's
    live belief; which principal it uses does not change the conclusion, and
    pinning it keeps runs reproducible.
    """
    return probe_downstream(client, "MFS001001")


@register_probe("probe_exchanges")
def probe_access_control(context: dict[str, Any], client: httpx.Client) -> dict[str, Any]:
    """Every access-control adversarial exchange, in one HTTP_PROBE payload.

    Four controls (ownership, input validation, log visibility, stale
    credential) all read from this single run rather than each re-probing
    the target: the log-visibility control specifically needs to see what
    the *other* probes' attempts produced, so they have to share one
    exchange rather than run independently.
    """
    return probe_access_exchanges(client)
