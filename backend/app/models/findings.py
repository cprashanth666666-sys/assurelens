"""ORM models for findings, history and remediation.

Mirrors migration 0005. See docs/SCHEMA.md section 3.5.
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    Computed,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    SmallInteger,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

_severity = ENUM("CRITICAL", "HIGH", "MEDIUM", "LOW", name="severity_t", create_type=False)
_finding_status = ENUM(
    "OPEN", "IN_REMEDIATION", "RETEST_PENDING", "CLOSED", "ACCEPTED_RISK",
    name="finding_status_t", create_type=False,
)


class Finding(Base):
    __tablename__ = "findings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ref: Mapped[str] = mapped_column(Text, unique=True)
    engagement_id: Mapped[int] = mapped_column(
        ForeignKey("engagements.id", ondelete="CASCADE")
    )
    control_id: Mapped[int] = mapped_column(ForeignKey("controls.id"))
    origin_result_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("test_results.id")
    )

    title: Mapped[str] = mapped_column(Text)
    description: Mapped[str] = mapped_column(Text)
    root_cause: Mapped[str | None] = mapped_column(Text)
    recommendation: Mapped[str | None] = mapped_column(Text)

    likelihood: Mapped[int] = mapped_column(SmallInteger)
    impact: Mapped[int] = mapped_column(SmallInteger)
    # Database-generated (STORED): the multiplication happens in exactly one
    # place, so the number on screen and the number banded to a severity can
    # never drift apart.
    risk_score: Mapped[int] = mapped_column(
        SmallInteger, Computed("likelihood * impact", persisted=True)
    )
    severity: Mapped[str] = mapped_column(_severity)

    owner: Mapped[str | None] = mapped_column(Text)
    effort_days: Mapped[Decimal | None] = mapped_column(Numeric(5, 1))
    status: Mapped[str] = mapped_column(_finding_status, default="OPEN")
    is_internal_note_only: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    control: Mapped[Any] = relationship("Control")
    history: Mapped[list[FindingHistory]] = relationship(
        back_populates="finding", cascade="all, delete-orphan",
        order_by="FindingHistory.changed_at",
    )
    remediation_items: Mapped[list[RemediationItem]] = relationship(
        back_populates="finding", cascade="all, delete-orphan",
        order_by="RemediationItem.sequence",
    )


class FindingHistory(Base):
    __tablename__ = "finding_history"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    finding_id: Mapped[int] = mapped_column(
        ForeignKey("findings.id", ondelete="CASCADE")
    )
    changed_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    actor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    field: Mapped[str] = mapped_column(Text)
    old_value: Mapped[str | None] = mapped_column(Text)
    new_value: Mapped[str | None] = mapped_column(Text)

    finding: Mapped[Finding] = relationship(back_populates="history")


class RemediationItem(Base):
    __tablename__ = "remediation_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    finding_id: Mapped[int] = mapped_column(
        ForeignKey("findings.id", ondelete="CASCADE")
    )
    sequence: Mapped[int] = mapped_column(SmallInteger)
    action: Mapped[str] = mapped_column(Text)
    owner: Mapped[str | None] = mapped_column(Text)
    effort_days: Mapped[Decimal | None] = mapped_column(Numeric(5, 1))
    target_date: Mapped[dt.date | None] = mapped_column(Date)
    expected_residual_risk: Mapped[int | None] = mapped_column(SmallInteger)

    finding: Mapped[Finding] = relationship(back_populates="remediation_items")
