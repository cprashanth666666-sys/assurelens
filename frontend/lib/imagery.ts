/**
 * The image programme.
 *
 * Four photographs, each doing a specific job. This is a deliberately short
 * list: an assurance instrument with a photograph on every panel stops
 * looking like an instrument. [UX 2.6]
 *
 * Sourcing rules, which are the same rules the product applies to statutory
 * text in SOURCES.md:
 *
 * 1. Every image is attributed to a named photographer with a link, even
 *    though the Unsplash licence does not require it. A tool whose entire
 *    argument is "cite what you are standing on" cannot use uncredited
 *    images.
 * 2. Every URL was fetched and checked for HTTP 200, and every photograph
 *    was LOOKED AT before selection. The first Bengaluru candidate had a
 *    three-storey Christmas tree in the foreground and the first estate
 *    candidate was a neon-lit server rack — the dark-ops-console cliché
 *    UX 1.1 rejects. Alt text is not a substitute for looking.
 * 3. No people. Stock photographs of smiling colleagues are the fastest way
 *    to make a compliance tool look like a brochure.
 *
 * Served straight from Unsplash's own CDN rather than through next/image:
 * `images.unsplash.com` already does format negotiation and width variants,
 * so proxying it would add a hop, a `sharp` dependency in the Docker path
 * and image-optimisation billing, in exchange for nothing.
 */

export type Plate = {
  /** Unsplash asset id, i.e. the `photo-<id>` path segment. */
  id: string;
  alt: string;
  /** What the photograph is doing here, shown as the figure caption. */
  caption: string;
  credit: { name: string; href: string };
  /** Intrinsic ratio, used to reserve space so nothing shifts on load. */
  ratio: number;
};

const UNSPLASH = "https://images.unsplash.com/photo-";

/** Widths offered to the browser. Anything wider is wasted on a 1440px page. */
const WIDTHS = [480, 768, 1200, 1800] as const;

export function plateSrc(plate: Plate, width = 1200): string {
  return `${UNSPLASH}${plate.id}?auto=format&fit=crop&w=${width}&q=70`;
}

export function plateSrcSet(plate: Plate): string {
  return WIDTHS.map((w) => `${plateSrc(plate, w)} ${w}w`).join(", ");
}

export const PLATES = {
  /**
   * Vidhana Soudha, the seat of the Karnataka legislature. Chosen over a
   * generic glass tower because the subject of this product is a statute:
   * the building where law is made is a more honest hero for it than an
   * office park, and the sandstone sits in the palette rather than fighting
   * it.
   */
  statute: {
    id: "1588416936097-41850ab3d86d",
    alt:
      "The Vidhana Soudha in Bengaluru, seat of the Karnataka state " +
      "legislature, photographed from its lawns in low afternoon sun.",
    caption:
      "Vidhana Soudha, Bengaluru — where the law this workbench executes is made.",
    credit: { name: "@passiondroid", href: "https://unsplash.com/@passiondroid" },
    ratio: 4 / 3,
  },

  /** The estate under test: a real city, not an abstraction. */
  estate: {
    id: "1728978645470-b8c0aacd4fa9",
    alt:
      "Aerial view of Bengaluru under monsoon cloud, dense low-rise housing " +
      "running to high-rise towers on the horizon.",
    caption:
      "Bengaluru. Meridian is a fictional GCC in this city; every record tested is synthetic.",
    credit: { name: "@vishwasnavadak", href: "https://unsplash.com/@vishwasnavadak" },
    ratio: 5 / 4,
  },

  /** Evidence: tied bundles of paper, which is what a workpaper file is. */
  evidence: {
    id: "1526656001029-20a71b17f7ba",
    alt:
      "Stacked bundles of aged paper files tied with black ribbon, seen from " +
      "above in an archive.",
    caption:
      "Evidence, before it was queryable. The sufficiency gate asks the same question of both.",
    credit: { name: "@seargreyson", href: "https://unsplash.com/@seargreyson" },
    ratio: 4 / 3,
  },

  /** The control library: a structural grid, read as a lattice of controls. */
  structure: {
    id: "1523477593243-78bbf626fd3b",
    alt:
      "Close view of a glass curtain wall, its panels held on a regular grid " +
      "of steel spider fittings.",
    caption: "Twenty-five controls on one frame, each pinned to a single clause.",
    credit: { name: "@dozy_de", href: "https://unsplash.com/@dozy_de" },
    ratio: 3 / 2,
  },
} as const satisfies Record<string, Plate>;
