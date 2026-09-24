# AssureLens: UI/UX Design Brief

| | |
|---|---|
| Version | 6.0, *Signal + Motion* (5.0 *Signal* earlier the same day) |
| Date | 24 September 2026 (v4.0 and v3.0: 23-24 September; v2.0: 22 September; v1.0: 21 September 2026) |
| Status | Shipped on branch `workd` |
| Related | [DESIGN.md](DESIGN.md) (the specification) · [PRD.md](PRD.md) · [TRD.md](TRD.md) · [SCHEMA.md](SCHEMA.md) |

> **v5.0 revision.** The built v4 product was judged dark, dull and low-energy, and the owner explicitly overrode every earlier visual position, including the muted severity scale and the neutral styling of `INSUFFICIENT_EVIDENCE`. v5 replaces the design at its foundation: a bright, light-first, high-contrast colour system; a real type scale; a ruled grid of flat colour blocks instead of translucent tiles over a moving gradient. **§14 is the full record**: the award research it rests on, the audit of v4, measured contrast for every pair, and what changed structurally. §§1-2 below are rewritten for v5. §§11-13 are kept as history and are **superseded** wherever they conflict with §14.

> [DESIGN.md](DESIGN.md) is the specification a new screen is built from; this file is the reasoning.

---

## 1. The aesthetic, in one line

**A bright instrument with a loud verdict.** It should look like a precise tool you trust at a glance: a white work surface, near-black ink, one cobalt voice and one lime highlighter, with the conclusions set larger and in stronger colour than anything decorative on the page.

The reference points are award-winning editorial data and fintech sites (§14.1), not the SaaS dashboard and no longer the photocopied workpaper.

### 1.1 Negative constraints (binding)

| ✗ Not this | Why it's wrong here |
|---|---|
| **Rounded cards floating on a grey page** | Still the templated AI dashboard. v5 uses a ruled grid with square corners. |
| **Moving or gradient backgrounds, translucent tiles, backdrop blur** | v4's ground made every text pair depend on what was moving behind it. Retired. |
| **Muted, desaturated status colour** | v4's severity and verdict inks sat at 1.3-1.4:1 luminance from each other. Status is now full strength. |
| **Small grey uppercase labels** | v4's 11px tracked labels measured 3.0-3.4:1. Labels are now 13px, sentence case, AA ink. |
| **Purple gradients, neon glows** | Still decoration where the content is a legal conclusion. Cobalt is used flat, never as a gradient. |
| **Emoji status icons** | Verdict marks remain geometric shapes. |
| **Big number + percentage-change tiles, any headline compliance %** | A product decision, not a visual one. [PRD §7.3] Large numerals are allowed only for counts and dates. |
| **Animated counters, confetti, progress celebration** | Compliance progress is not a game. |
| **Colour-only encoding** | Every verdict and severity has a word and a shape. |
| **Em-dashes in UI copy** | A generated-copy tell. Colons, commas, full stops. |

### 1.2 Positive direction

| Do this | Because |
|---|---|
| **Flat colour blocks for structure** | The reference set builds hierarchy from blocks of saturated colour, not from shadows. §14.2 P1 |
| **A type scale with real steps** | Display ≈ 5.75× body (92 / 16px). v4 topped out at 2.7× (38 / 14px). §14.2 P2 |
| **Rules and a grid, square corners** | One radius (zero), one shadow (overlays only). §14.2 P3 |
| **Mono for every identifier and measurement** | Data should read as data. Refs, seeds, hashes, counts, intervals. §14.2 P4 |
| **Maximum contrast for anything that must be read** | Every text pair ≥ 4.5:1, most ≥ 7:1, measured. §14.3 |
| **Tabular figures everywhere** | Unchanged. |

---

## 2. Design tokens

All colour, type, spacing and motion values live in `frontend/styles/tokens.css`; Tailwind (`frontend/tailwind.config.ts`) replaces its defaults with those tokens, so no default colour, radius or shadow is reachable. The v4 names (`n-*`, `accent-*`, `warm-*`, `verdict-*`, `ground-*`) no longer exist, so no component could keep v4 styling by accident.

The full palette, the type scale and the measured ratio for every pair are in §14.3 and [DESIGN.md §2-3](DESIGN.md).

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

- **Masthead**, not a nav bar: a solid cobalt band. The entity name carries the weight, product and engagement name are secondary. v5: fixed height, no condense on scroll, the statutory date in a lime block. [§14.4]
- **A ruled tab rail** of 48px cells; the active cell is a lime block with an ink foot. No pill nav, no sidebar. Six destinations do not need a sidebar.
- **Persistent footer disclosure** on an ink band. The synthetic-data and not-legal-advice statement is always visible, not a dismissible banner. [PRD §9]

---

## 4. Screens

### 4.1 Overview — *where do I stand*

Client view lands here. Three blocks, stacked, full width.

**A. Readiness by domain.** A horizontal segmented bar per domain (Notice & Consent, Security Safeguards, Retention & Erasure, Data Principal Rights, Third-Party & Transfers, AI Governance). Each bar segments into Pass / Fail / **Insufficient** / N-A, with counts, and **coverage % printed beside it, not inside it**.

> **No headline compliance percentage anywhere on this screen.** [PRD §7.3] If a reviewer asks where the score is, the answer is the FAQ in the README — a domain with 40% coverage and a domain with 95% coverage cannot be averaged into one honest number.

**B. Risk heatmap.** 5×5 likelihood × impact grid, findings plotted as counts per cell. Full-strength severity fill (`--sev-*`) with a numeral and an ink border, never colour alone. Clicking a cell filters the findings register.

**C. Evidence quality meter.** The screen's distinctive element and the product's thesis made visual. A horizontal band showing what proportion of in-scope controls have: *sufficient evidence* / *thin evidence* / *no evidence*. Reading directly: **"You have graded 60% of your estate. Here is the other 40%."**

### 4.2 Controls — the library

Dense table. 25 rows, no pagination, sticky header.

| Ref | Control | Domain | DPDP | ISO 27001 | NIST AI | Last result | Coverage |
|---|---|---|---|---|---|---|---|
| `DPDP-06-02` | Access to personal data is restricted… | Security | R6(1)(b) | A.5.15 | — | **Fail** | 100% |

- Ref in mono cobalt. Framework refs as sharp 12px mono tags; an unverified citation is dashed with a trailing "?".
- Filter rail above: domain, framework, verdict, executable-vs-documented.
- Row hover and keyboard focus: `--cobalt-tint` with a 3px cobalt bar at the left edge. No zebra (v5: hairlines only). No hover lift, no scale transform.
- Sort by any column; sorted column header carries a 2px accent rule.

### 4.3 Control detail

Two columns, 2:1.

**Left** — objective; clause reference with **the verbatim quoted text of the rule** (this is the credibility move: the reader sees the statute, not a paraphrase); test procedure; evidence contract with items and status; result history (small step chart, last 5 runs).

**Right** — current verdict block (§6); statistics (n, N, coverage, point estimate, Wilson CI, method named); thresholds applied, with **any override flagged in accent**; linked findings.

### 4.4 Test run console

The one screen permitted motion — and only functional motion.

- Suite selector, seed field (pre-filled `42`, editable — visibly reproducible), Run.
- Results stream into a log-style list as each control resolves: `ref · control · verdict · n/N · elapsed`.
- **Run progress:** a 3px cobalt indeterminate rule. No spinners (v5 removed the one on the Run button), no skeletons that pulse, no progress celebration.
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

Paper metaphor, and the only place it is allowed: white page on the `--inset` field, page-width column, print margins visible, Geist headings on the v5 scale. Export buttons: Workpaper (DOCX), Executive summary (DOCX).

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
| Colour | v5: the **ink chip** (`--insufficient`, 19:1), the highest-contrast fill in the set. Never red, amber, or yellow. See §14.5. |
| Icon | None, or a neutral horizontal rule glyph. **Never** ⚠ 🚨 ❗ |
| Language | *"Insufficient evidence"* — never "Unknown", "Error", "Incomplete", "N/A", "Pending" |
| Weight | Same chip, size and weight as Pass and Fail. It is a peer verdict, not a lesser one. |
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

`Insufficient evidence` as the ink chip, followed by the gate code (`G3`) as a dotted-underline `<abbr>` tooltip target. Never a dash, never blank — an empty cell reads as "not run", which is a different and less honest thing.

---

## 7. Accessibility

| Requirement | |
|---|---|
| Contrast | WCAG AA throughout, measured (§14.3). Body `ink-2` on surface 10.9:1, primary ink 19.0:1, labels 6.9:1. |
| Colour independence | **Every** severity and verdict carries a text label. Colour is redundant encoding, always. |
| Keyboard | Full path through the demo without a mouse. Tables: arrow navigation, Enter to expand, Esc to collapse. |
| Focus | 3px `--cobalt` outline, 2px offset. Never `outline: none`. |
| Screen reader | Tables use real `<th scope>`. Run console is an `aria-live="polite"` region so verdicts are announced. |
| Motion | `prefers-reduced-motion`: reveals are immediate, the scroll-progress rule is hidden, the indeterminate rule is static. |
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

`Masthead` · `RoleSwitch` · `TabNav` · `DataTable` (sortable, expandable, sticky header — the workhorse) · `VerdictBadge` · `VerdictBlock` · `SeverityIndicator` · `ReadinessBar` · `RiskHeatmap` · `EvidenceQualityMeter` · `StatPair` (label/value, tabular) · `ClauseQuote` (verbatim rule text, 20px behind a 4px cobalt rule) · `EvidenceViewer` (mono, request/response) · `ThresholdRow` · `RunConsole` · `EffortImpactScatter` · `ColumnMapper` · `ReportPreview` · `DisclosureFooter`

Built with **fully custom styling from the tokens** in `tokens.css`; v5 adds `PageHeader` and `DeadlineCount`. Tailwind is configured to the token scale — no default Tailwind palette, no default radius scale, no default shadows. An untouched shadcn look is an explicit fail condition. [§1.1]

---

## 10. Design review checklist (Day 10 gate)

Run before declaring the build done. Any ✗ blocks.

- [ ] No element from the §1.1 negative list appears anywhere
- [ ] No headline compliance percentage exists on any screen
- [ ] `INSUFFICIENT_EVIDENCE` renders neutral, with why / how to resolve / owner, in every location
- [ ] All numerals are tabular and align in columns
- [ ] Every corner is square (v5 radius is 0), except the indeterminate rule
- [ ] No shadow on the page; `--shadow-overlay` only on genuine overlays
- [ ] Every severity and verdict has a text label, not colour alone
- [ ] Full demo path completes by keyboard alone
- [ ] Contrast checked on every token pair in both themes
- [ ] Phone width (390px): no horizontal body scroll, demo still completable
- [ ] Dark mode keeps every pair at AA (§14.3) and does not read as a security-ops console
- [ ] No em-dash in any visible UI string
- [ ] Synthetic-data disclosure visible on every screen
- [ ] `design-taste-frontend` / `ui-ux-pro-max` review passed against this brief
- [ ] No `w-*` or spacing utility resolves to nothing (see §11.6 — the replaced Tailwind scale silently deletes classes)
- [ ] Reduced motion: every reveal is visible, no tint chases the cursor, the indeterminate rule is static
- [ ] Every photograph is credited to a named photographer, and was looked at before selection

---

## 11. Revision 2.0 — *Warm instrument*

> **Superseded by §14 (v5.0).** Kept as a record of the reasoning at the time. Where it conflicts with §14 or [DESIGN.md](DESIGN.md), those win.

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

> **Superseded by §14 (v5.0).** Kept as a record of the reasoning at the time. Where it conflicts with §14 or [DESIGN.md](DESIGN.md), those win.

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

---

## 13. Revision 4.0 — *Living Ground*

> **Superseded by §14 (v5.0).** Kept as a record of the reasoning at the time. Where it conflicts with §14 or [DESIGN.md](DESIGN.md), those win.

> Status: **approved 24 September 2026, palette B.** Phases 1–3 complete; see §13.9 for the decisions and the measured results. Phase 4 (finish) has not started: the performance budget in §13.7 is missed by two pre-existing transitions and needs a decision first.

v3.0 made the ground vivid and gave the tiles a physical response. v4.0 makes the ground feel **alive and expensive** without moving anything the reader needs to read. The rule from §12.0 still carries all the weight: **text never sits on the moving ground.**

### 13.0 Non-negotiables, restated as the test every item below must pass

1. Text never sits on the moving ground. Every line of copy is on a tile whose opacity sets its contrast; WCAG AA minimum on every text/tile pair, both themes.
2. Continuous motion only in the ground and purely decorative, non-text layers. Tiles, tables and text move only in response to the reader.
3. The ground carries no status. `INSUFFICIENT_EVIDENCE` renders in neutral ink as a peer verdict: same weight, slot and motion as Pass and Fail.
4. No headline compliance %, no animated or tweened numbers, no celebration on PASS, no emoji, no custom cursor, no neon outer glows, no transform on `<tr>`. Tables, run console and evidence viewer never tilt.
5. No purple or electric blue unless approved.
6. Reduced motion: the ground renders one static frame with its full colour, every micro-movement stops, and all content is visible.
7. Only transform, opacity, colour and shader uniforms animate. Zero CLS from any effect.

Every subsection ends with one line per item showing which of these it could threaten and how it doesn't.

### 13.1 Palette: three directions (choose one)

Six hues each, ordered warm to cool, read by the shader and by the CSS fallback alike from `--ground-1..6`. None uses purple or electric blue; the most blue hue in any set is A's deep sea `#2a9db8`, carried over from the approved v3.0 palette.

| | Light (1 → 6) | Dark (1 → 6) | Reasoning |
|---|---|---|---|
| **A — Tidal Coast** | `#ffc27a` saffron · `#ff8f7a` coral · `#f4b3a0` sand rose · `#9be3d2` sea glass · `#52d1be` turquoise · `#2a9db8` deep sea | `#3a2019` · `#552723` · `#5a3226` · `#16504a` · `#0f4a4a` · `#0a2f43` | Continuity with v3.0. The two new intermediates (sand rose, sea glass) give the mesh somewhere to blend instead of snapping warm to cool. Reads as a coastline at golden hour: calm, the least surprising of the three. |
| **B — Spice Market** | `#f6c453` turmeric · `#ffa24c` marigold · `#f2745c` chilli coral · `#93c572` cardamom · `#3baa8c` jade · `#1f7a80` deep teal | `#3b2a0e` · `#4a2410` · `#4a1b17` · `#1e3a1c` · `#0f3b33` · `#0b2b30` | Warm-dominant, the most saturated. Rooted in the engagement's place without being a postcard. The greens stop it tipping into an all-orange "sunset" cliché. Highest energy; the photos have to hold their own against it. |
| **C — Tea Garden** | `#ffb870` marigold · `#e6e27a` citron · `#9bd38a` tea leaf · `#5ccb9f` mint · `#20a57e` emerald · `#2b8c99` lake teal | `#3e2a12` · `#2e2f12` · `#1f3a1c` · `#103d30` · `#0b3a2c` · `#0c3440` | Cool-green dominant, the quietest to read beside dense tables. One marigold counterpoint keeps it from going monochrome. Greens read as "growth" and are easiest on the eye across a long session. |

Screenshots of each on Overview and Controls at 1440 and 375px are listed in the Phase 2 report.

- *NN1/3:* the palette only paints the ground; tiles, ink and verdict tokens are untouched, so contrast is unchanged and no hue can be read as a status.
- *NN5:* no purple, no electric blue in any set.

### 13.2 The ground: `LivingGround` (raw WebGL, no library)

- **Colour field.** Six colour points on a 3×2 lattice, each on its own slow orbit (110–160s per lap), blended by inverse-distance weight at power 2.4 into a mesh gradient, warped by two octaves of simplex noise. A colour region crosses roughly one viewport width in 40–60s. The first cut used power 1.6, which averaged all six hues toward a muddy grey-beige; power 2.4 plus a 15% chroma lift keeps each region its own colour.
- **(a) Pointer parallax.** The warp origin eases toward the pointer (lerp 0.06 per frame), maximum offset 3% of the viewport. The colour field moves at half that; near motes move up to 1.5×, which is where the depth comes from. On touch it follows the last touch point. Nothing calls `preventDefault`.
- **(b) Scroll response.** Flow speed rises with scroll velocity and settles back on a slightly under-damped spring (stiffness 60, damping 10.8), so a flick surges the flow and it lands with a little overshoot. Scroll position is read **once per frame inside the render loop**, not in a scroll listener, so there is no scroll handler at all.
- **(c) Light motes.** Sixteen soft, out-of-focus Gaussian discs drifting upward at 4–10px/s with a sinusoidal sway. Size (4–15px), opacity (0.10–0.30) and pointer parallax all scale with depth. Drawn in the same shader pass; no DOM nodes.
- **(d) Film grain.** The existing SVG grain, now oversized to 200% and stepped between six offsets per 0.5s (12fps) with `steps(1)`: one pre-rasterised texture translated on the compositor, never repainted. Effective opacity ~4% light, ~3% dark. It stays above the ground and below content (§12.6's z-order). It is CSS rather than shader grain so it stays crisp: the shader renders at half resolution and grain upscaled from there turns to soft blobs.
- **(e) Waves.** See §13.3.
- **(f) Decorative travel.** A hairline highlight laps the border of the cover sheet and the three principle tiles once per 14s, drawn inside the border at ≤20% opacity with no blur outside it. The masthead aperture mark rotates one turn per 60s. Never on tables or text-bearing controls. *(Phase 3.)*

- *NN2:* all of (a)–(f) are in the ground or on decorative, non-text layers. Tiles still move only on hover, press, focus, scroll-entry.
- *NN3:* motes, grain and highlights are colourless or palette-derived and never sit near a verdict.
- *NN7:* the shader animates only uniforms; grain, waves, highlight and aperture animate only `transform`/`opacity`. The canvas is `position:absolute; inset:0` in a fixed layer, so it cannot shift layout.

### 13.3 Waves: kept as CSS, on top of the canvas

The three seamless wave layers stay the v3.0 CSS layer, stacked **above** the WebGL canvas and below content, rather than being ported into the shader:

1. **They survive the context.** If `webglcontextlost` fires, the canvas unmounts and the CSS ground returns underneath waves that never stopped. Shader waves would vanish with the context.
2. **They stay crisp.** The shader renders at 0.5×; wave crests upscaled from half resolution would soften visibly. CSS waves are vector at full resolution.
3. **They cost nothing extra.** Three `transform` animations on the compositor versus extra per-pixel work in a shader already doing noise, six-point blending and sixteen motes.
4. **They are already proven** seamless and measured (§12.3).

The cost is one extra composited layer, which is negligible.

- *NN6:* the existing reduced-motion rule already freezes them.

### 13.4 Tile finish (Phase 4)

Every tile gets, in addition to the §12.4 behaviour:

- a 1px **inner top highlight** (`inset 0 1px 0`, white ~50% light / ~8% dark);
- a 1px **low-alpha outer hairline**, dark on light and light on dark, replacing today's light-only edge;
- a **three-layer shadow**: contact (0 1px 1px), mid (0 6px 14px) and ambient (0 24px 48px), each tinted toward the ground hue, never neutral grey;
- **2% noise** inside the tile, on a fixed-size pseudo-element so it cannot repaint on scroll;
- frosting above 768px only (§12.6), unchanged.

- *NN1:* the noise and highlight are ≤2% and ≤50% alpha on a 93% tile; text contrast is re-measured after the change (§13.8).

### 13.5 Typography, spacing and states (Phase 4)

- **Spacing:** every margin, padding and gap resolves to `--sp-*`. The audit found all spacing already on-scale; the off-scale values are **sizes** and **tracking**, listed in the Phase 2 report and fixed in Phase 4.
- **Type:** `text-wrap: balance` on headings, `pretty` on prose. Tracking tightens as size grows (a token per size step). Emphasis by Geist's weight axis rather than size jumps. Only OpenType features Geist actually ships, verified against the font file before use. Tabular numerals everywhere (unchanged). Filing-style section numbers (`§01`, `§02`) in JetBrains Mono on page-level headings.
- **Microstates:** every interactive element gets a designed default / hover / focus-visible / active / disabled / loading. The gap matrix is in the Phase 2 report.
- **Micro-interactions:** buttons press to `scale(0.97)` with a spring release; a soft sheen follows the pointer across primary buttons; the focus ring animates in over `--dur-fast`; the tab underline slides between tabs as one element.
- **Designed states:** API unreachable, no runs yet, a suite returning zero rows. Each says what happened and what to do, and uses the hairline indeterminate rule; no spinners, no pulsing skeletons. The Run button's current spinner is removed for the same reason.
- **Entrance choreography (first load only):** ground fades in over 600ms, masthead next, tiles stagger at 40ms, with the whole sequence ≤900ms. It never blocks input, and is skipped on client-side navigation and under reduced motion.
- **Route transitions:** React `<ViewTransition>` as sanctioned by the Next 16 guide (`name` + `share="morph"` + `default="none"`), morphing the control ref from its table row into the control-detail heading. Browsers without the View Transitions API navigate instantly.
- **The Aperture** (Overview cover sheet): see §13.6.

- *NN2:* the sheen and focus ring respond to the reader; the entrance runs once; no text moves continuously.
- *NN4:* no transform lands on a `<tr>`. The route morph names a `<span>` inside the cell, not the row.
- *NN6:* entrance, sheen, press spring and view transitions all collapse under reduced motion.

### 13.6 The Aperture (Phase 4, pending a threshold decision)

On the Overview cover sheet, the reader sets **k** (successes) and **n** (trials) with labelled range inputs. An SVG band shows the 95% Wilson interval against the threshold rule, and the verdict slot switches between **Insufficient evidence / Pass / Fail**, with its gate code, using one identical cross-fade for all three. It is input-driven only, keyboard operable, and announced through an `aria-live` region.

Wilson is a pure function in `frontend/lib/`, asserted with `node -e` so that 12/12 at z=1.96 gives a lower bound of **0.7575 ± 0.0005**.

**Blocked on a decision:** the frontend holds no gate constants, and the backend's (`min_sample_n = 30`, `max_ci_width = 0.20`, `min_coverage_pct = 10.0`) define when the gate fires, not what separates Pass from Fail. No existing constant is a pass/fail rate. It will not be invented.

- *NN3:* the three verdicts share one component, one weight and one transition. Pass gets nothing Insufficient does not.
- *NN4:* the interval bounds update instantly on input and are never tweened.

### 13.7 Performance budget and how it is enforced

| Rule | Value | Where |
|---|---|---|
| Render resolution | 0.5× of CSS size, upscaled by CSS | `RENDER_SCALE` |
| DPR cap | 1.5 fine pointer, 1 coarse pointer | `dprCap` |
| Frame cap | 30fps when `saveData` or `hardwareConcurrency <= 4` | `minFrameMs` |
| Hidden tab | loop cancelled on `visibilitychange` | `onVisibility` |
| Software GL | refused via `failIfMajorPerformanceCaveat` → CSS ground | context options |
| Context lost | canvas unmounts → CSS ground | `onLost` |
| Handlers | pointer/resize only stash numbers; all reads once per frame | — |
| **Budget** | **p95 frame time ≤ 16.7ms at 1440px while scrolling Controls; no long task >50ms attributable to the ground** | measured in Phase 3 |

Frame samples are exposed on `window.__livingGround.frames` for the Phase 3 measurement.

**A defect caught in the first cut:** the CSS blooms were retired on a timer while the canvas was revealed inside a `requestAnimationFrame`. When frames were throttled, the timer won: the blooms vanished and the canvas never appeared, leaving a flat ground that was neither engine. The canvas is now revealed only inside the frame that first draws it, and the blooms are retired only by the canvas's own `transitionend`. This is the §11.7 lesson again, a timer standing in for an event.

### 13.8 Reduced motion

| Layer | Under `prefers-reduced-motion: reduce` |
|---|---|
| WebGL ground | One static frame, full colour. The loop never starts. |
| Motes, parallax, scroll surge | Frozen in that frame. |
| Grain | Stops on its first step. |
| Waves, blooms | Frozen (existing §12 rule). |
| Border highlight, aperture spin | Stopped. |
| Entrance choreography | Skipped; everything visible immediately. |
| Tile tilt, button spring, sheen | Off; hover states remain as colour only. |
| Route transitions | Instant. |

**Also found in the audit:** content revealed on scroll starts at opacity 0, so anything that renders the page **without scrolling it** (printing, full-page capture) shows below-the-fold tiles as blank. For a tool that prints workpapers that breaks NN6, and a `@media print` rule forcing every reveal visible ships in Phase 4.

### 13.9 Decisions and Phase 3 results

**Decisions (24 September 2026):** palette **B, Spice Market**; §13 approved as written; the Aperture judges Pass/Fail against a **5% tolerable exception rate** (Pass when the Wilson lower bound is ≥ 0.95, Fail when the upper bound is < 0.95, otherwise the gate decides), with G1/G2 mirroring `backend/app/engine/thresholds.py` (`min_sample_n = 30`, `max_ci_width = 0.20`). The skill's flags on em-dashes, per-tile eyebrow labels and hand-drawn SVG marks are **noted, not actioned**: fixing them means rewriting copy and adding an icon dependency, both outside scope.

**Shipped in Phase 3:** palette B baked into `--ground-1..6` with the candidate block and the `?ground` switch removed; the border light (§13.2f) on the cover sheet and principle tiles; the aperture spin.

**Fallbacks, all measured, all pass:**

| Test | Result |
|---|---|
| WebGL unavailable | CSS ground, canvas never shown, blooms on, waves moving |
| `webglcontextlost` mid-session | canvas unmounted, engine attribute removed, blooms back, waves never stopped |
| Reduced motion | one static frame, 0 loop frames in 1.5s, 6/6 reveals visible without scrolling, border light hidden, 0 running animations |
| Hidden tab | loop frozen while hidden, resumed on visible |
| Transitions disabled | blooms retired correctly (see defect below) |

**Defect found by measurement:** `transitionend` never fires for a zero-duration transition, so where transitions are switched off the blooms under an opaque canvas were never retired and both grounds rendered at once. The canvas now also checks its computed `transition-duration` once shown.

**Performance: budget MISSED as shipped, and the cause is not the ground.** p95 while scrolling Controls, production build, 1440×900, integrated GPU (Intel Iris Xe):

| Condition | p95 |
|---|---|
| Full v4 as built | 33.6 / 50.2 / 66.6 ms (three runs) |
| Full v4, WebGL ground idle (no scroll) | 16.9 ms |
| Full v4 while scrolling, **neither trigger below active** | **16.9 / 16.9 ms, within budget** |
| … plus rows transitioning under the cursor | 33.5 ms |
| … plus the masthead condense transition | 33.4 ms |
| v3.0 CSS ground (WebGL off), dev build | 83.4 ms |

At 375px (mobile emulation, coarse pointer, DPR 3 → canvas capped to 188×406) the full stack measures **33.4 ms**.

The WebGL ground, the frosting, the grain and the waves together fit the budget. Both causes are v2/v3 transitions that run **during** scroll: the masthead's `transition-all` animating padding (layout on every frame) each time the scroll crosses 24px, and table rows running their background and edge-rule transitions as they slide under a stationary cursor. The fix is a decision the brief reserves for the reader of this report, so it is not applied.

---

## 14. Revision 5.0: *Signal*

v4 was used and rejected: it read as dark, dull and low-energy, and the previous round had only changed colour values. The brief for v5 was a **base-level** redesign (colour, type, spacing, layout, component structure) with full authority to override every earlier position.

### 14.1 Research: award-winning references

Only sites whose award could be confirmed on the awarding body's own page are cited. Each live site was opened at 1440×900 and its computed styles sampled, so the notes below describe what the site does, not what it is remembered to do.

| Site | Award (verified) | Colour strategy | Type hierarchy | Density / spacing | Why it feels bright and premium |
|---|---|---|---|---|---|
| **Breaking** (plastics data science; Maven Creative, The Limbo Society) | Awwwards Site of the Day, 14 Aug 2024, + Developer Award; tagged *Data Visualization* | Flat electric cobalt `#2D41D3` floods whole sections, white type on it; acid yellow-lime as the highlighter; pale ground between blocks | Grotesk display at poster size (~130px) against ~20px body; one family, weight does the rest | Full-bleed colour bands; generous section padding; one idea per band | Colour is used as **surface**, not tint. One saturated hue plus one high-key accent. No gradient, no shadow |
| **Shift5** (fleet and defence operational intelligence; Non-Linear Studio) | Awwwards Site of the Day, 2 Mar 2026; tagged *Data Visualization, Retro* | Hard colour blocks on a grid: vermilion, light grey, near-black `#202020` | 200px display, tracking −4px; mono (NonSans) for the "System status" data list | A strict grid of rectangles; data set as a numbered mono list | Square corners, zero shadow, a ruled grid. Data looks like instrumentation |
| **Jeton** (payments / e-wallet; Bürocratik) | Awwwards Site of the Day, 27 Jan 2025, + Developer Award (7.8) | One brand colour, saturated coral-red `#F73B20`, used big | Sequel Sans, headline 106px at weight 500 vs 16px body | Very few elements per viewport | A single committed hue at full saturation, and headline weight 500 rather than bold |
| **AI in Banking UX Design** (Vide Infra) | CSS Design Awards Website of the Day, 15 Nov 2024 (scores 20/20 UI, UX, Innovation) | White ground, black ink in the reading sections | PP Neue Montreal, 235px display with −0.05em tracking; body 19px | Wide margins, long reading measure kept under control | Extreme scale contrast between display and body; body text is *large* |
| **Madar** (logistics management platform; Vide Infra) | Awwwards Site of the Day, 19 Sep 2025 | Navy `#172E64` + orange `#FF6340` (Awwwards palette listing) | Not verified: the live site could not be reached at a verifiable URL | n/a | Listed for the palette only: one deep structural hue plus one hot accent |
| **Navigate** (Web3 data platform; Resn) | Awwwards Site of the Day, 16 Apr 2025; tagged *Data Visualization, Colorful* | Orange `#FF6D38` + periwinkle `#8584FF` (Awwwards palette listing) | Not verified (site timed out) | n/a | Listed for the palette only |

Sources: [awwwards.com/sites/breaking](https://www.awwwards.com/sites/breaking) · [awwwards.com/sites/shift-5](https://www.awwwards.com/sites/shift-5) · [awwwards.com/sites/jeton](https://www.awwwards.com/sites/jeton) · [cssdesignawards.com/sites/ai-in-banking-ux-design/46554](https://www.cssdesignawards.com/sites/ai-in-banking-ux-design/46554) · [awwwards.com/sites/madar](https://www.awwwards.com/sites/madar) · [awwwards.com/sites/navigate](https://www.awwwards.com/sites/navigate). No Webby or FWA winner in these categories could be verified on the awarding body's own page within the session, so none is cited.

### 14.2 The recurring principles, and how v4 broke each

| | Principle across winners | What v4 did instead |
|---|---|---|
| **P1** | **Saturated colour as flat surface.** One structural hue plus one high-key accent, used as blocks. | Colour lived only in a moving gradient *behind* 93%-opaque off-white tiles. Everything you read sat on the same near-white, so the colour was felt as noise at the edges, never as structure. |
| **P2** | **Extreme type-scale contrast.** Display 100-235px against 16-19px body, one grotesk, weight 400-500 for display. | 83 of 91 font-size uses were 11-13px. The largest size (38px) was used once. Default UI was 13px, body 14px. Hierarchy had nowhere to come from, so everything read at the same volume. |
| **P3** | **Grid and hard edges, not floating cards.** Square corners, rules, zero or near-zero shadow. | 14px-radius tiles with a layered drop shadow, tilting toward the cursor: exactly the "rounded cards floating on a page" the v1 brief rejected, dressed up with motion. |
| **P4** | **Mono as the data voice.** Identifiers and measurements set as instrumentation. | Mono existed but at 11px in `n-400`/`n-500` grey, so the data was the faintest thing on the page. |
| **P5** | **Maximum contrast for what must be read.** Near-black on white, white on the brand hue. | Labels at 3.0-3.4:1, severity high/medium below 4.5:1, verdict colours 1.3-1.4:1 apart in luminance (§14.3). |

### 14.3 Contrast, measured

Computed with the WCAG 2.x relative-luminance formula (script: `contrast.py`, kept with the session artefacts). v4's tile is 93% opaque, so it was composited over the ground before measuring.

**v4 (as shipped), worst cases:**

| Pair | Ratio | |
|---|---|---|
| `n-400` 11px uppercase labels on tile over deep teal | 3.23:1 | fails AA |
| `n-400` on zebra row `n-50` | 3.02:1 | fails AA |
| `verdict-na` on tile | 3.23:1 | fails AA |
| `sev-high` on tile | 4.14:1 | fails AA |
| `sev-medium` on tile over teal | 4.49:1 | fails AA |
| unchecked chip box `n-300` vs panel (UI, needs 3:1) | 2.20:1 | fails |
| hairline `n-100` vs tile | 1.31:1 | invisible |
| pass vs fail ink (luminance only) | 1.28:1 | indistinguishable in greyscale |

**v5 light:**

| Pair | Ratio | Level |
|---|---|---|
| ink `#0d1017` on surface `#ffffff` | 19.03:1 | AAA |
| ink on page `#f4f5f7` | 17.44:1 | AAA |
| body `ink-2 #363d4a` on surface | 10.92:1 | AAA |
| meta/labels `ink-3 #525a69` on surface / page / inset | 6.94 / 6.36 / 5.86:1 | AA |
| link cobalt `#2436e6` on surface / inset | 7.65 / 6.46:1 | AAA / AA |
| white on cobalt masthead, primary button | 7.65:1 | AAA |
| white on cobalt-deep (hover) | 9.88:1 | AAA |
| ink on lime `#cdf23a` (active tab, highlight) | 14.82:1 | AAA |
| white on PASS `#0b8048` | 5.01:1 | AA |
| white on FAIL `#d0231a` | 5.33:1 | AA |
| white on INSUFFICIENT `#0d1017` | 19.03:1 | AAA |
| N/A text on surface | 6.94:1 | AA |
| pass / fail as inline text on surface | 5.41 / 5.91:1 | AA |
| severity: white on critical / ink on high / medium / low | 5.33 / 7.30 / 12.39 / 10.22:1 | AA / AAA / AAA / AAA |
| control borders `#7d8697` vs surface (UI) | 3.67:1 | ≥ 3:1 |
| focus ring cobalt vs surface (UI) | 7.65:1 | ≥ 3:1 |

**v5 dark** (surface `#151821`): ink 16.10, ink-2 10.57, ink-3 6.99, link `#9aa5ff` 7.77, pass text 9.78, fail text 6.98, white on cobalt block 6.61, ink on PASS / FAIL / INSUFFICIENT fills 8.62 / 6.96 / 17.65, ink on lime 15.14, control border 3.85:1. Every text pair clears AA and most clear AAA.

**One known limit.** The severity-high (2.61:1) and severity-medium (1.54:1) *fills* do not separate from white as shapes. Their text passes (7.3 and 12.4:1), and every severity chip carries a 1px ink border and a word, so the boundary and the meaning never depend on the fill.

Rendered values were also read back from the browser (`getComputedStyle`) to confirm the chips render the tokens (light Fail: white on `rgb(208,35,26)`; dark Fail: `rgb(11,13,18)` on `rgb(255,107,95)`).

### 14.4 What changed, structurally

| Layer | v4 | v5 | Principle |
|---|---|---|---|
| **Ground** | WebGL mesh gradient + CSS waves + film grain + drifting blooms (`LivingGround`, `AmbientBackground`) | A flat `#f4f5f7` page. The six decorative components (`LivingGround`, `AmbientBackground`, `EdgeTravel`, `SurfaceMotion`, `Spotlight`, `ScrollProgress`) are **deleted** | P1, P5 |
| **Surfaces** | `.panel`: 93%-opaque tile, 14px radius, tinted drop shadow, backdrop blur, 3D tilt | `.ruled` grid (1px ink gaps between white cells), `.sheet` (white, 1px ink frame), `.section-rule` (2px ink top rule). Radius 0 everywhere, no shadow on the page | P3 |
| **Colour** | Oat/teal/terracotta, muted severity, neutral-grey Insufficient | Cool neutrals, cobalt used as flat blocks (masthead, cover fact block, primary action), lime as highlighter (active tab, `<mark>`, scroll progress), full-strength verdict and severity fills | P1, P5 |
| **Type** | 11/12/13/14px for almost everything; one 38px line | 12 / 13 / 14 / **16 body** / 20 / 28 / 36-56 page title / 40-64 counts / 44-92 cover display; tracking tightens with size; nothing below 12px | P2 |
| **Labels** | 11px uppercase, 0.14-0.18em tracking, 3.2:1 | `.label`: 13px, sentence case, weight 500, 6.9:1 | P5 |
| **Masthead** | Translucent veil, condensed on scroll (scroll listener + animated padding) | Solid cobalt band, fixed height, no scroll listener; deadline in a lime block | P1 |
| **Navigation** | Text tabs with a 2px underline | Ruled rail of 48px cells; active cell is a lime block with an ink foot | P1, P3 |
| **Page headers** | Title boxed inside a tile (text could not sit on the ground) | `PageHeader`: 36-56px title standing on the page, 16-20px lede | P2 |
| **Overview** | Stack of tiles: cover, three equal principle cards, two photo tiles | One ruled cover grid: display statement (white), cobalt fact block with the day count, full-colour photograph, the three commitments as a numbered list | P1, P2, P3 |
| **Controls** | Intro tile + photo; text-link filter rail; 12px zebra table | Page title + ruled count strip (25 / 13 / 12 / 1 in 40-64px mono); filters as 44px toggle blocks (active = ink fill); 14px table, 12/16px cells, inset header band with 2px ink rule, cobalt hover bar | P2, P3, P4 |
| **Control detail** | Grid of tilting tiles with 11px uppercase headings | Title + ruled fact strip; main column in `section-rule` sections with 20px headings; side column in `sheet` asides with inset heading bands | P2, P3 |
| **Run console** | Suite chips with pale tint, spinner on Run | 44px toggle blocks (selected = ink fill, lime check); Run button states the count ("Run 5 suites"), no spinner; ink results header band with per-verdict counts | P1, P4 |
| **Verdicts** | Coloured text + 9px mark | Solid chips, one size and weight; Insufficient evidence is the **ink** chip | P5 |
| **Statute quotation** | Source Serif 4 | 20px Geist behind a 4px cobalt rule, lime "Legal basis" tag. The serif is no longer loaded | P2 |
| **Photographs** | Duotoned into the palette, 10px radius | Full colour, square, reserved box | P1 |
| **Scroll progress** | JS component with a scroll listener | CSS scroll-driven animation (`animation-timeline: scroll()`), no JavaScript; hidden where unsupported and under reduced motion | P4 (no cost) |

**Kept because it was right:** no headline compliance percentage; every verdict and severity has a word and a shape; tabular figures; `row-interactive` answering keyboard focus as well as hover; measured sticky heights; `Reveal` failing visible; the print rule; the full reduced-motion block. No npm dependency was added (Geist and JetBrains Mono were already loaded through `next/font`).

### 14.5 The Insufficient-evidence decision, revisited

The owner lifted the rule that `INSUFFICIENT_EVIDENCE` must be neutral grey. The **principle** behind that rule, that it is a peer verdict and never a warning, is kept; its **rendering** changes. In v4, grey ink next to coloured Pass and Fail read as the lesser verdict: the absence of a result. In v5 it is the ink chip, the highest-contrast fill in the set (19:1), same size, weight and slot as the others. It is still never red, amber or yellow.

### 14.6 Tooling used, and what was missing

- `design-taste-frontend` was loaded. Its own §13 declares dashboards and data tables out of scope, so only its anti-default rules (em-dash ban, no three-equal cards, eyebrow restraint, one radius system, colour lock) were applied.
- `ui-ux-pro-max` was loaded and its design-system generator run. It recommended a dark OLED style, which contradicts the light-first brief, and was rejected; its accessibility and interaction checklists were applied.
- **Not available:** the Figma connector is installed but unauthorised in this environment, so no design file could be read or produced, and no automated contrast/visual-regression tool exists in the project. Contrast was computed with a script and verified against computed styles instead.

### 14.7 Verification

- Screenshots before and after at 1440×900 and 390×844 for Overview, Controls, Control detail and Test runs, plus dark mode at 1440.
- No horizontal page overflow at 375, 390, 768 and 1440px in either theme (measured `scrollWidth`).
- `npm run typecheck`, `npm run lint` and `npm run build` (with `NEXT_PUBLIC_API_BASE_URL` set, as `next.config.mjs` requires) pass.

---

## 15. Revision 6.0: *Signal + Motion*

v5 fixed the colour, type and structure. v6 answers the next brief: **real photos and video, and a more interactive product**, designed in Figma first.

### 15.1 Figma

The file *AssureLens v6 Revamp* (drafts of the owner's Figma account) holds three boards: **Overview / Desktop 1440** (split hero with the video slot, the evidence gate, the media bento, with the real poster frames uploaded), **Controls / Desktop 1440** (search, instant filters, table), and **Motion & interaction spec**. The code implements those boards; DESIGN.md §6 is the spec. Figma's Weave AI media models were not available (the account is not linked to Weave), so no media was generated.

### 15.2 Media

Stock footage rather than generated: for a compliance product, real footage of the real city and real paper is more credible than synthetic imagery. Three Pexels clips, each chosen for a job: **Bengaluru's IT district at sunrise** (the estate under test), **network cables in a server room** (tests run against a live service; its cobalt light matches the brand), and **hands searching archive files** (evidence). Re-encoded to about 2 MB in total, self-hosted, credited on screen. Behaviour rules are in DESIGN.md §6.

### 15.3 Interactivity, and why each piece exists

- **The evidence gate explorer** (`GateExplorer`, `lib/wilson.ts`) turns the product's thesis into something the reader can move. It mirrors the engine's G1 (n >= 30), G2 (width <= 0.20) and G3 (coverage >= 10%) exactly (`backend/app/engine/thresholds.py`) and uses the 5% tolerable exception rate decided in §13.9. The Wilson function reproduces the brief's check value: 12 of 12 gives a lower bound of 0.7575. All three outcomes are reachable from the presets (verified: Too few items gives Insufficient, Clean gives Pass, Borderline gives Insufficient via threshold straddle, Clearly failing gives Fail).
- **Instant control search and filters** replace a server round trip per filter click (the production API answers in about 3.5s). The URL still reflects the filter.
- **Sliding tab indicator, page transition, staggered run results**: continuity and sequence, not decoration.

### 15.4 What did not change

The v5 palette, contrast ratios (§14.3), type scale, ruled structure and all product rules: no headline compliance percentage, verdict and severity always carry a word and a shape, every verdict gets identical motion, and reduced motion is honoured everywhere.

### 15.5 Dependencies added (approved by the owner)

`motion` 13.4.2 and `@phosphor-icons/react` 2.1.10.

