# 07 - Integration & GitHub

WORKSTREAM: 07 - Integration & GitHub
UPDATED_AT: 2026-09-11
SOURCE_OF_TRUTH: main@2f2235ccc2253929f86483c3495f7ce1385d0748
STATE: BLOCKED
CURRENT_TASK: Vercel access recheck and production deployment smoke
RESULT: OPEN — latest main remains `2f2235ccc2253929f86483c3495f7ce1385d0748`. The Vercel connector was initially available for tool discovery but became disabled before project/deployment/runtime verification could be completed. Independent web access could not resolve the production domains through the available web path. No new production runtime evidence was obtained, so existing deployment/build blocker and OPEN deployed-E2E gates remain unchanged.

## LAST_COMPLETED
- Re-read latest main: `2f2235ccc2253929f86483c3495f7ce1385d0748`.
- Re-read the 07 workstream status and retained the last verified production facts: repository-root `baseball-player-sim` deployment on current-main predecessor failed in Vercel Python packaging, while `baseball-player-sim-ui` READY deployment was stale and lacked `/api/v1/session`.
- Re-initialized the Vercel connector and confirmed the tool surface was briefly discoverable, but the connector became disabled before live project/deployment fetches could complete.
- Tried an independent HTTP/web fallback against the known production domains; the available web path could not resolve/open those deployment URLs, so no HTTP assertions were fabricated.
- No application, gameplay, ratings, growth, injury, events, KBO rules, stat formulas, UI, advance breadth, persistence code, DB schema, SessionStore semantics, or deployment configuration was changed.

## CURRENT_FINDINGS
- There is no new evidence that a READY production deployment containing P0 FastAPI/Neon wiring exists after the last verified failure.
- Latest GitHub main still contains the existing packaging/deployment configuration and no packaging-fix commit was observed after `2f2235ccc2253929f86483c3495f7ce1385d0748`.
- Because the Vercel connector disabled mid-task and independent HTTP fallback could not access the domains, `/api/v1/session`, career creation, next_game, revision, persistence, idempotency, stale-409, cold-start, and browser E2E were not rerun.
- Prior Neon/Postgres adapter/schema/CAS/idempotency evidence remains valid but is not substituted for deployed runtime evidence.

## BLOCKERS
- Vercel connector unavailable during the actual verification phase.
- No independent HTTP/browser path in the current execution environment successfully reached the production Vercel domains.
- The last verified repository-root Vercel deployment remained blocked by Python packaging metadata and no later READY current-main deployment could be independently observed.

## OPEN_ITEMS
- Re-establish Vercel project/deployment/runtime access and identify the latest production deployment for `baseball-player-sim` / canonical production domain.
- Confirm the deployed Git SHA is current-main or its packaging-fix successor and that deployment state is READY.
- Run production smoke: GET session -> create career -> GET state -> next_game -> revision +1 -> GET state -> reconnect -> same-key replay -> stale revision 409 -> error schema.
- Verify Neon production session/idempotency rows and cold-start persistence.
- Run deployed browser E2E and verify backend DTO authority / no MockGameDataProvider authority.

## DEPENDENCIES
- Neon production PostgreSQL/schema: READY and previously validated.
- GitHub main: `2f2235ccc2253929f86483c3495f7ce1385d0748`.
- Vercel connector/runtime access: BLOCKED in this verification attempt.

## NEXT_ACTION
- Once Vercel access is available again, inspect the latest production deployment first. If current-main packaging is still failing, resolve only that deployment-config blocker; otherwise immediately execute the existing production smoke and Neon/browser verification without feature changes.

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
- VERCEL_ACCESS_RECHECK = BLOCKED
- VERCEL_CURRENT_MAIN_BUILD = OPEN
- VERCEL_DEPLOYED_SHA_VERIFIED = OPEN
- VERCEL_DATABASE_URL_PRODUCTION_SCOPE_VERIFIED = OPEN
- VERCEL_PRODUCTION_WIRING = OPEN
- PRODUCTION_API_SESSION_ROUTE = OPEN
- PRODUCTION_SESSION_PERSISTENCE = OPEN
- PRODUCTION_REVISION_CAS = OPEN
- PRODUCTION_IDEMPOTENCY = OPEN
- DEPLOYED_NEXT_GAME_E2E = OPEN
- DEPLOYED_BROWSER_E2E = OPEN
- COLD_START_PERSISTENCE = OPEN
- P0_WEB_PYTHON_PRODUCTION_COMPLETE = OPEN
