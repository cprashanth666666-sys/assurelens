"""The runner, end to end, and the constraints that back it.

Uses stub procedures rather than real suites: this is Day 4, the suites are
Days 5-7, and the point is that the engine works before anything depends on
it.
"""

from __future__ import annotations

import datetime as dt
from typing import Any

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError, ProgrammingError
from sqlalchemy.orm import Session

from app.engine import runner
from app.engine.evidence import (
    EvidenceBroker,
    EvidenceBundle,
    EvidenceContract,
    EvidenceItem,
    EvidenceKind,
    EvidenceRequirement,
    TargetUnreachable,
    content_hash,
)
from app.engine.gate import InferenceMode, RawResult, SampleFrame, Verdict
from app.models.control import Control, Engagement
from app.models.control import TestProcedure as ProcedureRow
from app.models.results import AuditEntry, EvidenceRecord
from app.models.results import TestResult as ResultRow
from app.models.results import TestRun as RunRow

pytestmark = pytest.mark.usefixtures("seeded_db")


# --- Stub procedures --------------------------------------------------------


class SoundProcedure:
    """Reports a well-evidenced pass."""

    evidence_contract = EvidenceContract(
        required=(
            EvidenceRequirement("records", EvidenceKind.DB_QUERY, defines_population=True),
        )
    )

    def execute(self, evidence: EvidenceBundle, config: dict[str, Any]) -> RawResult:
        rows = evidence.payload("records", [])
        return RawResult(
            outcome=Verdict.PASS,
            sample_size=len(rows),
            population_size=len(rows),
            successes=len(rows),
            sample_frame=SampleFrame.CENSUS,
            detail={"checked": len(rows)},
        )


class ThinlyEvidencedProcedure:
    """Measures a pass from far too little. The gate should override it."""

    evidence_contract = EvidenceContract(
        required=(
            EvidenceRequirement("records", EvidenceKind.DB_QUERY, defines_population=True),
        )
    )

    def execute(self, evidence: EvidenceBundle, config: dict[str, Any]) -> RawResult:
        return RawResult(
            outcome=Verdict.PASS,
            sample_size=12,
            population_size=24_000,
            successes=12,
            inference_mode=InferenceMode.POPULATION,
        )


class ProbeProcedure:
    evidence_contract = EvidenceContract(
        required=(EvidenceRequirement("exchanges", EvidenceKind.HTTP_PROBE),)
    )

    def execute(self, evidence: EvidenceBundle, config: dict[str, Any]) -> RawResult:
        return RawResult(
            outcome=Verdict.FAIL,
            inference_mode=InferenceMode.CENSUS,
            sample_size=8,
            population_size=8,
            successes=5,
            sample_frame=SampleFrame.CENSUS,
        )


@pytest.fixture
def broker() -> EvidenceBroker:
    b = EvidenceBroker()
    b.register(EvidenceKind.DB_QUERY, lambda name, ctx: [{"id": i} for i in range(60)])
    b.register(EvidenceKind.HTTP_PROBE, lambda name, ctx: [{"status": 200}] * 8)
    return b


@pytest.fixture
def engagement_id(seeded_db: Session) -> int:
    engagement = seeded_db.scalar(select(Engagement).order_by(Engagement.id).limit(1))
    assert engagement is not None
    return engagement.id


def _attach(db: Session, control_ref: str, plugin_key: str, suite: str) -> None:
    """Point a real control at a stub procedure for the duration of a test."""
    control = db.scalar(select(Control).where(Control.ref == control_ref))
    assert control is not None
    # Reuse the existing row rather than deleting it: test_results reference
    # procedures, so a raw delete recreates the foreign-key violation the
    # loader was just fixed to avoid.
    contract = {
        "required": [
            {"name": "records", "kind": "DB_QUERY", "defines_population": True}
        ]
    }

    existing = db.scalar(
        select(ProcedureRow).where(ProcedureRow.control_id == control.id)
    )
    if existing is not None:
        existing.plugin_key = plugin_key
        existing.suite = suite
        # The contract too: the stub reads an evidence name the real YAML
        # does not declare, and a stale contract would collect the wrong
        # names and leave the stub reading an empty bundle.
        existing.evidence_contract = contract
        db.flush()
        return

    db.add(
        ProcedureRow(
            control_id=control.id,
            plugin_key=plugin_key,
            suite=suite,
            config={},
            evidence_contract=contract,
        )
    )
    db.flush()


# --- End to end -------------------------------------------------------------


def test_a_run_persists_a_complete_statistics_row(
    seeded_db: Session, broker: EvidenceBroker, engagement_id: int
) -> None:
    """The Day 4 acceptance criterion: a run executes and records everything
    needed to reproduce its conclusion."""
    runner._REGISTRY.pop("stub.sound", None)
    runner.register("stub.sound")(SoundProcedure)
    _attach(seeded_db, "DPDP-06-01", "stub.sound", "stub_suite")

    run = runner.run_suites(
        seeded_db, engagement_id, ["stub_suite"], seed=42,
        broker=broker, engine_version="test",
    )
    seeded_db.flush()

    assert run.status == "COMPLETE"
    assert run.seed == 42

    result = seeded_db.scalar(
        select(ResultRow).where(
            ResultRow.run_id == run.id,
            ResultRow.detail["checked"].astext == "60",
        )
    )
    assert result is not None
    assert result.verdict == "PASS"
    assert result.sample_size == 60
    assert result.ci_method == "wilson_95"
    assert result.ci_lower is not None and result.ci_upper is not None
    assert result.thresholds_applied["min_sample_n"] == 30
    seeded_db.rollback()


def test_the_gate_overrides_a_thinly_evidenced_pass(
    seeded_db: Session, broker: EvidenceBroker, engagement_id: int
) -> None:
    """The procedure said PASS. Twelve of 24,000 cannot support that, and the
    stored row says both things: what was measured and why it was overridden."""
    runner._REGISTRY.pop("stub.thin", None)
    runner.register("stub.thin")(ThinlyEvidencedProcedure)
    _attach(seeded_db, "DPDP-06-01", "stub.thin", "stub_suite")

    run = runner.run_suites(
        seeded_db, engagement_id, ["stub_suite"], seed=42,
        broker=broker, engine_version="test",
    )
    seeded_db.flush()

    result = seeded_db.scalar(
        select(ResultRow).where(
            ResultRow.run_id == run.id, ResultRow.gate_fired.is_(True)
        )
    )
    assert result is not None
    assert result.verdict == "INSUFFICIENT_EVIDENCE"
    assert result.raw_outcome == "PASS", "what the procedure measured is preserved"
    assert "G3_COVERAGE" in result.gate_reasons
    assert result.gate_explanations and result.gate_remedies
    seeded_db.rollback()


def test_evidence_is_recorded_with_a_hash(
    seeded_db: Session, broker: EvidenceBroker, engagement_id: int
) -> None:
    """So the workpaper can assert the evidence has not changed since the
    conclusion was drawn from it."""
    runner._REGISTRY.pop("stub.sound2", None)
    runner.register("stub.sound2")(SoundProcedure)
    _attach(seeded_db, "DPDP-06-01", "stub.sound2", "stub_suite")

    run = runner.run_suites(
        seeded_db, engagement_id, ["stub_suite"], seed=42,
        broker=broker, engine_version="test",
    )
    seeded_db.flush()

    records = seeded_db.scalars(
        select(EvidenceRecord)
        .join(ResultRow)
        .where(ResultRow.run_id == run.id)
    ).all()

    assert records
    assert all(len(r.content_hash) == 64 for r in records)
    assert all(r.collected_at for r in records)
    seeded_db.rollback()


def test_a_scoped_out_control_is_recorded_not_skipped(
    seeded_db: Session, broker: EvidenceBroker, engagement_id: int
) -> None:
    """DPDP-08-04 does not bind a BFSI GCC. The run records NOT_APPLICABLE
    with the reason, rather than omitting it -- a control silently absent from
    a workpaper is the gap nobody notices."""
    run = runner.run_suites(
        seeded_db, engagement_id, ["stub_suite"], seed=42,
        broker=broker, engine_version="test",
    )
    seeded_db.flush()

    control = seeded_db.scalar(select(Control).where(Control.ref == "DPDP-08-04"))
    assert control is not None
    result = seeded_db.scalar(
        select(ResultRow).where(
            ResultRow.run_id == run.id, ResultRow.control_id == control.id
        )
    )

    assert result is not None
    assert result.verdict == "NOT_APPLICABLE"
    assert result.gate_fired is False
    assert "Third Schedule" in " ".join(result.gate_explanations)
    seeded_db.rollback()


def test_an_unreachable_target_never_produces_a_pass(
    seeded_db: Session, engagement_id: int
) -> None:
    """The most dangerous failure this product could have: a green report
    produced by testing nothing."""
    runner._REGISTRY.pop("stub.probe", None)
    runner.register("stub.probe")(ProbeProcedure)
    _attach(seeded_db, "DPDP-06-02", "stub.probe", "stub_suite")

    def refuse(name: str, ctx: dict[str, Any]) -> Any:
        raise TargetUnreachable(name)

    dead = EvidenceBroker()
    dead.register(EvidenceKind.DB_QUERY, refuse)
    dead.register(EvidenceKind.HTTP_PROBE, refuse)

    run = runner.run_suites(
        seeded_db, engagement_id, ["stub_suite"], seed=42,
        broker=dead, engine_version="test",
    )
    seeded_db.flush()

    results = seeded_db.scalars(
        select(ResultRow).where(
            ResultRow.run_id == run.id, ResultRow.gate_fired.is_(True)
        )
    ).all()

    assert results
    assert all(r.verdict == "INSUFFICIENT_EVIDENCE" for r in results)
    assert any("G8_TARGET_UNREACHABLE" in r.gate_reasons for r in results)
    seeded_db.rollback()


def test_a_run_writes_an_audit_entry(
    seeded_db: Session, broker: EvidenceBroker, engagement_id: int
) -> None:
    """The assurance tool has to be auditable itself."""
    before = seeded_db.scalar(
        select(AuditEntry).where(AuditEntry.action == "RUN_STARTED").limit(1)
    )
    run = runner.run_suites(
        seeded_db, engagement_id, ["stub_suite"], seed=7,
        broker=broker, engine_version="test",
    )
    seeded_db.flush()

    entry = seeded_db.scalar(
        select(AuditEntry).where(
            AuditEntry.action == "RUN_STARTED", AuditEntry.entity_id == str(run.id)
        )
    )
    assert entry is not None
    assert entry.detail["seed"] == 7
    del before
    seeded_db.rollback()


# --- The constraints that back the product's argument ----------------------


def test_the_database_refuses_an_unexplained_insufficient_verdict(
    seeded_db: Session, engagement_id: int
) -> None:
    """INSUFFICIENT_EVIDENCE without a gate reason is unrepresentable.

    Enforced in DDL rather than application code, so no code path -- including
    a future one nobody has written yet -- can record a non-answer that does
    not explain itself. It is impossible, at the database level, to shrug.
    """
    run = RunRow(
        engagement_id=engagement_id, seed=1, suites=["x"],
        status="COMPLETE", engine_version="test",
    )
    seeded_db.add(run)
    seeded_db.flush()

    control = seeded_db.scalar(select(Control).limit(1))
    assert control is not None

    seeded_db.add(
        ResultRow(
            run_id=run.id, control_id=control.id,
            verdict="INSUFFICIENT_EVIDENCE",
            gate_fired=False,  # the lie the constraint exists to refuse
            gate_reasons=[],
        )
    )

    with pytest.raises(IntegrityError):
        seeded_db.flush()
    seeded_db.rollback()


def test_the_database_refuses_a_fired_gate_with_no_reason(
    seeded_db: Session, engagement_id: int
) -> None:
    run = RunRow(
        engagement_id=engagement_id, seed=1, suites=["x"],
        status="COMPLETE", engine_version="test",
    )
    seeded_db.add(run)
    seeded_db.flush()
    control = seeded_db.scalar(select(Control).limit(1))
    assert control is not None

    seeded_db.add(
        ResultRow(
            run_id=run.id, control_id=control.id, verdict="FAIL",
            gate_fired=True, gate_reasons=[],
        )
    )

    with pytest.raises(IntegrityError):
        seeded_db.flush()
    seeded_db.rollback()


def test_the_audit_log_cannot_be_rewritten(seeded_db: Session) -> None:
    """Append-only, enforced by revoking UPDATE and DELETE. An audit trail
    that can be edited is not one."""
    seeded_db.add(
        AuditEntry(action="TEST", entity_type="test", entity_id="1", detail={})
    )
    seeded_db.flush()

    with pytest.raises((ProgrammingError, IntegrityError)):
        seeded_db.execute(text("DELETE FROM audit_log WHERE action = 'TEST'"))
        seeded_db.flush()
    seeded_db.rollback()


# --- Registry ---------------------------------------------------------------


def test_registering_the_same_key_twice_raises() -> None:
    """Two procedures under one key would make which ran depend on import
    order, and the workpaper would name the wrong one."""
    runner._REGISTRY.pop("stub.dup", None)
    runner.register("stub.dup")(SoundProcedure)

    with pytest.raises(ValueError, match="already registered"):
        runner.register("stub.dup")(SoundProcedure)

    runner._REGISTRY.pop("stub.dup", None)


def test_content_hash_is_stable_across_key_order() -> None:
    """Otherwise the workpaper's integrity claim breaks on dict ordering
    rather than on tampering."""
    assert content_hash({"a": 1, "b": 2}) == content_hash({"b": 2, "a": 1})


def test_content_hash_changes_when_evidence_changes() -> None:
    assert content_hash({"a": 1}) != content_hash({"a": 2})


def test_attestation_only_bundle_is_detected() -> None:
    """The failure mode of questionnaire-based tools, caught at the bundle."""
    now = dt.datetime.now(dt.UTC)
    bundle = EvidenceBundle(
        items={
            "policy": EvidenceItem(
                "policy", EvidenceKind.ATTESTATION, "interview", {"confirmed": True},
                now, content_hash({"confirmed": True}),
            )
        }
    )

    assert bundle.is_attestation_only is True


def test_a_mixed_bundle_is_not_attestation_only() -> None:
    now = dt.datetime.now(dt.UTC)
    bundle = EvidenceBundle(
        items={
            "policy": EvidenceItem(
                "policy", EvidenceKind.ATTESTATION, "interview", {}, now, "h1"
            ),
            "logs": EvidenceItem(
                "logs", EvidenceKind.DB_QUERY, "est_access_logs", [], now, "h2"
            ),
        }
    )

    assert bundle.is_attestation_only is False
