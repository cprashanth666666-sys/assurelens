import { RunConsole } from "@/components/RunConsole";
import { fetchEngagement, fetchRun, fetchRuns, fetchSuites } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function RunsPage() {
  const engagement = await fetchEngagement();

  if (engagement === null) {
    return (
      <section className="border border-n-200 bg-n-0 p-6">
        <h2>Test run console</h2>
        <p className="mt-3 max-w-prose text-n-600">
          The API is unreachable, so a run cannot be started. The page renders
          regardless &mdash; content never waits on a cold backend.
        </p>
      </section>
    );
  }

  const [catalogue, runs] = await Promise.all([
    fetchSuites(),
    fetchRuns(engagement.id),
  ]);

  // Show the most recent run on arrival, so the page has something to say
  // before anyone presses anything.
  const latest = runs && runs.length > 0 ? await fetchRun(runs[0]!.id) : null;

  return (
    <div className="flex flex-col gap-5">
      <header>
        <h2>Test run console</h2>
        <p className="mt-2 max-w-prose text-n-600">
          Select suites and run. Each control resolves to a verdict, and where
          the evidence cannot carry a conclusion the result says so, with what
          would resolve it. A gated verdict is a peer of a pass, not a failure
          to produce one.
        </p>
      </header>

      <RunConsole
        engagementId={engagement.id}
        catalogue={catalogue}
        initialRun={latest}
      />
    </div>
  );
}
