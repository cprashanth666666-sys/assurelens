import { FRAMEWORK_LABEL } from "@/lib/api";

/**
 * A framework mapping, as a sharp mono tag. [UX 4.2]
 *
 * An unverified citation is marked, not hidden: ISO/IEC 27001 is a paid
 * standard this project has not purchased, so its cross-references are from
 * working knowledge. A dashed border and a trailing "?" say so.
 */
export function FrameworkBadge({
  code,
  clauseRef,
  unverified = false,
}: {
  code: string;
  clauseRef?: string;
  unverified?: boolean;
}) {
  return (
    <span
      title={unverified ? "Citation not verified against the source standard" : undefined}
      className={[
        "inline-flex min-h-[24px] items-center whitespace-nowrap border px-2 font-mono text-xs font-medium",
        unverified
          ? "cursor-help border-dashed border-control text-ink-3"
          : "border-rule-strong bg-surface text-ink",
      ].join(" ")}
    >
      {FRAMEWORK_LABEL[code] ?? code}
      {clauseRef ? ` ${clauseRef}` : ""}
      {unverified ? " ?" : ""}
    </span>
  );
}
