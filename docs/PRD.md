# AssureLens — Product Requirements Document

**DPDP + AI Controls Assurance Workbench**

| | |
|---|---|
| Version | 1.0 |
| Date | 21 September 2026 |
| Author | C. Prashanth |
| Status | Approved for build |
| Related | [TRD.md](TRD.md) · [UX_BRIEF.md](UX_BRIEF.md) · [SCHEMA.md](SCHEMA.md) · [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) · [../SOURCES.md](../SOURCES.md) |

---

## 1. Why this exists

### 1.1 The regulatory clock is real and short

The Digital Personal Data Protection Rules, 2025 were notified as G.S.R. 846(E) on **13 November 2025**. Rule 1(4) puts the core operating obligations — Rules 3, 5 to 16, 22 and 23 — into force **eighteen months after publication**, which is **13 May 2027**. Consent Manager registration (Rule 4) lands a year in, on 13 November 2026. [SOURCES A1.1]

Everything an organisation must actually *do* — notice, consent, security safeguards, breach intimation, retention and erasure, data-principal rights, cross-border transfer, Significant Data Fiduciary audit — arrives in a single tranche on one date. There is no staggered ramp for the hard parts.

### 1.2 The market is not ready, and knows it

EY India surveyed 150+ professionals on DPDP readiness. The results are not close: [SOURCES B1]

| | |
|---|---|
| Have **not** drafted DPDP-aligned policies or governance frameworks | ~81% |
| Have **not** begun comprehensive implementation | >83% |
| **Not** very familiar with the Act and Rules | ~70% |
| **Not** equipped to adopt privacy technologies (consent management, data discovery, rights fulfilment) | ~77% |
| Cite limited access to subject-matter expertise | 76.4% |
| Have initiated a gap assessment | ~48% |
| Have categorised personal data and identified third-party processors | ~38% |

Read those last two rows against the first three. Roughly half have *started looking*; barely a third know where their personal data sits or who processes it. The gap is not awareness — it is the absence of a repeatable method to turn a statute into something you can test and evidence.

### 1.3 The gap is sharpest exactly where the work is delivered

The EY India GCC Pulse Survey 2025 (Bengaluru, 23 November 2025) names Bengaluru, Hyderabad and Chennai among India's GCC hubs, and reports: [SOURCES B2]

- **83%** of GCCs investing in GenAI, **58%** in agentic AI
- **7%** have a fully embedded cybersecurity Centre of Excellence
- **60%** monitor third-party access to data (up from 44% in 2024)
- **42%** report compliance complexity and data-privacy concerns (up from 32%)

An organisation deploying agentic AI over Indian personal data, without an embedded security CoE, eighteen months from a hard compliance date, with incomplete visibility of its own processors — that is the modal India GCC in 2026. EY's own Intelligent GCC suite lists "embed governance with responsible AI" as one of four capabilities, which is the firm naming the same gap.

### 1.4 And there is a specific seam in how the work gets staffed

An EY Chennai *Risk Consulting — Digital Risk — Manager (Cloud)* posting asks for a *"strong audit mindset with the ability to design, execute, and evidence control testing."* The same posting mentions no AI, no DPDP, and no analytics tooling. EY Hyderabad runs Supply Chain and Third-Party Risk roles; AI Governance roles sit elsewhere in the India network. [SOURCES B3]

So: evidenced control testing lives in one place, DPDP in another, AI assurance in a third. **AssureLens sits in that seam** — one workbench where a DPDP obligation becomes a testable control, the test actually runs, and the result is only asserted when the evidence supports it.

> **What this is not.** This is not a claim that EY lacks these capabilities — EY publishes extensively on both DPDP and Responsible AI. The gap is in the *client population*, and in the tooling that connects three currently-separate practice areas. [SOURCES C]

### 1.5 The honesty problem nobody else solves

Compliance dashboards are overwhelmingly green. They are green because they score *policy existence*, not *control effectiveness*, and because sampling five records and reporting "98% compliant" is easier than admitting five records prove nothing.

This matters commercially. An assurance report that overstates confidence is worse than no report: the client stops looking, and the regulator does not. Rule 13(2) requires a Significant Data Fiduciary to furnish the Board *"a report containing significant observations"* from its DPIA and audit. A report built on unsupported numbers is a liability with a cover page.

**AssureLens refuses to state a result its evidence cannot support.** Every control returns `Pass`, `Fail`, or **`Insufficient Evidence`**, and the third outcome is a first-class, designed, deliberate state — not an error, not a gap to be filled with an estimate. This is the product's point of view, and section 6 specifies it precisely.

---

## 2. What AssureLens is

> A two-sided assurance workbench that turns the DPDP Act and Rules 2025 — mapped to ISO/IEC 27001 and the NIST AI RMF — into an executable control library, runs real tests against a live system and real data, gates every result on evidence sufficiency, and produces an audit-grade workpaper and a prioritised remediation roadmap.

**One sentence for the interview:** *"I turned a statute into testable controls, built the engine that tests them, and made it refuse to give you a number it can't defend."*

### 2.1 Product principles

| # | Principle | Consequence in the build |
|---|---|---|
| P1 | **Evidence before assertion** | No verdict without a declared evidence contract satisfied. `Insufficient Evidence` is a designed state, not a failure mode. |
| P2 | **Every control traces to a clause** | Each control cites a rule/clause reference. If it maps to nothing, it is a good practice, not a control, and is labelled that way. |
| P3 | **Tests execute, they do not opine** | Controls in scope for v1 run against real synthetic data or a live target service. A questionnaire answer is evidence *about* a control, never the test *of* one. |
| P4 | **The tool is itself auditable** | Append-only audit log, deterministic seeding, reproducible runs. An assurance tool you cannot audit is a contradiction. |
| P5 | **Limits are shipped, not hidden** | Sample sizes, confidence intervals, coverage, exclusions and unverified sources are rendered in the UI and printed in the workpaper. |
| P6 | **Two readers, one truth** | The consultant and the client see the same results. The role switch changes emphasis and permissions, never the numbers. |

### 2.2 Explicit non-goals

| Not doing | Why |
|---|---|
| A generic GRC platform | Depth on one regulation beats breadth across ten. |
| Legal advice | The product cites clauses and tests controls. It does not opine on interpretation, and says so on every report. |
| Real authentication / multi-tenancy | v1 is a public demo. Auth is *designed* in the TRD, not built. |
| Live integrations (ServiceNow, Jira, AWS Config) | Designed as an extension point; not built. |
| Real client data of any kind | Synthetic only. Thrive Together and MerakiPeople data is confidential and excluded by design. |
| A scored "compliance percentage" headline | A single percentage is exactly the false confidence P1 exists to prevent. Readiness is reported per domain, with coverage. |

---

## 3. The demo scenario

A fictional client, built so the demo tells a story in three minutes.

### 3.1 Meridian Financial Services India GCC

| | |
|---|---|
| Entity | Captive Global Capability Centre, Bengaluru (Whitefield) |
| Parent | Meridian Financial Group, headquartered in the US, with an EU banking subsidiary |
| Headcount | ~1,800 |
| Role | Operations, analytics and engineering for the group's retail banking business, including the India retail book |
| Personal data | ~2.4M Indian retail customers — KYC identifiers, contact data, transaction history, support call transcripts |
| AI in production | `MFS-CPS-v3`, a credit pre-screening model that scores loan enquiries before a human underwriter sees them |
| Third parties | 14 processors — cloud hosting, a KYC verification vendor, a marketing automation platform, a call-transcription vendor, an offshore BPO |
| Status | Expects to be notified a **Significant Data Fiduciary**, so Rule 13 (annual DPIA + audit, algorithmic due diligence) applies |
| Engagement | EY Digital Risk has been asked for a DPDP and AI-controls readiness assessment ahead of the 13 May 2027 deadline |

Why BFSI: highest DPDP stakes, richest control set, the AI model is materially consequential, and the cross-border flow to a US/EU parent makes Rule 15 live rather than theoretical.

### 3.2 What is wrong at Meridian (the seeded narrative)

The synthetic estate is seeded with defects that a real assessment would find. Each maps to a control, and each is *findable by an executing test* — not asserted by the fixture.

| # | Defect | Surfaces via | Clause |
|---|---|---|---|
| S1 | Consent withdrawal updates the consent store but the marketing segment refreshes nightly — a withdrawn principal is still marketable for up to 22 hours | Consent propagation suite | DPDP Act s.6(6), Rule 3 |
| S2 | The KYC vendor's service account can read customer records beyond the accounts it verifies (ownership check missing on one endpoint) | Access-control probes | Rule 6(1)(b) |
| S3 | A spend/limit cap can be bypassed by submitting `NaN` — the comparison silently returns false | Access-control probes | Rule 6(1)(b) |
| S4 | Call-transcription vendor token last used 14 months ago, still active, no DPA reference on file | Third-party access monitor | Rule 6(1)(b), (c) |
| S5 | 11,400 dormant customer records past the Third Schedule period, never erased; no 48-hour pre-erasure notice mechanism exists | PII + retention suite | Rule 8(1), 8(2) |
| S6 | Processing logs are purged at 90 days — below the Rule 8(3) one-year minimum | PII + retention suite | Rule 8(3) |
| S7 | `MFS-CPS-v3` selection rate for one applicant group is 0.71 of the highest group — below the four-fifths threshold | AI assurance suite | Rule 13(3) |
| S8 | Two input features have drifted materially since training (PSI > 0.25); no drift monitoring exists | AI assurance suite | Rule 13(3) |
| S9 | Support call transcripts contain unmasked PAN-format identifiers in a store with no encryption at rest | PII discovery | Rule 6(1)(a) |
| S10 | Breach runbook exists but has never been exercised; no evidence of the Rule 7(1) content set being producible | Evidence review — **fires the sufficiency gate** | Rule 7(1) |
| S11 | Grievance redressal published, but no measurement of whether responses land inside ninety days | Evidence review — **fires the sufficiency gate** | Rule 14(3) |
| S12 | Cross-border transfer to the US parent documented, but the control's testability depends on an unissued Rule 15 order | **Source-unverified gate** | Rule 15 |

S10, S11 and S12 exist specifically so the demo shows the product **declining to grade**. A tool that finds nine problems and confidently green-lights everything else has not demonstrated judgement. One that says *"three of these I cannot responsibly grade, and here is exactly what evidence would let me"* has.

### 3.3 The three-minute demo path

1. Open the engagement overview. Readiness by domain, risk heatmap, evidence-quality meter. **No single headline percentage.**
2. Run the test suites live. Watch verdicts land — including two that land on `Insufficient Evidence`.
3. Open finding F-003 (the NaN cap bypass). Show the probe request and response as attached evidence.
4. Open a gated control. Show *why* the gate fired and precisely what would clear it.
5. Toggle role: consultant → client CISO. Same numbers, different framing and permissions.
6. Export the workpaper. Open the DOCX.

---

## 4. Users

### 4.1 Aarti Menon — Senior, Digital Risk, EY (primary)

Four years in technology risk, currently on a DPDP readiness engagement for a Bengaluru GCC. Bills by the hour and is judged on defensible workpapers.

**Jobs to be done**
- Scope an assessment in hours, not a week of building a spreadsheet from the bare Act.
- Run repeatable, evidenced tests rather than re-deriving procedures per client.
- Produce a workpaper a reviewing manager will sign, and a finding a client cannot argue away.
- Know, before the client does, which conclusions are thin.

**What she fears:** signing a conclusion the evidence does not support; a client disputing a finding she cannot reproduce.

**Her one-line test of this product:** *"Can I hand this workpaper to a manager without rewriting it?"*

### 4.2 Rohan Iyer — CISO and acting DPO, Meridian India GCC (primary)

Security lead who inherited the DPO role. Reports to a group CISO in New York and an India MD. Has a budget conversation in six weeks and no defensible number to bring to it.

**Jobs to be done**
- Understand where he actually stands, not where a vendor's green dashboard says he stands.
- Get a prioritised list he can resource — impact against effort.
- Track remediation and re-test, so progress is evidence, not assertion.
- Have something credible to put in front of the group board.

**What he fears:** being told he is 94% compliant and then being wrong on 13 May 2027.

**His one-line test:** *"What do I fix first, and what will it cost me?"*

### 4.3 Secondary readers

| Reader | Uses | Needs |
|---|---|---|
| EY engagement Manager/Partner | Reviews the workpaper | Traceability, sign-off trail, stated limitations |
| Data Protection Board (hypothetical) | Rule 13(2) observations report | Clause traceability, methodology, honest limits |
| Meridian group board | Executive summary | One page, no jargon, ranked actions, stated uncertainty |

### 4.4 The role switch

A persistent control in the header, with two states. **It changes framing and permission, never a number.**

| | **Consultant view** (Aarti) | **Client view** (Rohan) |
|---|---|---|
| Landing | Test run console — work to do | Engagement overview — where do I stand |
| Language | "Control ineffective", "exception noted" | "Not working", "needs fixing" |
| Findings | Full register, drafting and editing | Read-only; internal reviewer notes hidden |
| Evidence | Raw artifacts — probe payloads, queries, samples | Summarised; raw artifact on request |
| Sufficiency gate | Shows the failed rule and threshold | Shows what evidence is needed and who supplies it |
| Roadmap | Effort estimates, engagement sequencing | Owners, dates, budget framing |
| Export | Full workpaper (DOCX) | Executive summary (1 page) |
| Can run tests | Yes | Yes, but cannot edit control definitions |

The switch is honest about itself: a line under the control reads *"Viewing as client. Same results, presented for the data fiduciary."*

---

## 5. Scope

### 5.1 MoSCoW

**MUST — the demo does not exist without these**

| ID | Feature | Acceptance |
|---|---|---|
| M1 | Control library, ~25 DPDP controls, each citing a rule and mapped to ISO 27001 and NIST AI RMF | Every control has objective, procedure, evidence contract, clause ref, ≥1 framework mapping |
| M2 | Seeded-flaw target service | Runs standalone; all planted defects live and reachable over HTTP |
| M3 | Deterministic synthetic data generator | Same seed → byte-identical dataset |
| M4 | Test engine with plugin registration and evidence contracts | A new suite can be added without touching engine core |
| M5 | **Evidence Sufficiency Gate** | Section 6. Unit-tested against known inputs |
| M6 | 5 executable test suites | Section 5.2 |
| M7 | Findings register with severity = likelihood × impact | Auto-raised from failing controls, manually editable |
| M8 | Engagement overview: readiness by domain, risk heatmap, evidence-quality meter | No single headline compliance % anywhere |
| M9 | DOCX workpaper export | Opens cleanly in Word; audit format per 7.1 |
| M10 | Role switch | Section 4.4 |
| M11 | Public deployment, no login, pre-seeded | Cold load → demo complete in under 3 minutes |

**SHOULD**

| ID | Feature |
|---|---|
| S1 | CSV upload with column mapping — makes it a reusable accelerator, not a fixed demo |
| S2 | Remediation roadmap, 90-day, effort × impact |
| S3 | External reference band overlay (EY survey figures, clearly labelled as external) |
| S4 | Control detail history — result over time |
| S5 | Executive summary export (1 page) |

**COULD** — multi-engagement workspace; control-library editor in-app; re-test a single finding; evidence file upload with hashing.

**WON'T (v1)** — real auth/RBAC enforcement; multi-tenancy; live cloud/GRC integrations; PDF redlining; NLP over policy documents; any real client data.

### 5.2 The five test suites

Algorithms and thresholds are specified in [TRD.md](TRD.md) §4. Here: what each proves, and to whom.

| # | Suite | Proves | Clause | Catches |
|---|---|---|---|---|
| 1 | **PII discovery + retention** | We know where personal data is, and we erase and retain on the legal clock | Rule 6(1)(a), 8(1), 8(2), 8(3) | S5, S6, S9 |
| 2 | **Consent withdrawal propagation** | Withdrawal actually stops downstream processing, at withdrawal speed | Act s.6(6), Rule 3 | S1 |
| 3 | **Access-control probes** | Access to personal data is actually restricted, under adversarial conditions | Rule 6(1)(b) | S2, S3 |
| 4 | **Third-party access monitor** | We know which processors hold access, on what basis, last used when | Rule 6(1)(b),(c) | S4 |
| 5 | **AI model assurance** | Algorithmic due diligence, evidenced | **Rule 13(3)**, NIST AI RMF MEASURE | S7, S8 |

> **Why suite 5 is a legal control, not a nice-to-have.** Rule 13(3) requires a Significant Data Fiduciary to *"observe due diligence to verify that technical measures including algorithmic software adopted by it … are not likely to pose a risk to the rights of Data Principals."* Fairness, drift and input-validation testing is how that due diligence is evidenced. This is the bridge between DPDP work and AI assurance work — the seam identified in §1.4. [SOURCES A1.3]

**Suite 2 deserves a note.** Consent withdrawal is where privacy tooling most often fails silently. The consent store updates instantly; the downstream systems refresh on a batch. The record looks compliant and the principal keeps getting marketed to. Suite 2 withdraws consent and then *asks the downstream system* — it tests the outcome, not the record.

**Suite 3 is an adversarial test, deliberately.** Probes attempt ownership override, boundary and type-confusion bypass (`NaN`, negative, overflow), IDOR, and stale-credential reuse. Assurance that only checks the happy path is not assurance.

**Suite 1 tests both directions of Rule 8.** Erasure overdue (8(1)) *and* logs purged too early (8(3)). Over-deletion is as much a finding as under-deletion, and most tools only look for one.

### 5.3 Framework mapping

| Framework | Role | Example |
|---|---|---|
| **DPDP Act 2023 + Rules 2025** | Primary. Every control cites a clause. | Rule 6(1)(c) → access logging |
| **ISO/IEC 27001:2022** | Control-design cross-reference; the language client security teams already speak | A.8.12 data leakage prevention; A.5.15 access control; A.8.15 logging |
| **NIST AI RMF 1.0** *(and ISO/IEC 42001 where it adds)* | Structures suite 5 | MEASURE 2.11 fairness/bias; MEASURE 2.4 drift; GOVERN 1.2 |

Mappings are many-to-many and shown as badges on every control, so a client already running ISO 27001 sees immediately what they can reuse — a genuine consulting insight, not decoration.

---

## 6. The Evidence Sufficiency Gate

**The signature feature.** Specified here in full because it is the product's argument.

### 6.1 Premise

A control verdict is a claim about a population — *"access to personal data is restricted"* — usually made from a sample. The claim is only as good as the sample. Most tools discard that fact at the moment of rendering. AssureLens carries it to the surface and lets it override the verdict.

### 6.2 Verdicts

| Verdict | Meaning |
|---|---|
| `PASS` | Control operated effectively, **and** evidence was sufficient to say so |
| `FAIL` | Control did not operate effectively, and the evidence is sufficient to say so |
| `INSUFFICIENT_EVIDENCE` | The test may have produced a signal, but the evidence cannot carry a conclusion |
| `NOT_APPLICABLE` | Out of scope for this entity, with a stated reason |

`INSUFFICIENT_EVIDENCE` is **not** a soft fail and must never be styled as one. It is a statement about the assessment, not the client.

### 6.3 Gate rules

The gate runs **after** the test and can override `PASS`/`FAIL`. Every rule is a named constant, documented in the TRD, and unit-tested.

| Rule | Fires when | Rationale |
|---|---|---|
| **G1 — Minimum sample** | `n < MIN_SAMPLE_N` (default 30) for a population-inference control | Below ~30 the interval is too wide to conclude |
| **G2 — Interval width** | Wilson 95% interval width > `MAX_CI_WIDTH` (default 0.20) | A "compliance rate" of 60–95% is not a finding |
| **G3 — Coverage** | Sampled population < `MIN_COVERAGE_PCT` (default 10%) of declared population | Testing 200 of 2.4M records proves little about the 2.4M |
| **G4 — Missing artifact** | A required evidence item in the contract is absent | Every control declares what it needs |
| **G5 — Stale evidence** | Newest evidence older than `MAX_EVIDENCE_AGE_DAYS` (default 90) | A control that worked in March is not evidence for September |
| **G6 — Non-representative sample** | Sample frame flagged as convenience or filtered | Testing only active accounts says nothing about dormant ones |
| **G7 — Source unverified** | Control's clause basis is an [SOURCES] open item | The product applies its own honesty rule to itself (S12) |
| **G8 — Target unreachable** | Probe could not execute | Absence of evidence, not evidence of absence |

`MIN_SAMPLE_N`, `MAX_CI_WIDTH`, `MIN_COVERAGE_PCT` and `MAX_EVIDENCE_AGE_DAYS` are per-control overridable, and every override is recorded and printed in the workpaper. Quietly loosening a threshold to turn a gate into a pass is exactly the behaviour this feature exists to prevent — so the product makes it visible.

### 6.4 What is always carried

Every result, regardless of verdict:

```
verdict, sample_size, population_size, coverage_pct,
point_estimate, ci_lower, ci_upper, ci_method,
evidence_items[], gate_fired, gate_reasons[],
thresholds_applied{}, threshold_overrides{}, run_at, run_seed
```

Proportions use the **Wilson score interval**, not the normal approximation — Wald is badly behaved at the extremes, and "30 of 30 passed" is precisely where an assurance tool must not report a zero-width interval. [TRD §5]

### 6.5 Rendering (contract with the UX brief)

`INSUFFICIENT_EVIDENCE` must read as deliberate. Never red, never an error icon, never a warning triangle. Neutral, confident, and always accompanied by:

1. **Why** — the gate rule, in plain language: *"Tested 12 of 2,400 records (0.5% coverage). Below the 10% threshold for a population conclusion."*
2. **What would clear it** — *"Sample 240 records, or narrow the control's scope to a defined subpopulation."*
3. **Who supplies it** — the evidence owner.

Full specification in [UX_BRIEF.md](UX_BRIEF.md) §6.

### 6.6 Demo success metric

The demo is successful when a meaningful share of controls land on `INSUFFICIENT_EVIDENCE` and every one explains itself. Target: **≥3 gated controls** in the seeded engagement, each with a distinct gate reason. If everything grades cleanly, the gate is decorative and the argument fails.

---

## 7. Outputs

### 7.1 Workpaper (DOCX) — for Aarti

Audit format, one section per control tested:

```
Control ref · Control objective · Clause reference (DPDP / ISO / NIST)
Procedure performed
Population and sample (n, N, coverage %, selection method)
Evidence obtained (itemised, with collection timestamps)
Result (Pass / Fail / Insufficient Evidence)
  — where a proportion: point estimate with 95% Wilson CI
  — where gated: gate rule, threshold, and what would clear it
Exception / finding (if any), with root cause
Recommendation
Prepared by · Date · Run ID · Seed
```

Front matter: scope, basis of preparation, methodology, **limitations** (stated, not buried), and a standing note that the document is not legal advice. Appendix: control library with full mappings; threshold register including every override.

### 7.2 Executive summary (1 page) — for Rohan

Where we stand by domain; the five things to fix first, ranked by impact × effort; what we could not conclude and why; what changes before 13 May 2027.

### 7.3 In-product

Engagement overview (readiness by domain, risk heatmap, evidence-quality meter); findings register with severity matrix; remediation roadmap; control detail with result history.

**Deliberately absent: a single headline compliance percentage.** It is the most requested feature in this category and the most dishonest. Readiness is reported per domain with coverage attached, and §11's FAQ answers the request rather than dodging it.

---

## 8. Success metrics

### 8.1 Product

| Metric | Target | Why |
|---|---|---|
| Seeded defects detected | **10 / 10** of S1–S9 (S10–S12 are gate cases) | The tests are real or they are not |
| False positives on clean controls | 0 | A tool that cries wolf is unusable |
| Controls gated on the seeded engagement | ≥3, each with a distinct reason | Proves §6 is load-bearing |
| Time to first finding, cold load | < 90s | Demo constraint |
| Full demo path | < 3 min | Interview constraint |
| Run reproducibility | Identical results for identical seed | P4 |
| Workpaper | Opens in Word, no manual fixing | Aarti's one-line test |

### 8.2 Project

| Metric | Target |
|---|---|
| Public URL loads cold and runs end to end | Yes |
| Every displayed figure traced to SOURCES.md | 100% |
| Every control cites a verified clause, or is flagged G7 | 100% |
| Open items D1–D6 closed or explicitly flagged in-product | 100% |
| README reads as a case memo | Problem, approach, findings, limits, what I'd do differently |

---

## 9. Limitations

Stated here, in the README, and in the workpaper front matter. Not buried.

1. **Synthetic data.** The estate is generated. It demonstrates that the tests work; it says nothing about any real organisation.
2. **Not legal advice.** Clause mappings are the author's reading of the Rules. A qualified adviser should confirm scope before reliance.
3. **Rules not fully in force.** Rules 3, 5–16, 22, 23 commence 13 May 2027. Controls are written against the notified text; interpretation will develop, and Board guidance may change it.
4. **Corrigendum not fully reviewed.** A corrigendum was published 16 December 2025. [SOURCES D1]
5. **Partial control coverage.** ~25 controls authored, ~12 executable in v1. The rest are documented with evidence contracts and render as `INSUFFICIENT_EVIDENCE` under G4 — which is the honest state for a control that has not been tested.
6. **Survey benchmarks are directional.** EY figures are self-reported from 150+ professionals, not a random sample of Indian enterprises. Shown as an external reference band, never as the user's position. [SOURCES B1]
7. **Single fictional entity.** Control weighting is tuned for a BFSI GCC and would need rework for another sector.
8. **No auth.** Public demo. Do not upload anything real.
9. **The hiring-seam reading is an inference** from a small sample of public job postings, not a claim about EY's staffing. [SOURCES B3]

---

## 10. Risks

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | Control library balloons past 25 | High | Med | Hard cap. 25 authored, 12 executable. Cut breadth before depth. |
| R2 | Misciting a rule | Med | **High** | Every citation traced in SOURCES; G7 gate for unverified; close D1 before publishing |
| R3 | Deployment eats day 10 | Med | High | Deploy a skeleton on day 1. Never a day-10 first deploy. |
| R4 | Gate statistics wrong | Low | **High** | Wilson implementation unit-tested against published values before any suite uses it |
| R5 | Demo too slow | Med | Med | Pre-seed and cache; measure the path from day 8 |
| R6 | UI drifts to generic SaaS | Med | Med | UX brief states negative constraints; design review before day 10 |
| R7 | Seeded flaws feel contrived | Low | Med | Every defect is a real failure pattern; S1 and S3 are drawn from patterns the author has seen in review work |
| R8 | Scope creep into a GRC platform | Med | High | §5.1 WON'T list is binding |

---

## 11. Anticipated questions

**"Why not just use OneTrust / a GRC suite?"** They manage compliance workflow. They do not execute adversarial tests against a running system, and they do not refuse to grade on thin evidence. AssureLens is a testing and evidence instrument, not a workflow tool.

**"Give me one compliance score."** No — and this is the product's position, not an omission. A single number averages a fatal access-control gap against a missing policy PDF. Readiness is per domain, with coverage attached, so you can see which parts of the estimate are load-bearing. [§7.3]

**"Isn't 'Insufficient Evidence' just admitting you don't know?"** Yes. That is the feature. An assurance opinion is only worth the evidence behind it, and naming the boundary is what separates an assessment from a dashboard.

**"Is the data real?"** No, and it says so on every screen and in every export. The tests are real; the estate they run against is generated.

**"How long would this take on a real engagement?"** The control library and test engine are reusable; per-client work is data mapping and evidence collection. That is the accelerator argument — and it is stated as an argument, not measured, because with one fictional client there is no measurement to report.

---

## 12. Build sequencing

Ten working days, full-time, with a demoable slice every day. Detail in [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md).

Day 1 skeleton + deploy · Day 2 control library · Day 3 target service + data generator · Day 4 engine + gate · Days 5–7 the five suites · Day 8 findings and overview · Day 9 upload, export, role switch · Day 10 deploy, README, verification, demo.

**Sequencing rationale.** Day 4 — the engine and the gate — is the critical path: every suite depends on it and it is the feature the product is arguing for. It is built before any suite, unit-tested against known values, and never touched again under time pressure. If days 5–7 overrun, suites are cut. **The gate is not cut.**
