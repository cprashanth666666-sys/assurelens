/**
 * Suite 5 results, drawn as evidence rather than as a score. [Day 7]
 *
 * Fairness: one row per applicant group, the selection rate with its 95%
 * Wilson interval drawn to scale. A group too small to conclude from is
 * shown with its (very wide) interval and labelled as unassessed, in neutral
 * ink: it is never coloured or worded as a disparity.
 *
 * Drift: one row per input feature, PSI with its band, and the feature's
 * current distribution across the ten training deciles against the 10% line
 * each bin held at training time, so the drift is visible, not just a number.
 *
 * The detail JSON is untyped per procedure, so everything is narrowed before
 * use: one procedure changing shape must not crash every control page.
 */

type Group = {
  group: string;
  n: number;
  rate: number | null;
  ci_lower: number | null;
  ci_upper: number | null;
  status: string;
};

type Fairness = {
  groups: Group[];
  selection_rate_ratio: number | null;
  lowest_group: string | null;
  highest_group: string | null;
  demographic_parity_difference: number | null;
  equal_opportunity: { difference: number | null; basis: string };
  threshold: number;
  min_group_n: number;
  convention_note: string;
};

type Feature = {
  feature: string;
  psi: number | null;
  band: string;
  n: number;
  baseline_mean?: number;
  observed_mean?: number | null;
  bin_share?: (number | null)[];
};

type Drift = {
  features: Feature[];
  thresholds: { moderate: number; significant: number };
  baseline_captured_at: string | null;
  convention_note: string;
};

type Validation = {
  null_rates: { feature: string; null_rate: number | null; exceeds: boolean }[];
  duplicate_principals: number;
  out_of_range: string;
  max_null_rate: number;
  leakage_screen: {
    labelled_rows: number;
    correlations: { feature: string; correlation_with_outcome: number | null; suspected_leakage: boolean }[];
    suspected: string[];
    threshold: number;
    note: string;
  };
};

const isObj = (v: unknown): v is Record<string, unknown> => typeof v === "object" && v !== null;

export function fairnessOf(detail: Record<string, unknown>): Fairness | null {
  const f = detail.fairness;
  return isObj(f) && Array.isArray(f.groups) ? (f as unknown as Fairness) : null;
}

export function driftOf(detail: Record<string, unknown>): { drift: Drift; validation: Validation | null; exceptions: string[]; monitored: boolean } | null {
  const d = detail.drift;
  if (!isObj(d) || !Array.isArray(d.features)) return null;
  const v = detail.validation;
  return {
    drift: d as unknown as Drift,
    validation: isObj(v) && Array.isArray(v.null_rates) ? (v as unknown as Validation) : null,
    exceptions: Array.isArray(detail.exceptions) ? detail.exceptions.map(String) : [],
    monitored: detail.has_drift_monitoring === true,
  };
}

const pct = (v: number | null | undefined, d = 1) => (v == null ? "n/a" : `${(v * 100).toFixed(d)}%`);
const num = (v: number | null | undefined, d = 3) => (v == null ? "n/a" : v.toFixed(d));

// --- Fairness ------------------------------------------------------------------

export function FairnessView({ f }: { f: Fairness }) {
  const failing = f.selection_rate_ratio != null && f.selection_rate_ratio < f.threshold;
  const unassessed = f.groups.filter((g) => g.status !== "compared").map((g) => `group ${g.group} (n=${g.n})`);
  return (
    <section className="flex flex-col gap-4" aria-labelledby="fairness-h">
      <div>
        <h4 id="fairness-h" className="text-base font-semibold">Selection rate by applicant group</h4>
        <p className="m-0 mt-1 text-meta text-ink-3">Rule 13(3) due diligence / NIST AI RMF MEASURE 2.11</p>
      </div>

      <dl className="ruled m-0 grid-cols-2 sm:grid-cols-4">
        <Figure
          label="Lowest / highest"
          value={num(f.selection_rate_ratio, 2)}
          sub={f.lowest_group && f.highest_group ? `group ${f.lowest_group} / group ${f.highest_group}` : "fewer than two groups compared"}
          tone={failing ? "fail" : undefined}
        />
        <Figure label="Four-fifths line" value={num(f.threshold, 2)} sub="convention, see note" />
        <Figure label="Parity difference" value={pct(f.demographic_parity_difference)} sub="highest minus lowest rate" />
        <Figure label="Equal opportunity gap" value={pct(f.equal_opportunity.difference)} sub="among known good outcomes" />
      </dl>

      <div className="sheet">
        <div className="grid grid-cols-[3rem_minmax(0,1fr)] gap-x-4 border-b-2 border-rule-strong bg-inset px-4 py-2 text-meta font-semibold text-ink-2 sm:grid-cols-[4.5rem_5rem_minmax(0,1fr)_10rem]">
          <span>Group</span>
          <span className="hidden sm:block">Decisions</span>
          <span>Selection rate, 95% interval</span>
          <span className="hidden sm:block">Status</span>
        </div>
        <ul className="m-0 list-none p-0">
          {f.groups.map((g) => (
            <li key={g.group} className="grid grid-cols-[3rem_minmax(0,1fr)] items-center gap-x-4 gap-y-2 border-b border-rule px-4 py-3 last:border-b-0 sm:grid-cols-[4.5rem_5rem_minmax(0,1fr)_10rem]">
              <span className="font-mono text-sm font-semibold text-ink">{g.group}</span>
              <span className="hidden font-mono text-sm text-ink-2 sm:block">{g.n.toLocaleString()}</span>
              <RateBar g={g} threshold={f.highest_group ? rateOf(f, f.highest_group) * f.threshold : null} />
              {g.status === "compared" ? (
                <span className="col-start-2 text-meta font-medium text-ink-2 sm:col-start-auto">Compared</span>
              ) : (
                <span className="chip col-start-2 w-fit border border-dashed border-control text-na sm:col-start-auto" title={`Below the minimum group size of ${f.min_group_n}`}>
                  Too small to conclude
                </span>
              )}
            </li>
          ))}
        </ul>
      </div>

      <p className="m-0 text-sm text-ink-2">
        Groups under {f.min_group_n} decisions are left out of every comparison and
        reported as unassessed, never as a disparity: their interval is too wide to
        say anything.
        {unassessed.length > 0 && (
          <> Unassessed here: <span className="font-mono font-semibold">{unassessed.join(", ")}</span>.</>
        )}{" "}
        {f.equal_opportunity.basis}
      </p>
      <p className="m-0 border-l-4 border-rule pl-3 text-meta text-ink-3">{f.convention_note}</p>
    </section>
  );
}

function rateOf(f: Fairness, label: string): number {
  return f.groups.find((g) => g.group === label)?.rate ?? 0;
}

/** Rate and interval on a 0 to 100% scale, with the four-fifths line (80% of
 * the highest group's rate) marked so the reader can see who falls below it. */
function RateBar({ g, threshold }: { g: Group; threshold: number | null }) {
  const small = g.status !== "compared";
  const lo = (g.ci_lower ?? 0) * 100;
  const hi = (g.ci_upper ?? 0) * 100;
  return (
    <div className="min-w-0">
      <div
        className="relative h-[20px]"
        role="img"
        aria-label={`Group ${g.group}: ${pct(g.rate)} selected, 95% interval ${pct(g.ci_lower)} to ${pct(g.ci_upper)}${small ? ", too small to conclude" : ""}`}
      >
        <div className="absolute inset-x-0 top-[9px] h-[2px] bg-inset" />
        <div
          className={`absolute top-[6px] h-[8px] ${small ? "border border-dashed border-control bg-transparent" : "bg-cobalt"}`}
          style={{ left: `${lo}%`, width: `${Math.max(hi - lo, 0.8)}%` }}
        />
        {g.rate != null && (
          <div className="absolute top-[3px] h-[14px] w-[3px] -translate-x-1/2 bg-ink" style={{ left: `${g.rate * 100}%` }} />
        )}
        {threshold != null && (
          <div className="absolute inset-y-0 w-0 border-l-2 border-dotted border-fail" style={{ left: `${threshold * 100}%` }} title="Four-fifths of the highest group's rate" />
        )}
      </div>
      <p className="m-0 mt-1 font-mono text-xs text-ink-2">
        {pct(g.rate)} <span className="text-ink-3">[{pct(g.ci_lower)} to {pct(g.ci_upper)}]</span>
      </p>
    </div>
  );
}

// --- Drift ---------------------------------------------------------------------

const BAND_CLASS: Record<string, string> = {
  significant: "bg-fail text-on-verdict",
  moderate: "border border-rule-strong bg-sev-medium text-on-lime",
  stable: "border border-control text-ink-2",
};

export function DriftView({
  drift, validation, exceptions, monitored,
}: {
  drift: Drift; validation: Validation | null; exceptions: string[]; monitored: boolean;
}) {
  return (
    <section className="flex flex-col gap-4" aria-labelledby="drift-h">
      <div>
        <h4 id="drift-h" className="text-base font-semibold">Input drift against the training baseline</h4>
        <p className="m-0 mt-1 text-meta text-ink-3">
          Rule 13(3) due diligence / NIST AI RMF MEASURE 2.4
          {drift.baseline_captured_at && <> / baseline captured {drift.baseline_captured_at.slice(0, 10)}</>}
        </p>
      </div>

      {exceptions.length > 0 && (
        <ul className="m-0 flex list-none flex-col gap-2 p-0">
          {exceptions.map((e) => (
            <li key={e} className="border-l-4 border-fail bg-inset px-4 py-2 text-sm text-ink">{e}</li>
          ))}
        </ul>
      )}
      {!monitored && exceptions.length === 0 && (
        <p className="m-0 text-sm text-ink-2">No drift monitoring is recorded for this model.</p>
      )}

      <p className="m-0 text-sm text-ink-2">
        Bars show where today&rsquo;s inputs fall across the ten training deciles.
        At training each bin held 10% (the dashed line); a drifted feature piles
        into the outer bins.
      </p>
      <div className="sheet">
        <ul className="m-0 list-none p-0">
          {drift.features.map((f) => (
            <li key={f.feature} className="grid grid-cols-1 gap-3 border-b border-rule px-4 py-4 last:border-b-0 sm:grid-cols-[minmax(0,1fr)_14rem] sm:items-center">
              <div className="min-w-0">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-mono text-sm font-semibold text-ink">{f.feature}</span>
                  <span className={`chip ${BAND_CLASS[f.band] ?? "border border-dashed border-control text-na"}`}>
                    {f.band === "significant" ? "Significant drift" : f.band === "moderate" ? "Moderate drift" : f.band === "stable" ? "Stable" : f.band}
                  </span>
                </div>
                <p className="m-0 mt-1 font-mono text-xs text-ink-2">
                  PSI {num(f.psi)}
                  {f.baseline_mean != null && <> / mean {f.baseline_mean} at training, {num(f.observed_mean, 2)} now</>}
                </p>
              </div>
              {f.bin_share && <Deciles shares={f.bin_share} feature={f.feature} />}
            </li>
          ))}
        </ul>
      </div>
      <p className="m-0 border-l-4 border-rule pl-3 text-meta text-ink-3">{drift.convention_note}</p>

      {validation && <ValidationView v={validation} />}
    </section>
  );
}

/** Share of current inputs in each training decile. At training every bin
 * held 10% (the dashed line); a drifted feature piles into the top bins. */
function Deciles({ shares, feature }: { shares: (number | null)[]; feature: string }) {
  const max = Math.max(0.2, ...shares.map((s) => s ?? 0));
  const line = (0.1 / max) * 100;
  return (
    <figure className="m-0">
      <div
        className="relative flex h-[48px] items-end gap-[2px] border-b border-rule-strong"
        role="img"
        aria-label={`${feature}: share of current inputs per training decile, ${shares.map((s) => pct(s, 0)).join(", ")}`}
      >
        {shares.map((s, i) => (
          <div key={i} className="flex-1 bg-cobalt" style={{ height: `${((s ?? 0) / max) * 100}%` }} />
        ))}
        <div className="pointer-events-none absolute inset-x-0 border-t border-dashed border-ink" style={{ bottom: `${line}%` }} />
      </div>
      <figcaption className="mt-1 flex justify-between font-mono text-xs text-ink-3">
        <span>low</span><span>high</span>
      </figcaption>
    </figure>
  );
}

function ValidationView({ v }: { v: Validation }) {
  const overNull = v.null_rates.filter((x) => x.exceeds);
  return (
    <div className="flex flex-col gap-3">
      <h4 className="text-base font-semibold">Input validation</h4>
      <dl className="m-0 grid grid-cols-[auto_1fr] gap-x-4 gap-y-2 text-sm">
        <dt className="text-ink-3">Null rates</dt>
        <dd className="m-0 text-ink">
          {overNull.length === 0
            ? `All features under the ${pct(v.max_null_rate, 0)} limit.`
            : overNull.map((x) => `${x.feature} ${pct(x.null_rate)}`).join(", ")}
        </dd>
        <dt className="text-ink-3">Duplicates</dt>
        <dd className="m-0 text-ink">{v.duplicate_principals === 0 ? "No duplicate applicant records." : `${v.duplicate_principals} duplicate applicant records.`}</dd>
        <dt className="text-ink-3">Range</dt>
        <dd className="m-0 text-ink-2">{v.out_of_range}</dd>
        <dt className="text-ink-3">Leakage screen</dt>
        <dd className="m-0 text-ink">
          {v.leakage_screen.suspected.length === 0
            ? `No feature correlates with the outcome above ${v.leakage_screen.threshold} (${v.leakage_screen.labelled_rows.toLocaleString()} labelled decisions).`
            : <>Suspected, requires review: <span className="font-mono font-semibold">{v.leakage_screen.suspected.join(", ")}</span></>}
          <span className="mt-1 block font-mono text-xs text-ink-3">
            {v.leakage_screen.correlations.map((c) => `${c.feature} r=${num(c.correlation_with_outcome)}`).join("  /  ")}
          </span>
        </dd>
      </dl>
      <p className="m-0 border-l-4 border-rule pl-3 text-meta text-ink-3">{v.leakage_screen.note}</p>
    </div>
  );
}

function Figure({ label, value, sub, tone }: { label: string; value: string; sub: string; tone?: "fail" }) {
  return (
    <div className="px-4 py-3">
      <dt className="label">{label}</dt>
      <dd className={`m-0 mt-1 font-mono text-xl font-medium ${tone === "fail" ? "text-fail-text" : "text-ink"}`}>{value}</dd>
      <dd className="m-0 text-xs text-ink-3">{sub}</dd>
    </div>
  );
}
