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
    <section className="border border-n-200 bg-n-0 p-6">
      <h2>{title}</h2>
      <p className="mt-3 max-w-prose text-n-600">{summary}</p>
      <p className="mt-4 font-mono text-xs text-n-400">Builds on {buildsOn}</p>
    </section>
  );
}
