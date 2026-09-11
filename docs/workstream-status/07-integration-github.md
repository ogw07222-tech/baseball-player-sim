# 07 - Integration & GitHub

WORKSTREAM: 07 - Integration & GitHub
UPDATED_AT: 2026-09-11
TASK_START_MAIN: `f336b9be10f252300971be3d146b51ad7ff91537`
P1_INTEGRATION_BASE: `2fadd1e2295cdb42b8da70adb845c4b1fa9d9a20`
STATE: P1_UI_BACKEND_CONTRACT_VALIDATED
CURRENT_TASK: P1 UI ↔ Backend Contract Expansion
RESULT: PASS — next_game/week/month now share one typed, transactional production HTTP contract; automatic season advance remains intentionally OPEN.

## P0 BASELINE
P0 production evidence remains valid and was not reimplemented in this task:
- FastAPI production runtime: PASS
- Neon production persistence: PASS
- create career/state/next_game: PASS
- revision CAS/stale 409: PASS
- idempotency replay: PASS
- separate-client/browser reload persistence: PASS
- production HTTP provider authority: PASS
- strict forced cold-start evidence: OPEN, non-blocking for P1
- Vercel Git auto-deploy remains OFF

## CONTRACT AUDIT
Existing production transport at task start:
- `GET /api/v1/session` -> `{has_career, revision}`
- `POST /api/v1/career` -> authoritative Dashboard + Season snapshot + `meta.revision`
- `GET /api/v1/state` -> atomic authoritative Dashboard + Season snapshot + `meta.revision`
- `POST /api/v1/advance` -> transactional `expected_revision` + `idempotency_key`; only `next_game` was exposed
- `POST /api/v1/save` -> revision-checked checkpoint
- errors -> typed envelope with `error.code/message/retryable/details` and `meta.revision`

Current UI can truthfully consume player summary, abilities, season batting line, status, traits/story, progress, user team batting, revision/session state, and nullable/empty presentation collections. League-wide standings/leaderboards, next-game scouting data, and other optional datasets are still not modeled by the backend and were not fabricated.

## P1 CHANGES — PR #52
PR: #52 `P1 integration: expand UI/backend mutation contract`

### Advance response
Successful `/api/v1/advance` now returns the authoritative snapshot plus an additive mutation envelope:
- `mutation.kind = advance`
- `mutation.command`
- `mutation.result`

`mutation.result` reuses the existing `AdvanceResultViewModel` contract:
- period label/date range
- games played
- hitter/pitcher period line
- team record delta
- season total line
- notable events
- rating changes

Create/state reads remain clean snapshots and do not include a mutation result.

### Supported commands
After 03 PR #50 merged, the HTTP dispatcher exposes only proven domain methods:
- `next_game` -> `ProductionAdvanceService.advance_one_game()`
- `week` -> `ProductionAdvanceService.advance_one_week()`
- `month` -> `ProductionAdvanceService.advance_one_month()`

Automatic `season` remains rejected without mutation. 07 does not invent finalize/start-next-season semantics.

### Completed-season boundary
03 `SeasonCompleteError` is mapped to HTTP 409 `SEASON_COMPLETE`, `retryable=false`.
The error propagates out of the SessionStore transaction before update/idempotency insertion, so persisted payload and revision remain unchanged.

### DTO / transport compatibility
Frontend transport types now explicitly model:
- session
- revision metadata
- progress
- atomic snapshot
- advance mutation/result
- error envelope

The progress DTO keeps legacy optional presentation fields compatible while the current backend still sends its full canonical progress object.

### Retry / exactly-once boundary
`HttpBackendPresentationGateway` now preserves one generated idempotency key and identical serialized mutation request across one retryable transport retry. A lost response can therefore resolve through server replay rather than becoming a second logical mutation.

Merged 06 PR #51 behavior is preserved:
- typed `NETWORK_ERROR`
- typed backend conflict metadata
- authoritative revision conflict recovery at the UI layer
- required production provider injection / no implicit production mock authority
- duplicate-click mutation lock

## 03 DEPENDENCY
PR #50 `Growth/Career: P1 production advance breadth` merged before final 07 integration.

Accepted 03 contract:
- week/month are exact compositions of canonical scheduled-game advancement
- save/load deterministic equivalence is covered
- near season end stops at game 144
- completed-season game/week/month reject before mutation
- automatic season transition remains OPEN pending offseason pitcher-usage/lifecycle integration policy

07 changes only HTTP/store/presentation wiring around those methods.

## 06 DEPENDENCY
PR #51 `Web UI: production-backed career interaction hardening` merged before final 07 integration.

Current UI still intentionally exposes only Next Game. Backend `week` and `month` are now ready for 06 to expose when UX chooses to restore those controls. No 06 visual/layout files were changed by PR #52.

## VALIDATION
Final implementation head before this status-only update: `135d5618e125e2584428c1efd5846eae3e827778`
Workflow: tests run #736 (`34580368274`)

PASS:
- web install
- TypeScript/Vite production build
- web tests
- Python dependency/Vercel packaging contract
- Python compile
- external Postgres durable-store tests
- Vercel FastAPI entrypoint smoke
- API vertical-slice tests
- related production integration tests
- full Python unit suite
- auto-career smoke
- balance smoke
- high-school/draft calibration gate

Contract-specific validation covers:
- next_game mutation result payload
- week/month through the same CAS/idempotency mutation path
- exact replay response with no second revision
- restart persistence after period advances
- stale revision 409
- same idempotency key with different fingerprint conflict
- automatic season rejection with unchanged stored payload/revision
- `SEASON_COMPLETE` rollback with unchanged stored payload/revision
- atomic Dashboard + Season frontend snapshot
- retryable mutation retry reusing the same idempotency key/body
- typed backend/network error compatibility

No production deployment was consumed for this validation.

## MERGE ORDER
Completed/required order:
1. PR #50 — 03 domain breadth — MERGED
2. PR #51 — 06 production UI hardening — MERGED
3. PR #52 — 07 HTTP/DTO/transaction integration — READY TO MERGE after CI PASS

After PR #52, 06 may independently expose week/month controls against the published contract. Season UI remains blocked on a later explicit lifecycle contract.

## GATES
- P1_CONTRACT_AUDIT = PASS
- PR50_03_DOMAIN_BREADTH = PASS_MERGED
- PR51_06_UI_HARDENING = PASS_MERGED
- SESSION_STATE_DTO = PASS
- CREATE_CAREER_CONTRACT = PASS
- ADVANCE_NEXT_GAME_CONTRACT = PASS
- ADVANCE_WEEK_CONTRACT = PASS
- ADVANCE_MONTH_CONTRACT = PASS
- ADVANCE_MUTATION_RESULT_DTO = PASS
- REVISION_CAS = PASS
- IDEMPOTENCY_REPLAY = PASS
- SAME_KEY_TRANSPORT_RETRY = PASS
- STALE_REVISION_409 = PASS
- PERSISTENCE_RESTART = PASS
- SEASON_COMPLETE_ROLLBACK = PASS
- WEB_TYPE_BUILD_COMPATIBILITY = PASS
- PRODUCTION_PROVIDER_COMPATIBILITY = PASS
- AUTOMATIC_SEASON_COMMAND = OPEN
- FORCED_COLD_START_EVIDENCE = OPEN_NON_BLOCKING
- P1_UI_BACKEND_CONTRACT_EXPANSION = PASS

## NEXT_ACTION
Merge PR #52. Then hand the stable `week`/`month` transport contract to 06 for optional UI exposure. Keep automatic season advancement closed until the explicit season-finalization/offseason state contract is approved.
