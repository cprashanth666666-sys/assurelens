"""Enums, control library, engagements.

Implements docs/SCHEMA.md sections 3.1, 3.2 and 3.3.

Revision ID: 0001
Revises:
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# --- Enum definitions -------------------------------------------------------
# create_type=False: the types are created once, explicitly, below. Letting
# SQLAlchemy auto-create them per column produces duplicate-type errors when a
# type is reused across tables.

VERDICT = postgresql.ENUM(
    "PASS", "FAIL", "INSUFFICIENT_EVIDENCE", "NOT_APPLICABLE",
    name="verdict_t", create_type=False,
)

# Gate rule codes are structured, never prose, so they can be counted,
# filtered and rendered consistently. [SCHEMA D3, PRD 6.3]
GATE_REASON = postgresql.ENUM(
    "G1_MIN_SAMPLE", "G2_CI_WIDTH", "G3_COVERAGE", "G4_MISSING_ARTIFACT",
    "G5_STALE_EVIDENCE", "G6_NON_REPRESENTATIVE", "G7_SOURCE_UNVERIFIED",
    "G8_TARGET_UNREACHABLE",
    name="gate_reason_t", create_type=False,
)

SEVERITY = postgresql.ENUM(
    "CRITICAL", "HIGH", "MEDIUM", "LOW", name="severity_t", create_type=False,
)

FINDING_STATUS = postgresql.ENUM(
    "OPEN", "IN_REMEDIATION", "RETEST_PENDING", "CLOSED", "ACCEPTED_RISK",
    name="finding_status_t", create_type=False,
)

EVIDENCE_KIND = postgresql.ENUM(
    "DB_QUERY", "HTTP_PROBE", "FILE_ARTIFACT", "ATTESTATION",
    name="evidence_kind_t", create_type=False,
)

# CENSUS controls (the probe set *is* the population) skip the sampling gates
# G1/G2/G3. POPULATION controls do not. [TRD 4.3]
INFERENCE_MODE = postgresql.ENUM(
    "POPULATION", "CENSUS", name="inference_mode_t", create_type=False,
)

RUN_STATUS = postgresql.ENUM(
    "QUEUED", "RUNNING", "COMPLETE", "FAILED", name="run_status_t", create_type=False,
)

SOURCE_STATUS = postgresql.ENUM(
    "VERIFIED", "UNVERIFIED", name="source_status_t", create_type=False,
)

CONTROL_DOMAIN = postgresql.ENUM(
    "NOTICE_CONSENT", "SECURITY_SAFEGUARDS", "RETENTION_ERASURE",
    "PRINCIPAL_RIGHTS", "THIRD_PARTY_TRANSFER", "AI_GOVERNANCE",
    "BREACH_RESPONSE", "GOVERNANCE_ACCOUNTABILITY",
    name="control_domain_t", create_type=False,
)

ROLE = postgresql.ENUM(
    "CONSULTANT", "CLIENT", "REVIEWER", name="role_t", create_type=False,
)

_ALL_ENUMS = [
    VERDICT, GATE_REASON, SEVERITY, FINDING_STATUS, EVIDENCE_KIND,
    INFERENCE_MODE, RUN_STATUS, SOURCE_STATUS, CONTROL_DOMAIN, ROLE,
]


def upgrade() -> None:
    bind = op.get_bind()
    for enum in _ALL_ENUMS:
        enum.create(bind, checkfirst=True)

    # --- Control library ---------------------------------------------------

    op.create_table(
        "frameworks",
        sa.Column("id", sa.SmallInteger, primary_key=True, autoincrement=True),
        sa.Column("code", sa.Text, nullable=False, unique=True),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("version", sa.Text, nullable=False),
        sa.Column("authority", sa.Text),
        sa.Column("source_url", sa.Text),
    )

    op.create_table(
        "framework_clauses",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "framework_id", sa.SmallInteger,
            sa.ForeignKey("frameworks.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("ref", sa.Text, nullable=False),
        sa.Column("title", sa.Text, nullable=False),
        # Verbatim statutory text. Rendered by ClauseQuote so the reader sees
        # the statute rather than a paraphrase. [UX 4.3]
        sa.Column("verbatim_text", sa.Text),
        sa.Column("in_force_from", sa.Date),
        sa.Column(
            "source_status", SOURCE_STATUS, nullable=False, server_default="VERIFIED",
        ),
        sa.Column("source_note", sa.Text),
        sa.UniqueConstraint("framework_id", "ref", name="uq_clause_framework_ref"),
    )

    op.create_table(
        "controls",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("ref", sa.Text, nullable=False, unique=True),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("objective", sa.Text, nullable=False),
        sa.Column("domain", CONTROL_DOMAIN, nullable=False),
        sa.Column("procedure_text", sa.Text, nullable=False),
        sa.Column(
            "inference_mode", INFERENCE_MODE, nullable=False, server_default="POPULATION",
        ),
        sa.Column("is_executable", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("auto_raise", sa.Boolean, nullable=False, server_default=sa.true()),
        # Per-control threshold overrides. Every non-null value is printed in
        # the workpaper threshold register — loosening a gate stays visible.
        # [PRD 6.3]
        sa.Column(
            "threshold_overrides", postgresql.JSONB, nullable=False, server_default="{}",
        ),
        sa.Column("yaml_source", sa.Text, nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.create_table(
        "control_clause_mappings",
        sa.Column(
            "control_id", sa.Integer,
            sa.ForeignKey("controls.id", ondelete="CASCADE"), primary_key=True,
        ),
        sa.Column(
            "clause_id", sa.Integer,
            sa.ForeignKey("framework_clauses.id", ondelete="CASCADE"), primary_key=True,
        ),
        sa.Column("is_primary", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("rationale", sa.Text),
    )

    # Exactly one primary clause per control: its legal basis.
    op.create_index(
        "ux_control_primary_clause", "control_clause_mappings", ["control_id"],
        unique=True, postgresql_where=sa.text("is_primary"),
    )
    op.create_index("ix_ctrl_map_clause", "control_clause_mappings", ["clause_id"])

    op.create_table(
        "test_procedures",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "control_id", sa.Integer,
            sa.ForeignKey("controls.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("plugin_key", sa.Text, nullable=False),
        sa.Column("suite", sa.Text, nullable=False),
        sa.Column("config", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("evidence_contract", postgresql.JSONB, nullable=False),
        sa.UniqueConstraint("control_id", "plugin_key", name="uq_procedure_control_plugin"),
    )

    # --- Engagements -------------------------------------------------------

    op.create_table(
        "organizations",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("sector", sa.Text),
        sa.Column("city", sa.Text),
        sa.Column("headcount", sa.Integer),
        # Drives whether Rule 13 (annual DPIA + audit, algorithmic due
        # diligence) is in scope. [SOURCES A1.3]
        sa.Column(
            "is_significant_data_fiduciary", sa.Boolean, nullable=False,
            server_default=sa.false(),
        ),
        # The estate is generated. The UI disclosure depends on this. [SCHEMA D6]
        sa.Column("is_synthetic", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("notes", sa.Text),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("email", sa.Text, unique=True),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("role", ROLE, nullable=False),
        sa.Column("org_id", sa.Integer, sa.ForeignKey("organizations.id")),
        # v1 has no auth; the demo actor is written instead. Schema is
        # auth-ready so adding it later needs no migration. [SCHEMA D7, TRD 9]
        sa.Column("is_demo_actor", sa.Boolean, nullable=False, server_default=sa.false()),
    )

    op.create_table(
        "engagements",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "org_id", sa.Integer,
            sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("scope_note", sa.Text),
        sa.Column("period_start", sa.Date),
        sa.Column("period_end", sa.Date),
        # 2027-05-13 for Meridian: eighteen months after G.S.R. 846(E) of
        # 13 Nov 2025, per Rule 1(4). [SOURCES A1.1]
        sa.Column("compliance_deadline", sa.Date),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.create_table(
        "engagement_controls",
        sa.Column(
            "engagement_id", sa.Integer,
            sa.ForeignKey("engagements.id", ondelete="CASCADE"), primary_key=True,
        ),
        sa.Column(
            "control_id", sa.Integer,
            sa.ForeignKey("controls.id", ondelete="CASCADE"), primary_key=True,
        ),
        sa.Column("in_scope", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("na_reason", sa.Text),
        sa.Column("evidence_owner", sa.Text),
        # A control cannot be scoped out without a written reason. Unexplained
        # exclusions are how assurance scope quietly shrinks to what passes.
        sa.CheckConstraint(
            "in_scope OR na_reason IS NOT NULL", name="ck_na_reason",
        ),
    )


def downgrade() -> None:
    op.drop_table("engagement_controls")
    op.drop_table("engagements")
    op.drop_table("users")
    op.drop_table("organizations")
    op.drop_table("test_procedures")
    op.drop_index("ix_ctrl_map_clause", table_name="control_clause_mappings")
    op.drop_index("ux_control_primary_clause", table_name="control_clause_mappings")
    op.drop_table("control_clause_mappings")
    op.drop_table("controls")
    op.drop_table("framework_clauses")
    op.drop_table("frameworks")

    bind = op.get_bind()
    for enum in reversed(_ALL_ENUMS):
        enum.drop(bind, checkfirst=True)
