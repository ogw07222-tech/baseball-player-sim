# 07 - Integration & GitHub

WORKSTREAM: 07 - Integration & GitHub
UPDATED_AT: 2026-09-11
SOURCE_OF_TRUTH: main@4a07dd8170ac7336e849bc6a4b0d124bf10dd5a7
STATE: BLOCKED
CURRENT_TASK: P0 Production Persistence Completion — Neon Wiring + Vercel Handoff
RESULT: PARTIAL PASS — actual Neon production project/database/schema and persistence/CAS/idempotency store semantics are verified; PR #44 is merged and main CI is GREEN. Vercel production wiring and deployed browser/next_game E2E remain BLOCKED because the connected Vercel account exposes no team/project.

## LAST_COMPLETED
- Started this task from `main@1982d39fa67eef79b8ed118629bb66c88fc15dcd` and re-audited the merged PR #43 production persistence/wiring code.
- Connected Neon was inspected. Organization `건우` existed but contained no project, so a new production project `baseball-player-sim-production` was created.
- Created/confirmed Neon PostgreSQL 16 production resources: default branch `production`, database `baseball_sim`, role `baseball_sim_app`, region `aws-us-east-2`.
- Confirmed Neon provides both direct and pooled endpoints. The application connection uses the pooled endpoint with SSL required; migration/admin work should use a direct/unpooled connection.
- Applied the SessionStore schema to the real Neon production database and introspected both tables, columns, PK/FK constraints, JSONB fields, TIMESTAMPTZ fields, and revision CHECK constraint.
- Created a copy-on-write Neon `p0-validation` branch from production to validate persistence without inserting validation rows into the production branch.
- On the validation branch, stored a session at revision 1, loaded it from a separate Neon invocation, committed revision 2 plus an idempotency record in one transaction, and loaded both again from a later separate invocation.
- Verified a stale revision=1 guarded update affects zero rows after revision 2 is committed, leaving the durable state unchanged.
- Verified the stored idempotency fingerprint, committed response payload, and resulting revision survive later invocations; a different fingerprint is detected as conflicting reuse.
- Existing `PostgresSessionStore` tests remain the executable application-layer concurrency proof against real PostgreSQL 16: same-session/same-revision concurrent requests execute exactly one mutator and same-key concurrent retries execute once plus one replay.
- Added canonical migration `migrations/0001_session_store.sql`, migration contract test `tests/test_postgres_migration.py`, and secret-free `docs/p0-production-neon-vercel-handoff.md`.
- Added the migration test to the existing PostgreSQL-backed external-store CI gate.
- Feature run #651 completed GREEN across migration/external-store tests, Vercel entrypoint, API vertical slice, related production tests, full Python suite, Auto career smoke, Balance smoke, draft calibration, web build, and web tests.
- PR #44 `P0: Codify Neon production schema and Vercel handoff` passed PR run #652 GREEN and merged as `4a07dd8170ac7336e849bc6a4b0d124bf10dd5a7`.
- Post-merge main run #653 completed GREEN across the same required gates.

## CURRENT_FINDINGS
- Production persistence architecture is Browser -> same-origin Vercel -> FastAPI `/api/v1/*` -> authoritative `CareerEngine` -> `ProductionAdvanceService` -> `PostgresSessionStore` -> Neon PostgreSQL.
- Provider-specific persistence remains behind the existing `SessionStore` protocol; gameplay/domain/presentation layers are not coupled to Neon.
- Canonical production schema is now source-controlled in `migrations/0001_session_store.sql` and matches the schema actually applied to the Neon production database.
- `baseball_sim_sessions` persists opaque `session_id`, canonical serialized save payload as JSONB, revision, save_version, and updated_at. `session_id` is unique via the primary key and revision is constrained to >= 1.
- `baseball_sim_idempotency` persists `(session_id, idempotency_key)` composite primary key, request fingerprint, committed response JSONB, resulting revision, created_at, and FK cascade to the session.
- `PostgresSessionStore.mutate()` uses one PostgreSQL transaction, locks the session row with `SELECT ... FOR UPDATE`, checks durable idempotency under the lock, compares expected revision, executes the authoritative mutator only for the winning revision, writes the full save with revision+1, inserts the replay record, and commits atomically.
- Real Neon persistence was verified across separate connector/database invocations. Actual simultaneous two-connection race execution was validated at the same adapter contract against real PostgreSQL 16 in CI rather than through the Neon connector itself.
- Production adapter selection remains fail-closed. On Vercel/production, absence of an external database URL yields `SAVE_FAILED`; SQLite/local filesystem is not accepted as production authority.
- Simplest Vercel production env contract is `DATABASE_URL` only. Its value must be the secret Neon pooled connection string for the `production` branch / `baseball_sim` database / `baseball_sim_app` role. The secret must remain outside Git, PRs, status files, and logs.
- `APP_ENV=production` is not required on Vercel because Vercel supplies the `VERCEL` runtime environment signal used by current code. `BASEBALL_SIM_PRODUCTION=1` remains available for non-Vercel production-like execution/tests but is not required in the Vercel project.
- `SESSION_COOKIE_SECURE` is not required because the existing production runtime policy already sets Secure + HttpOnly + SameSite=Lax for the opaque anonymous session cookie.
- The Vercel project must use the repository root rather than `web/`; the root FastAPI entrypoint builds/serves the Vite frontend in the same-origin topology.
- Connected Vercel access still returns no teams/projects. Therefore the actual production project cannot be inspected/configured, `DATABASE_URL` cannot be injected, a production redeploy cannot be initiated, and deployed runtime/browser validation cannot be completed from this connection.
- No gameplay, hitting/pitching probability, rating, growth, injury, event, pitcher usage, KBO rule, stat formula, UI redesign, new screen, or advance breadth behavior was changed.

## BLOCKERS
- Vercel project/account authorization: the connected Vercel capability exposes zero teams/projects, so the project owning the production domain cannot currently be configured or deployed here.
- Because Vercel production environment access is unavailable, the already-created Neon pooled production connection cannot yet be injected as project-scope `DATABASE_URL` and deployed runtime evidence cannot be collected.

## OPEN_ITEMS
- Authorize/connect the Vercel account/team/project that owns the intended production deployment.
- Set Vercel Project Settings -> Environment Variables -> `DATABASE_URL` to the secret Neon pooled production connection string with **Production** scope only (unless Preview is intentionally given its own isolated database later).
- Confirm Vercel Root Directory is repository root.
- Create a new production deployment/redeploy after the environment variable is added or changed.
- Run `python tools/deployed_p0_smoke.py https://<production-domain>` against the deployed main build.
- Verify in a real browser: session/create/state, one next_game, revision +1, game/stat change, refresh persistence, later/separate serverless invocation persistence, idempotent retry with zero duplicate game, stale expected_revision 409, normal API error schema, backend DTO rendering, and no MockGameDataProvider authority.
- Keep the `p0-validation` Neon branch until validation cleanup is explicitly requested; do not delete it implicitly.

## DEPENDENCIES
- Neon production PostgreSQL resource: READY and schema applied.
- Vercel account/project authorization for production deployment: BLOCKED.
- 06 Web UI may continue relying on relative `/api/v1`; no frontend domain simulation change is required.

## NEXT_ACTION
- Restore Vercel project authorization, inject the existing Neon pooled production connection as `DATABASE_URL` in Production scope, confirm repository-root deployment, redeploy current main, then execute the deployed HTTP/browser/cold-start smoke. Only after those runtime checks pass may `VERCEL_PRODUCTION_WIRING`, `DEPLOYED_NEXT_GAME_E2E`, and `P0_WEB_PYTHON_PRODUCTION_COMPLETE` be marked PASS.

## RELATED_PRS
- #44 merged: Neon production schema + Vercel handoff
- #43 merged: P0 Vercel production persistence wiring code
- #42 merged: P0 Web ↔ Python local/CI vertical slice
- #37 merged: production presentation contract/provider foundation

## RELATED_BRANCHES
- main
- feature/p0-neon-production-handoff
- feature/p0-production-deployment
- feature/p0-web-python-vertical-slice
- Neon branch `production`
- Neon branch `p0-validation`

## GATES
- NEON_PRODUCTION_PROJECT = PASS
- NEON_PRODUCTION_DATABASE = PASS
- NEON_PRODUCTION_SCHEMA = PASS
- NEON_PERSISTENCE_VALIDATION = PASS
- POSTGRES_SESSION_STORE_ADAPTER = PASS
- POSTGRES_MIGRATION_CONTRACT = PASS
- POSTGRES_REAL_SERVICE_TESTS = PASS
- POSTGRES_RESTART_RECOVERY = PASS
- POSTGRES_CAS_RACE = PASS
- POSTGRES_CONCURRENT_IDEMPOTENCY = PASS
- PRODUCTION_FAIL_CLOSED = PASS
- PRODUCTION_SECURE_SESSION_COOKIE = PASS
- EXTERNAL_DURABLE_STORE = PASS
- PRODUCTION_SESSION_PERSISTENCE = PASS
- PRODUCTION_REVISION_CAS = PASS
- PRODUCTION_IDEMPOTENCY = PASS
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
- PR44_CI = PASS
- PR44_MERGED = PASS
- MAIN_CI_GREEN = PASS
- MOCK_NOT_PRODUCTION_AUTHORITY = PASS
- VERCEL_PRODUCTION_WIRING = BLOCKED
- DEPLOYED_NEXT_GAME_E2E = OPEN
- DEPLOYED_BROWSER_E2E = OPEN
- COLD_START_PERSISTENCE = OPEN
- P0_WEB_PYTHON_PRODUCTION_COMPLETE = OPEN
