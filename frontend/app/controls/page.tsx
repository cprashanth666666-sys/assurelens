import Link from "next/link";

import { ControlTable } from "@/components/ControlTable";
import { PageHeader } from "@/components/PageHeader";
import { Reveal } from "@/components/Reveal";
import { DOMAINS, DOMAIN_LABEL, fetchControls, type Domain } from "@/lib/api";

export const dynamic = "force-dynamic";

type SearchParams = Promise<{ domain?: string; executable?: string }>;

export default async function ControlsPage({
  searchParams,
}: {
  searchParams: SearchParams;
}) {
  const params = await searchParams;

  const query = new URLSearchParams();
  if (params.domain) query.set("domain", params.domain);
  if (params.executable) query.set("executable", params.executable);
  const qs = query.toString();

  const controls = await fetchControls(qs ? `?${qs}` : "");

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
          <Count label={params.domain || params.executable ? "Shown" : "Controls"} value={controls.length} />
          <Count label="Executable" value={executable} />
          <Count label="Documented" value={controls.length - executable} />
          <Count label="Not applicable" value={outOfScope} />
        </dl>
      </PageHeader>

      <FilterRail active={params.domain} executable={params.executable} />

      <Reveal>
        <ControlTable controls={controls} />
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

function FilterRail({ active, executable }: { active?: string; executable?: string }) {
  const href = (next: Record<string, string | undefined>) => {
    const q = new URLSearchParams();
    const domain = "domain" in next ? next.domain : active;
    const exec = "executable" in next ? next.executable : executable;
    if (domain) q.set("domain", domain);
    if (exec) q.set("executable", exec);
    const s = q.toString();
    return s ? `/controls?${s}` : "/controls";
  };

  return (
    <nav aria-label="Filter controls" className="flex flex-col gap-4 xl:flex-row xl:items-end xl:justify-between">
      <FilterGroup label="Domain">
        <FilterLink href={href({ domain: undefined })} active={!active}>All</FilterLink>
        {DOMAINS.map((d: Domain) => (
          <FilterLink key={d} href={href({ domain: d })} active={active === d}>
            {DOMAIN_LABEL[d]}
          </FilterLink>
        ))}
      </FilterGroup>

      <FilterGroup label="Type">
        <FilterLink href={href({ executable: undefined })} active={!executable}>All</FilterLink>
        <FilterLink href={href({ executable: "true" })} active={executable === "true"}>Executable</FilterLink>
        <FilterLink href={href({ executable: "false" })} active={executable === "false"}>Documented</FilterLink>
      </FilterGroup>
    </nav>
  );
}

function FilterGroup({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="min-w-0">
      <p className="label m-0">{label}</p>
      {/* Scrolls sideways on a phone rather than wrapping into five rows. */}
      <div className="scroll-x edge-fade mt-2 flex flex-nowrap gap-2 pb-1 md:flex-wrap">{children}</div>
    </div>
  );
}

function FilterLink({
  href,
  active,
  children,
}: {
  href: string;
  active: boolean;
  children: React.ReactNode;
}) {
  return (
    <Link href={href} aria-current={active ? "true" : undefined} className="toggle">
      {children}
    </Link>
  );
}
