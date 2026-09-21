import { Placeholder } from "@/components/Placeholder";

export default function RunsPage() {
  return (
    <Placeholder
      title="Test run console"
      summary={
        "Select suites, set the seed, run. Verdicts stream in as each control " +
        "resolves. A gated verdict lands as calmly as a pass — that restraint " +
        "is the point. The only animation in the product is a 1px " +
        "indeterminate rule under the running control."
      }
      buildsOn="Day 5"
    />
  );
}
