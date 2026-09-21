"""Control library and engagement endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.schemas import ClauseRef, ControlDetail, ControlSummary, EngagementSummary
from app.db import get_db
from app.models.control import Control, Engagement, EngagementControl

router = APIRouter()


def _scope_index(db: Session) -> dict[int, EngagementControl]:
    """Scoping for the demo engagement, keyed by control id.

    v1 has a single engagement. When multi-engagement arrives this becomes a
    parameter rather than a lookup.
    """
    engagement = db.scalar(select(Engagement).order_by(Engagement.id).limit(1))
    if engagement is None:
        return {}
    rows = db.scalars(
        select(EngagementControl).where(
            EngagementControl.engagement_id == engagement.id
        )
    ).all()
    return {row.control_id: row for row in rows}


def _summary(control: Control, scoped: EngagementControl | None) -> ControlSummary:
    primary = control.primary_mapping
    procedure = control.procedures[0] if control.procedures else None

    return ControlSummary(
        ref=control.ref,
        title=control.title,
        domain=control.domain,
        inference_mode=control.inference_mode,
        is_executable=control.is_executable,
        suite=procedure.suite if procedure else None,
        primary_clause=primary.clause.ref if primary else None,
        primary_framework=primary.clause.framework.code if primary else None,
        framework_refs=sorted(
            {m.clause.framework.code for m in control.mappings}
        ),
        in_scope=scoped.in_scope if scoped else True,
        na_reason=scoped.na_reason if scoped else None,
        evidence_owner=scoped.evidence_owner if scoped else None,
        primary_source_unverified=(
            primary is not None and primary.clause.source_status == "UNVERIFIED"
        ),
    )


@router.get("/controls", response_model=list[ControlSummary])
def list_controls(
    db: Session = Depends(get_db),
    domain: str | None = Query(None),
    framework: str | None = Query(None),
    executable: bool | None = Query(None),
    in_scope: bool | None = Query(None),
) -> list[ControlSummary]:
    stmt = (
        select(Control)
        .options(
            selectinload(Control.mappings),
            selectinload(Control.procedures),
        )
        .order_by(Control.ref)
    )
    if domain:
        stmt = stmt.where(Control.domain == domain)
    if executable is not None:
        stmt = stmt.where(Control.is_executable == executable)

    scope = _scope_index(db)
    rows = [_summary(c, scope.get(c.id)) for c in db.scalars(stmt).all()]

    # Framework and scope filters apply after assembly: both depend on joined
    # state that is cheaper to filter in Python for a 25-row library than to
    # express as a correlated subquery.
    if framework:
        rows = [r for r in rows if framework in r.framework_refs]
    if in_scope is not None:
        rows = [r for r in rows if r.in_scope == in_scope]
    return rows


@router.get("/controls/{ref}", response_model=ControlDetail)
def get_control(ref: str, db: Session = Depends(get_db)) -> ControlDetail:
    control = db.scalar(
        select(Control)
        .where(Control.ref == ref)
        .options(
            selectinload(Control.mappings),
            selectinload(Control.procedures),
        )
    )
    if control is None:
        raise HTTPException(status_code=404, detail=f"No control with ref {ref}")

    scoped = _scope_index(db).get(control.id)
    procedure = control.procedures[0] if control.procedures else None

    clauses = [
        ClauseRef(
            framework_code=m.clause.framework.code,
            framework_name=m.clause.framework.name,
            ref=m.clause.ref,
            title=m.clause.title,
            verbatim_text=m.clause.verbatim_text,
            in_force_from=m.clause.in_force_from,
            source_status=m.clause.source_status,
            source_note=m.clause.source_note,
            is_primary=m.is_primary,
            rationale=m.rationale,
        )
        # Primary first, then by framework and ref, so the legal basis leads.
        for m in sorted(
            control.mappings,
            key=lambda m: (not m.is_primary, m.clause.framework.code, m.clause.ref),
        )
    ]

    return ControlDetail(
        **_summary(control, scoped).model_dump(),
        objective=control.objective,
        procedure_text=control.procedure_text,
        auto_raise=control.auto_raise,
        threshold_overrides=control.threshold_overrides,
        yaml_source=control.yaml_source,
        plugin_key=procedure.plugin_key if procedure else None,
        evidence_contract=procedure.evidence_contract if procedure else None,
        clauses=clauses,
    )


@router.get("/engagement", response_model=EngagementSummary)
def get_engagement(db: Session = Depends(get_db)) -> EngagementSummary:
    engagement = db.scalar(
        select(Engagement)
        .options(selectinload(Engagement.organization))
        .order_by(Engagement.id)
        .limit(1)
    )
    if engagement is None:
        raise HTTPException(
            status_code=404,
            detail="No engagement seeded. Run `python -m app.seed`.",
        )

    controls = db.scalars(select(Control)).all()
    scope = _scope_index(db)

    return EngagementSummary(
        id=engagement.id,
        name=engagement.name,
        scope_note=engagement.scope_note,
        compliance_deadline=engagement.compliance_deadline,
        organization=engagement.organization.name,
        city=engagement.organization.city,
        sector=engagement.organization.sector,
        headcount=engagement.organization.headcount,
        is_significant_data_fiduciary=(
            engagement.organization.is_significant_data_fiduciary
        ),
        is_synthetic=engagement.organization.is_synthetic,
        control_count=len(controls),
        executable_count=sum(1 for c in controls if c.is_executable),
        out_of_scope_count=sum(1 for s in scope.values() if not s.in_scope),
    )
