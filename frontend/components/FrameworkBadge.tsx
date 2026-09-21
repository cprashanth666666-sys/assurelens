import { FRAMEWORK_LABEL } from "@/lib/api";

/**
 * Framework mappings are the one place pills are permitted. [UX 4.2]
 *
 * An unverified citation is marked, not hidden. ISO/IEC 27001 is a paid
 * standard this project has not purchased, so its cross-references are
 * recorded from working knowledge and labelled as such — a reader can then
 * tell which citations carry weight.
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
        "inline-block rounded-sm border px-1 font-mono text-2xs leading-table",
        unverified
          ? "border-dashed border-n-300 text-n-500"
          : "border-n-200 text-n-600",
      ].join(" ")}
    >
      {FRAMEWORK_LABEL[code] ?? code}
      {clauseRef ? ` ${clauseRef}` : ""}
      {unverified ? " ?" : ""}
    </span>
  );
}
