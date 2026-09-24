import type { ClauseRef } from "@/lib/api";
import { FRAMEWORK_LABEL } from "@/lib/api";

/**
 * The verbatim text of the clause a control rests on: the reader sees the
 * statute, not a paraphrase. [UX 4.3]
 *
 * v5 marks quoted matter by a 4px cobalt rule and a larger size, not by a
 * serif. The primary basis carries the lime "Legal basis" tag.
 */
export function ClauseQuote({ clause }: { clause: ClauseRef }) {
  const unverified = clause.source_status === "UNVERIFIED";

  return (
    <div className={`border-l-4 pl-4 md:pl-5 ${clause.is_primary ? "border-cobalt" : "border-rule"}`}>
      <div className="flex flex-wrap items-center gap-2">
        <span className="font-mono text-sm font-semibold text-ink">
          {FRAMEWORK_LABEL[clause.framework_code] ?? clause.framework_code} {clause.ref}
        </span>
        {clause.is_primary && (
          <span className="bg-lime px-2 py-[2px] text-meta font-semibold text-on-lime">Legal basis</span>
        )}
        {clause.in_force_from && (
          <span className="font-mono text-meta text-ink-3">in force {clause.in_force_from}</span>
        )}
      </div>

      <p className="m-0 mt-1 text-sm font-medium text-ink-2">{clause.title}</p>

      {clause.verbatim_text ? (
        <blockquote className="m-0 mt-3 text-lg font-normal leading-prose text-ink">
          &ldquo;{clause.verbatim_text}&rdquo;
        </blockquote>
      ) : (
        <p className="m-0 mt-3 text-sm text-ink-3">No verbatim text recorded for this reference.</p>
      )}

      {unverified && clause.source_note && (
        <p className="m-0 mt-3 border-l-2 border-dashed border-control pl-3 text-sm text-ink-2">
          <span className="font-semibold text-ink">Unverified.</span> {clause.source_note}
        </p>
      )}

      {clause.rationale && (
        <p className="m-0 mt-3 text-sm text-ink-2">
          <span className="font-semibold text-ink">Why this clause.</span> {clause.rationale}
        </p>
      )}
    </div>
  );
}
