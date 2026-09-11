# 07 - Integration & GitHub

WORKSTREAM: 07 - Integration & GitHub
UPDATED_AT: 2026-09-11
DEPLOYED_SOURCE_OF_TRUTH: `b3ca2fe9cd6c84f400d7d301a2c30176bf0978cc`
CURRENT_MAIN_AT_VALIDATION: `e1418f0c69e84d5c038a1a0b860296e24c55102f` (later status-documentation commits only; no application-code delta from deployed SHA)
STATE: VALIDATED_WITH_OPEN_COLD_START_GATE
CURRENT_TASK: Full Production Smoke after FIRST GATE PASS
RESULT: PRODUCTION API / NEON / BROWSER SMOKE PASS — explicit forced cold-start persistence remains OPEN because the available runtime telemetry does not expose function-instance identity or a deterministic cold-start trigger.

## PRODUCTION DEPLOYMENT
- Production project: `baseball-player-sim` (`prj_5m6Qi5Ljj0ebBtZPcWbZjQADj1ZD`).
- Validated deployment: `dpl_FZZyPNWuSTDzscY4hndgNZD2sdyc`.
- Deployment state: `READY`.
- Deployed Git SHA: `b3ca2fe9cd6c84f400d7d301a2c30176bf0978cc`.
- Deployed SHA contains PR #49, PR #48, and PR #45.
- Current main is ahead only by workstream-status documentation; deployed application code is the validated production code.
- `git.deploymentEnabled=false` remains preserved.

## FIRST GATE
- `GET /api/v1/session` = HTTP 200 with FastAPI JSON `{ "has_career": false, "revision": null }` on a fresh production session.
- Previous circular-import `FUNCTION_INVOCATION_FAILED` is resolved.
- Previous fail-closed `SAVE_FAILED: external transactional durable store is required in production` is resolved after Production `DATABASE_URL` configuration/redeployment.
- Neon/Postgres adapter initialization is operational.

## FULL API SMOKE
A temporary validation-only GitHub Actions branch ran the repository's existing `tools/deployed_p0_smoke.py` directly against `https://baseball-player-sim.vercel.app`. No validation workflow was merged to main and no production application code was changed.

Observed PASS sequence:
- fresh session reported no career;
- `POST /api/v1/career` returned 201 and created revision 1;
- `GET /api/v1/state` returned the created authoritative state;
- one `next_game` mutation returned 200 and revision advanced 1 -> 2;
- persisted game/stat state changed (game 1 and real batting aggregate changes);
- replay with the same idempotency key returned the same committed result with no duplicate mutation;
- stale `expected_revision` returned HTTP 409 `REVISION_CONFLICT`;
- a new HTTP client carrying only the production session cookie recovered the same revision-2 state;
- unknown API route returned normal JSON 404 rather than frontend fallback.

Vercel runtime logs independently show the production sequence `session 200 -> career 201 -> state 200 -> advance 200 -> replay advance 200 -> stale advance 409 -> state 200` on deployment `dpl_FZZyPNWuSTDzscY4hndgNZD2sdyc`.

## NEON PRODUCTION EVIDENCE
- Neon project: `baseball-player-sim-production` (`soft-paper-34017307`).
- Production/default branch: `br-muddy-morning-a5gtu4wg`.
- Database: `baseball_sim`.
- `baseball_sim_sessions` contains the production smoke session at revision 2, save_version 3.
- The saved payload contains `games_completed = 1`, a persisted recent game, and non-zero farm/overall batting aggregates, proving game/stat mutation was durably stored.
- `baseball_sim_idempotency` contains exactly one row for the smoke mutation key with `resulting_revision = 2`; replay did not create a duplicate row.
- Session identifiers were inspected only via one-way hash; no cookie/session secret or database credential was exposed.

## BROWSER E2E
- A validation-only headless Playwright workflow exercised the real Production URL.
- Browser opened the Production frontend and observed the NEW CAREER page.
- Browser created player `BrowserE2E` through the actual UI.
- Dashboard rendered `GAME 0 / 144`.
- Browser clicked `다음 경기` and observed `GAME 1 / 144`.
- Browser reloaded the page and the same player/career remained at `GAME 1 / 144`.
- Final browser result: PASS — production browser create/advance/reload persistence.
- An earlier validation attempt failed only because the test supplied a 13-character name while the UI intentionally enforces `maxLength=12`; the corrected test passed without application changes.

## PRODUCTION PROVIDER AUTHORITY
- Production bootstrap in `web/src/main.tsx` explicitly constructs `ProductionPresentationProvider(new HttpBackendPresentationGateway())` and injects it into `App`.
- `App` has a mock fallback only when no provider is injected; the Production bootstrap does inject the HTTP production provider.
- Therefore `MockGameDataProvider` is not the Production authority.

## COLD-START / SEPARATE INVOCATION
- Separate-client persistence = PASS: a new HTTP client using the same opaque session cookie recovered the exact revision-2 state from Neon-backed production storage.
- Multiple independent Vercel serverless HTTP invocations also read/write the same durable state successfully.
- Forced cold-start persistence = OPEN: current Vercel connector/runtime logs do not expose serverless instance identity and no deterministic function recycle/cold-start control is available in this session. Do not relabel this as PASS without explicit cold-start evidence.

## GATES
- PR45_MERGED = PASS
- PR48_LOCKFILE_FIX_MERGED = PASS
- PR49_RUNTIME_IMPORT_FIX_MERGED = PASS
- VERCEL_GIT_AUTO_DEPLOY = OFF
- VERCEL_CURRENT_MAIN_BUILD = PASS
- VERCEL_DEPLOYED_SHA_VERIFIED = PASS
- PRODUCTION_API_ROUTE_REACHED = PASS
- PRODUCTION_API_SESSION_ROUTE = PASS
- PRODUCTION_DATABASE_URL_VISIBLE = PASS
- VERCEL_PRODUCTION_WIRING = PASS
- PRODUCTION_SESSION_PERSISTENCE = PASS
- PRODUCTION_REVISION_CAS = PASS
- PRODUCTION_IDEMPOTENCY = PASS
- DEPLOYED_NEXT_GAME_E2E = PASS
- SEPARATE_CLIENT_PERSISTENCE = PASS
- DEPLOYED_BROWSER_E2E = PASS
- MOCK_NOT_PRODUCTION_AUTHORITY = PASS
- COLD_START_PERSISTENCE = OPEN
- P0_WEB_PYTHON_PRODUCTION_COMPLETE = OPEN (only explicit forced-cold-start evidence remains open)

## NEXT_ACTION
Obtain explicit cold-start/recycled-instance evidence without changing application semantics. If that evidence confirms the same session survives a fresh serverless instance, mark `COLD_START_PERSISTENCE = PASS` and close `P0_WEB_PYTHON_PRODUCTION_COMPLETE`.
