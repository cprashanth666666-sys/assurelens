import { FindingsRegister } from "@/components/FindingsRegister";
import { PageHeader } from "@/components/PageHeader";
import { Placeholder } from "@/components/Placeholder";
import { Reveal } from "@/components/Reveal";
import { fetchEngagement, fetchFindings } from "@/lib/api";
import { getRole } from "@/lib/role-server";

export const dynamic = "force-dynamic";

type SearchParams = Promise<{ likelihood?: string; impact?: string }>;

export default async function FindingsPage({
  searchParams,
}: {
  searchParams: SearchParams;
}) {
  const [params, role] = await Promise.all([searchParams, getRole()]);
  const engagement = await fetchEngagement();

  if (engagement === null) {
    return (
      <PageHeader
        title="Findings register"
        lede="The API is unreachable, so findings cannot be listed. The page renders regardless; content never waits on a cold backend."
      />
    );
  }

  const findings = await fetchFindings(engagement.id);

  if (findings === null) {
    return (
      <Placeholder
        title="Findings register"
        summary="The API is unreachable, so findings cannot be listed right now."
        buildsOn="Day 8"
      />
    );
  }

  const likelihood = Number(params.likelihood);
  const impact = Number(params.impact);
  // Internal reviewer notes never leave the server for the client role --
  // filtering client-side only would still ship the text in the RSC
  // payload. [PRD 4.4: "internal reviewer notes hidden"]
  const visibleFindings = role === "client"
    ? findings.filter((f) => !f.is_internal_note_only)
    : findings;

  return (
    <div className="flex flex-col gap-7">
      <PageHeader
        title="Findings register"
        lede="Findings raised by tests that actually ran; none are seeded. Severity is likelihood × impact, carried as a left border and a text label, never colour alone. Expand a row for the evidence, the root cause, and the history of what changed."
      />

      <Reveal>
        <FindingsRegister
          findings={visibleFindings}
          initialLikelihood={Number.isInteger(likelihood) ? likelihood : undefined}
          initialImpact={Number.isInteger(impact) ? impact : undefined}
        />
      </Reveal>
    </div>
  );
}
