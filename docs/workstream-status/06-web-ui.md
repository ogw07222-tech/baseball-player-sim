# 06 - Web UI

WORKSTREAM: 06 - Web UI
UPDATED_AT: 2026-09-12
SOURCE_OF_TRUTH: main@48011c849a813a4e8a570067670ada9e5f633836 + PR #69 `ui/interactive-event-p1`
STATE: REVIEW
CURRENT_TASK: Interactive Event UI P1 on merged backend contract
RESULT: FRONTEND PASS — production EVENT queue/resolve UI is wired to merged PR #67 contract; PR #69 awaits final repository-wide CI completion and 05 validation

## SOURCE STATE
- PR #64 Interactive Event System P1: MERGED.
- PR #66 authoritative Interactive Event effect application: MERGED.
- PR #67 Interactive Event transport and resolve API: MERGED.
- Task-start latest main: `48011c849a813a4e8a570067670ada9e5f633836`.
- Implementation PR: #69 `Web UI: Interactive Event P1 production integration`.
- No `src/` backend production logic was modified by 06.

## BACKEND CONTRACT CONSUMED
### EVENT
`pending_events: InteractiveEvent[]` is consumed as an independent player-decision domain.

`InteractiveEvent` fields consumed directly from backend:
- `event_id`, `event_type`, `category`, `title`, `description`
- `occurred_at`, `generated_at`, `season`, `game_number`
- `importance`, `trigger_context`, `choices`, `status`
- `expires_at`, `source`, `dedupe_key`, `blocking`
- `selected_choice_id`, `resolved_at`, `resolution_summary`

`InteractiveEventChoice` fields consumed directly:
- `choice_id`, `label`, `description`, `preview_effects`, `risk_level`, `requirements`

Resolve endpoint:
- `POST /api/v1/events/{event_id}/resolve`
- request: `choice_id`, `expected_revision`, `idempotency_key`
- response mutation kind: `resolve_event`
- response result: `resolved_event`, `applied_effects`, `resolution`, `pending_events`

### CAREER
`notable_events: CanonicalEventDTO[]` remains a separate automatic-history domain.
It is never merged into `pending_events` and is rendered only as a recent CAREER summary after an advance response.

## SEASON HUB INTEGRATION
- Session/state load reads authoritative `pending_events` through the existing production provider/gateway.
- Season navigation shows a `결정 필요 N` badge when pending EVENTs exist.
- Season Hub embeds the current EVENT decision panel above the existing Season screen.
- Advance responses from `next_game`, `week`, and `month` update pending EVENT state directly from the backend response.
- If an advance produces pending EVENTs, UI moves to Season Hub so the decision is immediately visible.
- Automatic season advance is not exposed because the merged backend still rejects that command.

## EVENT PRESENTATION
- Sports-data panel; no modal spam or RPG dialogue styling.
- Displays category, importance, title, description, season/game/time context, trigger context and choices.
- `importance` changes visual emphasis only.
- Choice preview mapper translates backend semantic labels only; it does not invent rating deltas or hidden effect values.
- Backend-provided `duration` and `games_remaining` are shown when present.

## MULTIPLE EVENT QUEUE
- Supports 0 / 1 / N pending EVENTs.
- Queue order is the backend array order; frontend does not sort.
- Shows `결정 1 / N`.
- Successful resolution replaces the pending list with the backend-returned list and displays the next first item.

## RESOLVE FLOW
choice click -> shared mutation lock -> choice buttons disabled/loading -> production resolve API -> authoritative response applied -> resolution summary shown -> remaining pending queue shown.

No client-generated event IDs, client-side effect mutation, optimistic permanent state, or local resolved-state authority is used.

## REVISION / IDEMPOTENCY
- Resolve and advance mutations use the gateway-owned current authoritative revision.
- Resolve sends `expected_revision` and a generated `idempotency_key`.
- Retryable network transport retry reuses the exact serialized request body, therefore the same idempotency key.
- Resolve response revision becomes the revision for the next mutation.
- Resolved mutation snapshots are consumed after success so later authoritative refreshes cannot accidentally reuse stale cached resolve data.
- `REVISION_CONFLICT` triggers a new `/state` read and replaces Dashboard, Season and pending EVENT state.

## ERROR STATES
Explicit EVENT UI handling:
- `NETWORK_ERROR`: connection message; pending EVENT remains.
- `REVISION_CONFLICT`: authoritative state reload.
- `INVALID_EVENT_CHOICE`: invalid-choice message.
- `EVENT_ALREADY_RESOLVED`: authoritative reload; stale EVENT disappears only if server says it is gone.
- `EVENT_NOT_FOUND`: authoritative reload.
- `SIMULATION_CONFLICT`: authoritative reload.
- no pending EVENT: explicit empty state.

## UNSUPPORTED EFFECT
`UNSUPPORTED_EVENT_EFFECT` is shown as:
`현재 이 선택은 아직 지원되지 않습니다. 다른 선택지를 사용해 주세요.`
The EVENT is not removed or treated as successful.

## RESPONSIVE
- EVENT choices collapse to one column on tablet/mobile widths.
- Choice buttons retain >=46px target height on narrow layout.
- Long context/preview text wraps rather than overflowing.
- Advance controls collapse vertically at mobile width.

## FILES CHANGED
- `web/src/App.tsx`
- `web/src/InteractiveEventUi.test.tsx` (new)
- `web/src/components/InteractiveEventPanel.tsx` (new)
- `web/src/interactiveEvent.css` (new)
- `web/src/main.tsx`
- `web/src/screens/PlayerDashboard.tsx`
- `web/src/services/GameDataProvider.ts`
- `web/src/services/GameDataProvider.test.ts`
- `web/src/services/HttpBackendPresentationGateway.ts`
- `web/src/services/HttpBackendPresentationGateway.test.ts`
- `web/src/services/InteractiveEventRevision.test.ts` (new)
- `web/src/types/backendPresentation.ts`
- `docs/workstream-status/06-web-ui.md`

## TESTS
PR #69 workflow run #984 on code head `895bfce6770e3cbfe527642a00fb136ddb989321`:
- Web install: PASS
- Web build: PASS
- Web tests: PASS
- Vercel Python packaging: PASS
- Python compile: PASS
- external durable-store tests: PASS
- FastAPI entrypoint smoke: PASS
- API vertical-slice tests: PASS
- related production integration tests: PASS
- full repository Python unit/regression tail: still running when this status file was finalized

Frontend coverage includes:
- no pending EVENT
- one pending EVENT
- multiple EVENT canonical order
- choice/preview/risk/requirements/context rendering
- resolve success and backend resolution summary
- duplicate-click prevention
- same-idempotency-key network retry
- revision update after resolve
- stale revision authoritative reload
- unsupported effect
- already resolved
- network failure
- pending count update / next EVENT
- EVENT / CAREER separation
- merged next-game/week/month controls, no season auto-advance
- narrow-layout smoke

## GATES
- EVENT_RENDERING = PASS
- MULTIPLE_EVENTS = PASS
- RESOLVE_FLOW = PASS
- DUPLICATE_CLICK = PASS
- REVISION_HANDLING = PASS
- IDEMPOTENCY = PASS
- UNSUPPORTED_EFFECT = PASS
- CAREER_EVENT_SEPARATION = PASS
- RESPONSIVE = PASS
- FRONTEND_TESTS = PASS
- PRODUCTION_BUILD = PASS
- BACKEND_EVENT_TRANSPORT_REGRESSION = PASS
- FULL_REPOSITORY_CI = REVIEW

## READY FOR 05 FINAL VALIDATION
NO — frontend implementation/build/tests and EVENT transport regressions are green, but PR #69's full repository CI tail must finish before 06 hands the branch to 05 as final-validation-ready.

## NEXT ACTION
- Do not expand EVENT catalog/frequency/effect semantics in 06.
- When PR #69 full CI is GREEN, hand the exact PR head to 05 for final validation.
- Any backend semantic mismatch goes to 07/03/04 rather than being reconstructed in frontend.
