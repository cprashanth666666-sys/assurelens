import { Placeholder } from "@/components/Placeholder";

export default function ReportPage() {
  return (
    <Placeholder
      title="Workpaper and export"
      summary={
        "An audit-format DOCX workpaper: control, procedure, population and " +
        "sample, evidence, result with its confidence interval and, where a " +
        "control was gated, the gate reason printed in full. Plus a " +
        "one-page executive summary generated from the same data."
      }
      buildsOn="Day 9"
    />
  );
}
