# 07 - Integration & GitHub

WORKSTREAM: 07 - Integration & GitHub
UPDATED_AT: 2026-09-11
SOURCE_OF_TRUTH: main@818226121022b62f17d31beffe28ffed343cd56d
STATE: BLOCKED
CURRENT_TASK: Final Vercel Production Runtime Verification
RESULT: BLOCKED — Vercel connector access is working, but the FIRST GATE failed. The latest Production deployment for `baseball-player-sim` is `dpl_E8HQViPuLgzzbuvgASB4KmtEMAfg` and is `ERROR`, not `READY`. Its Git metadata points to `8a6f48c9ab833ab5412cc246e31b6b6c09275296`, which GitHub comparison proves is behind PR #45 merge commit `0a9ad6d3aac51e3d7b4eafa8befe2fb449bee1a2` and therefore does not contain the packaging fix. `GET /api/v1/session` against that deployment returned an HTTP 302 Vercel SSO redirect rather than the production API response. Per verification policy, full production smoke was not run and runtime gates remain OPEN/FAIL as recorded below.

## LAST_COMPLETED
- Re-read current main: `818226121022b62f17d31beffe28ffed343cd56d`.
- Confirmed PR #45 merge commit remains `0a9ad6d3aac51e3d7b4eafa8befe2fb449bee1a2`.
- Vercel connector live access succeeded.
- Checked latest Production deployment for project `baseball-player-sim` (`prj_5m6Qi5Ljj0ebBtZPcWbZjQADj1ZD`).
- Latest deployment: `dpl_E8HQViPuLgzzbuvgASB4KmtEMAfg`, state `ERROR`, target `production`.
- Deployment Git SHA: `8a6f48c9ab833ab5412cc246e31b6b6c09275296`.
- GitHub compare `0a9ad6d...8a6f48c` reports the deployed SHA is behind the PR #45 merge commit, so the deployment does not contain the packaging fix.
- `GET https://baseball-player-634by6u9s-ogw2.vercel.app/api/v1/session` returned HTTP 302 to Vercel SSO, not an application session response.
- Because FIRST GATE failed, no create/state/next_game/Neon/idempotency/stale-revision/cold-start/browser smoke was executed.
- No application code, gameplay, ratings, growth, injury, events, KBO rules, stat formulas, Neon schema, SessionStore semantics, UI, or advance breadth was changed.

## CURRENT_FINDINGS
- `VERCEL_PYTHON_PACKAGING` and `VERCEL_UV_LOCK_CI` remain PASS from PR #45/GitHub CI evidence.
- `VERCEL_CONNECTOR_ACCESS` is now PASS.
- `VERCEL_CURRENT_MAIN_BUILD` is FAIL because the latest Production deployment is `ERROR`.
- `VERCEL_DEPLOYED_SHA_VERIFIED` is FAIL because the latest Production deployment points to `8a6f48c9...`, which predates and does not contain `0a9ad6d3...`.
- `PRODUCTION_API_SESSION_ROUTE` is FAIL for this deployment because the request did not reach a normal application response; it returned a Vercel SSO redirect.
- GitHub CI PASS is not used as a substitute for Vercel runtime PASS.
- Full runtime smoke remains intentionally unexecuted until all three FIRST GATE checks pass.

## BLOCKERS
- Current Production deployment is stale and failed (`ERROR`).
- Current Production deployment SHA does not include PR #45.
- Session route is not currently evidenced at runtime; the tested deployment URL redirected to Vercel SSO.

## OPEN_ITEMS
- Produce a new Production deployment from current main or a main successor containing `0a9ad6d3aac51e3d7b4eafa8befe2fb449bee1a2`.
- Verify that deployment reaches `READY`.
- Verify its deployed Git SHA contains PR #45.
- Verify Production `GET /api/v1/session` returns the expected application response rather than Vercel auth/redirect behavior.
- Only after those three pass: career create, state, next_game, revision +1, game/stat change, refresh persistence, Neon session/idempotency rows, same-key replay, stale 409, separate invocation/cold-start persistence, browser E2E, and production authority check.

## DEPENDENCIES
- Neon production PostgreSQL/schema: READY and previously validated.
- PR #45 packaging fix: merged and GitHub CI validated.
- Vercel connector live access: PASS.
- Current Production deployment: FAIL/stale.

## NEXT_ACTION
- Redeploy current main to the `baseball-player-sim` Production project, then re-run only the FIRST GATE: deployment READY, deployed SHA contains `0a9ad6d3...`, and `/api/v1/session` returns an application response. Do not proceed to full smoke until all three pass. Do not expose `DATABASE_URL`, auth cookies, or other secrets.

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
- P0_WEB_PYTHON_PRODUCTION_COMPLETE = OPEN
