import { Placeholder } from "@/components/Placeholder";

export default function FindingsPage() {
  return (
    <Placeholder
      title="Findings register"
      summary={
        "Findings raised by tests that actually ran; none are seeded. " +
        "Severity is likelihood × impact, carried as a left border and a text " +
        "label, never colour alone. Expand a row for the evidence: for a " +
        "probe finding, the HTTP exchange itself."
      }
      buildsOn="Day 8"
    />
  );
}
