import Link from "next/link";
import { notFound } from "next/navigation";

import { ClauseQuote } from "@/components/ClauseQuote";
import { FrameworkBadge } from "@/components/FrameworkBadge";
import { DOMAIN_LABEL, fetchControl } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function ControlDetailPage({
  params,
}: {
  params: Promise<{ ref: string }>;
}) {
  const { ref } = await params;
  const control = await fetchControl(ref);

  if (control === null) notFound();

  const primary = control.clauses.find((c) => c.is_primary);
  const secondary = control.clauses.filter((c) => !c.is_primary);

  return (
    <article className="flex flex-col gap-5">
      <nav className="text-xs">
        <Link href="/controls" className="text-accent-600 no-underline hover:underline">
          Control library
        </Link>
        <span className="mx-2 text-n-300">/</span>
        <span className="font-mono text-n-500">{control.ref}</span>
      </nav>

      <header>
        <h2>{control.title}</h2>
        <p className="m-0 mt-2 text-xs text-n-500">
          {DOMAIN_LABEL[control.domain]} &middot;{" "}
          {control.inference_mode === "CENSUS"
            ? "Census — the test set is the population"
            : "Population — inference from a sample"}
        </p>
      </header>

      {!control.in_scope && (
        <section className="border border-n-200 bg-n-50 p-4">
          <h3 className="text-2xs uppercase tracking-[0.14em] text-n-500">
            Not applicable to this engagement
          </h3>
          <p className="m-0 mt-2 max-w-prose text-sm text-n-700">
            {control.na_reason}
          </p>
          <p className="m-0 mt-3 text-xs text-n-500">
            The control stays in the library on purpose. An assessor should be
            able to see that the rule was considered and why it does not bind,
            rather than find it silently absent.
          </p>
        </section>
      )}

      <div className="grid gap-5 lg:grid-cols-detail">
        <div className="flex flex-col gap-5">
          <Panel title="Objective">
            <p className="m-0 max-w-prose text-base leading-prose text-n-700">
              {control.objective}
            </p>
          </Panel>

          <Panel title="Procedure performed">
            <p className="m-0 max-w-prose text-base leading-prose text-n-700">
              {control.procedure_text}
            </p>
          </Panel>

          {primary && (
            <Panel title="Legal basis">
              <ClauseQuote clause={primary} />
            </Panel>
          )}

          {secondary.length > 0 && (
            <Panel title="Also maps to">
              <div className="flex flex-col gap-5">
                {secondary.map((c) => (
                  <ClauseQuote key={`${c.framework_code}-${c.ref}`} clause={c} />
                ))}
              </div>
            </Panel>
          )}
        </div>

        <aside className="flex flex-col gap-5">
          <Panel title="Test">
            {control.is_executable ? (
              <dl className="m-0 grid grid-cols-[auto_1fr] gap-x-4 gap-y-2 text-xs">
                <Dt>Suite</Dt>
                <Dd>{control.suite}</Dd>
                <Dt>Procedure</Dt>
                <Dd>{control.plugin_key}</Dd>
                <Dt>Evidence</Dt>
                <Dd>
                  {evidenceNames(control.evidence_contract).join(", ") || "—"}
                </Dd>
              </dl>
            ) : (
              <p className="m-0 text-sm text-n-600">
                Documented, not executed in this release. It resolves to
                insufficient evidence under G4 — the honest state for a control
                that has not been tested.
              </p>
            )}
          </Panel>

          <Panel title="Frameworks">
            <div className="flex flex-wrap gap-1">
              {control.clauses.map((c) => (
                <FrameworkBadge
                  key={`${c.framework_code}-${c.ref}`}
                  code={c.framework_code}
                  clauseRef={c.ref}
                  unverified={c.source_status === "UNVERIFIED"}
                />
              ))}
            </div>
          </Panel>

          <Panel title="Provenance">
            <dl className="m-0 grid grid-cols-[auto_1fr] gap-x-4 gap-y-2 text-xs">
              <Dt>Source</Dt>
              <Dd>{control.yaml_source}</Dd>
              <Dt>Evidence owner</Dt>
              <Dd>{control.evidence_owner ?? "—"}</Dd>
              <Dt>Thresholds</Dt>
              <Dd>
                {Object.keys(control.threshold_overrides).length === 0
                  ? "Engine defaults"
                  : JSON.stringify(control.threshold_overrides)}
              </Dd>
            </dl>
          </Panel>
        </aside>
      </div>
    </article>
  );
}

function evidenceNames(contract: Record<string, unknown> | null): string[] {
  const required = contract?.required;
  if (!Array.isArray(required)) return [];
  return required
    .map((item) =>
      typeof item === "object" && item !== null && "name" in item
        ? String((item as { name: unknown }).name)
        : null,
    )
    .filter((n): n is string => n !== null);
}

function Panel({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section className="panel p-4">
      <h3 className="text-2xs uppercase tracking-[0.14em] text-n-400">
        {title}
      </h3>
      <div className="mt-3">{children}</div>
    </section>
  );
}

const Dt = ({ children }: { children: React.ReactNode }) => (
  <dt className="text-n-500">{children}</dt>
);

const Dd = ({ children }: { children: React.ReactNode }) => (
  <dd className="m-0 font-mono text-n-800">{children}</dd>
);
