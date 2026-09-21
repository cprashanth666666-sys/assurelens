import type { ClauseRef } from "@/lib/api";
import { FRAMEWORK_LABEL } from "@/lib/api";

/**
 * Renders the verbatim text of the clause a control rests on.
 *
 * This is the credibility move: the reader sees the statute, not a
 * paraphrase. Serif on a ruled left margin, because it is quoted matter and
 * should read as such rather than as UI copy. [UX 4.3]
 */
export function ClauseQuote({ clause }: { clause: ClauseRef }) {
  const unverified = clause.source_status === "UNVERIFIED";

  return (
    <div className="border-l-2 border-n-200 pl-4">
      <div className="flex flex-wrap items-baseline gap-2">
        <span className="font-mono text-xs text-n-700">
          {FRAMEWORK_LABEL[clause.framework_code] ?? clause.framework_code}{" "}
          {clause.ref}
        </span>
        {clause.is_primary && (
          <span className="text-2xs uppercase tracking-[0.14em] text-accent-600">
            Legal basis
          </span>
        )}
        {clause.in_force_from && (
          <span className="font-mono text-2xs text-n-400">
            in force {clause.in_force_from}
          </span>
        )}
      </div>

      <p className="m-0 mt-1 text-sm text-n-700">{clause.title}</p>

      {clause.verbatim_text ? (
        <blockquote className="m-0 mt-3 font-serif text-base leading-prose text-n-800">
          &ldquo;{clause.verbatim_text}&rdquo;
        </blockquote>
      ) : (
        <p className="m-0 mt-3 text-sm text-n-500">
          No verbatim text recorded for this reference.
        </p>
      )}

      {unverified && clause.source_note && (
        <p className="m-0 mt-3 border-l-2 border-dashed border-n-300 pl-3 text-xs text-n-500">
          <span className="uppercase tracking-[0.14em]">Unverified</span> —{" "}
          {clause.source_note}
        </p>
      )}

      {clause.rationale && (
        <p className="m-0 mt-3 text-xs text-n-500">
          <span className="uppercase tracking-[0.14em] text-n-400">Why</span>{" "}
          {clause.rationale}
        </p>
      )}
    </div>
  );
}
