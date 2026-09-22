/**
 * Always visible, never dismissible.
 *
 * The synthetic-data and not-legal-advice statements are a standing
 * disclosure, not a banner a user can clear. A tool that asserts compliance
 * conclusions has to say what it is standing on, on every screen. [PRD 9, UX 3]
 */
export function DisclosureFooter() {
  return (
    <footer className="mt-9 border-t border-n-200 bg-n-50">
      {/* A 2px rule in the two brand inks, full bleed. The only place the
          pairing is stated outright rather than used. */}
      <div
        aria-hidden="true"
        className="h-px w-full"
        style={{
          background:
            "linear-gradient(90deg, var(--accent-500), var(--warm-500) 60%, transparent)",
        }}
      />
      <div className="mx-auto flex max-w-content flex-wrap items-center justify-between gap-2 px-4 py-4 md:px-5">
        <p className="m-0 max-w-prose text-2xs text-n-500">
          Synthetic demonstration data. Not legal advice. Clause mappings are
          the author&rsquo;s reading of the DPDP Rules 2025.
        </p>
        <p className="m-0 font-mono text-2xs text-n-400">
          engine 0.1.0
        </p>
      </div>
    </footer>
  );
}
