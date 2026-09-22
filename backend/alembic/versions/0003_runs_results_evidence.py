"""Test runs, results and evidence.

Implements docs/SCHEMA.md section 3.4, renumbered to 0003 because Alembic is
linear and the estate was built first.

The CHECK constraints here are the product's argument expressed in DDL: a
verdict of INSUFFICIENT_EVIDENCE cannot be written without a recorded reason.
It is impossible, at the database level, to shrug.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

VERDICT = postgresql.ENUM(
    "PASS", "FAIL", "INSUFFICIENT_EVIDENCE", "NOT_APPLICABLE",
    name="verdict_t", create_type=False,
)
GATE_REASON = postgresql.ENUM(
    "G1_MIN_SAMPLE", "G2_CI_WIDTH", "G3_COVERAGE", "G4_MISSING_ARTIFACT",
    "G5_STALE_EVIDENCE", "G6_NON_REPRESENTATIVE", "G7_SOURCE_UNVERIFIED",
    "G8_TARGET_UNREACHABLE",
    name="gate_reason_t", create_type=False,
)
EVIDENCE_KIND = postgresql.ENUM(
    "DB_QUERY", "HTTP_PROBE", "FILE_ARTIFACT", "ATTESTATION",
    name="evidence_kind_t", create_type=False,
)
RUN_STATUS = postgresql.ENUM(
    "QUEUED", "RUNNING", "COMPLETE", "FAILED",
    name="run_status_t", create_type=False,
)
ROLE = postgresql.ENUM("CONSULTANT", "CLIENT", "REVIEWER", name="role_t", create_type=False)


def upgrade() -> None:
    op.create_table(
        "test_runs",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "engagement_id", sa.Integer,
            sa.ForeignKey("engagements.id", ondelete="CASCADE"), nullable=False,
        ),
        # Recorded so a run can be reproduced exactly. An assurance result
        # nobody can regenerate is an assertion, not a finding.
        sa.Column("seed", sa.BigInteger, nullable=False),
        sa.Column("suites", postgresql.ARRAY(sa.Text), nullable=False),
        sa.Column("status", RUN_STATUS, nullable=False, server_default="QUEUED"),
        sa.Column(
            "started_at", sa.DateTime(timezone=True), nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("engine_version", sa.Text, nullable=False),
        sa.Column("error", sa.Text),
    )

    op.create_table(
        "test_results",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column(
            "run_id", sa.Integer,
            sa.ForeignKey("test_runs.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("control_id", sa.Integer, sa.ForeignKey("controls.id"), nullable=False),
        sa.Column("procedure_id", sa.Integer, sa.ForeignKey("test_procedures.id")),

        sa.Column("verdict", VERDICT, nullable=False),
        # What the procedure measured, before the gate had its say. Keeping it
        # makes an override legible: "would have passed, but coverage was
        # 0.5%" is a different statement from "failed".
        sa.Column("raw_outcome", VERDICT),
        sa.Column("gate_fired", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column(
            "gate_reasons", postgresql.ARRAY(GATE_REASON),
            nullable=False, server_default="{}",
        ),
        sa.Column(
            "gate_explanations", postgresql.ARRAY(sa.Text),
            nullable=False, server_default="{}",
        ),
        sa.Column(
            "gate_remedies", postgresql.ARRAY(sa.Text),
            nullable=False, server_default="{}",
        ),

        # Statistics live with the verdict rather than being recomputed. A
        # conclusion has to be reproducible from its own row.
        sa.Column("sample_size", sa.Integer),
        sa.Column("population_size", sa.BigInteger),
        sa.Column("successes", sa.Integer),
        sa.Column("coverage_pct", sa.Numeric(6, 3)),
        sa.Column("point_estimate", sa.Numeric(6, 5)),
        sa.Column("ci_lower", sa.Numeric(6, 5)),
        sa.Column("ci_upper", sa.Numeric(6, 5)),
        sa.Column("ci_method", sa.Text),
        sa.Column(
            "ci_width", sa.Numeric(6, 5),
            sa.Computed("ci_upper - ci_lower", persisted=True),
        ),

        sa.Column("thresholds_applied", postgresql.JSONB, nullable=False, server_default="{}"),
        # Every loosened threshold, printed in the workpaper. Widening a bound
        # to turn INSUFFICIENT_EVIDENCE into PASS is the one manoeuvre that
        # would hollow this product out, so it is recorded, not hidden.
        sa.Column("threshold_overrides", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("detail", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("duration_ms", sa.Integer),
        sa.Column(
            "run_at", sa.DateTime(timezone=True), nullable=False,
            server_default=sa.func.now(),
        ),

        sa.CheckConstraint(
            "population_size IS NULL OR sample_size IS NULL "
            "OR sample_size <= population_size",
            name="ck_sample_le_population",
        ),
        sa.CheckConstraint(
            "sample_size IS NULL OR successes IS NULL OR successes <= sample_size",
            name="ck_successes_le_sample",
        ),
        # The two that matter. A gate that fired must say why, and an
        # INSUFFICIENT_EVIDENCE verdict must have come from the gate. Together
        # they make an unexplained non-answer unrepresentable.
        sa.CheckConstraint(
            "NOT gate_fired OR cardinality(gate_reasons) > 0",
            name="ck_gate_reasons_present",
        ),
        sa.CheckConstraint(
            "verdict <> 'INSUFFICIENT_EVIDENCE' OR gate_fired",
            name="ck_insufficient_implies_gate",
        ),
    )

    op.create_table(
        "evidence_items",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column(
            "result_id", sa.BigInteger,
            sa.ForeignKey("test_results.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("kind", EVIDENCE_KIND, nullable=False),
        sa.Column("label", sa.Text, nullable=False),
        sa.Column("source_ref", sa.Text),
        sa.Column("payload", postgresql.JSONB),
        # So the workpaper can assert the evidence has not changed since the
        # conclusion was drawn from it.
        sa.Column("content_hash", sa.Text, nullable=False),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("age_days", sa.Integer),
        sa.Column("is_sufficient", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("insufficiency_note", sa.Text),
    )

    # Append-only. The assurance tool has to be auditable itself. [PRD P4]
    op.create_table(
        "audit_log",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column(
            "occurred_at", sa.DateTime(timezone=True), nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("actor_id", sa.Integer, sa.ForeignKey("users.id")),
        sa.Column("actor_role", ROLE),
        sa.Column("action", sa.Text, nullable=False),
        sa.Column("entity_type", sa.Text, nullable=False),
        sa.Column("entity_id", sa.Text),
        sa.Column("detail", postgresql.JSONB, nullable=False, server_default="{}"),
    )
    # A REVOKE does not bind the table owner, which is the application's own
    # user -- so revoking UPDATE and DELETE from PUBLIC leaves the log fully
    # rewritable by exactly the account that writes to it. A trigger binds
    # everyone, owner included.
    op.execute(
        """
        CREATE OR REPLACE FUNCTION audit_log_is_append_only()
        RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION
                'audit_log is append-only; % is not permitted', TG_OP
                USING ERRCODE = 'restrict_violation';
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER audit_log_no_rewrite
        BEFORE UPDATE OR DELETE ON audit_log
        FOR EACH ROW EXECUTE FUNCTION audit_log_is_append_only();
        """
    )
    op.execute("REVOKE UPDATE, DELETE ON audit_log FROM PUBLIC")

    # Now that test_results exists, the estate's assessment table can point
    # at it. Deferred from 0002 because Alembic is linear.
    op.create_foreign_key(
        "fk_assessment_result", "est_model_assessments", "test_results",
        ["result_id"], ["id"], ondelete="SET NULL",
    )

    op.create_index("ix_results_run", "test_results", ["run_id"])
    op.create_index(
        "ix_results_control_time", "test_results", ["control_id", "run_at"],
        postgresql_using="btree",
    )
    op.create_index("ix_results_verdict", "test_results", ["verdict"])
    op.create_index(
        "ix_results_gate", "test_results", ["gate_reasons"], postgresql_using="gin"
    )
    op.create_index("ix_evidence_result", "evidence_items", ["result_id"])
    op.create_index(
        "ix_audit_entity", "audit_log", ["entity_type", "entity_id", "occurred_at"]
    )


def downgrade() -> None:
    for index, table in (
        ("ix_audit_entity", "audit_log"),
        ("ix_evidence_result", "evidence_items"),
        ("ix_results_gate", "test_results"),
        ("ix_results_verdict", "test_results"),
        ("ix_results_control_time", "test_results"),
        ("ix_results_run", "test_results"),
    ):
        op.drop_index(index, table_name=table)

    op.drop_constraint(
        "fk_assessment_result", "est_model_assessments", type_="foreignkey"
    )
    op.execute("DROP TRIGGER IF EXISTS audit_log_no_rewrite ON audit_log")
    op.execute("DROP FUNCTION IF EXISTS audit_log_is_append_only()")
    op.drop_table("audit_log")
    op.drop_table("evidence_items")
    op.drop_table("test_results")
    op.drop_table("test_runs")
