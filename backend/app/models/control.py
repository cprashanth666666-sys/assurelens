"""ORM models for the control library and engagement scoping.

Mirrors migration 0001. See docs/SCHEMA.md sections 3.2 and 3.3.
"""

from __future__ import annotations

import datetime as dt
from typing import Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    SmallInteger,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import ENUM, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

# create_type=False: the enum types are created once by migration 0001.
_source_status = ENUM(
    "VERIFIED", "UNVERIFIED", name="source_status_t", create_type=False
)
_control_domain = ENUM(
    "NOTICE_CONSENT", "SECURITY_SAFEGUARDS", "RETENTION_ERASURE",
    "PRINCIPAL_RIGHTS", "THIRD_PARTY_TRANSFER", "AI_GOVERNANCE",
    "BREACH_RESPONSE", "GOVERNANCE_ACCOUNTABILITY",
    name="control_domain_t", create_type=False,
)
_inference_mode = ENUM(
    "POPULATION", "CENSUS", name="inference_mode_t", create_type=False
)
_role = ENUM("CONSULTANT", "CLIENT", "REVIEWER", name="role_t", create_type=False)


class Framework(Base):
    __tablename__ = "frameworks"

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    code: Mapped[str] = mapped_column(Text, unique=True)
    name: Mapped[str] = mapped_column(Text)
    version: Mapped[str] = mapped_column(Text)
    authority: Mapped[str | None] = mapped_column(Text)
    source_url: Mapped[str | None] = mapped_column(Text)

    clauses: Mapped[list[FrameworkClause]] = relationship(
        back_populates="framework", cascade="all, delete-orphan"
    )


class FrameworkClause(Base):
    __tablename__ = "framework_clauses"
    __table_args__ = (UniqueConstraint("framework_id", "ref"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    framework_id: Mapped[int] = mapped_column(
        ForeignKey("frameworks.id", ondelete="CASCADE")
    )
    ref: Mapped[str] = mapped_column(Text)
    title: Mapped[str] = mapped_column(Text)
    # Verbatim statutory text. The UI renders it so the reader sees the
    # statute rather than a paraphrase. [UX 4.3]
    verbatim_text: Mapped[str | None] = mapped_column(Text)
    in_force_from: Mapped[dt.date | None] = mapped_column(Date)
    source_status: Mapped[str] = mapped_column(_source_status, default="VERIFIED")
    source_note: Mapped[str | None] = mapped_column(Text)

    framework: Mapped[Framework] = relationship(back_populates="clauses")
    mappings: Mapped[list[ControlClauseMapping]] = relationship(
        back_populates="clause", cascade="all, delete-orphan"
    )


class Control(Base):
    __tablename__ = "controls"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ref: Mapped[str] = mapped_column(Text, unique=True)
    title: Mapped[str] = mapped_column(Text)
    objective: Mapped[str] = mapped_column(Text)
    domain: Mapped[str] = mapped_column(_control_domain)
    procedure_text: Mapped[str] = mapped_column(Text)
    inference_mode: Mapped[str] = mapped_column(_inference_mode, default="POPULATION")
    is_executable: Mapped[bool] = mapped_column(Boolean, default=False)
    auto_raise: Mapped[bool] = mapped_column(Boolean, default=True)
    threshold_overrides: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    yaml_source: Mapped[str] = mapped_column(Text)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    mappings: Mapped[list[ControlClauseMapping]] = relationship(
        back_populates="control",
        cascade="all, delete-orphan",
        order_by="ControlClauseMapping.is_primary.desc()",
    )
    procedures: Mapped[list[TestProcedure]] = relationship(
        back_populates="control", cascade="all, delete-orphan"
    )

    @property
    def primary_mapping(self) -> ControlClauseMapping | None:
        """The control's legal basis.

        G7_SOURCE_UNVERIFIED considers only this clause. Secondary
        cross-references (ISO, NIST) are for navigation and never carry a
        verdict, so an unverified ISO title must not gate a control whose
        DPDP basis was read from the gazette.
        """
        return next((m for m in self.mappings if m.is_primary), None)


class ControlClauseMapping(Base):
    __tablename__ = "control_clause_mappings"

    control_id: Mapped[int] = mapped_column(
        ForeignKey("controls.id", ondelete="CASCADE"), primary_key=True
    )
    clause_id: Mapped[int] = mapped_column(
        ForeignKey("framework_clauses.id", ondelete="CASCADE"), primary_key=True
    )
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    rationale: Mapped[str | None] = mapped_column(Text)

    control: Mapped[Control] = relationship(back_populates="mappings")
    clause: Mapped[FrameworkClause] = relationship(back_populates="mappings")


class TestProcedure(Base):
    __tablename__ = "test_procedures"
    __table_args__ = (UniqueConstraint("control_id", "plugin_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    control_id: Mapped[int] = mapped_column(
        ForeignKey("controls.id", ondelete="CASCADE")
    )
    plugin_key: Mapped[str] = mapped_column(Text)
    suite: Mapped[str] = mapped_column(Text)
    config: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    evidence_contract: Mapped[dict[str, Any]] = mapped_column(JSONB)

    control: Mapped[Control] = relationship(back_populates="procedures")


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(Text)
    sector: Mapped[str | None] = mapped_column(Text)
    city: Mapped[str | None] = mapped_column(Text)
    headcount: Mapped[int | None] = mapped_column(Integer)
    is_significant_data_fiduciary: Mapped[bool] = mapped_column(Boolean, default=False)
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=True)
    notes: Mapped[str | None] = mapped_column(Text)

    engagements: Mapped[list[Engagement]] = relationship(
        back_populates="organization", cascade="all, delete-orphan"
    )


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str | None] = mapped_column(Text, unique=True)
    name: Mapped[str] = mapped_column(Text)
    role: Mapped[str] = mapped_column(_role)
    org_id: Mapped[int | None] = mapped_column(ForeignKey("organizations.id"))
    is_demo_actor: Mapped[bool] = mapped_column(Boolean, default=False)


class Engagement(Base):
    __tablename__ = "engagements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    org_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE")
    )
    name: Mapped[str] = mapped_column(Text)
    scope_note: Mapped[str | None] = mapped_column(Text)
    period_start: Mapped[dt.date | None] = mapped_column(Date)
    period_end: Mapped[dt.date | None] = mapped_column(Date)
    compliance_deadline: Mapped[dt.date | None] = mapped_column(Date)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    organization: Mapped[Organization] = relationship(back_populates="engagements")
    scoped_controls: Mapped[list[EngagementControl]] = relationship(
        back_populates="engagement", cascade="all, delete-orphan"
    )


class EngagementControl(Base):
    __tablename__ = "engagement_controls"
    __table_args__ = (
        CheckConstraint("in_scope OR na_reason IS NOT NULL", name="ck_na_reason"),
    )

    engagement_id: Mapped[int] = mapped_column(
        ForeignKey("engagements.id", ondelete="CASCADE"), primary_key=True
    )
    control_id: Mapped[int] = mapped_column(
        ForeignKey("controls.id", ondelete="CASCADE"), primary_key=True
    )
    in_scope: Mapped[bool] = mapped_column(Boolean, default=True)
    # Required when in_scope is false, by database constraint. Unexplained
    # exclusions are how assurance scope quietly shrinks to what passes.
    na_reason: Mapped[str | None] = mapped_column(Text)
    evidence_owner: Mapped[str | None] = mapped_column(Text)

    engagement: Mapped[Engagement] = relationship(back_populates="scoped_controls")
    control: Mapped[Control] = relationship()
