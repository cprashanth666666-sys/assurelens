"""The DOCX workpaper. [PRD 7.1]

One section per control tested in a run, in the audit format Aarti expects:
procedure, population and sample, evidence, result, exception, recommendation.
Front matter states scope, methodology and limitations -- not buried in an
appendix. Nothing here reads `datetime.now()`: every date on the page comes
from the run itself, so the same run ID renders the same bytes twice.
"""

from __future__ import annotations

import io
from decimal import Decimal

from docx import Document
from docx.document import Document as DocumentT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.control import Control, Engagement, EngagementControl
from app.models.findings import Finding
from app.models.results import TestResult, TestRun
from app.reporting._docx import MUTED, apply_base_styles, to_utc

NOT_LEGAL_ADVICE = (
    "This document is a working paper prepared by AssureLens, a demonstration "
    "instrument. It is not legal advice. Clause mappings are the author's "
    "reading of the Digital Personal Data Protection Rules, 2025 and should be "
    "confirmed by a qualified adviser before reliance."
)

LIMITATIONS = [
    "Synthetic data. The estate tested here is generated. It demonstrates "
    "that the procedures work; it says nothing about any real organisation.",
    "Not legal advice. Clause mappings are the author's reading of the "
    "Rules. A qualified adviser should confirm scope before reliance.",
    "Rules not fully in force. Rules 3, 5-16, 22 and 23 commence 13 May "
    "2027. Controls are written against the notified text; interpretation "
    "will develop before commencement.",
    "Partial control coverage. Roughly 25 controls are authored; the "
    "remainder are documented with evidence contracts and render as "
    "Insufficient Evidence under gate G4, the honest state for a control "
    "that has not been tested.",
    "Single fictional entity. Control weighting is tuned for a BFSI global "
    "capability centre and would need rework for another sector.",
]

VERDICT_LABEL = {
    "PASS": "Pass",
    "FAIL": "Fail",
    "INSUFFICIENT_EVIDENCE": "Insufficient Evidence",
    "NOT_APPLICABLE": "Not Applicable",
}

def build_workpaper(db: Session, run_id: int) -> bytes:
    run = db.get(TestRun, run_id, options=[selectinload(TestRun.results)])
    if run is None:
        raise ValueError(f"No run with id {run_id}")

    engagement = db.get(
        Engagement, run.engagement_id, options=[selectinload(Engagement.organization)]
    )
    if engagement is None:
        raise ValueError(f"No engagement with id {run.engagement_id}")

    all_controls = sorted(
        db.scalars(
            select(Control).options(selectinload(Control.mappings))
        ).all(),
        key=lambda c: c.ref,
    )
    # One lookup, built once, used both to sort and to render each result's
    # section -- not a fresh query per result for a value already in hand.
    controls_by_id = {c.id: c for c in all_controls}

    results = sorted(
        db.scalars(
            select(TestResult)
            .where(TestResult.run_id == run_id)
            .options(
                selectinload(TestResult.evidence),
                selectinload(TestResult.run),
            )
        ).all(),
        key=lambda r: controls_by_id[r.control_id].ref if r.control_id in controls_by_id else "",
    )

    scope = {
        row.control_id: row
        for row in db.scalars(
            select(EngagementControl).where(
                EngagementControl.engagement_id == engagement.id
            )
        ).all()
    }
    findings_by_result = {
        f.origin_result_id: f
        for f in db.scalars(
            select(Finding).where(
                Finding.engagement_id == engagement.id,
                Finding.origin_result_id.is_not(None),
            )
        ).all()
    }

    doc = Document()
    _set_core_properties(doc, run)
    apply_base_styles(doc, {1: 20, 2: 14, 3: 11.5})

    _front_matter(doc, engagement, run)
    doc.add_page_break()  # type: ignore[no-untyped-call]

    for result in results:
        control = controls_by_id[result.control_id]
        _control_section(
            doc, control, result, scope.get(result.control_id),
            findings_by_result.get(result.id), run,
        )

    doc.add_page_break()  # type: ignore[no-untyped-call]
    _appendix_control_library(doc, all_controls, scope)
    _appendix_threshold_register(doc, all_controls, results)

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def _set_core_properties(doc: DocumentT, run: TestRun) -> None:
    props = doc.core_properties
    props.title = f"AssureLens Workpaper — Run {run.id}"
    props.author = "AssureLens"
    props.comments = f"Generated from run {run.id}, seed {run.seed}."
    # Derived from the run, never from the clock the export happens to run
    # on -- the same run ID renders the same bytes on any machine, any day.
    props.created = to_utc(run.started_at)
    props.modified = to_utc(run.completed_at or run.started_at)
    props.revision = 1


def _front_matter(doc: DocumentT, engagement: Engagement, run: TestRun) -> None:
    doc.add_heading("Assurance Workpaper", level=1)
    doc.add_paragraph(engagement.name)

    p = doc.add_paragraph()
    p.add_run(engagement.organization.name).bold = True
    if engagement.organization.city:
        p.add_run(f" · {engagement.organization.city}")

    meta = doc.add_paragraph()
    meta.add_run(
        f"Run {run.id} · Seed {run.seed} · Suites: {', '.join(run.suites)} · "
        f"Prepared {run.started_at:%d %B %Y}"
    ).italic = True

    doc.add_heading("Scope", level=2)
    doc.add_paragraph(
        engagement.scope_note
        or "Scope not recorded on this engagement."
    )

    doc.add_heading("Basis of preparation", level=2)
    doc.add_paragraph(
        "This workpaper covers every control tested in the run named above. "
        "Each section records the procedure performed, the population and "
        "sample it drew from, the evidence obtained, and the result the "
        "evidence supports. Where the evidence could not carry a "
        "conclusion, the result says so and states what would resolve it, "
        "rather than reporting a conclusion the sample cannot support."
    )

    doc.add_heading("Methodology", level=2)
    doc.add_paragraph(
        "Procedures execute against a live target service on a recorded "
        "seed. Proportions are reported with a 95% Wilson score interval, "
        "which is stable at the extremes where a normal approximation is "
        "not. A control's evidence must clear the Sufficiency Gate — "
        "minimum sample size, confidence interval width, population "
        "coverage, evidence freshness and representativeness — before a "
        "Pass or Fail is reported; a control that does not clear the gate "
        "is reported as Insufficient Evidence, a peer verdict, not a "
        "lesser one."
    )

    doc.add_heading("Limitations", level=2)
    for item in LIMITATIONS:
        doc.add_paragraph(item, style="List Bullet")

    note = doc.add_paragraph()
    note.add_run(NOT_LEGAL_ADVICE).italic = True


def _control_section(
    doc: DocumentT,
    control: Control,
    result: TestResult,
    scoped: EngagementControl | None,
    finding: Finding | None,
    run: TestRun,
) -> None:
    doc.add_heading(f"{control.ref} — {control.title}", level=2)

    doc.add_paragraph(control.objective)

    primary = control.primary_mapping
    clause_p = doc.add_paragraph()
    if primary is not None:
        clause_p.add_run(
            f"{primary.clause.framework.code} {primary.clause.ref}"
        ).bold = True
        if primary.clause.verbatim_text:
            quote = doc.add_paragraph(f"“{primary.clause.verbatim_text}”")
            quote.paragraph_format.left_indent = Pt(18)
            for run_ in quote.runs:
                run_.italic = True
        others = [m for m in control.mappings if not m.is_primary]
        if others:
            doc.add_paragraph(
                "Also maps to: "
                + ", ".join(f"{m.clause.framework.code} {m.clause.ref}" for m in others)
            )
    else:
        clause_p.add_run("No verified clause basis on record.").italic = True

    if result.verdict == "NOT_APPLICABLE":
        # Scoped out of the engagement -- the procedure never ran, so
        # nothing below this point would be true of it. Say why and stop,
        # rather than describing a procedure and a sample that don't exist
        # for this control. [scope.na_reason is required by the schema
        # whenever a control is out of scope]
        out_of_scope = doc.add_paragraph()
        out_of_scope.add_run("Out of scope: ").bold = True
        out_of_scope.add_run(
            scoped.na_reason if scoped is not None and scoped.na_reason
            else "No reason recorded."
        )
        footer = doc.add_paragraph()
        footer_run = footer.add_run(
            f"Prepared by AssureLens engine · {run.started_at:%d %b %Y} · "
            f"Run {run.id} · Seed {run.seed}"
        )
        footer_run.italic = True
        footer_run.font.size = Pt(8.5)
        footer_run.font.color.rgb = MUTED
        return

    doc.add_heading("Procedure performed", level=3)
    doc.add_paragraph(control.procedure_text)

    doc.add_heading("Population and sample", level=3)
    doc.add_paragraph(_population_line(control, result))

    doc.add_heading("Evidence obtained", level=3)
    if result.evidence:
        for item in result.evidence:
            doc.add_paragraph(
                f"{item.label} ({item.kind}) — collected {item.collected_at:%d %b %Y %H:%M UTC}, "
                f"SHA-256 {item.content_hash[:16]}…",
                style="List Bullet",
            )
    else:
        doc.add_paragraph("No evidence items were recorded for this result.")

    doc.add_heading("Result", level=3)
    result_p = doc.add_paragraph()
    result_p.add_run(VERDICT_LABEL.get(result.verdict, result.verdict)).bold = True
    estimate, lower, upper = result.point_estimate, result.ci_lower, result.ci_upper
    if estimate is not None and lower is not None and upper is not None:
        doc.add_paragraph(
            f"Point estimate {_pct(estimate)}, "
            f"95% Wilson interval {_pct(lower)} to {_pct(upper)}."
        )
    if result.gate_fired:
        for why, resolve in zip(result.gate_explanations, result.gate_remedies, strict=False):
            g = doc.add_paragraph()
            g.add_run("Why. ").bold = True
            g.add_run(why)
            if resolve:
                r = doc.add_paragraph()
                r.add_run("Resolve. ").bold = True
                r.add_run(resolve)

    doc.add_heading("Exception / finding", level=3)
    if finding is not None:
        doc.add_paragraph(finding.description)
        if finding.root_cause:
            rc = doc.add_paragraph()
            rc.add_run("Root cause. ").bold = True
            rc.add_run(finding.root_cause)
    else:
        doc.add_paragraph("No exception was raised from this result.")

    doc.add_heading("Recommendation", level=3)
    doc.add_paragraph(
        finding.recommendation if finding is not None and finding.recommendation
        else "No recommendation recorded."
    )

    footer = doc.add_paragraph()
    footer.alignment = WD_ALIGN_PARAGRAPH.LEFT
    footer_run = footer.add_run(
        f"Prepared by AssureLens engine · {run.started_at:%d %b %Y} · "
        f"Run {run.id} · Seed {run.seed}"
    )
    footer_run.italic = True
    footer_run.font.size = Pt(8.5)
    footer_run.font.color.rgb = MUTED


def _population_line(control: Control, result: TestResult) -> str:
    n = result.sample_size
    big_n = result.population_size
    coverage = result.coverage_pct
    method = (
        "full population examined (census)" if control.inference_mode == "CENSUS"
        else "sampled from the declared population"
    )
    if n is None:
        return f"No sample was drawn. Selection method: {method}."
    parts = [f"n = {n:,}"]
    if big_n is not None:
        parts.append(f"N = {big_n:,}")
    if coverage is not None:
        parts.append(f"{coverage}% coverage")
    parts.append(f"selection method: {method}")
    return ", ".join(parts) + "."


def _pct(value: Decimal) -> str:
    return f"{float(value) * 100:.1f}%"


def _appendix_control_library(
    doc: DocumentT, controls: list[Control], scope: dict[int, EngagementControl]
) -> None:
    doc.add_heading("Appendix A — Control library", level=2)
    table = doc.add_table(rows=1, cols=5)
    table.style = "Light Grid Accent 1"
    header = table.rows[0].cells
    columns = ("Ref", "Title", "Domain", "Legal basis", "Executable")
    for cell, text in zip(header, columns, strict=True):
        cell.text = text
        for p in cell.paragraphs:
            for r in p.runs:
                r.bold = True

    for control in controls:
        scoped = scope.get(control.id)
        primary = control.primary_mapping
        row = table.add_row().cells
        row[0].text = control.ref
        row[1].text = control.title
        row[2].text = control.domain.replace("_", " ").title()
        row[3].text = (
            f"{primary.clause.framework.code} {primary.clause.ref}" if primary else "—"
        )
        row[4].text = (
            "No — out of scope" if scoped is not None and not scoped.in_scope
            else "Yes" if control.is_executable
            else "No — documented"
        )


def _appendix_threshold_register(
    doc: DocumentT, controls: list[Control], results: list[TestResult]
) -> None:
    doc.add_heading("Appendix B — Threshold register", level=2)

    overrides_by_control = {c.ref: c.threshold_overrides for c in controls if c.threshold_overrides}
    run_overrides = {
        r.id: r.threshold_overrides for r in results if r.threshold_overrides
    }

    if not overrides_by_control and not run_overrides:
        doc.add_paragraph(
            "No control-level or run-level threshold overrides are on record. "
            "Every result in this workpaper applied the engine's default "
            "thresholds."
        )
        return

    doc.add_paragraph(
        "Quietly loosening a threshold to turn a gate into a pass is exactly "
        "the behaviour this feature exists to prevent, so every override is "
        "listed here."
    )
    table = doc.add_table(rows=1, cols=3)
    table.style = "Light Grid Accent 1"
    header = table.rows[0].cells
    for cell, text in zip(header, ("Control", "Overridden thresholds", "Level"), strict=True):
        cell.text = text
        for p in cell.paragraphs:
            for r in p.runs:
                r.bold = True

    for ref, overrides in sorted(overrides_by_control.items()):
        row = table.add_row().cells
        row[0].text = ref
        row[1].text = ", ".join(f"{k}={v}" for k, v in overrides.items())
        row[2].text = "Control definition"

    control_by_id = {c.id: c.ref for c in controls}
    for result in results:
        if not result.threshold_overrides:
            continue
        row = table.add_row().cells
        row[0].text = control_by_id.get(result.control_id, str(result.control_id))
        row[1].text = ", ".join(f"{k}={v}" for k, v in result.threshold_overrides.items())
        row[2].text = f"Run {result.run_id}"
