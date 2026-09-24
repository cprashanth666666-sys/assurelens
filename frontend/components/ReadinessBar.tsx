import type { Domain, DomainReadiness } from "@/lib/api";
import { DOMAIN_LABEL } from "@/lib/api";

/**
 * Readiness by domain: a horizontal segmented bar per domain, Pass / Fail /
 * Insufficient evidence / Not yet measured / Not applicable, with coverage
 * printed BESIDE the bar, never inside it or averaged into one number.
 * [UX_BRIEF 4.1.A, PRD 7.3]
 *
 * "Not yet measured" is a fifth, real segment the brief's four-way split
 * does not name: a documented control has no test procedure at all, so the
 * runner never creates a result for it, and an executable control a run has
 * not yet reached is in the same state. Reporting either as "insufficient
 * evidence" would be exactly the fabrication this product refuses
 * everywhere else -- a gate reason nobody computed. [backend readiness
 * endpoint, controls.py]
 *
 * Segments reuse the product's own verdict fills (never a chart-specific
 * palette): colour follows the same state everywhere it appears, and every
 * segment carries a count, so nothing here depends on colour alone.
 */

type Segment = {
  key: string;
  count: number;
  label: string;
  className: string;
};

export function ReadinessByDomain({ rows }: { rows: DomainReadiness[] }) {
  return (
    <div className="flex flex-col gap-1">
      <Legend />
      <ul className="m-0 flex list-none flex-col gap-px bg-rule-strong p-0">
        {rows.map((row) => (
          <li key={row.domain}>
            <DomainRow row={row} />
          </li>
        ))}
      </ul>
    </div>
  );
}

function segmentsOf(row: DomainReadiness): Segment[] {
  return [
    { key: "pass", count: row.pass_, label: "Pass", className: "bg-pass" },
    { key: "fail", count: row.fail, label: "Fail", className: "bg-fail" },
    {
      key: "insufficient",
      count: row.insufficient_evidence,
      label: "Insufficient evidence",
      className: "bg-insufficient",
    },
    {
      key: "not_measured",
      count: row.not_measured,
      label: "Not yet measured",
      className: "bg-inset bg-[repeating-linear-gradient(135deg,var(--control)_0,var(--control)_1px,transparent_1px,transparent_6px)] opacity-70",
    },
    {
      key: "na",
      count: row.not_applicable,
      label: "Not applicable",
      className: "border-x border-dashed border-control bg-surface",
    },
  ].filter((s) => s.count > 0);
}

function DomainRow({ row }: { row: DomainReadiness }) {
  const segments = segmentsOf(row);
  const total = row.total || 1;

  return (
    <div className="grid grid-cols-1 gap-2 bg-surface p-4 sm:grid-cols-[10rem_minmax(0,1fr)_9rem] sm:items-center sm:gap-4">
      <p className="m-0 text-sm font-medium text-ink">
        {DOMAIN_LABEL[row.domain as Domain] ?? row.domain}
      </p>

      <div
        className="flex h-[22px] w-full divide-x divide-surface overflow-hidden border border-rule-strong"
        role="img"
        aria-label={
          `${DOMAIN_LABEL[row.domain as Domain] ?? row.domain}: ` +
          segments.map((s) => `${s.count} ${s.label.toLowerCase()}`).join(", ") +
          ` of ${row.total} controls.`
        }
      >
        {segments.map((s) => (
          <span
            key={s.key}
            className={`${s.className} h-full`}
            style={{ width: `${(s.count / total) * 100}%` }}
            title={`${s.label}: ${s.count}`}
          />
        ))}
      </div>

      <p className="m-0 text-right font-mono text-sm text-ink-2 sm:text-left">
        <span className="font-semibold text-ink">{row.coverage_pct.toFixed(0)}%</span>{" "}
        tested
        <span className="ml-2 text-ink-3">({row.total})</span>
      </p>
    </div>
  );
}

const LEGEND: { label: string; swatch: string }[] = [
  { label: "Pass", swatch: "bg-pass" },
  { label: "Fail", swatch: "bg-fail" },
  { label: "Insufficient evidence", swatch: "bg-insufficient" },
  {
    label: "Not yet measured",
    swatch: "bg-inset bg-[repeating-linear-gradient(135deg,var(--control)_0,var(--control)_1px,transparent_1px,transparent_6px)]",
  },
  { label: "Not applicable", swatch: "border border-dashed border-control bg-surface" },
];

function Legend() {
  return (
    <ul className="m-0 flex flex-wrap gap-x-5 gap-y-2 p-0 text-meta text-ink-2">
      {LEGEND.map((item) => (
        <li key={item.label} className="flex list-none items-center gap-2">
          <span aria-hidden="true" className={`h-[10px] w-[10px] shrink-0 ${item.swatch}`} />
          {item.label}
        </li>
      ))}
    </ul>
  );
}
