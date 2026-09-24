import { PageHeader } from "@/components/PageHeader";
import { Placeholder } from "@/components/Placeholder";
import { Reveal } from "@/components/Reveal";
import { RoadmapList } from "@/components/RoadmapList";
import { RoadmapScatter } from "@/components/RoadmapScatter";
import { fetchEngagement, fetchRoadmap } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function RoadmapPage() {
  const engagement = await fetchEngagement();

  if (engagement === null) {
    return (
      <PageHeader
        title="Remediation roadmap"
        lede="The API is unreachable, so the roadmap cannot be built. The page renders regardless; content never waits on a cold backend."
      />
    );
  }

  const roadmap = await fetchRoadmap(engagement.id);

  if (roadmap === null || roadmap.items.length === 0) {
    return (
      <Placeholder
        title="Remediation roadmap"
        summary={
          roadmap === null
            ? "The API is unreachable, so the roadmap cannot be built right now."
            : "No open findings to sequence. The roadmap is empty because nothing is currently open."
        }
        buildsOn="Day 8"
      />
    );
  }

  return (
    <div className="flex flex-col gap-9">
      <PageHeader
        title="Remediation roadmap"
        lede="A plan, not a scoreboard: effort against impact, then an ordered list of actions with owners and the expected reduction in risk score. The ordering rule is printed below, not summarised, so it can be argued with rather than accepted."
      />

      <Reveal as="section" className="flex flex-col gap-4">
        <h3 className="m-0 text-lg font-medium">Effort × impact</h3>
        <RoadmapScatter items={roadmap.items} />
      </Reveal>

      <Reveal as="section" className="flex flex-col gap-4">
        <h3 className="m-0 text-lg font-medium">Sequence</h3>
        <RoadmapList orderingRule={roadmap.ordering_rule} items={roadmap.items} />
      </Reveal>
    </div>
  );
}
