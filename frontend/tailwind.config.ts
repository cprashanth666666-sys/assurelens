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
      white: "var(--pure-white)",
      // Translucent panel for sticky chrome. Literal rgba behind the var, so
      // backdrop-blur has something to blur through. [tokens.css]
      veil: "var(--surface-veil)",
      scrim: "var(--surface-scrim)",
      accent: {
        50: "var(--accent-50)",
        100: "var(--accent-100)",
        400: "var(--accent-400)",
        500: "var(--accent-500)",
        600: "var(--accent-600)",
        700: "var(--accent-700)",
      },
      // The second voice. Rules, hover marks, active filters — never status.
      warm: {
        50: "var(--warm-50)",
        100: "var(--warm-100)",
        400: "var(--warm-400)",
        500: "var(--warm-500)",
        600: "var(--warm-600)",
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
        "pass-bg": "var(--verdict-pass-bg)",
        "fail-bg": "var(--verdict-fail-bg)",
        "insufficient-bg": "var(--verdict-insufficient-bg)",
        "na-bg": "var(--verdict-na-bg)",
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
      "2xl": "var(--fs-2xl)",
      // v2.0: one display size, for the single statement line on the
      // overview. It carries a sentence, never a percentage — the KPI
      // numeral is still a fail condition. [UX 1.1, 1.3]
      "3xl": "var(--fs-3xl)",
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
      9: "var(--sp-9)",
      px: "1px",
    },

    // Controls stay at 2-3px. `lg` (10px) is reachable but exists only for
    // image plates — a hard corner on a photograph reads as an unstyled
    // <img>. rounded-xl / -2xl / -full remain unreachable. [UX 2.3]
    borderRadius: {
      none: "0",
      sm: "var(--radius-sm)",
      md: "var(--radius-md)",
      lg: "var(--radius-lg)",
      full: "999px",
    },

    // Two shadows. `raise` is the hover state of an interactive surface and
    // is tinted warm; `overlay` is for genuine overlays. shadow-sm/md/lg/xl
    // stay unreachable. [UX 2.3]
    boxShadow: {
      none: "none",
      raise: "var(--shadow-raise)",
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

      /**
       * Column widths, restored.
       *
       * Replacing `theme.spacing` (above) also removes every numeric width,
       * because Tailwind derives `width` from the spacing scale. The result
       * is that `w-32` on a table header emits NOTHING — the class is simply
       * absent from the stylesheet, the browser reports no error, and the
       * column silently falls back to auto-layout. Every `w-*` in this
       * project had been dead since Day 1 and the tables had been laying
       * themselves out by content width the whole time.
       *
       * These are the Tailwind defaults for the steps actually used, named
       * so the call sites did not have to change.
       */
      width: {
        24: "6rem",
        28: "7rem",
        32: "8rem",
        40: "10rem",
        44: "11rem",
      },

      // One motion rhythm, shared by utilities and by the component classes
      // in globals.css. A transition written against anything else is
      // out of step with the rest of the product. [UX 7.1]
      transitionDuration: {
        fast: "var(--dur-fast)",
        base: "var(--dur-base)",
        slow: "var(--dur-slow)",
      },
      transitionTimingFunction: {
        out: "var(--ease-out)",
        in: "var(--ease-in)",
        inout: "var(--ease-inout)",
      },
    },
  },
  plugins: [],
};

export default config;
