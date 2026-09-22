"""Load the control library from YAML into the database.

The library lives in git so it is reviewable as a diff; the database is a
projection of it. [TRD ADR-008]

Idempotent: running twice produces the same state. Validation is strict and
fails loudly — a control library that silently drops a mapping is worse than
one that refuses to load, because the gap is invisible in the workpaper.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Any

import yaml
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.control import (
    Control,
    ControlClauseMapping,
    Engagement,
    EngagementControl,
    Framework,
    FrameworkClause,
    Organization,
    TestProcedure,
    User,
)
from app.models.results import TestResult

# Repo-root-relative default, correct for a source checkout. Overridden by
# CONTROLS_DIR in the container, where the source tree is not the repo tree.
_DEFAULT_CONTROLS_DIR = Path(__file__).resolve().parents[3] / "controls"


def controls_directory() -> Path:
    configured = get_settings().controls_dir
    return Path(configured) if configured else _DEFAULT_CONTROLS_DIR

# Files carrying a framework plus its clauses. dpdp.yaml also carries the
# controls themselves.
FRAMEWORK_FILES = ("dpdp.yaml", "iso27001_map.yaml", "nist_ai_rmf_map.yaml")


class ControlLibraryError(RuntimeError):
    """The library on disk is invalid. Never silently tolerated."""


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ControlLibraryError(
            f"{path} not found. The controls directory is bind-mounted; on a "
            f"fresh clone check that it was not created empty."
        )
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ControlLibraryError(f"{path} did not parse to a mapping.")
    return data


def _upsert_framework(db: Session, spec: dict[str, Any]) -> Framework:
    fw = db.scalar(select(Framework).where(Framework.code == spec["code"]))
    if fw is None:
        fw = Framework(code=spec["code"])
        db.add(fw)
    fw.name = spec["name"]
    fw.version = spec["version"]
    fw.authority = spec.get("authority")
    fw.source_url = spec.get("source_url")
    db.flush()
    return fw


def _upsert_clause(
    db: Session, framework: Framework, spec: dict[str, Any]
) -> FrameworkClause:
    clause = db.scalar(
        select(FrameworkClause).where(
            FrameworkClause.framework_id == framework.id,
            FrameworkClause.ref == spec["ref"],
        )
    )
    if clause is None:
        clause = FrameworkClause(framework_id=framework.id, ref=spec["ref"])
        db.add(clause)

    clause.title = spec["title"]
    verbatim = spec.get("verbatim_text")
    clause.verbatim_text = verbatim.strip() if verbatim else None
    clause.source_status = spec.get("source_status", "VERIFIED")
    clause.source_note = spec.get("source_note")

    in_force = spec.get("in_force_from")
    if isinstance(in_force, str):
        clause.in_force_from = dt.date.fromisoformat(in_force)
    elif isinstance(in_force, dt.date):
        clause.in_force_from = in_force

    # A clause asserted as VERIFIED with no text to point at is the exact
    # unsupported assertion this product refuses to make.
    if clause.source_status == "VERIFIED" and not clause.verbatim_text:
        raise ControlLibraryError(
            f"Clause {framework.code} {spec['ref']} is marked VERIFIED but "
            f"carries no verbatim_text. Quote the instrument or mark it "
            f"UNVERIFIED."
        )

    db.flush()
    return clause


def _upsert_control(db: Session, spec: dict[str, Any], source: str) -> Control:
    control = db.scalar(select(Control).where(Control.ref == spec["ref"]))
    if control is None:
        control = Control(ref=spec["ref"])
        db.add(control)

    control.title = spec["title"]
    control.objective = spec["objective"].strip()
    control.domain = spec["domain"]
    control.procedure_text = spec["procedure_text"].strip()
    control.inference_mode = spec.get("inference_mode", "POPULATION")
    control.is_executable = bool(spec.get("is_executable", False))
    control.auto_raise = bool(spec.get("auto_raise", True))
    control.threshold_overrides = spec.get("threshold_overrides") or {}
    control.yaml_source = source
    db.flush()
    return control


def _sync_mappings(
    db: Session,
    control: Control,
    specs: list[dict[str, Any]],
    clause_index: dict[tuple[str, str], FrameworkClause],
) -> None:
    """Replace this control's mappings with exactly what the YAML declares."""
    for existing in list(control.mappings):
        db.delete(existing)
    db.flush()

    primaries = [s for s in specs if s.get("primary")]
    if len(primaries) != 1:
        raise ControlLibraryError(
            f"Control {control.ref} declares {len(primaries)} primary clauses; "
            f"exactly one is required. A control without a single legal basis "
            f"is a good practice, not a control."
        )

    for spec in specs:
        # Default framework is DPDP: the primary basis is always a DPDP
        # provision, and most secondary refs are DPDP too.
        fw_code = spec.get("framework", "DPDP")
        key = (fw_code, spec["ref"])
        clause = clause_index.get(key)
        if clause is None:
            raise ControlLibraryError(
                f"Control {control.ref} references {fw_code} {spec['ref']}, "
                f"which is not defined in any clause file."
            )
        db.add(
            ControlClauseMapping(
                control_id=control.id,
                clause_id=clause.id,
                is_primary=bool(spec.get("primary")),
                rationale=spec.get("rationale"),
            )
        )
    db.flush()


def _sync_procedure(db: Session, control: Control, spec: dict[str, Any]) -> None:
    """Upsert the control's procedure rather than replacing it.

    Deleting and recreating looks equivalent and is not: test_results
    reference the procedure that produced them, so a delete violates that
    foreign key the moment any run exists. Since the library is upserted on
    every boot, that turned the first deploy after the first run into a crash.

    Keeping the row also keeps the link meaningful -- a workpaper cites which
    procedure produced a result, and a recreated row with a new id would
    quietly orphan that citation.
    """
    plugin_key = spec.get("plugin_key")
    suite = spec.get("suite")

    if not control.is_executable:
        # Genuinely no longer executable. Detach rather than delete, so
        # historical results keep their statistics and lose only the link.
        for existing in list(control.procedures):
            db.execute(
                update(TestResult)
                .where(TestResult.procedure_id == existing.id)
                .values(procedure_id=None)
            )
            db.delete(existing)
        db.flush()
        return

    if not plugin_key or not suite:
        raise ControlLibraryError(
            f"Control {control.ref} is executable but declares no "
            f"plugin_key/suite. An executable control must say what runs it."
        )

    procedure = db.scalar(
        select(TestProcedure).where(
            TestProcedure.control_id == control.id,
            TestProcedure.plugin_key == plugin_key,
        )
    )
    if procedure is None:
        procedure = TestProcedure(control_id=control.id, plugin_key=plugin_key)
        db.add(procedure)

    procedure.suite = suite
    procedure.config = spec.get("config") or {}
    procedure.evidence_contract = spec.get("evidence_contract") or {}

    # Any other procedure for this control is stale: the YAML declares one.
    for existing in list(control.procedures):
        if existing.plugin_key != plugin_key:
            db.execute(
                update(TestResult)
                .where(TestResult.procedure_id == existing.id)
                .values(procedure_id=None)
            )
            db.delete(existing)

    db.flush()


def load_control_library(db: Session, controls_dir: Path | None = None) -> dict[str, int]:
    """Load frameworks, clauses, controls and mappings. Idempotent."""
    directory = controls_dir or controls_directory()
    clause_index: dict[tuple[str, str], FrameworkClause] = {}
    control_specs: list[tuple[dict[str, Any], str]] = []

    for filename in FRAMEWORK_FILES:
        data = _load_yaml(directory / filename)
        framework = _upsert_framework(db, data["framework"])
        for clause_spec in data.get("clauses", []):
            clause = _upsert_clause(db, framework, clause_spec)
            clause_index[(framework.code, clause.ref)] = clause
        for control_spec in data.get("controls", []):
            control_specs.append((control_spec, filename))

    controls_loaded = 0
    for spec, source in control_specs:
        control = _upsert_control(db, spec, source)
        _sync_mappings(db, control, spec.get("clauses", []), clause_index)
        _sync_procedure(db, control, spec)
        controls_loaded += 1

    db.flush()
    return {
        "frameworks": len(FRAMEWORK_FILES),
        "clauses": len(clause_index),
        "controls": controls_loaded,
        "executable": sum(1 for s, _ in control_specs if s.get("is_executable")),
    }


def load_engagement_scope(
    db: Session, controls_dir: Path | None = None
) -> dict[str, int]:
    """Create the demo organisation, users and engagement, and scope controls."""
    directory = controls_dir or controls_directory()
    data = _load_yaml(directory / "meridian_scope.yaml")
    spec = data["engagement"]

    org = db.scalar(
        select(Organization).where(Organization.name == spec["organization"])
    )
    if org is None:
        org = Organization(name=spec["organization"])
        db.add(org)
    org.sector = "Financial services"
    org.city = "Bengaluru"
    org.headcount = 1800
    org.is_significant_data_fiduciary = True
    org.is_synthetic = True
    db.flush()

    for name, email, role in (
        ("Aarti Menon", "aarti.menon@example.test", "CONSULTANT"),
        ("Rohan Iyer", "rohan.iyer@example.test", "CLIENT"),
        ("Engagement Reviewer", "reviewer@example.test", "REVIEWER"),
    ):
        user = db.scalar(select(User).where(User.email == email))
        if user is None:
            db.add(
                User(
                    email=email, name=name, role=role, org_id=org.id, is_demo_actor=True
                )
            )
    db.flush()

    engagement = db.scalar(
        select(Engagement).where(
            Engagement.org_id == org.id, Engagement.name == spec["name"]
        )
    )
    if engagement is None:
        engagement = Engagement(org_id=org.id, name=spec["name"])
        db.add(engagement)
    engagement.scope_note = spec["scope_note"].strip()
    engagement.compliance_deadline = dt.date.fromisoformat(spec["compliance_deadline"])
    db.flush()

    owners: dict[str, str] = data.get("evidence_owners", {})
    exclusions = {
        item["control"]: item["na_reason"].strip()
        for item in data.get("out_of_scope", [])
    }

    unknown = set(exclusions) - {
        c.ref for c in db.scalars(select(Control)).all()
    }
    if unknown:
        raise ControlLibraryError(
            f"meridian_scope.yaml excludes controls that do not exist: {sorted(unknown)}"
        )

    excluded = 0
    for control in db.scalars(select(Control)).all():
        scoped = db.scalar(
            select(EngagementControl).where(
                EngagementControl.engagement_id == engagement.id,
                EngagementControl.control_id == control.id,
            )
        )
        if scoped is None:
            scoped = EngagementControl(
                engagement_id=engagement.id, control_id=control.id
            )
            db.add(scoped)

        na_reason = exclusions.get(control.ref)
        scoped.in_scope = na_reason is None
        scoped.na_reason = na_reason
        scoped.evidence_owner = owners.get(control.domain)
        if na_reason:
            excluded += 1

    db.flush()
    return {"engagement_id": engagement.id, "excluded": excluded}
