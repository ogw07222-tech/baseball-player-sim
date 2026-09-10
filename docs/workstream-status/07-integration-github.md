# 07 - Integration & GitHub

WORKSTREAM: 07 - Integration & GitHub
UPDATED_AT: 2026-09-11
SOURCE_OF_TRUTH: main@6649f96b27d0171000e4a9251188e10492b866f3
STATE: BLOCKED
CURRENT_TASK: Final Vercel Production Runtime Verification
RESULT: BLOCKED — Vercel tool discovery succeeded, but the first required live call (`list_teams`) immediately disabled the connector again. Per verification policy, no current Production deployment status, deployed SHA, or `/api/v1/session` result is inferred from GitHub CI or historical deployment evidence. Full production smoke was not run and all runtime gates remain OPEN.

## LAST_COMPLETED
- Re-read task-start main: `6649f96b27d0171000e4a9251188e10492b866f3`.
- Confirmed PR #45 packaging fix remains in ancestry through merge commit `0a9ad6d3aac51e3d7b4eafa8befe2fb449bee1a2`.
- Re-read the current 07 workstream status before probing Vercel.
- Confirmed code/CI gates remain PASS: PEP 621 `[project]`, `uv lock --dry-run --python 3.12`, FastAPI entrypoint/import, API/full Python suite, and web build/tests.
- Vercel tool discovery exposed `list_teams`, `list_projects`, `list_deployments`, deployment inspection/build logs, and protected URL fetch tools.
- The first actual `list_teams` call returned that the Vercel tool had been disabled. No further Vercel calls were made.
- Because the first gate was not evidenced, full production smoke was not executed.
- No application code, gameplay, ratings, growth, injury, events, KBO rules, stat formulas, Neon schema, SessionStore semantics, UI, or advance breadth was changed.

## CURRENT_FINDINGS
- `VERCEL_PYTHON_PACKAGING` and `VERCEL_UV_LOCK_CI` remain PASS based on PR #45/GitHub Actions evidence.
- Connector failure is an access/tooling blocker, not evidence that the production deployment itself failed.
- Current Vercel Production deployment status, deployed Git SHA, and production `/api/v1/session` response are unknown in this run.
- Therefore `VERCEL_CURRENT_MAIN_BUILD`, `VERCEL_DEPLOYED_SHA_VERIFIED`, and `PRODUCTION_API_SESSION_ROUTE` remain OPEN.
- GitHub CI PASS is not used as a substitute for Vercel runtime PASS.
- Full create/state/next_game/persistence/idempotency/stale-409/cold-start/browser verification must remain OPEN until the first three production gates are evidenced.

## BLOCKERS
- Vercel connector repeatedly becomes unavailable on the first live API call after successful tool discovery.

## OPEN_ITEMS
- Obtain current Production deployment status = READY via restored connector or manual Vercel UI evidence.
- Verify deployed SHA is `0a9ad6d3aac51e3d7b4eafa8befe2fb449bee1a2` or a later main successor containing it.
- Verify Production `GET /api/v1/session` returns the expected API response.
- Only after those three pass: career create, state, next_game, revision +1, refresh persistence, Neon session/idempotency rows, same-key replay, stale 409, separate invocation/cold-start persistence, and browser E2E.

## DEPENDENCIES
- Neon production PostgreSQL/schema: READY and previously validated.
- PR #45 packaging fix: merged and GitHub CI validated.
- Vercel connector live access: BLOCKED in this run.

## NEXT_ACTION
- Use manual verification fallback or restored connector. First collect exactly: Production deployment READY, deployed SHA, and `/api/v1/session` response. Do not expose `DATABASE_URL` or cookie values. If all three pass, resume the existing production smoke without feature/refactor work.

## RELATED_PRS
- #45 merged: minimal Vercel Python PEP 621/uv packaging fix
- #44 merged: Neon production schema + Vercel handoff
- #43 merged: P0 Vercel production persistence wiring code
- #42 merged: P0 Web ↔ Python local/CI vertical slice
- #37 merged: production presentation contract/provider foundation

## RELATED_BRANCHES
- main
- Neon branch `production`
- Neon branch `p0-validation`

## GATES
- NEON_PRODUCTION_PROJECT = PASS
- NEON_PRODUCTION_DATABASE = PASS
- NEON_PRODUCTION_SCHEMA = PASS
- EXTERNAL_DURABLE_STORE = PASS
- POSTGRES_SESSION_STORE_ADAPTER = PASS
- POSTGRES_MIGRATION_CONTRACT = PASS
- POSTGRES_REAL_SERVICE_TESTS = PASS
- PRODUCTION_FAIL_CLOSED = PASS
- PRODUCTION_SECURE_SESSION_COOKIE = PASS
- MOCK_NOT_PRODUCTION_AUTHORITY_CODE = PASS
- VERCEL_PYTHON_PACKAGING = PASS
- VERCEL_PYPROJECT_DEPENDENCY_CONTRACT = PASS
- VERCEL_UV_LOCK_CI = PASS
- PR45_CI = PASS
- PR45_MERGED = PASS
- VERCEL_CONNECTOR_ACCESS = BLOCKED
- VERCEL_CURRENT_MAIN_BUILD = OPEN
- VERCEL_DEPLOYED_SHA_VERIFIED = OPEN
- PRODUCTION_API_SESSION_ROUTE = OPEN
- VERCEL_DATABASE_URL_PRODUCTION_SCOPE_VERIFIED = OPEN
- VERCEL_PRODUCTION_WIRING = OPEN
- PRODUCTION_SESSION_PERSISTENCE = OPEN
- PRODUCTION_REVISION_CAS = OPEN
- PRODUCTION_IDEMPOTENCY = OPEN
- DEPLOYED_NEXT_GAME_E2E = OPEN
- DEPLOYED_BROWSER_E2E = OPEN
- COLD_START_PERSISTENCE = OPEN
- P0_WEB_PYTHON_PRODUCTION_COMPLETE = OPEN
