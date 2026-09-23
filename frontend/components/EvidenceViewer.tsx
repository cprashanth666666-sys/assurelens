import Link from "next/link";

import type { ControlResult, EvidenceOut, LatestResult } from "@/lib/api";
import { VerdictBadge } from "./VerdictBadge";

/**
 * What the latest run found for this control, and what it stood on.
 *
 * Three things, in the order an assessor asks for them:
 *
 * 1. **The verdict**, with why it gated and what would resolve it.
 * 2. **The finding** -- the procedure's own record of its exceptions, in
 *    monospace, because it is evidence and should read as evidence, not as
 *    UI copy that has been paraphrased on the way to the screen.
 * 3. **The evidence ledger** -- each item collected, with the SHA-256 that
 *    pins exactly what was read. The payload itself is not stored; the hash
 *    is what lets anyone prove later that a finding rests on the bytes it
 *    claims to.
 *
 * Server-rendered, with native <details> for expansion. Nothing here needs
 * client JavaScript. [UX 4.3]
 */
export function EvidenceViewer({ latest }: { latest: LatestResult }) {
  if (latest.kind === "unreachable") {
    return (
      <p className="m-0 text-sm text-n-600">
        The API could not be reached, so the latest result is unknown. That is
        different from the control never having run, and is reported as such.
      </p>
    );
  }

  if (latest.kind === "never-run") {
    return (
      <p className="m-0 text-sm text-n-600">
        No run has tested this control yet. Start one from{" "}
        <Link href="/runs" className="link-grow text-accent-600 no-underline">
          Test Runs
        </Link>
        .
      </p>
    );
  }

  const r = latest.result;
  const ranked = rankedProcessors(r.detail);
  // The runner stamps population_source on every result, including one that
  // never executed. On its own it is bookkeeping, not a finding, and showing
  // "Full finding record" over a single null would imply there was one.
  const substantive = Object.keys(r.detail).some((k) => k !== "population_source");

  return (
    <div className="flex flex-col gap-4">
      <Header result={r} />

      {r.gate_fired && (
        <div className="flex flex-col gap-2">
          {r.gate_explanations.map((why, i) => (
            <div key={why} className="border-l-2 border-n-200 pl-3">
              <p className="m-0 text-xs text-n-700">{why}</p>
              {r.gate_remedies[i] && (
                <p className="m-0 mt-1 text-xs text-n-500">
                  <span className="uppercase tracking-[0.14em] text-n-400">
                    Resolve
                  </span>{" "}
                  {r.gate_remedies[i]}
                </p>
              )}
            </div>
          ))}
        </div>
      )}

      {ranked && <RankedProcessors rows={ranked} />}

      {substantive && (
        <details className="group">
          <summary className="cursor-pointer text-2xs uppercase tracking-[0.14em] text-n-500 transition-colors duration-base ease-out hover:text-n-800">
            Full finding record
          </summary>
          <MonoBlock label="Finding record" value={r.detail} />
        </details>
      )}

      <Ledger items={r.evidence} />
    </div>
  );
}

function Header({ result }: { result: ControlResult }) {
  return (
    <div className="flex flex-wrap items-baseline justify-between gap-2">
      <VerdictBadge verdict={result.verdict} gateReasons={result.gate_reasons} />
      <p className="m-0 font-mono text-2xs text-n-500">
        run {result.run_id} &middot; seed {result.seed}
        {result.completed_at && <> &middot; {result.completed_at.slice(0, 10)}</>}
      </p>
    </div>
  );
}

// --- Ranked processors (DPDP-TP-01) ----------------------------------------

type RankedRow = {
  processor: string;
  status: string;
  issues: { check: string; detail: string }[];
};

/** Narrow the untyped detail to the ranked list, or nothing. The detail is
 *  per-procedure JSON; trusting its shape without checking would turn one
 *  procedure's change into a crash on every control page. */
function rankedProcessors(detail: Record<string, unknown>): RankedRow[] | null {
  const ranked = detail.ranked;
  if (!Array.isArray(ranked)) return null;
  const rows = ranked.filter(
    (row): row is RankedRow =>
      typeof row === "object" &&
      row !== null &&
      typeof (row as RankedRow).processor === "string" &&
      Array.isArray((row as RankedRow).issues),
  );
  return rows.length > 0 ? rows : null;
}

const CHECK_LABEL: Record<string, string> = {
  access_after_offboarding: "Access after offboarding",
  no_processor_agreement: "No processor agreement",
  stale_credential: "Stale credential",
  excess_scope: "Excess scope",
  credential_not_rotated: "Not rotated",
};

function RankedProcessors({ rows }: { rows: RankedRow[] }) {
  return (
    <div>
      <h4 className="text-2xs font-semibold uppercase tracking-[0.14em] text-n-500">
        Processors, worst first
      </h4>
      <ol className="m-0 mt-2 flex list-none flex-col gap-2 p-0">
        {rows.map((row) => (
          <li
            key={row.processor}
            className="border-b border-n-100 pb-2 text-xs last:border-b-0"
          >
            <div className="flex flex-wrap items-baseline justify-between gap-2">
              <span className="text-n-800">{row.processor}</span>
              <span className="font-mono text-2xs text-n-500">
                {row.issues.length === 0
                  ? row.status === "offboarded"
                    ? "offboarded"
                    : "no issues"
                  : `${row.issues.length} issue${row.issues.length === 1 ? "" : "s"}`}
              </span>
            </div>
            {row.issues.length > 0 && (
              <ul className="m-0 mt-1 list-none p-0">
                {row.issues.map((issue) => (
                  <li key={issue.check} className="mt-1 text-n-600">
                    <span className="font-semibold text-verdict-fail">
                      {CHECK_LABEL[issue.check] ?? issue.check}
                    </span>{" "}
                    &mdash; {issue.detail}
                  </li>
                ))}
              </ul>
            )}
          </li>
        ))}
      </ol>
    </div>
  );
}

// --- Evidence ledger --------------------------------------------------------

function Ledger({ items }: { items: EvidenceOut[] }) {
  if (items.length === 0) {
    return (
      <p className="m-0 text-xs text-n-500">
        No evidence was collected for this result.
      </p>
    );
  }

  return (
    <div>
      <h4 className="text-2xs font-semibold uppercase tracking-[0.14em] text-n-500">
        Evidence collected
      </h4>
      <ul className="m-0 mt-2 flex list-none flex-col gap-3 p-0">
        {items.map((item) => (
          <li key={item.label} className="text-xs">
            <div className="flex flex-wrap items-baseline justify-between gap-2">
              <span className="font-mono text-n-800">{item.label}</span>
              <span className="font-mono text-2xs text-n-400">
                {item.kind.toLowerCase().replace(/_/g, " ")}
              </span>
            </div>
            <p
              className="m-0 mt-1 break-all font-mono text-2xs text-n-500"
              title={item.content_hash}
            >
              sha256 {item.content_hash.slice(0, 16)}&hellip;
              {item.content_hash.slice(-8)}
            </p>
            {item.summary != null && (
              <details className="mt-1">
                <summary className="cursor-pointer text-2xs text-n-500 transition-colors duration-base ease-out hover:text-n-800">
                  Summary
                </summary>
                <MonoBlock label={`${item.label} summary`} value={item.summary} />
              </details>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}

/**
 * Evidence in monospace, in its own scroll box. The only element on the page
 * permitted to be wider than its column. [UX 8]
 *
 * Focusable so a keyboard user can scroll it; a scroll region you can only
 * reach with a mouse is a region some readers cannot read. [a11y]
 */
function MonoBlock({ label, value }: { label: string; value: unknown }) {
  return (
    <pre
      tabIndex={0}
      aria-label={label}
      className="scroll-x m-0 mt-2 max-h-[22rem] overflow-y-auto rounded-md border border-n-200 bg-n-50 p-3 font-mono text-2xs leading-table text-n-700"
    >
      {JSON.stringify(value, null, 2)}
    </pre>
  );
}
