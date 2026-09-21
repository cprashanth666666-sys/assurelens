import type { Config } from "tailwindcss";

/**
 * Tailwind configured to the AssureLens token scale.
 *
 * CRITICAL: these keys sit under `theme`, NOT `theme.extend`. They REPLACE
 * Tailwind's defaults rather than adding to them. Extending would leave
 * `bg-blue-500`, `rounded-2xl` and `shadow-lg` reachable, and the untouched
 * default look creeps back in — an explicit fail condition. [UX 9, PLAN Day 1]
 */
const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    // Replaces the default palette entirely. Every colour resolves to a token.
    colors: {
      transparent: "transparent",
      current: "currentColor",
      n: {
        0: "var(--n-0)",
        25: "var(--n-25)",
        50: "var(--n-50)",
        100: "var(--n-100)",
        200: "var(--n-200)",
        300: "var(--n-300)",
        400: "var(--n-400)",
        500: "var(--n-500)",
        600: "var(--n-600)",
        700: "var(--n-700)",
        800: "var(--n-800)",
        900: "var(--n-900)",
      },
      accent: {
        50: "var(--accent-50)",
        100: "var(--accent-100)",
        500: "var(--accent-500)",
        600: "var(--accent-600)",
        700: "var(--accent-700)",
      },
      sev: {
        critical: "var(--sev-critical)",
        high: "var(--sev-high)",
        medium: "var(--sev-medium)",
        low: "var(--sev-low)",
        "critical-bg": "var(--sev-critical-bg)",
        "high-bg": "var(--sev-high-bg)",
        "medium-bg": "var(--sev-medium-bg)",
        "low-bg": "var(--sev-low-bg)",
      },
      verdict: {
        pass: "var(--verdict-pass)",
        fail: "var(--verdict-fail)",
        // Neutral ink by design. Never red, amber or yellow. [UX 6.1]
        insufficient: "var(--verdict-insufficient)",
        na: "var(--verdict-na)",
      },
    },

    fontFamily: {
      sans: "var(--font-sans)",
      mono: "var(--font-mono)",
      // Report preview only, where it signals "document" against the UI's
      // "instrument". [UX 2.2]
      serif: "var(--font-serif)",
    },

    fontSize: {
      "2xs": "var(--fs-2xs)",
      xs: "var(--fs-xs)",
      sm: "var(--fs-sm)",
      base: "var(--fs-base)",
      md: "var(--fs-md)",
      lg: "var(--fs-lg)",
      xl: "var(--fs-xl)",
      // Deliberately the largest. No hero numerals. [UX 2.2]
      "2xl": "var(--fs-2xl)",
    },

    spacing: {
      0: "0",
      1: "var(--sp-1)",
      2: "var(--sp-2)",
      3: "var(--sp-3)",
      4: "var(--sp-4)",
      5: "var(--sp-5)",
      6: "var(--sp-6)",
      7: "var(--sp-7)",
      8: "var(--sp-8)",
      px: "1px",
    },

    // Nothing above 4px. Removes rounded-lg / -xl / -2xl / -full entirely.
    borderRadius: {
      none: "0",
      sm: "var(--radius-sm)",
      md: "var(--radius-md)",
    },

    // One shadow, for overlays. Removes shadow-sm/md/lg/xl. [UX 2.3]
    boxShadow: {
      none: "none",
      overlay: "var(--shadow-overlay)",
    },

    borderWidth: {
      0: "0",
      DEFAULT: "1px",
      2: "2px",
      3: "3px",
    },

    lineHeight: {
      tight: "var(--lh-tight)",
      table: "var(--lh-table)",
      prose: "var(--lh-prose)",
    },

    maxWidth: {
      content: "var(--content-max)",
      prose: "75ch",
      full: "100%",
    },

    extend: {
      // Extending is permitted only where there is no default to displace.
      gridTemplateColumns: {
        detail: "2fr 1fr",
        heatmap: "auto repeat(5, minmax(0, 1fr))",
      },
    },
  },
  plugins: [],
};

export default config;
