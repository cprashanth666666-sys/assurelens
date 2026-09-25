"""ORM models for intake documents.

Mirrors migration 0006. See docs/SCHEMA.md conventions D4 (evidence is hashed
and timestamped) and D8 (append-only history) — a document's raw bytes never
live in this table; `storage_key` points at the object store, and a
re-classification writes a new `DocumentClassification` row rather than
overwriting the previous one.
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

_document_source = ENUM("UPLOAD", "URL", name="document_source_t", create_type=False)
_document_status = ENUM(
    "RECEIVED", "PROCESSING", "EXTRACTED", "CLASSIFIED", "REJECTED", "FAILED",
    name="document_status_t", create_type=False,
)


class Document(Base):
    __tablename__ = "documents"
    __table_args__ = (
        UniqueConstraint("engagement_id", "content_hash", name="uq_documents_engagement_hash"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    engagement_id: Mapped[int] = mapped_column(
        ForeignKey("engagements.id", ondelete="CASCADE")
    )
    source_type: Mapped[str] = mapped_column(_document_source)
    original_name: Mapped[str] = mapped_column(Text)
    declared_mime: Mapped[str | None] = mapped_column(Text)
    detected_mime: Mapped[str | None] = mapped_column(Text)
    size_bytes: Mapped[int] = mapped_column(BigInteger)
    content_hash: Mapped[str] = mapped_column(Text)
    storage_backend: Mapped[str] = mapped_column(Text)
    storage_key: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(_document_status, default="RECEIVED")
    rejection_reason: Mapped[str | None] = mapped_column(Text)
    uploaded_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    processed_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))

    extraction: Mapped[DocumentExtraction | None] = relationship(
        back_populates="document", cascade="all, delete-orphan", uselist=False
    )
    classifications: Mapped[list[DocumentClassification]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="DocumentClassification.id.desc()",
    )

    @property
    def latest_classification(self) -> DocumentClassification | None:
        return self.classifications[0] if self.classifications else None


class DocumentExtraction(Base):
    """One row per document. A re-extraction replaces it — the text is a
    derived artifact of the stored bytes, not itself evidence of anything."""

    __tablename__ = "document_extractions"

    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), primary_key=True
    )
    extracted_text: Mapped[str | None] = mapped_column(Text)
    text_storage_key: Mapped[str | None] = mapped_column(Text)
    truncated: Mapped[bool] = mapped_column(Boolean, default=False)
    page_count: Mapped[int | None] = mapped_column(Integer)
    extraction_engine: Mapped[str] = mapped_column(Text)
    extraction_error: Mapped[str | None] = mapped_column(Text)
    extracted_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    document: Mapped[Document] = relationship(back_populates="extraction")


class DocumentClassification(Base):
    """Append-only, like finding_history: a re-classification writes a new
    row so "what did the classifier think, and when" stays answerable."""

    __tablename__ = "document_classifications"
    __table_args__ = (
        CheckConstraint(
            "confidence >= 0 AND confidence <= 1", name="ck_classification_confidence_range"
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE")
    )
    category: Mapped[str] = mapped_column(Text)
    confidence: Mapped[Decimal] = mapped_column(Numeric(4, 3))
    method: Mapped[str] = mapped_column(Text)
    reasoning: Mapped[str | None] = mapped_column(Text)
    classified_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    document: Mapped[Document] = relationship(back_populates="classifications")
