# Design System: AssureLens, *Signal* (v6.0: Signal + Motion)

> Semantic design system for AssureLens, a DPDP + AI controls assurance workbench. This is the specification new screens are built from. The reasoning, the award research it rests on and the measured contrast for every pair are in [UX_BRIEF.md §14](UX_BRIEF.md). Tokens live in `frontend/styles/tokens.css`; component classes in `frontend/styles/globals.css`.

## 1. Visual Theme & Atmosphere

A bright, flat, high-contrast instrument. White work surfaces on a pale cool-grey page, near-black ink, and two brand colours used as **solid blocks**: cobalt for the instrument (masthead, the cover fact block, primary action, links, focus) and signal lime for the highlighter (the active tab, emphasis, scroll progress). Structure is a ruled grid with square corners. Nothing floats, nothing is translucent, and the background never moves.

The verdicts are the loudest thing on any screen: solid chips at full strength.

- **Density:** Daily App (5): dense tables with 12/16px cell padding and 14px text inside a generous page rhythm (48-64px between sections)
- **Variance:** Offset (6): 8/4 and 5/7 splits on the cover, 2:1 on control detail
- **Motion:** Fluid (6): spring feedback, shared-layout tab indicator, in-view video, an interactive evidence gate. Everything collapses under reduced motion

## 2. Color Palette & Roles

### Neutrals (light)
- **Page** `#F4F5F7`: the page field
- **Surface** `#FFFFFF`: tables, forms, sections, the cover
- **Inset** `#E9ECF1`: table header band, code blocks, aside headings, gate-explanation rows
- **Ink** `#0D1017`: primary text, structural rules (19.0:1 on surface)
- **Ink 2** `#363D4A`: body prose (10.9:1)
- **Ink 3** `#525A69`: labels and meta (6.9:1 surface, 5.9:1 inset)
- **Rule** `#D6DAE1`: hairlines between rows only
- **Control** `#7D8697`: input and toggle borders (3.7:1, UI)

### Brand
- **Cobalt** `#2436E6`: masthead band, cover fact block, primary button, focus ring. White on it 7.7:1. As link text 7.7:1
- **Cobalt Deep** `#1A28C2`: hover and pressed (white 9.9:1)
- **Cobalt Tint** `#E7EAFF`: row hover, suite tags
- **Lime** `#CDF23A`: active tab, `<mark>`, legal-basis tag, deadline block, scroll progress. **Ink text only** (14.8:1); never white on lime
- **Band** `#0D1017`: footer and run-result header (white text)

### Verdicts (solid chips, equal size and weight)
- **Pass** `#0B8048`, white text (5.0:1)
- **Fail** `#D0231A`, white text (5.3:1)
- **Insufficient evidence** `#0D1017`, white text (19.0:1). The ink chip: a conclusion, not an absence of one. Never red, amber or yellow
- **Not applicable**: dashed `Control` outline, `#525A69` text (6.9:1)
- Inline verdict text: pass `#0A7A44` (5.4:1), fail `#C41F17` (5.9:1)

### Severity (solid chips, 1px ink border, text label always)
- **Critical** `#D0231A` white text (5.3:1) · **High** `#FF7A1F` ink text (7.3:1) · **Medium** `#FFC93C` ink text (12.4:1) · **Low** `#8CC2FF` ink text (10.2:1)

### Dark mode
Page `#0B0D12`, surface `#151821`, inset `#1E222D`, ink `#F2F4F8` (16.1:1), ink 2 `#C3C8D3` (10.6:1), ink 3 `#9BA3B2` (7.0:1), link `#9AA5FF` (7.8:1), cobalt block `#3342F0` (white 6.6:1). Verdict and critical fills lighten (`#33C47A`, `#FF6B5F`, ink chip becomes `#F2F4F8`) and take **ink** text (8.6 / 7.0 / 17.7:1). Lime is unchanged. Dark mode follows `prefers-color-scheme` and an explicit `data-theme` wins in both directions.

## 3. Typography Rules

- **Sans:** **Geist** for everything read. Display and page titles at weight 500 with tight tracking; headings 600; body 400
- **Mono:** **JetBrains Mono** for every identifier and measurement: control refs, run ids, seeds, hashes, counts, intervals, framework refs. All numerals `tabular-nums`
- **No serif.** Quoted statute is marked by a 4px cobalt rule and 20px size
- **Scale** (token: size, use):
  - `xs` 12px: gate codes, photo credits only
  - `meta` 13px: labels, table headers, captions
  - `sm` 14px: table body, controls
  - `base` 16px: body prose
  - `lg` 20px: section titles (h3)
  - `xl` 28px: block headlines (h2)
  - `2xl` 36-56px (fluid): page titles, tracking −0.035em
  - `num` 40-64px (fluid): counts and the day count, in mono. Never a percentage or a score
  - `display` 44-92px (fluid): the cover statement only, tracking −0.045em, line-height 0.98
- **Nothing smaller than 12px.** No uppercase tracked micro-labels: labels are `.label`, 13px sentence case, weight 500
- Measure: prose max 68ch; `text-wrap: balance` on headings, `pretty` on paragraphs

## 4. Component Stylings

- **Masthead:** solid cobalt band, sticky, fixed height. Aperture mark (lime and white blades), "AssureLens / engagement" line, client name at 20px. Deadline in a lime block (hidden below 640px). Role switch as a white field
- **Tab rail:** white bar with a 2px ink foot; 48px ruled cells; active cell = lime fill, ink text, 3px ink inner foot. Scrolls with edge fades below 768px
- **Page header (`PageHeader`):** optional kicker (breadcrumb), 36-56px title on the page field, 16-20px lede, optional children (count strip, fact strip)
- **Ruled grid (`.ruled`):** cells on 1px ink gaps inside a 1px ink frame. Used for the cover, count strips and fact strips
- **Sheet (`.sheet`):** white surface, 1px ink frame. Tables, the run console, asides
- **Section (`.section-rule`):** 2px ink top rule, 16px gap, then an h3
- **Buttons (`.btn-primary`):** cobalt fill, white text, 44px tall, square. Hover: cobalt deep. Press: 1px down. Label states the action and its object ("Run 5 suites"). No spinner
- **Toggles (`.toggle`):** 44px square-cornered blocks with a `Control` border; selected is a solid ink fill with surface text. Used for filters and suite selection. Focus ring on the block, not the hidden input
- **Fields (`.field`):** 44px, `Control` border, label above; focus = cobalt border + 3px cobalt ring
- **Chips (`.chip`):** 24px, 13px semibold; verdicts and severities as above; suite tags on cobalt tint in mono
- **Tables (`.data-table`):** 14px body, 12/16px cell padding, inset header band with a 2px ink rule, 1px `Rule` hairlines, no zebra. Rows answer hover **and** keyboard focus with cobalt tint and a 3px cobalt bar at the left edge; rows never move. Minimum widths (60rem controls, 46rem results) so they scroll sideways on phones rather than crushing columns
- **Gate explanation:** inset row, 4px ink left rule, "Why." then "Resolve." in bold lead-ins
- **Photographs:** full colour, square, box reserved by aspect ratio; caption and credit below on the surface
- **Placeholder:** 2px dashed frame, lime "Builds on Day N" tag
- **Focus:** 3px cobalt outline, 2px offset, everywhere

## 5. Layout Principles

- Max content width 1440px; side gutter 16px, 32px from 768px
- Page rhythm: 48px between sections (`gap-7`), 64px on the overview
- Cover splits at 1024px into 8/4 (statement / cobalt fact block) and 5/7 (photograph / principles)
- Control detail: 2:1 from 1024px; main column in ruled sections, side column in sheets
- Single column below 768px, no horizontal page scroll (measured at 375, 390, 768, 1440 in both themes). Only tables, filter rails and code blocks scroll sideways, inside their own container
- Sticky masthead and tab rail; heights measured by `ResizeObserver`, never hardcoded
- Full-height regions use `dvh`

## 6. Motion & Interaction

Library: **Motion** (`motion/react`), wrapped once in `MotionConfig reducedMotion="user"` (`components/MotionProvider.tsx`). Icons: **Phosphor** (`@phosphor-icons/react`; `/dist/ssr` in server components). The Figma file *AssureLens v6 Revamp* holds the Overview and Controls boards and the motion spec this section implements.

| Interaction | Behaviour | What it reports |
|---|---|---|
| Tab indicator | One lime block (`layoutId="tab-active"`) slides between tabs, spring 520/42 | Where you are |
| Page change | `app/template.tsx`: 8px rise + fade, 280ms | Continuity |
| Hero video | Muted 10s loop, plays only while 40% in view, visible Pause/Play (WCAG 2.2.2), poster only under reduced motion or Save-Data | Context: the estate under test |
| Media bento | Clip plays on hover or focus (in view on touch), pauses on leave; 2.5% zoom | Attention |
| Evidence gate | Sliders and scenario presets move the 95% Wilson interval with a spring (transform only); verdict cross-fades identically for every verdict; gate reasons enter and leave | Cause and effect |
| Control search | Filters as you type, rows fade (opacity only, never a transform on `<tr>`), live count, `/` focuses search, empty state, URL kept in sync | Feedback |
| Run results | Rows arrive 40ms apart (capped at 12); tally chips spring in, same spring for every verdict | Sequence |
| Buttons | 1px press; arrow nudges 3px on hover | Affordance |
| Scroll progress | 3px lime rule, CSS `animation-timeline: scroll()` | Position |

- **Reduced motion:** reveals immediate, videos show their poster, springs become instant, scroll rule hidden, hover zooms off
- **Timing:** 120ms fast, 180ms base, 320ms slow; springs as listed

## 6a. Media

- Three self-hosted clips in `frontend/public/media`, each 1280px H.264, 10s, no audio, `+faststart` (estate 1.08 MB, evidence 0.72 MB, network 0.18 MB), with a JPEG poster. Registry and credits in `frontend/lib/media.ts`
- Every clip and photograph is credited on screen (Pexels / Unsplash photographer, linked)
- Text never sits on footage: overlays are solid blocks (cobalt fact block, white Pause chip at 19:1)

## 7. Anti-Patterns (Banned)

- No moving, gradient or animated backgrounds; no translucent or blurred surfaces (video is content in a frame, never a page background)
- No rounded cards, no drop shadows on the page (overlays only), no 3D tilt
- No text below 12px; no 11px uppercase tracked labels
- No muted or desaturated status colour; no colour-only encoding
- No white text on lime
- No headline compliance percentage, KPI score tile or animated counter; large numerals only for counts and dates
- No colour, size, glow or motion given to one verdict and not the others
- No emoji; no em-dashes in UI copy
- No serif; no Inter
- No `window` scroll listeners; scroll effects use CSS scroll-driven animation or IntersectionObserver
- No `h-screen`; use `dvh`
- No spacing utility off the token scale (it emits nothing; see UX_BRIEF §11.6)
