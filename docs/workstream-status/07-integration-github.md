# 07 - Integration & GitHub

WORKSTREAM: 07 - Integration & GitHub
UPDATED_AT: 2026-09-11
SOURCE_OF_TRUTH: main@9512e407d83bf13be608fa3f46fc7f2581b5b1bc
STATE: BLOCKED
CURRENT_TASK: Post-Redeploy Production Verification
RESULT: OPEN — user reports Production DATABASE_URL was added and Vercel was redeployed, but the connected Vercel capability still exposes zero teams/projects and cannot fetch the known production domain (403). Production runtime HTTP E2E therefore remains unverified. Neon production DB currently contains zero session rows and zero idempotency rows, so there is not yet durable production-smoke evidence.

## LAST_COMPLETED
- Re-read latest main at task start: `9512e407d83bf13be608fa3f46fc7f2581b5b1bc`.
- Re-read the 07 workstream status and retained prior Neon production PASS evidence.
- Rechecked Vercel account visibility after the user completed DATABASE_URL configuration and redeploy; the connected capability still returns zero teams/projects.
- Tried authenticated fetch of the known production domain `baseball-player-sim-ui.vercel.app`; Vercel capability returned 403 and could not create an authenticated/share fetch.
- Independent container HTTP access is unavailable in this environment because the domain cannot be DNS-resolved there; no production HTTP assertions were fabricated.
- Queried the actual Neon production database `baseball_sim` on branch `production`: `baseball_sim_sessions` has 0 rows and `baseball_sim_idempotency` has 0 rows, with no latest production update timestamp.
- No application, gameplay, ratings, growth, injury, events, KBO rules, stat formulas, UI, advance breadth, persistence code, schema, or deployment configuration was changed.

## CURRENT_FINDINGS
- User-reported deployment action: `DATABASE_URL` added to Vercel Production and production redeploy completed.
- Vercel management evidence: unavailable from this connection. Project, latest deployment, deployed commit SHA, root directory, and environment-variable target cannot currently be independently inspected.
- Runtime evidence: unavailable because the connected Vercel domain fetch is unauthorized and this execution environment cannot reach the public domain directly.
- Neon production resource remains READY and schema remains previously validated.
- Neon production currently has no session/idempotency rows, so no production smoke request has yet produced durable database state that can be independently observed here.
- Prior PostgreSQL/Neon adapter validation remains valid for persistence, CAS, and idempotency semantics, but it is not a substitute for deployed Vercel E2E evidence.
- `MockGameDataProvider` remains non-production authority by merged code/CI evidence; deployed browser authority cannot be re-proven until the production deployment is reachable.

## BLOCKERS
- Connected Vercel authorization still exposes no team/project and returns 403 for the known production deployment URL.
- No alternate outbound HTTP/browser capability in this execution environment can reach the production domain, so create/state/next_game/replay/409 runtime requests cannot be executed truthfully.
- Because no production HTTP smoke can be issued, the Neon production database remains empty and cannot provide post-redeploy persistence/cold-start evidence.

## OPEN_ITEMS
- Restore Vercel project/deployment visibility to this connected capability, or otherwise provide a production deployment URL that the runtime verification tool can access.
- Verify latest production deployment status, deployed Git SHA, repository-root configuration, and existence of `DATABASE_URL` with Production target without exposing its value.
- Execute production smoke: GET session -> create career -> GET state -> next_game -> revision +1/state change -> GET state -> reconnect/later invocation -> same state -> same-key replay with no duplicate game -> stale expected_revision 409 -> API error schema.
- After smoke, verify Neon production session row, revision increment, updated_at change, idempotency row, and absence of duplicate mutation without exposing full save payload/session secret.
- Execute deployed browser E2E and verify backend DTO authority / no MockGameDataProvider production authority.

## DEPENDENCIES
- Neon production PostgreSQL: READY.
- Vercel Production DATABASE_URL/redeploy: user reports COMPLETE, independent verification OPEN.
- Vercel account/project authorization for inspection and runtime fetch: BLOCKED.

## NEXT_ACTION
- As soon as Vercel deployment access is visible, inspect the current production deployment and run the complete deployed HTTP/browser/cold-start smoke against the already-prepared Neon production database. Do not change simulation behavior while resolving access.

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
- VERCEL_REDEPLOY_USER_REPORTED = PASS
- VERCEL_PROJECT_ACCESS = BLOCKED
- VERCEL_DEPLOYED_SHA_VERIFIED = OPEN
- VERCEL_DATABASE_URL_PRODUCTION_SCOPE_VERIFIED = OPEN
- VERCEL_PRODUCTION_WIRING = OPEN
- PRODUCTION_SESSION_PERSISTENCE = OPEN
- PRODUCTION_REVISION_CAS = OPEN
- PRODUCTION_IDEMPOTENCY = OPEN
- DEPLOYED_NEXT_GAME_E2E = OPEN
- DEPLOYED_BROWSER_E2E = OPEN
- COLD_START_PERSISTENCE = OPEN
- P0_WEB_PYTHON_PRODUCTION_COMPLETE = OPEN
