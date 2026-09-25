"use client";

import { CaretDownIcon, XIcon } from "@phosphor-icons/react";
import { useEffect, useMemo, useState } from "react";

import {
  DOMAINS,
  DOMAIN_LABEL,
  FINDING_STATUSES,
  FINDING_STATUS_LABEL,
  SEVERITIES,
  SEVERITY_CLASS,
  SEVERITY_LABEL,
  fetchFinding,
  updateFinding,
  type Domain,
  type Finding,
  type FindingDetail,
  type FindingStatus,
  type Severity,
} from "@/lib/api";
import { useRole } from "./RoleProvider";

/**
 * The findings register. [UX_BRIEF 4.5]
 *
 * Findings raised by tests that ran; none are seeded (`FindingService`,
 * `engine/findings.py`, only ever calls `raise_from_result` from the runner
 * on a FAIL verdict). Severity is a left border plus a text label, never
 * colour alone, on every row and in the filter chips.
 *
 * A likelihood/impact pair arriving in the URL (a heatmap cell click) is
 * read once on mount as a standing filter, shown as its own removable chip
 * rather than folded into the severity filter -- a cell and a severity band
 * are not the same question, even though severity is derived from them.
 */
export function FindingsRegister({
  findings,
  initialLikelihood,
  initialImpact,
}: {
  findings: Finding[];
  initialLikelihood?: number;
  initialImpact?: number;
}) {
  const role = useRole();
  const [rows, setRows] = useState(findings);
  const [domain, setDomain] = useState<Domain | "all">("all");
  const [severity, setSeverity] = useState<Severity | "all">("all");
  const [status, setStatus] = useState<FindingStatus | "all">("all");
  const [cell, setCell] = useState<{ likelihood: number; impact: number } | null>(
    initialLikelihood !== undefined && initialImpact !== undefined
      ? { likelihood: initialLikelihood, impact: initialImpact }
      : null,
  );
  const [expanded, setExpanded] = useState<Set<string>>(new Set());

  const filtered = useMemo(() => {
    return rows.filter((f) => {
      // Internal reviewer notes -- a finding drafted for the file, not yet
      // meant for the client -- are hidden from the client view entirely,
      // not just read-only. [PRD 4.4: "internal reviewer notes hidden"]
      if (role === "client" && f.is_internal_note_only) return false;
      if (domain !== "all" && f.domain !== domain) return false;
      if (severity !== "all" && f.severity !== severity) return false;
      if (status !== "all" && f.status !== status) return false;
      if (cell && (f.likelihood !== cell.likelihood || f.impact !== cell.impact)) return false;
      return true;
    });
  }, [rows, domain, severity, status, cell, role]);

  const anyFilter = domain !== "all" || severity !== "all" || status !== "all" || cell !== null;
  const visibleTotal = role === "client"
    ? rows.filter((f) => !f.is_internal_note_only).length
    : rows.length;

  function toggle(ref: string) {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(ref)) next.delete(ref);
      else next.add(ref);
      return next;
    });
  }

  function onSaved(updated: FindingDetail) {
    setRows((prev) => prev.map((f) => (f.ref === updated.ref ? updated : f)));
  }

  return (
    <div className="flex flex-col gap-5">
      <div className="flex flex-col gap-4 xl:flex-row xl:items-end xl:justify-between">
        <FilterGroup label="Domain">
          <Chip on={domain === "all"} onClick={() => setDomain("all")}>All</Chip>
          {DOMAINS.map((d) => (
            <Chip key={d} on={domain === d} onClick={() => setDomain(d)}>{DOMAIN_LABEL[d]}</Chip>
          ))}
        </FilterGroup>
        <FilterGroup label="Severity">
          <Chip on={severity === "all"} onClick={() => setSeverity("all")}>All</Chip>
          {SEVERITIES.map((s) => (
            <Chip key={s} on={severity === s} onClick={() => setSeverity(s)}>{SEVERITY_LABEL[s]}</Chip>
          ))}
        </FilterGroup>
        <FilterGroup label="Status">
          <Chip on={status === "all"} onClick={() => setStatus("all")}>All</Chip>
          {FINDING_STATUSES.map((s) => (
            <Chip key={s} on={status === s} onClick={() => setStatus(s)}>{FINDING_STATUS_LABEL[s]}</Chip>
          ))}
        </FilterGroup>
      </div>

      <p className="m-0 flex flex-wrap items-center gap-3 text-sm text-ink-2" aria-live="polite">
        <span>
          Showing <strong className="font-mono text-ink">{filtered.length}</strong> of{" "}
          <span className="font-mono">{visibleTotal}</span> findings
        </span>
        {cell && (
          <button
            type="button"
            className="chip inline-flex items-center gap-1 border border-control font-semibold"
            onClick={() => setCell(null)}
          >
            Likelihood {cell.likelihood} × impact {cell.impact}
            <XIcon size={12} weight="bold" aria-hidden />
          </button>
        )}
        {anyFilter && (
          <button
            type="button"
            className="link inline-flex items-center gap-1 font-semibold"
            onClick={() => { setDomain("all"); setSeverity("all"); setStatus("all"); setCell(null); }}
          >
            <XIcon size={14} weight="bold" aria-hidden />
            Clear filters
          </button>
        )}
      </p>

      {filtered.length === 0 ? (
        <div className="border-2 border-dashed border-control bg-surface px-5 py-7">
          <p className="m-0 text-lg font-semibold text-ink">No finding matches.</p>
          <p className="m-0 mt-2 text-base text-ink-2">
            Nothing in the register fits these filters. Clear them to see all {visibleTotal}.
          </p>
        </div>
      ) : (
        <div className="sheet">
          <div className="scroll-x">
            <table className="data-table min-w-[64rem]">
              <thead>
                <tr>
                  <th scope="col" className="w-24">ID</th>
                  <th scope="col">Finding</th>
                  <th scope="col" className="w-40">Control</th>
                  <th scope="col" className="w-32">Severity</th>
                  <th scope="col" className="w-20">L × I</th>
                  <th scope="col" className="w-44">Owner</th>
                  <th scope="col" className="w-36">Status</th>
                  <th scope="col" aria-label="Expand" className="w-10" />
                </tr>
              </thead>
              <tbody>
                {filtered.map((f) => (
                  <Row
                    key={f.ref}
                    finding={f}
                    open={expanded.has(f.ref)}
                    onToggle={() => toggle(f.ref)}
                    onSaved={onSaved}
                  />
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

const SEVERITY_BORDER: Record<Severity, string> = {
  CRITICAL: "var(--sev-critical)",
  HIGH: "var(--sev-high)",
  MEDIUM: "var(--sev-medium)",
  LOW: "var(--sev-low)",
};

function Row({
  finding, open, onToggle, onSaved,
}: {
  finding: Finding;
  open: boolean;
  onToggle: () => void;
  onSaved: (updated: FindingDetail) => void;
}) {
  return (
    <>
      <tr
        className="row-interactive cursor-pointer"
        style={{ boxShadow: `inset 3px 0 0 0 ${SEVERITY_BORDER[finding.severity]}` }}
        onClick={onToggle}
        aria-expanded={open}
      >
        <td>
          <span className="whitespace-nowrap font-mono font-semibold text-ink">{finding.ref}</span>
        </td>
        <td>
          <span className="font-medium text-ink">{finding.title}</span>
        </td>
        <td className="text-ink-2">
          <span className="font-mono text-sm">{finding.control_ref}</span>
        </td>
        <td>
          <span className={`chip ${SEVERITY_CLASS[finding.severity]}`}>
            {SEVERITY_LABEL[finding.severity]}
          </span>
        </td>
        <td className="font-mono text-sm text-ink-2">
          {finding.likelihood} × {finding.impact}
        </td>
        <td className="text-ink-2">{finding.owner ?? <span className="text-ink-3">Unassigned</span>}</td>
        <td>
          <span className="text-sm text-ink-2">{FINDING_STATUS_LABEL[finding.status]}</span>
        </td>
        <td>
          <CaretDownIcon
            size={16}
            weight="bold"
            aria-hidden
            className={`transition-transform ${open ? "rotate-180" : ""}`}
          />
        </td>
      </tr>
      {open && (
        <tr>
          <td colSpan={8} className="bg-inset">
            <ExpandedFinding finding={finding} onSaved={onSaved} />
          </td>
        </tr>
      )}
    </>
  );
}

function ExpandedFinding({
  finding, onSaved,
}: {
  finding: Finding;
  onSaved: (updated: FindingDetail) => void;
}) {
  const role = useRole();
  const [detail, setDetail] = useState<FindingDetail | null | "loading">("loading");
  const [status, setStatus] = useState<FindingStatus>(finding.status);
  const [owner, setOwner] = useState(finding.owner ?? "");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(false);

  useEffect(() => {
    let cancelled = false;
    fetchFinding(finding.ref).then((d) => { if (!cancelled) setDetail(d); });
    return () => { cancelled = true; };
  }, [finding.ref]);

  async function save() {
    setSaving(true);
    setError(false);
    const updated = await updateFinding(finding.ref, {
      status,
      owner: owner.trim() === "" ? null : owner.trim(),
    });
    setSaving(false);
    if (updated === null) {
      setError(true);
      return;
    }
    setDetail(updated);
    onSaved(updated);
  }

  return (
    <div className="flex flex-col gap-5 px-5 py-5 md:px-6">
      <div className="grid gap-5 md:grid-cols-2">
        <Field label="Evidence / description">
          <p className="m-0 text-sm leading-prose text-ink-2">{finding.description}</p>
        </Field>
        {finding.root_cause && (
          <Field label="Root cause">
            <p className="m-0 text-sm leading-prose text-ink-2">{finding.root_cause}</p>
          </Field>
        )}
        {finding.recommendation && (
          <Field label="Recommendation">
            <p className="m-0 text-sm leading-prose text-ink-2">{finding.recommendation}</p>
          </Field>
        )}
        <Field label="Effort">
          <p className="m-0 font-mono text-sm text-ink-2">
            {finding.effort_days !== null ? `${finding.effort_days} days` : "Not estimated"}
          </p>
        </Field>
      </div>

      {role === "consultant" ? (
        <div className="flex flex-wrap items-end gap-4 border-t border-rule pt-4">
          <label className="flex flex-col gap-1 text-sm">
            <span className="label">Status</span>
            <select
              value={status}
              onChange={(e) => setStatus(e.target.value as FindingStatus)}
              className="field"
            >
              {FINDING_STATUSES.map((s) => (
                <option key={s} value={s}>{FINDING_STATUS_LABEL[s]}</option>
              ))}
            </select>
          </label>
          <label className="flex flex-col gap-1 text-sm">
            <span className="label">Owner</span>
            <input
              type="text"
              value={owner}
              onChange={(e) => setOwner(e.target.value)}
              placeholder="Unassigned"
              className="field"
            />
          </label>
          <button type="button" onClick={save} disabled={saving} className="btn btn-secondary">
            {saving ? "Saving…" : "Save"}
          </button>
          {error && <p className="m-0 text-sm text-fail-text">Could not save. Try again.</p>}
        </div>
      ) : (
        // Read-only for the client: same fields, no form. [PRD 4.4]
        <div className="flex flex-wrap gap-6 border-t border-rule pt-4">
          <Field label="Status">
            <p className="m-0 text-sm text-ink">{FINDING_STATUS_LABEL[finding.status]}</p>
          </Field>
          <Field label="Owner">
            <p className="m-0 text-sm text-ink">{finding.owner ?? "Unassigned"}</p>
          </Field>
        </div>
      )}

      <div className="border-t border-rule pt-4">
        <p className="label m-0 mb-2">History</p>
        {detail === "loading" && <p className="m-0 text-sm text-ink-3">Loading…</p>}
        {detail === null && <p className="m-0 text-sm text-ink-3">History unavailable.</p>}
        {detail && detail !== "loading" && (
          detail.history.length === 0 ? (
            <p className="m-0 text-sm text-ink-3">No changes recorded since this finding was raised.</p>
          ) : (
            <ul className="m-0 flex flex-col gap-1 p-0 text-sm text-ink-2">
              {detail.history.map((h, i) => (
                <li key={i} className="list-none font-mono text-xs">
                  {new Date(h.changed_at).toLocaleString()} — {h.field}: {h.old_value ?? "—"} → {h.new_value ?? "—"}
                </li>
              ))}
            </ul>
          )
        )}
      </div>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-1">
      <p className="label m-0">{label}</p>
      {children}
    </div>
  );
}

function FilterGroup({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div role="group" aria-label={label} className="min-w-0">
      <p className="label m-0">{label}</p>
      <div className="scroll-x edge-fade mt-2 flex flex-nowrap gap-2 pb-1 md:flex-wrap">{children}</div>
    </div>
  );
}

function Chip({ on, onClick, children }: { on: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button type="button" aria-pressed={on} data-selected={on ? "true" : "false"} onClick={onClick} className="toggle">
      {children}
    </button>
  );
}
