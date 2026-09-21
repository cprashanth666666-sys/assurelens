# ⚠ Target Service — DELIBERATELY VULNERABLE

**This service contains intentional security defects. Do not deploy it against anything real.**

It exists so that AssureLens's access-control suite has a genuine target to probe over HTTP, rather than calling flawed functions in-process. A defect that is not reachable over the network should not be found — same as reality. [docs/TRD.md §1.2]

## Safety properties

| | |
|---|---|
| Data | Synthetic only. Generated, never real. |
| Database credentials | **None.** This service holds no database connection. |
| Network reach | Cannot reach production, the AssureLens database, or any external system. |
| Labelling | The root endpoint `/` states that the service is deliberately vulnerable. |
| Rate limiting | Applied to all endpoints. |

These conditions are build requirements, not conveniences. Publishing a knowingly flawed service is only acceptable when it is unmistakably labelled and incapable of reaching anything real. [docs/TRD.md §9]

## Planted defects

Built on Day 3. Each defect is annotated in `defects.py` with the control it violates:

| Ref | Defect | Violates |
|---|---|---|
| S2 | Vendor service account can read customers beyond its scope (missing ownership check) | Rule 6(1)(b) |
| S3 | Spend-cap bypass via `NaN` — every IEEE-754 comparison with `NaN` is false | Rule 6(1)(b) |
| S4 | 14-month-unused vendor token still accepted | Rule 6(1)(b), (c) |
| S1 | Consent withdrawal updates the store but the marketing segment refreshes nightly | Act s.6(6) |

## Running

```bash
docker compose up target_service
```

Then `http://localhost:8001`.
