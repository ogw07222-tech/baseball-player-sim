# 07 - Integration & GitHub

WORKSTREAM: 07 - Integration & GitHub
UPDATED_AT: 2026-09-11
SOURCE_OF_TRUTH: main@6ffaf0247fa6c7b9bfd268897aec38f34d79bc8c
STATE: BLOCKED
CURRENT_TASK: Final Vercel Production Runtime Verification
RESULT: BLOCKED — task-start main is `6ffaf0247fa6c7b9bfd268897aec38f34d79bc8c`, a status-only successor of PR #45 merge `0a9ad6d3aac51e3d7b4eafa8befe2fb449bee1a2`. Vercel tool discovery succeeded, but the first required live call (`list_teams`) immediately disabled the connector. Per gate policy, no deployment status, deployed SHA, or `/api/v1/session` response is inferred from GitHub CI or historical Vercel evidence. Runtime gates remain OPEN.

## LAST_COMPLETED
- Re-read task-start main: `6ffaf0247fa6c7b9bfd268897aec38f34d79bc8c`; parent is PR #45 merge `0a9ad6d3aac51e3d7b4eafa8befe2fb449bee1a2`.
- Re-read this workstream status before probing Vercel.
- Confirmed previously completed code/CI gates remain PASS: PEP 621 `[project]`, `uv lock --dry-run --python 3.12`, FastAPI entrypoint/import, API integration/full Python suite, and web build/tests.
- Attempted the required first Vercel live probe. Tool discovery exposed `list_teams`, `list_projects`, `list_deployments`, deployment inspection/build logs, and protected URL fetch tools.
- The first actual `list_teams` call returned that the Vercel tool had been disabled. No further Vercel calls were made.
- Because first-gate evidence was not obtained, full production smoke was not executed.
- No application code, gameplay, ratings, growth, injury, events, KBO rules, stat formulas, Neon schema, SessionStore semantics, UI, or advance breadth was changed.

## CURRENT_FINDINGS
- `VERCEL_PYTHON_PACKAGING` and `VERCEL_UV_LOCK_CI` remain PASS based on PR #45/GitHub Actions evidence.
- Connector failure is an access/tooling blocker, not evidence that the production deployment itself failed.
- Current Vercel deployment status, deployed Git SHA, and production `/api/v1/session` response are all unknown in this run.
- Therefore `VERCEL_CURRENT_MAIN_BUILD`, `VERCEL_DEPLOYED_SHA_VERIFIED`, and `PRODUCTION_API_SESSION_ROUTE` remain OPEN.
- Full create/state/next_game/persistence/idempotency/stale-409/cold-start/browser runtime verification must not run or be marked PASS until the first three production gates are evidenced.

## BLOCKERS
- Vercel connector becomes unavailable on the first live API call after successful tool discovery.

## OPEN_ITEMS
- Manual or restored-connector evidence for latest Production deployment status = READY.
- Evidence that deployed SHA is `0a9ad6d3aac51e3d7b4eafa8befe2fb449bee1a2` or later main containing it (including status-only successors such as `6ffaf024...`).
- Production `GET /api/v1/session` successful response.
- Only after those three pass: career create, state, next_game, revision +1, refresh persistence, Neon session/idempotency rows, same-key replay, stale 409, separate invocation/cold-start persistence, and browser E2E.

## DEPENDENCIES
- Neon production PostgreSQL/schema: READY and previously validated.
- PR #45 packaging fix: merged and GitHub CI validated.
- Vercel connector live access: BLOCKED in this run.

## NEXT_ACTION
- Use the existing manual verification fallback or restored connector. First collect exactly: Production deployment READY, deployed SHA, and `/api/v1/session` response. Do not expose `DATABASE_URL` or cookie values. If all three pass, resume the existing production smoke without feature/refactor work.

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
