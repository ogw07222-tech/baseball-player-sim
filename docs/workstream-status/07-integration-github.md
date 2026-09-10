# 07 - Integration & GitHub

WORKSTREAM: 07 - Integration & GitHub
UPDATED_AT: 2026-09-11
SOURCE_OF_TRUTH: main@0a9ad6d3aac51e3d7b4eafa8befe2fb449bee1a2
STATE: BLOCKED
CURRENT_TASK: Fix Confirmed Vercel Python Packaging Failure
RESULT: PARTIAL_PASS — confirmed `uv lock` packaging blocker is fixed in code and merged via PR #45. Branch and PR CI both prove the PEP 621 project metadata, uv resolution path, FastAPI entrypoint, API/full Python tests, and web build/tests are green. Actual post-merge Vercel deployment READY and `/api/v1/session` remain OPEN because the Vercel connector disabled again on the first live post-merge call.

## LAST_COMPLETED
- Task-start main was `ed9ff7831ab899c625a36217c90c07927a1a8d12`.
- Confirmed root cause from prior real Vercel build evidence: Vercel Python runtime invoked `uv lock` against root `pyproject.toml`, which had only `[tool.vercel]` and no PEP 621 `[project]`, causing `No project table found` before FastAPI startup.
- Re-read current dependency/install contract: `requirements.txt` includes `requirements-api.txt`; runtime dependencies are `fastapi>=0.115,<1`, `httpx>=0.27,<1`, `uvicorn>=0.30,<1`, and `psycopg[binary]>=3.2,<4`; CI installs them from `requirements-api.txt`.
- Added minimal `[project]` metadata: name `baseball-player-sim`, version `0.1.0`, `requires-python = ">=3.12"`, and the same four runtime dependency specifiers. No build backend or publish/package-framework migration was added.
- Preserved `[tool.vercel] entrypoint = "src.api.app:app"` and the existing Vite build command unchanged.
- Added `tests/test_python_dependency_contract.py` to parse the PEP 621 metadata, require exact dependency equality with `requirements-api.txt`, and preserve the Vercel entrypoint contract.
- Added CI `uv lock --dry-run --python 3.12` packaging validation and enabled the workflow on `fix/**` branches.
- Branch run #660 (`34514693916`) completed SUCCESS: Vercel packaging/uv validation, compile, external durable store tests, FastAPI entrypoint smoke, API vertical slice, related production integration, full unit suite, auto career, balance, draft calibration, artifact upload, web build/tests all PASS.
- PR run #661 (`34514739802`) completed SUCCESS with the same gates PASS.
- PR #45 `Fix Vercel Python project metadata` merged with merge commit `0a9ad6d3aac51e3d7b4eafa8befe2fb449bee1a2`.
- Post-merge main run #662 (`34514958869`) started on the merge SHA; Vercel packaging/uv validation, compile, external-store tests, FastAPI entrypoint, API integration and web build/tests were already PASS at last observation, while the remainder of the Python job was still running.
- After merge, Vercel tool discovery succeeded, but the first live `list_teams` call disabled the connector again. No Vercel deployment state or runtime response was inferred.
- No gameplay, ratings, growth, injury, events, KBO rules, stat formulas, Neon schema, SessionStore/CAS/idempotency semantics, UI redesign, or advance-breadth logic was changed.

## CURRENT_FINDINGS
- `VERCEL_PYTHON_PACKAGING` is PASS at code/CI level: the exact previously failing `uv lock` class now succeeds in both branch and PR GitHub Actions.
- Dependency authority remains `requirements-api.txt` for local/CI install; `project.dependencies` is the Vercel/uv mirror required by the platform. The contract test prevents silent drift between them.
- Local/container TOML parsing and uv project recognition succeeded; local registry resolution was limited by outbound DNS, so complete resolution evidence comes from GitHub Actions `uv lock --dry-run` PASS rather than being overstated as a local network PASS.
- Actual Vercel `VERCEL_CURRENT_MAIN_BUILD` cannot yet be marked PASS solely from GitHub CI. A Vercel production/preview deployment of `0a9ad6d3...` must reach READY and create the Python function.
- `/api/v1/session` has not been rerun against a READY deployment containing PR #45, so the production route remains OPEN.

## BLOCKERS
- Vercel connector again became unavailable on the first live post-merge call, preventing inspection/triggering of the current-main Vercel deployment and protected runtime fetch.
- Root `vercel.json` has Git deployment disabled, so a merge does not by itself prove a new production deployment exists; actual Vercel deployment evidence is required.

## OPEN_ITEMS
- Re-establish Vercel connector or use manual Vercel UI evidence to verify a deployment from `0a9ad6d3aac51e3d7b4eafa8befe2fb449bee1a2` (or later status-only successor with identical code) reaches READY.
- Confirm Vercel build completes Python dependency installation/function creation and frontend build.
- Verify `GET /api/v1/session` returns the expected API response on that deployment.
- Only after those build gates PASS, resume production create/state/next_game/revision/persistence/idempotency/stale-409/cold-start/browser verification.

## DEPENDENCIES
- Neon production PostgreSQL/schema: READY and previously validated.
- GitHub packaging fix: merged in PR #45 at `0a9ad6d3aac51e3d7b4eafa8befe2fb449bee1a2`.
- Vercel connector live access: BLOCKED at post-merge verification.

## NEXT_ACTION
- Inspect or manually redeploy the repository-root `baseball-player-sim` project from the PR #45 merge SHA. First require Vercel READY + correct deployed SHA + `/api/v1/session` 200; then resume existing production smoke without any feature/refactor work.

## RELATED_PRS
- #45 merged: minimal Vercel Python PEP 621/uv packaging fix
- #44 merged: Neon production schema + Vercel handoff
- #43 merged: P0 Vercel production persistence wiring code
- #42 merged: P0 Web ↔ Python local/CI vertical slice
- #37 merged: production presentation contract/provider foundation

## RELATED_BRANCHES
- main
- fix/vercel-python-packaging
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
