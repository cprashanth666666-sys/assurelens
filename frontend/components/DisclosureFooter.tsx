/**
 * Always visible, never dismissible. A tool that asserts compliance
 * conclusions has to say what it is standing on, on every screen.
 * [PRD 9, UX 3]
 *
 * v5: an ink band, so the disclosure reads as the end of the document rather
 * than as a faint caption under it.
 */
export function DisclosureFooter() {
  return (
    <footer className="bg-band text-on-band">
      <div className="mx-auto flex max-w-content flex-wrap items-center justify-between gap-4 px-4 py-6 md:px-6">
        <p className="m-0 max-w-prose text-sm">
          <strong className="font-semibold">Synthetic demonstration data. Not legal advice.</strong>{" "}
          <span className="text-on-band-2">
            Clause mappings are the author&rsquo;s reading of the DPDP Rules 2025.
          </span>
        </p>
        <p className="m-0 font-mono text-meta text-on-band-2">engine 0.1.0</p>
      </div>
    </footer>
  );
}
