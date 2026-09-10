# 07 - Integration & GitHub

WORKSTREAM: 07 - Integration & GitHub
UPDATED_AT: 2026-09-11
SOURCE_OF_TRUTH: main@b455db85e0ffa81cbe93f2f8106f9a20e7538a52
STATE: BLOCKED
CURRENT_TASK: Vercel Connector Stability Recheck + Minimal Production Gate Probe
RESULT: OPEN/BLOCKED — Vercel connector tool discovery succeeded, but the first live `list_teams` call immediately disabled the connector. Per task contract, no deployment/project/runtime facts were inferred beyond prior verified evidence. The minimal production probe (deployment status, deployed SHA, `/api/v1/session`) was not run, and no full production smoke was attempted.

## LAST_COMPLETED
- Re-read latest main at task start: `b455db85e0ffa81cbe93f2f8106f9a20e7538a52`.
- Re-read the 07 workstream status.
- Re-loaded the Vercel connector skill and successfully discovered the `list_teams` tool surface.
- First live `list_teams` invocation returned a tool-level disable event; the connector became unavailable before any current team/project/deployment evidence could be collected.
- Per the explicit task rule, stopped Vercel verification immediately rather than carrying forward stale project/deployment assumptions as current facts.
- No application, gameplay, ratings, growth, injury, events, KBO rules, stat formulas, UI, advance breadth, persistence logic, DB schema, SessionStore semantics, or deployment configuration was changed.

## CURRENT_FINDINGS
- Vercel connector discovery is available but the live connector is not stable enough to complete even Step 1 (`list teams`).
- No current evidence was collected for team/project visibility, latest production deployment status, deployed commit SHA, or `/api/v1/session`.
- Prior verified evidence remains historical only: the last current-main root deployment had a Python packaging failure and the last READY UI deployment was stale/pre-P0. This task does not automatically treat those historical results as the current deployment state.
- Because Step 1 failed, Step 2 minimal production probe and Step 3 full production smoke were intentionally not executed.
- Prior Neon/Postgres durable-store validation remains PASS but is not substituted for deployed runtime evidence.

## BLOCKERS
- Vercel connector live access is unstable/unavailable: first `list_teams` call disabled the connector.
- Without stable connector access, current project identification, latest deployment status/SHA, build logs, and protected runtime fetch cannot be independently verified.

## OPEN_ITEMS
- Re-establish stable Vercel connector access and successfully complete: list teams -> list projects -> identify production project -> list latest deployments.
- If Step 1 succeeds, verify only the minimal production gate first: latest production deployment status, deployed Git SHA, and `GET /api/v1/session`.
- Only if that minimal probe is current-main/READY/session-route PASS should the complete career/create/state/next_game/persistence/idempotency/stale-409/cold-start/browser smoke be run.
- If the current deployment is actually failing, fetch its current build log and classify the real blocker before proposing any packaging fix.

## DEPENDENCIES
- Neon production PostgreSQL/schema: READY and previously validated.
- GitHub main at task start: `b455db85e0ffa81cbe93f2f8106f9a20e7538a52`.
- Vercel connector live access: BLOCKED in this attempt.

## NEXT_ACTION
- Retry Vercel connector access. Do not infer current deployment state from historical failures. The first successful sequence must be team/project/deployment discovery followed by the three-point minimal production probe.

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
