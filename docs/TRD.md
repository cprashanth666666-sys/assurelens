# AssureLens — Technical Requirements Document

| | |
|---|---|
| Version | 1.0 |
| Date | 21 September 2026 |
| Status | Approved for build |
| Related | [PRD.md](PRD.md) · [SCHEMA.md](SCHEMA.md) · [UX_BRIEF.md](UX_BRIEF.md) · [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) · [../SOURCES.md](../SOURCES.md) |

---

## 1. Architecture

### 1.1 Components

```
┌────────────────────────────────────────────────────────────┐
│  frontend/          Next.js 15 App Router, React 19, TS    │
│  Server Components for reads · Client for run console      │
└───────────────────────────┬────────────────────────────────┘
                            │ HTTPS / JSON
┌───────────────────────────▼────────────────────────────────┐
│  backend/           FastAPI (Python 3.12)                  │
│    api/       REST routers                                 │
│    engine/    test runner · evidence broker · GATE         │
│    suites/    5 registered test-suite plugins              │
│    reporting/ DOCX workpaper + exec summary                │
│    ingest/    CSV upload, column mapping, profiling        │
│    seed/      deterministic synthetic generator            │
└──────┬─────────────────────────────────┬───────────────────┘
       │ SQLAlchemy 2.x                  │ HTTP probes
┌──────▼──────────────┐      ┌───────────▼────────────────────┐
│  PostgreSQL 16      │      │  target_service/               │
│  (Alembic)          │      │  FastAPI — Meridian's          │
└─────────────────────┘      │  customer API, WITH SEEDED     │
                             │  DEFECTS. Never imported by    │
                             │  the backend; only reached     │
                             │  over HTTP, as a real target.  │
                             └────────────────────────────────┘
```

### 1.2 Why the target service is a separate process

The tempting shortcut is to have suite 3 call the flawed functions directly. That would be a lie: it tests the code, not the deployed system, and it means the "vulnerability" is a fixture rather than a reachable defect.

The target service runs as its own process behind its own base URL. Suite 3 authenticates and probes it over HTTP exactly as an external tester would. Consequences that make the demo honest:

- A defect that is not reachable over the network is not found — same as reality.
- Evidence is a real request/response pair, attachable to the workpaper.
- If the target is down, the gate fires **G8 — target unreachable**, rather than silently passing.
- The seeded flaws can be fixed in the target and the suite re-run to show the finding close.

### 1.3 Request flow — a test run

```
POST /api/engagements/{id}/runs  {suite_ids[], seed?}
  → TestRunner creates test_run (status=running, seed recorded)
  → for each control in scope:
        resolve TestProcedure plugin
        EvidenceBroker.collect(contract)      # DB query | HTTP probe | file
        procedure.execute(evidence) -> RawResult(outcome, n, N, ...)
        SufficiencyGate.apply(RawResult, thresholds) -> Verdict
        persist test_result + evidence_items
        if verdict == FAIL and control.auto_raise: FindingService.raise()
  → test_run (status=complete)
Frontend polls GET /api/runs/{id} (2s) until complete.
```

Server-Sent Events were considered for the live console. Rejected: polling at 2s is sufficient for a ≤60s run, and SSE adds a failure mode on serverless hosting for no demo benefit. [ADR-004]

### 1.4 Deployment

| Component | Host | Notes |
|---|---|---|
| frontend | Vercel | Free tier |
| backend | Render (Docker web service) | Free tier; cold start ~30s |
| target_service | Render (second service) | Deliberately separate |
| Postgres | Render managed | Free tier |

**Cold-start mitigation.** Render free tier sleeps. The frontend issues `GET /api/health` on first paint and the overview renders from a cached snapshot while the backend wakes, so a recruiter opening a cold link sees content immediately, not a spinner. Measured from day 8 against the <90s target [PRD §8.1].

Local development is `docker compose up` — Postgres, backend, target service, frontend — with one `.env`.

---

## 2. Stack decisions (ADRs)

| # | Decision | Rationale | Rejected |
|---|---|---|---|
| ADR-001 | **FastAPI + Python** for backend | The statistics, PII detection, PSI and fairness maths belong in Python; author has FastAPI exposure from prior review work | Node backend — would force a second service for the maths anyway |
| ADR-002 | **Next.js App Router + TS** | Server Components suit read-heavy dense tables; one deploy target; real product feel | Streamlit — fastest to ship, but caps the UX brief and reads as a notebook |
| ADR-003 | **PostgreSQL** | Many-to-many control mappings, JSONB evidence payloads, append-only audit log | SQLite — no JSONB ergonomics, poor fit for a hosted demo |
| ADR-004 | **Polling, not SSE** | §1.3 | SSE, WebSockets |
| ADR-005 | **Separate target service** | §1.2 | In-process fixtures |
| ADR-006 | **Wilson score interval** | Correct near 0 and 1, where Wald collapses to zero width — exactly the case the gate must catch | Wald; bootstrap (overkill, non-deterministic) |
| ADR-007 | **python-docx** for workpaper | Native DOCX; Word-openable; matches audit convention | HTML→PDF (loses editability, and auditors edit workpapers) |
| ADR-008 | **Controls as YAML, seeded to DB** | Reviewable in git, diffable, the library *is* the intellectual content | DB-only (invisible in review); code-only (not editable) |
| ADR-009 | **No auth in v1** | Public demo; auth designed in §9 | Clerk/Auth.js — days of work, demo friction, zero assessment value |
| ADR-010 | **Deterministic seeding** | PRD P4; reproducible runs are an audit requirement | Random fixtures |

---

## 3. Test engine

### 3.1 Domain model

```python
Control          # what must be true (YAML → DB)
  └─ TestProcedure          # how to determine it (plugin)
       ├─ EvidenceContract  # what it needs to be allowed to conclude
       └─ execute()         # → RawResult
SufficiencyGate  # may override RawResult.outcome → Verdict
TestResult       # persisted verdict + statistics + evidence refs
Finding          # raised from a FAIL
```

### 3.2 Plugin contract

Every suite registers procedures against a stable interface. Adding a suite must not require editing engine core [PRD M4].

```python
@register("consent.withdrawal_propagation")
class WithdrawalPropagation(TestProcedure):
    evidence_contract = EvidenceContract(
        required=[
            Evidence("consent_records", EvidenceKind.DB_QUERY),
            Evidence("downstream_segment", EvidenceKind.HTTP_PROBE),
        ],
        population_source="consent_records",
        max_age_days=30,
    )

    def execute(self, ev: EvidenceBundle, cfg: dict) -> RawResult:
        ...
        return RawResult(
            outcome=Outcome.FAIL,
            sample_size=n, population_size=N,
            successes=k,                      # gate computes the interval
            detail={...}, artifacts=[...],
        )
```

`execute()` reports what it measured. It **never** decides sufficiency — that is the gate's job, and keeping the two apart is what stops a suite author from quietly widening a threshold. [PRD §6.3]

### 3.3 Evidence broker

Resolves a contract into an `EvidenceBundle`. Four kinds:

| Kind | Source | Failure → gate |
|---|---|---|
| `DB_QUERY` | Postgres (synthetic estate) | G4 if empty |
| `HTTP_PROBE` | target service | **G8** if unreachable |
| `FILE_ARTIFACT` | uploaded/seeded artifacts | G4 if absent, G5 if stale |
| `ATTESTATION` | questionnaire answer | Never sufficient alone — see below |

**Attestations never carry a verdict by themselves.** An attestation is evidence *about* a control, not the test *of* one [PRD P3]. A control whose only evidence is an attestation resolves to `INSUFFICIENT_EVIDENCE` under G4. This is what makes S10 (breach runbook never exercised) and S11 (grievance SLA unmeasured) gate rather than pass — and it is the single most common failure of questionnaire-based compliance tools.

Every collected item is hashed (SHA-256) and stored with `collected_at`, so the workpaper can assert the evidence has not changed since the conclusion was drawn.

### 3.4 Determinism

- Fixed `seed` per run, recorded on `test_runs` and printed in the workpaper.
- All randomness via `numpy.random.default_rng(seed)`. No bare `random`.
- Probe ordering sorted, never dict-iteration order.
- Timestamps in the synthetic estate are relative to a fixed `EPOCH` constant, not `now()`, so retention results do not drift day to day.

Enforced by test: the same seed twice must produce identical `test_results` rows excluding `id` and `run_at`.

---

## 4. The five suites

Thresholds below are **defaults**, declared as named constants in `engine/thresholds.py`, overridable per control, and every override printed in the workpaper [PRD §6.3].

### 4.1 Suite 1 — PII discovery and retention

**Clause:** Rule 6(1)(a) security of personal data · Rule 8(1) erasure · Rule 8(2) 48-hour notice · Rule 8(3) one-year minimum log retention. [SOURCES A1.3]

**1a. PII discovery.** Scan declared data assets, detect identifier classes, compare against the data inventory.

| Detector | Method |
|---|---|
| PAN-format | `[A-Z]{5}[0-9]{4}[A-Z]` + positional check |
| Aadhaar-format | 12 digits + **Verhoeff checksum** |
| Indian mobile | `[6-9]\d{9}` with delimiter tolerance |
| Email | RFC-lite pattern |
| Account number | length + issuer-prefix heuristic |
| Free-text PII | detectors over transcript columns — catches S9 |

Synthetic identifiers are generated to be *format-valid and checksum-valid but not real* — a real Aadhaar must never appear in a public repo, and a detector tested only against invalid strings is not tested.

**FAIL** if an asset holds an identifier class absent from the inventory, or holds unencrypted identifiers where the asset declares `encryption_at_rest = false`.

**1b. Retention — both directions.**

```
overdue_erasure = records where
    last_principal_contact < EPOCH - third_schedule_period
    AND erased_at IS NULL
    AND NOT legal_hold
                                    → FAIL (Rule 8(1))  [S5]

pre_erasure_notice = for records approaching erasure,
    a notice ≥48h before?           → FAIL if absent (Rule 8(2))  [S5]

log_retention = min(log age) < 365 days
    where processing_logs purged     → FAIL (Rule 8(3))  [S6]
```

> Over-deletion is a finding. A system that deletes personal data on schedule but purges processing logs at 90 days breaches Rule 8(3) while looking maximally privacy-friendly. Testing only one direction is the standard mistake.

### 4.2 Suite 2 — Consent withdrawal propagation

**Clause:** DPDP Act s.6(6) (withdrawal as easy as giving) · Rule 3 (notice must describe withdrawal). [SOURCES A1.3]

Outcome test, not record test:

```
1. sample n principals with active consent for purpose P     (n = 50 default)
2. record downstream state: does the marketing segment include them?
3. POST withdrawal via the target service's consent endpoint
4. assert 200 and consent store updated                      → record latency
5. re-probe downstream segment for each principal
6. classify:
     PROPAGATED    removed within PROPAGATION_SLA_SECONDS (300)
     LAGGED        removed, but beyond SLA
     NOT_PROPAGATED still present at probe time
```

`successes = PROPAGATED`; anything else counts against. Catches **S1**: consent store updates instantly, nightly batch means up to 22h of lag → `LAGGED` → FAIL with a measured latency distribution, which is a far stronger finding than "no propagation control observed."

Also asserts withdrawal effort parity (s.6(6)): step count and required fields for withdrawal vs grant, from the target service's form descriptors.

### 4.3 Suite 3 — Access-control probes (adversarial)

**Clause:** Rule 6(1)(b) measures to control access to computer resources. [SOURCES A1.3]

Authenticates to the target service as each of several principals, then probes. Each probe declares expected-vs-actual; deviation is a finding with the request/response pair as evidence.

| Probe | Attack | Expect | Catches |
|---|---|---|---|
| `P-01` ownership override | Read another tenant's customer via the vendor service account | 403 | **S2** |
| `P-02` IDOR enumeration | Sequential `customer_id` as a low-privilege principal | 403/404 | — |
| `P-03` type confusion | `spend_cap: NaN` — `NaN > limit` is always false | 400 | **S3** |
| `P-04` boundary | negative, zero, `Infinity`, int64 overflow on the same field | 400 | — |
| `P-05` stale credential | Authenticate with a 14-month-unused vendor token | 401 | **S4** |
| `P-06` privilege escalation | Self-assign a role via profile update | 403 | — |
| `P-07` mass assignment | Extra `is_admin: true` in an update body | ignored/400 | — |
| `P-08` log visibility | Was P-01 recorded in the access log? | logged | Rule 6(1)(c) |

P-03 is the NaN bypass and it is the probe worth explaining in an interview: IEEE-754 makes every comparison with `NaN` false, so a naive `if value > cap: reject` lets `NaN` straight through. It is a one-line defect with an unbounded blast radius, invisible to a code reviewer skimming for logic errors, and it is exactly the class of finding an adversarial review exists to catch.

P-08 tests the *control on the control*: if an unauthorised access is not logged, Rule 6(1)(c) visibility fails even where access control held.

**Statistics:** probe outcomes are census, not sample — the probe set is the population. `coverage_pct = 100`, G1/G2/G3 do not apply, **G8 does**.

### 4.4 Suite 4 — Third-party access monitor

**Clause:** Rule 6(1)(b) access control extending to processors · 6(1)(c) logging and review. Resonates with the EY GCC finding that only 60% monitor third-party data access. [SOURCES A1.3, B2]

For each of Meridian's 14 processors:

| Check | Fails when |
|---|---|
| DPA on file | No processor agreement reference |
| Scope proportionality | Granted scopes ⊃ scopes actually exercised in 180 days |
| Staleness | `last_used_at` > `STALE_ACCESS_DAYS` (180) and credential active |
| Credential rotation | `issued_at` > `MAX_CREDENTIAL_AGE_DAYS` (365), never rotated |
| Offboarding | Terminated relationship, access still live |
| Cross-border flag | Processor outside India without a documented Rule 15 basis |

Catches **S4** on staleness + missing DPA. Output ranks processors by residual risk — directly usable in a client conversation.

### 4.5 Suite 5 — AI model assurance

**Clause:** **Rule 13(3)** — SDF due diligence that algorithmic software does not pose a risk to Data Principals' rights. Mapped to NIST AI RMF MEASURE 2.11 (fairness) and 2.4 (drift). [SOURCES A1.3]

Target: `MFS-CPS-v3`, credit pre-screening.

**5a. Fairness — four-fifths rule.**
```
selection_rate(g) = approved(g) / applicants(g)
ratio = min(selection_rate) / max(selection_rate)
FAIL if ratio < FAIRNESS_RATIO_THRESHOLD (0.80)
```
Also computed: demographic parity difference, equal-opportunity difference (TPR gap) where ground truth exists. Per-group Wilson intervals; **a group below `MIN_GROUP_N` (30) is reported as gated, not as a disparity** — small-group noise masquerading as bias is the classic fairness-audit error. Catches **S7** at ratio 0.71.

**5b. Drift — Population Stability Index.**
```
PSI = Σ (actual% − expected%) · ln(actual% / expected%)
      over 10 quantile bins from the training distribution
PSI < 0.10  stable · 0.10–0.25 moderate · > 0.25 significant → FAIL
```
Zero-count bins use Laplace smoothing (ε = 1e-6) — otherwise PSI diverges to infinity and the result is meaningless. Catches **S8** on two features.

**5c. Input data validation.** Nulls above threshold; out-of-range against declared schema; duplicate applicant IDs; **target leakage** (any feature with |correlation| > `LEAKAGE_CORR_THRESHOLD` = 0.95 against the label, reported as suspected leakage requiring review, never as a certainty).

---

## 5. The Sufficiency Gate — implementation

### 5.1 Wilson score interval

```python
def wilson_interval(k: int, n: int, z: float = 1.959963985) -> tuple[float, float]:
    """95% Wilson score interval for k successes in n trials."""
    if n == 0:
        raise ValueError("undefined for n=0")
    p = k / n
    d = 1 + z*z/n
    centre = (p + z*z/(2*n)) / d
    margin = (z / d) * math.sqrt(p*(1-p)/n + z*z/(4*n*n))
    return max(0.0, centre - margin), min(1.0, centre + margin)
```

Unit-tested against published values before any suite consumes it [PRD R4]:

| k / n | Expected 95% Wilson | Note |
|---|---|---|
| 0 / 10 | ≈ (0.0000, 0.2775) | Wald gives (0,0) — the exact failure this avoids |
| 10 / 10 | ≈ (0.7225, 1.0000) | |
| 5 / 10 | ≈ (0.2366, 0.7634) | |
| 30 / 30 | ≈ (0.8843, 1.0000) | width 0.116 — passes G2 |
| 12 / 12 | ≈ (0.7387, 1.0000) | width 0.261 — **fails G2**, "12 of 12" is not a conclusion |

That last row is the whole argument in one line: twelve for twelve looks like a perfect score and is not evidence of one.

### 5.2 Gate evaluation

```python
def apply(raw: RawResult, ctl: Control, th: Thresholds) -> Verdict:
    reasons = []
    if raw.target_unreachable:                      reasons.append(G8)
    if raw.missing_required_evidence:               reasons.append(G4)
    if raw.source_status == "unverified":           reasons.append(G7)
    if raw.evidence_age_days > th.max_evidence_age: reasons.append(G5)
    if raw.sample_frame in NON_REPRESENTATIVE:      reasons.append(G6)

    if ctl.inference_mode == POPULATION:            # census probes skip these
        if raw.n < th.min_sample_n:                 reasons.append(G1)
        if raw.n > 0:
            lo, hi = wilson_interval(raw.successes, raw.n)
            if (hi - lo) > th.max_ci_width:         reasons.append(G2)
        if raw.coverage_pct < th.min_coverage_pct:  reasons.append(G3)

    return Verdict(INSUFFICIENT_EVIDENCE, reasons) if reasons \
           else Verdict(raw.outcome, [])
```

**Ordering matters.** Structural reasons (G8, G4, G7) are evaluated before statistical ones, so a control with no evidence at all is reported as "no evidence" rather than "sample too small" — different problems with different remedies.

All reasons are collected, not short-circuited: the UI shows every reason and every remedy [UX §6].

### 5.3 Threshold defaults

```python
MIN_SAMPLE_N            = 30     # n below which no population inference
MAX_CI_WIDTH            = 0.20   # 95% Wilson width above which no conclusion
MIN_COVERAGE_PCT        = 10.0   # sampled share of declared population
MAX_EVIDENCE_AGE_DAYS   = 90
PROPAGATION_SLA_SECONDS = 300
STALE_ACCESS_DAYS       = 180
MAX_CREDENTIAL_AGE_DAYS = 365
FAIRNESS_RATIO_THRESHOLD= 0.80   # four-fifths rule
MIN_GROUP_N             = 30
PSI_SIGNIFICANT         = 0.25
PSI_MODERATE            = 0.10
LEAKAGE_CORR_THRESHOLD  = 0.95
```

Each carries a docstring citing its basis. Four-fifths is a US EEOC convention adopted here as a documented, arguable default — not a DPDP requirement, and the product says so rather than implying legal force.

---

## 6. CSV upload and column mapping

Turns a fixed demo into a reusable accelerator [PRD S1].

1. **Upload** — CSV/XLSX, ≤ 25 MB, ≤ 500k rows.
2. **Profile** — per column: inferred type, null %, cardinality, sample values, and **PII detector hits**.
3. **Suggest** — map columns to the canonical schema (`principal_id`, `consent_status`, `last_contact_at`, `group_attribute`, `score`, `outcome`, …) by name similarity + detector agreement. Confidence shown; nothing auto-applied above the user's head.
4. **Confirm** — user adjusts; mapping saved as a reusable profile.
5. **Validate** — required fields present, types coercible, dates parseable. Failures block the run rather than degrading it silently.
6. **Run** — suites execute against the uploaded asset. Suites whose required fields are unmapped return `INSUFFICIENT_EVIDENCE` (G4), **not** an error. A partial upload yields a partial, honest assessment.

Uploads are ephemeral (24h TTL, purged by job), and the upload screen states plainly that this is a public demo and no real personal data should be uploaded.

---

## 7. Reporting

`python-docx`, template-driven, structure per [PRD §7.1].

| Requirement | Implementation |
|---|---|
| Deterministic | Same run ID → byte-identical document (fixed metadata, no `now()` in body) |
| Traceable | Every control prints clause ref, run ID, seed, evidence hashes |
| Honest | Limitations in front matter; every gate reason printed in full |
| Editable | Real DOCX styles, real tables — an auditor must be able to edit it |
| Tabular figures | Numeric columns right-aligned, monospaced, consistent precision |

Threshold register appendix lists every threshold applied **and every override**, so loosening a gate is visible in the deliverable [PRD §6.3].

Executive summary is a second, one-page template driven from the same data — never a separately maintained narrative.

---

## 8. API surface

```
GET  /api/health
GET  /api/engagements/{id}
GET  /api/controls                    ?framework=&domain=&status=
GET  /api/controls/{ref}
POST /api/engagements/{id}/runs       {suite_ids[], seed?}
GET  /api/runs/{id}                   status + results (polled)
GET  /api/results/{id}/evidence
GET  /api/engagements/{id}/findings
PATCH /api/findings/{id}
GET  /api/engagements/{id}/roadmap
POST /api/uploads                     multipart
POST /api/uploads/{id}/mapping
GET  /api/engagements/{id}/report.docx        ?variant=workpaper|summary
POST /api/engagements/{id}/reset      re-seed to demo state
```

`/reset` matters for a public demo: anyone can explore destructively, and the next visitor gets a clean engagement.

Errors are RFC 7807 problem+json. Pydantic v2 models throughout; OpenAPI served at `/docs`.

---

## 9. Security (and how auth would be added)

**Built in v1:** input validation at every boundary; parameterised queries only; CORS locked to the frontend origin; rate limiting on run and upload; upload type/size limits with content sniffing; secrets via environment only; the target service isolated with **no database credentials** and no path to production data.

**Deliberately not built:** authentication and RBAC [ADR-009].

**How it would be added** — designed now so the schema does not need rework. `users` and `roles` already exist in [SCHEMA.md](SCHEMA.md). Auth.js on the frontend issues a session; the backend validates a JWT in a dependency; `require_role("consultant")` guards mutating routes; engagement-scoped row filtering enforces tenancy; the audit log gains a real `actor_id` in place of the demo's synthetic actor. The role switch becomes a claim rather than a toggle.

**The target service is deliberately vulnerable.** Its README and its `/` response say so. It holds only synthetic data, has no DB credentials, and is rate-limited. Publishing a knowingly flawed service requires it to be unmistakably labelled and incapable of reaching anything real — both conditions are met, and the labelling is a build requirement, not a nicety.

---

## 10. Testing

| Layer | Tool | Covers |
|---|---|---|
| Unit | pytest | **Wilson interval against published values**; each gate rule in isolation; PSI incl. zero-bin smoothing; Verhoeff checksum; detectors against valid and invalid inputs |
| Suite | pytest | Each suite against a known fixture with a known answer |
| **Seeded-defect** | pytest | **Every one of S1–S9 is detected**; S10–S12 gate with the expected reason |
| False-positive | pytest | A clean fixture produces zero findings |
| Determinism | pytest | Same seed → identical results |
| Contract | schemathesis | API responses match OpenAPI |
| E2E | Playwright | Full demo path; report downloads and opens |

The seeded-defect suite is the one that matters. It is the executable form of [PRD §8.1] and it is what lets the README state a detection rate as a measured number rather than a claim.

CI (GitHub Actions): lint (ruff, eslint) → typecheck (mypy, tsc) → unit → suite → E2E on PR.

---

## 11. Performance

| Operation | Target |
|---|---|
| Overview load (warm) | < 500 ms |
| Control library (25 rows) | < 300 ms |
| Full run, 5 suites | < 45 s |
| Single suite | < 15 s |
| DOCX generation | < 5 s |
| CSV profile, 100k rows | < 10 s |
| Cold start to first content | < 30 s (cached snapshot while backend wakes) |

Approach: pandas vectorisation over row loops; indexes per [SCHEMA.md](SCHEMA.md) §4; `LIMIT` on every list endpoint; suites run concurrently where independent (3 and 4 both hit the target service — serialised to keep probe evidence clean).

---

## 12. Repository layout

```
backend/
  app/
    api/          routers
    engine/       runner.py  gate.py  evidence.py  thresholds.py  stats.py
    suites/       pii_retention.py  consent.py  access_probes.py
                  third_party.py  ai_assurance.py
    reporting/    workpaper.py  summary.py  templates/
    ingest/       upload.py  profiler.py  mapper.py
    seed/         generator.py  meridian.py
    models/       SQLAlchemy
  alembic/
  tests/
controls/         dpdp.yaml  iso27001_map.yaml  nist_ai_rmf_map.yaml
target_service/   app.py  defects.py  README.md
frontend/         app/  components/  lib/  styles/tokens.css
docs/             PRD.md  TRD.md  UX_BRIEF.md  SCHEMA.md  IMPLEMENTATION_PLAN.md
README.md  SOURCES.md  docker-compose.yml
```

`controls/*.yaml` is the intellectual core of the project and lives in git precisely so it is reviewable as a diff [ADR-008].
