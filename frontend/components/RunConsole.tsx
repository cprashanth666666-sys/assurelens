"use client";

import { useState } from "react";

import {
  fetchRun,
  startRun,
  type ResultSummary,
  type RunDetail,
  type SuiteCatalogue,
  type Verdict,
} from "@/lib/api";
import { VerdictBadge } from "./VerdictBadge";

/**
 * The run console.
 *
 * The screen with the strongest claim on motion, and the strictest limit on
 * what kind. Everything that moves here reports state:
 *
 * * the indeterminate rule, while a run is in flight;
 * * the result rows, which arrive in a 30ms stagger so the eye reads them as
 *   a sequence of findings rather than a block that blinked into place;
 * * the gate explanation, which expands from the row it belongs to.
 *
 * What is still banned: spinners (v5 removed the Run button's), pulsing
 * skeletons, animated counters, and any celebration of a pass. A gated verdict must
 * land as calmly as a pass, because that restraint IS the argument. If
 * PASS got a flourish and INSUFFICIENT_EVIDENCE did not, the interface
 * would be quietly telling the reader which answer it prefers. [UX 4.4]
 */
export function RunConsole({
  engagementId,
  catalogue,
  initialRun,
}: {
  engagementId: number;
  catalogue: SuiteCatalogue | null;
  initialRun: RunDetail | null;
}) {
  const suites = catalogue?.suites ?? [];
  const [selected, setSelected] = useState<string[]>(suites);
  const [seed, setSeed] = useState("42");
  const [running, setRunning] = useState(false);
  const [run, setRun] = useState<RunDetail | null>(initialRun);
  const [error, setError] = useState<string | null>(null);

  async function execute() {
    setRunning(true);
    setError(null);

    const started = await startRun(engagementId, selected, Number(seed) || 42);
    if (started === null) {
      setError("The run could not be started. The API may be waking.");
      setRunning(false);
      return;
    }

    setRun(await fetchRun(started.id));
    setRunning(false);
  }

  function toggle(suite: string) {
    setSelected((current) =>
      current.includes(suite)
        ? current.filter((s) => s !== suite)
        : [...current, suite],
    );
  }

  const count = selected.length;

  return (
    <div className="flex flex-col gap-6">
      <section className="sheet p-5 md:p-6" aria-labelledby="run-heading">
        <h3 id="run-heading">Configure a run</h3>

        <div className="mt-5 flex flex-col gap-5 lg:flex-row lg:items-end">
          <fieldset className="m-0 min-w-0 flex-1 border-0 p-0">
            <legend className="label">Suites</legend>
            <div className="mt-2 flex flex-wrap gap-2">
              {suites.length === 0 && (
                <span className="text-sm text-ink-2">No suites registered.</span>
              )}
              {suites.map((suite) => {
                const on = selected.includes(suite);
                return (
                  <label key={suite} data-selected={on ? "true" : "false"} className="toggle">
                    <input
                      type="checkbox"
                      checked={on}
                      onChange={() => toggle(suite)}
                      className="sr-only"
                    />
                    {/* Drawn, so the whole 44px block is the target rather
                        than a 13px native box. [a11y touch-target-size] */}
                    <svg viewBox="0 0 14 14" width="14" height="14" aria-hidden="true" className="shrink-0">
                      <rect
                        x="0.75"
                        y="0.75"
                        width="12.5"
                        height="12.5"
                        fill={on ? "var(--lime)" : "transparent"}
                        stroke={on ? "var(--lime)" : "currentColor"}
                        strokeWidth="1.5"
                      />
                      <path
                        d="M3.5 7.2 6 9.6l4.5-5.2"
                        fill="none"
                        stroke="var(--on-lime)"
                        strokeWidth="1.8"
                        strokeLinecap="square"
                        style={{ opacity: on ? 1 : 0 }}
                      />
                    </svg>
                    <span className="font-mono">{suite}</span>
                  </label>
                );
              })}
            </div>
          </fieldset>

          <div className="flex items-end gap-3">
            <div>
              <label htmlFor="seed" className="label block">
                Seed
              </label>
              <input
                id="seed"
                value={seed}
                onChange={(e) => setSeed(e.target.value)}
                inputMode="numeric"
                className="field mt-2 w-24 font-mono"
              />
            </div>

            <button
              type="button"
              onClick={execute}
              disabled={running || count === 0}
              className="btn btn-primary min-w-[10rem]"
            >
              {running
                ? "Running"
                : count === 0
                  ? "Select a suite"
                  : `Run ${count} suite${count === 1 ? "" : "s"}`}
            </button>
          </div>
        </div>

        <p className="m-0 mt-4 max-w-prose text-sm text-ink-2">
          The seed is recorded on the run and printed in the workpaper. A result
          nobody can regenerate is an assertion, not a finding.
        </p>

        {running && <div className="indeterminate-rule mt-4" />}

        {error && (
          <p role="alert" className="m-0 mt-4 border-l-4 border-fail bg-inset px-4 py-3 text-sm text-ink">
            {error}
          </p>
        )}
      </section>

      {run && <Results run={run} />}
    </div>
  );
}

const VERDICT_ORDER: Verdict[] = ["PASS", "FAIL", "INSUFFICIENT_EVIDENCE", "NOT_APPLICABLE"];

function Results({ run }: { run: RunDetail }) {
  const counts = run.results.reduce<Partial<Record<Verdict, number>>>((acc, r) => {
    acc[r.verdict] = (acc[r.verdict] ?? 0) + 1;
    return acc;
  }, {});

  return (
    <section className="sheet" aria-labelledby="results-heading">
      <header className="flex flex-wrap items-center justify-between gap-4 bg-band px-5 py-4 text-on-band">
        <div>
          <h3 id="results-heading" className="text-on-band">
            Run {run.id}{" "}
            <span className="font-normal text-on-band-2">{run.status.toLowerCase()}</span>
          </h3>
          <p className="m-0 mt-1 font-mono text-meta text-on-band-2">
            seed {run.seed} / {run.result_count} results
          </p>
        </div>
        {/* Counts per verdict, side by side at equal weight. No total score,
            and no verdict is summed into another. */}
        <ul className="m-0 flex list-none flex-wrap gap-2 p-0">
          {VERDICT_ORDER.filter((v) => counts[v]).map((v) => (
            <li key={v} className="flex items-center gap-2 bg-surface px-2 py-1">
              <VerdictBadge verdict={v} />
              <span className="font-mono text-sm font-semibold text-ink">{counts[v]}</span>
            </li>
          ))}
        </ul>
      </header>

      <div className="scroll-x">
        <table className="data-table min-w-[46rem]">
          <thead>
            <tr>
              <th scope="col" className="w-32">Ref</th>
              <th scope="col">Control</th>
              <th scope="col" className="w-48">Verdict</th>
              <th scope="col" className="w-32">Sample</th>
              <th scope="col" className="w-40">95% interval</th>
            </tr>
          </thead>
          <tbody>
            {run.results.map((result) => (
              <ResultRow key={result.id} result={result} />
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function ResultRow({ result }: { result: ResultSummary }) {
  const gated = result.verdict === "INSUFFICIENT_EVIDENCE";

  return (
    <>
      <tr className="row-interactive">
        <td>
          <span className="whitespace-nowrap font-mono font-semibold text-link">
            {result.control_ref}
          </span>
        </td>
        <td className="font-medium text-ink">{result.control_title}</td>
        <td>
          <VerdictBadge verdict={result.verdict} gateReasons={result.gate_reasons} />
          {result.gate_fired && result.raw_outcome && (
            <div className="mt-1 text-meta text-ink-3">
              measured {result.raw_outcome.toLowerCase()}
            </div>
          )}
        </td>
        <td className="font-mono text-ink">
          {result.sample_size === null
            ? "n/a"
            : `${result.sample_size.toLocaleString()}${
                result.population_size ? ` / ${result.population_size.toLocaleString()}` : ""
              }`}
          {result.coverage_pct !== null && (
            <div className="text-meta text-ink-3">{result.coverage_pct.toFixed(2)}% coverage</div>
          )}
        </td>
        <td className="font-mono text-ink">
          {result.ci_lower === null || result.ci_upper === null
            ? "n/a"
            : `${result.ci_lower.toFixed(3)} to ${result.ci_upper.toFixed(3)}`}
        </td>
      </tr>

      {gated && (
        <tr>
          <td className="bg-inset" />
          <td colSpan={4} className="bg-inset">
            {/* Why, then what would resolve it. A gate that cannot say how
                to clear it is an excuse. [UX 6.2] */}
            <div className="flex flex-col gap-3">
              {result.gate_explanations.map((why, i) => (
                <div key={why} className="max-w-prose border-l-4 border-insufficient pl-3">
                  <p className="m-0 text-sm text-ink">
                    <span className="font-semibold">Why.</span> {why}
                  </p>
                  {result.gate_remedies[i] && (
                    <p className="m-0 mt-1 text-sm text-ink-2">
                      <span className="font-semibold text-ink">Resolve.</span>{" "}
                      {result.gate_remedies[i]}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </td>
        </tr>
      )}
    </>
  );
}
