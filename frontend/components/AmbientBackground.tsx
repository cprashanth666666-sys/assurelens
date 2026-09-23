/**
 * The moving ground: a sunset-to-sea gradient, three drifting colour blooms,
 * and three layers of waves that roll continuously along the bottom of the
 * viewport. [UX 12.3]
 *
 * A server component with no JavaScript at all. Every movement is a CSS
 * animation of `transform`, so it runs on the compositor thread and cannot
 * block input, a run, or a scroll -- the page stays as responsive with the
 * waves moving as without them.
 *
 * Why the waves loop seamlessly: each layer is one wave PERIOD drawn twice
 * side by side in a 200%-wide strip, and the strip slides left by exactly
 * half its width. At the end of a cycle the second copy sits where the first
 * began, so the jump back to the start is invisible. The path starts and
 * ends at the same height with the same slope, which is what removes the
 * seam where the two copies meet.
 *
 * Three layers at three speeds and three depths of colour give parallax:
 * the slow, dark back wave reads as further away than the fast, pale front
 * one. That is the "depth" in the brief, done with timing rather than blur.
 *
 * Decorative only: aria-hidden, pointer-events none, and frozen under
 * prefers-reduced-motion (globals.css).
 */
export function AmbientBackground() {
  return (
    <div aria-hidden="true" className="ambient fixed inset-0 z-0">
      <div className="ambient-blob ambient-blob--sun" />
      <div className="ambient-blob ambient-blob--coral" />
      <div className="ambient-blob ambient-blob--lagoon" />

      <div className="ambient-waves">
        <Wave className="wave wave--deep" />
        <Wave className="wave wave--mid" />
        <Wave className="wave wave--foam" />
      </div>
    </div>
  );
}

/** One wave period (1440 wide), drawn twice so the strip can loop. */
const PERIOD =
  "M0 60 C 240 20, 480 20, 720 60 C 960 100, 1200 100, 1440 60 L 1440 120 L 0 120 Z";

function Wave({ className }: { className: string }) {
  return (
    <svg
      className={className}
      viewBox="0 0 2880 120"
      preserveAspectRatio="none"
      focusable="false"
    >
      <path d={PERIOD} />
      <path d={PERIOD} transform="translate(1440 0)" />
    </svg>
  );
}
