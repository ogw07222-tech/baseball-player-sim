# 07 - Integration & GitHub

WORKSTREAM: 07 - Integration & GitHub
UPDATED_AT: 2026-09-11
SOURCE_OF_TRUTH: main@20368ed279702c316b03d8c11a5113d331e1b7ea
STATE: WAITING
CURRENT_TASK: Correct Stale-Deployment Gate Semantics + Wait for New Production Deployment
RESULT: WAITING — current GitHub main contains PR #45, but no new Vercel Production deployment sourced from current main exists yet. The only visible Production deployment remains historical stale deployment `dpl_E8HQViPuLgzzbuvgASB4KmtEMAfg` at `8a6f48c9ab833ab5412cc246e31b6b6c09275296`. Its historical failure is preserved separately and is not reused as a current-main production FAIL. Current-main Vercel build/SHA/session-route gates therefore remain OPEN until a new Production deployment appears.

## LAST_COMPLETED
- Verified latest main at task start: `20368ed279702c316b03d8c11a5113d331e1b7ea`.
- Re-read this workstream status.
- Queried Vercel Production deployments for `baseball-player-sim` without re-running smoke against the stale deployment.
- Confirmed no Production deployment newer than historical `dpl_E8HQViPuLgzzbuvgASB4KmtEMAfg` exists yet.
- Corrected gate semantics so historical stale deployment failures are separated from current-main production verification.
- No code, config, feature, refactor, gameplay, ratings, growth, injury, events, pitcher usage, KBO rules, stat formulas, UI, or Neon schema changes were made.

## CURRENT_FINDINGS
- Latest GitHub main is `20368ed279702c316b03d8c11a5113d331e1b7ea` and contains PR #45 merge `0a9ad6d3aac51e3d7b4eafa8befe2fb449bee1a2` in its ancestry.
- Vercel connector read/inspection access is available.
- No new current-main Production deployment exists yet.
- Therefore current-main Production build, deployed-SHA verification, and `/api/v1/session` runtime status are NOT VERIFIED and remain OPEN.
- Historical stale deployment failure remains valid historical evidence only.
- The old `No project table found in pyproject.toml` error belongs to stale pre-PR45 deployment evidence and must not be interpreted as a current-main build failure.

## HISTORICAL
- STALE_PRODUCTION_DEPLOYMENT = FAIL
- STALE_DEPLOYMENT_ID = `dpl_E8HQViPuLgzzbuvgASB4KmtEMAfg`
- STALE_DEPLOYMENT_SHA = `8a6f48c9ab833ab5412cc246e31b6b6c09275296`
- STALE_DEPLOYMENT_PACKAGING = FAIL
- Historical failure reason: pre-PR45 packaging metadata lacked the PEP 621 `[project]` table.

## BLOCKERS
- No Production deployment sourced from current main (or later main successor containing PR #45) has appeared yet.

## OPEN_ITEMS
- Detect a new `baseball-player-sim` Production deployment newer than the historical stale deployment.
- Run FIRST GATE only: deployment `READY`, deployed SHA contains PR #45, and `GET /api/v1/session` returns FastAPI JSON.
- Only if all three pass, execute full production smoke: career create, GET state, one `next_game`, revision +1, refresh/reconnect persistence, Neon session row, Neon idempotency row, same-key replay without duplicate mutation, stale expected_revision 409, separate invocation/cold-start persistence, browser E2E, and production MockGameDataProvider authority absence.

## DEPENDENCIES
- Neon production PostgreSQL/schema: READY and previously validated.
- PR #45 packaging fix: merged and GitHub CI validated.
- Vercel connector read/inspection access: PASS.
- New current-main Production deployment: PENDING.

## NEXT_ACTION
- Wait for/detect a new Production deployment sourced from current main. Do not retest historical `dpl_E8HQViPuLgzzbuvgASB4KmtEMAfg`. When a new deployment appears, run only the FIRST GATE. Proceed to full smoke only if all three FIRST GATE checks pass.

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
- MOCK_NOT_PRODUCTION_AUTHORITY = OPEN
- P0_WEB_PYTHON_PRODUCTION_COMPLETE = OPEN
