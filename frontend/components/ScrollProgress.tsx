"use client";

import { useEffect, useRef } from "react";

/**
 * A 2px rule across the top of the window showing how far down the document
 * the reader is.
 *
 * This earns its place rather than decorating: the control library is a
 * 25-row table and a run result is longer still, and on a phone — where the
 * scrollbar is a transient overlay or absent — there is otherwise no cue for
 * how much is left. It is the scroll equivalent of a page number.
 *
 * Written as a `scaleX` on a custom property, so each scroll event costs a
 * paint and nothing else. Updated on a rAF, never directly in the handler.
 */
export function ScrollProgress() {
  const ref = useRef<HTMLDivElement>(null);
  const frame = useRef<number | null>(null);

  useEffect(() => {
    const node = ref.current;
    if (!node) return;

    const update = () => {
      frame.current = null;
      const scrollable =
        document.documentElement.scrollHeight - window.innerHeight;

      // A page shorter than the viewport has no progress to report. Hiding
      // the rule is more honest than pinning it to 100%.
      if (scrollable <= 8) {
        node.style.setProperty("--progress", "0");
        node.hidden = true;
        return;
      }

      node.hidden = false;
      const ratio = Math.min(1, Math.max(0, window.scrollY / scrollable));
      node.style.setProperty("--progress", ratio.toFixed(4));
    };

    const onScroll = () => {
      if (frame.current === null) frame.current = requestAnimationFrame(update);
    };

    update();
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll, { passive: true });

    return () => {
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", onScroll);
      if (frame.current !== null) cancelAnimationFrame(frame.current);
    };
  }, []);

  return (
    <div
      ref={ref}
      className="scroll-progress"
      aria-hidden="true"
      hidden
    />
  );
}
