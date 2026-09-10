# 07 - Integration & GitHub

WORKSTREAM: 07 - Integration & GitHub
UPDATED_AT: 2026-09-11
SOURCE_OF_TRUTH: `main@13c7976fdae227b10f20d7130f6f7e176eb579e3`
STATE: BLOCKED
CURRENT_TASK: Diagnose Vercel FUNCTION_INVOCATION_FAILED Runtime Crash
RESULT: ROOT CAUSE FIX MERGED / RUNTIME REDEPLOY BLOCKED — Production deployment `dpl_AbPPVvPXDPAgcbYUvJsGBRM2Ti7Q` is READY at Git SHA `51e7e64d6c7bb44ba99cbe4771da8985e8450546`, but `GET /api/v1/session` returns HTTP 500 `FUNCTION_INVOCATION_FAILED`. Runtime logs prove a Python module-import circularity: Vercel directly loads `src/api/app.py`; `app.py` imports `.store`; initializing package `src.api` executes `src/api/__init__.py`, which eagerly re-imports `.app` and requests `app` before `app.py` reaches `app = create_app()`. PR #49 changes the package export to lazy loading and adds a Vercel-style direct-module-loader regression test. PR #49 merged as `13c7976fdae227b10f20d7130f6f7e176eb579e3`; all CI gates passed. A post-merge Production redeploy could not be created through the currently exposed Vercel connector because its deploy action rejects invocation without hidden/runtime-required `target`, `name`, and full `files` inputs. No new deployment containing PR #49 exists yet, so runtime verification remains OPEN.

## LAST_COMPLETED
- Confirmed newest Production deployment `dpl_AbPPVvPXDPAgcbYUvJsGBRM2Ti7Q` is Vercel state `READY`, target `production`, source `git`, deployed SHA `51e7e64d6c7bb44ba99cbe4771da8985e8450546`.
- Verified deployed SHA contains PR #45 merge `0a9ad6d3aac51e3d7b4eafa8befe2fb449bee1a2` and PR #48 merge `6380ab6535df44c0f522cf6d579e740732f735d1` in ancestry.
- Reproduced target request: `GET /api/v1/session` -> HTTP 500, `x-vercel-error: FUNCTION_INVOCATION_FAILED`.
- Read runtime traceback before changing code. Exact failing chain: `src/api/app.py` line 26 `from .store import ...` -> package init `src/api/__init__.py` line 3 `from .app import app, create_app` -> `ImportError: cannot import name 'app' from 'src.api.app'`; Python process exits status 1.
- Root-cause classification: A — FastAPI/module import failure, specifically Vercel direct-module loading interacting with eager `src.api` re-export and causing a circular import. The failure occurs before endpoint execution and before the production DB selection path can be runtime-verified.
- Changed only `src/api/__init__.py` and `tests/test_python_dependency_contract.py`.
- Added a regression test that directly loads `src/api/app.py` via `importlib.util.spec_from_file_location("src.api.app", ...)`, matching the relevant Vercel loader behavior.
- PR #49 `fix: avoid Vercel direct-import crash` merged as `13c7976fdae227b10f20d7130f6f7e176eb579e3`.
- PR #49 CI PASS: Vercel packaging contract including direct-loader regression, `uv lock --dry-run --python 3.12`, compile, durable-store tests, FastAPI entrypoint, API vertical slice, related production integration tests, full Python suite (302 tests / OK), auto-career smoke, balance smoke, draft calibration, web build/tests.
- Preserved `git.deploymentEnabled=false`; no gameplay, ratings, growth, events, UI redesign, DB schema, SessionStore semantics, or dependency declaration changes.

## CURRENT_FINDINGS
- PRODUCTION_DEPLOYMENT_ID = `dpl_AbPPVvPXDPAgcbYUvJsGBRM2Ti7Q`.
- PRODUCTION_DEPLOYED_SHA = `51e7e64d6c7bb44ba99cbe4771da8985e8450546`.
- PRODUCTION_DEPLOYMENT_STATE = `READY`.
- PRODUCTION_API_SESSION = FAIL on deployed pre-fix SHA with `FUNCTION_INVOCATION_FAILED`.
- VERCEL_RUNTIME_ROOT_CAUSE = confirmed circular import in `src.api` package initialization.
- PR45_IN_DEPLOYED_SHA = PASS.
- PR48_IN_DEPLOYED_SHA = PASS.
- PR49_RUNTIME_FIX_MERGED = PASS.
- DATABASE_URL_VISIBLE_IN_PRODUCTION_RUNTIME = OPEN. The current crash occurs while importing the module, before `_external_database_url()` / `_default_store()` can provide runtime evidence. The available Vercel connector in this session does not expose environment-variable listing. This is not evidence that `DATABASE_URL` is missing.
- POST_FIX_PRODUCTION_DEPLOYMENT = NONE observed.

## BLOCKERS
- No Production deployment containing PR #49 merge `13c7976fdae227b10f20d7130f6f7e176eb579e3` or later main exists yet.
- The exposed Vercel deploy action cannot create a Git-linked current-main Production deployment in this session; invocation is rejected because the runtime requires explicit `target`, project `name`, and full `files` bundle inputs not exposed by the connector schema.

## OPEN_ITEMS
- Create one Production deployment from latest main containing PR #49 while keeping `git.deploymentEnabled=false`.
- FIRST GATE after redeploy: deployment `READY`; deployed SHA contains PR #49, PR #48, and PR #45; `GET /api/v1/session` returns valid FastAPI JSON and no `FUNCTION_INVOCATION_FAILED`.
- After import succeeds, use `/api/v1/session` behavior and runtime logs to verify the production database path. If the external database variable is unavailable, production should fail closed at the application layer rather than crash during import.
- Only after FIRST GATE passes, continue full production smoke: career create/state/one next_game/revision +1/idempotency/stale revision/persistence/cold-start/browser E2E/production-authority verification.

## NEXT_ACTION
- Manually deploy latest main through a Vercel Git-aware UI/CLI/API path that can target Production without re-enabling Git auto-deploy. Once the new deployment appears, verify only FIRST GATE first; do not run full career smoke until `/api/v1/session` is healthy.

## RELATED_PRS
- #49 merged: Vercel direct-module import circularity fix
- #48 merged: web npm lockfile fix
- #45 merged: Vercel Python packaging fix
- #44 merged: Neon production schema + Vercel handoff
- #43 merged: P0 production persistence wiring
- #42 merged: Web ↔ Python vertical slice

## GATES
- PR45_MERGED = PASS
- PR48_LOCKFILE_FIX_MERGED = PASS
- PR49_RUNTIME_IMPORT_FIX_MERGED = PASS
- VERCEL_GIT_AUTO_DEPLOY = OFF
- VERCEL_RUNTIME_ROOT_CAUSE_IDENTIFIED = PASS
- VERCEL_DIRECT_IMPORT_REGRESSION = PASS
- VERCEL_CURRENT_MAIN_BUILD = OPEN
- VERCEL_DEPLOYED_SHA_VERIFIED = OPEN
- PRODUCTION_API_SESSION_ROUTE = OPEN
- PRODUCTION_DATABASE_URL_VISIBLE = OPEN
- VERCEL_PRODUCTION_WIRING = OPEN
- PRODUCTION_SESSION_PERSISTENCE = OPEN
- PRODUCTION_REVISION_CAS = OPEN
- PRODUCTION_IDEMPOTENCY = OPEN
- DEPLOYED_NEXT_GAME_E2E = OPEN
- DEPLOYED_BROWSER_E2E = OPEN
- COLD_START_PERSISTENCE = OPEN
- MOCK_NOT_PRODUCTION_AUTHORITY = OPEN
- P0_WEB_PYTHON_PRODUCTION_COMPLETE = OPEN
