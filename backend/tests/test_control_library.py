"""The control library is the intellectual core of the project.

These tests assert the properties that make it defensible, not merely
loadable: every control has one legal basis, every VERIFIED clause quotes the
instrument, and nothing is scoped out without a written reason.
"""

from __future__ import annotations

import datetime as dt
import shutil
from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.control import (
    Control,
    ControlClauseMapping,
    EngagementControl,
    Framework,
    FrameworkClause,
)
from app.seed.controls import (
    FRAMEWORK_FILES,
    ControlLibraryError,
    controls_directory,
    load_control_library,
)

pytestmark = pytest.mark.usefixtures("seeded_db")


def test_library_size(seeded_db: Session) -> None:
    """25 controls, capped deliberately. Depth over breadth. [PRD R1]"""
    controls = seeded_db.scalars(select(Control)).all()

    assert len(controls) == 25
    assert sum(1 for c in controls if c.is_executable) == 13


def test_every_control_has_exactly_one_primary_clause(seeded_db: Session) -> None:
    """A control without a single legal basis is a good practice, not a control.

    [PRD P2]
    """
    for control in seeded_db.scalars(select(Control)).all():
        primaries = [m for m in control.mappings if m.is_primary]
        assert len(primaries) == 1, f"{control.ref} has {len(primaries)} primary clauses"


def test_every_primary_clause_is_a_dpdp_provision(seeded_db: Session) -> None:
    """ISO and NIST are cross-references. They never carry the legal basis."""
    for control in seeded_db.scalars(select(Control)).all():
        primary = control.primary_mapping
        assert primary is not None
        assert primary.clause.framework.code == "DPDP", (
            f"{control.ref} rests on {primary.clause.framework.code}, not DPDP"
        )


def test_verified_clauses_quote_the_instrument(seeded_db: Session) -> None:
    """A clause asserted as VERIFIED with nothing to point at is the exact
    unsupported assertion this product refuses to make."""
    verified = seeded_db.scalars(
        select(FrameworkClause).where(FrameworkClause.source_status == "VERIFIED")
    ).all()

    assert verified, "no verified clauses loaded"
    for clause in verified:
        assert clause.verbatim_text, f"{clause.ref} is VERIFIED but quotes nothing"


def test_unverified_clauses_explain_themselves(seeded_db: Session) -> None:
    """An unverified citation must say why, so a reader knows what it rests on."""
    unverified = seeded_db.scalars(
        select(FrameworkClause).where(FrameworkClause.source_status == "UNVERIFIED")
    ).all()

    assert unverified, "expected ISO and NIST cross-references to be unverified"
    for clause in unverified:
        assert clause.source_note, f"{clause.ref} is UNVERIFIED with no note"


def test_iso_and_nist_are_all_unverified(seeded_db: Session) -> None:
    """ISO/IEC 27001 is a paid standard this project has not purchased.

    Marking those mappings VERIFIED would be an unsupported assertion. They
    are secondary references, so this does not gate any control — G7 looks
    only at the primary clause.
    """
    for code in ("ISO27001", "NIST_AI_RMF"):
        framework = seeded_db.scalar(select(Framework).where(Framework.code == code))
        assert framework is not None
        assert framework.clauses
        assert all(c.source_status == "UNVERIFIED" for c in framework.clauses)


def test_executable_controls_declare_a_procedure(seeded_db: Session) -> None:
    for control in seeded_db.scalars(select(Control)).all():
        if control.is_executable:
            assert control.procedures, f"{control.ref} is executable but has no procedure"
            assert control.procedures[0].evidence_contract
        else:
            assert not control.procedures


def test_commencement_dates_match_rule_1(seeded_db: Session) -> None:
    """Rules 3 and 5-16 commence eighteen months after 13 Nov 2025; Rule 4 at
    twelve months. The Act is already in force. [SOURCES A1.1]"""
    by_ref = {
        c.ref: c
        for c in seeded_db.scalars(
            select(FrameworkClause).join(Framework).where(Framework.code == "DPDP")
        ).all()
    }

    assert by_ref["R6(1)(b)"].in_force_from == dt.date(2027, 5, 13)
    assert by_ref["R13(3)"].in_force_from == dt.date(2027, 5, 13)
    assert by_ref["R4"].in_force_from == dt.date(2026, 11, 13)
    assert by_ref["Act s.8(7)(a)"].in_force_from == dt.date(2023, 8, 11)


def test_third_schedule_control_is_scoped_out_with_a_reason(
    seeded_db: Session,
) -> None:
    """Meridian is a BFSI GCC, and the Third Schedule names only e-commerce,
    online gaming and social media intermediaries above user thresholds. A
    control that tested Rule 8(1) here would be testing an inapplicable rule.
    [SOURCES A1.3 correction]
    """
    control = seeded_db.scalar(select(Control).where(Control.ref == "DPDP-08-04"))
    assert control is not None

    scoped = seeded_db.scalar(
        select(EngagementControl).where(EngagementControl.control_id == control.id)
    )
    assert scoped is not None
    assert scoped.in_scope is False
    assert scoped.na_reason
    assert "Third Schedule" in scoped.na_reason


def test_erasure_control_rests_on_the_act_not_the_third_schedule(
    seeded_db: Session,
) -> None:
    """For a bank, erasure is governed by Act s.8(7)(a) with its legal-retention
    carve-out — the Act illustrates that carve-out with a bank. Resting this
    control on Rule 8(1) would be a citation error an informed reviewer would
    catch immediately."""
    control = seeded_db.scalar(select(Control).where(Control.ref == "DPDP-08-01"))
    assert control is not None
    assert control.primary_mapping is not None
    assert control.primary_mapping.clause.ref == "Act s.8(7)(a)"


def test_ai_controls_rest_on_rule_13_3(seeded_db: Session) -> None:
    """Rule 13(3) is what makes fairness and drift testing a statutory
    obligation rather than a voluntary good practice. [PRD 5.2]"""
    for ref in ("DPDP-13-02", "DPDP-13-03"):
        control = seeded_db.scalar(select(Control).where(Control.ref == ref))
        assert control is not None
        assert control.primary_mapping is not None
        assert control.primary_mapping.clause.ref == "R13(3)"


def test_every_control_is_scoped_for_the_engagement(seeded_db: Session) -> None:
    controls = seeded_db.scalars(select(Control)).all()
    scoped = seeded_db.scalars(select(EngagementControl)).all()

    assert len(scoped) == len(controls)
    assert all(s.evidence_owner for s in scoped)


def test_database_refuses_a_second_primary_clause(seeded_db: Session) -> None:
    """Enforced by a partial unique index, not application code, so a seeding
    script cannot bypass it."""
    control = seeded_db.scalar(select(Control).where(Control.ref == "DPDP-06-02"))
    assert control is not None
    other = seeded_db.scalar(
        select(FrameworkClause).where(FrameworkClause.ref == "R6(1)(d)")
    )
    assert other is not None

    seeded_db.add(
        ControlClauseMapping(
            control_id=control.id, clause_id=other.id, is_primary=True
        )
    )
    with pytest.raises(IntegrityError):
        seeded_db.flush()
    seeded_db.rollback()


def test_database_refuses_scoping_out_without_a_reason(seeded_db: Session) -> None:
    """`CHECK (in_scope OR na_reason IS NOT NULL)`. Unexplained exclusions are
    how assurance scope quietly shrinks to whatever passes. [SCHEMA 3.3]"""
    scoped = seeded_db.scalar(
        select(EngagementControl).where(EngagementControl.in_scope.is_(True)).limit(1)
    )
    assert scoped is not None

    scoped.in_scope = False
    scoped.na_reason = None
    with pytest.raises(IntegrityError):
        seeded_db.flush()
    seeded_db.rollback()


def test_every_population_source_names_required_evidence(seeded_db: Session) -> None:
    """What the loader enforces, checked against what it actually stored."""
    for control in seeded_db.scalars(select(Control)).all():
        for procedure in control.procedures:
            contract = procedure.evidence_contract or {}
            source = contract.get("population_source")
            if source is not None:
                names = [item["name"] for item in contract.get("required", [])]
                assert source in names, f"{control.ref}: {source!r} not in {names}"


def test_the_loader_refuses_a_population_source_that_matches_nothing(
    seeded_db: Session, tmp_path: Path
) -> None:
    for filename in FRAMEWORK_FILES:
        shutil.copy(controls_directory() / filename, tmp_path / filename)
    dpdp = tmp_path / "dpdp.yaml"
    text = dpdp.read_text(encoding="utf-8")
    assert "population_source: third_parties" in text
    dpdp.write_text(
        text.replace("population_source: third_parties", "population_source: third_party", 1),
        encoding="utf-8",
    )

    # A savepoint, so the framework upserts that precede the refusal do not
    # leak into the session every other test shares.
    savepoint = seeded_db.begin_nested()
    try:
        with pytest.raises(ControlLibraryError, match="'third_party'"):
            load_control_library(seeded_db, tmp_path)
    finally:
        savepoint.rollback()
