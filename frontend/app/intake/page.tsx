import { IntakePortal } from "@/components/IntakePortal";
import { PageHeader } from "@/components/PageHeader";
import { fetchDocuments, fetchEngagement } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function IntakePage() {
  const engagement = await fetchEngagement();

  if (engagement === null) {
    return (
      <PageHeader
        title="Document intake"
        lede="The API is unreachable, so a document cannot be submitted. The page renders regardless; content never waits on a cold backend."
      />
    );
  }

  const documents = (await fetchDocuments(engagement.id)) ?? [];

  return (
    <div className="flex flex-col gap-7">
      <PageHeader
        title="Document intake"
        lede="Submit a policy, notice or agreement as a file, or point at a published page. Each submission is stored, its text extracted, and classified against known DPDP document types. A submission the classifier cannot confidently place is reported as such, not guessed."
      />

      <IntakePortal engagementId={engagement.id} initialDocuments={documents} />
    </div>
  );
}
