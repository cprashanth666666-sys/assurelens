# Deployment

| Component | Host | Why |
|---|---|---|
| Frontend | **Vercel** | Free, no expiry, Git integration |
| Backend + target service | **Render** | Free web services; they sleep, they do not expire |
| PostgreSQL | **Neon** | Free plan with **no expiry** — see below |

> **Why not Render's database.** Render's Free PostgreSQL **expires 30 days after creation**. After a 14-day grace period Render **deletes it and all its data** (Render docs, *Free Postgres → 30-day limit*). A link that goes in a job application has to survive months, not 30 days, so Postgres lives on Neon, whose free plan states plainly that none of its limits delete your data.

> **Order matters.** Vercel needs the API URL at *build* time and Render needs the Vercel origin for CORS, so the dependency is two-way and resolves in four passes. Running Vercel early produces a failed build **by design** — the guard in `frontend/next.config.mjs` refuses to ship a bundle pointing at localhost.

---

## Step 1 — Neon (PostgreSQL)

1. Sign up at [neon.tech](https://neon.tech) and create a project named `assurelens`.
2. Pick the region closest to you (`ap-southeast-1` Singapore for India).
3. Copy the connection string from **Connection Details**. It looks like:

   ```
   postgresql://neondb_owner:••••@ep-something-123.ap-southeast-1.aws.neon.tech/neondb?sslmode=require
   ```

   Paste it **verbatim**. The backend normalises the bare `postgresql://` prefix to the psycopg driver itself, so you do not need to edit it.

**Free plan limits, against what this project uses:**

| Limit | Free plan | AssureLens |
|---|---|---|
| Expiry | none | — |
| Storage | 0.5 GB / project | ~50 MB after the Day 3 synthetic estate |
| Compute | 100 CU-hours / month | scale-to-zero after 5 min idle; a demo opened occasionally uses very little |

---

## Step 2 — Render (backend and target service)

Target: existing Render project **`assurelens`**, environment **`EY`**.

1. **New → Blueprint** at [dashboard.render.com](https://dashboard.render.com).
2. Connect `cprashanth666666-sys/assurelens`. Render reads [render.yaml](render.yaml) and creates two services: `assurelens-api` and `assurelens-target`.
3. When prompted for a destination, choose project **`assurelens`** → environment **`EY`**.
4. Render prompts for the two variables marked `sync: false`:

   | Variable | Value |
   |---|---|
   | `DATABASE_URL` | the Neon string from Step 1 |
   | `CORS_ALLOW_ORIGINS` | `http://localhost:3000` — placeholder, replaced in Step 4 |

5. Wait for the deploy. The start command runs `alembic upgrade head`, then `python -m app.seed`, then uvicorn — so the control library is loaded on first boot. Seeding is idempotent, so redeploys are safe.
6. Copy the API URL, roughly `https://assurelens-api.onrender.com`. Render appends a suffix if the name is taken, so **copy the real one**.
7. Confirm:

   ```bash
   curl https://assurelens-api.onrender.com/api/health
   curl https://assurelens-api.onrender.com/api/engagement
   ```

   Expect `{"status":"ok","database":"up",...}` and an engagement reporting **25 controls, 13 executable, 1 out of scope**.

   If `database` reads **`misconfigured`**, the connection string is wrong — that state exists specifically to tell you it is a configuration fault and not a cold start, so do not wait it out.

---

## Step 3 — Vercel (frontend)

1. **Add New → Project** at [vercel.com/new](https://vercel.com/new), import the same repo.

   | Setting | Value | Why |
   |---|---|---|
   | **Root Directory** | `frontend` | The repo root holds the backend too |
   | Framework Preset | Next.js | Auto-detected |

2. **Environment Variables** — add **before** the first build:

   | Variable | Value | Scope |
   |---|---|---|
   | `NEXT_PUBLIC_API_BASE_URL` | the Render API URL from Step 2 | Production, Preview, Development |

   `NEXT_PUBLIC_*` is inlined into the client bundle during `next build` and never read at runtime. Added afterwards it does nothing until the next build. The build **fails with an explicit message** if it is missing — deliberate, and far better than a deployed page whose visitors' browsers quietly probe their own port 8000.

3. Deploy, then copy the production URL, e.g. `https://assurelens.vercel.app`.

---

## Step 4 — Close the loop (CORS)

Render → `assurelens-api` → **Environment**:

```
CORS_ALLOW_ORIGINS = https://assurelens.vercel.app,http://localhost:3000
```

No trailing slash. Never `*`: the backend sends credentials, and browsers reject that combination anyway.

Redeploy the API, then open the Vercel URL. The overview should report **API `ok`**, **Database `up`**, and `/controls` should list 25 controls.

---

## Continuous deployment

| Branch | Vercel | Render |
|---|---|---|
| `main` | Production | Auto-deploy |
| `workd` | Preview URL per push | No |

Preview deployments call the production API, which is what the shared `NEXT_PUBLIC_API_BASE_URL` scope gives you.

---

## Cold starts

Render free web services sleep after inactivity and take roughly 30 seconds to wake; Neon computes suspend after 5 minutes and resume in about a second. The frontend is built for this: it renders immediately and probes `/api/health` in the background, and the database connect timeout is bounded at 5 seconds so health always answers rather than hanging. [TRD §1.4]

**Open the link a few minutes before an interview demo** so everything is warm.

---

## Verifying a deployment

```bash
# Backend alive, connected, and seeded
curl https://<api>.onrender.com/api/health
curl https://<api>.onrender.com/api/engagement

# Target service reachable and labelled as deliberately vulnerable
curl https://<target>.onrender.com/

# Frontend served
curl -o /dev/null -w "%{http_code}\n" https://<app>.vercel.app/
```

The target service returns a warning in its root response. That labelling is a build requirement, not decoration — see [target_service/README.md](target_service/README.md).
