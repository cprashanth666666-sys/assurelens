"""Persist the generated estate for Meridian.

Idempotent by replacement: the estate is wholly derived from a seed, so the
honest way to re-seed is to delete what was there and regenerate, not to
reconcile row by row. The control library is different — it is edited by hand
and upserted — which is why the two live in separate modules.

Bulk inserts throughout, and specifically `insert(_table(Model))` rather
than `insert(Model)`. The latter is an ORM bulk insert that fetches primary
keys back, which degrades to one `INSERT ... RETURNING` per row: 24,000
principals took nine minutes instead of seven seconds. Nothing here needs the
generated keys -- they are read back in one query afterwards -- so the Core
executemany path is both faster and more honest about what it does.
"""

from __future__ import annotations

import logging
from typing import Any, cast

from sqlalchemy import Table, delete, func, insert, select
from sqlalchemy.orm import Session

from app.models.control import Organization
from app.models.estate import (
    AccessLog,
    ConsentEvent,
    ConsentRecord,
    DataAsset,
    DataPrincipal,
    ModelAssessment,
    ModelPrediction,
    ModelRegistry,
    ProcessingActivity,
    ThirdParty,
)
from app.seed.generator import GeneratedEstate, generate_estate

log = logging.getLogger(__name__)


def _table(model: type[Any]) -> Table:
    """The Table behind a mapped class.

    SQLAlchemy declares `__table__` as FromClause, which is accurate for the
    general case and wrong for every mapped class here. Casting once keeps the
    Core-insert call sites readable instead of carrying nine type ignores.
    """
    return cast(Table, model.__table__)

# Delete order matters: children before parents, so foreign keys hold at every
# intermediate step rather than relying on cascade ordering.
_WIPE_ORDER = (
    ModelAssessment,
    ModelPrediction,
    ModelRegistry,
    ConsentEvent,
    ConsentRecord,
    AccessLog,
    ThirdParty,
    DataPrincipal,
    ProcessingActivity,
    DataAsset,
)


def _org(db: Session) -> Organization:
    org = db.scalar(select(Organization).order_by(Organization.id).limit(1))
    if org is None:
        raise RuntimeError(
            "No organisation seeded. Run the control library seed first: "
            "the estate belongs to an engagement, not the other way round."
        )
    return org


def wipe_estate(db: Session) -> None:
    """Empty the estate tables.

    `synchronize_session=False` is load-bearing, not a micro-optimisation.
    The default strategy loads every deleted row into the session's identity
    map so in-memory objects can be reconciled -- roughly 110,000 objects for
    this estate. Every later flush then walks that map, which turned a
    seven-second re-seed into nine minutes. Nothing here reads those objects
    afterwards, so there is nothing to synchronise.
    """
    for model in _WIPE_ORDER:
        db.execute(delete(model).execution_options(synchronize_session=False))
    db.expunge_all()
    db.flush()


def persist_estate(db: Session, estate: GeneratedEstate, org_id: int) -> dict[str, int]:
    """Write the generated estate. Assumes the tables are empty."""
    # --- Assets and activities ---------------------------------------------
    db.execute(
        insert(_table(DataAsset)),
        [{**a, "org_id": org_id} for a in estate.assets],
    )
    db.flush()

    asset_ids = {
        name: asset_id
        for asset_id, name in db.execute(
            select(DataAsset.id, DataAsset.name)
        ).all()
    }

    from app.seed.generator import generate_activities

    db.execute(
        insert(_table(ProcessingActivity)),
        [{**a, "org_id": org_id} for a in generate_activities(asset_ids)],
    )

    # --- Principals --------------------------------------------------------
    # The generated rows carry identifier columns the schema does not hold:
    # aadhaar, pan, mobile and the rest live in the asset content that suite 1
    # scans, not on the principal row. Stripping them here keeps the estate
    # honest about where personal data actually sits.
    principal_columns = {
        "external_ref", "last_contact_at", "erased_at", "legal_hold",
        "legal_hold_basis", "pre_erasure_notice_at", "group_attribute",
        "is_minor",
    }
    db.execute(
        insert(_table(DataPrincipal)),
        [
            {k: v for k, v in p.items() if k in principal_columns}
            | {"org_id": org_id}
            for p in estate.principals
        ],
    )
    db.flush()

    principal_ids = {
        ref: pid
        for pid, ref in db.execute(
            select(DataPrincipal.id, DataPrincipal.external_ref)
        ).all()
    }

    # --- Consent -----------------------------------------------------------
    db.execute(
        insert(_table(ConsentRecord)),
        [
            {
                "principal_id": principal_ids[c["external_ref"]],
                "purpose": c["purpose"],
                "status": c["status"],
                "granted_at": c["granted_at"],
                "withdrawn_at": c["withdrawn_at"],
                "downstream_synced_at": c["downstream_synced_at"],
            }
            for c in estate.consents
        ],
    )
    db.flush()

    consent_ids = {
        pid: cid
        for cid, pid in db.execute(
            select(ConsentRecord.id, ConsentRecord.principal_id)
        ).all()
    }

    db.execute(
        insert(_table(ConsentEvent)),
        [
            {
                "consent_id": consent_ids[principal_ids[e["external_ref"]]],
                "event": e["event"],
                "occurred_at": e["occurred_at"],
                "latency_ms": e["latency_ms"],
            }
            for e in estate.consent_events
        ],
    )

    # --- Processors --------------------------------------------------------
    db.execute(
        insert(_table(ThirdParty)),
        [{**t, "org_id": org_id} for t in estate.third_parties],
    )

    # --- Access logs -------------------------------------------------------
    db.execute(
        insert(_table(AccessLog)),
        [
            {
                "org_id": org_id,
                "actor_ref": r["actor_ref"],
                "asset_id": asset_ids.get(r["asset_name"]),
                "action": r["action"],
                "occurred_at": r["occurred_at"],
                "was_authorised": r["was_authorised"],
            }
            for r in estate.access_logs
        ],
    )

    # --- Model and predictions ---------------------------------------------
    db.execute(
        insert(_table(ModelRegistry)),
        [{**m, "org_id": org_id} for m in estate.models],
    )
    db.flush()

    model_id = db.scalar(select(ModelRegistry.id).limit(1))

    db.execute(
        insert(_table(ModelPrediction)),
        [
            {
                "model_id": model_id,
                "principal_id": principal_ids[p["external_ref"]],
                "features": p["features"],
                "score": p["score"],
                "decision": p["decision"],
                "ground_truth": p["ground_truth"],
                "predicted_at": p["predicted_at"],
            }
            for p in estate.predictions
        ],
    )

    db.flush()
    return {
        "assets": len(estate.assets),
        "principals": len(estate.principals),
        "consents": len(estate.consents),
        "consent_events": len(estate.consent_events),
        "third_parties": len(estate.third_parties),
        "access_logs": len(estate.access_logs),
        "predictions": len(estate.predictions),
    }


def estate_is_populated(db: Session) -> bool:
    return bool(db.scalar(select(func.count()).select_from(DataPrincipal)))


def load_estate(
    db: Session, seed: int, *, force: bool = False
) -> dict[str, Any]:
    """Generate and persist Meridian's estate from a seed.

    Skips when the estate already exists, because this runs on every boot and
    the estate is bulk data derived from a seed -- rebuilding it changes
    nothing. That matters more than it sounds: seeding 24,000 principals takes
    seconds against a local database and minutes across a network, which is
    long enough to fail a platform health check and leave the service flapping
    on restart.

    `force=True` re-seeds anyway, which is what the demo reset endpoint wants.
    """
    org = _org(db)

    if not force and estate_is_populated(db):
        existing = db.scalar(select(func.count()).select_from(DataPrincipal))
        log.info("estate already populated (%d principals); skipping", existing)
        return {"skipped": True, "principals": existing or 0, "seed": seed}

    wipe_estate(db)
    estate = generate_estate(seed)
    counts = persist_estate(db, estate, org.id)
    counts["seed"] = seed
    counts["skipped"] = False
    return counts
