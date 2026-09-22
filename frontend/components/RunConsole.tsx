"use client";

import { useState } from "react";

import {
  fetchRun,
  startRun,
  type ResultSummary,
  type RunDetail,
  type SuiteCatalogue,
} from "@/lib/api";
import { VerdictBadge } from "./VerdictBadge";

/**
 * The run console.
 *
 * The one screen permitted motion, and only functional motion: a 1px
 * indeterminate rule while a run is in flight. No spinners, no pulsing
 * skeletons, no progress celebration. A gated verdict lands as calmly as a
 * pass, because that restraint is the argument. [UX 4.4]
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

  return (
    <div className="flex flex-col gap-5">
      <section className="border border-n-200 bg-n-0 p-4">
        <h3 className="text-2xs uppercase tracking-[0.14em] text-n-400">
          Run
        </h3>

        <div className="mt-3 flex flex-wrap items-end gap-6">
          <fieldset className="border-0 p-0">
            <legend className="text-2xs uppercase tracking-[0.14em] text-n-400">
              Suites
            </legend>
            <div className="mt-2 flex flex-wrap gap-4">
              {suites.length === 0 && (
                <span className="text-sm text-n-500">
                  No suites registered.
                </span>
              )}
              {suites.map((suite) => (
                <label key={suite} className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={selected.includes(suite)}
                    onChange={() => toggle(suite)}
                  />
                  <span className="font-mono text-xs">{suite}</span>
                </label>
              ))}
            </div>
          </fieldset>

          <div>
            <label
              htmlFor="seed"
              className="block text-2xs uppercase tracking-[0.14em] text-n-400"
            >
              Seed
            </label>
            <input
              id="seed"
              value={seed}
              onChange={(e) => setSeed(e.target.value)}
              inputMode="numeric"
              className="mt-2 w-24 rounded-sm border border-n-200 bg-n-0 px-2 py-1 font-mono text-sm"
            />
          </div>

          <button
            type="button"
            onClick={execute}
            disabled={running || selected.length === 0}
            className="rounded-sm border border-accent-600 bg-accent-600 px-4 py-1.5 text-sm font-semibold text-n-0 disabled:border-n-200 disabled:bg-n-100 disabled:text-n-400"
          >
            {running ? "Running" : "Run"}
          </button>
        </div>

        <p className="m-0 mt-3 text-xs text-n-500">
          The seed is recorded on the run and printed in the workpaper. A
          result nobody can regenerate is an assertion, not a finding.
        </p>

        {running && <div className="indeterminate-rule mt-3" />}
        {error && <p className="m-0 mt-3 text-sm text-n-600">{error}</p>}
      </section>

      {run && <Results run={run} />}
    </div>
  );
}

function Results({ run }: { run: RunDetail }) {
  const counts = run.results.reduce<Record<string, number>>((acc, r) => {
    acc[r.verdict] = (acc[r.verdict] ?? 0) + 1;
    return acc;
  }, {});

  return (
    <section className="border border-n-200 bg-n-0">
      <header className="flex flex-wrap items-baseline justify-between gap-3 border-b border-n-200 px-4 py-3">
        <h3 className="text-2xs uppercase tracking-[0.14em] text-n-400">
          Run {run.id} &middot; {run.status.toLowerCase()}
        </h3>
        <p className="m-0 font-mono text-2xs text-n-500">
          seed {run.seed} &middot; {run.result_count} results &middot;{" "}
          {Object.entries(counts)
            .map(([v, n]) => `${n} ${v.toLowerCase().replace(/_/g, " ")}`)
            .join(" · ")}
        </p>
      </header>

      <div className="scroll-x">
        <table className="w-full border-collapse text-xs leading-table">
          <thead>
            <tr className="border-b border-n-200 bg-n-50 text-left">
              <Th className="w-32">Ref</Th>
              <Th>Control</Th>
              <Th className="w-44">Verdict</Th>
              <Th className="w-28">Sample</Th>
              <Th className="w-40">95% interval</Th>
            </tr>
          </thead>
          <tbody>
            {run.results.map((result, i) => (
              <ResultRow key={result.id} result={result} zebra={i % 2 === 1} />
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function ResultRow({
  result,
  zebra,
}: {
  result: ResultSummary;
  zebra: boolean;
}) {
  const gated = result.verdict === "INSUFFICIENT_EVIDENCE";

  return (
    <>
      <tr
        className={`border-b border-n-100 align-top ${zebra ? "bg-n-25" : ""}`}
      >
        <Td>
          <span className="whitespace-nowrap font-mono text-accent-600">
            {result.control_ref}
          </span>
        </Td>
        <Td className="text-n-800">{result.control_title}</Td>
        <Td>
          <VerdictBadge
            verdict={result.verdict}
            gateReasons={result.gate_reasons}
          />
          {result.gate_fired && result.raw_outcome && (
            <div className="mt-1 text-2xs text-n-500">
              measured {result.raw_outcome.toLowerCase()}
            </div>
          )}
        </Td>
        <Td className="font-mono text-n-600">
          {result.sample_size === null
            ? "—"
            : `${result.sample_size.toLocaleString()}${
                result.population_size
                  ? ` / ${result.population_size.toLocaleString()}`
                  : ""
              }`}
          {result.coverage_pct !== null && (
            <div className="text-2xs text-n-500">
              {result.coverage_pct.toFixed(2)}% coverage
            </div>
          )}
        </Td>
        <Td className="font-mono text-n-600">
          {result.ci_lower === null || result.ci_upper === null
            ? "—"
            : `${result.ci_lower.toFixed(3)} – ${result.ci_upper.toFixed(3)}`}
        </Td>
      </tr>

      {gated && (
        <tr className={`border-b border-n-100 ${zebra ? "bg-n-25" : ""}`}>
          <td />
          <td colSpan={4} className="px-3 pb-3">
            {/* Why, what would resolve it, in that order. A gate that cannot
                say how to clear it is an excuse. [UX 6.2] */}
            {result.gate_explanations.map((why, i) => (
              <div key={why} className="mb-2 max-w-prose">
                <p className="m-0 text-xs text-n-700">{why}</p>
                {result.gate_remedies[i] && (
                  <p className="m-0 mt-1 text-xs text-n-500">
                    <span className="uppercase tracking-[0.14em] text-n-400">
                      Resolve
                    </span>{" "}
                    {result.gate_remedies[i]}
                  </p>
                )}
              </div>
            ))}
          </td>
        </tr>
      )}
    </>
  );
}

function Th({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <th
      scope="col"
      className={`px-3 py-2 text-2xs font-semibold uppercase tracking-[0.14em] text-n-500 ${className}`}
    >
      {children}
    </th>
  );
}

function Td({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return <td className={`px-3 py-2 ${className}`}>{children}</td>;
}
