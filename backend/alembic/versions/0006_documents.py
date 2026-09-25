"""Intake documents: upload/URL submission, extraction, relevancy classification.

Raw bytes never enter this database — `storage_backend`/`storage_key` point at
an object store, and `content_hash` (sha256 of the raw bytes) is what the
workpaper can later cite as unchanged, mirroring how `evidence_items` already
hashes rather than fully stores its payload [SCHEMA D4]. A document row is the
audit trail for "what was submitted, when, and what it was found to be" — the
bytes themselves live elsewhere.

`document_classifications` is append-only, like `finding_history`: a
re-classification (a better extraction, a corrected heuristic) writes a new
row rather than overwriting the old verdict, so "why did the tool think this
was a DPIA on Tuesday" stays answerable.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

DOCUMENT_SOURCE = postgresql.ENUM(
    "UPLOAD", "URL", name="document_source_t", create_type=False,
)
DOCUMENT_STATUS = postgresql.ENUM(
    "RECEIVED", "PROCESSING", "EXTRACTED", "CLASSIFIED", "REJECTED", "FAILED",
    name="document_status_t", create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    DOCUMENT_SOURCE.create(bind, checkfirst=True)
    DOCUMENT_STATUS.create(bind, checkfirst=True)

    op.create_table(
        "documents",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column(
            "engagement_id", sa.Integer,
            sa.ForeignKey("engagements.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("source_type", DOCUMENT_SOURCE, nullable=False),
        # Filename as uploaded, or the submitted URL. Never trusted as a path.
        sa.Column("original_name", sa.Text, nullable=False),
        sa.Column("declared_mime", sa.Text),
        # What magic-byte sniffing found. The filename extension is never
        # trusted for routing extraction or validation. [SOURCES: plan §Security]
        sa.Column("detected_mime", sa.Text),
        sa.Column("size_bytes", sa.BigInteger, nullable=False),
        sa.Column("content_hash", sa.Text, nullable=False),
        sa.Column("storage_backend", sa.Text, nullable=False),
        # Object key. Derived from the content hash, never from a user-supplied
        # filename, so a submitted "../../etc/passwd" cannot become a path.
        sa.Column("storage_key", sa.Text, nullable=False),
        sa.Column(
            "status", DOCUMENT_STATUS, nullable=False, server_default="RECEIVED",
        ),
        sa.Column("rejection_reason", sa.Text),
        sa.Column("uploaded_by", sa.Integer, sa.ForeignKey("users.id")),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("processed_at", sa.DateTime(timezone=True)),
        # Re-uploading the same bytes for the same engagement resolves to the
        # existing row rather than a duplicate — the same principle as evidence
        # hashing: identical content is identical evidence.
        sa.UniqueConstraint(
            "engagement_id", "content_hash", name="uq_documents_engagement_hash",
        ),
    )
    op.create_index("ix_documents_engagement", "documents", ["engagement_id", "status"])

    op.create_table(
        "document_extractions",
        sa.Column(
            "document_id", sa.BigInteger,
            sa.ForeignKey("documents.id", ondelete="CASCADE"), primary_key=True,
        ),
        # Capped at extraction time (see app/ingest/extract.py); the full text
        # of an oversized document lives at text_storage_key instead, not here.
        sa.Column("extracted_text", sa.Text),
        sa.Column("text_storage_key", sa.Text),
        sa.Column("truncated", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("page_count", sa.Integer),
        sa.Column("extraction_engine", sa.Text, nullable=False),
        sa.Column("extraction_error", sa.Text),
        sa.Column(
            "extracted_at", sa.DateTime(timezone=True), nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.create_table(
        "document_classifications",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column(
            "document_id", sa.BigInteger,
            sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("category", sa.Text, nullable=False),
        sa.Column("confidence", sa.Numeric(4, 3), nullable=False),
        sa.Column("method", sa.Text, nullable=False),
        sa.Column("reasoning", sa.Text),
        sa.Column(
            "classified_at", sa.DateTime(timezone=True), nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "confidence >= 0 AND confidence <= 1", name="ck_classification_confidence_range",
        ),
    )
    op.create_index(
        "ix_document_classifications_document", "document_classifications", ["document_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_document_classifications_document", table_name="document_classifications",
    )
    op.drop_table("document_classifications")
    op.drop_table("document_extractions")
    op.drop_index("ix_documents_engagement", table_name="documents")
    op.drop_table("documents")
    DOCUMENT_STATUS.drop(op.get_bind(), checkfirst=True)
    DOCUMENT_SOURCE.drop(op.get_bind(), checkfirst=True)
