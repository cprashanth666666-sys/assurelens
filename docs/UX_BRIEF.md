# AssureLens — UI/UX Design Brief

| | |
|---|---|
| Version | 3.0 — *Tidal* |
| Date | 23 September 2026 (v2.0: 22 September; v1.0: 21 September 2026) |
| Status | Approved for build |
| Related | [PRD.md](PRD.md) · [TRD.md](TRD.md) · [SCHEMA.md](SCHEMA.md) |

> **v3.0 revision.** A vivid, continuously moving gradient ground with wave motion, and raised tiles that tilt toward the cursor and the finger. §12 records the change, the positions it reverses, and the one rule that keeps it readable: text never sits on the moving ground. Everything in §12.7 is unchanged.

> **v2.0 revision.** The v1.0 aesthetic was judged, on the built product, to have overshot restraint into plainness. §1.3 records exactly which constraints were lifted and which were re-affirmed; §11 records the full change and the reasoning. Everything not named in §1.3 still stands as written.

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

### 1.3 v2.0 — what was lifted, and what was not

v1.0 was written against one failure mode: the templated AI dashboard. It succeeded, and then kept going. Built out, the product read as *unfinished* rather than *restrained* — and an assurance tool that looks unfinished is not read as disciplined, it is read as a prototype.

The diagnosis matters, because "make it less plain" and "make it a SaaS dashboard" are one careless step apart. Three findings:

1. **Nothing was actually wrong with the rules.** The three faces named in §2.2 were never loaded — no `next/font`, no stylesheet link — so every screen had been rendering in Segoe UI since Day 1. The brief specified Inter Tight, JetBrains Mono and Source Serif 4; the build shipped the system font. A large share of "it looks plain" was a missing `<link>`.
2. **Restraint was being confused with absence.** "One accent colour, earned" is a good rule. One accent colour on a neutral ground *with no second voice anywhere* is a monochrome, and a monochrome has no way to signal that anyone made a decision.
3. **Motion was banned outright** (§7, v1.0: "the product has exactly one animation"). But a page with no state transitions does not read as calm — it reads as static, and on a phone it gives the reader no feedback that anything responded to them.

**Lifted:**

| v1.0 constraint | v2.0 position | Why |
|---|---|---|
| Page ground is near-white `#fcfcfb` | **Warm oat `#f6f2e8`**, under a three-tint radial wash at ≤7% chroma | The ground is the largest surface on every screen. A near-white ground is the one that reads as "unstyled default". Oat reads as paper, which is the reference this brief named in the first line. |
| One accent colour only | **Two inks: teal `#1c6b84` + terracotta `#bb6640`** | Terracotta is a second *voice*, not a second status colour: rules under headings, hover marks, the active filter. It is never permitted to carry severity or verdict — those stay on their own scale. |
| "The product has exactly one animation" | **A motion system with one rhythm** (`--dur-fast/base/slow`, `--ease-out/in/inout`) | The test is unchanged and is now written down: *motion must report state*. Hover, focus, entrance and run progress all report something. §11.3 lists what is still banned. |
| No imagery at all | **Four duotone plates, credited** | See §11.4. The programme is deliberately short and every image is mapped into the two inks, so no photograph sits in the layout at full saturation. |
| No radius above 4px | **Controls stay at 2–3px; `--radius-lg: 10px` exists for image plates only** | A hard corner on a photograph looks like an unstyled `<img>`. Nothing else may use it. |
| One shadow token, overlays only | **Two: `--shadow-overlay` and `--shadow-raise`** | `raise` is the hover state of an interactive surface and is tinted *warm*. A neutral-grey shadow on warm paper is the tell that a palette was applied afterwards. |

**Re-affirmed, and not negotiable:**

- **No headline compliance percentage.** Still the product's whole position. [PRD §7.3]
- **`INSUFFICIENT_EVIDENCE` renders in neutral ink, as a peer verdict.** Every visual revision must leave this alone. If `PASS` ever gets a flourish that a gated verdict does not, the interface is quietly telling the reader which answer it prefers.
- **No animated counters, no progress celebration, no confetti.** Compliance progress is not a game, and a number that ticks upward is a number the reader is being encouraged to feel rather than check.
- **No emoji status icons.** The verdict marks added in v2.0 are geometric *shapes* — full disc, half disc, empty ring, dash — carrying the verdict without colour. That is an accessibility gain, not an icon set.
- **No dark security-ops console.** Dark mode keeps the warmth and stays a document.
- **No full-width marketing hero.** The overview gained a **cover sheet**, which is a different object: no call to action, no pitch, no metric tile. A workpaper file has a cover; a product has a hero. The distinction is the whole discipline here, because "the page looks plain" leads to a hero section faster than to anything else.
- **Tabular figures everywhere.** Unchanged.

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
- [ ] No `w-*` or spacing utility resolves to nothing (see §11.6 — the replaced Tailwind scale silently deletes classes)
- [ ] Reduced motion: every reveal is visible, no tint chases the cursor, the indeterminate rule is static
- [ ] Every photograph is credited to a named photographer, and was looked at before selection

---

## 11. Revision 2.0 — *Warm instrument*

### 11.1 Palette

The neutral ramp stays warm and moves further from white. **No surface in the product is `#ffffff`.**

```css
--n-0:  #fdfbf6;   /* panel  — off-white, never pure white */
--n-25: #f6f2e8;   /* page ground — warm oat */
--n-50: #efe9db;   /* zebra, inset */
--n-500:#6a6353;   /* secondary text — 5.4:1 on ground */
--n-600:#524b3e;   /* body           — 7.6:1 on ground */

--accent-500: #1c6b84;   /* teal ink   — interactive, structural */
--warm-500:   #bb6640;   /* terracotta — second voice, NEVER status */
```

The ground carries three radial tints (teal, terracotta, green) at 5–7% alpha with `background-attachment: fixed`, plus an SVG `feTurbulence` grain laid **over the ground and under the content**. Grain on body text is noise; grain in the margins is paper.

**Chroma ceiling on the wash is about 7%.** At the point the tint becomes noticeable *as colour* it has become a gradient background, which is on the §1.1 reject list.

### 11.2 Type

`next/font/google` now actually loads Inter Tight, JetBrains Mono and Source Serif 4, with `display: swap` and Next's generated fallback metrics so the swap does not shift the line.

One size was added — `--fs-3xl`, fluid at `clamp(1.625rem, 4.4vw + 0.75rem, 2.375rem)` — used **once**, for the cover-sheet statement line. It carries a sentence. A 38px numeral in that slot would be the KPI tile §1.1 rejects. Fixed at 38px it ran to four lines on a 375px phone and read as a shouted headline; the clamp was the fix.

### 11.3 Motion

One rhythm, defined once in tokens and read by both the utility classes and the component CSS:

```css
--dur-fast: 120ms;  /* press, tint */
--dur-base: 200ms;  /* hover, focus, state */
--dur-slow: 340ms;  /* entrance, reveal */
--ease-out: cubic-bezier(0.22, 1, 0.36, 1);
```

| Motion | What state it reports | Where |
|---|---|---|
| Masthead condense + backdrop blur | You have scrolled away from the top | `Masthead` |
| Scroll-progress rule (2px) | How much of a long table remains | `ScrollProgress` |
| Scroll reveal, 40ms stagger | This content just entered view | `Reveal` |
| Cursor spotlight | The pointer is over this panel | `Spotlight` |
| Row rule wipe + tint | This row is under the cursor **or the keyboard** | `.row-interactive` |
| Panel lift (2px, warm shadow) | This surface is interactive | `.panel-raise` |
| Result rows, 30ms stagger, capped at 12 | Findings arriving in sequence | `RunConsole` |
| Plate desaturation easing back | The photograph is resolving under attention | `.plate-zoom` |
| Indeterminate rule | A run is in flight | `RunConsole` |
| Aperture mark rotating 45° | The masthead condensed | `Masthead` |

Still banned: decorative loops, animated counters, pulsing skeletons, celebration on `PASS`, and any transform on a `<tr>` — table layout handles it inconsistently, so the result-row entrance is **opacity only** and the stagger carries the sequence.

**Performance rules, which are the reason the above is affordable:**

- `Spotlight` and `ScrollProgress` never read layout inside an event handler. Pointer position is stashed and flushed once per `requestAnimationFrame`; the rect is measured on enter and on resize only. A `getBoundingClientRect()` inside `pointermove` is the standard way to lose 60fps.
- Every transition is `transform`, `opacity` or colour. Nothing animates a box dimension, so none of this can contribute to CLS.
- `Reveal` disconnects its observer after firing. A permanent observer per panel is a scroll-time cost for an effect that already happened.
- `Spotlight` bails out entirely under `pointer: coarse`.

**Reduced motion** is handled in a block placed deliberately *outside every `@layer`*, at the end of `globals.css`. `.reveal` starts at `opacity: 0` and is defined in `@layer components`; an override in `@layer base` only beats it because `!important` reverses cascade-layer order. That is true, and far too subtle a mechanism for the rule deciding whether a reader who asked for less motion sees the page at all. Unlayered declarations beat every layer outright.

Under `reduce`: reveals are visible, the spotlight is off, nothing lifts or scales, and the indeterminate rule becomes a **static filled rule** — still "something is running", without the loop.

### 11.4 The image programme

Four photographs, declared in `lib/imagery.ts`, each doing one job:

| Plate | Subject | Job |
|---|---|---|
| `statute` | Vidhana Soudha, Bengaluru | Cover sheet. The seat of the Karnataka legislature — the building where the law this product executes is made. Chosen over a glass tower because the subject here is a statute. |
| `estate` | Bengaluru under monsoon cloud | The estate under test is a real city; every record in it is synthetic. |
| `evidence` | Tied bundles of archive paper | Evidence before it was queryable. The gate asks the same question of both. |
| `structure` | Glass curtain wall on a steel grid | The control library: twenty-five controls on one frame. |

**Sourcing rules — the same rules this product applies to statutory text in `SOURCES.md`:**

1. **Every image is credited** to a named photographer with a link, though the Unsplash licence does not require it. A tool whose entire argument is *cite what you are standing on* cannot run uncredited images.
2. **Every URL was fetched and checked for 200, and every photograph was looked at.** This was not ceremony. The top-ranked "Bengaluru office building" result had a three-storey Christmas tree and toy houses filling the foreground; the top "server room" result was a neon-lit rack — the dark-ops-console cliché §1.1 rejects. Both carried clean, plausible alt text. **Alt text is not a substitute for looking.**
3. **No people.** Stock photographs of smiling colleagues are the fastest way to make a compliance tool look like a brochure.

**Treatment — a real duotone, not a tint.** The first attempt desaturated to 0.72 and laid a soft wash over the top, which left a bright green lawn and a blue sky sitting in the middle of a warm oat page looking pasted in. Desaturating a photograph *towards* a palette is not the same as mapping it *into* one. The plate now drives the image to greyscale, multiplies a teal-to-terracotta ramp over it, and screens a paper tone back into the shadows. Every photograph resolves to the same two inks, which is what makes four unrelated stock images read as one commissioned set. `isolation: isolate` contains the blend, so the result does not change depending on what the plate happens to sit on.

**Delivery:** plain `<img>` with a hand-built `srcSet` and `sizes`, not `next/image`. `images.unsplash.com` is already an image CDN doing format negotiation and width variants; proxying it would add a hop, a `sharp` dependency in the Docker path, and image-optimisation billing, in exchange for nothing. Each plate reserves its box with `aspect-ratio` so there is no CLS, and carries its own gradient, so a blocked CDN leaves a composed rectangle with a caption rather than a broken-image glyph in the middle of an audit report.

### 11.5 Responsive

- The masthead and tab rail are **sticky**, and their heights are **measured** (`ResizeObserver` publishing `--masthead-h` and `--tabnav-h`) rather than hardcoded. A guessed `top: 57px` fails quietly — as a gap of scrolling content showing between two sticky bars — the moment the type scale or the wrap point changes.
- At rest on a phone the identity block takes the whole row so the client name wraps at a sensible measure; once condensed it clamps to one line and shares the row with the role switch. The statutory date is reference, not navigation, so it is what goes first. Chrome on a 375×812 phone went from **about 450px to about 150px**.
- The tab rail scrolls the active tab into view on navigation, so "Report" is reachable on a 375px screen instead of sitting silently off-screen.
- Edge fades are scoped to **below 768px**. A mask is unconditional and the overflow is not: at desktop width the filter rail wraps and the tab rail fits, and the fade was eating the first six pixels of the word "Domain" to signal scrolling that could not happen. A cue for a state the element is not in is just damage.
- Suite checkboxes became **chips**: the whole 36px chip is the target, not a 13px native box.

### 11.6 Two latent bugs this revision exposed

Both predate v2.0 and had been shipping silently since Day 1.

**The fonts were never loaded.** §2.2 named three faces; `tokens.css` listed them in `--font-sans`, `--font-mono` and `--font-serif`; nothing ever fetched them. The product had been rendering in Segoe UI on Windows and system-ui elsewhere. It failed invisibly because the fallback stack is legitimate — the page looked *fine*, just anonymous.

**Every `w-*` utility was dead.** `tailwind.config.ts` replaces `theme.spacing`, which is correct: extending it would leave `rounded-2xl` and `shadow-lg` reachable, an explicit fail condition. But Tailwind derives `width` from `spacing`, so replacing it also deleted every numeric width. `w-32` on a table header emitted **nothing** — no rule in the stylesheet, no console warning, no error. Every table in the product had been laying itself out by content width, and the column widths written in the source had never once applied. Fixed by restoring the used steps under `theme.extend.width`.

> Both share a failure signature worth naming: **a declaration that is simply absent produces no error anywhere.** It is the same class of fault as the scheme-less `render.yaml` host and the `NEXT_PUBLIC_API_BASE_URL00` typo — the system does not break, it quietly does something else instead. The check that catches it is looking at the rendered result, not reading the source and agreeing with yourself.

### 11.7 Three faults the review pass caught in v2.0 itself

§11.6 lists bugs v2.0 *exposed*. These three it *introduced*, and all were found by looking at the rendered result rather than re-reading the source.

**Zebra rows had no hover state.** `.row-interactive:hover` sets `--accent-50`; the striping is applied in markup as Tailwind's `bg-n-25`. Hovering an odd row, the element reported `:hover` correctly and its computed background stayed `--n-25`. Half the rows in every table had no hover feedback, and the CSS read as correct in both files.

The interesting part is that the first diagnosis was wrong. Tailwind 3's `@tailwind` directives are a build-time bucketing, **not** native CSS cascade layers — a check in the browser showed both rules sitting unlayered, so the layer-order explanation could not be the cause. What resolved it was moving the rule so it wins on ordinary cascade terms, and then *verifying the computed colour changed* (`rgb(246,242,232)` → `rgb(231,241,242)`). Reasoning about the cascade from the source produced a confident wrong answer twice; the computed style produced the right one immediately.

**The focus ring was drawn on a 1px element.** The suite chips hide a real checkbox with `sr-only` so the whole 36px chip is the hit target — but `sr-only` collapses that input to a 1×1px clipped box, and the global `:focus-visible` ring went with it. Measured: input 1×1, chip 141×36. A keyboard user could tab through the five suites with no visible indication of where they were. Fixed with `.chip:focus-within`, so the ring is drawn on the thing the reader can see.

**The spotlight forced a layout on every scroll event.** `Spotlight` was written specifically to keep pointer tracking off the layout path — and then subscribed to `window.scroll` with a handler calling `getBoundingClientRect()` directly, unthrottled, firing whether or not the pointer was near the panel. Its own docstring claimed the opposite. The rect is now read inside the existing `requestAnimationFrame` flush, which bounds it to once per frame *and* only while the pointer is moving over the element; the scroll and resize listeners are gone entirely.

> The common thread with §11.6: **a comment asserting a property is not the property.** Two of these three shipped with documentation stating they did the right thing.

---

## 12. Revision 3.0 — *Tidal*

v2.0 made the product warm and considered. It was still read as too quiet. v3.0 answers a direct brief: **a bright, vibrant, colourful background with a gradient and continuous wave motion; depth and contrast; tiles that rise and respond to the cursor and to touch, equally on desktop and mobile.**

This reverses several v2.0 positions outright, and they are recorded here rather than quietly edited out of §1.3.

| v2.0 position | v3.0 position |
|---|---|
| Warm oat ground, tints capped at ~7% chroma | **A saturated sunset-to-sea gradient** that moves continuously |
| Motion must report state; no idle loops | **Continuous motion in the ground only** (waves, drifting colour). Everything the reader interacts with still moves only in response to them |
| Rules not shadows; one warm `raise` shadow | **Raised tiles** with layered shadows tinted toward the sea hue |
| Radius 2–3px, 10px for photographs only | **14px for tiles.** Controls inside them keep 2–3px |
| Photographs fully duotoned | **Photographs in colour** under a light wash, full colour on hover |

### 12.0 The rule that makes the rest possible

> **Text never sits on the moving ground.**

A gradient that runs from saffron to deep teal and moves under the page cannot guarantee contrast anywhere: grey caption text that passes 4.5:1 over saffron fails over coral. So every line of copy lives on a tile — including things that used to sit directly on the page in v2.0: page headers, the filter rail, figure captions and the table's scroll hint. The tile is 93% opaque (fully scrim-opaque on phones), so contrast is set by the tile and is the same wherever the ground happens to be under it that second.

This is what lets the ground be as vivid as the brief asks without the product becoming harder to read.

### 12.1 The ground

| Token | Hex | Role |
|---|---|---|
| `--ground-1` Saffron | `#ffc27a` | Warm corner, top left |
| `--ground-2` Coral | `#ff8f7a` | Warm mid |
| `--ground-3` Turquoise | `#52d1be` | Cool mid |
| `--ground-4` Deep sea | `#2a9db8` | Cool corner, bottom right |

A 125° linear gradient through all four, with three soft colour blooms (sun, coral, lagoon) drifting over it on 26s, 33s and 39s cycles. Chosen as a **warm/cool pair** so no single hue dominates. One colour reads as a brand splash; two temperatures read as a horizon. There's no purple and no electric blue, which are the recognisable AI-gradient cliché.

**Dark mode** keeps the same structure in deep tones (ember `#3a2019`, oxblood `#552723`, deep lagoon `#0f4a4a`, midnight sea `#0a2f43`) with dimmer waves. It doesn't read as a security-ops console.

### 12.2 Type

**Geist** replaces Inter Tight for all UI text. Inter is the default face of generated interfaces; Geist has the same neutrality with its own character. **JetBrains Mono** is unchanged for identifiers and evidence.

The cover-sheet statement line moved from serif to Geist, semibold, tracked tight (−0.03em). **Source Serif 4 is kept for one purpose only: verbatim statutory quotation** (`ClauseQuote`), where it marks quoted matter as quoted. That exception is deliberate and is the only serif in the product.

### 12.3 Motion — the waves

`AmbientBackground.tsx` is a **server component with no JavaScript**. Everything in it is a CSS animation of `transform`, so it runs on the compositor thread and can't block input, a test run, or scrolling.

- **Three wave layers** along the bottom of the viewport: deep (34s), mid (21s, reversed), foam (13s). Different speeds and depths of colour give **parallax**, so the slow dark back wave reads as further away than the fast pale front one. That's where the depth comes from: timing, not blur.
- **Seamless looping.** Each layer is one wave period drawn twice across a 200%-wide strip that slides left by exactly half its width. The path starts and ends at the same height with the same slope, so there's no seam and no visible jump. This is the one place linear easing is used: a wave that eased in and out would visibly stall once per cycle.
- **A static twin** of the gradient is painted on `html`, so the first frame, and any iOS overscroll bounce past the fixed layer, shows the same colours rather than a flash of white.

Verified in the browser: over 1.5s the three layers moved −16px, +27px and −43px respectively.

### 12.4 Tiles — rise and tilt

`SurfaceMotion.tsx` is mounted once in the layout and uses **event delegation**, so tiles stay server-rendered. Any element with `data-tilt` takes part.

| Input | Behaviour |
|---|---|
| **Mouse** | The tile rises 6px, scales to 1.012, rotates toward the cursor and catches light at the pointer. It settles on leave. |
| **Touch** | A press lifts the tile and tilts it toward the contact point, and release settles it. A press that turns into a scroll arrives as `pointercancel` and also settles, so dragging a list never leaves a card stuck mid-tilt. **Nothing calls `preventDefault`**: scroll, taps and links behave exactly as without it. |
| **Keyboard** | `:focus-within` raises the tile without tilting it. There's no pointer to tilt toward. |
| **Reduced motion** | Nothing is attached, and the stylesheet pins every tile flat. |

- **Tilt scales with tile width**: `6° × min(1, 360 / width)`. Rotation moves an edge by width × sin(angle), so 6° would swing a 700px panel's edges nearly 40px and make its text swim. Verified: a 454px tile peaks at 4.8°, a 343px tile at the full 6°.
- **Spring settle.** Rising uses a short ease-out; settling uses `cubic-bezier(0.34, 1.4, 0.64, 1)`, a small overshoot, so a released tile lands rather than stops.
- **Performance.** The pointer position is stashed and applied once per animation frame, with the rect read inside that frame. Only custom properties are written, and CSS turns them into a `transform`.
- **Not everything tilts.** Tables, the run console and the evidence viewer rise on hover but don't rotate. A surface moving under the reader while they select a checkbox or scroll a code block works against them.

Scroll reveal is also stronger: tiles now travel 24px and scale from 0.98 with a spring settle, so on a phone each one surfaces as it scrolls in.

### 12.5 Photographs

The duotone is lighter: `grayscale(0.45)` under a turquoise-to-coral multiply wash at 42%, and on hover `grayscale(0)` with the wash at 14%. The photographs are now in colour and belong to the palette.

The wash has **its own tokens** (`--plate-wash-a/b`), deliberately not the ground colours and not overridden in dark mode. The first build reused the ground tokens, and in dark mode the wash became `rgb(15,74,74)` → `rgb(85,39,35)`. A multiply wash darkens by definition, so the cover photograph rendered as a flat grey block. It was caught in the browser, not in review.

### 12.6 Performance and responsiveness

- **Frosting only above 768px.** `backdrop-filter` re-samples everything behind an element on every frame the ground moves, and on a phone with a dozen tiles that is the difference between smooth and not. Below 768px the tile is simply more opaque.
- **No horizontal overflow** at 375, 768 or 1280px (measured).
- **Grain above the ground, below content**: z-index 1, because at equal z-index the later-in-tree ambient layer would paint over it.

### 12.7 Still not negotiable

Unchanged from every earlier version:

- **No headline compliance percentage.** [PRD §7.3]
- **`INSUFFICIENT_EVIDENCE` renders in neutral ink, as a peer verdict.** The tiles and ground are decoration. They carry no status, and no verdict gets a colour, glow or motion the others don't.
- **No animated counters or celebration on `PASS`.**
- **No emoji.** Verdict marks remain geometric shapes.
- **No neon outer glows, and no custom cursors.**
- **Reduced motion:** the ground freezes (keeping its colour), tiles never rotate, reveals are immediate.

### 12.8 Where v3.0 departs from the `stitch-design-taste` rules

The skill was applied except where it contradicts the brief:

| Skill rule | v3.0 | Reason |
|---|---|---|
| Neutral base; gradient backgrounds discouraged | Vivid moving gradient | Explicitly requested |
| Maximum one accent | Teal and terracotta, plus the ground's four hues | Explicitly requested colour; the inks still never carry status |
| Serif banned in software UIs | One serif, for quoted statute only | Marks quoted legal text as quoted: a meaning, not a style |
| No three-equal-card rows | Three principle tiles kept on the overview | Each tile states a distinct engine behaviour (one clause, the gate, the seed), not decorative feature copy. The row collapses to one column below 768px |
| Use picsum, not Unsplash | Unsplash kept | Every URL was fetched and checked for 200, each photo was looked at, and all are credited (§11.4) |

Everything else in the skill is followed: Geist, no Inter, no pure black, no neon glows, no custom cursor, no emoji, transform/opacity-only animation, 44px touch targets, `dvh` rather than `vh`, and single-column collapse below 768px.
