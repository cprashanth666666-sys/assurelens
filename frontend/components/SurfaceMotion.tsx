"use client";

import { useEffect } from "react";

/**
 * Makes every `[data-tilt]` tile rise and tilt toward the pointer -- mouse
 * on a desktop, finger on a phone or tablet. [UX 12.4]
 *
 * One component, mounted once in the layout, using event delegation on the
 * document. The alternative -- a client wrapper around every card -- would
 * turn server-rendered tiles into client components just to listen for a
 * pointer, and ship that JavaScript for every card on every page.
 *
 * Mouse: the tile follows the cursor while it is over it, and settles when
 * it leaves.
 * Touch: a press lifts and tilts the tile toward the contact point, and
 * release settles it. A press that turns into a scroll arrives as
 * `pointercancel`, which also settles it, so dragging a list never leaves a
 * card stuck mid-tilt. Nothing here calls preventDefault: scrolling, links
 * and taps behave exactly as they would without it.
 *
 * Performance: the pointer position is stashed and applied once per
 * animation frame, and the tile's rect is read inside that same frame, not
 * in the event handler. Only CSS custom properties are written, which the
 * stylesheet turns into a `transform` -- no layout, no reflow.
 *
 * Under prefers-reduced-motion nothing is attached at all.
 */
export function SurfaceMotion() {
  useEffect(() => {
    if (
      typeof window.matchMedia === "function" &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches
    ) {
      return;
    }

    const maxTilt = 6; // degrees; mirrors --tilt-max
    let active: HTMLElement | null = null;
    let point = { x: 0, y: 0 };
    let frame: number | null = null;

    const apply = () => {
      frame = null;
      const tile = active;
      if (!tile) return;

      const box = tile.getBoundingClientRect();
      if (box.width === 0 || box.height === 0) return;

      // -0.5 .. 0.5 across the tile, clamped so a pointer that has just
      // left the edge cannot over-rotate it.
      const px = Math.min(0.5, Math.max(-0.5, (point.x - box.left) / box.width - 0.5));
      const py = Math.min(0.5, Math.max(-0.5, (point.y - box.top) / box.height - 0.5));

      // Wide tiles tilt less. Rotation moves an edge by width * sin(angle),
      // so 6 degrees swings a 700px panel's edges nearly 40px -- enough to
      // make its text swim. Scaling to width keeps the edge travel roughly
      // constant whatever the tile's size.
      const tilt = maxTilt * Math.min(1, 360 / box.width);

      tile.style.setProperty("--ry", `${(px * 2 * tilt).toFixed(2)}deg`);
      tile.style.setProperty("--rx", `${(-py * 2 * tilt).toFixed(2)}deg`);
      tile.style.setProperty("--gx", `${((px + 0.5) * 100).toFixed(1)}%`);
      tile.style.setProperty("--gy", `${((py + 0.5) * 100).toFixed(1)}%`);
    };

    const schedule = () => {
      if (frame === null) frame = requestAnimationFrame(apply);
    };

    const settle = (tile: HTMLElement | null) => {
      if (!tile) return;
      tile.removeAttribute("data-active");
      tile.style.removeProperty("--rx");
      tile.style.removeProperty("--ry");
    };

    const activate = (tile: HTMLElement, event: PointerEvent) => {
      if (active && active !== tile) settle(active);
      active = tile;
      tile.setAttribute("data-active", "true");
      point = { x: event.clientX, y: event.clientY };
      schedule();
    };

    const tileFrom = (target: EventTarget | null): HTMLElement | null =>
      target instanceof Element ? target.closest<HTMLElement>("[data-tilt]") : null;

    const onMove = (event: PointerEvent) => {
      if (event.pointerType !== "mouse") return; // touch tilts on press only
      const tile = tileFrom(event.target);
      if (!tile) {
        if (active) settle(active);
        active = null;
        return;
      }
      activate(tile, event);
    };

    const onDown = (event: PointerEvent) => {
      if (event.pointerType === "mouse") return;
      const tile = tileFrom(event.target);
      if (tile) activate(tile, event);
    };

    const onRelease = (event: PointerEvent) => {
      if (event.pointerType === "mouse") return;
      settle(active);
      active = null;
    };

    const onLeaveWindow = () => {
      settle(active);
      active = null;
    };

    document.addEventListener("pointermove", onMove, { passive: true });
    document.addEventListener("pointerdown", onDown, { passive: true });
    document.addEventListener("pointerup", onRelease, { passive: true });
    document.addEventListener("pointercancel", onRelease, { passive: true });
    document.documentElement.addEventListener("pointerleave", onLeaveWindow);

    return () => {
      document.removeEventListener("pointermove", onMove);
      document.removeEventListener("pointerdown", onDown);
      document.removeEventListener("pointerup", onRelease);
      document.removeEventListener("pointercancel", onRelease);
      document.documentElement.removeEventListener("pointerleave", onLeaveWindow);
      if (frame !== null) cancelAnimationFrame(frame);
      settle(active);
    };
  }, []);

  return null;
}
