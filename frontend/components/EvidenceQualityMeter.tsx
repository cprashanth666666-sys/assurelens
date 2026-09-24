import type { EvidenceQuality } from "@/lib/api";

/**
 * Evidence quality meter: one composition bar across the whole estate --
 * sufficient evidence / thin (insufficient evidence) / not yet measured.
 * [UX_BRIEF 4.1.C]
 *
 * A single-series bar needs no legend box (the title names it, per the
 * dataviz skill), but each segment still carries a visible count and text
 * label beside the bar -- never colour alone -- and reuses the product's
 * own verdict/status fills rather than a chart-specific palette, the same
 * rule ReadinessByDomain and RiskHeatmap follow.
 */

const SEGMENTS: {
  key: keyof Pick<EvidenceQuality, "sufficient" | "thin" | "no_evidence">;
  label: string;
  className: string;
}[] = [
  { key: "sufficient", label: "Sufficient evidence", className: "bg-pass" },
  { key: "thin", label: "Thin (insufficient evidence)", className: "bg-insufficient" },
  {
    key: "no_evidence",
    label: "Not yet measured",
    className:
      "bg-inset bg-[repeating-linear-gradient(135deg,var(--control)_0,var(--control)_1px,transparent_1px,transparent_6px)] opacity-70",
  },
];

export function EvidenceQualityMeter({ quality }: { quality: EvidenceQuality }) {
  const total = quality.total || 1;

  return (
    <div className="flex flex-col gap-2">
      <div
        className="flex h-[22px] w-full divide-x divide-surface overflow-hidden border border-rule-strong"
        role="img"
        aria-label={
          `Evidence quality across ${quality.total} controls: ` +
          SEGMENTS.map((s) => `${quality[s.key]} ${s.label.toLowerCase()}`).join(", ") +
          "."
        }
      >
        {SEGMENTS.filter((s) => quality[s.key] > 0).map((s) => (
          <span
            key={s.key}
            className={`${s.className} h-full`}
            style={{ width: `${(quality[s.key] / total) * 100}%` }}
            title={`${s.label}: ${quality[s.key]}`}
          />
        ))}
      </div>

      <ul className="m-0 flex flex-wrap gap-x-5 gap-y-2 p-0 text-meta text-ink-2">
        {SEGMENTS.map((s) => (
          <li key={s.key} className="flex list-none items-center gap-2">
            <span aria-hidden="true" className={`h-[10px] w-[10px] shrink-0 ${s.className}`} />
            {s.label}
            <span className="font-mono text-ink-3">({quality[s.key]})</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
