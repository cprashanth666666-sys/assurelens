import { Placeholder } from "@/components/Placeholder";
import { HealthProbe } from "@/components/HealthProbe";

export default function OverviewPage() {
  return (
    <div className="flex flex-col gap-6">
      <Placeholder
        title="Engagement overview"
        summary={
          "Readiness by domain, a 5×5 risk heatmap, and the evidence quality " +
          "meter — what proportion of the estate has been graded, and what " +
          "has not. Deliberately no headline compliance percentage: a domain " +
          "at 40% coverage and one at 95% cannot be averaged into an honest " +
          "number."
        }
        buildsOn="Day 8"
      />
      <HealthProbe />
    </div>
  );
}
