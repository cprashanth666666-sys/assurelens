import Link from "next/link";

import { DOMAIN_LABEL, type ControlSummary } from "@/lib/api";
import { FrameworkBadge } from "./FrameworkBadge";

/**
 * The dense table is the workhorse of this product. Auditors read tables.
 *
 * Zebra striping, hairline rules, sticky header, tabular figures. No hover
 * lift, no scale transform, no card grid. [UX 4.2]
 */
export function ControlTable({ controls }: { controls: ControlSummary[] }) {
  return (
    <div className="scroll-x border border-n-200 bg-n-0">
      <table className="w-full border-collapse text-xs leading-table">
        <thead>
          <tr className="border-b border-n-200 bg-n-50 text-left">
            <Th className="w-32">Ref</Th>
            <Th>Control</Th>
            <Th className="w-40">Domain</Th>
            <Th className="w-32">Basis</Th>
            <Th className="w-44">Also maps to</Th>
            <Th className="w-24">Test</Th>
          </tr>
        </thead>
        <tbody>
          {controls.map((control, i) => (
            <tr
              key={control.ref}
              className={[
                "border-b border-n-100 align-top",
                i % 2 === 1 ? "bg-n-25" : "",
                control.in_scope ? "" : "text-n-400",
              ].join(" ")}
            >
              <Td>
                <Link
                  href={`/controls/${control.ref}`}
                  className="whitespace-nowrap font-mono text-accent-600 no-underline hover:underline"
                >
                  {control.ref}
                </Link>
              </Td>

              <Td>
                <span className={control.in_scope ? "text-n-800" : ""}>
                  {control.title}
                </span>
                {!control.in_scope && (
                  <span className="ml-2 text-2xs uppercase tracking-[0.14em] text-n-500">
                    Not applicable
                  </span>
                )}
                {control.primary_source_unverified && (
                  <span
                    className="ml-2 text-2xs uppercase tracking-[0.14em] text-n-500"
                    title="The clause this control rests on could not be verified"
                  >
                    Source unverified
                  </span>
                )}
              </Td>

              <Td className="text-n-600">{DOMAIN_LABEL[control.domain]}</Td>

              <Td>
                {control.primary_clause && (
                  <FrameworkBadge
                    code={control.primary_framework ?? "DPDP"}
                    clauseRef={control.primary_clause}
                    unverified={control.primary_source_unverified}
                  />
                )}
              </Td>

              <Td>
                <span className="flex flex-wrap gap-1">
                  {control.framework_refs
                    .filter((f) => f !== control.primary_framework)
                    .map((f) => (
                      <FrameworkBadge key={f} code={f} unverified />
                    ))}
                </span>
              </Td>

              <Td className="text-n-600">
                {control.is_executable ? (
                  <span className="font-mono text-2xs">{control.suite}</span>
                ) : (
                  <span className="text-2xs uppercase tracking-[0.14em] text-n-400">
                    Documented
                  </span>
                )}
              </Td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Th({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <th
      scope="col"
      className={`px-3 py-2 text-2xs font-semibold uppercase tracking-[0.14em] text-n-500 ${className}`}
    >
      {children}
    </th>
  );
}

function Td({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return <td className={`px-3 py-2 ${className}`}>{children}</td>;
}
