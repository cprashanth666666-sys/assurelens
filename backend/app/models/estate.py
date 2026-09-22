"""ORM models for the synthetic estate.

Every table is prefixed `est_` so it can never be mistaken for assessment
data. Mirrors migration 0002. [SCHEMA D6]
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class DataAsset(Base):
    __tablename__ = "est_data_assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    org_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE")
    )
    name: Mapped[str] = mapped_column(Text)
    system: Mapped[str | None] = mapped_column(Text)
    classification: Mapped[str | None] = mapped_column(Text)
    # What the inventory claims. Suite 1 compares it against what detectors
    # actually find; the gap is the finding.
    declared_identifier_classes: Mapped[list[str]] = mapped_column(
        ARRAY(Text), default=list
    )
    encryption_at_rest: Mapped[bool] = mapped_column(Boolean, default=False)
    record_count: Mapped[int | None] = mapped_column(BigInteger)
    hosted_region: Mapped[str | None] = mapped_column(Text)


class AssetRecord(Base):
    """What an asset actually contains.

    The gap between this and `DataAsset.declared_identifier_classes` is the
    finding: an inventory describes what an organisation believes it holds,
    and a scan establishes what it does.
    """

    __tablename__ = "est_asset_records"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    asset_id: Mapped[int] = mapped_column(
        ForeignKey("est_data_assets.id", ondelete="CASCADE")
    )
    principal_id: Mapped[int | None] = mapped_column(
        ForeignKey("est_data_principals.id", ondelete="CASCADE")
    )
    content: Mapped[dict[str, Any]] = mapped_column(JSONB)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class ProcessingActivity(Base):
    __tablename__ = "est_processing_activities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    org_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE")
    )
    purpose: Mapped[str] = mapped_column(Text)
    lawful_basis: Mapped[str] = mapped_column(Text)
    asset_id: Mapped[int | None] = mapped_column(ForeignKey("est_data_assets.id"))
    retention_days: Mapped[int | None] = mapped_column(Integer)
    # Rule 8(3) sets a one-year floor.
    log_retention_days: Mapped[int | None] = mapped_column(Integer)


class DataPrincipal(Base):
    __tablename__ = "est_data_principals"
    __table_args__ = (UniqueConstraint("org_id", "external_ref"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    org_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE")
    )
    external_ref: Mapped[str] = mapped_column(Text)
    last_contact_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    erased_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    # The s.8(7)(a) carve-out. A record held WITHOUT a recorded basis is the
    # finding; one held with a basis is compliant however old it is.
    legal_hold: Mapped[bool] = mapped_column(Boolean, default=False)
    legal_hold_basis: Mapped[str | None] = mapped_column(Text)
    pre_erasure_notice_at: Mapped[dt.datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    group_attribute: Mapped[str | None] = mapped_column(Text)
    is_minor: Mapped[bool] = mapped_column(Boolean, default=False)

    consents: Mapped[list[ConsentRecord]] = relationship(
        back_populates="principal", cascade="all, delete-orphan"
    )


class ConsentRecord(Base):
    __tablename__ = "est_consent_records"
    __table_args__ = (UniqueConstraint("principal_id", "purpose"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    principal_id: Mapped[int] = mapped_column(
        ForeignKey("est_data_principals.id", ondelete="CASCADE")
    )
    purpose: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text)
    granted_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True))
    withdrawn_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    # Defect S1: the store updates instantly, the downstream on a batch.
    downstream_synced_at: Mapped[dt.datetime | None] = mapped_column(
        DateTime(timezone=True)
    )

    principal: Mapped[DataPrincipal] = relationship(back_populates="consents")
    events: Mapped[list[ConsentEvent]] = relationship(
        back_populates="consent", cascade="all, delete-orphan"
    )


class ConsentEvent(Base):
    __tablename__ = "est_consent_events"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    consent_id: Mapped[int] = mapped_column(
        ForeignKey("est_consent_records.id", ondelete="CASCADE")
    )
    event: Mapped[str] = mapped_column(Text)
    occurred_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True))
    latency_ms: Mapped[int | None] = mapped_column(BigInteger)

    consent: Mapped[ConsentRecord] = relationship(back_populates="events")


class ThirdParty(Base):
    __tablename__ = "est_third_parties"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    org_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE")
    )
    name: Mapped[str] = mapped_column(Text)
    category: Mapped[str | None] = mapped_column(Text)
    # NULL means no processor agreement, which Act s.8(2) requires before
    # engaging a processor at all.
    dpa_reference: Mapped[str | None] = mapped_column(Text)
    granted_scopes: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    exercised_scopes: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    credential_issued_at: Mapped[dt.datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    last_used_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    relationship_ended_at: Mapped[dt.datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    country: Mapped[str | None] = mapped_column(Text)
    credential_token: Mapped[str | None] = mapped_column(Text)


class AccessLog(Base):
    __tablename__ = "est_access_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    org_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE")
    )
    actor_ref: Mapped[str] = mapped_column(Text)
    asset_id: Mapped[int | None] = mapped_column(ForeignKey("est_data_assets.id"))
    action: Mapped[str] = mapped_column(Text)
    occurred_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True))
    was_authorised: Mapped[bool | None] = mapped_column(Boolean)


class ModelRegistry(Base):
    __tablename__ = "est_model_registry"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    org_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE")
    )
    name: Mapped[str] = mapped_column(Text)
    purpose: Mapped[str] = mapped_column(Text)
    deployed_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    # Without a baseline, drift is not computable at all.
    training_snapshot: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    has_drift_monitoring: Mapped[bool] = mapped_column(Boolean, default=False)
    # Rule 13(3) bites on software affecting the rights of Data Principals.
    is_consequential: Mapped[bool] = mapped_column(Boolean, default=True)

    predictions: Mapped[list[ModelPrediction]] = relationship(
        back_populates="model", cascade="all, delete-orphan"
    )


class ModelPrediction(Base):
    __tablename__ = "est_model_predictions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    model_id: Mapped[int] = mapped_column(
        ForeignKey("est_model_registry.id", ondelete="CASCADE")
    )
    principal_id: Mapped[int | None] = mapped_column(
        ForeignKey("est_data_principals.id")
    )
    features: Mapped[dict[str, Any]] = mapped_column(JSONB)
    score: Mapped[Decimal | None] = mapped_column(Numeric(8, 6))
    decision: Mapped[str | None] = mapped_column(Text)
    # Known for only a subset, which is what makes equal opportunity
    # computable on part of the population and not the whole.
    ground_truth: Mapped[str | None] = mapped_column(Text)
    predicted_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True))

    model: Mapped[ModelRegistry] = relationship(back_populates="predictions")


class ModelAssessment(Base):
    __tablename__ = "est_model_assessments"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    model_id: Mapped[int] = mapped_column(
        ForeignKey("est_model_registry.id", ondelete="CASCADE")
    )
    # Foreign key added when test_results exists.
    result_id: Mapped[int | None] = mapped_column(BigInteger)
    metric: Mapped[str] = mapped_column(Text)
    feature: Mapped[str | None] = mapped_column(Text)
    group_label: Mapped[str | None] = mapped_column(Text)
    value: Mapped[Decimal | None] = mapped_column(Numeric(12, 6))
    # Carried so a small group reports as insufficient evidence rather than
    # as a disparity.
    group_n: Mapped[int | None] = mapped_column(Integer)
    assessed_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
