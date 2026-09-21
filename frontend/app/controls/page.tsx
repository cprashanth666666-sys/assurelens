import Link from "next/link";

import { ControlTable } from "@/components/ControlTable";
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
      <section className="border border-n-200 bg-n-0 p-6">
        <h2>Control library</h2>
        <p className="mt-3 max-w-prose text-n-600">
          The API is unreachable, so the library cannot be listed. The page
          renders regardless — content never waits on a cold backend.
        </p>
      </section>
    );
  }

  const executable = controls.filter((c) => c.is_executable).length;
  const outOfScope = controls.filter((c) => !c.in_scope).length;

  return (
    <div className="flex flex-col gap-5">
      <header>
        <h2>Control library</h2>
        <p className="mt-2 max-w-prose text-n-600">
          Controls derived from the Digital Personal Data Protection Act 2023
          and Rules 2025, cross-mapped to ISO/IEC 27001:2022 and the NIST AI
          RMF. Every control cites one clause as its legal basis, and the
          clause is quoted verbatim on the control&rsquo;s page.
        </p>
        <p className="m-0 mt-3 font-mono text-2xs text-n-500">
          {controls.length} controls &middot; {executable} executable &middot;{" "}
          {controls.length - executable} documented
          {outOfScope > 0 && ` · ${outOfScope} not applicable`}
        </p>
      </header>

      <FilterRail active={params.domain} executable={params.executable} />

      <ControlTable controls={controls} />
    </div>
  );
}

function FilterRail({
  active,
  executable,
}: {
  active?: string;
  executable?: string;
}) {
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
    <nav
      aria-label="Filter controls"
      className="flex flex-wrap items-center gap-x-4 gap-y-2 border-y border-n-100 py-2 text-xs"
    >
      <span className="text-2xs uppercase tracking-[0.14em] text-n-400">
        Domain
      </span>
      <FilterLink href={href({ domain: undefined })} active={!active}>
        All
      </FilterLink>
      {DOMAINS.map((d: Domain) => (
        <FilterLink key={d} href={href({ domain: d })} active={active === d}>
          {DOMAIN_LABEL[d]}
        </FilterLink>
      ))}

      <span className="ml-auto text-2xs uppercase tracking-[0.14em] text-n-400">
        Type
      </span>
      <FilterLink
        href={href({ executable: undefined })}
        active={!executable}
      >
        All
      </FilterLink>
      <FilterLink
        href={href({ executable: "true" })}
        active={executable === "true"}
      >
        Executable
      </FilterLink>
      <FilterLink
        href={href({ executable: "false" })}
        active={executable === "false"}
      >
        Documented
      </FilterLink>
    </nav>
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
    <Link
      href={href}
      aria-current={active ? "true" : undefined}
      className={[
        "no-underline",
        active
          ? "font-semibold text-n-800 underline decoration-accent-500 decoration-2 underline-offset-4"
          : "text-n-500 hover:text-n-700",
      ].join(" ")}
    >
      {children}
    </Link>
  );
}
