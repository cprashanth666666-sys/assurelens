import Link from "next/link";
import { notFound } from "next/navigation";

import { ClauseQuote } from "@/components/ClauseQuote";
import { EvidenceViewer } from "@/components/EvidenceViewer";
import { FrameworkBadge } from "@/components/FrameworkBadge";
import { PageHeader } from "@/components/PageHeader";
import { DOMAIN_LABEL, fetchControl, fetchLatestResult } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function ControlDetailPage({
  params,
}: {
  params: Promise<{ ref: string }>;
}) {
  const { ref } = await params;
  // In parallel: the result does not depend on the control body, and a cold
  // backend should cost one round trip, not two.
  const [control, latest] = await Promise.all([
    fetchControl(ref),
    fetchLatestResult(ref),
  ]);

  if (control === null) notFound();

  const primary = control.clauses.find((c) => c.is_primary);
  const secondary = control.clauses.filter((c) => !c.is_primary);

  return (
    <article className="flex flex-col gap-7">
      <PageHeader
        title={control.title}
        kicker={
          <nav aria-label="Breadcrumb" className="flex flex-wrap items-center gap-2">
            <Link href="/controls" className="link font-medium">
              Control library
            </Link>
            <span aria-hidden="true" className="text-ink-3">/</span>
            <span className="bg-ink px-2 py-[2px] font-mono text-sm font-semibold text-surface">
              {control.ref}
            </span>
          </nav>
        }
      >
        <dl className="ruled m-0 mt-2 grid-cols-1 sm:grid-cols-3">
          <Fact label="Domain" value={DOMAIN_LABEL[control.domain]} />
          <Fact
            label="Inference"
            value={
              control.inference_mode === "CENSUS"
                ? "Census: the test set is the population"
                : "Population: inference from a sample"
            }
          />
          <Fact
            label="Test"
            value={control.is_executable ? `Executable, ${control.suite} suite` : "Documented, not executed"}
          />
        </dl>
      </PageHeader>

      {!control.in_scope && (
        <section className="border-l-4 border-insufficient bg-surface p-5">
          <h3>Not applicable to this engagement</h3>
          <p className="m-0 mt-2 max-w-prose text-base text-ink">{control.na_reason}</p>
          <p className="m-0 mt-3 max-w-prose text-sm text-ink-2">
            The control stays in the library on purpose. An assessor should be
            able to see that the rule was considered and why it does not bind,
            rather than find it silently absent.
          </p>
        </section>
      )}

      <div className="grid gap-7 lg:grid-cols-detail lg:gap-8">
        <div className="flex min-w-0 flex-col gap-7">
          <Section title="Objective">
            <p className="m-0 max-w-prose text-lg leading-prose text-ink">{control.objective}</p>
          </Section>

          <Section title="Procedure performed">
            <p className="m-0 max-w-prose text-base text-ink-2">{control.procedure_text}</p>
          </Section>

          {control.is_executable && (
            <Section title="Latest result">
              <EvidenceViewer latest={latest} />
            </Section>
          )}

          {primary && (
            <Section title="Legal basis">
              <ClauseQuote clause={primary} />
            </Section>
          )}

          {secondary.length > 0 && (
            <Section title="Also maps to">
              <div className="flex flex-col gap-6">
                {secondary.map((c) => (
                  <ClauseQuote key={`${c.framework_code}-${c.ref}`} clause={c} />
                ))}
              </div>
            </Section>
          )}
        </div>

        <aside className="flex min-w-0 flex-col gap-5">
          <Aside title="Test">
            {control.is_executable ? (
              <dl className="m-0 grid grid-cols-[auto_1fr] gap-x-4 gap-y-3 text-sm">
                <Dt>Suite</Dt>
                <Dd>{control.suite}</Dd>
                <Dt>Procedure</Dt>
                <Dd>{control.plugin_key}</Dd>
                <Dt>Evidence</Dt>
                <Dd>{evidenceNames(control.evidence_contract).join(", ") || "none declared"}</Dd>
              </dl>
            ) : (
              <p className="m-0 text-sm text-ink-2">
                Documented, not executed in this release. It resolves to
                insufficient evidence under G4, the honest state for a control
                that has not been tested.
              </p>
            )}
          </Aside>

          <Aside title="Frameworks">
            <div className="flex flex-wrap gap-2">
              {control.clauses.map((c) => (
                <FrameworkBadge
                  key={`${c.framework_code}-${c.ref}`}
                  code={c.framework_code}
                  clauseRef={c.ref}
                  unverified={c.source_status === "UNVERIFIED"}
                />
              ))}
            </div>
          </Aside>

          <Aside title="Provenance">
            <dl className="m-0 grid grid-cols-[auto_1fr] gap-x-4 gap-y-3 text-sm">
              <Dt>Source</Dt>
              <Dd>{control.yaml_source}</Dd>
              <Dt>Evidence owner</Dt>
              <Dd>{control.evidence_owner ?? "not recorded"}</Dd>
              <Dt>Thresholds</Dt>
              <Dd>
                {Object.keys(control.threshold_overrides).length === 0
                  ? "Engine defaults"
                  : JSON.stringify(control.threshold_overrides)}
              </Dd>
            </dl>
          </Aside>
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

/** A section of the main column: a 2px ink rule, then a real heading. */
function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="section-rule">
      <h3>{title}</h3>
      <div className="mt-4">{children}</div>
    </section>
  );
}

/** A reference block in the side column: white sheet, inset heading band. */
function Aside({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="sheet">
      <h3 className="border-b border-rule bg-inset px-4 py-3 text-base">{title}</h3>
      <div className="p-4">{children}</div>
    </section>
  );
}

function Fact({ label, value }: { label: string; value: string }) {
  return (
    <div className="px-4 py-3">
      <dt className="label">{label}</dt>
      <dd className="m-0 mt-1 text-sm font-semibold text-ink">{value}</dd>
    </div>
  );
}

const Dt = ({ children }: { children: React.ReactNode }) => (
  <dt className="text-ink-3">{children}</dt>
);

const Dd = ({ children }: { children: React.ReactNode }) => (
  <dd className="m-0 break-words font-mono text-ink">{children}</dd>
);
