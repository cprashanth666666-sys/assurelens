import { Placeholder } from "@/components/Placeholder";

export default function RoadmapPage() {
  return (
    <Placeholder
      title="Remediation roadmap"
      summary={
        "A 90-day plan: effort against impact, then an ordered list of " +
        "actions with owners and expected residual risk. The ordering rule is " +
        "printed on screen so a client can argue with it rather than accept it."
      }
      buildsOn="Day 8"
    />
  );
}
