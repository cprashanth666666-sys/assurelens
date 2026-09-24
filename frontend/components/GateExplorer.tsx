"use client";

import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import { useId, useState } from "react";

import { VERDICT_LABEL } from "@/lib/api";
import { GATE, evaluateGate } from "@/lib/wilson";
import { VerdictBadge } from "./VerdictBadge";

/**
 * The evidence gate, made touchable.
 *
 * The reader sets how many items were tested, how many failed, and how big
 * the population is. The 95% Wilson interval moves with a spring and the
 * verdict changes the moment the gate opens or closes. Every verdict gets the
 * same cross-fade: Pass is not rewarded with more motion than Insufficient
 * evidence. [UX_BRIEF 14.5]
 *
 * The interval bar animates transform only (x and scaleX of a full-width
 * element), so dragging a slider never triggers layout.
 */

const PRESETS = [
  { label: "Too few items", n: 12, ex: 0, pop: 2400 },
  { label: "Clean, well covered", n: 400, ex: 4, pop: 2400 },
  { label: "Borderline", n: 240, ex: 6, pop: 2400 },
  { label: "Clearly failing", n: 240, ex: 30, pop: 2400 },
] as const;

export function GateExplorer() {
  const [n, setN] = useState(48);
  const [ex, setEx] = useState(1);
  const [pop, setPop] = useState(2400);
  const reduce = useReducedMotion();
  const r = evaluateGate(n, ex, pop);
  const spring = reduce ? { duration: 0 } : { type: "spring" as const, stiffness: 260, damping: 30 };

  return (
    <div className="ruled lg:grid-cols-[minmax(0,5fr)_minmax(0,7fr)]">
      {/* Inputs */}
      <div className="flex flex-col gap-6 p-5 md:p-7">
        <Slider label="Items tested (n)" value={n} min={1} max={800} onChange={(v) => { setN(v); if (ex > v) setEx(v); if (pop < v) setPop(Math.ceil(v / 100) * 100); }} />
        <Slider label="Exceptions found" value={ex} min={0} max={Math.min(n, 80)} onChange={setEx} />
        <Slider label="Population (N)" value={pop} min={100} max={24000} step={100} onChange={(v) => setPop(Math.max(v, n))} />

        <div>
          <p className="label m-0">Try a scenario</p>
          <div className="mt-2 flex flex-wrap gap-2">
            {PRESETS.map((p) => {
              const active = p.n === n && p.ex === ex && p.pop === pop;
              return (
                <button
                  key={p.label}
                  type="button"
                  data-selected={active ? "true" : "false"}
                  className="toggle"
                  onClick={() => { setN(p.n); setEx(p.ex); setPop(p.pop); }}
                >
                  {p.label}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Result */}
      <div className="flex min-w-0 flex-col gap-5 p-5 md:p-7" aria-live="polite">
        <div className="flex min-h-[32px] flex-wrap items-center gap-3">
          <AnimatePresence mode="wait" initial={false}>
            <motion.span
              key={r.verdict}
              initial={reduce ? false : { opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              exit={reduce ? undefined : { opacity: 0, y: -6 }}
              transition={{ duration: 0.16 }}
              className="inline-flex"
            >
              <VerdictBadge verdict={r.verdict} />
            </motion.span>
          </AnimatePresence>
          <span className="sr-only">Verdict: {VERDICT_LABEL[r.verdict]}.</span>
          {r.reasons.filter((x) => x.code !== "STRADDLE").length > 0 && (
            <span className="font-mono text-sm font-medium text-ink-2">
              {r.reasons.filter((x) => x.code !== "STRADDLE").map((x) => x.code).join(" ")}
            </span>
          )}
        </div>

        <IntervalBar lower={r.lower} upper={r.upper} rate={r.rate} spring={spring} />

        <dl className="m-0 grid grid-cols-2 gap-x-6 gap-y-3 font-mono text-sm sm:grid-cols-4">
          <Stat label="Pass rate" value={r.rate.toFixed(3)} />
          <Stat label="95% interval" value={`${r.lower.toFixed(3)} to ${r.upper.toFixed(3)}`} wide />
          <Stat label="Coverage" value={`${r.coveragePct.toFixed(1)}%`} />
        </dl>

        <ul className="m-0 flex list-none flex-col gap-2 p-0">
          <AnimatePresence initial={false}>
            {r.reasons.map((reason) => (
              <motion.li
                key={reason.code}
                layout={!reduce}
                initial={reduce ? false : { opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                exit={reduce ? undefined : { opacity: 0, x: -8 }}
                transition={{ duration: 0.18 }}
                className="border-l-4 border-insufficient bg-inset px-4 py-3 text-sm text-ink"
              >
                <span className="mr-2 font-mono font-semibold">
                  {reason.code === "STRADDLE" ? "Threshold" : reason.code}
                </span>
                {reason.text}
              </motion.li>
            ))}
          </AnimatePresence>
          {r.reasons.length === 0 && (
            <li className="border-l-4 border-rule px-4 py-3 text-sm text-ink-2">
              The gate is open: sample, coverage and interval all clear it, so a
              conclusion can be published.
            </li>
          )}
        </ul>

        <p className="m-0 text-meta text-ink-3">
          Engine thresholds: G1 n &ge; {GATE.minSampleN}, G2 width &le; {GATE.maxCiWidth.toFixed(2)},
          G3 coverage &ge; {GATE.minCoveragePct}%. Pass needs the lower bound &ge; {GATE.threshold};
          Fail needs the upper bound below it.
        </p>
      </div>
    </div>
  );
}

function Slider({
  label, value, min, max, step = 1, onChange,
}: {
  label: string; value: number; min: number; max: number; step?: number; onChange: (v: number) => void;
}) {
  const id = useId();
  const pct = ((value - min) / (max - min || 1)) * 100;
  return (
    <div>
      <div className="flex items-baseline justify-between gap-4">
        <label htmlFor={id} className="label">{label}</label>
        <output htmlFor={id} className="font-mono text-lg font-medium text-ink">{value.toLocaleString()}</output>
      </div>
      <input
        id={id}
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="range mt-3 w-full"
        style={{ "--pct": `${pct}%` } as React.CSSProperties}
      />
    </div>
  );
}

function IntervalBar({
  lower, upper, rate, spring,
}: {
  lower: number; upper: number; rate: number; spring: object;
}) {
  // Scale 0.5 to 1.0: below half the story is always "fail", and the
  // interesting movement happens near the 0.95 threshold.
  const lo = 0.5;
  const pos = (v: number) => Math.max(0, Math.min(1, (v - lo) / (1 - lo)));
  return (
    <figure className="m-0">
      <div className="relative h-[48px] overflow-hidden px-2" role="img" aria-label={`95% interval from ${lower.toFixed(3)} to ${upper.toFixed(3)}, threshold ${GATE.threshold}`}>
        <div className="absolute inset-x-0 top-[20px] h-2 bg-inset" />
        <motion.div
          className="absolute inset-x-0 top-[20px] h-2 origin-left bg-cobalt"
          initial={false}
          animate={{ x: `${pos(lower) * 100}%`, scaleX: Math.max(0.004, pos(upper) - pos(lower)) }}
          transition={spring}
        />
        <motion.div
          className="absolute inset-x-0 top-[16px]"
          initial={false}
          animate={{ x: `${pos(rate) * 100}%` }}
          transition={spring}
        >
          <span className="block h-4 w-4 -translate-x-1/2 rounded-full border-2 border-surface bg-ink" />
        </motion.div>
        <div className="absolute inset-y-0 w-[2px] bg-fail" style={{ left: `${pos(GATE.threshold) * 100}%` }} />
      </div>
      <figcaption className="relative mt-1 h-[18px] font-mono text-xs text-ink-3">
        <span className="absolute left-0">0.50</span>
        <span
          className="absolute -translate-x-1/2 whitespace-nowrap text-fail-text"
          style={{ left: `${pos(GATE.threshold) * 100}%` }}
        >
          0.95
        </span>
        <span className="absolute right-0">1.00</span>
      </figcaption>
    </figure>
  );
}

function Stat({ label, value, wide = false }: { label: string; value: string; wide?: boolean }) {
  return (
    <div className={wide ? "col-span-2" : ""}>
      <dt className="label font-sans">{label}</dt>
      <dd className="m-0 mt-1 text-base font-medium text-ink">{value}</dd>
    </div>
  );
}
