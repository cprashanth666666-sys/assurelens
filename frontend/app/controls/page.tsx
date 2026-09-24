import { ControlsBrowser } from "@/components/ControlsBrowser";
import { PageHeader } from "@/components/PageHeader";
import { Reveal } from "@/components/Reveal";
import { fetchControls } from "@/lib/api";

export const dynamic = "force-dynamic";

type SearchParams = Promise<{ domain?: string; executable?: string }>;

export default async function ControlsPage({
  searchParams,
}: {
  searchParams: SearchParams;
}) {
  const params = await searchParams;
  // All 25 rows, once. Search and filters then run in the browser.
  const controls = await fetchControls("");

  if (controls === null) {
    return (
      <PageHeader
        title="Control library"
        lede="The API is unreachable, so the library cannot be listed. The page renders regardless; content never waits on a cold backend."
      />
    );
  }

  const executable = controls.filter((c) => c.is_executable).length;
  const outOfScope = controls.filter((c) => !c.in_scope).length;

  return (
    <div className="flex flex-col gap-7">
      <PageHeader
        title="Control library"
        lede={
          <>
            Controls derived from the Digital Personal Data Protection Act 2023
            and Rules 2025, cross-mapped to ISO/IEC 27001:2022 and the NIST AI
            RMF. Every control cites one clause as its legal basis, quoted
            verbatim on the control&rsquo;s page.
          </>
        }
      >
        {/* Counts of controls, not results: there is still no score. */}
        <dl className="ruled m-0 mt-2 grid-cols-2 sm:grid-cols-4">
          <Count label="Controls" value={controls.length} />
          <Count label="Executable" value={executable} />
          <Count label="Documented" value={controls.length - executable} />
          <Count label="Not applicable" value={outOfScope} />
        </dl>
      </PageHeader>

      <Reveal>
        <ControlsBrowser
          controls={controls}
          initialDomain={params.domain}
          initialExec={params.executable}
        />
      </Reveal>
    </div>
  );
}

function Count({ label, value }: { label: string; value: number }) {
  return (
    <div className="px-4 py-4 md:px-5">
      <dt className="label">{label}</dt>
      <dd className="m-0 mt-1 font-mono text-num font-medium tracking-head text-ink">{value}</dd>
    </div>
  );
}
