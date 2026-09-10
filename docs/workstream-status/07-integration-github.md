# 07 - Integration & GitHub

WORKSTREAM: 07 - Integration & GitHub
UPDATED_AT: 2026-09-11
SOURCE_OF_TRUTH: main@4510578409a2107bfa3486d4a78292432294f9c0
STATE: BLOCKED
CURRENT_TASK: P0 Final Production Deployment Verification
RESULT: BLOCKED — Vercel connector access is working, but the current Production deployment is still the stale failed deployment `dpl_E8HQViPuLgzzbuvgASB4KmtEMAfg`. It is `ERROR`, points to Git SHA `8a6f48c9ab833ab5412cc246e31b6b6c09275296`, and therefore does not contain PR #45 merge `0a9ad6d3aac51e3d7b4eafa8befe2fb449bee1a2`. Build inspection reconfirmed the old pre-fix `No project table found in pyproject.toml` failure. `GET /api/v1/session` returned HTTP 302 Vercel SSO redirect rather than FastAPI JSON. A connector production redeploy was attempted, but the available deploy action requires an explicit file bundle and cannot redeploy the existing Git-linked project/commit directly in this session; no new deployment was created. Per gate policy, full production smoke was not run.

## LAST_COMPLETED
- Task-start main verified: `4510578409a2107bfa3486d4a78292432294f9c0`.
- Re-read this workstream status before deployment probing.
- Vercel connector access succeeded for the `ogw` team and `baseball-player-sim` project.
- Latest Production deployment verified as `dpl_E8HQViPuLgzzbuvgASB4KmtEMAfg`, target `production`, state/readyState `ERROR`.
- Deployment Git SHA verified as `8a6f48c9ab833ab5412cc246e31b6b6c09275296`.
- PR #45 merge remains `0a9ad6d3aac51e3d7b4eafa8befe2fb449bee1a2`; deployed SHA is older and does not contain it.
- Deployment details and build logs reconfirmed failure at Vercel buildStep: `uv lock` failed because the stale deployed `pyproject.toml` had no `[project]` table.
- `GET https://baseball-player-634by6u9s-ogw2.vercel.app/api/v1/session` returned HTTP 302 to Vercel SSO, not application JSON.
- Attempted connector production deployment. The exposed deployment operation requires `target`, `name`, and a non-empty `files` bundle; with no supported Git-source/redeploy input, the existing linked repository cannot be safely redeployed from current main through this connector action.
- Because FIRST GATE failed, career/state/next_game/Neon/idempotency/stale-revision/cold-start/browser smoke was intentionally not executed.
- No application code, gameplay formulas, ratings, growth, injury, events, pitcher usage, KBO rules, stat formulas, UI, Neon schema, or unrelated cleanup was changed.

## CURRENT_FINDINGS
- `VERCEL_CONNECTOR_ACCESS = PASS` for read/inspection operations.
- `VERCEL_CURRENT_MAIN_BUILD = FAIL`: latest Production remains `ERROR`.
- `VERCEL_DEPLOYED_SHA_VERIFIED = FAIL`: deployed SHA `8a6f48c9...` predates PR #45 and current main.
- `PRODUCTION_API_SESSION_ROUTE = FAIL`: current deployment did not return FastAPI session JSON.
- Build result is FAIL on stale code with the exact packaging error PR #45 fixed in GitHub main.
- This does not invalidate PR #45 CI/packaging PASS; it shows the fixed commit has not yet been evidenced in Vercel Production.
- The connector's available deploy action is not sufficient to redeploy the Git-linked project from a selected Git SHA without supplying a full file bundle.
- Full runtime verification remains OPEN until a new Production deployment containing PR #45 reaches READY and serves the session route.

## BLOCKERS
- No Production deployment containing PR #45/current main exists yet in Vercel evidence.
- Latest Production deployment is stale and failed.
- Available connector deployment action cannot directly redeploy the existing Git-linked project from current main/commit in this session.
- Session route on the stale failed deployment returns Vercel auth redirect rather than application response.

## OPEN_ITEMS
- Trigger a new `baseball-player-sim` Production deployment from current main (or later main successor containing PR #45) through Vercel UI/Git deployment or another supported redeploy path.
- Verify deployment reaches `READY` and inspect its build logs/Python function.
- Verify deployed SHA contains `0a9ad6d3aac51e3d7b4eafa8befe2fb449bee1a2`.
- Verify Production `GET /api/v1/session` returns the expected FastAPI response.
- Only then execute: career create, GET state, one `next_game`, revision +1, game/stat change, refresh/reconnect persistence, Neon session/idempotency row evidence, same-key replay without duplicate mutation, stale expected_revision 409, separate invocation/cold-start persistence, browser E2E, and runtime production-authority check.

## DEPENDENCIES
- Neon production PostgreSQL/schema: READY and previously validated.
- PR #45 packaging fix: merged and GitHub CI validated.
- Vercel connector read/inspection access: PASS.
- A supported production redeploy trigger for the Git-linked project: BLOCKED in this connector session.

## NEXT_ACTION
- In Vercel, trigger a Production redeploy/new deployment for current `main` on project `baseball-player-sim` (not the stale `8a6f48c9...` deployment). After it appears, re-run only the FIRST GATE: `READY`, deployed SHA contains PR #45, and `/api/v1/session` returns FastAPI JSON. If all pass, immediately continue with the existing full production smoke. Do not expose `DATABASE_URL`, cookies, or secrets.

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
- VERCEL_CONNECTOR_ACCESS = PASS
- VERCEL_REDEPLOY_ACTION = BLOCKED
- VERCEL_CURRENT_MAIN_BUILD = FAIL
- VERCEL_DEPLOYED_SHA_VERIFIED = FAIL
- PRODUCTION_API_SESSION_ROUTE = FAIL
- VERCEL_DATABASE_URL_PRODUCTION_SCOPE_VERIFIED = OPEN
- VERCEL_PRODUCTION_WIRING = OPEN
- PRODUCTION_SESSION_PERSISTENCE = OPEN
- PRODUCTION_REVISION_CAS = OPEN
- PRODUCTION_IDEMPOTENCY = OPEN
- DEPLOYED_NEXT_GAME_E2E = OPEN
- DEPLOYED_BROWSER_E2E = OPEN
- COLD_START_PERSISTENCE = OPEN
- MOCK_NOT_PRODUCTION_AUTHORITY = OPEN
- P0_WEB_PYTHON_PRODUCTION_COMPLETE = OPEN
