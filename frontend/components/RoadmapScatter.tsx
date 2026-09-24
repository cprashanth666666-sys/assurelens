import { SEVERITY_CLASS, type RoadmapItem } from "@/lib/api";

/**
 * Effort x impact scatter. [UX_BRIEF 4.6]
 *
 * X is effort in days (0 to 10, the service's own CRITICAL ceiling from
 * `DEFAULT_EFFORT_DAYS`), left is cheap; Y is impact (1 to 5, the same
 * scale the heatmap uses), top is severe. Two independent measures on two
 * axes of the SAME chart, not a dual y-axis on one. Quadrant hairlines sit
 * at the midpoint of each scale and are labelled in the margin, never as a
 * shaded block -- a point straddling a line is still exactly where it is.
 *
 * Each point takes its fill from the finding's own severity, the product's
 * reserved status colour, not a chart-specific categorical hue; a ref label
 * sits beside every point since a roadmap rarely holds more than a dozen.
 */
const EFFORT_MAX = 10;
const IMPACT_MAX = 5;

export function RoadmapScatter({ items }: { items: RoadmapItem[] }) {
  const xOf = (effort: number) => Math.min(1, effort / EFFORT_MAX) * 100;
  const yOf = (impact: number) => 100 - (Math.min(IMPACT_MAX, impact) / IMPACT_MAX) * 100;

  return (
    <figure className="m-0 flex flex-col gap-2">
      <div className="flex gap-2">
        <div className="flex w-8 shrink-0 flex-col justify-between py-1 text-right">
          <span className="label">5</span>
          <span className="label">1</span>
        </div>
        <div
          className="relative aspect-[16/10] w-full border border-rule-strong bg-surface"
          role="img"
          aria-label={`Effort by impact for ${items.length} findings: ${items
            .map((i) => `${i.ref} at ${i.effort_days} days effort, impact ${i.impact}`)
            .join(", ")}.`}
        >
          {/* Quadrant hairlines at the midpoint of each scale. */}
          <div className="absolute inset-y-0 left-1/2 w-px bg-rule" aria-hidden="true" />
          <div className="absolute inset-x-0 top-1/2 h-px bg-rule" aria-hidden="true" />

          {items.map((item) => (
            <div
              key={item.ref}
              className="group absolute -translate-x-1/2 -translate-y-1/2"
              style={{ left: `${xOf(item.effort_days)}%`, top: `${yOf(item.impact)}%` }}
            >
              <span
                title={`${item.ref}: ${item.control_ref}, effort ${item.effort_days}d, impact ${item.impact}, priority ${item.priority.toFixed(2)}`}
                className={`block h-3 w-3 cursor-default rounded-full border-2 border-surface ${bgOf(item)}`}
              />
              <span className="pointer-events-none absolute left-1/2 top-full mt-1 -translate-x-1/2 whitespace-nowrap font-mono text-xs text-ink-2">
                {item.ref}
              </span>
            </div>
          ))}
        </div>
      </div>
      <div className="ml-10 flex justify-between font-mono text-xs text-ink-3">
        <span>0 days</span>
        <span>{EFFORT_MAX} days</span>
      </div>

      <figcaption className="mt-1 grid grid-cols-1 gap-x-4 gap-y-1 text-meta text-ink-2 sm:grid-cols-2">
        <p className="m-0">Top-left: quick wins — high impact, low effort.</p>
        <p className="m-0">Top-right: major projects — high impact, high effort.</p>
        <p className="m-0">Bottom-left: fill-ins — low impact, low effort.</p>
        <p className="m-0">Bottom-right: low priority — low impact, high effort.</p>
      </figcaption>
    </figure>
  );
}

function bgOf(item: RoadmapItem): string {
  return SEVERITY_CLASS[item.severity].split(" ").find((c) => c.startsWith("bg-")) ?? "bg-ink";
}
