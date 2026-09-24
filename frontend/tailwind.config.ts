import type { Config } from "tailwindcss";

/**
 * Tailwind configured to the AssureLens v5 "Signal" token scale.
 *
 * These keys sit under `theme`, NOT `theme.extend`, so they REPLACE the
 * defaults: `bg-blue-500`, `rounded-2xl` and `shadow-lg` stay unreachable and
 * every colour resolves to a token in styles/tokens.css. [DESIGN.md 2]
 *
 * v5 renamed the palette (n-*, accent-*, warm-* are gone) so that no
 * component could keep its v4 styling by accident: every call site had to be
 * rewritten against the new roles.
 */
const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    colors: {
      transparent: "transparent",
      current: "currentColor",
      page: "var(--page)",
      surface: "var(--surface)",
      inset: "var(--inset)",
      ink: {
        DEFAULT: "var(--ink)",
        2: "var(--ink-2)",
        3: "var(--ink-3)",
      },
      rule: {
        DEFAULT: "var(--rule)",
        strong: "var(--rule-strong)",
      },
      control: "var(--control)",
      cobalt: {
        DEFAULT: "var(--cobalt)",
        deep: "var(--cobalt-deep)",
        tint: "var(--cobalt-tint)",
      },
      "on-cobalt": {
        DEFAULT: "var(--on-cobalt)",
        2: "var(--on-cobalt-2)",
      },
      link: "var(--link)",
      lime: "var(--lime)",
      "on-lime": "var(--on-lime)",
      band: "var(--band)",
      "on-band": {
        DEFAULT: "var(--on-band)",
        2: "var(--on-band-2)",
      },
      // Verdicts: solid fills, one text colour on all three filled chips.
      pass: { DEFAULT: "var(--pass)", text: "var(--pass-text)" },
      fail: { DEFAULT: "var(--fail)", text: "var(--fail-text)" },
      insufficient: "var(--insufficient)",
      "on-verdict": "var(--on-verdict)",
      na: "var(--na-text)",
      sev: {
        critical: "var(--sev-critical)",
        "on-critical": "var(--on-sev-critical)",
        high: "var(--sev-high)",
        medium: "var(--sev-medium)",
        low: "var(--sev-low)",
      },
    },

    fontFamily: {
      sans: "var(--font-sans)",
      mono: "var(--font-mono)",
    },

    // [size, line-height]. The step names carry the role, so a call site
    // says what the text IS, not how big it happens to be.
    fontSize: {
      xs: ["var(--fs-xs)", "1.4"],
      meta: ["var(--fs-meta)", "1.4"],
      sm: ["var(--fs-sm)", "var(--lh-table)"],
      base: ["var(--fs-base)", "var(--lh-prose)"],
      lg: ["var(--fs-lg)", "1.3"],
      xl: ["var(--fs-xl)", "var(--lh-tight)"],
      "2xl": ["var(--fs-2xl)", "1.02"],
      num: ["var(--fs-num)", "1"],
      display: ["var(--fs-display)", "var(--lh-display)"],
    },

    letterSpacing: {
      normal: "0",
      display: "var(--track-display)",
      title: "var(--track-title)",
      head: "var(--track-head)",
      label: "0.04em",
    },

    spacing: {
      0: "0",
      px: "1px",
      1: "var(--sp-1)",
      2: "var(--sp-2)",
      3: "var(--sp-3)",
      4: "var(--sp-4)",
      5: "var(--sp-5)",
      6: "var(--sp-6)",
      7: "var(--sp-7)",
      8: "var(--sp-8)",
      9: "var(--sp-9)",
      10: "var(--sp-10)",
    },

    // All-sharp. `full` survives only for the indeterminate rule and the
    // scrollbar thumb, which are lines, not surfaces.
    borderRadius: {
      none: "0",
      DEFAULT: "var(--radius)",
      full: "999px",
    },

    // One shadow, for genuine overlays. Nothing on the page floats.
    boxShadow: {
      none: "none",
      overlay: "var(--shadow-overlay)",
    },

    borderWidth: {
      0: "0",
      DEFAULT: "1px",
      2: "2px",
      3: "3px",
      4: "4px",
    },

    lineHeight: {
      none: "1",
      display: "var(--lh-display)",
      tight: "var(--lh-tight)",
      table: "var(--lh-table)",
      prose: "var(--lh-prose)",
    },

    maxWidth: {
      content: "var(--content-max)",
      prose: "68ch",
      full: "100%",
    },

    extend: {
      gridTemplateColumns: {
        detail: "minmax(0, 2fr) minmax(0, 1fr)",
      },

      // Replacing `theme.spacing` also deletes every numeric width, because
      // Tailwind derives `width` from it. These restore the steps used, so a
      // `w-32` on a table header emits a rule rather than silently nothing.
      // [UX_BRIEF 11.6]
      width: {
        24: "6rem",
        28: "7rem",
        32: "8rem",
        36: "9rem",
        40: "10rem",
        44: "11rem",
        48: "12rem",
      },

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
