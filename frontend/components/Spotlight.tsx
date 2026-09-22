"use client";

import { useCallback, useEffect, useRef } from "react";

/**
 * A soft tint that tracks the cursor across a panel.
 *
 * The whole effect lives in CSS (`.spotlight` in globals.css); this component
 * does nothing but publish the pointer position as two custom properties.
 * That division matters:
 *
 * * `pointermove` fires at display rate. Writing a style on every event is a
 *   layout read inside an input handler — the classic way to lose 60fps.
 *   Coordinates are stashed and both the measure and the write happen once
 *   per frame in `flush`. [a11y main-thread-budget]
 * * There is no scroll or resize listener. The rect is re-read inside that
 *   same rAF, so it is never stale by more than a frame, and it costs
 *   nothing at all unless the pointer is moving over this element.
 * * Custom-property writes do not invalidate layout, only paint.
 *
 * Fine pointers only. On a touchscreen the CSS hover query never matches, so
 * the tint stays at zero opacity and this listener is the only cost — which
 * is why it also bails out early under `pointer: coarse`.
 */
export function Spotlight({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const rect = useRef<DOMRect | null>(null);
  const point = useRef({ x: 0, y: 0 });
  const frame = useRef<number | null>(null);

  const flush = useCallback(() => {
    frame.current = null;
    const node = ref.current;
    if (!node) return;

    // Measured HERE, inside the rAF, rather than in a scroll handler.
    //
    // The first version listened to `scroll` and called
    // getBoundingClientRect() on every event — a forced layout on every
    // scroll frame, on a page that already has two other scroll listeners,
    // and it fired whether or not the pointer was anywhere near this panel.
    // That is precisely the cost this component was written to avoid.
    //
    // Doing it in the flush bounds it to once per frame AND only while the
    // pointer is actually moving over the element, which is the only time
    // the value is used.
    rect.current = node.getBoundingClientRect();
    const box = rect.current;
    if (box.width === 0) return;

    const x = ((point.current.x - box.left) / box.width) * 100;
    const y = ((point.current.y - box.top) / box.height) * 100;
    node.style.setProperty("--mx", `${x.toFixed(2)}%`);
    node.style.setProperty("--my", `${y.toFixed(2)}%`);
  }, []);

  useEffect(() => {
    const node = ref.current;
    if (!node) return;

    if (
      typeof window.matchMedia === "function" &&
      !window.matchMedia("(hover: hover) and (pointer: fine)").matches
    ) {
      return;
    }

    const onMove = (event: PointerEvent) => {
      point.current = { x: event.clientX, y: event.clientY };
      if (frame.current === null) {
        frame.current = requestAnimationFrame(flush);
      }
    };

    // One listener. No scroll or resize subscription is needed, because the
    // rect is re-read inside the rAF flush and is therefore never stale by
    // more than a frame.
    node.addEventListener("pointermove", onMove);

    return () => {
      node.removeEventListener("pointermove", onMove);
      if (frame.current !== null) cancelAnimationFrame(frame.current);
    };
  }, [flush]);

  return (
    <div ref={ref} className={`spotlight ${className}`}>
      {children}
    </div>
  );
}
