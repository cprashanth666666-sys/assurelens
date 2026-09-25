"use client";

import { VERDICT_CLASS, VERDICT_LABEL, type Verdict } from "@/lib/api";
import { useRole } from "./RoleProvider";

/**
 * A verdict, rendered as a peer of the others: one chip, one size, one
 * weight, one slot. Colour is redundant encoding; the word and the SHAPE
 * carry the verdict on their own (full disc, half disc, empty ring, dash),
 * so it survives monochrome print and colour-vision deficiency.
 * [PRD 6.5, a11y color-not-only]
 *
 * The raw gate codes (G1, G3, ...) are consultant instrumentation -- a
 * client reads the plain-language "Why / Resolve" block that sits beside
 * this badge wherever it appears, not a code they would have to look up.
 * [PRD 4.4: "shows the failed rule and threshold" vs "shows what evidence
 * is needed and who supplies it"] A single client leaf, not a server/client
 * split per caller, since every caller already sits inside `RoleProvider`.
 */

const SHAPE: Record<Verdict, React.ReactNode> = {
  // Full: a conclusion the evidence closed.
  PASS: <circle cx="5" cy="5" r="3.8" fill="currentColor" />,

  // Half: a conclusion the evidence closed, adversely. Drawn as a filled
  // semicircle inside the same ring, so it reads as the same object in a
  // different state rather than as a different icon.
  FAIL: (
    <>
      <circle cx="5" cy="5" r="3.8" fill="none" stroke="currentColor" strokeWidth="1.3" />
      <path d="M5 1.2A3.8 3.8 0 0 0 5 8.8Z" fill="currentColor" />
    </>
  ),

  // Empty: the shape of a conclusion, not filled by evidence.
  INSUFFICIENT_EVIDENCE: (
    <circle cx="5" cy="5" r="3.4" fill="none" stroke="currentColor" strokeWidth="1.3" />
  ),

  // A rule: nothing to conclude, by scope.
  NOT_APPLICABLE: (
    <path d="M1.5 5h7" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
  ),
};

export function VerdictBadge({
  verdict,
  gateReasons = [],
}: {
  verdict: Verdict;
  gateReasons?: string[];
}) {
  const role = useRole();
  const codes = gateReasons.map((r) => r.split("_")[0]).join(" ");

  return (
    <span className="inline-flex items-center gap-2 whitespace-nowrap">
      <span className={`chip ${VERDICT_CLASS[verdict]}`}>
        <svg viewBox="0 0 10 10" width="10" height="10" aria-hidden="true" className="shrink-0">
          {SHAPE[verdict]}
        </svg>
        {VERDICT_LABEL[verdict]}
      </span>

      {codes && role === "consultant" && (
        <abbr
          className="cursor-help font-mono text-xs font-medium text-ink-2 underline decoration-dotted underline-offset-2"
          title={gateReasons.join(", ")}
        >
          {codes}
        </abbr>
      )}
    </span>
  );
}
