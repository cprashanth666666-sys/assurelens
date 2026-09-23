# Design System: AssureLens — *Tidal*

> Semantic design system for AssureLens, a DPDP + AI controls assurance workbench. Source of truth for generating new screens. The rationale behind every decision is in [UX_BRIEF.md §12](UX_BRIEF.md); this file is the specification.

## 1. Visual Theme & Atmosphere

A bright, living ground under calm, solid work surfaces. A sunset-to-sea gradient drifts and rolls continuously behind the page, with three layers of waves moving at three speeds along the bottom edge. Everything the reader actually works with sits on raised, near-opaque tiles that lift and tilt toward the cursor or finger, then settle with a small spring.

The atmosphere is **a clear, warm afternoon on the water, seen from a well-lit office**. The colour and movement live in the ground; the tiles are still, legible and serious. The motion is ambient, the content is steady.

- **Density:** Daily App Balanced (5) — dense audit tables inside generous tiles
- **Variance:** Offset Asymmetric (6) — split cover sheet, 2:1 detail layout
- **Motion:** Fluid CSS (6) — perpetual motion in the ground only; interaction motion on tiles

## 2. Color Palette & Roles

### Ground (moving, decorative, never carries text)
- **Saffron** (`#FFC27A`) — warm corner of the ground gradient, top left
- **Coral** (`#FF8F7A`) — warm mid-tone of the gradient
- **Turquoise** (`#52D1BE`) — cool mid-tone of the gradient
- **Deep Sea** (`#2A9DB8`) — cool corner, bottom right
- **Sun Bloom** (`rgba(255,214,102,0.60)`) · **Coral Bloom** (`rgba(255,111,97,0.46)`) · **Lagoon Bloom** (`rgba(38,196,178,0.52)`) — drifting colour fields over the gradient
- **Foam / Mid / Deep Wave** (`rgba(255,255,255,0.30)` / `rgba(27,138,158,0.30)` / `rgba(12,84,104,0.36)`) — the three wave layers, front to back

### Surfaces
- **Tile** (`rgba(253,251,246,0.93)`) — every surface that carries text. Never pure white
- **Tile Edge** (`rgba(255,255,255,0.72)`) — 1px highlight border on tiles
- **Scrim** (`rgba(253,251,246,0.94)`) — tiles on phones (no frosting), sticky masthead when condensed
- **Inset Oat** (`#EFE9DB`) — table zebra, table header band, code blocks

### Ink
- **Primary Ink** (`#241F17`) — body text. Never pure black
- **Heading Ink** (`#393328`) — headings
- **Secondary Ink** (`#6A6353`) — metadata, captions (5.4:1 on tile)

### Accent and second voice
- **Teal Ink** (`#1C6B84`, pressed `#15566C`) — the single interactive accent: primary button, links, focus rings, active tab
- **Terracotta** (`#BB6640`) — the second voice: hover rules, active filter underline. **Never status**

### Verdicts (the only colours that carry meaning)
- **Pass** (`#3E6B4C`) · **Fail** (`#8F322A`) · **Insufficient Evidence** (`#524B3E`, neutral ink by design) · **Not Applicable** (`#8E8571`)

### Dark mode ground
Ember `#3A2019` → Oxblood `#552723` → Deep Lagoon `#0F4A4A` → Midnight Sea `#0A2F43`, with blooms at ~16% and waves dimmed. Tiles become `rgba(26,23,18,0.90)`.

## 3. Typography Rules

- **Display & UI:** **Geist** — semibold headings tracked tight (−0.014em; −0.03em on the one display line). Hierarchy by weight and colour, not size. The largest size is fluid `clamp(1.625rem, 4.4vw + 0.75rem, 2.375rem)` and carries a sentence, never a number
- **Body:** Geist at 14px, line-height 1.6, max 75ch
- **Mono:** **JetBrains Mono** — control refs, run ids, seeds, hashes, evidence. All numerals are `tabular-nums`, everywhere
- **Serif:** **Source Serif 4, only for verbatim statutory quotation.** Nowhere else
- **Banned:** Inter, generic system fonts, and Times New Roman, Georgia, Garamond and Palatino

## 4. Component Stylings

- **Tiles:** 14px radius, 1px light edge, layered shadow tinted toward the sea hue (`0 12px 30px -10px rgba(16,72,88,0.34)`). On hover or press they rise 6px, scale to 1.012, tilt up to 6° toward the pointer (less on wide tiles) and catch a soft light at the pointer position, then settle with a small spring overshoot. Frosted blur above 768px only
- **Buttons:** Teal fill, 3px radius, 40px minimum height. Hover raises 1px with a tile shadow; press scales to 0.985. No outer glow
- **Chips (multi-select):** the whole 36px chip is the hit target, with a drawn checkbox. Selected is a teal border with a pale teal fill; the focus ring is drawn on the chip, not the hidden input
- **Fields:** Label above, 36px tall, teal border and 3px pale teal ring on focus
- **Tables:** Inside a tile, never tilted. Rows answer hover *and* keyboard focus with a terracotta rule wiping in at the left edge and a pale teal tint. Rows never move
- **Photographs:** On a tile, 10px radius, lightly desaturated under a turquoise-to-coral wash, full colour on hover. Always credited
- **Loading:** a 2px teal-to-terracotta indeterminate rule. No full-panel spinner and no skeleton pulse
- **Empty / unknown states:** Plain sentences that say which state it is. "Never run" and "API unreachable" are different messages

## 5. Layout Principles

- **Text never sits on the moving ground.** Every line of copy is on a tile, including page headers, filter rails and captions
- Max content width 1440px, side gutter 16px (20px from 768px)
- Cover sheet splits at 1024px, not 768px; control detail uses a 2:1 split from 1024px
- Single column below 768px, with no horizontal page scroll. Only tables and code blocks scroll sideways, inside their own tile
- Sticky masthead and tab rail, heights **measured** at runtime, never hardcoded
- Full-height regions use `dvh`, never `vh`

## 6. Motion & Interaction

- **Ambient (perpetual):** waves roll at 34s, 21s (reversed) and 13s; blooms drift at 26s, 33s and 39s. CSS `transform` only, compositor thread, no JavaScript
- **Interactive:** tile rise and tilt driven by pointer position, batched once per animation frame; spring settle `cubic-bezier(0.34, 1.4, 0.64, 1)`
- **Touch parity:** press lifts and tilts, release or scroll settles. Never blocks scroll
- **Entrance:** tiles surface on scroll, rising 24px from a scale of 0.98, with a 40ms stagger per item
- **Micro:** underlines grow from the left, tab rules wipe in, the masthead aperture rotates 45° on condense
- **Reduced motion:** the ground freezes in colour, tiles never rotate, entrances are immediate, and the indeterminate rule becomes static
- **Timing rhythm:** 120ms press, 200ms hover, 340ms entrance, 560ms spring settle

## 7. Anti-Patterns (Banned)

- No emoji anywhere, including as status icons
- No Inter font, and no generic serif
- No pure black (`#000000`) and no pure-white surfaces
- No purple or electric-blue gradients, and no neon outer glows
- No custom mouse cursors
- No text directly on the moving ground
- No headline compliance percentage, KPI numeral tile or animated counter
- No colour, glow or motion given to one verdict and not the others. `INSUFFICIENT_EVIDENCE` is a peer of `PASS`
- No tilt on tables, forms or scrollable content
- No 3-equal-card marketing rows used as decoration (the three principle tiles each state an engine behaviour)
- No filler UI ("Scroll to explore", bouncing chevrons), and no AI copy clichés ("Elevate", "Seamless", "Unleash")
- No uncredited or unchecked images
- No `h-screen`; use `dvh`
