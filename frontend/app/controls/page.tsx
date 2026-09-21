import { Placeholder } from "@/components/Placeholder";

export default function ControlsPage() {
  return (
    <Placeholder
      title="Control library"
      summary={
        "25 controls drawn from the DPDP Rules 2025 and cross-mapped to " +
        "ISO/IEC 27001:2022 and the NIST AI RMF. Each carries an objective, " +
        "a test procedure, an evidence contract, and the verbatim text of the " +
        "rule it rests on — so the reader sees the statute, not a paraphrase."
      }
      buildsOn="Day 2"
    />
  );
}
