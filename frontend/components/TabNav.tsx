"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useRef } from "react";

/**
 * Six destinations do not need a sidebar. A ruled rail of full-height cells,
 * sticky under the masthead; the active cell is a lime block with an ink
 * foot (`.tab` in globals.css). [DESIGN.md 4]
 *
 * On a narrow screen the rail scrolls the active tab into view on navigation
 * and fades at both edges, so "Report" is discoverable on a 375px phone.
 * [a11y nav-state-active, horizontal-scroll]
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
  const railRef = useRef<HTMLDivElement>(null);
  const navRef = useRef<HTMLElement>(null);

  useEffect(() => {
    const rail = railRef.current;
    if (!rail) return;

    const active = rail.querySelector<HTMLElement>('[aria-current="page"]');
    if (!active) return;

    // Only worth doing when the rail actually overflows; on a desktop this
    // would be a no-op scroll that steals focus position for nothing.
    if (rail.scrollWidth <= rail.clientWidth + 4) return;

    const target =
      active.offsetLeft - rail.clientWidth / 2 + active.offsetWidth / 2;

    rail.scrollTo({
      left: Math.max(0, target),
      behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches
        ? "auto"
        : "smooth",
    });
  }, [pathname]);

  /** Publish the rail height too, so sticky table headers can sit under the
   * whole chrome stack rather than under a guess. See Masthead. */
  useEffect(() => {
    const node = navRef.current;
    if (!node || typeof ResizeObserver === "undefined") return;

    const publish = () => {
      document.documentElement.style.setProperty(
        "--tabnav-h",
        `${Math.round(node.getBoundingClientRect().height)}px`,
      );
    };

    const observer = new ResizeObserver(publish);
    observer.observe(node);
    publish();

    return () => observer.disconnect();
  }, []);

  return (
    <nav
      aria-label="Sections"
      ref={navRef}
      style={{ top: "var(--masthead-h, 64px)" }}
      className="sticky z-30 border-b-2 border-rule-strong bg-surface"
    >
      <div ref={railRef} className="scroll-x edge-fade mx-auto max-w-content md:px-6">
        <ul className="m-0 flex list-none divide-x divide-rule p-0 md:border-x md:border-rule">
          {TABS.map((tab) => {
            const active =
              tab.href === "/" ? pathname === "/" : pathname.startsWith(tab.href);

            return (
              <li key={tab.href}>
                <Link
                  href={tab.href}
                  aria-current={active ? "page" : undefined}
                  className="tab"
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
