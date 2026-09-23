/**
 * Day 1 scaffolding. Each route renders what it will become and which day
 * builds it, so the deployed skeleton is honest about being a skeleton
 * rather than showing a fake dashboard.
 *
 * Every instance of this component is deleted by the day it names.
 */
export function Placeholder({
  title,
  summary,
  buildsOn,
}: {
  title: string;
  summary: string;
  buildsOn: string;
}) {
  return (
    <section data-tilt className="panel relative overflow-hidden p-5 md:p-6">
      {/* A hatched corner: this panel is scaffolding and says so at a glance,
          without a banner taking up a line of the layout. */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute -right-6 -top-6 h-[72px] w-[72px] rotate-45"
        style={{
          background:
            "repeating-linear-gradient(45deg, var(--warm-100) 0 6px, transparent 6px 12px)",
        }}
      />
      <h2>{title}</h2>
      <p className="mt-3 max-w-prose text-n-600">{summary}</p>
      <p className="mt-4 inline-flex items-center gap-2 font-mono text-xs text-n-400">
        <span aria-hidden="true" className="h-px w-5 bg-warm-500" />
        Builds on {buildsOn}
      </p>
    </section>
  );
}
