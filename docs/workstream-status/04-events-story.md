# 04 - Events & Story

WORKSTREAM: 04 - Events & Story
UPDATED_AT: 2026-09-12
SOURCE_OF_TRUTH: `main@3a4fc58a3c56d9042561494a08a676762fb4661d`
STATE: ACTIVE
CURRENT_TASK: Interactive Event System P1 — diversified mid-season decision events
IMPLEMENTATION_BRANCH: `feature/interactive-event-system-p1`
IMPLEMENTATION_PR: #64 `Events: Interactive Event System P1`
VALIDATED_CODE_HEAD: `fc9d71b627cf2107f077806b1218778f039e8a59`
VALIDATION_RUN: GitHub Actions #936 / `34665918451`
RESULT: PASS_WITH_PREEXISTING_DRAFT_BALANCE_CI_BLOCKER

## TERMINOLOGY
Project terminology is now explicit:
- **EVENT / 이벤트** = player-facing interactive decision event with choices.
- **CAREER / 커리어** = automatic factual career timeline record such as debut, injury, record, award, roster move, growth/lifecycle fact.

`CareerSourceFact -> CanonicalEventDTO` is therefore treated as the **Career Timeline / Career Records** layer and is not the interactive EVENT domain.

## CURRENT_GITHUB_STATE
- PR #54 03 CareerSourceFact: MERGED.
- PR #56 CanonicalEventDTO v1: MERGED.
- PR #57 canonical event HTTP/frontend transport: MERGED.
- PR #62 deterministic CanonicalEventDTO presentation v2: OPEN / mergeable; this is CAREER presentation work, not interactive EVENT work.
- PR #64 Interactive Event System P1: OPEN / mergeable at latest implementation checkpoint.
- Latest observed main at task start and final re-check: `3a4fc58a3c56d9042561494a08a676762fb4661d`.

## EVENT_SCHEMA_P1
New `src/interactive_events.py` owns the interactive EVENT contract.

`InteractiveEvent`:
- deterministic `event_id`
- `event_type`
- `category`
- `title`
- `description`
- `occurred_at`
- `generated_at`
- `season`
- `game_number`
- `importance`
- `trigger_context`
- `choices[]`
- `status`: `pending | resolved | expired`
- optional `expires_at`
- `source`
- deterministic `dedupe_key`
- `blocking` metadata
- resolved-only `selected_choice_id`, `resolved_at`, `resolution_summary`

`InteractiveEventChoice`:
- `choice_id`
- `label`
- `description`
- `preview_effects[]`
- optional `risk_level`
- optional `requirements`

`EventChoiceEffect` is declarative only:
- `effect_type`
- `target`
- `magnitude`
- optional `duration`
- metadata

04 does not execute these requests against Player/Career state.

## GENERATION_PIPELINE
Production path after PR #64:
`simulation game -> committed postgame state -> eligibility evaluation -> deterministic EVENT opportunity -> pending InteractiveEvent`.

Generation is wired per constituent game in `CareerGameAdvanceProvider`, so:
- `next_game`
- `week`
- `month`
all preserve the exact game/date where an EVENT occurred.

The period does not wait at its end and then invent one random event.

P1 pending policy is non-blocking. A week/month continues after an EVENT is generated, up to the configured pending cap.

The canonical production provider no longer auto-resolves the legacy v0.4 `CareerEvent` choice path. Legacy code remains for compatibility/testing outside this new P1 domain, but it is not the new production EVENT contract.

## INITIAL_EVENT_CATALOG
P1 has 10 archetypes across six categories:

TRAINING
- `batting_training_intensity`
- `defense_training_focus`
- `weakness_focus`

FORM
- `slump_response`
- `hot_streak_routine`

COACH
- `coach_method_trial`

TEAM ROLE
- `role_competition`
- `position_practice`

MEDIA
- `media_interview`

RECOVERY
- `fatigue_management`

Each EVENT has 2-3 choices. Choices are designed as trade-offs rather than direct correct/incorrect answers: development upside vs fatigue cost, specialization vs versatility/opportunity cost, stability vs variance, recovery vs development opportunity.

## EFFECT_AUTHORITY
04 owns only the request vocabulary. Current effect request families:
- `training_focus`
- `fatigue_modifier`
- `form_modifier`
- `development_modifier`
- `temporary_trait_request`

04 never performs `rating += X`, `form = Y`, fatigue mutation, injury mutation, or Trait mutation from the new EVENT layer.

Resolution returns `InteractiveEventResolution.effects[]`; 03 must own any future authoritative interpretation/application.

If an applied effect creates a CAREER-worthy factual transition, 03 should emit the corresponding `CareerSourceFact`; that later flows independently into Career Timeline / Career Records.

## RNG_CONTRACT
EVENT occurrence/selection uses a deterministic SHA-256-derived child stream keyed by:
- canonical seed
- season
- exact game number
- namespace / event type

It does not call or advance the canonical simulation RNG.

Rendering and choices are static deterministic catalog data and consume no RNG.

Validated contract:
`same save + seed + action sequence -> same EVENT occurrence coordinates and same choices`.

## FREQUENCY_CONTROL
P1 generic controls:
- per-game deterministic opportunity gate: default 4%
- global season EVENT cap: default 6
- max pending EVENT count: default 3
- per-event cooldown: default 32 games
- category cooldown: default 18 games
- per-archetype season cap
- once-per-season hook
- once-per-career hook
- form/fatigue/level/position/game-window eligibility hooks

Season-scoped cooldown/count maps reset when a new season starts. EVENT history remains, preserving a future once-per-career authority basis.

These are structural defaults, not final balance targets. Exact frequency tuning belongs to 05.

## PENDING_AND_RESOLUTION
Default P1 EVENTs are `blocking=False`.

Generation:
`none -> pending`

Choice selection:
`pending -> resolved`

Resolved EVENT record retains:
- selected choice id
- resolved timestamp
- deterministic resolution summary
- original choices / trigger context / generation coordinate

Invalid choice is rejected.
A resolved EVENT cannot resolve twice.

Resolution produces effect requests only and mutates no Player/Career simulation state.

## PERSISTENCE
`InteractiveEventState` is additive in canonical save payload as `interactive_event_state`.

It persists:
- pending/resolved EVENT records
- event cooldown state
- category cooldown state
- occurrence counters

Old saves without the field load cleanly with an empty InteractiveEventState.
Simulation RNG state is serialized independently and is not changed by EVENT generation/resolution.

## CAREER_SEPARATION
Interactive EVENT types are not `CanonicalEventDTO` and do not contain Career Timeline fields such as `sequence` or `state_effects`.

CAREER remains:
`03 CareerSourceFact / authoritative gameplay marker -> CanonicalEventDTO -> transport -> UI timeline`.

EVENT remains:
`eligibility -> InteractiveEvent pending -> player choice -> EventChoiceEffect request -> 03 authority`.

No automatic CAREER fact is fabricated by 04 when an EVENT resolves.

## 03_HANDOFF
03 should define the authoritative interpreter/application transaction for `EventChoiceEffect` requests.

Required contract:
- validate target/effect type/magnitude class
- apply effect atomically with EVENT resolution command
- own any actual state mutation
- emit CareerSourceFact only when an authoritative resulting transition is Career Timeline-worthy
- reject unsupported effect requests rather than silently reinterpret them

P1 04 does not prescribe rating-point values or growth formula coefficients.

## 07_HANDOFF
07 can expose without reconstructing EVENT semantics:
- current pending InteractiveEvent[]
- newly generated events for the mutation response
- resolve command carrying deterministic `event_id + choice_id`
- returned declarative effect request / later 03 authoritative result

Existing Career Timeline `notable_events: CanonicalEventDTO[]` should remain a separate transport field/domain. Do not merge EVENT choices into CanonicalEventDTO.

## VALIDATION
Exact code/test checkpoint: `fc9d71b627cf2107f077806b1218778f039e8a59`.
GitHub Actions: run #936 / `34665918451`.

PASS before full-suite legacy blocker:
- web build/tests
- Python dependency/package validation
- compile
- PostgreSQL durable-store tests
- Vercel FastAPI entrypoint smoke
- API vertical-slice tests
- related production integration tests
- all new Interactive Event P1 tests
- legacy v0.4 event-flow tests
- CareerSourceFact / CanonicalEventDTO tests
- production week/month composition and save/load regressions

New P1 tests cover:
- 10 diversified archetypes / six categories / 2-3 choices each
- eligible EVENT generated
- ineligible EVENT excluded
- same seed deterministic / byte-stable event data
- no canonical RNG consumption
- event cooldown
- duplicate prevention
- season cap
- multiple categories
- pending -> resolved
- invalid choice rejection
- double resolution rejection
- generation/resolution do not mutate player state
- InteractiveEvent is not CanonicalEventDTO
- next_game occurrence coordinate
- week/month non-blocking continuation + exact occurrence coordinate
- pending/resolved save-load roundtrip
- old save without interactive event state compatibility
- new-season season-control reset while retaining EVENT history

Repository-wide unit step still FAILS only on the pre-existing unrelated legacy balance test:
`test_balance_v04.BalanceV04Tests.test_draft_distribution_not_extreme`
with deterministic undrafted rate `0.056666666666666664` versus stale assertion `> 0.10`.
The same exact failure existed before this P1 branch on the main-producing PR #61 and PR #62 validation. 04 must not alter draft tuning to satisfy it.
Downstream workflow steps after the full-unit command are skipped because that legacy gate exits non-zero.

## OPEN / NON-SCOPE
- 03 authoritative effect application: OPEN
- 07 API/transport commands and response typing: OPEN
- 06 EVENT UI: OPEN
- final frequency calibration: OPEN_05
- relationship/rivalry systems: out of P1
- contract/FA gameplay: out of P1
- LLM prose: prohibited in P1
- large event catalog expansion: later batch
- expiration behavior exists in schema but automatic expiry policy is not enabled in P1

## GATES
- INTERACTIVE_EVENT_SCHEMA = PASS
- MIDSEASON_GENERATION = PASS
- DETERMINISM = PASS
- DEDUPE = PASS
- CHOICE_RESOLUTION_CONTRACT = PASS
- CAREER_EVENT_SEPARATION = PASS
- SAVE_LOAD_PERSISTENCE = PASS
- P1_TARGETED_AND_INTEGRATION_VALIDATION = PASS
- REPOSITORY_FULL_CI = OPEN_PREEXISTING_DRAFT_BALANCE_GATE
- READY_FOR_03_07 = YES
