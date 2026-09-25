# AssureLens

**A DPDP + AI controls assurance workbench.** It turns the Digital Personal Data Protection Act 2023 and Rules 2025 into an executable control library, runs real tests against a live system, and **refuses to state a result its evidence cannot support**.

> **Status: Day 10 of 10.** The product is complete and locally verified: 25 controls, 13 executable across five live test suites, DOCX workpaper and executive summary export, role switch, document intake. **Not yet publicly deployed** — see Limitations. See [docs/IMPLEMENTATION_PLAN.md](docs/IMPLEMENTATION_PLAN.md) for the day-by-day build log.

> **Synthetic data only.** The estate is generated. Nothing here describes any real organisation. This is not legal advice.

---

## The problem

India's DPDP Rules 2025 were notified as **G.S.R. 846(E) on 13 November 2025**. Rule 1(4) puts the core operating obligations — Rules 3, 5 to 16, 22 and 23 — into force eighteen months later, on **13 May 2027**. Notice, consent, security safeguards, breach intimation, retention and erasure, data-principal rights, cross-border transfer, and Significant Data Fiduciary audit all arrive on one date.

An EY India survey of 150+ professionals found roughly **81% have not drafted DPDP-aligned policies**, **over 83% have not begun implementation**, and **77% are not equipped to adopt privacy technologies**. Only about **38% have categorised their personal data and identified their third-party processors**.

The gap is not awareness. It is the absence of a repeatable method to turn a statute into something you can test and evidence.

Every figure above is traced in [SOURCES.md](SOURCES.md).

## The point of view

Compliance dashboards are overwhelmingly green, because they score whether a policy *exists* rather than whether a control *works*, and because sampling five records and reporting "98% compliant" is easier than admitting five records prove nothing.

AssureLens returns `Pass`, `Fail`, or **`Insufficient Evidence`** — and the third is a designed, first-class verdict, not an error. Twelve successes out of twelve looks like a perfect score; its 95% Wilson interval is 0.74 to 1.00, which is not a conclusion. The tool says so.

This is enforced at the database level: a verdict of `INSUFFICIENT_EVIDENCE` cannot be written without a recorded gate reason.

## What I built

- A **control library**: 25 DPDP controls, each citing a verified clause and cross-mapped to ISO/IEC 27001:2022 and the NIST AI RMF. 13 are executable; the rest are documented with an evidence contract and correctly render `INSUFFICIENT_EVIDENCE` under gate `G4` — a control that has not been tested says so, rather than being silently omitted.
- A **test engine** with a plugin registry and an Evidence Sufficiency Gate: eight structured gate reasons (`G1`–`G8`), unit-tested against known statistical inputs, that block a `Pass`/`Fail` unless the sample size, confidence-interval width, population coverage, evidence freshness and representativeness all clear their threshold.
- **Five live test suites** — PII discovery and retention, consent-withdrawal propagation, adversarial access-control probes, third-party access posture, and AI model assurance (fairness and drift) — run against a real, deliberately-vulnerable target service over HTTP, on a recorded seed.
- **Findings, a risk heatmap, and a remediation roadmap**, auto-raised from failing controls only, never seeded, with severity as likelihood × impact and an ordering rule (impact ÷ effort) printed on screen rather than hidden in a sort.
- **Export**: a full audit-format DOCX workpaper and a one-page executive summary, both built from the same live computations the UI shows, so the exported numbers and the on-screen numbers can't drift apart.
- A **role switch** — consultant and client views differ in language, evidence detail and what can be edited, never in the numbers themselves.
- **Document intake**: upload or submit a URL for a policy document; text is extracted and classified against DPDP document types with a confidence score.

## What I found

A full run of all five suites, seed 42, against the seeded Meridian estate (measured 2026-09-25):

| | |
|---|---|
| Controls in the library | **25** (13 executable, 1 out of scope with a written reason) |
| Results from a full run | **14** |
| `Fail`, each with a real evidenced exception | **12** |
| `Insufficient Evidence`, correctly gated | **1** — the processor-erasure cascade; Meridian keeps no record of erasure instructions sent to processors, so there is genuinely nothing to conclude from |
| `Not Applicable`, correctly scoped out | **1** — the Third Schedule retention timetable, which binds only e-commerce, gaming and social-media entities above a user-count threshold; Meridian is none of these |
| Seeded defects detected | **10 / 10** (S1–S9, plus the access-log visibility gap) |
| False positives on a clean control | **0** |

Every one of those ten detections is a real exception a live procedure produced against the target service or the seeded estate — none are asserted from a mock. Four of them (ownership override, a `NaN` bypassing a spend-cap guard, an access refusal that produced no log entry, and a 425-day-stale credential that still authenticated) were found by a suite I built and wired up on the last day of this project: `access_probes` existed as a control-library declaration since early in the build, with no procedure behind it, so those four controls sat at `INSUFFICIENT_EVIDENCE` — the honest state for "not tested" — rather than a fabricated pass. Closing that gap, not documenting around it, is what the last day of a ship-honestly project should do.

## Architecture

```
Next.js (React, TS) ──HTTPS──> FastAPI ──> PostgreSQL
                                   │
                                   └──HTTP probes──> target_service
                                                     (deliberately vulnerable)
```

The **target service** is a separate process carrying intentional defects. The access-control suite probes it over HTTP exactly as an external tester would — so a defect that is not network-reachable is not found, same as reality. It holds no database credentials and is labelled as vulnerable at its root endpoint.

## Documentation

| | |
|---|---|
| [docs/PRD.md](docs/PRD.md) | Problem, users, scope, the Evidence Sufficiency Gate, limitations |
| [docs/TRD.md](docs/TRD.md) | Architecture, ADRs, test-suite algorithms, gate statistics |
| [docs/SCHEMA.md](docs/SCHEMA.md) | PostgreSQL DDL, ER diagram, seed plan |
| [docs/UX_BRIEF.md](docs/UX_BRIEF.md) | Design tokens, screens, the binding "not this" list |
| [docs/IMPLEMENTATION_PLAN.md](docs/IMPLEMENTATION_PLAN.md) | 10 days, acceptance criteria, pre-decided cut order |
| [SOURCES.md](SOURCES.md) | Every external figure and legal citation, with verbatim quotes |
| [DEPLOY.md](DEPLOY.md) | Render + Vercel setup, in the order the dependencies allow |

## Running locally

```bash
cp .env.example .env
docker compose up
```

Frontend `http://localhost:3000` · API `http://localhost:8000/docs` · Target service `http://localhost:8001`

Without Docker:

```bash
cd backend && python -m venv .venv && .venv/Scripts/python -m pip install -e ".[dev]"
cd frontend && npm install && npm run dev
```

## Checks

```bash
docker compose up -d postgres target_service   # the consent and access-probe suites reach the target over HTTP
cd backend && ruff check . && mypy app && pytest -q
cd frontend && npm run lint && npm run typecheck && npm run build
```

Without `target_service` running, the consent and access-probe controls correctly gate on
`G8_TARGET_UNREACHABLE` and their findings tests fail — that is the gate working,
not a flaky test.

`DATABASE_URL` is required with no default, and `NEXT_PUBLIC_API_BASE_URL` must
be set at **build** time — Next.js inlines `NEXT_PUBLIC_*` into the bundle
during `next build` and never reads it at runtime. Both refuse to start or
build without their value, deliberately: a silent fallback to localhost turns a
configuration mistake into what looks like a transient outage.

## Limitations

Stated here because a tool that asserts compliance conclusions has to say what it is standing on.

1. **Synthetic data.** The estate is generated. It demonstrates that the tests work; it says nothing about any real organisation.
2. **Not legal advice.** Clause mappings are the author's reading of the Rules.
3. **The Rules are not fully in force.** Interpretation will develop, and Board guidance may change it.
4. **A corrigendum (G.S.R. 892(E), 11 December 2025) has been reviewed** — it is purely typographical (Rule 1's own Gazette wording) and changes no rule numbering, timing, or text this product cites. See [SOURCES.md](SOURCES.md) §D1.
5. **Two source items remain genuinely open.** First Schedule Part B (Consent Manager obligations) has not been extracted in full — the dependent control gates on `G7_SOURCE_UNVERIFIED` rather than asserting a result. The statutory retention period for an Indian bank under PMLA/RBI KYC rules could not be confirmed against a primary source; secondary sources put it at five years, not the Act's own illustrative ten, and no control cites the disputed figure. Both tracked in [SOURCES.md](SOURCES.md) §D.
6. **No authentication.** This is a public demonstration. Do not upload real personal data.
7. **Not yet deployed to a public URL.** `render.yaml` and `DEPLOY.md` are written and ready, but no live instance exists at time of writing. The plan's own risk register names this failure mode directly — "a first deployment on the last day is the single most common way a portfolio project ends up local-only" — and it applies here: cold-load timing against the public URL, the <3-minute full-demo-path target, and a shareable link are all unverified until this is done. Deployment needs accounts on Neon, Cloudflare R2, Render and Vercel that only the project owner can create.
8. **The role switch has no server-side enforcement.** Consultant/client framing is a UI lens, not access control — by design, since this product has no login. A determined client-role user could still call the edit endpoint directly.

## What I'd do differently

- **Build the estate and the live target service before writing any control that depends on both.** The `access_probes` suite existed as a control-library declaration for most of the build with no procedure behind it — a documented, gated gap rather than a silent one, but still a day-10 fix that belonged on day 5 or 6, when the suites around it were built. The lesson generalises: a control's YAML and its procedure should ship in the same commit, or the gap should be a tracked task with a date, not a paragraph in a status report.
- **Decide the role switch's trust model on day 1, not day 9.** It works well as a UI lens, but "consultant edits, client reads" reads like an access boundary even though the product deliberately has none. Naming that explicitly earlier would have avoided writing client-side-only enforcement that a reviewer could reasonably mistake for real.
- **Keep a running, dated ledger of open source-verification items from day 2**, not just at the end. Two of seven were still open by day 10 (see Limitations #5) simply because closing them competed with feature work every day in between; a lighter-weight, continuously-updated version of the same table would have caught that drift sooner.

## Author

C. Prashanth — built as a portfolio project for a Digital Risk / Technology Risk consulting application.
