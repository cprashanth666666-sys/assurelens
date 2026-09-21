# AssureLens

**A DPDP + AI controls assurance workbench.** It turns the Digital Personal Data Protection Act 2023 and Rules 2025 into an executable control library, runs real tests against a live system, and **refuses to state a result its evidence cannot support**.

> **Status: Day 1 of 10.** Skeleton and deployment pipeline. The control library, test engine and suites are being built — see [docs/IMPLEMENTATION_PLAN.md](docs/IMPLEMENTATION_PLAN.md). This README becomes a full case memo on Day 10.

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
cd backend && ruff check . && mypy app && pytest -q
cd frontend && npm run lint && npm run typecheck && npm run build
```

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
4. **A corrigendum published 16 December 2025 has not yet been fully reviewed** — see [SOURCES.md](SOURCES.md) §D.
5. **No authentication.** This is a public demonstration. Do not upload real personal data.

## Author

C. Prashanth — built as a portfolio project for a Digital Risk / Technology Risk consulting application.
