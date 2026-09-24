"""FindingService: turns a FAIL into a tracked finding. [Day 8, TRD 1.3]

Called from the runner immediately after a result is persisted, exactly
once per (run, control) pair, and only for a clean `FAIL` -- never for
`INSUFFICIENT_EVIDENCE`. A gated control has nothing to raise a finding
about yet; the gate's own explanation already says what is missing. Raising
a "finding" from a result the product itself says is inconclusive would
undercut the whole argument for the gate's existence.

Two rules keep findings honest about where their numbers come from:

**Idempotent, not additive.** A control that fails again on a later run does
not spawn a second finding -- the existing open one is refreshed (new
origin result, new description, a history row for what changed) via the
partial unique index on (engagement_id, control_id) WHERE status is open.
A finding the consultant has closed or accepted stays closed; a fresh
failure after that reopens nothing automatically, because a status change a
human made is not something a re-run gets to overwrite silently.

**Likelihood and impact are computed, never invented, and both are printed
on screen with the rule that produced them** -- the same discipline the gate
applies to its own thresholds. Impact comes from a domain table (an
editorial judgement of the class of harm, stated as such). Likelihood comes
from the exception rate the procedure itself measured (1 - point_estimate),
banded; where a procedure reports no proportion, likelihood is held at 4
with an explicit note, not at a false-neutral midpoint.
"""

from __future__ import annotations

import re
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.control import Control, EngagementControl
from app.models.findings import Finding, FindingHistory
from app.models.results import TestResult

OPEN_STATUSES = ("OPEN", "IN_REMEDIATION", "RETEST_PENDING")

# Editorial judgement of the class of harm a domain's controls guard
# against, not a DPDP-stated weighting. Printed alongside every finding so
# it can be argued with, the same discipline the four-fifths and PSI
# conventions carry elsewhere in this engine.
DOMAIN_IMPACT: dict[str, int] = {
    "SECURITY_SAFEGUARDS": 5,       # direct unauthorised access to personal data
    "AI_GOVERNANCE": 5,             # automated decisions affecting rights, hardest to detect
    "RETENTION_ERASURE": 4,         # data held that should not exist
    "THIRD_PARTY_TRANSFER": 4,      # personal data exposed to a processor outside direct control
    "BREACH_RESPONSE": 4,           # failure here compounds every other harm
    "NOTICE_CONSENT": 3,            # autonomy harm, usually remediable without lasting exposure
    "PRINCIPAL_RIGHTS": 3,
    "GOVERNANCE_ACCOUNTABILITY": 2,  # a process gap, one step removed from direct harm
}
DEFAULT_IMPACT = 3
IMPACT_NOTE = (
    "Impact is a domain-based editorial judgement of the class of harm, not "
    "a DPDP-stated weighting."
)

# A starting effort estimate, in days, by severity -- a documented default
# the roadmap can compute against before anyone has scoped the actual fix,
# and every row it produces says so. Editable per finding once a consultant
# has a real estimate.
DEFAULT_EFFORT_DAYS: dict[str, float] = {
    "CRITICAL": 10.0, "HIGH": 5.0, "MEDIUM": 2.0, "LOW": 1.0,
}

NO_RATE_LIKELIHOOD = 4
NO_RATE_NOTE = (
    "No proportion is measured by this procedure; likelihood is held at "
    "4 (likely) because the finding concerns a continuously operating "
    "system rather than a single historical sample."
)


def band_severity(risk_score: int) -> str:
    """20-25 CRITICAL / 12-19 HIGH / 6-11 MEDIUM / 1-5 LOW. [SCHEMA 3.5]"""
    if risk_score >= 20:
        return "CRITICAL"
    if risk_score >= 12:
        return "HIGH"
    if risk_score >= 6:
        return "MEDIUM"
    return "LOW"


def _impact(control: Control) -> tuple[int, str]:
    value = DOMAIN_IMPACT.get(control.domain, DEFAULT_IMPACT)
    return value, IMPACT_NOTE


def _likelihood(result: TestResult) -> tuple[int, str | None]:
    """1-5, from the measured exception rate where one exists."""
    if result.point_estimate is not None:
        exception_rate = 1 - float(result.point_estimate)
        if exception_rate >= 0.75:
            return 5, None
        if exception_rate >= 0.50:
            return 4, None
        if exception_rate >= 0.25:
            return 3, None
        if exception_rate >= 0.05:
            return 2, None
        return 1, None
    return NO_RATE_LIKELIHOOD, NO_RATE_NOTE


def _describe(control: Control, result: TestResult) -> str:
    """One sentence, from the numbers the procedure actually measured.

    Two shapes are recognised by structure, the same way the frontend's
    evidence viewer narrows `detail` -- not by suite name, so a procedure
    the author does not yet know about still falls through to the generic,
    always-available path rather than producing no description at all.
    """
    detail = result.detail or {}

    fairness = detail.get("fairness")
    if isinstance(fairness, dict) and fairness.get("groups"):
        ratio = fairness.get("selection_rate_ratio")
        lowest, highest = fairness.get("lowest_group"), fairness.get("highest_group")
        threshold = fairness.get("threshold")
        if ratio is not None and lowest and highest:
            return (
                f"The selection-rate ratio is {ratio} (group {lowest} against "
                f"group {highest}), below the {threshold} four-fifths line."
            )

    exceptions = detail.get("exceptions")
    if isinstance(exceptions, list) and exceptions:
        # Either a list of ready-made sentences (drift), or a list of
        # structured exception dicts carrying their own "finding" sentence
        # (consent's withdrawal-parity check) -- never the dict's own repr.
        sentences: list[str] = []
        for item in exceptions[:3]:
            if isinstance(item, str):
                sentences.append(item)
            elif isinstance(item, dict) and isinstance(item.get("finding"), str):
                sentences.append(item["finding"])
        if len(sentences) == len(exceptions[:3]):
            return " ".join(
                s if s.endswith((".", "!", "?")) else f"{s}." for s in sentences
            )

    if result.successes is not None and result.sample_size:
        exception_count = result.sample_size - result.successes
        population_note = ""
        if (
            result.population_size
            and result.population_size != result.sample_size
            and result.coverage_pct is not None
        ):
            population_note = (
                f" ({float(result.coverage_pct):.1f}% of the "
                f"{result.population_size:,}-item population)"
            )
        return (
            f"{exception_count:,} of {result.sample_size:,} tested show the "
            f"exception{population_note}."
        )

    return control.objective


_REF_PATTERN = re.compile(r"^F-(\d+)$")


def _next_ref(db: Session) -> str:
    """`F-001`, `F-002`, ... Read-modify-write against a single-engagement
    demo database; no concurrent writers exist in this deployment."""
    refs = db.scalars(select(Finding.ref)).all()
    highest = 0
    for ref in refs:
        match = _REF_PATTERN.match(ref)
        if match:
            highest = max(highest, int(match.group(1)))
    return f"F-{highest + 1:03d}"


def _log(
    db: Session, finding: Finding, field: str, old: Any, new: Any, actor_id: int | None = None
) -> None:
    if old == new:
        return
    db.add(FindingHistory(
        finding_id=finding.id, actor_id=actor_id, field=field,
        old_value=None if old is None else str(old),
        new_value=None if new is None else str(new),
    ))


def raise_from_result(db: Session, control: Control, result: TestResult) -> Finding:
    """Create or refresh the finding for this (engagement, control).

    Only called for a plain FAIL (the runner's own condition, mirroring
    TRD 1.3): `if verdict == FAIL and control.auto_raise: FindingService`.
    """
    run = result.run
    engagement_id = run.engagement_id

    impact, impact_note = _impact(control)
    likelihood, likelihood_note = _likelihood(result)
    severity = band_severity(likelihood * impact)
    description = _describe(control, result)
    notes = [n for n in (impact_note, likelihood_note) if n]
    if notes:
        description = f"{description} {' '.join(notes)}"

    existing = db.scalar(
        select(Finding).where(
            Finding.engagement_id == engagement_id,
            Finding.control_id == control.id,
            Finding.status.in_(OPEN_STATUSES),
        )
    )

    if existing is not None:
        _log(db, existing, "description", existing.description, description)
        _log(db, existing, "likelihood", existing.likelihood, likelihood)
        _log(db, existing, "impact", existing.impact, impact)
        _log(db, existing, "origin_result_id", existing.origin_result_id, result.id)
        existing.description = description
        existing.likelihood = likelihood
        existing.impact = impact
        existing.severity = severity
        existing.origin_result_id = result.id
        db.flush()
        return existing

    engagement_control = db.get(EngagementControl, (engagement_id, control.id))
    owner = engagement_control.evidence_owner if engagement_control else None

    finding = Finding(
        ref=_next_ref(db),
        engagement_id=engagement_id,
        control_id=control.id,
        origin_result_id=result.id,
        title=control.title,
        description=description,
        likelihood=likelihood,
        impact=impact,
        severity=severity,
        owner=owner,
        effort_days=DEFAULT_EFFORT_DAYS[severity],
        status="OPEN",
    )
    db.add(finding)
    db.flush()
    return finding
