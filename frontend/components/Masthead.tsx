"use client";

import { useEffect, useRef } from "react";

import { ENGAGEMENT } from "@/lib/engagement";
import { DeadlineCount } from "./DeadlineCount";
import { RoleSwitch } from "./RoleSwitch";

/**
 * The masthead: a flat cobalt band, headed by whose engagement this is.
 * [DESIGN.md 4]
 *
 * v5 drops the v2-v4 condense-on-scroll. It needed a window scroll listener
 * and animated padding (a layout on every frame, UX_BRIEF 13.9), and bought a
 * few pixels. The band is now one fixed, compact height at every scroll
 * position, and on a phone it is two short rows rather than a shrinking one.
 */
export function Masthead() {
  const ref = useRef<HTMLElement>(null);

  /**
   * Publish the real height so the tab rail sticks directly beneath it. A
   * hardcoded `top` is a guess that fails quietly, as a strip of scrolling
   * content showing between two sticky bars.
   */
  useEffect(() => {
    const node = ref.current;
    if (!node || typeof ResizeObserver === "undefined") return;

    const publish = () => {
      document.documentElement.style.setProperty(
        "--masthead-h",
        `${Math.round(node.getBoundingClientRect().height)}px`,
      );
    };

    const observer = new ResizeObserver(publish);
    observer.observe(node);
    publish();
    return () => observer.disconnect();
  }, []);

  return (
    <header ref={ref} className="sticky top-0 z-40 bg-cobalt text-on-cobalt">
      <div className="mx-auto flex max-w-content flex-wrap items-center gap-x-6 gap-y-3 px-4 py-3 md:px-6">
        {/* On a phone the identity takes the whole first row so the client
            name is never squeezed beside the role switch. */}
        <div className="flex min-w-0 basis-full items-center gap-3 md:flex-1 md:basis-0">
          <Aperture />
          <div className="min-w-0">
            <p className="m-0 flex items-baseline gap-2 text-sm font-semibold leading-tight">
              <span>AssureLens</span>
              <span aria-hidden="true" className="text-on-cobalt-2">/</span>
              <span className="truncate font-medium text-on-cobalt-2">
                {ENGAGEMENT.engagementName}
              </span>
            </p>
            <h1
              className="m-0 mt-1 truncate text-lg font-semibold tracking-head text-on-cobalt"
              title={ENGAGEMENT.organisation}
            >
              {ENGAGEMENT.organisation}
            </h1>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <Deadline />
          <RoleSwitch />
        </div>
      </div>
    </header>
  );
}

/**
 * The mark: four aperture blades, the one metaphor this product is entitled
 * to. White and lime on the cobalt band. Static.
 */
function Aperture() {
  return (
    <svg viewBox="0 0 32 32" width="32" height="32" aria-hidden="true" className="shrink-0">
      {[0, 90, 180, 270].map((angle) => (
        <path
          key={angle}
          d="M16 16 L16 2 A14 14 0 0 1 28.1 9 Z"
          fill={angle % 180 === 0 ? "var(--lime)" : "var(--on-cobalt)"}
          transform={`rotate(${angle} 16 16)`}
        />
      ))}
      <circle cx="16" cy="16" r="4.5" fill="var(--cobalt)" />
    </svg>
  );
}

/** The statutory clock: date server-rendered, day count after hydration. */
function Deadline() {
  return (
    <p
      className="m-0 hidden items-center gap-2 bg-lime px-3 py-2 font-mono text-sm font-medium text-on-lime sm:flex"
      title="DPDP Rules obligations commence"
    >
      <span className="font-sans text-meta font-semibold">Commences</span>
      <span>{ENGAGEMENT.complianceDeadline}</span>
      <span aria-hidden="true">/</span>
      <DeadlineCount suffix=" days" />
    </p>
  );
}
