"""Findings, history, remediation. [Day 8, SCHEMA 3.5]

findings.ref is globally unique ('F-003'), allocated by FindingService, not
by the caller -- a client-supplied ref could collide or skip, and either
failure mode is invisible until two findings fight over the same number.

finding_history is append-only, mirroring audit_log: every field a
consultant changes leaves a row, so "who moved this to CLOSED and when" is
answerable without trusting anyone's memory.

remediation_items exists here but nothing populates it yet. A finding is a
measured fact; a remediation item is a plan someone has committed to, and
this project does not fabricate a plan on a control's behalf. It is filled
in once a consultant actually writes one -- Day 8's roadmap reads directly
from findings instead. [severity_t and finding_status_t were created in
migration 0001, ahead of this table's need for them.]
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

SEVERITY = postgresql.ENUM(
    "CRITICAL", "HIGH", "MEDIUM", "LOW", name="severity_t", create_type=False,
)
FINDING_STATUS = postgresql.ENUM(
    "OPEN", "IN_REMEDIATION", "RETEST_PENDING", "CLOSED", "ACCEPTED_RISK",
    name="finding_status_t", create_type=False,
)


def upgrade() -> None:
    op.create_table(
        "findings",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("ref", sa.Text, nullable=False, unique=True),
        sa.Column(
            "engagement_id", sa.Integer,
            sa.ForeignKey("engagements.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column(
            "control_id", sa.Integer,
            sa.ForeignKey("controls.id"), nullable=False,
        ),
        sa.Column(
            "origin_result_id", sa.BigInteger,
            sa.ForeignKey("test_results.id"),
        ),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("root_cause", sa.Text),
        sa.Column("recommendation", sa.Text),
        sa.Column("likelihood", sa.SmallInteger, nullable=False),
        sa.Column("impact", sa.SmallInteger, nullable=False),
        sa.Column(
            "risk_score", sa.SmallInteger,
            sa.Computed("likelihood * impact", persisted=True),
        ),
        sa.Column("severity", SEVERITY, nullable=False),
        sa.Column("owner", sa.Text),
        sa.Column("effort_days", sa.Numeric(5, 1)),
        sa.Column(
            "status", FINDING_STATUS, nullable=False, server_default="OPEN",
        ),
        sa.Column(
            "is_internal_note_only", sa.Boolean, nullable=False,
            server_default=sa.false(),
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "likelihood BETWEEN 1 AND 5", name="ck_finding_likelihood_range",
        ),
        sa.CheckConstraint(
            "impact BETWEEN 1 AND 5", name="ck_finding_impact_range",
        ),
    )
    op.create_index(
        "ix_findings_engagement", "findings", ["engagement_id", "status"],
    )
    op.create_index(
        "ix_findings_risk", "findings", [sa.text("risk_score DESC")],
    )
    # One open finding per (engagement, control): a re-run that still fails
    # refreshes the existing finding rather than duplicating it.
    op.create_index(
        "ux_findings_open_per_control",
        "findings", ["engagement_id", "control_id"],
        unique=True,
        postgresql_where=sa.text(
            "status IN ('OPEN', 'IN_REMEDIATION', 'RETEST_PENDING')"
        ),
    )

    op.create_table(
        "finding_history",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column(
            "finding_id", sa.Integer,
            sa.ForeignKey("findings.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column(
            "changed_at", sa.DateTime(timezone=True), nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("actor_id", sa.Integer, sa.ForeignKey("users.id")),
        sa.Column("field", sa.Text, nullable=False),
        sa.Column("old_value", sa.Text),
        sa.Column("new_value", sa.Text),
    )
    op.create_index(
        "ix_finding_history_finding", "finding_history", ["finding_id"],
    )

    op.create_table(
        "remediation_items",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "finding_id", sa.Integer,
            sa.ForeignKey("findings.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("sequence", sa.SmallInteger, nullable=False),
        sa.Column("action", sa.Text, nullable=False),
        sa.Column("owner", sa.Text),
        sa.Column("effort_days", sa.Numeric(5, 1)),
        sa.Column("target_date", sa.Date),
        sa.Column("expected_residual_risk", sa.SmallInteger),
        sa.CheckConstraint(
            "expected_residual_risk IS NULL "
            "OR expected_residual_risk BETWEEN 1 AND 25",
            name="ck_remediation_residual_range",
        ),
        sa.UniqueConstraint(
            "finding_id", "sequence", name="uq_remediation_finding_sequence",
        ),
    )


def downgrade() -> None:
    op.drop_table("remediation_items")
    op.drop_index("ix_finding_history_finding", table_name="finding_history")
    op.drop_table("finding_history")
    op.drop_index("ux_findings_open_per_control", table_name="findings")
    op.drop_index("ix_findings_risk", table_name="findings")
    op.drop_index("ix_findings_engagement", table_name="findings")
    op.drop_table("findings")
