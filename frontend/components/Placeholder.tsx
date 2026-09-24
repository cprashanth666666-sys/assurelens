/**
 * Scaffolding. Each route renders what it will become and which day builds
 * it, so the deployed skeleton is honest about being a skeleton rather than
 * showing a fake dashboard. Every instance is deleted by the day it names.
 *
 * v5: a dashed frame (unbuilt) with a lime tag stating when it lands.
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
    <section className="border-2 border-dashed border-control bg-surface p-5 md:p-7">
      <p className="m-0 inline-flex bg-lime px-2 py-1 font-mono text-meta font-medium text-on-lime">
        Builds on {buildsOn}
      </p>
      <h2 className="mt-4">{title}</h2>
      <p className="m-0 mt-3 max-w-prose text-base text-ink-2">{summary}</p>
    </section>
  );
}
