import Link from "next/link";

import { DOMAIN_LABEL, type ControlSummary } from "@/lib/api";
import { FrameworkBadge } from "./FrameworkBadge";

/**
 * The dense table is the workhorse of this product. Auditors read tables.
 *
 * Zebra striping, hairline rules, tabular figures. Still no hover lift, no
 * scale transform, no card grid: a row that moves breaks the column
 * alignment that makes a table readable in the first place. [UX 4.2]
 *
 * What v2.0 adds is a row that ANSWERS the cursor without moving — a
 * terracotta rule wipes in at the left edge and the row takes a faint accent
 * tint (`.row-interactive`). It also answers the keyboard: the rule appears
 * on `:focus-within` too, so tabbing through 25 control links tracks the
 * same way the mouse does. [a11y focus-states]
 *
 * No sticky header, deliberately. `overflow-x: auto` on the wrapper makes it
 * a scroll container in BOTH axes, so a `position: sticky` thead would
 * resolve against the wrapper rather than the viewport and simply never
 * stick. The workarounds are fragile; 25 rows do not need one.
 */
export function ControlTable({ controls }: { controls: ControlSummary[] }) {
  return (
    <div className="panel overflow-hidden">
      <div className="scroll-x">
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
                  "row-interactive border-b border-n-100 align-top",
                  i % 2 === 1 ? "bg-n-25" : "",
                  control.in_scope ? "" : "text-n-400",
                ].join(" ")}
              >
                <Td>
                  <Link
                    href={`/controls/${control.ref}`}
                    className="link-grow whitespace-nowrap font-mono text-accent-600 no-underline transition-colors duration-base ease-out hover:text-accent-700"
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

      {/* Six columns cannot fit a 375px screen, and a table that is cut off
          with no affordance reads as broken rather than scrollable. Shown
          only below the breakpoint where it is unconditionally true, so it
          is never a lie. [a11y swipe-clarity] */}
      <p className="m-0 flex items-center gap-2 border-t border-n-100 px-3 py-2 text-2xs text-n-500 md:hidden">
        <svg viewBox="0 0 16 10" width="16" height="10" aria-hidden="true" fill="none">
          <path
            d="M1 5h14M11 1.5 14.5 5 11 8.5"
            stroke="currentColor"
            strokeWidth="1.2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
        Scroll the table sideways for basis and framework mappings.
      </p>
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
