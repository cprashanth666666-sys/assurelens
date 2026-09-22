"""ORM models for runs, results, evidence and the audit log.

Mirrors migration 0003. See docs/SCHEMA.md section 3.4.
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, ENUM, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

_verdict = ENUM(
    "PASS", "FAIL", "INSUFFICIENT_EVIDENCE", "NOT_APPLICABLE",
    name="verdict_t", create_type=False,
)
_gate_reason = ENUM(
    "G1_MIN_SAMPLE", "G2_CI_WIDTH", "G3_COVERAGE", "G4_MISSING_ARTIFACT",
    "G5_STALE_EVIDENCE", "G6_NON_REPRESENTATIVE", "G7_SOURCE_UNVERIFIED",
    "G8_TARGET_UNREACHABLE",
    name="gate_reason_t", create_type=False,
)
_evidence_kind = ENUM(
    "DB_QUERY", "HTTP_PROBE", "FILE_ARTIFACT", "ATTESTATION",
    name="evidence_kind_t", create_type=False,
)
_run_status = ENUM(
    "QUEUED", "RUNNING", "COMPLETE", "FAILED", name="run_status_t", create_type=False
)
_role = ENUM("CONSULTANT", "CLIENT", "REVIEWER", name="role_t", create_type=False)


class TestRun(Base):
    __tablename__ = "test_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    engagement_id: Mapped[int] = mapped_column(
        ForeignKey("engagements.id", ondelete="CASCADE")
    )
    # A result nobody can regenerate is an assertion, not a finding.
    seed: Mapped[int] = mapped_column(BigInteger)
    suites: Mapped[list[str]] = mapped_column(ARRAY(Text))
    status: Mapped[str] = mapped_column(_run_status, default="QUEUED")
    started_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    completed_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    engine_version: Mapped[str] = mapped_column(Text)
    error: Mapped[str | None] = mapped_column(Text)

    results: Mapped[list[TestResult]] = relationship(
        back_populates="run", cascade="all, delete-orphan"
    )


class TestResult(Base):
    """Append-only. A re-test writes a new row; history is the audit trail."""

    __tablename__ = "test_results"
    __table_args__ = (
        CheckConstraint(
            "NOT gate_fired OR cardinality(gate_reasons) > 0",
            name="ck_gate_reasons_present",
        ),
        CheckConstraint(
            "verdict <> 'INSUFFICIENT_EVIDENCE' OR gate_fired",
            name="ck_insufficient_implies_gate",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("test_runs.id", ondelete="CASCADE"))
    control_id: Mapped[int] = mapped_column(ForeignKey("controls.id"))
    procedure_id: Mapped[int | None] = mapped_column(ForeignKey("test_procedures.id"))

    verdict: Mapped[str] = mapped_column(_verdict)
    # Pre-gate outcome, so an override reads as "would have passed, but..."
    raw_outcome: Mapped[str | None] = mapped_column(_verdict)
    gate_fired: Mapped[bool] = mapped_column(Boolean, default=False)
    gate_reasons: Mapped[list[str]] = mapped_column(ARRAY(_gate_reason), default=list)
    gate_explanations: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    gate_remedies: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)

    sample_size: Mapped[int | None] = mapped_column(Integer)
    population_size: Mapped[int | None] = mapped_column(BigInteger)
    successes: Mapped[int | None] = mapped_column(Integer)
    coverage_pct: Mapped[Decimal | None] = mapped_column(Numeric(6, 3))
    point_estimate: Mapped[Decimal | None] = mapped_column(Numeric(6, 5))
    ci_lower: Mapped[Decimal | None] = mapped_column(Numeric(6, 5))
    ci_upper: Mapped[Decimal | None] = mapped_column(Numeric(6, 5))
    ci_method: Mapped[str | None] = mapped_column(Text)

    thresholds_applied: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    threshold_overrides: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    detail: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    run_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    run: Mapped[TestRun] = relationship(back_populates="results")
    evidence: Mapped[list[EvidenceRecord]] = relationship(
        back_populates="result", cascade="all, delete-orphan"
    )


class EvidenceRecord(Base):
    __tablename__ = "evidence_items"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    result_id: Mapped[int] = mapped_column(
        ForeignKey("test_results.id", ondelete="CASCADE")
    )
    kind: Mapped[str] = mapped_column(_evidence_kind)
    label: Mapped[str] = mapped_column(Text)
    source_ref: Mapped[str | None] = mapped_column(Text)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    content_hash: Mapped[str] = mapped_column(Text)
    collected_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True))
    age_days: Mapped[int | None] = mapped_column(Integer)
    is_sufficient: Mapped[bool] = mapped_column(Boolean, default=True)
    insufficiency_note: Mapped[str | None] = mapped_column(Text)

    result: Mapped[TestResult] = relationship(back_populates="evidence")


class AuditEntry(Base):
    """Append-only: UPDATE and DELETE are revoked at the database level."""

    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    occurred_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    actor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    actor_role: Mapped[str | None] = mapped_column(_role)
    action: Mapped[str] = mapped_column(Text)
    entity_type: Mapped[str] = mapped_column(Text)
    entity_id: Mapped[str | None] = mapped_column(Text)
    detail: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
