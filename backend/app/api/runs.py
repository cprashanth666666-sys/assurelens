"""Test run endpoints.

The engine is reachable only through these. Runs execute synchronously: the
whole suite set completes in well under the plan's 45-second budget, and a
job queue would add a failure mode for no benefit at this size. The console
polls `GET /api/runs/{id}` regardless, so moving to async later changes
nothing the client can observe.
"""

from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.config import Settings, get_settings
from app.db import get_db
from app.engine import runner
from app.engine.collectors import default_broker, registered_evidence
from app.models.control import Control, Engagement
from app.models.results import AuditEntry, TestResult, TestRun
from app.reporting.summary import build_summary
from app.reporting.workpaper import build_workpaper

router = APIRouter()


class RunRequest(BaseModel):
    # At least one suite: running nothing would report a clean, empty
    # assessment, which is the most misleading result this product could give.
    suite_ids: list[str] = Field(min_length=1)
    seed: int | None = None


class ResultSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    control_ref: str
    control_title: str
    verdict: str
    raw_outcome: str | None
    gate_fired: bool
    gate_reasons: list[str]
    gate_explanations: list[str]
    gate_remedies: list[str]

    sample_size: int | None
    population_size: int | None
    successes: int | None
    coverage_pct: float | None
    point_estimate: float | None
    ci_lower: float | None
    ci_upper: float | None
    ci_method: str | None

    thresholds_applied: dict[str, object]
    threshold_overrides: dict[str, object]
    duration_ms: int | None


class RunSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    engagement_id: int
    seed: int
    suites: list[str]
    status: str
    started_at: dt.datetime
    completed_at: dt.datetime | None
    engine_version: str
    error: str | None
    result_count: int


class RunDetail(RunSummary):
    results: list[ResultSummary]


class EvidenceOut(BaseModel):
    """What was collected, as persisted: a label, a content hash that pins
    the exact bytes, and a summary. The full payload is never stored."""

    label: str
    kind: str
    source_ref: str | None
    content_hash: str
    collected_at: dt.datetime
    summary: object | None


class ControlResult(ResultSummary):
    """The latest result for one control, with what the procedure found.

    `detail` is where a procedure records its exceptions -- the ranked
    processor list, the unencrypted assets -- and it is what the evidence
    viewer shows. Evidence rows carry the hash and a summary; the detail
    carries the finding.
    """

    run_id: int
    seed: int
    completed_at: dt.datetime | None
    detail: dict[str, object]
    evidence: list[EvidenceOut]


def _summarise(run: TestRun, results: list[TestResult]) -> RunSummary:
    return RunSummary(
        id=run.id,
        engagement_id=run.engagement_id,
        seed=run.seed,
        suites=list(run.suites),
        status=run.status,
        started_at=run.started_at,
        completed_at=run.completed_at,
        engine_version=run.engine_version,
        error=run.error,
        result_count=len(results),
    )


def _result_rows(db: Session, run_id: int) -> list[TestResult]:
    return list(
        db.scalars(
            select(TestResult)
            .where(TestResult.run_id == run_id)
            .order_by(TestResult.id)
        ).all()
    )


def _to_summary(result: TestResult, controls: dict[int, Control]) -> ResultSummary:
    control = controls[result.control_id]
    return ResultSummary(
        id=result.id,
        control_ref=control.ref,
        control_title=control.title,
        verdict=result.verdict,
        raw_outcome=result.raw_outcome,
        gate_fired=result.gate_fired,
        gate_reasons=list(result.gate_reasons),
        gate_explanations=list(result.gate_explanations),
        gate_remedies=list(result.gate_remedies),
        sample_size=result.sample_size,
        population_size=result.population_size,
        successes=result.successes,
        coverage_pct=float(result.coverage_pct) if result.coverage_pct is not None else None,
        point_estimate=(
            float(result.point_estimate) if result.point_estimate is not None else None
        ),
        ci_lower=float(result.ci_lower) if result.ci_lower is not None else None,
        ci_upper=float(result.ci_upper) if result.ci_upper is not None else None,
        ci_method=result.ci_method,
        thresholds_applied=result.thresholds_applied,
        threshold_overrides=result.threshold_overrides,
        duration_ms=result.duration_ms,
    )


@router.post(
    "/engagements/{engagement_id}/runs",
    response_model=RunSummary,
    status_code=status.HTTP_201_CREATED,
)
def start_run(
    engagement_id: int,
    request: RunRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> RunSummary:
    engagement = db.get(Engagement, engagement_id)
    if engagement is None:
        raise HTTPException(status_code=404, detail=f"No engagement {engagement_id}")

    # Falls back to the configured default rather than something arbitrary:
    # a run whose seed nobody recorded cannot be regenerated, which makes its
    # results an assertion rather than a finding.
    seed = request.seed if request.seed is not None else settings.default_seed

    run = runner.run_suites(
        db,
        engagement_id=engagement_id,
        suites=request.suite_ids,
        seed=seed,
        broker=default_broker(),
        engine_version=settings.engine_version,
    )
    db.commit()

    return _summarise(run, _result_rows(db, run.id))


@router.get("/engagements/{engagement_id}/runs", response_model=list[RunSummary])
def list_runs(
    engagement_id: int, db: Session = Depends(get_db)
) -> list[RunSummary]:
    runs = db.scalars(
        select(TestRun)
        .where(TestRun.engagement_id == engagement_id)
        .order_by(TestRun.id.desc())
        .limit(50)
    ).all()
    return [_summarise(r, _result_rows(db, r.id)) for r in runs]


@router.get("/engagements/{engagement_id}/summary")
def get_summary(engagement_id: int, db: Session = Depends(get_db)) -> Response:
    """The one-page executive summary DOCX. [PRD 7.2, S5]

    Engagement-scoped, not run-scoped: it reads the engagement's current
    readiness and roadmap, the same live state the overview page shows.
    """
    try:
        content = build_summary(db, engagement_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    db.add(
        AuditEntry(
            action="REPORT_EXPORTED",
            entity_type="engagement",
            entity_id=str(engagement_id),
            detail={"format": "executive_summary_docx"},
        )
    )
    db.commit()

    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": (
                f'attachment; filename="assurelens-summary-{engagement_id}.docx"'
            )
        },
    )


@router.get("/runs/{run_id}", response_model=RunDetail)
def get_run(run_id: int, db: Session = Depends(get_db)) -> RunDetail:
    run = db.scalar(
        select(TestRun).where(TestRun.id == run_id).options(selectinload(TestRun.results))
    )
    if run is None:
        raise HTTPException(status_code=404, detail=f"No run {run_id}")

    results = _result_rows(db, run.id)
    controls = {
        c.id: c
        for c in db.scalars(
            select(Control).where(
                Control.id.in_([r.control_id for r in results] or [0])
            )
        ).all()
    }

    return RunDetail(
        **_summarise(run, results).model_dump(),
        results=[_to_summary(r, controls) for r in results],
    )


@router.get("/runs/{run_id}/workpaper")
def get_workpaper(run_id: int, db: Session = Depends(get_db)) -> Response:
    """The DOCX workpaper for one run. [PRD 7.1, M9]

    A GET, not a POST: exporting a document a second time changes nothing
    about the run it describes, and a GET is what a plain link/download
    button issues without extra client code.
    """
    try:
        content = build_workpaper(db, run_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    db.add(
        AuditEntry(
            action="REPORT_EXPORTED",
            entity_type="test_run",
            entity_id=str(run_id),
            detail={"format": "workpaper_docx"},
        )
    )
    db.commit()

    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f'attachment; filename="assurelens-workpaper-run-{run_id}.docx"'
        },
    )


@router.get("/controls/{ref}/latest-result", response_model=ControlResult | None)
def latest_result(ref: str, db: Session = Depends(get_db)) -> ControlResult | None:
    """The most recent result for a control, or null if it has never run.

    Null rather than 404: "this control has not been tested yet" is a normal
    state the page should render, not an error the client has to catch.
    """
    control = db.scalar(select(Control).where(Control.ref == ref))
    if control is None:
        raise HTTPException(status_code=404, detail=f"No control with ref {ref}")

    result = db.scalar(
        select(TestResult)
        .where(TestResult.control_id == control.id)
        .order_by(TestResult.id.desc())
        .limit(1)
        .options(selectinload(TestResult.evidence))
    )
    if result is None:
        return None

    run = db.get(TestRun, result.run_id)
    assert run is not None  # FK guarantees it

    return ControlResult(
        **_to_summary(result, {control.id: control}).model_dump(),
        run_id=run.id,
        seed=run.seed,
        completed_at=run.completed_at,
        detail=dict(result.detail or {}),
        evidence=[
            EvidenceOut(
                label=e.label,
                kind=e.kind,
                source_ref=e.source_ref,
                content_hash=e.content_hash,
                collected_at=e.collected_at,
                summary=(e.payload or {}).get("summary"),
            )
            for e in sorted(result.evidence, key=lambda e: e.label)
        ],
    )


@router.get("/suites")
def list_suites(db: Session = Depends(get_db)) -> dict[str, object]:
    """What the console may ask for.

    Derived from what is actually registered rather than a hand-maintained
    list, so it cannot drift from what will really run.
    """
    suites = db.scalars(
        select(Control)
        .join(Control.procedures)
        .order_by(Control.ref)
    ).all()

    suite_names = sorted(
        {p.suite for c in suites for p in c.procedures}
    )
    return {
        "suites": suite_names,
        "registered_procedures": runner.registered_keys(),
        "registered_evidence": registered_evidence(),
    }
