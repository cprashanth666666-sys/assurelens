/**
 * Video clips, self-hosted in /public/media.
 *
 * Every clip is from Pexels (free to use under the Pexels licence) and is
 * credited on screen anyway, for the same reason the photographs are: a tool
 * whose argument is "cite what you stand on" cannot run uncredited media.
 *
 * Each was re-encoded from the Pexels original to 1280px H.264, 10 seconds,
 * no audio track, `+faststart` so playback begins before the file finishes.
 * Sizes: estate 1.08 MB, evidence 0.72 MB, network 0.18 MB.
 */

export type Clip = {
  src: string;
  poster: string;
  /** Describes what is on screen, for the accessible name. */
  label: string;
  credit: { name: string; href: string; source: string };
};

export const CLIPS = {
  estate: {
    src: "/media/estate.mp4",
    poster: "/media/estate-poster.jpg",
    label: "Aerial view of Bengaluru's IT district at sunrise, glass office towers among residential blocks.",
    credit: {
      name: "Anil Sharma",
      href: "https://www.pexels.com/video/aerial-view-of-bengaluru-s-it-hub-at-sunrise-30590791/",
      source: "Pexels",
    },
  },
  network: {
    src: "/media/network.mp4",
    poster: "/media/network-poster.jpg",
    label: "Close view of network cables plugged into a switch, status lights blinking.",
    credit: {
      name: "Dima Krivoy",
      href: "https://www.pexels.com/video/blue-colored-cables-1085656/",
      source: "Pexels",
    },
  },
  evidence: {
    src: "/media/evidence.mp4",
    poster: "/media/evidence-poster.jpg",
    label: "Hands searching through indexed record cards in an archive drawer.",
    credit: {
      name: "Tima Miroshnichenko",
      href: "https://www.pexels.com/video/looking-among-files-6549976/",
      source: "Pexels",
    },
  },
} satisfies Record<string, Clip>;
