"use client";

import { Fragment } from "react";
import Link from "next/link";

import { SEVERITY_CLASS, type Finding } from "@/lib/api";
import { bandSeverity } from "@/lib/severity";

/**
 * The risk heatmap: a 5x5 likelihood x impact grid. [UX_BRIEF 4.1.B]
 *
 * Rows are likelihood (5 at top, descending); columns are impact (1 to 5,
 * ascending). One grid, 6 columns by 6 rows -- a label gutter plus the 25
 * cells plus a bottom label row -- so the axis numerals are guaranteed to
 * line up with their row and column: two separate grids sized independently
 * would not.
 *
 * Each cell's severity is FIXED by its position, the same banding the gate
 * applies to every finding, so the grid's colouring never changes; what
 * changes is which cells have findings plotted in them, shown as a count.
 * A cell is never itself a finding -- clicking one links to the register
 * filtered to that exact (likelihood, impact) pair, matching the API's own
 * filter contract. [engine/findings.py::band_severity]
 */
const LEVELS = [5, 4, 3, 2, 1] as const;
const IMPACT_COLS = [1, 2, 3, 4, 5] as const;

export function RiskHeatmap({ findings }: { findings: Finding[] }) {
  const counts = new Map<string, number>();
  for (const f of findings) {
    const key = `${f.likelihood}-${f.impact}`;
    counts.set(key, (counts.get(key) ?? 0) + 1);
  }

  return (
    <div className="flex flex-col gap-3">
      <div
        className="grid gap-1"
        style={{ gridTemplateColumns: "1.5rem repeat(5, minmax(0, 1fr))" }}
      >
        {LEVELS.map((likelihood) => (
          <Fragment key={likelihood}>
            <span className="label flex items-center justify-end pr-1">
              {likelihood}
            </span>
            {IMPACT_COLS.map((impact) => (
              <Cell
                key={`${likelihood}-${impact}`}
                likelihood={likelihood}
                impact={impact}
                count={counts.get(`${likelihood}-${impact}`) ?? 0}
              />
            ))}
          </Fragment>
        ))}
        <span aria-hidden="true" />
        {IMPACT_COLS.map((impact) => (
          <p key={`impact-${impact}`} className="label m-0 text-center">
            {impact}
          </p>
        ))}
      </div>

      <p className="label m-0 pl-6">Likelihood (rows) x impact (columns), 1 to 5</p>

      <ul className="m-0 flex flex-wrap gap-x-5 gap-y-2 p-0 text-meta text-ink-2">
        {(["CRITICAL", "HIGH", "MEDIUM", "LOW"] as const).map((severity) => (
          <li key={severity} className="flex list-none items-center gap-2">
            <span aria-hidden="true" className={`h-[10px] w-[10px] shrink-0 ${bgClassOf(severity)}`} />
            {LABEL[severity]}
          </li>
        ))}
      </ul>
    </div>
  );
}

const LABEL = { CRITICAL: "Critical", HIGH: "High", MEDIUM: "Medium", LOW: "Low" } as const;

function bgClassOf(severity: keyof typeof LABEL): string {
  return SEVERITY_CLASS[severity].split(" ").find((c) => c.startsWith("bg-")) ?? "";
}

function Cell({
  likelihood, impact, count,
}: {
  likelihood: number; impact: number; count: number;
}) {
  const severity = bandSeverity(likelihood * impact);
  const label = `Likelihood ${likelihood}, impact ${impact}, ${severity.toLowerCase()} risk band: ${count} finding${count === 1 ? "" : "s"}`;

  return (
    <Link
      href={count > 0 ? `/findings?likelihood=${likelihood}&impact=${impact}` : "#"}
      aria-disabled={count === 0}
      aria-label={label}
      title={label}
      className={[
        "flex aspect-square items-center justify-center border text-sm font-semibold no-underline",
        SEVERITY_CLASS[severity],
        count > 0
          ? "cursor-pointer hover:brightness-95 focus-visible:brightness-95"
          : "pointer-events-none opacity-40",
      ].join(" ")}
    >
      {count > 0 ? count : ""}
    </Link>
  );
}
