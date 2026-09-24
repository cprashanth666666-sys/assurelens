/**
 * The head of every page: a display-size title directly on the page field,
 * a lede at reading size, and optional content (counts, breadcrumbs) below.
 *
 * v4 boxed every page title inside a translucent tile because text could not
 * sit on the moving ground. The ground is flat now, so the title stands on
 * the page at 36-56px and carries the page's hierarchy by size alone.
 * [DESIGN.md 5]
 */
export function PageHeader({
  title,
  lede,
  kicker,
  children,
}: {
  title: string;
  lede?: React.ReactNode;
  /** Small line above the title: a breadcrumb or a ref. Optional. */
  kicker?: React.ReactNode;
  children?: React.ReactNode;
}) {
  return (
    <header className="flex flex-col gap-4">
      {kicker && <div className="text-sm">{kicker}</div>}
      <h2 className="max-w-[22ch] text-2xl font-medium tracking-title">{title}</h2>
      {lede && <p className="m-0 max-w-prose text-base text-ink-2 md:text-lg md:leading-prose">{lede}</p>}
      {children}
    </header>
  );
}
