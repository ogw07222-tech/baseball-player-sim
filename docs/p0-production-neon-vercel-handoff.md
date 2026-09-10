# P0 Production Neon → Vercel Handoff

## Production database

Provider: Neon (Lakebase Postgres / PostgreSQL 16)

Production resource contract:
- Project: `baseball-player-sim-production`
- Branch: `production`
- Database: `baseball_sim`
- Role: `baseball_sim_app`
- Region: `aws-us-east-2`
- Runtime connection: pooled PostgreSQL endpoint with `sslmode=require`
- Migration/admin connection: direct/unpooled PostgreSQL endpoint

Never commit a connection string, role password, or generated credential to Git, PR bodies, issues, logs, or status documents.

## Schema

Canonical migration: `migrations/0001_session_store.sql`.

Tables:
- `baseball_sim_sessions`: opaque session id, canonical JSONB save payload, revision, save version, updated timestamp.
- `baseball_sim_idempotency`: `(session_id, idempotency_key)` primary key, request fingerprint, committed response JSONB, resulting revision, creation timestamp, FK cascade to session.

`PostgresSessionStore` remains the only application adapter boundary. Production mutation semantics are transaction + `SELECT ... FOR UPDATE` + revision comparison + durable idempotency lookup + one authoritative mutation + revision-guarded update + idempotency insert + commit.

## Vercel production environment

Required project environment variable:
- `DATABASE_URL`: the Neon **pooled** connection string for the production branch/database/role. Scope: **Production**.

No additional application environment variable is required on Vercel for production detection because Vercel supplies `VERCEL`. `BASEBALL_SIM_PRODUCTION=1` remains available for non-Vercel production-like execution/tests, but is not required for the Vercel deployment.

Do not configure `BASEBALL_SIM_SQLITE_PATH` as a production fallback. Production intentionally fails closed when no external database URL is available.

After adding or changing `DATABASE_URL`, create a new production deployment/redeploy so the function receives the updated environment.

## Vercel project settings

The Vercel project must deploy from the repository root, not `web/`, because the production topology uses the root Python/FastAPI entrypoint and builds the Vite frontend as part of the same deployment.

Expected runtime topology:

Browser → same-origin `/api/v1/*` → FastAPI → `CareerEngine` → `ProductionAdvanceService` → `PostgresSessionStore` → Neon

Non-API routes are served by the built SPA. Unknown `/api/*` routes must remain JSON 404 responses rather than SPA fallback.

## Production smoke

After the production deployment is available, run:

```bash
python tools/deployed_p0_smoke.py https://<production-domain>
```

The smoke covers session discovery, career creation, state load, one `next_game`, revision increment, durable resume with a new client, idempotency replay, stale revision 409, and API error schema.

Then verify in a real browser:
1. Open the production URL and create/resume a career.
2. Confirm the displayed dashboard/state comes from the backend DTO.
3. Advance exactly one game and observe game/stat change.
4. Refresh the page and confirm the same career/revision remains.
5. Repeat after a later/separate function invocation to confirm serverless-instance independence.
6. Confirm production does not bootstrap `MockGameDataProvider` as authority.

## Current external blocker

If the connected Vercel account exposes no team/project, `DATABASE_URL` cannot be injected and the deployed smoke cannot be completed from ChatGPT. In that case keep `VERCEL_PRODUCTION_WIRING`, `DEPLOYED_NEXT_GAME_E2E`, and `P0_WEB_PYTHON_PRODUCTION_COMPLETE` OPEN/BLOCKED until Vercel project authorization is restored.
