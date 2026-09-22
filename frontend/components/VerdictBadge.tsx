import { VERDICT_CLASS, VERDICT_LABEL, type Verdict } from "@/lib/api";

/**
 * A verdict, rendered as a peer of the others.
 *
 * Insufficient evidence gets neutral ink, the same type weight, the same
 * slot. No warning colour, no alert icon, no smaller font. It is a
 * deliberate conclusion about the assessment, not a fault in the client, and
 * styling it as an alert would say the opposite. [PRD 6.5, UX 6.1]
 *
 * v2.0 adds a 8px mark before the label. It is NOT decoration and NOT a
 * status icon in the ✅/⚠️ sense UX 1.1 rejects: it is a SHAPE, so the four
 * verdicts are distinguishable without relying on colour — a filled disc, a
 * hollow ring, a half disc, a dash. On a monochrome print, or to a reader
 * with deuteranopia, the shape and the word still carry it.
 * [a11y color-not-only]
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
  const codes = gateReasons.map((r) => r.split("_")[0]).join(" ");

  return (
    <span className="inline-flex items-baseline gap-2 whitespace-nowrap">
      <span className={`inline-flex items-center gap-2 font-semibold ${VERDICT_CLASS[verdict]}`}>
        <svg
          viewBox="0 0 10 10"
          width="9"
          height="9"
          aria-hidden="true"
          className="shrink-0 translate-y-px"
        >
          {SHAPE[verdict]}
        </svg>
        {VERDICT_LABEL[verdict]}
      </span>

      {codes && (
        <sup
          className="cursor-help font-mono text-2xs text-n-500 underline decoration-dotted decoration-from-font underline-offset-2 transition-colors duration-base ease-out hover:text-n-700"
          title={gateReasons.join(", ")}
        >
          {codes}
        </sup>
      )}
    </span>
  );
}
