# AssureLens — UI/UX Design Brief

| | |
|---|---|
| Version | 1.0 |
| Date | 21 September 2026 |
| Status | Approved for build |
| Related | [PRD.md](PRD.md) · [TRD.md](TRD.md) · [SCHEMA.md](SCHEMA.md) |

> At build time, run the `design-taste-frontend` / `ui-ux-pro-max` skill against this brief before writing components, and again as a review pass before Day 10. This document is the input to that review and the standard it is judged against.

---

## 1. The aesthetic, in one line

**Audit-grade restraint.** It should look like an instrument a Big Four manager would sign a workpaper out of — dense, calm, legible under fluorescent light, with the numbers doing all the talking.

The reference points are the *printed workpaper*, the *statistical table*, and the *regulatory filing* — not the SaaS dashboard.

### 1.1 Negative constraints (binding)

These are rejections, not preferences. A design review that finds any of them fails.

| ✗ Not this | Why it's wrong here |
|---|---|
| **Rounded cards floating on a grey page** | The default AI-generated dashboard. Instantly reads as templated. |
| **Purple/blue gradients, glassmorphism, glows** | Decoration where the content is a legal conclusion. |
| **Emoji status icons** (✅ ⚠️ 🚨) | Nothing undermines an assurance verdict faster. |
| **Dark "security ops console"** | Wrong genre — this is audit, not a SOC. Theatre over judgement. |
| **Full-width marketing hero** | It's a workbench. There is no landing page. |
| **Big number + percentage-change tiles** | The KPI-tile reflex. Actively wrong here: we refuse a headline compliance %. [PRD §7.3] |
| **Animated counters, confetti, progress celebration** | Compliance progress is not a game. |
| **Colour-only severity encoding** | Fails accessibility and fails print. |
| **Pill badges for everything** | Rounded pills everywhere is a tell. Used sparingly and only for framework mappings. |
| **Default shadcn/Tailwind look, untouched** | Recognisable at a glance as unmodified defaults. |
| **Icon next to every label** | Decoration density without information density. |

### 1.2 Positive direction

| Do this | Because |
|---|---|
| **Information density without crowding** | Auditors read tables. Give them a real table, 32px rows, not a card grid. |
| **Rules, not shadows** | 1px hairlines define structure. Elevation only for genuine overlays. |
| **One accent colour, earned** | Accent is reserved for severity and interactive affordance. Never decorative. |
| **Tabular figures everywhere** | Numbers in columns must align. `font-variant-numeric: tabular-nums`, no exceptions. |
| **Generous line-height inside dense tables** | Density comes from tight margins, not cramped text. |
| **Left-aligned page structure, max 1440px** | A workpaper has a margin. Content does not stretch to a 27" monitor. |
| **Typographic hierarchy over colour hierarchy** | Weight and size carry structure; colour carries meaning. |
| **Monospace for identifiers and evidence** | Control refs, run IDs, hashes, probe payloads. |

---

## 2. Design tokens

CSS custom properties in `frontend/styles/tokens.css`. Nothing hardcodes a hex.

### 2.1 Colour

Neutrals are **slightly warm** — a cool grey ramp is the default-SaaS tell. Warmth reads as paper.

```css
:root {
  /* Neutral — warm grey, paper-leaning */
  --n-0:   #ffffff;
  --n-25:  #fcfcfb;   /* page ground */
  --n-50:  #f7f6f4;   /* table zebra, inset panels */
  --n-100: #eeece8;   /* hairlines, dividers */
  --n-200: #dedbd5;   /* borders */
  --n-300: #c2beb6;   /* disabled */
  --n-400: #9b968c;   /* placeholder */
  --n-500: #6f6a61;   /* secondary text */
  --n-600: #55504a;   /* body on light */
  --n-700: #3b3733;   /* headings */
  --n-800: #262320;   /* primary text */
  --n-900: #14120f;   /* max contrast */

  /* Accent — deep ink blue. Interactive + structural only. */
  --accent-700: #1b3a5c;
  --accent-600: #24506f;
  --accent-500: #2f6690;
  --accent-100: #dce7ef;
  --accent-50:  #eef4f8;

  /* Severity — 4 steps, muted. Never neon. */
  --sev-critical: #8c2f2a;
  --sev-high:     #b4612c;
  --sev-medium:   #8a7124;
  --sev-low:      #4a6b52;
  --sev-critical-bg: #f7e9e8;
  --sev-high-bg:     #faefe4;
  --sev-medium-bg:   #f7f2e0;
  --sev-low-bg:      #eaf1ec;

  /* Verdicts — see §6. INSUFFICIENT is NEUTRAL by design. */
  --verdict-pass:         #3f6b4a;
  --verdict-fail:         #8c2f2a;
  --verdict-insufficient: #55504a;   /* deliberately neutral ink */
  --verdict-na:           #9b968c;
}
```

**Dark mode.** Tokens redefined under `@media (prefers-color-scheme: dark)` and `[data-theme="dark"]`, both guarded so an explicit choice wins. Dark mode inverts the neutral ramp and *desaturates* severity further. Light is the primary design; dark must not become the ops-console look §1.1 rejects.

### 2.2 Type

```css
--font-sans: "Inter Tight", "Inter", -apple-system, "Segoe UI", sans-serif;
--font-mono: "JetBrains Mono", "SF Mono", "Cascadia Mono", monospace;
--font-serif: "Source Serif 4", Georgia, serif;   /* report headings only */

--fs-2xs: 0.6875rem;  /* 11px — table meta, captions */
--fs-xs:  0.75rem;    /* 12px — dense table body */
--fs-sm:  0.8125rem;  /* 13px — default UI */
--fs-base:0.875rem;   /* 14px — body prose */
--fs-md:  1rem;
--fs-lg:  1.25rem;
--fs-xl:  1.5rem;
--fs-2xl: 1.875rem;   /* largest on screen — no 48px hero numbers */
```

Rules:
- **All numerals `tabular-nums`.** Set globally on `body`, never overridden.
- Headings: `--font-sans`, weight 600, tight tracking (−0.011em). Serif is used **only** in the report preview, where it signals "document" against the UI's "instrument".
- Body copy max ~75 characters.
- Line-height 1.5 in tables, 1.6 in prose. Density from margin, not leading. [§1.2]

### 2.3 Spacing, borders, elevation

```css
--sp-1: 4px;  --sp-2: 8px;  --sp-3: 12px; --sp-4: 16px;
--sp-5: 24px; --sp-6: 32px; --sp-7: 48px; --sp-8: 64px;

--radius-sm: 2px;   /* inputs, buttons */
--radius-md: 3px;   /* panels */
/* No radius above 4px anywhere. Rounded-2xl is the templated look. */

--border-hair:   1px solid var(--n-100);
--border-strong: 1px solid var(--n-200);

--shadow-overlay: 0 4px 16px rgb(20 18 15 / 0.10);
/* The ONLY shadow token. Modals, popovers, dropdowns. Nothing else. */
```

Panels are defined by a 1px border and a background shift — never by a drop shadow. This single rule does most of the work of not looking templated.

---

## 3. Layout

```
┌───────────────────────────────────────────────────────────────┐
│ MASTHEAD  AssureLens · Meridian Financial Services India GCC  │
│           DPDP + AI Controls Readiness    [ Consultant ▾ ]    │
│───────────────────────────────────────────────────────────────│
│ Overview │ Controls │ Test Runs │ Findings │ Roadmap │ Report │
├──────────┴────────────────────────────────────────────────────┤
│                                                               │
│   Content, left-aligned, max-width 1440px                     │
│                                                               │
└───────────────────────────────────────────────────────────────┘
│ Synthetic demonstration data. Not legal advice.  Run #4 · seed 42 │
└───────────────────────────────────────────────────────────────┘
```

- **Masthead**, not a nav bar: entity name and engagement title carry the weight, product name is secondary. A workpaper is headed by whose it is.
- **Tabs with a 2px bottom rule** on the active item. No pill nav, no sidebar. Six destinations do not need a sidebar, and a sidebar is the SaaS reflex.
- **Persistent footer disclosure.** The synthetic-data and not-legal-advice statement is always visible, not a dismissible banner. [PRD §9]

---

## 4. Screens

### 4.1 Overview — *where do I stand*

Client view lands here. Three blocks, stacked, full width.

**A. Readiness by domain.** A horizontal segmented bar per domain (Notice & Consent, Security Safeguards, Retention & Erasure, Data Principal Rights, Third-Party & Transfers, AI Governance). Each bar segments into Pass / Fail / **Insufficient** / N-A, with counts, and **coverage % printed beside it, not inside it**.

> **No headline compliance percentage anywhere on this screen.** [PRD §7.3] If a reviewer asks where the score is, the answer is the FAQ in the README — a domain with 40% coverage and a domain with 95% coverage cannot be averaged into one honest number.

**B. Risk heatmap.** 5×5 likelihood × impact grid, findings plotted as counts per cell. Muted severity fill with a numeral — never colour alone. Clicking a cell filters the findings register.

**C. Evidence quality meter.** The screen's distinctive element and the product's thesis made visual. A horizontal band showing what proportion of in-scope controls have: *sufficient evidence* / *thin evidence* / *no evidence*. Reading directly: **"You have graded 60% of your estate. Here is the other 40%."**

### 4.2 Controls — the library

Dense table. 25 rows, no pagination, sticky header.

| Ref | Control | Domain | DPDP | ISO 27001 | NIST AI | Last result | Coverage |
|---|---|---|---|---|---|---|---|
| `DPDP-06-02` | Access to personal data is restricted… | Security | R6(1)(b) | A.5.15 | — | **Fail** | 100% |

- Ref in mono. Framework refs in mono at `--fs-2xs` — the only place pills are allowed, and only for framework mappings.
- Filter rail above: domain, framework, verdict, executable-vs-documented.
- Row hover: `--n-50`. Zebra striping on even rows. No hover lift, no scale transform.
- Sort by any column; sorted column header carries a 2px accent rule.

### 4.3 Control detail

Two columns, 2:1.

**Left** — objective; clause reference with **the verbatim quoted text of the rule** (this is the credibility move: the reader sees the statute, not a paraphrase); test procedure; evidence contract with items and status; result history (small step chart, last 5 runs).

**Right** — current verdict block (§6); statistics (n, N, coverage, point estimate, Wilson CI, method named); thresholds applied, with **any override flagged in accent**; linked findings.

### 4.4 Test run console

The one screen permitted motion — and only functional motion.

- Suite selector, seed field (pre-filled `42`, editable — visibly reproducible), Run.
- Results stream into a log-style list as each control resolves: `ref · control · verdict · n/N · elapsed`.
- **The only animation in the product:** a 1px indeterminate rule under the running control. No spinners, no skeletons that pulse, no progress celebration.
- Verdicts land in place. A gated verdict lands as calmly as a pass — that restraint is the point.
- On completion: summary line, and newly raised findings listed with links.

### 4.5 Findings register

| ID | Finding | Control | Severity | L×I | Root cause | Owner | Status |
|---|---|---|---|---|---|---|---|

- Severity as a 3px left border on the row + a text label. **Never colour alone.** [§1.1]
- Expand a row in place for: evidence (probe request/response in a mono block), recommendation, effort, history.
- Consultant can edit; client is read-only with internal reviewer notes hidden. [PRD §4.4]

### 4.6 Roadmap

90-day plan, two panes. **Left:** effort × impact scatter, findings as plotted points, quadrant rules hairline-thin and labelled in the margin (no shaded quadrant blocks). **Right:** an ordered list — sequence, action, owner, effort, expected residual reduction. Ordered by impact ÷ effort; the ordering rule is printed on screen so it can be argued with.

### 4.7 Upload and mapping

Three steps, breadcrumbed. Drop zone is a dashed 1px rule, not an illustrated empty state. Profile table: column, inferred type, null %, cardinality, sample, **detector hits**. Mapping: suggested target with a confidence indicator; unmapped required fields listed explicitly with *"suites that will return Insufficient Evidence: 2"* — telling the user the honest consequence before they run.

A standing notice: **"Public demonstration. Do not upload real personal data."**

### 4.8 Report preview

Paper metaphor, and the only place it is allowed: white page on `--n-100` ground, serif headings, page-width column, print margins visible. Export buttons: Workpaper (DOCX), Executive summary (DOCX).

---

## 5. The role switch

Masthead control, right-aligned, labelled **`Viewing as: Consultant ▾`**. Two options with one-line descriptions.

On switch:
- A hairline band under the masthead states the change: *"Viewing as client (CISO / DPO). Same results, presented for the data fiduciary."*
- Content re-renders per [PRD §4.4].
- **No colour-theme change, no layout change.** It is a lens, not a different product. Dressing it up as a dramatic mode switch would imply the numbers change — they do not.

---

## 6. Rendering `INSUFFICIENT_EVIDENCE`

**The most important rendering decision in the product.** [PRD §6.5]

### 6.1 Non-negotiables

| Rule | |
|---|---|
| Colour | `--verdict-insufficient` — **neutral ink**. Never red, amber, or yellow. |
| Icon | None, or a neutral horizontal rule glyph. **Never** ⚠ 🚨 ❗ |
| Language | *"Insufficient evidence"* — never "Unknown", "Error", "Incomplete", "N/A", "Pending" |
| Weight | Same type weight as Pass and Fail. It is a peer verdict, not a lesser one. |
| Position | Same slot. It does not get pushed to a footnote. |

### 6.2 The verdict block

```
┌──────────────────────────────────────────────────────────┐
│  INSUFFICIENT EVIDENCE                                   │
│                                                          │
│  Why                                                     │
│  Coverage below threshold — tested 12 of 2,400 records   │
│  (0.5%). Population conclusions require 10%.  [G3]       │
│                                                          │
│  Also                                                    │
│  Sample size below minimum — n=12, minimum 30.    [G1]   │
│                                                          │
│  What would resolve this                                 │
│  Sample 240 records, or narrow the control's scope to a  │
│  defined subpopulation and restate the objective.        │
│                                                          │
│  Evidence owner       Data Engineering, Meridian India   │
│  Threshold basis      MIN_COVERAGE_PCT = 10.0 (default)  │
└──────────────────────────────────────────────────────────┘
```

Every gate reason is shown with its rule ID — never only the first. Every block answers three questions in this order: **why · what would resolve it · who owns it.** A gate that does not say how to clear it is just an excuse.

### 6.3 In tables

`Insufficient` in `--verdict-insufficient`, plus a superscript gate code (`G3`) that is a tooltip target. Never a dash, never blank — an empty cell reads as "not run", which is a different and less honest thing.

---

## 7. Accessibility

| Requirement | |
|---|---|
| Contrast | WCAG AA throughout; AAA for body text. `--n-600` on `--n-25` = 8.1:1. |
| Colour independence | **Every** severity and verdict carries a text label. Colour is redundant encoding, always. |
| Keyboard | Full path through the demo without a mouse. Tables: arrow navigation, Enter to expand, Esc to collapse. |
| Focus | 2px `--accent-500` outline, 2px offset. Never `outline: none`. |
| Screen reader | Tables use real `<th scope>`. Run console is an `aria-live="polite"` region so verdicts are announced. |
| Motion | `prefers-reduced-motion` removes the one indeterminate rule. Nothing else moves. |
| Zoom | Usable at 200% without horizontal scroll, except tables (which scroll in their own container). |

---

## 8. Responsive

Desktop-first — this is a workbench used on a laptop — but it must not break when a recruiter opens the link on a phone.

| Width | Behaviour |
|---|---|
| ≥1280px | Full layout, all table columns |
| 1024–1279 | Control detail collapses 2:1 → stacked |
| 768–1023 | Tabs scroll horizontally; secondary table columns hidden behind a column toggle |
| <768px | Tables become stacked definition lists, label-above-value. Heatmap scrolls in its own container. Run console remains fully usable. |

Side gutter never below 16px. Only tables, the heatmap and the scatter may exceed viewport width, each inside its own `overflow-x: auto`.

---

## 9. Component inventory

`Masthead` · `RoleSwitch` · `TabNav` · `DataTable` (sortable, expandable, sticky header — the workhorse) · `VerdictBadge` · `VerdictBlock` · `SeverityIndicator` · `ReadinessBar` · `RiskHeatmap` · `EvidenceQualityMeter` · `StatPair` (label/value, tabular) · `ClauseQuote` (verbatim rule text, serif, ruled left margin) · `EvidenceViewer` (mono, request/response) · `ThresholdRow` · `RunConsole` · `EffortImpactScatter` · `ColumnMapper` · `ReportPreview` · `DisclosureFooter`

Built on Radix primitives (behaviour and a11y) with **fully custom styling from the tokens above**. Tailwind is configured to the token scale — no default Tailwind palette, no default radius scale, no default shadows. An untouched shadcn look is an explicit fail condition. [§1.1]

---

## 10. Design review checklist (Day 10 gate)

Run before declaring the build done. Any ✗ blocks.

- [ ] No element from the §1.1 negative list appears anywhere
- [ ] No headline compliance percentage exists on any screen
- [ ] `INSUFFICIENT_EVIDENCE` renders neutral, with why / how to resolve / owner, in every location
- [ ] All numerals are tabular and align in columns
- [ ] No border-radius exceeds 4px
- [ ] Exactly one shadow token is in use, only on overlays
- [ ] Every severity and verdict has a text label, not colour alone
- [ ] Full demo path completes by keyboard alone
- [ ] Contrast checked on every token pair in both themes
- [ ] Phone width (390px): no horizontal body scroll, demo still completable
- [ ] Dark mode does not read as a security-ops console
- [ ] Synthetic-data disclosure visible on every screen
- [ ] `design-taste-frontend` / `ui-ux-pro-max` review passed against this brief
