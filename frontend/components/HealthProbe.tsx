"use client";

import { useEffect, useState } from "react";

/**
 * Calls /api/health on first paint.
 *
 * Two jobs. It wakes a sleeping free-tier backend while the page already
 * shows content, so a cold link never presents only a spinner [TRD 1.4]. And
 * it proves, on the deployed skeleton, that frontend and backend actually
 * talk across origins — the Day 1 acceptance criterion.
 */

type Health = {
  status: string;
  engine_version: string;
  database: string;
};

type State =
  | { kind: "probing" }
  | { kind: "up"; health: Health }
  | { kind: "down"; reason: string };

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export function HealthProbe() {
  const [state, setState] = useState<State>({ kind: "probing" });

  useEffect(() => {
    let cancelled = false;

    fetch(`${API_BASE}/api/health`)
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json() as Promise<Health>;
      })
      .then((health) => {
        if (!cancelled) setState({ kind: "up", health });
      })
      .catch((e: unknown) => {
        if (!cancelled) {
          setState({
            kind: "down",
            reason: e instanceof Error ? e.message : "unreachable",
          });
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <section aria-live="polite" className="sheet flex flex-wrap items-center gap-x-7 gap-y-3 px-5 py-4">
      <h3 className="text-base font-semibold">Backend connectivity</h3>

      {state.kind === "probing" && (
        <div className="min-w-[12rem] flex-1">
          <p className="m-0 text-sm text-ink-2">Waking the API&hellip;</p>
          <div className="indeterminate-rule mt-2" />
        </div>
      )}

      {state.kind === "up" && (
        <dl className="m-0 flex flex-wrap gap-x-6 gap-y-2 text-sm">
          <Stat label="API" value={state.health.status} ok={state.health.status === "ok"} />
          <Stat label="Database" value={state.health.database} ok={state.health.database === "up"} />
          <Stat label="Engine" value={state.health.engine_version} />
        </dl>
      )}

      {state.kind === "down" && (
        <p className="m-0 text-sm text-ink-2">
          <span className="chip mr-2 bg-fail text-on-verdict">Unreachable</span>
          {state.reason}. The shell renders regardless; content never waits on a
          cold backend.
        </p>
      )}
    </section>
  );
}

/** A status pair. The square is real state (up or not), never decoration. */
function Stat({ label, value, ok }: { label: string; value: string; ok?: boolean }) {
  return (
    <div className="flex items-center gap-2">
      {ok !== undefined && (
        <span
          aria-hidden="true"
          className={`inline-block h-[10px] w-[10px] ${ok ? "bg-pass" : "bg-fail"}`}
        />
      )}
      <dt className="text-ink-3">{label}</dt>
      <dd className="m-0 font-mono font-semibold text-ink">{value}</dd>
    </div>
  );
}
