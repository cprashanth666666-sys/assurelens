# Demo script — 3 minutes

Written from the actual, measured product state (2026-09-25), not a plan.
Each beat names the exact screen and the exact thing to point at.

## Setup (before the interviewer is watching)

Have the app open on **Overview**, role switch on **Consultant**, and no
run in progress. If a run has never happened, start one first so Findings
and Roadmap aren't empty when you get there — the pacing below assumes
they're already populated.

## 0:00–0:20 — The argument, in one sentence

**Screen: Overview, top of page.**

> "This is AssureLens — it turns the DPDP Rules into tests that actually
> run against a live system, and it's built around one refusal: it will
> not state a compliance result its evidence can't support."

Scroll to the evidence-gate slider. Move the sample-size slider down until
it gates.

> "Twelve out of twelve successes looks perfect. Its 95% confidence
> interval is 0.74 to 1.00 — that's not a conclusion, and the tool says
> so instead of rounding it up to a green checkmark."

## 0:20–1:00 — A real test, running live

**Screen: Test Runs.**

> "This isn't canned data — I can run it again right now."

Click **Run 5 suites**. While it runs (a few seconds):

> "Five suites, one of them probing a separate, deliberately vulnerable
> target service over real HTTP — the same way an external tester would."

When it completes, scroll to a `FAIL` row with a Wilson interval, then to
the one `INSUFFICIENT EVIDENCE` row (the processor-erasure cascade).

> "This one didn't fail — it gated. Meridian keeps no record of erasure
> instructions sent to processors, so there's nothing to conclude from.
> The tool says exactly why, and what would resolve it, right here — not
> a caveat buried in an appendix."

## 1:00–1:40 — Findings, not a scoreboard

**Screen: Findings register.**

> "Every one of these was raised automatically from a failing test —
> nothing here is seeded or typed in by hand."

Click a row open to show root cause / recommendation / history. Point at
the severity border + text label.

> "Severity is likelihood times impact, and it's never colour alone — this
> border is exactly the same signal as the text label next to it, so it
> survives a black-and-white printout."

**Screen: Roadmap.**

> "And this ordering isn't a gut call — it's impact over effort, printed
> on screen, so a client can check the math instead of just trusting the
> sequence."

## 1:40–2:15 — The role switch and the export

**Screen: anywhere, click the role switch to Client.**

> "Same data, different reader. A consultant sees the raw evidence and can
> edit; a client sees plain language and a read-only view — the numbers
> never change, only the framing does."

**Screen: Report.**

> "And this is the actual deliverable — a full audit-format Word document,
> or a one-page executive summary for the client, built from the exact
> same numbers you just saw on screen, not a separate report someone
> wrote by hand afterward."

Click the export button; show the downloaded file opening in Word if time
allows.

## 2:15–2:45 — Why this is the hard part, briefly

**Screen: back to Overview, the readiness-by-domain bars.**

> "There's deliberately no single compliance percentage anywhere in this
> product. A domain at 40% coverage and one at 95% can't be averaged into
> one honest number, so it isn't."

## 2:45–3:00 — Close

> "Ten of ten seeded defects caught, zero false positives, and every
> gated result explains itself. That's the whole pitch: not a dashboard
> that always looks good, a tool that says what it actually knows."

---

## If something breaks live

- **Run fails / target service unreachable:** the run console itself
  demonstrates the point — say so. "This is `G8_TARGET_UNREACHABLE` — the
  gate refusing to guess when the system it needs to probe isn't there.
  That's not a bug in the demo, that's the feature."
- **No time for the export click:** skip straight to the closing line;
  the workpaper/summary distinction can be described instead of shown.
- **Interviewer asks for the compliance percentage:** this is the one
  question the product is built to answer by refusing. "It doesn't have
  one, on purpose — that's page one of the README."
