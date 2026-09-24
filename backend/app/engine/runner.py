"""Test run orchestration.

Resolves each in-scope control to a registered procedure, collects the
evidence that procedure declared it needs, runs it, puts the result through
the gate, and persists everything.

The plugin registry is what keeps suites out of the engine: adding a suite
means registering a procedure, never editing this file.
"""

from __future__ import annotations

import datetime as dt
import json
import logging
import time
from collections.abc import Callable
from typing import Any, Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.engine import findings
from app.engine import gate as gate_module
from app.engine.evidence import (
    EvidenceBroker,
    EvidenceBundle,
    EvidenceContract,
    EvidenceKind,
    EvidenceRequirement,
)
from app.engine.gate import RawResult, Verdict
from app.engine.thresholds import DEFAULT_THRESHOLDS, Thresholds
from app.models.control import Control, EngagementControl, TestProcedure
from app.models.estate import ModelAssessment
from app.models.results import AuditEntry, EvidenceRecord, TestResult, TestRun

log = logging.getLogger(__name__)


class Procedure(Protocol):
    """What a suite implements.

    `execute` reports what it measured. It does not decide whether that is
    enough -- that is the gate's job, and keeping the two apart is what stops
    a suite author widening a bound to make a control pass.
    """

    evidence_contract: EvidenceContract

    def execute(self, evidence: EvidenceBundle, config: dict[str, Any]) -> RawResult: ...


_REGISTRY: dict[str, Procedure] = {}


def register(plugin_key: str) -> Callable[[type], type]:
    """Register a procedure under the key its control declares in YAML."""

    def decorator(cls: type) -> type:
        if plugin_key in _REGISTRY:
            raise ValueError(f"plugin key {plugin_key!r} is already registered")
        _REGISTRY[plugin_key] = cls()
        return cls

    return decorator


def registered_keys() -> list[str]:
    return sorted(_REGISTRY)


def get_procedure(plugin_key: str) -> Procedure | None:
    return _REGISTRY.get(plugin_key)


def _contract_from_spec(spec: dict[str, Any]) -> EvidenceContract:
    """Build a contract from the YAML the control declares."""
    required = tuple(
        EvidenceRequirement(
            name=item["name"],
            kind=EvidenceKind(item["kind"]),
            defines_population=bool(item.get("defines_population")),
        )
        for item in spec.get("required", [])
    )
    return EvidenceContract(required=required, max_age_days=spec.get("max_age_days"))


def _persist(
    db: Session,
    run: TestRun,
    control: Control,
    procedure_row: TestProcedure | None,
    outcome: gate_module.GateOutcome,
    bundle: EvidenceBundle,
    duration_ms: int,
    detail: dict[str, Any],
) -> TestResult:
    result = TestResult(
        run_id=run.id,
        control_id=control.id,
        procedure_id=procedure_row.id if procedure_row else None,
        verdict=outcome.verdict.value,
        raw_outcome=outcome.raw_outcome.value,
        gate_fired=outcome.gate_fired,
        gate_reasons=[r.value for r in outcome.reasons],
        gate_explanations=list(outcome.explanations),
        gate_remedies=list(outcome.remedies),
        sample_size=outcome.sample_size,
        population_size=outcome.population_size,
        successes=outcome.successes,
        coverage_pct=outcome.coverage_pct,
        point_estimate=outcome.point_estimate,
        ci_lower=outcome.ci_lower,
        ci_upper=outcome.ci_upper,
        ci_method=outcome.ci_method,
        thresholds_applied=outcome.thresholds_applied,
        threshold_overrides=outcome.threshold_overrides,
        detail=detail,
        duration_ms=duration_ms,
    )
    db.add(result)
    db.flush()

    for item in bundle.items.values():
        db.add(
            EvidenceRecord(
                result_id=result.id,
                kind=item.kind.value,
                label=item.name,
                source_ref=item.source_ref,
                # Only a summary is persisted: a full estate query would bloat
                # every row, and the hash already pins what was collected.
                payload={"summary": _summarise(item.payload)},
                content_hash=item.content_hash,
                collected_at=item.collected_at,
                age_days=item.age_days,
            )
        )

    # An override is recorded here as well as on the result, because the audit
    # log is append-only and the result row is not the place to look for
    # "who loosened what, when".
    if outcome.threshold_overrides:
        db.add(
            AuditEntry(
                action="THRESHOLD_OVERRIDDEN",
                entity_type="control",
                entity_id=control.ref,
                detail={"run_id": run.id, "overrides": outcome.threshold_overrides},
            )
        )

    db.flush()
    return result


def _summarise(payload: Any) -> Any:
    """A JSON-safe précis of what was collected.

    Round-tripped through json with `default=str` because evidence rows carry
    datetimes and Decimals, which JSONB will not take. The full payload is not
    stored -- an estate query would bloat every result row, and the content
    hash already pins exactly what was collected.
    """
    if isinstance(payload, list):
        summary: Any = {"kind": "list", "length": len(payload), "first": payload[:2]}
    elif isinstance(payload, dict):
        summary = {"kind": "mapping", "keys": sorted(payload)[:12]}
    else:
        summary = payload

    return json.loads(json.dumps(summary, default=str))


def run_suites(
    db: Session,
    engagement_id: int,
    suites: list[str],
    seed: int,
    broker: EvidenceBroker,
    engine_version: str,
    thresholds: Thresholds = DEFAULT_THRESHOLDS,
) -> TestRun:
    """Execute every in-scope control belonging to the named suites."""
    run = TestRun(
        engagement_id=engagement_id,
        seed=seed,
        suites=suites,
        status="RUNNING",
        engine_version=engine_version,
    )
    db.add(run)
    db.flush()

    db.add(
        AuditEntry(
            action="RUN_STARTED",
            entity_type="test_run",
            entity_id=str(run.id),
            detail={"suites": suites, "seed": seed},
        )
    )

    scoped = {
        row.control_id: row
        for row in db.scalars(
            select(EngagementControl).where(
                EngagementControl.engagement_id == engagement_id
            )
        ).all()
    }

    controls = db.scalars(
        select(Control)
        .options(selectinload(Control.procedures), selectinload(Control.mappings))
        .order_by(Control.ref)
    ).all()

    for control in controls:
        scope = scoped.get(control.id)

        # A control scoped out on legal applicability is not an evidence
        # question. Running it would produce a verdict about a rule that does
        # not bind, which is worse than no verdict.
        if scope is not None and not scope.in_scope:
            _record_not_applicable(db, run, control, scope.na_reason)
            continue

        procedure_row = control.procedures[0] if control.procedures else None
        if procedure_row is None or procedure_row.suite not in suites:
            continue

        _run_one(db, run, control, procedure_row, broker, thresholds, seed)

    run.status = "COMPLETE"
    run.completed_at = dt.datetime.now(dt.UTC)
    db.flush()
    return run


def _record_not_applicable(
    db: Session, run: TestRun, control: Control, reason: str | None
) -> None:
    db.add(
        TestResult(
            run_id=run.id,
            control_id=control.id,
            verdict=Verdict.NOT_APPLICABLE.value,
            raw_outcome=Verdict.NOT_APPLICABLE.value,
            gate_fired=False,
            gate_reasons=[],
            gate_explanations=[reason] if reason else [],
            gate_remedies=[],
            detail={"scoped_out": True},
        )
    )
    db.flush()


def _run_one(
    db: Session,
    run: TestRun,
    control: Control,
    procedure_row: TestProcedure,
    broker: EvidenceBroker,
    thresholds: Thresholds,
    seed: int,
) -> None:
    procedure = get_procedure(procedure_row.plugin_key)

    if procedure is None:
        # Declared executable, nothing registered to execute it. Reported as
        # missing evidence rather than skipped, because a control silently
        # absent from the workpaper is the gap nobody notices.
        outcome = gate_module.apply(
            RawResult(
                outcome=Verdict.PASS,
                missing_required_evidence=(f"procedure {procedure_row.plugin_key}",),
            ),
            thresholds,
            control.threshold_overrides,
        )
        _persist(
            db, run, control, procedure_row, outcome, EvidenceBundle(), 0,
            {"unregistered_plugin": procedure_row.plugin_key},
        )
        return

    contract = _contract_from_spec(procedure_row.evidence_contract or {})
    context = {"db": db, "seed": seed, "control_ref": control.ref,
               "config": procedure_row.config or {}}

    started = time.perf_counter()
    bundle = broker.collect(contract, context)

    primary_source = next(
        (r.name for r in contract.required if r.defines_population), None
    )

    if bundle.missing or bundle.unreachable:
        raw = RawResult(
            outcome=Verdict.PASS,
            missing_required_evidence=bundle.missing,
            target_unreachable=bundle.unreachable,
        )
    else:
        raw = procedure.execute(bundle, procedure_row.config or {})
        if bundle.is_attestation_only:
            raw = RawResult(**{**raw.__dict__, "attestation_only": True})
        age = bundle.newest_age_days
        if age is not None and raw.evidence_age_days is None:
            raw = RawResult(**{**raw.__dict__, "evidence_age_days": age})

    primary = control.primary_mapping
    if primary is not None and primary.clause.source_status == "UNVERIFIED":
        raw = RawResult(**{**raw.__dict__, "source_status": "UNVERIFIED"})

    outcome = gate_module.apply(raw, thresholds, control.threshold_overrides)
    duration_ms = int((time.perf_counter() - started) * 1000)

    result = _persist(
        db, run, control, procedure_row, outcome, bundle, duration_ms,
        {**raw.detail, "population_source": primary_source},
    )
    _persist_model_assessments(db, result, raw.detail)

    # Only a clean FAIL raises a finding -- never a gated result. The gate's
    # own explanation already says what is missing; a "finding" built from a
    # verdict the product itself calls inconclusive would undercut the whole
    # argument for the gate existing. [Day 8, TRD 1.3]
    if outcome.verdict == Verdict.FAIL and control.auto_raise:
        findings.raise_from_result(db, control, result)


def _persist_model_assessments(
    db: Session, result: TestResult, detail: dict[str, Any]
) -> None:
    """One `est_model_assessments` row per metric, feature and group.

    Model procedures report these in their detail; the runner writes them,
    because procedures never touch the database. Keeping them as rows as well
    as in the result's JSON means a metric can be queried across runs, and
    `group_n` travels with every group figure so a small group can never be
    read back as a disparity without its size beside it. [SCHEMA est_model_assessments]
    """
    rows = detail.get("model_assessments") or []
    model_id = detail.get("model_id")
    if not rows or model_id is None:
        return
    for row in rows:
        db.add(
            ModelAssessment(
                model_id=model_id,
                result_id=result.id,
                metric=row["metric"],
                feature=row.get("feature"),
                group_label=row.get("group_label"),
                value=row.get("value"),
                group_n=row.get("group_n"),
            )
        )
    db.flush()
