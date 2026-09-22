"use client";

import { useEffect, useRef, useState } from "react";

/**
 * Entrance on first scroll into view. Once, never on the way back out.
 *
 * Three rules this follows, which most scroll-reveal implementations break:
 *
 * 1. **Opacity and transform only.** Nothing here can shift layout, so the
 *    reveal cannot contribute to CLS. [a11y layout-shift-avoid]
 * 2. **It disconnects after firing.** A permanent observer on every panel is
 *    a scroll-time cost for an effect that already happened.
 * 3. **It fails visible, not hidden.** If IntersectionObserver is missing the
 *    element shows immediately; `@media (scripting: none)` and the <noscript>
 *    rule in layout.tsx cover JS being off entirely. A reveal that hides
 *    content when its own machinery fails is a bug that looks like a blank
 *    page.
 *
 * `delay` staggers a group by 40ms per item — enough to read as a sequence,
 * short enough that the last item is not still arriving after the eye has
 * moved on. [UX 7.3]
 */
export function Reveal({
  children,
  delay = 0,
  as: Tag = "div",
  className = "",
}: {
  children: React.ReactNode;
  delay?: number;
  as?: "div" | "section" | "li" | "article" | "header";
  className?: string;
}) {
  const ref = useRef<HTMLElement>(null);
  const [shown, setShown] = useState(false);

  useEffect(() => {
    const node = ref.current;
    if (!node) return;

    if (typeof IntersectionObserver === "undefined") {
      // Deferred out of the effect body on purpose. A synchronous setState
      // here would cascade one extra render per Reveal in the same commit —
      // and on a page with a dozen of them that is a dozen wasted renders in
      // exactly the environment least able to afford them.
      queueMicrotask(() => setShown(true));
      return;
    }

    // Already in view on load (above the fold) — show without waiting for a
    // scroll that may never come.
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            setShown(true);
            observer.disconnect();
          }
        }
      },
      { rootMargin: "0px 0px -8% 0px", threshold: 0.05 },
    );

    observer.observe(node);
    return () => observer.disconnect();
  }, []);

  return (
    <Tag
      ref={ref as never}
      className={`reveal ${className}`}
      data-shown={shown ? "true" : "false"}
      style={delay ? ({ "--reveal-delay": `${delay}ms` } as React.CSSProperties) : undefined}
    >
      {children}
    </Tag>
  );
}
