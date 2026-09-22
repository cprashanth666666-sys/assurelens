"""Synthetic estate: Meridian's generated data assets, principals, consent,
processors, access logs and model registry.

Implements docs/SCHEMA.md section 3.6, renumbered to 0002 because Alembic is
linear and the estate is built before the results tables.

Every table is prefixed `est_` so it can never be mistaken for assessment
data. [SCHEMA D6]
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "est_data_assets",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "org_id", sa.Integer,
            sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("system", sa.Text),
        sa.Column("classification", sa.Text),
        # What the inventory CLAIMS the asset holds. Suite 1 compares this
        # against what detectors actually find; the gap is the finding.
        sa.Column(
            "declared_identifier_classes", postgresql.ARRAY(sa.Text),
            nullable=False, server_default="{}",
        ),
        sa.Column(
            "encryption_at_rest", sa.Boolean, nullable=False, server_default=sa.false(),
        ),
        sa.Column("record_count", sa.BigInteger),
        sa.Column("hosted_region", sa.Text),
    )

    op.create_table(
        "est_processing_activities",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "org_id", sa.Integer,
            sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("purpose", sa.Text, nullable=False),
        sa.Column("lawful_basis", sa.Text, nullable=False),
        sa.Column("asset_id", sa.Integer, sa.ForeignKey("est_data_assets.id")),
        sa.Column("retention_days", sa.Integer),
        # Rule 8(3) sets a one-year floor. Seeded below it for one activity,
        # which is defect S6.
        sa.Column("log_retention_days", sa.Integer),
    )

    op.create_table(
        "est_data_principals",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column(
            "org_id", sa.Integer,
            sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("external_ref", sa.Text, nullable=False),
        # Drives the s.8(8) "purpose deemed no longer served" clock.
        sa.Column("last_contact_at", sa.DateTime(timezone=True)),
        sa.Column("erased_at", sa.DateTime(timezone=True)),
        # The s.8(7)(a) carve-out: retention necessary for compliance with
        # law. For a bank this is the norm, not the exception -- the Act's own
        # Illustration (II) is a bank holding client identity records for ten
        # years. A record held WITHOUT a recorded basis is the finding.
        sa.Column("legal_hold", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("legal_hold_basis", sa.Text),
        sa.Column("pre_erasure_notice_at", sa.DateTime(timezone=True)),
        # Fairness grouping for suite 5.
        sa.Column("group_attribute", sa.Text),
        sa.Column("is_minor", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.UniqueConstraint("org_id", "external_ref", name="uq_principal_external_ref"),
    )

    op.create_table(
        "est_consent_records",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column(
            "principal_id", sa.BigInteger,
            sa.ForeignKey("est_data_principals.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("purpose", sa.Text, nullable=False),
        sa.Column("status", sa.Text, nullable=False),
        sa.Column("granted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("withdrawn_at", sa.DateTime(timezone=True)),
        # Defect S1 lives here: the consent store updates instantly while the
        # downstream segment refreshes on a nightly batch, so the record looks
        # compliant while the principal keeps being processed.
        sa.Column("downstream_synced_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint(
            "principal_id", "purpose", name="uq_consent_principal_purpose"
        ),
    )

    op.create_table(
        "est_consent_events",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column(
            "consent_id", sa.BigInteger,
            sa.ForeignKey("est_consent_records.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("event", sa.Text, nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("latency_ms", sa.BigInteger),
    )

    op.create_table(
        "est_third_parties",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "org_id", sa.Integer,
            sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("category", sa.Text),
        # NULL is half of defect S4: no processor agreement on file, which
        # Act s.8(2) requires before engaging a processor at all.
        sa.Column("dpa_reference", sa.Text),
        sa.Column(
            "granted_scopes", postgresql.ARRAY(sa.Text),
            nullable=False, server_default="{}",
        ),
        sa.Column(
            "exercised_scopes", postgresql.ARRAY(sa.Text),
            nullable=False, server_default="{}",
        ),
        sa.Column("credential_issued_at", sa.DateTime(timezone=True)),
        sa.Column("last_used_at", sa.DateTime(timezone=True)),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("relationship_ended_at", sa.DateTime(timezone=True)),
        sa.Column("country", sa.Text),
        # Opaque token the probe suite authenticates with, so a stale
        # credential is tested over HTTP rather than asserted from a row.
        sa.Column("credential_token", sa.Text),
    )

    op.create_table(
        "est_access_logs",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column(
            "org_id", sa.Integer,
            sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("actor_ref", sa.Text, nullable=False),
        sa.Column("asset_id", sa.Integer, sa.ForeignKey("est_data_assets.id")),
        sa.Column("action", sa.Text, nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("was_authorised", sa.Boolean),
    )

    op.create_table(
        "est_model_registry",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "org_id", sa.Integer,
            sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("purpose", sa.Text, nullable=False),
        sa.Column("deployed_at", sa.DateTime(timezone=True)),
        # Per-feature quantile bins captured at training time. PSI is measured
        # against this, so without it drift is not computable at all.
        sa.Column("training_snapshot", postgresql.JSONB),
        sa.Column(
            "has_drift_monitoring", sa.Boolean, nullable=False,
            server_default=sa.false(),
        ),
        # Rule 13(3) bites on software affecting the rights of Data
        # Principals; a model that only sorts a queue does not.
        sa.Column(
            "is_consequential", sa.Boolean, nullable=False, server_default=sa.true(),
        ),
    )

    op.create_table(
        "est_model_predictions",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column(
            "model_id", sa.Integer,
            sa.ForeignKey("est_model_registry.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column(
            "principal_id", sa.BigInteger, sa.ForeignKey("est_data_principals.id")
        ),
        sa.Column("features", postgresql.JSONB, nullable=False),
        sa.Column("score", sa.Numeric(8, 6)),
        sa.Column("decision", sa.Text),
        # Present only where an outcome is known, which is what makes the
        # equal-opportunity metric computable on a subset.
        sa.Column("ground_truth", sa.Text),
        sa.Column("predicted_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "est_model_assessments",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column(
            "model_id", sa.Integer,
            sa.ForeignKey("est_model_registry.id", ondelete="CASCADE"), nullable=False,
        ),
        # Foreign key to test_results is added in the migration that creates
        # that table, since Alembic is linear and it does not exist yet.
        sa.Column("result_id", sa.BigInteger),
        sa.Column("metric", sa.Text, nullable=False),
        sa.Column("feature", sa.Text),
        sa.Column("group_label", sa.Text),
        sa.Column("value", sa.Numeric(12, 6)),
        # Carried so a group below the minimum size is reported as
        # insufficient evidence rather than as a disparity. Small-group noise
        # masquerading as bias is the classic fairness-audit error.
        sa.Column("group_n", sa.Integer),
        sa.Column(
            "assessed_at", sa.DateTime(timezone=True), nullable=False,
            server_default=sa.func.now(),
        ),
    )

    # --- Indexes ------------------------------------------------------------
    # Partial index matching the retention scan's exact predicate: it is the
    # heaviest query in the product. [SCHEMA 4]
    op.create_index(
        "ix_principals_erasure", "est_data_principals", ["last_contact_at"],
        postgresql_where=sa.text("erased_at IS NULL AND NOT legal_hold"),
    )
    op.create_index("ix_consent_purpose", "est_consent_records", ["purpose", "status"])
    op.create_index("ix_consent_events_consent", "est_consent_events", ["consent_id"])
    op.create_index("ix_predictions_model", "est_model_predictions", ["model_id"])
    op.create_index(
        "ix_access_logs_actor", "est_access_logs", ["actor_ref", "occurred_at"]
    )
    op.create_index("ix_assessments_model", "est_model_assessments", ["model_id"])


def downgrade() -> None:
    for index, table in (
        ("ix_assessments_model", "est_model_assessments"),
        ("ix_access_logs_actor", "est_access_logs"),
        ("ix_predictions_model", "est_model_predictions"),
        ("ix_consent_events_consent", "est_consent_events"),
        ("ix_consent_purpose", "est_consent_records"),
        ("ix_principals_erasure", "est_data_principals"),
    ):
        op.drop_index(index, table_name=table)

    for table in (
        "est_model_assessments", "est_model_predictions", "est_model_registry",
        "est_access_logs", "est_third_parties", "est_consent_events",
        "est_consent_records", "est_data_principals",
        "est_processing_activities", "est_data_assets",
    ):
        op.drop_table(table)
