/**
 * The evidence gate, as a pure function, for the Overview's interactive
 * explorer. It mirrors three of the engine's rules exactly
 * (backend/app/engine/thresholds.py) and states the one decision it adds.
 *
 *   G1  n < 30                      min_sample_n
 *   G2  95% Wilson width > 0.20     max_ci_width
 *   G3  coverage n / N < 10%        min_coverage_pct
 *
 * Pass / Fail uses a 5% tolerable exception rate (UX_BRIEF 13.9): Pass when
 * the interval's lower bound clears 0.95, Fail when its upper bound is below
 * 0.95. An interval straddling 0.95 cannot support either, so it is gated.
 * This is an illustration of the gate, not the engine's full procedure.
 */

export const GATE = {
  minSampleN: 30,
  maxCiWidth: 0.2,
  minCoveragePct: 10,
  threshold: 0.95,
  z: 1.96,
} as const;

export type GateVerdict = "PASS" | "FAIL" | "INSUFFICIENT_EVIDENCE";

export type GateReason = { code: "G1" | "G2" | "G3" | "STRADDLE"; text: string };

export type GateResult = {
  rate: number;
  lower: number;
  upper: number;
  width: number;
  coveragePct: number;
  verdict: GateVerdict;
  reasons: GateReason[];
};

/** 95% Wilson score interval for `successes` of `n`. */
export function wilson(successes: number, n: number, z: number = GATE.z) {
  if (n <= 0) return { lower: 0, upper: 1 };
  const p = successes / n;
  const z2 = z * z;
  const denom = 1 + z2 / n;
  const centre = (p + z2 / (2 * n)) / denom;
  const half = (z * Math.sqrt((p * (1 - p)) / n + z2 / (4 * n * n))) / denom;
  return { lower: Math.max(0, centre - half), upper: Math.min(1, centre + half) };
}

export function evaluateGate(n: number, exceptions: number, population: number): GateResult {
  const ex = Math.min(Math.max(0, exceptions), n);
  const { lower, upper } = wilson(n - ex, n);
  const width = upper - lower;
  const coveragePct = population > 0 ? (n / population) * 100 : 0;
  const reasons: GateReason[] = [];

  if (n < GATE.minSampleN) {
    reasons.push({ code: "G1", text: `Sample of ${n} is below the minimum of ${GATE.minSampleN} for a population conclusion.` });
  }
  if (width > GATE.maxCiWidth) {
    reasons.push({ code: "G2", text: `Interval width ${width.toFixed(3)} is wider than the ${GATE.maxCiWidth.toFixed(2)} limit.` });
  }
  if (coveragePct < GATE.minCoveragePct) {
    reasons.push({ code: "G3", text: `Coverage ${coveragePct.toFixed(1)}% is below the ${GATE.minCoveragePct}% minimum.` });
  }

  let verdict: GateVerdict;
  if (reasons.length > 0) verdict = "INSUFFICIENT_EVIDENCE";
  else if (lower >= GATE.threshold) verdict = "PASS";
  else if (upper < GATE.threshold) verdict = "FAIL";
  else {
    verdict = "INSUFFICIENT_EVIDENCE";
    reasons.push({ code: "STRADDLE", text: `The interval straddles ${GATE.threshold}, so neither Pass nor Fail can be stated.` });
  }

  return { rate: n > 0 ? (n - ex) / n : 0, lower, upper, width, coveragePct, verdict, reasons };
}
