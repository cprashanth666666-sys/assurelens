/* eslint-disable @next/next/no-img-element */
import { plateSrc, plateSrcSet, type Plate as PlateSpec } from "@/lib/imagery";

/**
 * A photograph, on a tinted plate, under a warm wash.
 *
 * `<img>` rather than `next/image` on purpose — see the note in lib/imagery.ts.
 * The eslint rule is disabled here and only here.
 *
 * Three things this does that a bare <img> does not:
 *
 * * **Reserves its box.** `aspect-ratio` on the plate means the layout is
 *   final before a byte of image arrives. No CLS on a slow connection.
 *   [a11y image-dimension]
 * * **Survives a failed load.** The plate carries its own teal-to-terracotta
 *   gradient, so a blocked CDN leaves a composed rectangle with a caption
 *   rather than a broken-image glyph in the middle of an audit report.
 * * **Desaturates and washes.** A full-colour stock photograph next to a
 *   muted palette reads as pasted in. The multiply layer puts it in the same
 *   ink as everything else. [UX 2.6]
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
    <figure className={`m-0 ${className}`}>
      <Plate plate={plate} sizes={sizes} priority={priority} />
      <figcaption className="mt-2 flex flex-wrap items-baseline justify-between gap-2 text-2xs text-n-500">
        <span className="max-w-prose">{plate.caption}</span>
        <a
          href={plate.credit.href}
          target="_blank"
          rel="noopener noreferrer"
          className="link-grow whitespace-nowrap font-mono text-n-400 no-underline transition-colors duration-base ease-out hover:text-n-600"
        >
          {plate.credit.name} · Unsplash
        </a>
      </figcaption>
    </figure>
  );
}
