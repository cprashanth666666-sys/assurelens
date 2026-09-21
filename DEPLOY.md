# Deployment

Three services: frontend on **Vercel**, backend and target service on **Render**, Postgres on Render.

> **Order matters.** Vercel needs the API URL at *build* time, and Render needs the Vercel origin for CORS. That is a two-way dependency, so it resolves in three passes. Doing Vercel first produces a failed build, by design — the guard in `frontend/next.config.mjs` refuses to ship a bundle pointing at localhost.

---

## Step 1 — Render (backend, target service, database)

Target: existing Render project **`assurelens`**, environment **`EY`** (currently empty).

1. **New → Blueprint** at [dashboard.render.com](https://dashboard.render.com)
2. Connect the GitHub repo `cprashanth666666-sys/assurelens`. Render reads [render.yaml](render.yaml) and provisions three things: `assurelens-api`, `assurelens-target`, `assurelens-db`.
3. When prompted for a destination, choose project **`assurelens`** → environment **`EY`**. Creating the blueprint from the project's own *Create new service* button does the same thing, but "New → Blueprint" is the path that reads `render.yaml` rather than asking you to configure a service by hand.
4. Render will prompt for the one variable marked `sync: false`:

   | Variable | Value |
   |---|---|
   | `CORS_ALLOW_ORIGINS` | `http://localhost:3000` — a placeholder; Step 3 replaces it |

5. Wait for the first deploy. Then note the API URL, which will be roughly:

   ```
   https://assurelens-api.onrender.com
   ```

   Render appends a suffix if the name is taken, so **copy the real one** rather than assuming.

6. Confirm it is alive:

   ```bash
   curl https://assurelens-api.onrender.com/api/health
   ```

   Expect `{"status":"ok","database":"up",...}`. If `database` reads `misconfigured`, the `DATABASE_URL` binding failed — that state exists specifically to tell you it is a configuration fault and not a cold start, so do not wait it out.

---

## Step 2 — Vercel (frontend)

1. **Add New → Project** at [vercel.com/new](https://vercel.com/new), import the same repo.
2. Settings that matter:

   | Setting | Value | Why |
   |---|---|---|
   | **Root Directory** | `frontend` | The repo root holds the backend too; Vercel must build the subdirectory |
   | Framework Preset | Next.js | Auto-detected |
   | Build Command | *(default)* | |

3. **Environment Variables** — add before the first build:

   | Variable | Value | Scope |
   |---|---|---|
   | `NEXT_PUBLIC_API_BASE_URL` | the Render API URL from Step 1 | Production, Preview, Development |

   `NEXT_PUBLIC_*` is inlined into the client bundle during `next build` and never read at runtime. Added afterwards, it does nothing until the next build. The build will **fail with an explicit message** if it is missing — that is deliberate, and preferable to a deployed page whose visitors' browsers quietly probe their own port 8000.

4. Deploy, then note the production URL, e.g. `https://assurelens.vercel.app`.

---

## Step 3 — Close the loop (CORS)

Back in Render → `assurelens-api` → **Environment**:

| Variable | Value |
|---|---|
| `CORS_ALLOW_ORIGINS` | your Vercel production URL, no trailing slash |

Comma-separate to include preview deployments:

```
https://assurelens.vercel.app,http://localhost:3000
```

Never `*`. The backend reads this as an explicit allowlist and sends credentials; a wildcard with credentials is both a security fault and rejected by browsers.

Redeploy the API, then open the Vercel URL. The overview page should report **API `ok`**, **Database `up`**.

---

## Continuous deployment

Once connected, both hosts redeploy on push:

| Branch | Vercel | Render |
|---|---|---|
| `main` | Production | Auto-deploy |
| `workd` | Preview URL per push | No |

Preview deployments call the production API, which is what the shared `NEXT_PUBLIC_API_BASE_URL` scope gives you. If a preview ever needs its own backend, set the variable per-environment.

---

## Free-tier cold starts

Render free services sleep after inactivity and take roughly 30 seconds to wake. The frontend is built for this: it renders immediately and probes `/api/health` in the background, so a cold link never shows only a spinner. The database connect timeout is bounded at 5 seconds so health always answers rather than hanging. [TRD §1.4]

Before an interview demo, open the link once a few minutes early to warm it.

---

## Verifying a deployment

```bash
# Backend alive and connected
curl https://<api>.onrender.com/api/health

# Target service is reachable and labelled as deliberately vulnerable
curl https://<target>.onrender.com/

# Frontend served
curl -o /dev/null -w "%{http_code}\n" https://<app>.vercel.app/
```

The target service returns a warning banner in its root response. That labelling is a build requirement, not decoration — see [target_service/README.md](target_service/README.md).
