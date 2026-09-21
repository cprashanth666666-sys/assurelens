"""Migration 0001 produces the schema the specification requires.

Runs in Alembic's offline mode, so it needs no database and runs in CI before
Postgres is reachable. It asserts on the generated DDL rather than on a live
connection.
"""

import io
import re
from contextlib import redirect_stdout

import pytest
from alembic.config import Config

from alembic import command


@pytest.fixture(scope="module")
def ddl() -> str:
    """Generated SQL for `alembic upgrade head`, offline."""
    cfg = Config("alembic.ini")
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        command.upgrade(cfg, "head", sql=True)
    return buffer.getvalue()


def test_gate_reason_enum_has_all_eight_rules(ddl: str) -> None:
    """G1 to G8 must all exist.

    Gate reasons are structured values, never prose, so they can be counted
    and filtered. Losing one silently would make a gate unreportable.
    [SCHEMA D3, PRD 6.3]
    """
    match = re.search(r"CREATE TYPE gate_reason_t AS ENUM \(([^)]*)\)", ddl)
    assert match, "gate_reason_t was not created"

    for code in (
        "G1_MIN_SAMPLE", "G2_CI_WIDTH", "G3_COVERAGE", "G4_MISSING_ARTIFACT",
        "G5_STALE_EVIDENCE", "G6_NON_REPRESENTATIVE", "G7_SOURCE_UNVERIFIED",
        "G8_TARGET_UNREACHABLE",
    ):
        assert code in match.group(1)


def test_verdict_enum_includes_insufficient_evidence(ddl: str) -> None:
    """INSUFFICIENT_EVIDENCE is a peer verdict, not an error state. [PRD 6.2]"""
    assert "INSUFFICIENT_EVIDENCE" in ddl


def test_inference_mode_distinguishes_census_from_population(ddl: str) -> None:
    """Census controls (probe suites) skip the sampling gates. [TRD 4.3]"""
    assert "CREATE TYPE inference_mode_t AS ENUM ('POPULATION', 'CENSUS')" in ddl


def test_control_has_exactly_one_primary_clause(ddl: str) -> None:
    """A control's legal basis is a single primary clause.

    Enforced by a partial unique index rather than application code, so it
    cannot be bypassed by a seeding script.
    """
    assert "ux_control_primary_clause" in ddl
    assert re.search(
        r"ux_control_primary_clause.*WHERE is_primary", ddl, re.IGNORECASE | re.DOTALL
    )


def test_scoping_a_control_out_requires_a_written_reason(ddl: str) -> None:
    """Unexplained exclusions are how assurance scope quietly shrinks.

    [SCHEMA 3.3]
    """
    assert "ck_na_reason" in ddl
    assert "in_scope OR na_reason IS NOT NULL" in ddl


def test_all_ten_enum_types_are_created(ddl: str) -> None:
    for enum_name in (
        "verdict_t", "gate_reason_t", "severity_t", "finding_status_t",
        "evidence_kind_t", "inference_mode_t", "run_status_t",
        "source_status_t", "control_domain_t", "role_t",
    ):
        assert f"CREATE TYPE {enum_name} AS ENUM" in ddl
