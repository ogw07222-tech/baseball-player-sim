# 07 - Integration & GitHub

WORKSTREAM: 07 - Integration & GitHub
UPDATED_AT: 2026-09-11
SOURCE_OF_TRUTH: main@8a6f48c9ab833ab5412cc246e31b6b6c09275296
STATE: BLOCKED
CURRENT_TASK: Post-Redeploy Production Verification
RESULT: FAIL/OPEN — Vercel access is restored, but the deployable P0 root project is not running successfully. `baseball-player-sim` targets current main but its production build fails before runtime; `baseball-player-sim-ui` is READY only on stale pre-P0 commit `44b4bbb9113e351ceb35aac75f02a8ee6eab3723` and returns 404 for `/api/v1/session`. Neon production has no session/idempotency rows, so deployed persistence evidence does not exist yet.

## LAST_COMPLETED
- Re-read task-start main `8a6f48c9ab833ab5412cc246e31b6b6c09275296` and the 07 status file.
- Vercel connector access is now restored. Team `ogw` resolves to slug `ogw2` / team ID `team_Zklx7aawqjHXpgeXNmagdqaP`.
- Confirmed three projects: `baseball-player-sim`, `baseball-player-sim-ui`, and `baseball-player-sim-ui-preview`.
- Identified `baseball-player-sim` as the P0 repository-root/FastAPI-capable production project: framework `python`, linked to `ogw07222-tech/baseball-player-sim`, latest target `production`, Git SHA `8a6f48c9ab833ab5412cc246e31b6b6c09275296`.
- Its latest production deployment `dpl_AWR72LW2KX6UQ23LcpRBmHFQXvz9` is `ERROR`. Build log root cause: Vercel Python build runs `uv lock` and fails because root `pyproject.toml` has `[tool.vercel]` but no required `[project]` table.
- Confirmed `baseball-player-sim-ui` is a separate Vite project with canonical domain `baseball-player-sim-ui.vercel.app`; its latest production deployment `dpl_CxT7av75RwmkCZEipRqEnHRffLo3` is `READY` but redeploys stale commit `44b4bbb9113e351ceb35aac75f02a8ee6eab3723` (`Merge pull request #17...`), predating PR #42/#43/#44 P0 backend work.
- Production request `GET https://baseball-player-sim-ui.vercel.app/api/v1/session` returned Vercel HTTP 404 `NOT_FOUND`, proving this READY deployment does not expose the P0 FastAPI route.
- Confirmed `baseball-player-sim-ui-preview` latest production-target deployment is also `ERROR` and is not the production authority.
- Queried actual Neon production `baseball_sim`: 0 session rows, max revision NULL, 0 idempotency rows, no latest update timestamps. Therefore no deployed P0 mutation has reached Neon production.
- No gameplay, rating, growth, injury, event, KBO rule, stat formula, UI, advance breadth, persistence logic, or feature code was changed during this verification task.

## CURRENT_FINDINGS
- Failure classification: `J. deployed SHA mismatch` on the READY UI project plus `C. deployment root/config issue` on the current-main root project.
- The current-main P0 code is present in GitHub but not successfully running on Vercel production. The repository-root project clones the correct SHA and fails during Python dependency/build preparation before FastAPI starts.
- Root `pyproject.toml` currently contains only `[tool.vercel] entrypoint = "src.api.app:app"` and the Vite build script. Vercel's current Python runtime invokes `uv lock`, which requires a valid `[project]` table; this is the direct build blocker observed in production logs.
- The READY `baseball-player-sim-ui` deployment is not usable for P0 verification because it is stale and `/api/v1/session` is absent.
- `DATABASE_URL` secret value was not exposed. Because the current-main deployment fails before runtime and the available Vercel tool surface does not enumerate project env variables, Production-scope presence cannot be independently proven from runtime behavior yet.
- Prior Neon/Postgres adapter/schema/CAS/idempotency validation remains PASS, but production Vercel -> FastAPI -> Neon evidence is absent.

## BLOCKERS
- `baseball-player-sim` production build failure: Vercel Python `uv lock` rejects the current root `pyproject.toml` because it has no `[project]` metadata table.
- The only READY canonical UI production deployment is stale SHA `44b4bbb9113e351ceb35aac75f02a8ee6eab3723`, so it cannot expose the P0 backend routes.
- Until a current-main production deployment reaches READY, session/create/state/next_game/revision/idempotency/stale-409/cold-start/browser E2E cannot be executed truthfully.

## OPEN_ITEMS
- Resolve the minimal Vercel Python packaging/deployment-config blocker for the repository-root project without changing simulation/domain behavior.
- Produce a READY production deployment from current main (or the minimal deployment-config-fix successor) on the repository-root FastAPI project.
- Verify `DATABASE_URL` is available to that deployment with Production scope without exposing the secret value.
- Execute production smoke: session -> career create -> state -> next_game -> revision +1 -> state -> same-key replay -> stale revision 409 -> API error schema.
- Verify Neon production session row, revision/updated_at change, idempotency row, and duplicate-mutation absence.
- Execute separate invocation/cold-start persistence and deployed browser E2E; verify frontend renders backend DTOs and MockGameDataProvider is not production authority.

## DEPENDENCIES
- Neon production PostgreSQL/schema: READY and previously validated.
- Vercel team/project access: RESTORED.
- Vercel current-main production deployment: BLOCKED by Python packaging config.
- 06 Web UI contract remains unchanged; no frontend feature work is needed.

## NEXT_ACTION
- Fix only the repository-root Vercel Python packaging metadata needed for the current Python runtime, redeploy latest main on `baseball-player-sim`, then immediately resume the existing deployed P0 smoke and Neon/browser verification. Do not change gameplay/domain/UI behavior.

## RELATED_PRS
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
- VERCEL_PROJECT_ACCESS = PASS
- VERCEL_PRODUCTION_PROJECT_IDENTIFIED = PASS
- VERCEL_CURRENT_MAIN_DEPLOY_ATTEMPT = PASS
- VERCEL_CURRENT_MAIN_BUILD = FAIL
- VERCEL_DEPLOYED_SHA_VERIFIED = FAIL
- VERCEL_DATABASE_URL_PRODUCTION_SCOPE_VERIFIED = OPEN
- VERCEL_PRODUCTION_WIRING = FAIL
- PRODUCTION_API_SESSION_ROUTE = FAIL
- PRODUCTION_SESSION_PERSISTENCE = OPEN
- PRODUCTION_REVISION_CAS = OPEN
- PRODUCTION_IDEMPOTENCY = OPEN
- DEPLOYED_NEXT_GAME_E2E = OPEN
- DEPLOYED_BROWSER_E2E = OPEN
- COLD_START_PERSISTENCE = OPEN
- P0_WEB_PYTHON_PRODUCTION_COMPLETE = OPEN
