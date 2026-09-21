"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

/**
 * Six destinations do not need a sidebar, and a sidebar is the SaaS reflex.
 * Tabs with a 2px bottom rule on the active item. No pills. [UX 3]
 */

const TABS = [
  { href: "/", label: "Overview" },
  { href: "/controls", label: "Controls" },
  { href: "/runs", label: "Test Runs" },
  { href: "/findings", label: "Findings" },
  { href: "/roadmap", label: "Roadmap" },
  { href: "/report", label: "Report" },
] as const;

export function TabNav() {
  const pathname = usePathname();

  return (
    <nav
      aria-label="Sections"
      className="border-b border-n-200 bg-n-0"
    >
      <div className="mx-auto max-w-content scroll-x px-4">
        <ul className="flex list-none gap-6 p-0">
          {TABS.map((tab) => {
            const active =
              tab.href === "/"
                ? pathname === "/"
                : pathname.startsWith(tab.href);

            return (
              <li key={tab.href}>
                <Link
                  href={tab.href}
                  aria-current={active ? "page" : undefined}
                  className={[
                    "-mb-px inline-block whitespace-nowrap border-b-2 py-3 text-sm no-underline",
                    active
                      ? "border-accent-500 font-semibold text-n-800"
                      : "border-transparent text-n-500 hover:text-n-700",
                  ].join(" ")}
                >
                  {tab.label}
                </Link>
              </li>
            );
          })}
        </ul>
      </div>
    </nav>
  );
}
