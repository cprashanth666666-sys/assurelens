import { SEVERITY_CLASS, SEVERITY_LABEL, type RoadmapItem } from "@/lib/api";

/**
 * The roadmap's ordered list: sequence, action, owner, effort, expected
 * residual reduction. [UX_BRIEF 4.6] The ordering rule is computed live by
 * the API (`priority = impact / effort_days`, never stored) and printed
 * here verbatim, not summarised, so a reader can check any two rows'
 * relative order by hand rather than trust the sequence number alone.
 */
export function RoadmapList({ orderingRule, items }: { orderingRule: string; items: RoadmapItem[] }) {
  return (
    <div className="flex flex-col gap-4">
      <p className="m-0 max-w-prose border-l-2 border-control bg-inset px-4 py-3 text-sm text-ink-2">
        {orderingRule}
      </p>

      <ol className="m-0 flex list-none flex-col gap-px bg-rule-strong p-0">
        {items.map((item) => (
          <li key={item.ref} className="bg-surface p-4 md:p-5">
            <div className="grid grid-cols-[2.5rem_minmax(0,1fr)] items-start gap-4 sm:grid-cols-[2.5rem_minmax(0,1fr)_9rem_9rem_11rem]">
              <p className="m-0 font-mono text-lg font-medium text-ink-3">{item.sequence}</p>

              <div className="flex flex-col gap-1">
                <p className="m-0 font-medium text-ink">{item.action}</p>
                <p className="m-0 flex flex-wrap items-center gap-2 text-meta text-ink-2">
                  <span className="font-mono">{item.ref}</span>
                  <span aria-hidden="true">·</span>
                  <span className="font-mono">{item.control_ref}</span>
                  <span className={`chip ${SEVERITY_CLASS[item.severity]}`}>
                    {SEVERITY_LABEL[item.severity]}
                  </span>
                </p>
              </div>

              <Meta label="Owner" value={item.owner ?? "Unassigned"} className="col-start-1 col-span-2 sm:col-start-3 sm:col-span-1" />
              <Meta label="Effort" value={`${item.effort_days} days`} className="col-start-1 col-span-2 sm:col-start-4 sm:col-span-1" />
              <Meta
                label="Risk score removed"
                value={`${item.expected_residual_reduction} / 25`}
                className="col-start-1 col-span-2 sm:col-start-5 sm:col-span-1"
              />
            </div>
          </li>
        ))}
      </ol>
    </div>
  );
}

function Meta({ label, value, className = "" }: { label: string; value: string; className?: string }) {
  return (
    <div className={className}>
      <p className="label m-0">{label}</p>
      <p className="m-0 font-mono text-sm text-ink">{value}</p>
    </div>
  );
}
