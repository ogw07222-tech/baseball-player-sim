# 07 - Integration & GitHub

WORKSTREAM: 07 - Integration & GitHub
UPDATED_AT: 2026-09-11
SOURCE_OF_TRUTH: main@546147bd280aafb1530904aeac328515718931f0
STATE: BLOCKED
CURRENT_TASK: Re-enable Vercel Git Production Deployments
RESULT: PARTIAL — PR #46 removed root `vercel.json` `git.deploymentEnabled: false`, restoring Git-triggered Vercel deployments for the root `baseball-player-sim` project. Merge to `main` automatically created Production deployment `dpl_BUJd7fdPfkJJwUHm3iPXXCWA4JkZ` from merge SHA `546147bd280aafb1530904aeac328515718931f0`, proving Git -> Vercel triggering is restored and Production Branch is operationally `main`. The current-main deployment then failed during the custom web build because `npm --prefix web ci` found no `web/package-lock.json`. This is a new current-main build blocker, distinct from the historical pre-PR45 Python packaging failure. Because deployment did not reach READY, `/api/v1/session` and full production smoke were not executed.

## LAST_COMPLETED
- Task-start main verified: `83e4a3c78568d343ae18c0a86e493288d75c974c`.
- Confirmed root `vercel.json` disabled all Git deployments with `git.deploymentEnabled: false`.
- Confirmed Vercel project `baseball-player-sim` (`prj_5m6Qi5Ljj0ebBtZPcWbZjQADj1ZD`) is Git-linked to `ogw07222-tech/baseball-player-sim`, framework `python`, root project.
- Confirmed production authority is `baseball-player-sim`, not `baseball-player-sim-ui`, for this P0 runtime verification.
- Vercel documentation confirms `git.deploymentEnabled: false` disables automatic Git deployments; removing the disabling block restores default enabled behavior.
- Created branch `fix/re-enable-vercel-git-deployments`.
- Changed root `vercel.json` to schema-only configuration; no unrelated Vercel settings were added.
- Opened PR #46 `fix: re-enable Vercel Git deployments` and merged it.
- PR #46 merge SHA: `546147bd280aafb1530904aeac328515718931f0`.
- Vercel automatically created Production deployment `dpl_BUJd7fdPfkJJwUHm3iPXXCWA4JkZ` from Git ref `main`, SHA `546147bd280aafb1530904aeac328515718931f0`.
- The deployment cloned `main` at `546147b`, selected Python 3.12 from `pyproject.toml`, installed Python dependencies successfully, and then failed at `npm --prefix web ci` because no npm lockfile exists under `web/`.
- No gameplay, ratings, growth, events, DB schema, SessionStore semantics, UI, stat formula, or unrelated configuration changes were made.

## CURRENT_FINDINGS
- `VERCEL_GIT_DEPLOYMENT_ENABLED = PASS`: a Git push/merge now creates Vercel deployments automatically.
- `NEW_CURRENT_MAIN_PRODUCTION_DEPLOYMENT = PASS`: a new Production deployment was created from `main` after PR #46 merge.
- Production Branch is operationally confirmed as `main` by the automatic Production deployment metadata (`githubCommitRef=main`, `target=production`, main branch alias).
- `VERCEL_DEPLOYED_SHA_VERIFIED = PASS`: deployment SHA `546147bd...` is the PR #46 merge SHA and is later than PR #45 merge `0a9ad6d3...`, so it contains the PR #45 packaging fix.
- `VERCEL_CURRENT_MAIN_BUILD = FAIL`: current-main deployment reached Python setup successfully but failed in the explicit web build command because `npm ci` requires an existing lockfile and `web/package-lock.json` is absent.
- `PRODUCTION_API_SESSION_ROUTE = OPEN`: not tested because FIRST GATE failed at deployment READY.
- The historical `No project table found in pyproject.toml` error is not the current failure; current-main passed that Python packaging stage.

## HISTORICAL
- STALE_PRODUCTION_DEPLOYMENT = FAIL
- STALE_DEPLOYMENT_ID = `dpl_E8HQViPuLgzzbuvgASB4KmtEMAfg`
- STALE_DEPLOYMENT_SHA = `8a6f48c9ab833ab5412cc246e31b6b6c09275296`
- STALE_DEPLOYMENT_PACKAGING = FAIL
- Historical failure reason: stale pre-PR45 deployment lacked the PEP 621 `[project]` table.

## BLOCKERS
- Current-main Production build fails because the configured command `npm --prefix web ci && npm --prefix web run build` requires `web/package-lock.json`, which is not present in the repository.

## OPEN_ITEMS
- Resolve the current-main web packaging/build blocker with a separate minimal dependency/build-contract change.
- Produce a new Production deployment and require `READY`.
- Reconfirm deployed SHA contains PR #45 or later main.
- Only after READY, verify `GET /api/v1/session` returns FastAPI JSON.
- Only if the full FIRST GATE passes, execute career create/state/next_game/revision/persistence/Neon/idempotency/stale-409/cold-start/browser production smoke.

## DEPENDENCIES
- PR #45 Python packaging fix: merged and verified present in deployed SHA ancestry.
- Neon production PostgreSQL/schema: READY and previously validated.
- Git -> Vercel automatic deployment triggering: RESTORED.
- Current web npm lockfile/build contract: BLOCKED.

## NEXT_ACTION
- Do not reinterpret the historical Python packaging failure as current. Address only the newly evidenced current-main npm lockfile/build blocker in a separate minimal task, then let Git create a new Production deployment and re-run FIRST GATE. Do not run `/api/v1/session` or full smoke until deployment is READY.

## RELATED_PRS
- #46 merged: re-enable Vercel Git deployments
- #45 merged: minimal Vercel Python PEP 621/uv packaging fix
- #44 merged: Neon production schema + Vercel handoff
- #43 merged: P0 Vercel production persistence wiring code
- #42 merged: P0 Web ↔ Python local/CI vertical slice
- #37 merged: production presentation contract/provider foundation

## RELATED_BRANCHES
- main
- fix/re-enable-vercel-git-deployments
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
- VERCEL_GIT_DEPLOYMENT_ENABLED = PASS
- NEW_CURRENT_MAIN_PRODUCTION_DEPLOYMENT = PASS
- VERCEL_CURRENT_MAIN_BUILD = FAIL
- VERCEL_DEPLOYED_SHA_VERIFIED = PASS
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
