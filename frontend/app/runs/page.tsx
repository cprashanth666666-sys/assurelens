import { PageHeader } from "@/components/PageHeader";
import { RunConsole } from "@/components/RunConsole";
import { fetchEngagement, fetchRun, fetchRuns, fetchSuites } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function RunsPage() {
  const engagement = await fetchEngagement();

  if (engagement === null) {
    return (
      <PageHeader
        title="Test run console"
        lede="The API is unreachable, so a run cannot be started. The page renders regardless; content never waits on a cold backend."
      />
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
    <div className="flex flex-col gap-7">
      <PageHeader
        title="Test run console"
        lede="Select suites and run. Each control resolves to a verdict, and where the evidence cannot carry a conclusion the result says so, with what would resolve it. A gated verdict is a peer of a pass, not a failure to produce one."
      />

      <RunConsole engagementId={engagement.id} catalogue={catalogue} initialRun={latest} />
    </div>
  );
}
