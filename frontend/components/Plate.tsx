/* eslint-disable @next/next/no-img-element */
import { plateSrc, plateSrcSet, type Plate as PlateSpec } from "@/lib/imagery";

/**
 * A photograph on a plate that reserves its box.
 *
 * `<img>` rather than `next/image` on purpose — see the note in lib/imagery.ts.
 * The eslint rule is disabled here and only here.
 *
 * Three things this does that a bare <img> does not:
 *
 * * **Reserves its box.** `aspect-ratio` on the plate means the layout is
 *   final before a byte of image arrives. No CLS on a slow connection.
 *   [a11y image-dimension]
 * * **Survives a failed load.** The plate carries its own inset fill, so a
 *   blocked CDN leaves a composed rectangle with a caption rather than a
 *   broken-image glyph in the middle of an audit report.
 * * **Stays a photograph.** v5 removed the v2-v4 duotone and wash: on a bright
 *   page a full-colour image belongs, and square corners keep it on the grid.
 *
 * `sizes` must be passed by the caller: getting it wrong is how a 1800px
 * asset gets downloaded for a 320px slot.
 */
export function Plate({
  plate,
  sizes,
  priority = false,
  zoom = true,
  fill = false,
  className = "",
}: {
  plate: PlateSpec;
  sizes: string;
  /** Hero images only. Everything below the fold stays lazy. */
  priority?: boolean;
  zoom?: boolean;
  /**
   * Fill the parent box instead of reserving the photograph's own ratio.
   * Only for a slot whose height is already determined by a sibling — the
   * cover sheet's text column, say. Everywhere else the ratio is what keeps
   * the layout from shifting on load, so dropping it needs a reason.
   */
  fill?: boolean;
  className?: string;
}) {
  return (
    <div
      className={`plate ${zoom ? "plate-zoom" : ""} ${className}`}
      style={fill ? undefined : { aspectRatio: String(plate.ratio) }}
    >
      <img
        src={plateSrc(plate)}
        srcSet={plateSrcSet(plate)}
        sizes={sizes}
        alt={plate.alt}
        loading={priority ? "eager" : "lazy"}
        fetchPriority={priority ? "high" : "auto"}
        decoding="async"
      />
    </div>
  );
}

/**
 * The plate with its caption and credit.
 *
 * The credit is not decoration. This product's whole argument is that a
 * claim should name what it rests on; running uncredited photographs under
 * that argument would undercut it on the one screen a reviewer looks at
 * hardest.
 */
export function Figure({
  plate,
  sizes,
  priority = false,
  className = "",
}: {
  plate: PlateSpec;
  sizes: string;
  priority?: boolean;
  className?: string;
}) {
  return (
    <figure className={`m-0 flex flex-col ${className}`}>
      <Plate plate={plate} sizes={sizes} priority={priority} />
      <figcaption className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1 px-4 py-3 text-meta text-ink-2">
        <span className="max-w-prose">{plate.caption}</span>
        <a
          href={plate.credit.href}
          target="_blank"
          rel="noopener noreferrer"
          className="link whitespace-nowrap font-mono text-xs"
        >
          {plate.credit.name} on Unsplash
        </a>
      </figcaption>
    </figure>
  );
}
