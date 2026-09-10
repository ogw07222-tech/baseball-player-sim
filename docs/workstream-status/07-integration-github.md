# 07 - Integration & GitHub

WORKSTREAM: 07 - Integration & GitHub
UPDATED_AT: 2026-09-11
VALIDATED_MAIN: `6380ab6535df44c0f522cf6d579e740732f735d1`
STATE: BLOCKED
CURRENT_TASK: Vercel Production Gate
RESULT: FAIL — a Production deployment newer than historical stale deployment `dpl_E8HQViPuLgzzbuvgASB4KmtEMAfg` exists, but the newest Production deployment is `dpl_2sx7gzn8zfTw14sevVEy9UHzdWXf` at Git SHA `80209cba45f684e6bf6603ab5f2dec705c4765a9` and is in Vercel state `ERROR`. Its build cloned main at `80209cb` and failed at `npm --prefix web ci` because that deployed commit did not contain `web/package-lock.json`. The deployed SHA is later than `0a9ad6d3aac51e3d7b4eafa8befe2fb449bee1a2` and therefore contains PR #45, but `/api/v1/session` serves Vercel's "Deployment has failed" HTML rather than FastAPI JSON. FIRST GATE therefore fails and full production smoke was not run.

## LAST_COMPLETED
- PR #48 `build: add web npm lockfile` merged to main with merge SHA `6380ab6535df44c0f522cf6d579e740732f735d1`.
- `web/package-lock.json` is present on current validated main and the lockfile fix passed exact `npm ci`, web build, web tests, Python packaging/uv validation, FastAPI entrypoint, API vertical slice, related production integration tests, full Python unit tests, auto-career smoke, balance smoke, and draft calibration in CI.
- Historical stale Production deployment remains `dpl_E8HQViPuLgzzbuvgASB4KmtEMAfg` / SHA `8a6f48c9ab833ab5412cc246e31b6b6c09275296`; its old runtime/database error is historical only and was not reused as evidence about current main.

## CURRENT_FINDINGS
- NEWER_PRODUCTION_DEPLOYMENT = YES.
- NEWEST_PRODUCTION_DEPLOYMENT = `dpl_2sx7gzn8zfTw14sevVEy9UHzdWXf`.
- NEWEST_PRODUCTION_SHA = `80209cba45f684e6bf6603ab5f2dec705c4765a9`.
- NEWEST_PRODUCTION_STATE = `ERROR`.
- FIRST_GATE_1_DEPLOYMENT_READY = FAIL.
- FIRST_GATE_2_SHA_CONTAINS_PR45 = PASS; Git compare shows `80209cba...` is 9 commits ahead of `0a9ad6d3...` with no divergence.
- FIRST_GATE_3_API_SESSION_FASTAPI_JSON = FAIL; direct fetch returns HTTP 200 with Vercel failure HTML, not the application JSON.
- BUILD_FAILURE = `npm ci` reports no package-lock/shrinkwrap in deployed commit `80209cba...`.
- CURRENT_MAIN_LOCKFILE_FIX = PASS on `6380ab6535df44c0f522cf6d579e740732f735d1`.
- ROOT_CAUSE_CLASSIFICATION = stale/intermediate deployed Git SHA relative to the lockfile fix, not evidence that PR #48 failed.
- CODE_CHANGE_REQUIRED = NO; no new application/code blocker was established beyond deploying a commit that predates PR #48.

## BLOCKERS
- No READY Production deployment currently verifies the PR #48 lockfile fix on Vercel.
- The latest observed Production deployment predates `6380ab6535df44c0f522cf6d579e740732f735d1` and cannot pass the current-main FIRST GATE.

## OPEN_ITEMS
- Create/observe one Production deployment from `6380ab6535df44c0f522cf6d579e740732f735d1` or a later main commit containing PR #48 and PR #45.
- Re-run FIRST GATE: deployment `READY`; deployed SHA includes PR #45 and lockfile fix; `GET /api/v1/session` returns actual FastAPI JSON.
- Only after all FIRST GATE checks pass, run career create, GET state, one `next_game`, revision +1, game/stat mutation, reconnect persistence, Neon session/idempotency rows, same-key replay, stale revision 409, cold-start persistence, browser E2E, and production-authority check excluding `MockGameDataProvider`.

## GATES
- PR45_MERGED = PASS
- PR48_LOCKFILE_FIX_MERGED = PASS
- WEB_NPM_LOCKFILE_CURRENT_MAIN = PASS
- NEWER_PRODUCTION_DEPLOYMENT_FOUND = PASS
- VERCEL_CURRENT_DEPLOYMENT_READY = FAIL
- VERCEL_DEPLOYED_SHA_CONTAINS_PR45 = PASS
- PRODUCTION_API_SESSION_ROUTE = FAIL
- FULL_PRODUCTION_SMOKE = NOT_RUN
- PRODUCTION_SESSION_PERSISTENCE = OPEN
- PRODUCTION_REVISION_CAS = OPEN
- PRODUCTION_IDEMPOTENCY = OPEN
- DEPLOYED_NEXT_GAME_E2E = OPEN
- DEPLOYED_BROWSER_E2E = OPEN
- COLD_START_PERSISTENCE = OPEN
- MOCK_NOT_PRODUCTION_AUTHORITY = OPEN
- P0_WEB_PYTHON_PRODUCTION_COMPLETE = OPEN
