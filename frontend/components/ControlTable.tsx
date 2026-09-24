"use client";

import { ArrowRightIcon } from "@phosphor-icons/react";
import { AnimatePresence, motion } from "motion/react";
import Link from "next/link";

import { DOMAIN_LABEL, type ControlSummary } from "@/lib/api";
import { FrameworkBadge } from "./FrameworkBadge";

/**
 * The control library table, the workhorse of the product.
 *
 * v5: 14px body (was 12px), 12/16px cell padding (was 8/12), a 2px ink rule
 * under an inset header band, hairlines between rows and no zebra (zebra plus
 * hairlines was two devices doing one job). Rows answer hover AND keyboard
 * focus with a cobalt bar and tint (`.row-interactive`); they never move.
 *
 * v6: rows fade in and out as the search and filters change. Opacity only:
 * a transform on a <tr> breaks column alignment in some engines.
 *
 * No sticky header: `overflow-x: auto` makes the wrapper a scroll container
 * in both axes, so a sticky thead would stick to the wrapper, not the
 * viewport. 25 rows do not need one.
 */
export function ControlTable({ controls }: { controls: ControlSummary[] }) {
  return (
    <div className="sheet">
      <div className="scroll-x">
        <table className="data-table min-w-[60rem]">
          <thead>
            <tr>
              <th scope="col" className="w-32">Ref</th>
              <th scope="col">Control</th>
              <th scope="col" className="w-44">Domain</th>
              <th scope="col" className="w-36">Legal basis</th>
              <th scope="col" className="w-44">Also maps to</th>
              <th scope="col" className="w-32">Test</th>
            </tr>
          </thead>
          <tbody>
            <AnimatePresence initial={false}>
            {controls.map((control) => (
              <motion.tr
                key={control.ref}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.16 }}
                className={`row-interactive ${control.in_scope ? "" : "text-ink-3"}`}
              >
                <td>
                  <Link
                    href={`/controls/${control.ref}`}
                    className="whitespace-nowrap font-mono font-semibold text-link no-underline hover:underline"
                  >
                    {control.ref}
                  </Link>
                </td>

                <td>
                  <span className={control.in_scope ? "font-medium text-ink" : ""}>
                    {control.title}
                  </span>
                  {(!control.in_scope || control.primary_source_unverified) && (
                    <span className="mt-1 flex flex-wrap gap-2">
                      {!control.in_scope && (
                        <span className="chip border border-dashed border-control text-na">
                          Not applicable
                        </span>
                      )}
                      {control.primary_source_unverified && (
                        <span
                          className="chip border border-dashed border-control text-ink-2"
                          title="The clause this control rests on could not be verified"
                        >
                          Source unverified
                        </span>
                      )}
                    </span>
                  )}
                </td>

                <td className="text-ink-2">{DOMAIN_LABEL[control.domain]}</td>

                <td>
                  {control.primary_clause && (
                    <FrameworkBadge
                      code={control.primary_framework ?? "DPDP"}
                      clauseRef={control.primary_clause}
                      unverified={control.primary_source_unverified}
                    />
                  )}
                </td>

                <td>
                  <span className="flex flex-wrap gap-1">
                    {control.framework_refs
                      .filter((f) => f !== control.primary_framework)
                      .map((f) => (
                        <FrameworkBadge key={f} code={f} unverified />
                      ))}
                  </span>
                </td>

                <td>
                  {control.is_executable ? (
                    <span className="chip bg-cobalt-tint font-mono font-medium text-ink">
                      {control.suite}
                    </span>
                  ) : (
                    <span className="text-meta text-ink-3">Documented</span>
                  )}
                </td>
              </motion.tr>
            ))}
            </AnimatePresence>
          </tbody>
        </table>
      </div>

      {/* Six columns cannot fit a 375px screen; say so, only where it is
          unconditionally true. [a11y swipe-clarity] */}
      <p className="m-0 flex items-center gap-2 border-t border-rule px-4 py-3 text-meta text-ink-2 md:hidden">
        <ArrowRightIcon size={16} weight="bold" aria-hidden />
        Scroll the table sideways for basis and framework mappings.
      </p>
    </div>
  );
}
