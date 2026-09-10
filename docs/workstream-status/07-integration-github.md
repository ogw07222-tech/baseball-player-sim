# 07 - Integration & GitHub

WORKSTREAM: 07 - Integration & GitHub
UPDATED_AT: 2026-09-11
SOURCE_OF_TRUTH: main@886a14665cd58f7a882eae5d9e9aaed155dca688
STATE: BLOCKED
CURRENT_TASK: P0 Production Deployment Completion — Vercel + External Durable Store
RESULT: OPEN — production persistence/Vercel wiring code is merged and CI-green, but actual Neon resource connection, Vercel project access, production deployment, cold-start persistence, and deployed browser E2E are not yet executable from the connected accounts

## LAST_COMPLETED
- Started from `main@0f988231bb6933f96180dbff4c6dbf8800a9885a` and audited the existing PR #42 SessionStore/API/deployment contract.
- Chose PostgreSQL with Neon as the intended Vercel external durable-store provider because the current SessionStore mutation contract maps directly to transactional row locking/CAS and Neon is Vercel/serverless compatible.
- Added `PostgresSessionStore` behind the existing `SessionStore` interface; no provider-specific behavior leaked into gameplay/presentation layers.
- Persisted opaque `session_id`, canonical full save payload, revision, save_version, updated_at, idempotency fingerprint, committed response, and resulting revision.
- Added row-level `SELECT ... FOR UPDATE` serialization so concurrent same-session/same-revision mutations execute the authoritative mutator exactly once; the loser receives revision conflict after the winner commits.
- Added same-key concurrent replay semantics: one mutation executes, the other waits and replays the committed response without a second simulation.
- Hardened production fail-closed selection: Vercel/production ignores any SQLite path and requires `BASEBALL_SIM_DATABASE_URL`, `DATABASE_URL`, or `POSTGRES_URL`; absent/unavailable external storage returns `SAVE_FAILED` rather than succeeding on ephemeral storage.
- Added production anonymous-session cookie policy: opaque UUID, HttpOnly, Secure on production, SameSite=Lax, Path=/, Max-Age=31536000; browser never transports the serialized save payload.
- Added root Vercel FastAPI configuration/entrypoint and Vite build hook; FastAPI owns `/api/v1/*`, serves built Vite SPA for non-API routes, and has an explicit JSON `/api/*` 404 before SPA fallback.
- Added reproducible deployed smoke script `tools/deployed_p0_smoke.py` covering create/state/next_game/revision/idempotency/stale-409/new-client recovery/API error schema.
- Added PostgreSQL 16 service-backed CI tests for external-store persistence, restart recovery, CAS race, same-key concurrency/idempotency, production fail-closed, secure cookie contract, Vercel entrypoint, and existing regression gates.
- First feature run #645 failed only because a cookie test used SQLite `:memory:` while SQLiteSessionStore opens per-operation connections; all PostgreSQL durable-store tests were already PASS. The fixture was changed to temp-file SQLite without changing production semantics.
- Feature run #646 completed GREEN across external-store tests, Vercel entrypoint, API vertical slice, related production tests, full Python suite, Auto career smoke, Balance smoke, draft calibration, web build, and web tests.
- PR #43 `P0: Complete Vercel production persistence wiring` passed PR run #647 GREEN and merged as `886a14665cd58f7a882eae5d9e9aaed155dca688`.
- Post-merge main run #648 completed GREEN across the same required gates.

## CURRENT_FINDINGS
- Intended production flow is Browser -> Vercel same origin -> FastAPI `/api/v1/*` -> authoritative CareerEngine -> ProductionAdvanceService -> Postgres SessionStore -> response -> browser.
- `HttpBackendPresentationGateway` already uses relative `/api/v1` with same-origin credentials, so no production CORS workaround or absolute backend URL is required.
- PostgreSQL adapter contract is validated against a real PostgreSQL 16 service in CI, including concurrent mutation behavior; it does not rely on a mock database for CAS semantics.
- Production store configuration precedence is `BASEBALL_SIM_DATABASE_URL` -> `DATABASE_URL` -> `POSTGRES_URL`.
- PostgreSQL schema is initialized idempotently with `CREATE TABLE IF NOT EXISTS` and keeps provider details behind `PostgresSessionStore`.
- `replace()` writes the complete canonical save at revision 1 and clears prior idempotency records for that anonymous session; `mutate()` commits complete save + revision+1 + replay record in one transaction.
- A second adapter instance can recover the same committed PostgreSQL session, validating process/cold-instance-independent persistence at the database-adapter level.
- No gameplay, hitting/pitching probability, rating, growth, injury, event, pitcher-usage, KBO inning/rule, stat formula, UI redesign, new screen, or week/month/season advance behavior was changed.
- Connected Vercel access currently exposes no usable team/project, and a direct fetch of the repo homepage deployment `baseball-player-sim-ui.vercel.app` through the connected Vercel capability returned 403. Therefore the existing production project's root directory, environment variables, deployment, and runtime logs cannot currently be managed/verified here.
- Neon plugin/resource access is not currently installed/connected. A Neon connection was suggested during this task, but no database resource can be provisioned or inspected until that user-authorized connection exists.

## BLOCKERS
- Vercel project/account authorization is not currently available through the connected Vercel capability; no team/project is visible and existing deployment access returns 403.
- Neon is not yet connected, so no real production Postgres resource or production `DATABASE_URL` can be provisioned/configured from this chat.
- Because those external resources are unavailable, production deployment and deployed runtime mutation tests cannot be executed truthfully.

## OPEN_ITEMS
- Connect/authorize the Vercel account/project that owns `baseball-player-sim-ui.vercel.app` or the intended replacement production project.
- Connect Neon, provision/select the production PostgreSQL database, and expose its pooled connection URL to Vercel production as `DATABASE_URL` (or the explicit `BASEBALL_SIM_DATABASE_URL` override).
- Confirm Vercel project Root Directory is repository root so root `pyproject.toml`/FastAPI entrypoint and `web/` Vite build execute in the intended same-origin topology.
- Deploy merged main and run `tools/deployed_p0_smoke.py <production-url>`.
- Perform real browser E2E on the deployed URL, including refresh persistence and confirmation that production UI renders backend DTOs with no MockGameDataProvider authority.
- Establish cold-start/serverless-instance persistence evidence from separate invocations/runtime logs after production deployment.

## DEPENDENCIES
- Vercel account/project authorization for the production domain.
- Neon account/resource authorization and production PostgreSQL connection string supplied through Vercel environment variables; secrets must remain outside Git.
- 06 Web UI can continue relying on the current relative `/api/v1` gateway contract; no frontend simulation logic is required.

## NEXT_ACTION
- After Vercel and Neon are connected, provision/link Neon, configure production `DATABASE_URL`, verify repository-root Vercel settings, deploy current main, then run deployed HTTP + browser + cold-start persistence smoke. Do not broaden advance beyond `next_game` until these production gates pass.

## RELATED_PRS
- #43 merged: P0 Vercel production persistence wiring
- #42 merged: P0 Web ↔ Python local/CI vertical slice
- #37 merged: production presentation contract/provider foundation

## RELATED_BRANCHES
- main
- feature/p0-production-deployment
- feature/p0-web-python-vertical-slice

## GATES
- POSTGRES_SESSION_STORE_ADAPTER = PASS
- POSTGRES_REAL_SERVICE_TESTS = PASS
- POSTGRES_RESTART_RECOVERY = PASS
- POSTGRES_CAS_RACE = PASS
- POSTGRES_CONCURRENT_IDEMPOTENCY = PASS
- PRODUCTION_FAIL_CLOSED = PASS
- PRODUCTION_SECURE_SESSION_COOKIE = PASS
- VERCEL_FASTAPI_ENTRYPOINT_CODE = PASS
- VERCEL_API_SPA_ROUTE_SEPARATION_CODE = PASS
- DEPLOYED_SMOKE_SCRIPT = PASS
- API_INTEGRATION_TESTS = PASS
- RELATED_PRODUCTION_TESTS = PASS
- PYTHON_UNIT_SUITE = PASS
- AUTO_CAREER_SMOKE = PASS
- BALANCE_SMOKE = PASS
- DRAFT_CALIBRATION_GATE = PASS
- WEB_BUILD = PASS
- WEB_TESTS = PASS
- PR43_CI = PASS
- PR43_MERGED = PASS
- MAIN_CI_GREEN = PASS
- MOCK_NOT_PRODUCTION_AUTHORITY = PASS
- EXTERNAL_DURABLE_STORE = OPEN
- VERCEL_PRODUCTION_WIRING = OPEN
- PRODUCTION_SESSION_PERSISTENCE = OPEN
- PRODUCTION_IDEMPOTENCY = OPEN
- PRODUCTION_REVISION_CAS = OPEN
- DEPLOYED_NEXT_GAME_E2E = OPEN
- DEPLOYED_BROWSER_E2E = OPEN
- COLD_START_PERSISTENCE = OPEN
- P0_WEB_PYTHON_PRODUCTION_COMPLETE = OPEN
