"use client";

import { useEffect, useRef, useState, useSyncExternalStore } from "react";

import { ENGAGEMENT } from "@/lib/engagement";
import { RoleSwitch } from "./RoleSwitch";

/**
 * A masthead, not a nav bar: the entity name carries the weight and the
 * product name is secondary, because a workpaper is headed by whose it is.
 * [UX 3]
 *
 * v2.0 makes it sticky and condensing. On scroll the vertical padding halves
 * and a translucent backdrop comes in — so on a phone, where the control
 * table is longer than four screens, the engagement it belongs to never
 * leaves the frame. The condense is padding and background only; nothing
 * moves horizontally and no text resizes, because a heading that shrinks
 * under the cursor is a gimmick.
 */
export function Masthead() {
  const [condensed, setCondensed] = useState(false);
  const ref = useRef<HTMLElement>(null);

  useEffect(() => {
    let frame: number | null = null;

    const update = () => {
      frame = null;
      setCondensed(window.scrollY > 24);
    };

    const onScroll = () => {
      if (frame === null) frame = requestAnimationFrame(update);
    };

    update();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => {
      window.removeEventListener("scroll", onScroll);
      if (frame !== null) cancelAnimationFrame(frame);
    };
  }, []);

  /**
   * Publish the masthead's real height so the tab rail can stick directly
   * beneath it and the table headers below that.
   *
   * The alternative is a hardcoded `top-[57px]`, which is a guess that is
   * wrong the moment the type scale, the deadline line or the wrap point
   * changes — and wrong quietly, as a 4px gap of scrolling content showing
   * through between two sticky bars. Measuring costs one ResizeObserver.
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
    <header
      ref={ref}
      data-condensed={condensed ? "true" : "false"}
      className={[
        "sticky top-0 z-40 border-b transition-all duration-base ease-out",
        condensed
          ? "border-n-200 bg-scrim shadow-raise backdrop-blur-md"
          : "border-n-100 bg-veil backdrop-blur-sm",
      ].join(" ")}
    >
      <div
        className={[
          "mx-auto flex max-w-content flex-wrap items-end justify-between gap-x-4 gap-y-2 px-4 transition-all duration-base ease-out md:px-5",
          condensed ? "py-2" : "py-3 md:py-4",
        ].join(" ")}
      >
        {/* At rest on a phone the identity block takes the whole row, so the
            client name wraps at a sensible measure instead of being squeezed
            into five two-word lines beside the date. Once condensed it shares
            the row with the role switch, because by then it is truncated to
            one line anyway. */}
        <div
          className={[
            "flex min-w-0 items-end gap-3 md:flex-1 md:basis-auto",
            condensed ? "flex-1" : "basis-full",
          ].join(" ")}
        >
          <Aperture condensed={condensed} />

          <div className="min-w-0">
            <p className="m-0 text-2xs uppercase tracking-[0.18em] text-n-400">
              AssureLens
            </p>
            {/* Condensed on a phone, the client name is clamped to one line.
                Two lines of 20px heading plus a tab rail is half an iPhone
                viewport spent on chrome before any content appears. */}
            <h1
              className={[
                "mt-1 text-md md:text-lg",
                condensed ? "truncate md:overflow-visible md:whitespace-normal" : "",
              ].join(" ")}
              title={ENGAGEMENT.organisation}
            >
              {ENGAGEMENT.organisation}
            </h1>
            {/* The sub-line is the first thing to go when space is tight. */}
            <p
              className={[
                "m-0 overflow-hidden text-xs text-n-500 transition-all duration-base ease-out",
                condensed ? "max-h-0 opacity-0" : "mt-1 max-h-5 opacity-100",
              ].join(" ")}
            >
              {ENGAGEMENT.engagementName} &middot; {ENGAGEMENT.city}
            </p>
          </div>
        </div>

        <div className="flex shrink-0 items-end gap-4 md:gap-5">
          {/* On a phone the statutory date is reference, not navigation, so
              it is what goes when the header condenses. On a desktop there
              is room for it either way. */}
          <div className={condensed ? "hidden md:block" : ""}>
            <Deadline />
          </div>
          <RoleSwitch />
        </div>
      </div>
    </header>
  );
}

/**
 * The mark: an aperture of four blades, drawn not imported. A lens is the
 * one metaphor this product is entitled to, and a geometric mark stays in
 * the palette where an icon-set glyph would not.
 *
 * It rotates 45° when the masthead condenses — a state change with a cause,
 * which is the only kind of motion the brief allows. [UX 7.1]
 */
function Aperture({ condensed }: { condensed: boolean }) {
  return (
    <svg
      viewBox="0 0 32 32"
      width="26"
      height="26"
      aria-hidden="true"
      className="shrink-0 transition-transform duration-slow ease-out"
      style={{ transform: condensed ? "rotate(45deg)" : "none" }}
    >
      <circle
        cx="16"
        cy="16"
        r="14"
        fill="none"
        stroke="var(--n-300)"
        strokeWidth="1.25"
      />
      {[0, 90, 180, 270].map((angle) => (
        <path
          key={angle}
          d="M16 16 L16 3 A13 13 0 0 1 27.3 9.5 Z"
          fill={angle % 180 === 0 ? "var(--accent-600)" : "var(--warm-500)"}
          opacity={angle % 180 === 0 ? 0.92 : 0.6}
          transform={`rotate(${angle} 16 16)`}
        />
      ))}
      <circle cx="16" cy="16" r="4.2" fill="var(--n-0)" />
    </svg>
  );
}

/**
 * The statutory clock.
 *
 * The date is server-rendered; the day count is filled in after mount. That
 * split is deliberate — "days remaining" depends on the reader's clock, and
 * computing it during SSR produces a number that is wrong for anyone in
 * another timezone and triggers a hydration mismatch besides. The date alone
 * is always correct, so it is what ships in the HTML.
 */
const DEADLINE_MS = Date.parse(`${ENGAGEMENT.complianceDeadline}T00:00:00Z`);

/** Never resubscribes: the count is read once per render, not pushed. */
const noSubscribe = () => () => {};

function daysRemaining(): number {
  return Math.max(0, Math.ceil((DEADLINE_MS - Date.now()) / 86_400_000));
}

function Deadline() {
  /**
   * useSyncExternalStore rather than setState-in-an-effect, because the
   * reader's clock IS an external store. It gives the server snapshot
   * (`null`) and the client snapshot (`daysRemaining()`) separate slots, so
   * the count appears after hydration with no mismatch and no extra render
   * pass. Rounding to whole days makes the snapshot stable across renders,
   * which is what the hook requires.
   */
  const days = useSyncExternalStore(noSubscribe, daysRemaining, () => null);

  return (
    <div className="text-right">
      <p className="m-0 text-2xs uppercase tracking-[0.18em] text-n-400">
        <span className="md:hidden">Commences</span>
        <span className="hidden md:inline">Obligations commence</span>
      </p>
      {/* One line on a phone, two on a desktop. The date and the count say
          the same thing; stacking them is a desktop luxury. */}
      <p className="m-0 mt-1 flex items-baseline justify-end gap-2 font-mono text-sm text-n-700 md:block">
        <span>{ENGAGEMENT.complianceDeadline}</span>
        <span
          className="text-2xs text-warm-600 transition-opacity duration-slow ease-out md:mt-1 md:block"
          style={{ opacity: days === null ? 0 : 1 }}
        >
          {days === null ? " " : `${days.toLocaleString()} days`}
        </span>
      </p>
    </div>
  );
}
