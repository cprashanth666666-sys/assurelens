"""Findings register and remediation roadmap. [Day 8]

v1 has a single engagement, matching `controls.py`'s own lookup, so every
route here resolves it the same way rather than trusting a path parameter
the frontend never actually varies.
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.engine.findings import band_severity
from app.models.control import Control, Engagement
from app.models.findings import Finding, FindingHistory

router = APIRouter()


class FindingHistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    changed_at: dt.datetime
    field: str
    old_value: str | None
    new_value: str | None


class FindingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ref: str
    control_ref: str
    control_title: str
    domain: str
    title: str
    description: str
    root_cause: str | None
    recommendation: str | None
    likelihood: int
    impact: int
    risk_score: int
    severity: str
    owner: str | None
    effort_days: float | None
    status: str
    is_internal_note_only: bool
    created_at: dt.datetime
    updated_at: dt.datetime


class FindingDetail(FindingOut):
    origin_result_id: int | None
    history: list[FindingHistoryOut]


class FindingUpdate(BaseModel):
    """Every field optional: a PATCH touches only what it names. Likelihood
    and impact are editable -- a consultant's judgement can override the
    auto-computed starting point -- and severity is always recomputed from
    whichever pair is now current, never left stale against an edited one."""

    title: str | None = None
    description: str | None = None
    root_cause: str | None = None
    recommendation: str | None = None
    likelihood: int | None = Field(default=None, ge=1, le=5)
    impact: int | None = Field(default=None, ge=1, le=5)
    owner: str | None = None
    effort_days: Decimal | None = None
    status: str | None = None
    is_internal_note_only: bool | None = None


class RoadmapItem(BaseModel):
    """One row: the finding, its cost and value, and where the ordering
    rule puts it. `priority` is impact ÷ effort, computed fresh on every
    request rather than stored, so it can never drift from the numbers it
    was built from."""

    sequence: int
    ref: str
    control_ref: str
    action: str
    owner: str | None
    effort_days: float
    impact: int
    likelihood: int
    severity: str
    priority: float
    expected_residual_reduction: int


class RoadmapOut(BaseModel):
    ordering_rule: str
    items: list[RoadmapItem]


VALID_STATUSES = ("OPEN", "IN_REMEDIATION", "RETEST_PENDING", "CLOSED", "ACCEPTED_RISK")

ORDERING_RULE = (
    "Ordered by impact ÷ effort (days), highest first: the finding that "
    "removes the most risk per day of work goes first. Ties broken by risk "
    "score, then by finding ref."
)


def _to_out(finding: Finding, control: Control) -> FindingOut:
    return FindingOut(
        ref=finding.ref,
        control_ref=control.ref,
        control_title=control.title,
        domain=control.domain,
        title=finding.title,
        description=finding.description,
        root_cause=finding.root_cause,
        recommendation=finding.recommendation,
        likelihood=finding.likelihood,
        impact=finding.impact,
        risk_score=finding.risk_score,
        severity=finding.severity,
        owner=finding.owner,
        effort_days=float(finding.effort_days) if finding.effort_days is not None else None,
        status=finding.status,
        is_internal_note_only=finding.is_internal_note_only,
        created_at=finding.created_at,
        updated_at=finding.updated_at,
    )


@router.get("/engagements/{engagement_id}/findings", response_model=list[FindingOut])
def list_findings(
    engagement_id: int,
    domain: str | None = None,
    severity: str | None = None,
    status_: str | None = Query(default=None, alias="status"),
    likelihood: int | None = None,
    impact: int | None = None,
    db: Session = Depends(get_db),
) -> list[FindingOut]:
    """Filterable for the heatmap: a cell click passes `likelihood` and
    `impact` and gets back exactly the findings plotted in that cell."""
    engagement = db.get(Engagement, engagement_id)
    if engagement is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Engagement not found.")

    findings = db.scalars(
        select(Finding)
        .where(Finding.engagement_id == engagement_id)
        .order_by(Finding.risk_score.desc(), Finding.ref)
    ).all()
    controls = {
        c.id: c for c in db.scalars(
            select(Control).where(Control.id.in_({f.control_id for f in findings}))
        ).all()
    }

    rows = []
    for f in findings:
        control = controls[f.control_id]
        if domain and control.domain != domain:
            continue
        if severity and f.severity != severity:
            continue
        if status_ and f.status != status_:
            continue
        if likelihood is not None and f.likelihood != likelihood:
            continue
        if impact is not None and f.impact != impact:
            continue
        rows.append(_to_out(f, control))
    return rows


@router.get("/findings/{ref}", response_model=FindingDetail)
def get_finding(ref: str, db: Session = Depends(get_db)) -> FindingDetail:
    finding = db.scalar(select(Finding).where(Finding.ref == ref))
    if finding is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Finding not found.")
    control = db.get(Control, finding.control_id)
    assert control is not None
    base = _to_out(finding, control)
    history = db.scalars(
        select(FindingHistory)
        .where(FindingHistory.finding_id == finding.id)
        .order_by(FindingHistory.changed_at)
    ).all()
    return FindingDetail(
        **base.model_dump(),
        origin_result_id=finding.origin_result_id,
        history=[FindingHistoryOut.model_validate(h) for h in history],
    )


@router.patch("/findings/{ref}", response_model=FindingDetail)
def update_finding(
    ref: str, body: FindingUpdate, db: Session = Depends(get_db)
) -> FindingDetail:
    finding = db.scalar(select(Finding).where(Finding.ref == ref))
    if finding is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Finding not found.")

    if body.status is not None and body.status not in VALID_STATUSES:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            f"status must be one of {VALID_STATUSES}.",
        )

    changes = body.model_dump(exclude_unset=True)
    for field, new_value in changes.items():
        old_value = getattr(finding, field)
        if old_value == new_value:
            continue
        db.add(FindingHistory(
            finding_id=finding.id, field=field,
            old_value=None if old_value is None else str(old_value),
            new_value=None if new_value is None else str(new_value),
        ))
        setattr(finding, field, new_value)

    if "likelihood" in changes or "impact" in changes:
        new_severity = band_severity(finding.likelihood * finding.impact)
        if new_severity != finding.severity:
            db.add(FindingHistory(
                finding_id=finding.id, field="severity",
                old_value=finding.severity, new_value=new_severity,
            ))
            finding.severity = new_severity

    finding.updated_at = dt.datetime.now(dt.UTC)
    db.commit()
    db.refresh(finding)

    control = db.get(Control, finding.control_id)
    assert control is not None
    base = _to_out(finding, control)
    history = db.scalars(
        select(FindingHistory)
        .where(FindingHistory.finding_id == finding.id)
        .order_by(FindingHistory.changed_at)
    ).all()
    return FindingDetail(
        **base.model_dump(),
        origin_result_id=finding.origin_result_id,
        history=[FindingHistoryOut.model_validate(h) for h in history],
    )


@router.get("/engagements/{engagement_id}/roadmap", response_model=RoadmapOut)
def get_roadmap(engagement_id: int, db: Session = Depends(get_db)) -> RoadmapOut:
    """The 90-day plan: every open finding, ranked by impact per day of
    effort. Nothing here is stored pre-ranked -- the rank is recomputed on
    every request from the same `effort_days` and `impact` a reader can see
    on the finding itself, so the order printed always matches the numbers
    printed beside it."""
    engagement = db.get(Engagement, engagement_id)
    if engagement is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Engagement not found.")

    findings = db.scalars(
        select(Finding).where(
            Finding.engagement_id == engagement_id,
            Finding.status.in_(("OPEN", "IN_REMEDIATION", "RETEST_PENDING")),
        )
    ).all()
    controls = {
        c.id: c for c in db.scalars(
            select(Control).where(Control.id.in_({f.control_id for f in findings}))
        ).all()
    }

    scored = []
    for f in findings:
        # `effort_days` is unset means "not yet estimated"; falls back to
        # 1.0. An explicit 0 (already fixed, zero days remaining) is a real
        # value and must survive to the displayed effort -- only the
        # priority division gets a floor, so a free fix still ranks first
        # rather than crashing on a division by zero.
        effort = float(f.effort_days) if f.effort_days is not None else 1.0
        priority = f.impact / max(effort, 0.1)
        scored.append((priority, f, controls[f.control_id], effort))

    scored.sort(key=lambda row: (-row[0], -row[1].risk_score, row[1].ref))

    items = [
        RoadmapItem(
            sequence=i + 1,
            ref=f.ref,
            control_ref=control.ref,
            action=f.recommendation or f"Remediate {control.ref}: {f.title}",
            owner=f.owner,
            effort_days=effort,
            impact=f.impact,
            likelihood=f.likelihood,
            severity=f.severity,
            priority=round(priority, 3),
            # A finding fixed outright removes the risk its own score
            # represents; nothing here claims a partial fix would do less.
            expected_residual_reduction=f.risk_score,
        )
        for i, (priority, f, control, effort) in enumerate(scored)
    ]
    return RoadmapOut(ordering_rule=ORDERING_RULE, items=items)
