# 07 - Integration & GitHub

WORKSTREAM: 07 - Integration & GitHub
UPDATED_AT: 2026-09-11
SOURCE_OF_TRUTH: `main` observed at `d6b8d86f4dd1f523ba5e1d09d84ad82d6a37cf55` before this status-sync commit
STATE: BLOCKED
CURRENT_TASK: Vercel Production Gate
RESULT: PRE-FIX PRODUCTION DEPLOYMENT FAILS FIRST GATE / FIX MERGED BUT NOT YET DEPLOYED

## CURRENT_FINDINGS
- Newer-than-historical Production deployment exists: `dpl_AbPPVvPXDPAgcbYUvJsGBRM2Ti7Q`.
- Deployment state: `READY`.
- Deployed Git SHA: `51e7e64d6c7bb44ba99cbe4771da8985e8450546`.
- That deployed SHA is later than PR #45 merge `0a9ad6d3aac51e3d7b4eafa8befe2fb449bee1a2` and contains the PR #45 Python packaging fix; it also contains the PR #48 `web/package-lock.json` fix.
- `GET /api/v1/session`: FAIL. Production alias returns HTTP 500 with `FUNCTION_INVOCATION_FAILED`; therefore the full production smoke was intentionally not run.
- Runtime traceback root cause: Vercel directly loads `src/api/app.py`; `app.py` imports `.store`; package initialization executes `src/api/__init__.py`, whose eager `from .app import app, create_app` re-imports the partially initialized module and raises `ImportError: cannot import name 'app' from 'src.api.app'`.
- Classification: A — FastAPI/module import failure caused by Vercel direct-module loading + eager package re-export circularity.
- This crash occurs before endpoint execution and before `_external_database_url()` / `_default_store()` can prove whether `DATABASE_URL` is visible at runtime. `DATABASE_URL_VISIBLE_IN_PRODUCTION_RUNTIME = OPEN`; this is not evidence that it is missing.
- Minimum fix is merged in PR #49 as merge SHA `13c7976fdae227b10f20d7130f6f7e176eb579e3`: lazy exports in `src/api/__init__.py` plus a Vercel-style direct-loader regression test.
- PR #49 CI passed, including the direct-loader regression, API/durable-store tests, full Python suite, web tests, and production integration smokes.
- Current main observed after PR #49: `d6b8d86f4dd1f523ba5e1d09d84ad82d6a37cf55`.
- No Production deployment newer than `dpl_AbPPVvPXDPAgcbYUvJsGBRM2Ti7Q` was observed, so no Production deployment containing PR #49/current main exists yet.
- `git.deploymentEnabled=false` remains preserved.

## FIRST GATES
- NEW_PRODUCTION_DEPLOYMENT_AFTER_HISTORICAL_STALE = PASS
- DEPLOYMENT_READY = PASS
- DEPLOYED_SHA_CONTAINS_PR45 = PASS
- GET_API_V1_SESSION_FASTAPI_JSON = FAIL
- FULL_PRODUCTION_SMOKE = NOT RUN by gate policy

## BLOCKER
A Production redeploy containing PR #49/current main is still required. The currently observed Production deployment is READY but remains on the pre-fix SHA and crashes during Python module import.

## NEXT_ACTION
Create one Production deployment from current main while keeping Git auto-deploy disabled. On that deployment, verify only these first: READY, deployed SHA contains PR #49/PR #45, and `GET /api/v1/session` returns actual FastAPI JSON. Only if all pass, continue career create/state/next_game/revision/idempotency/stale-revision/Neon persistence/cold-start/browser E2E/MockGameDataProvider authority checks.

## GATES
- PR45_MERGED = PASS
- PR48_LOCKFILE_FIX_MERGED = PASS
- PR49_RUNTIME_IMPORT_FIX_MERGED = PASS
- VERCEL_GIT_AUTO_DEPLOY = OFF
- VERCEL_RUNTIME_ROOT_CAUSE_IDENTIFIED = PASS
- VERCEL_DIRECT_IMPORT_REGRESSION = PASS
- POST_FIX_PRODUCTION_DEPLOYMENT = OPEN
- PRODUCTION_API_SESSION_ROUTE = FAIL on pre-fix deployment
- PRODUCTION_DATABASE_URL_VISIBLE = OPEN
- PRODUCTION_SESSION_PERSISTENCE = OPEN
- PRODUCTION_REVISION_CAS = OPEN
- PRODUCTION_IDEMPOTENCY = OPEN
- DEPLOYED_NEXT_GAME_E2E = OPEN
- DEPLOYED_BROWSER_E2E = OPEN
- COLD_START_PERSISTENCE = OPEN
- MOCK_NOT_PRODUCTION_AUTHORITY = OPEN
- P0_WEB_PYTHON_PRODUCTION_COMPLETE = OPEN
