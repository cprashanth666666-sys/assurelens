# AssureLens — Implementation Plan

| | |
|---|---|
| Version | 1.0 |
| Date | 21 September 2026 |
| Duration | 10 working days, full-time |
| Status | Approved for build |
| Related | [PRD.md](PRD.md) · [TRD.md](TRD.md) · [SCHEMA.md](SCHEMA.md) · [UX_BRIEF.md](UX_BRIEF.md) · [../SOURCES.md](../SOURCES.md) |

---

## 1. Sequencing rationale

Three rules shape the order:

1. **Deploy on Day 1, not Day 10.** A first deployment on the last day is the single most common way a portfolio project ends up as a local-only demo. The skeleton ships to a public URL before any feature exists. [PRD R3]
2. **The gate before the suites.** Day 4 builds the engine and the Evidence Sufficiency Gate, unit-tested against published statistical values, *before* any suite consumes it. Every suite depends on it, and it is the feature the product argues for. If Days 5–7 overrun, **suites get cut; the gate does not.** [PRD §12]
3. **Something demoable every day.** Each day ends with a state that could be shown. This is insurance against a mid-project stall becoming a total loss.

### Critical path

```
D1 skeleton+deploy → D2 controls → D3 target+data → D4 ENGINE+GATE ←── critical
                                                       ↓
                             D5 suites 1-2 → D6 suites 3-4 → D7 suite 5
                                                       ↓
                             D8 findings+overview → D9 upload/export/roles → D10 ship
```

### Pre-decided cuts

If the plan slips, cut in this order — decided now, so the decision is not made under pressure at 11pm on Day 9:

| Order | Cut | Keeps intact |
|---|---|---|
| 1 | CSV upload (S1) | Fixed demo still complete |
| 2 | Effort×impact scatter — becomes an ordered table | Roadmap still delivered |
| 3 | Executive summary export | Workpaper is the important one |
| 4 | Suite 4 (third-party) | 4 suites still demonstrate the engine |
| 5 | Control history chart | Current verdict unaffected |
| **Never** | **The gate · seeded-defect tests · workpaper · public deploy** | These are the project |

---

## 2. Definition of done

A feature is done when **all** hold:

- Acceptance criteria for the day met
- Unit tests pass; new logic has tests
- No `TODO`, no commented-out code, no `console.log`
- Typechecks clean (mypy, tsc)
- Any number it displays traces to a computation or to `SOURCES.md`
- Any control it touches cites a verified clause, or is flagged `G7_SOURCE_UNVERIFIED`
- UI work checked against the [UX_BRIEF](UX_BRIEF.md) §1.1 negative list
- Committed with a message explaining *why*, not what

---

## 3. Day plan

---

### Day 1 — Skeleton and first deploy

**Goal:** an empty but real, publicly reachable three-service application.

| Build | |
|---|---|
| Repo | `git init`, structure per [TRD §12], `.gitignore`, `.env.example` |
| Compose | `docker-compose.yml` — postgres, backend, target_service, frontend |
| Backend | FastAPI app, `/api/health`, Pydantic v2 settings, CORS |
| DB | Alembic init, migration `0001` (enums, control library, engagements) [SCHEMA §6] |
| Frontend | Next.js 15 + TS + Tailwind, configured **to the tokens**, not defaults |
| Tokens | `styles/tokens.css` — full colour/type/space scale from [UX §2] verbatim |
| Shell | `Masthead`, `TabNav`, `DisclosureFooter` — six empty tab routes |
| CI | GitHub Actions: ruff, mypy, eslint, tsc, pytest |
| **Deploy** | Vercel (frontend), Render ×2 + managed Postgres. **All three live.** |

**Acceptance**
- `docker compose up` → all four containers healthy
- Public frontend URL renders the shell, tabs navigate
- Public backend `/api/health` returns 200 from the deployed frontend
- CI green on first PR

**Show this works:** open the public URL on a phone. Shell renders, footer disclosure visible, no horizontal scroll.

**Watch for:** Tailwind config must *replace* the default palette/radius/shadow scales, not extend them. Extending leaves the defaults reachable and the untouched-shadcn look creeps back in. [UX §9]

---

### Day 2 — Control library

**Goal:** 25 controls authored, cited, mapped, seeded, browsable. **This is the intellectual core.**

| Build | |
|---|---|
| `controls/dpdp.yaml` | 25 controls: ref, title, objective, domain, procedure, inference mode, executable flag, evidence contract, threshold overrides |
| `controls/iso27001_map.yaml` | ISO/IEC 27001:2022 Annex A cross-references |
| `controls/nist_ai_rmf_map.yaml` | NIST AI RMF function/category references |
| Clause table | 14 DPDP rules with **verbatim text** from [SOURCES A1.2–A1.3], `in_force_from` per Rule 1 commencement |
| Loader | `app.seed.controls` — YAML → DB, idempotent, validates every control has exactly one primary clause |
| API | `GET /api/controls`, `GET /api/controls/{ref}` |
| UI | Controls table + filter rail [UX §4.2]; control detail with `ClauseQuote` [UX §4.3] |

**Control distribution** (25 total, 12 executable):

| Domain | Controls | Executable |
|---|---|---|
| Notice & Consent (R3, R4) | 4 | 2 |
| Security Safeguards (R6) | 6 | 4 |
| Retention & Erasure (R8) | 3 | 3 |
| Principal Rights (R9, R14) | 3 | 0 |
| Breach Response (R7) | 2 | 0 |
| Third-Party & Transfer (R6, R15) | 3 | 2 |
| AI Governance (R13) | 3 | 1 |
| Governance & Accountability (R13) | 1 | 0 |

**Acceptance**
- 25 controls seeded; every one has exactly one primary clause and ≥1 secondary mapping
- Clause detail shows the verbatim statutory text, not a paraphrase
- Controls depending on [SOURCES] open items D1–D5 carry `source_status = UNVERIFIED`
- Filter by domain / framework / executable works

**Show this works:** open `DPDP-06-02`, read Rule 6(1)(b) verbatim beside the control objective.

**Watch for:** the temptation to write 40 controls. The cap is 25 and it is binding. [PRD R1]

---

### Day 3 — Target service and synthetic estate

**Goal:** a live, deliberately flawed system, and a deterministic dataset with defects planted in it.

| Build | |
|---|---|
| `target_service/app.py` | Meridian's customer API: auth, `/customers/{id}`, `/customers/{id}/spend-cap`, `/consent/withdraw`, `/marketing/segment/{id}`, `/profile`, `/vendor/verify` |
| `target_service/defects.py` | Planted defects, each with a comment naming the control it violates |
| `target_service/README.md` | **"This service is deliberately vulnerable. Synthetic data only. Do not deploy against anything real."** [TRD §9] |
| Migrations | `0004` synthetic estate (`est_*`), `0005` uploads/audit, `0006` indexes |
| Generator | `app.seed.generator` — `numpy.default_rng(seed)`, fixed `EPOCH` |
| `app.seed.meridian` | Full seed per [SCHEMA §5] |
| Identifiers | Format-valid, **checksum-valid**, provably non-real synthetic PAN/Aadhaar/mobile |

**Planted defects** (S1–S9 from [PRD §3.2]) — each reachable over HTTP or present in data, none asserted by a fixture.

**Acceptance**
- `python -m app.seed.meridian --seed 42` twice → byte-identical row hashes
- 24,000 principals, 11,400 past retention, 14 third parties, 12,000 predictions with a 22-member smallest group
- Target service live at a public URL; the ownership-override and NaN endpoints manually reproducible with `curl`
- Target `/` response states it is deliberately vulnerable

**Show this works:** `curl` the NaN spend-cap bypass and watch it return 200 when it should return 400.

**Watch for:** the synthetic Aadhaar generator must pass Verhoeff (so the detector is genuinely tested) while being drawn from a reserved non-issued range. A real-looking identifier in a public repo is unacceptable regardless of provenance.

---

### Day 4 — Engine and the Sufficiency Gate ★ critical path

**Goal:** the product's argument, implemented and proven correct. **No suite work today.**

| Build | |
|---|---|
| `engine/stats.py` | `wilson_interval`, PSI with Laplace smoothing, Verhoeff |
| `engine/thresholds.py` | All constants from [TRD §5.3], each with a docstring citing its basis |
| `engine/gate.py` | G1–G8, ordered structural-before-statistical, all reasons collected |
| `engine/evidence.py` | `EvidenceBroker`, four evidence kinds, SHA-256 hashing |
| `engine/runner.py` | Plugin registry, run orchestration, result persistence |
| Migration `0002` | Runs, results, evidence + the CHECK constraints [SCHEMA §3.4] |
| API | `POST /api/engagements/{id}/runs`, `GET /api/runs/{id}` |

**Tests — the day's real deliverable**

```
test_wilson_known_values     # the 5 published pairs in TRD §5.1,
                             # incl. 0/10 → (0, 0.2775) and 12/12 failing G2
test_wilson_n_zero_raises
test_gate_g1 .. test_gate_g8 # each rule in isolation
test_gate_collects_all_reasons
test_gate_structural_before_statistical
test_gate_census_skips_g1_g2_g3
test_psi_zero_bin_smoothing  # no divergence to infinity
test_attestation_alone_gates # G4 — the questionnaire-tool failure mode
```

**Acceptance**
- Wilson matches published values to 4 decimal places
- `verdict = INSUFFICIENT_EVIDENCE` is impossible without `gate_fired` (DB constraint proven by a failing insert)
- A run executes end to end with a stub procedure and persists a complete statistics row

**Show this works:** run the gate unit tests. The 12/12 case failing G2 *is* the demo.

**Watch for:** any temptation to let a suite decide its own sufficiency. `execute()` reports measurements; the gate decides. Keeping that boundary is what makes the feature trustworthy. [TRD §3.2]

---

### Day 5 — Suites 1 and 2

| Build | |
|---|---|
| `suites/pii_retention.py` | 1a detectors (PAN, Aadhaar+Verhoeff, mobile, email, account, free-text); 1b retention **both directions** — overdue erasure (R8(1)), missing 48h notice (R8(2)), log retention below 365d (R8(3)) |
| `suites/consent.py` | Sample → probe downstream → withdraw → re-probe → classify PROPAGATED/LAGGED/NOT_PROPAGATED; withdrawal effort parity (s.6(6)) |
| UI | Run console [UX §4.4] — suite selector, seed field, streaming results |

**Acceptance**
- **S5** detected (11,400 overdue erasures) · **S6** detected (90d < 365d) · **S9** detected (unmasked PAN in unencrypted transcripts)
- **S1** detected as `LAGGED` with a measured latency distribution, not a binary fail
- Clean fixture → zero findings
- Run console streams verdicts; the indeterminate rule is the only motion

**Show this works:** run suites 1–2 in the console; watch S1 land with a median propagation latency in hours.

---

### Day 6 — Suites 3 and 4

| Build | |
|---|---|
| `suites/access_probes.py` | P-01 … P-08 [TRD §4.3], census mode, request/response captured as evidence |
| `suites/third_party.py` | DPA presence, scope proportionality, staleness, rotation, offboarding, cross-border flag |
| UI | `EvidenceViewer` — mono request/response block in control detail |

**Acceptance**
- **S2** (ownership override) and **S3** (NaN bypass) detected, each with the HTTP exchange attached
- **S4** detected on staleness + missing DPA
- Target service stopped → all probe controls return `INSUFFICIENT_EVIDENCE` with `G8_TARGET_UNREACHABLE`, **never `PASS`**
- Census mode correctly skips G1/G2/G3

**Show this works:** stop the target service, re-run suite 3, and show every control gating on G8 rather than silently passing. This is the behaviour that separates an assurance tool from a health check.

---

### Day 7 — Suite 5, AI assurance

| Build | |
|---|---|
| `suites/ai_assurance.py` | 5a fairness (four-fifths, demographic parity, equal opportunity, per-group Wilson, `MIN_GROUP_N` gating); 5b PSI drift with smoothing; 5c validation incl. suspected target leakage |
| Persistence | `est_model_assessments` rows per metric/feature/group |
| UI | Control detail renders per-group rates with intervals; small groups render **gated, not disparate** |

**Acceptance**
- **S7** detected — ratio 0.71 < 0.80
- **S8** detected — two features PSI > 0.25
- The **22-member group gates** on `MIN_GROUP_N` rather than reporting a disparity
- Leakage reported as *suspected, requiring review* — never as a certainty
- Mapped to Rule 13(3) and NIST MEASURE 2.11 / 2.4 in the UI

**Show this works:** the 22-member group. A naive tool screams bias; this one says the group is too small to conclude from. That contrast is the strongest thirty seconds in the demo.

---

### Day 8 — Findings, overview, roadmap

| Build | |
|---|---|
| `FindingService` | Auto-raise from FAIL, ref allocation (`F-001`), severity banding from likelihood × impact, history rows |
| Migration `0003` | Findings, history, remediation |
| API | findings list/patch, roadmap |
| UI overview | Readiness by domain, risk heatmap, **evidence quality meter** [UX §4.1] |
| UI findings | Register with left-border severity + text label, expandable evidence |
| UI roadmap | Effort×impact scatter + ordered list with the ordering rule printed |

**Acceptance**
- A full run raises ≥9 findings, **all from executed tests, none seeded**
- Heatmap cell click filters the register
- Evidence quality meter reads correctly: graded vs thin vs no evidence
- **No headline compliance percentage exists anywhere** [PRD §7.3]
- Severity uses text labels, never colour alone

**Show this works:** the evidence quality meter. *"You have graded 60% of your estate. Here is the other 40%."*

---

### Day 9 — Upload, export, role switch

| Build | |
|---|---|
| `ingest/` | Upload, profiler (types, nulls, cardinality, **detector hits**), mapper with confidence, validation, 24h TTL purge |
| `reporting/workpaper.py` | DOCX per [PRD §7.1] — front matter, per-control sections, threshold register **including overrides**, limitations |
| `reporting/summary.py` | One-page executive summary from the same data |
| UI | Upload/mapping flow [UX §4.7]; report preview [UX §4.8]; **role switch** [UX §5] |
| Audit | `THRESHOLD_OVERRIDDEN`, `REPORT_EXPORTED` logged |

**Acceptance**
- A CSV with different column names maps and runs; unmapped required fields → `INSUFFICIENT_EVIDENCE` (G4), not an error
- Mapping screen warns *before* running: "suites that will return Insufficient Evidence: 2"
- DOCX opens in Word with correct styles; gate reasons printed in full; limitations in front matter
- Role switch changes framing and permissions, **never a number**
- Same run ID → byte-identical DOCX

**Show this works:** export the workpaper, open it in Word, scroll to a gated control and read the gate reason printed in the deliverable.

---

### Day 10 — Ship

| Build | |
|---|---|
| Verification | Close [SOURCES] D1–D6, or flag in-product with `G7`. **Re-read the 16 Dec 2025 corrigendum** and amend controls if needed |
| Numbers | `data:validate-data` over every figure in UI and README |
| `README.md` | Case memo — problem, approach, what I found, limits, what I'd do differently |
| Design review | [UX §10] checklist, then `design-taste-frontend` / `ui-ux-pro-max` review |
| Code review | `code-review` skill across the diff |
| Perf | Cold-load path measured against <30s / <90s / <3min [TRD §11] |
| E2E | Playwright over the full demo path |
| Demo | 3-minute script + recorded walkthrough |
| Resume | One bullet, **only with measured numbers** |

**Acceptance**
- Public URL cold-loads and completes the full demo in under 3 minutes
- Every displayed figure traces to a computation or `SOURCES.md`
- Every control cites a verified clause or is flagged `G7`
- Design review: zero ✗
- README states limitations without being asked

**The resume bullet** is written last, from measured output:

> *Built AssureLens, a DPDP + AI controls assurance workbench: 25 controls mapped to the DPDP Rules 2025, ISO 27001 and NIST AI RMF; 5 executable test suites detected 9/9 seeded defects across a live target service with zero false positives, while gating N controls as insufficient evidence rather than reporting unsupported conclusions.*

`N` is filled from the actual run. Not before.

---

## 4. Build risk register

| # | Risk | Trigger | Response |
|---|---|---|---|
| B1 | Day 4 overruns | Gate tests not green by end of Day 4 | Take Day 5 for it. Cut a suite, never the gate. |
| B2 | Control authoring overruns Day 2 | <20 controls by end of day | Ship 20; the cap protects the schedule in both directions |
| B3 | Render cold starts break the demo | Cold load >30s on Day 8 measurement | Cached overview snapshot (already designed [TRD §1.4]); if still slow, a paid dyno for demo week |
| B4 | DOCX styling fights back | Day 9 afternoon, not opening cleanly | Simplify to a flat table layout — content over polish |
| B5 | Corrigendum invalidates a control | Day 10 verification | Flag `G7`, note it in limitations. The product's own honesty rule applies to itself. |
| B6 | UI drifts generic | Any day | §1.1 negative list is checked at every UI commit, not just Day 10 |
| B7 | Seeded defects feel contrived | Demo rehearsal | Each defect maps to a documented real-world failure pattern; S1 and S3 are drawn from patterns seen in prior review work |
| B8 | Scope creep to GRC platform | Any day | [PRD §5.1] WON'T list is binding |

---

## 5. Daily checklist

At the end of each day:

- [ ] Day's acceptance criteria met
- [ ] Tests green, CI green
- [ ] Deployed — the public URL reflects today's work
- [ ] Committed with reasons in the messages
- [ ] Any new figure traced to a source or a computation
- [ ] Any UI work checked against [UX §1.1]
- [ ] Tomorrow's first task written down

The third box is the one that matters. A project that deploys daily cannot fail to deploy.
