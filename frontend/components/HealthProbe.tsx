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
    <section
      aria-live="polite"
      className="panel p-4 md:p-5"
    >
      <h3 className="text-2xs uppercase tracking-[0.14em] text-n-400">
        Backend connectivity
      </h3>

      {state.kind === "probing" && (
        <>
          <p className="mt-2 text-sm text-n-500">Waking the API&hellip;</p>
          <div className="indeterminate-rule mt-2" />
        </>
      )}

      {state.kind === "up" && (
        <dl className="mt-2 grid grid-cols-[auto_1fr] gap-x-6 gap-y-1 text-sm">
          <dt className="text-n-500">API</dt>
          <dd className="m-0 font-mono text-n-800">{state.health.status}</dd>
          <dt className="text-n-500">Database</dt>
          <dd className="m-0 font-mono text-n-800">{state.health.database}</dd>
          <dt className="text-n-500">Engine</dt>
          <dd className="m-0 font-mono text-n-800">
            {state.health.engine_version}
          </dd>
        </dl>
      )}

      {state.kind === "down" && (
        <p className="mt-2 text-sm text-n-600">
          API unreachable ({state.reason}). The shell renders regardless —
          content never waits on a cold backend.
        </p>
      )}
    </section>
  );
}
