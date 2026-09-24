"""Control library and engagement endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.api.schemas import ClauseRef, ControlDetail, ControlSummary, EngagementSummary
from app.db import get_db
from app.models.control import Control, Engagement, EngagementControl
from app.models.results import TestResult, TestRun

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


# --- Readiness: overview, heatmap, evidence quality --------------------------
#
# Five real states, not the four the brief names, because a fourth state
# ("Insufficient evidence") only exists for a control the gate actually
# ran and gated. A documented control has no TestProcedure at all, and the
# runner's own loop skips it outright -- no TestResult row is ever created
# for one. Reporting it as "insufficient evidence" would be exactly the
# fabrication this project refuses everywhere else: a gate reason nobody
# computed, attached to a control nobody ran. It is its own state,
# "not measured", alongside an executable control a run has not reached yet.


class DomainReadiness(BaseModel):
    domain: str
    total: int
    pass_: int
    fail: int
    insufficient_evidence: int
    not_measured: int
    not_applicable: int
    # Share of the domain a verdict actually exists for -- pass, fail or
    # insufficient evidence all count, because each is a real conclusion
    # about a control that was run. [PRD 7.3: never a single headline %]
    coverage_pct: float


class EvidenceQuality(BaseModel):
    sufficient: int
    thin: int
    no_evidence: int
    total: int


class ReadinessOut(BaseModel):
    by_domain: list[DomainReadiness]
    evidence_quality: EvidenceQuality
    heatmap_note: str


HEATMAP_NOTE = (
    "Findings plotted by their likelihood x impact cell, both 1-5. A cell "
    "with a count is not itself a finding; click it to filter the register."
)


def _latest_results(db: Session, engagement_id: int) -> dict[int, TestResult]:
    """The most recent TestResult per control, for this engagement's run
    history. `max(id)` rather than `max(run_at)`: ids are append-only and
    strictly increasing, so it is exact where two results could in
    principle share a timestamp."""
    latest_ids = select(func.max(TestResult.id)).join(
        TestRun, TestRun.id == TestResult.run_id
    ).where(TestRun.engagement_id == engagement_id).group_by(TestResult.control_id)

    rows = db.scalars(select(TestResult).where(TestResult.id.in_(latest_ids))).all()
    return {r.control_id: r for r in rows}


@router.get("/engagements/{engagement_id}/readiness", response_model=ReadinessOut)
def get_readiness(engagement_id: int, db: Session = Depends(get_db)) -> ReadinessOut:
    engagement = db.get(Engagement, engagement_id)
    if engagement is None:
        raise HTTPException(status_code=404, detail="Engagement not found.")

    controls = db.scalars(select(Control)).all()
    scope = _scope_index(db)
    latest = _latest_results(db, engagement_id)

    by_domain: dict[str, dict[str, int]] = {}
    quality = {"sufficient": 0, "thin": 0, "no_evidence": 0}

    for control in controls:
        row = by_domain.setdefault(
            control.domain,
            {"total": 0, "PASS": 0, "FAIL": 0, "INSUFFICIENT_EVIDENCE": 0,
             "NOT_MEASURED": 0, "NOT_APPLICABLE": 0},
        )
        row["total"] += 1

        scoped = scope.get(control.id)
        if scoped is not None and not scoped.in_scope:
            row["NOT_APPLICABLE"] += 1
            continue

        result = latest.get(control.id)
        if result is None:
            row["NOT_MEASURED"] += 1
            quality["no_evidence"] += 1
            continue

        if result.verdict == "NOT_APPLICABLE":
            # The runner's own applicability check, distinct from the scope
            # table's in_scope flag handled above -- still not evidence.
            row["NOT_APPLICABLE"] += 1
            continue
        row[result.verdict] = row.get(result.verdict, 0) + 1
        if result.verdict == "INSUFFICIENT_EVIDENCE":
            quality["thin"] += 1
        else:
            quality["sufficient"] += 1

    domains = [
        DomainReadiness(
            domain=domain,
            total=row["total"],
            pass_=row["PASS"],
            fail=row["FAIL"],
            insufficient_evidence=row["INSUFFICIENT_EVIDENCE"],
            not_measured=row["NOT_MEASURED"],
            not_applicable=row["NOT_APPLICABLE"],
            # Out of the controls that could have produced a verdict, not
            # out of the domain's raw count -- a control ruled not
            # applicable was never eligible to be "covered" or not.
            coverage_pct=round(
                100.0 * (row["PASS"] + row["FAIL"] + row["INSUFFICIENT_EVIDENCE"])
                / (row["total"] - row["NOT_APPLICABLE"]),
                1,
            ) if row["total"] - row["NOT_APPLICABLE"] else 0.0,
        )
        for domain, row in sorted(by_domain.items())
    ]

    total_quality = sum(quality.values())
    return ReadinessOut(
        by_domain=domains,
        evidence_quality=EvidenceQuality(**quality, total=total_quality),
        heatmap_note=HEATMAP_NOTE,
    )
