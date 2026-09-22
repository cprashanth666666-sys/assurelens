"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useRef } from "react";

/**
 * Six destinations do not need a sidebar, and a sidebar is the SaaS reflex.
 * Tabs with a 2px rule on the active item. No pills. [UX 3]
 *
 * v2.0 adds three things, each of which is a behaviour rather than a
 * decoration:
 *
 * * The rail is **sticky under the masthead**, so navigation survives a long
 *   table. `top` is bound to the masthead's condensed height.
 * * The active rule is **drawn by CSS scaleX** (`.tab` in globals.css), and a
 *   terracotta rule wipes in on hover. No measuring, no layout reads, so it
 *   cannot desynchronise from the DOM the way a positioned indicator does.
 * * On a narrow screen the rail **scrolls the active tab into view** on
 *   navigation and fades at both edges, so "Report" is discoverable on a
 *   375px phone instead of sitting silently off-screen.
 *   [a11y nav-state-active, horizontal-scroll]
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
      className="sticky z-30 border-b border-n-200 bg-veil backdrop-blur-md"
    >
      <div
        ref={railRef}
        className="scroll-x edge-fade mx-auto max-w-content px-4 md:px-5"
      >
        <ul className="flex list-none gap-5 p-0 md:gap-6">
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
                    "tab -mb-px inline-block whitespace-nowrap py-3 text-sm no-underline",
                    "transition-colors duration-base ease-out",
                    active
                      ? "font-semibold text-n-800"
                      : "text-n-500 hover:text-n-800",
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
