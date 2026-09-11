# 07 - Integration & GitHub

WORKSTREAM: 07 - Integration & GitHub
UPDATED_AT: 2026-09-11
SOURCE_MAIN_AT_CHECK: `58f662324b99505ae6f73bb8188cdfb65224157d`
STATE: PRODUCTION_SMOKE_PASS_WITH_COLD_START_OPEN
CURRENT_TASK: Vercel Production Gate
RESULT: PASS WITH ONE OPEN EVIDENCE ITEM — a new READY Production deployment exists on an eligible post-PR-45 main SHA; FastAPI/Neon/session/create/state/advance/revision/idempotency/stale-CAS/reconnect/browser production authority are evidenced. Strict forced cold-start persistence is not directly observable from the available runtime metadata and remains OPEN.

## NEW PRODUCTION DEPLOYMENT
Historical stale deployment is comparison-only:
- deployment: `dpl_E8HQViPuLgzzbuvgASB4KmtEMAfg`
- SHA: `8a6f48c9ab833ab5412cc246e31b6b6c09275296`
- its historical `No project table found` failure is not treated as evidence about current main.

New Production deployment verified:
- project: `baseball-player-sim`
- deployment: `dpl_FZZyPNWuSTDzscY4hndgNZD2sdyc`
- target: Production
- state: `READY`
- deployed SHA: `b3ca2fe9cd6c84f400d7d301a2c30176bf0978cc`
- source: redeploy of `dpl_zeqW4tEs1FBs95cKeZABrXSEPcCU`

Eligibility check:
- required floor: `0a9ad6d3aac51e3d7b4eafa8befe2fb449bee1a2`
- GitHub compare reports deployed SHA `b3ca2fe...` is 35 commits ahead / 0 behind that floor.
- therefore the deployment satisfies the required PR #45-containing main lineage gate.

## FIRST THREE GATES
1. Deployment state READY: PASS.
2. Deployed Git SHA at/after required PR #45-containing main commit: PASS.
3. `GET /api/v1/session` actual FastAPI JSON: PASS.

Observed on the new deployment:
- HTTP 200
- content type `application/json`
- body `{"has_career":false,"revision":null}`
- secure `baseball_sim_session` cookie issued.

This supersedes the earlier production `SAVE_FAILED: external transactional durable store is required in production` gate failure. Current runtime can now reach the configured external durable store.

## FULL PRODUCTION SMOKE EVIDENCE
### Reproducible HTTP smoke
The repository's existing `tools/deployed_p0_smoke.py` contract performs:
- GET session
- POST career, expect revision 1
- GET state equal to created snapshot
- POST one `next_game`, expect revision 2 and game 1
- replay the same idempotency key/body and require byte-equivalent JSON
- stale expected revision and require HTTP 409 `REVISION_CONFLICT`
- copy the session cookie into a new HTTP client and require recovered state equal to committed advanced state
- API 404 schema check.

Vercel runtime logs for `dpl_FZZyPNWuSTDzscY4hndgNZD2sdyc` show the matching production sequence at 08:13:54Z–08:13:56Z:
- GET `/api/v1/session` -> 200
- POST `/api/v1/career` -> 201
- GET `/api/v1/state` -> 200
- POST `/api/v1/advance` -> 200
- POST `/api/v1/advance` -> 200 (replay)
- POST `/api/v1/advance` -> 409 (stale revision)
- GET `/api/v1/state` -> 200 (new-client resume)
- GET `/api/v1/not-a-route` -> 404.

### Neon durable state
Production Neon project:
- project: `baseball-player-sim-production`
- branch: `production`
- database: `baseball_sim`
- PostgreSQL 16.

Canonical tables exist:
- `baseball_sim_sessions`
- `baseball_sim_idempotency`.

The deployed smoke session is durably present:
- session id `87690c68c71e4a8d8e9b2f0a9a27d878`
- revision `2`
- save version `3`.

The corresponding idempotency row is durably present:
- key `deployment-smoke-05c9456b7b83472a8dce79e97aa5df1f`
- resulting revision `2`
- stored response revision `2`
- stored response dashboard game number `1`.

The idempotency table primary key is `(session_id, idempotency_key)`, and the smoke row exists once while Vercel logs show two successful advance requests followed by the stale 409. Together with the smoke script's exact replay assertion, this is production evidence of same-key replay without a second committed mutation.

## GAME / REVISION / PERSISTENCE
PASS:
- career create committed revision 1
- one next_game committed revision 2
- game counter reached 1
- authoritative response persisted in Neon idempotency storage
- refresh/new-client GET state succeeded after the mutation
- stale revision returned 409
- session row remained revision 2 after replay/stale request.

The smoke script validates the advanced response differs from the initial career state through the game progress contract; current durable response records game 1. No gameplay/rating tuning was involved.

## BROWSER E2E / PRODUCTION AUTHORITY
Runtime logs on the same new deployment show a separate browser flow at 08:14:21Z–08:14:24Z:
- GET `/` -> 200
- frontend JS/CSS -> 200
- GET session -> 200
- POST career -> 201
- POST advance -> 200
- browser refresh GET `/` + assets -> 304
- GET session -> 200
- GET state -> 200.

A matching Neon browser session exists at revision 2 with a non-`deployment-smoke-*` UUID idempotency key, confirming browser mutations were persisted through the production backend.

Deployed SHA `b3ca2fe...` `web/src/main.tsx` constructs exactly:
`ProductionPresentationProvider(new HttpBackendPresentationGateway())`
and injects it into `App`.

Therefore `MockGameDataProvider` is not production authority: PASS.

## SEPARATE INVOCATION / COLD START
Separate invocation/reconnect persistence: PASS.
- state recovery occurred through a new HTTP client using only the durable session cookie;
- later browser refresh also recovered revision/state through the backend;
- Neon is the durable authority.

Strict forced cold-start evidence: OPEN.
- Vercel runtime output available here identifies serverless requests/deployment but does not expose a definitive cold-start marker for the resumed request.
- no redeploy/restart was forced solely to manufacture this evidence, avoiding unnecessary production usage.
- this does not block the verified durable persistence path, but the explicit forced-cold-start gate is not claimed PASS.

## PRODUCTION GATES
- NEW_PRODUCTION_DEPLOYMENT = PASS
- DEPLOYMENT_READY = PASS
- DEPLOYED_SHA_ELIGIBLE = PASS
- FASTAPI_SESSION_JSON = PASS
- NEON_RUNTIME_CONNECTION = PASS
- CAREER_CREATE = PASS
- GET_STATE = PASS
- NEXT_GAME = PASS
- REVISION_PLUS_ONE = PASS
- GAME_PROGRESS_CHANGE = PASS
- REFRESH_RECONNECT_PERSISTENCE = PASS
- NEON_SESSION_ROW = PASS
- NEON_IDEMPOTENCY_ROW = PASS
- SAME_KEY_REPLAY_NO_DUPLICATE_COMMIT = PASS
- STALE_REVISION_409 = PASS
- SEPARATE_INVOCATION_PERSISTENCE = PASS
- STRICT_FORCED_COLD_START_EVIDENCE = OPEN
- BROWSER_E2E = PASS
- PRODUCTION_PROVIDER_AUTHORITY = PASS
- MOCK_PROVIDER_PRODUCTION_AUTHORITY = PASS (meaning mock is NOT authority)

No application code, schema, Vercel configuration, or deployment setting was changed during this verification.

## PRIOR P1 CANONICAL EVENT TIMELINE STATUS
The prior 07 task remains unchanged:
- 04 CanonicalEventDTO v1 design is ready.
- production canonical event HTTP integration remains blocked on 03/04 authoritative per-transition source facts.
- 07 must not reconstruct intermediate event semantics from final snapshots.
- no canonical-event production PR has been created yet.
- required merge order remains 03 source facts -> 04 canonical DTO implementation -> 07 HTTP pass-through -> 06 rendering.

## NEXT_ACTION
Production P0/P1 transport and durable-store gate is operational on the new deployment. Keep the strict forced-cold-start evidence item OPEN until an intentional test can prove it without unnecessary deployment churn. For canonical event timeline work, wait for the coordinated 03/04 source contract before changing 07 production code.
