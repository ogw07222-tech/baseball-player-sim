# 07 - Integration & GitHub

WORKSTREAM: 07 - Integration & GitHub
UPDATED_AT: 2026-09-11
SOURCE_OF_TRUTH: main@6380ab6535df44c0f522cf6d579e740732f735d1
STATE: BLOCKED
CURRENT_TASK: Fix Confirmed Vercel npm ci Lockfile Failure
RESULT: PARTIAL — the confirmed Vercel `npm --prefix web ci` blocker is fixed in GitHub main by PR #48, which adds the missing `web/package-lock.json` without changing dependency declarations or re-enabling Vercel Git auto-deploy. Exact `npm ci`, production web build, web tests, Python packaging, FastAPI entrypoint, API vertical slice, related production integration tests, full Python unit tests, auto-career smoke, balance smoke, and draft calibration all passed in validation CI. A one-time current-main Production deployment could not be created through the available Vercel connector because its exposed deployment action still does not provide a safe Git-SHA/manual-production source selector; no Preview or stale deployment was reused.

## LAST_COMPLETED
- Task-start main SHA: `03d41dac5bf7796a6c1f6caafd02892deee06826`.
- Confirmed no canonical JS lockfile existed in task-start main; `web/package.json` and npm commands are the existing frontend package-management contract.
- Generated `web/package-lock.json` from the unchanged `web/package.json` using Node 22 / npm 10; lockfileVersion is 3 and resolved package versions/integrities are pinned.
- Validation CI ran exact `npm ci`, `npm run build`, and `npm test`: all PASS; 3 Vitest files / 19 tests passed.
- Python validation on the same PR passed: dependency contract + `uv lock --dry-run --python 3.12`, compile, external Postgres tests, FastAPI entrypoint smoke, API vertical slice, related production integration tests, full unit suite, auto-career smoke, balance smoke, and high-school/draft calibration.
- Temporary workflow/validation-only edits were fully reverted before merge. Final PR diff contained only `web/package-lock.json` (+2388 lines).
- PR #48 `build: add web npm lockfile` merged to main with merge SHA `6380ab6535df44c0f522cf6d579e740732f735d1`.
- Verified `web/package-lock.json` exists on main.
- Verified root `vercel.json` still has `git.deploymentEnabled: false`; automatic Vercel Git deployments remain OFF.
- Verified no Vercel deployment was created after the PR #48 merge timestamp.
- No gameplay, UI, ratings, growth, events, Neon schema, SessionStore semantics, or unrelated application/config changes were made.

## CURRENT_FINDINGS
- CONFIRMED_ROOT_CAUSE = fixed: Vercel build command uses `npm --prefix web ci`, which previously had no `web/package-lock.json`.
- CANONICAL_JS_PACKAGE_MANAGER = npm.
- WEB_NPM_LOCKFILE = PASS.
- WEB_NPM_CI = PASS.
- WEB_BUILD = PASS.
- WEB_TESTS = PASS.
- PYTHON_REGRESSION = PASS.
- VERCEL_GIT_AUTO_DEPLOY = OFF.
- Current-main Production runtime remains NOT VERIFIED because no new manual Production deployment of the merged lockfile fix exists yet.

## HISTORICAL
- STALE_PRODUCTION_DEPLOYMENT = FAIL
- STALE_DEPLOYMENT_ID = `dpl_E8HQViPuLgzzbuvgASB4KmtEMAfg`
- STALE_DEPLOYMENT_SHA = `8a6f48c9ab833ab5412cc246e31b6b6c09275296`
- Earlier current-main deployment before PR #48 also failed at `npm ci` because the lockfile did not yet exist; this exact blocker is now fixed in main and CI-validated.

## BLOCKERS
- The current connector surface does not expose a safe one-time Production deployment from the linked Git repository/current-main SHA. Its deployment action cannot be used to select the current Git SHA without supplying a file bundle, so no manual deployment was fabricated.

## OPEN_ITEMS
- Trigger exactly one Production deployment from current main through a supported Vercel UI/CLI/API Git-source path while keeping auto-deploy OFF.
- FIRST GATE: require deployment `READY`, deployed SHA contains PR #48 lockfile fix and PR #45, and `GET /api/v1/session` returns FastAPI JSON.
- Only if FIRST GATE passes, continue career create/state/next_game/revision/persistence/Neon/idempotency/stale-409/cold-start/browser production smoke.

## NEXT_ACTION
- Manually deploy current main to Vercel project `baseball-player-sim` without changing `git.deploymentEnabled: false`. Once the new Production deployment appears, run FIRST GATE only before any full smoke.

## RELATED_PRS
- #48 merged: add reproducible web npm lockfile
- #47 merged: restore Vercel Git auto-deploy OFF
- #46 merged: temporary Git deployment trigger restoration
- #45 merged: Vercel Python packaging fix
- #44 merged: Neon production schema + Vercel handoff
- #43 merged: P0 production persistence wiring
- #42 merged: Web ↔ Python vertical slice

## GATES
- PR45_MERGED = PASS
- WEB_NPM_LOCKFILE = PASS
- WEB_NPM_CI = PASS
- WEB_BUILD = PASS
- WEB_TESTS = PASS
- PYTHON_REGRESSION = PASS
- VERCEL_GIT_AUTO_DEPLOY = OFF
- ONE_TIME_MANUAL_PRODUCTION_DEPLOYMENT = BLOCKED
- VERCEL_CURRENT_MAIN_BUILD = OPEN
- VERCEL_DEPLOYED_SHA_VERIFIED = OPEN
- PRODUCTION_API_SESSION_ROUTE = OPEN
- VERCEL_PRODUCTION_WIRING = OPEN
- PRODUCTION_SESSION_PERSISTENCE = OPEN
- PRODUCTION_REVISION_CAS = OPEN
- PRODUCTION_IDEMPOTENCY = OPEN
- DEPLOYED_NEXT_GAME_E2E = OPEN
- DEPLOYED_BROWSER_E2E = OPEN
- COLD_START_PERSISTENCE = OPEN
- MOCK_NOT_PRODUCTION_AUTHORITY = OPEN
- P0_WEB_PYTHON_PRODUCTION_COMPLETE = OPEN
