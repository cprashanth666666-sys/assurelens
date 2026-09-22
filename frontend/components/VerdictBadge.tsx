import { VERDICT_CLASS, VERDICT_LABEL, type Verdict } from "@/lib/api";

/**
 * A verdict, rendered as a peer of the others.
 *
 * Insufficient evidence gets neutral ink, the same type weight, the same
 * slot. No warning colour, no icon, no smaller font. It is a deliberate
 * conclusion about the assessment, not a fault in the client, and styling it
 * as an alert would say the opposite. [PRD 6.5, UX 6.1]
 */
export function VerdictBadge({
  verdict,
  gateReasons = [],
}: {
  verdict: Verdict;
  gateReasons?: string[];
}) {
  const codes = gateReasons.map((r) => r.split("_")[0]).join(" ");

  return (
    <span className="whitespace-nowrap">
      <span className={`font-semibold ${VERDICT_CLASS[verdict]}`}>
        {VERDICT_LABEL[verdict]}
      </span>
      {codes && (
        <sup
          className="ml-1 font-mono text-2xs text-n-500"
          title={gateReasons.join(", ")}
        >
          {codes}
        </sup>
      )}
    </span>
  );
}
