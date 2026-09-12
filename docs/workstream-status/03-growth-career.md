# 03 - Growth & Career

WORKSTREAM: 03 - Growth & Career
UPDATED_AT: 2026-09-12
TASK_START_MAIN: 3a4fc58a3c56d9042561494a08a676762fb4661d
STATE: NEXTGEN_CAREER_SOURCE_FACTS_IMPLEMENTED
CURRENT_TASK: Expand authoritative career source facts for next-generation event/story system
RESULT: PASS_WITH_PREEXISTING_REPO_CI_BLOCKER
BRANCH: feature/p1-nextgen-career-source-facts
PR: #63 Growth/Career: expand authoritative milestone award retirement facts
CODE_HEAD: 62c28b9c5afe9bb6870450c4699186158afbfc95

## SOURCE_STATE
- Latest main at task start and final recheck: `3a4fc58a3c56d9042561494a08a676762fb4661d`.
- Existing CareerSourceFact contract and deterministic coordinates remain unchanged.
- Existing fact coverage before this task: roster promotion/demotion, first-team debut, injury/recovery/change, form transition, Trait gain/loss, event rating change, season growth, season finalized.
- Source facts remain presentation-free and are emitted at authoritative mutation points.

## NEW_FACT_TYPES
### `career_milestone_reached`
Supported authoritative KBO first-team batting milestone keys:
- `career_first_hit`
- `career_first_home_run`
- `career_first_rbi`
- `career_hits_100`
- `career_hits_500`
- `career_hits_1000`
- `career_home_runs_100`

Milestones are emitted exactly at the first-team counting-stat mutation using `before < threshold <= after`. FARM stats are not included. The same threshold hook is used in both production full-game advance and headless CareerEngine season advance.

### `award_granted`
The existing KBO season award authority `_determine_awards()` already decides and persists:
- 타격왕
- 홈런왕
- 타점왕
- 도루왕
- 골든글러브
- MVP

Each actually granted award emits `award_granted` when the existing `player.awards` durable row is appended. No award algorithm was added or tuned.

### `career_retired`
The existing retirement mutation now emits one fact when phase/roster/retirement_age actually transition to RETIRED. `state_delta.retirement_reason` records the factual caller path (`retirement_rule`, `max_seasons_guard`, or explicit). Repeated `retire()` after already retired is a no-op and emits nothing.

## MILESTONE_SUPPORT
PASS for exact first-team batting counting-stat milestones listed above.
OPEN / unsupported because current production does not have authoritative state for:
- user pitcher career W/SV milestone accumulation
- hitting streak milestone state
- a canonical personal-best transition/history event

`Player.best_season()` is a derived query, not an authoritative mutation event, so no personal-best source fact was invented.

## AWARD_SUPPORT
PASS for the existing KBO award calculation/output listed above.
OPEN for awards without existing authority, including rookie award and Best Nine-style awards.
High-school tournament MVP exists in legacy tournament flow but was not expanded in this production-career batch.

## TEAM_MOVEMENT_SUPPORT
OPEN. No production trade, release, contract lifecycle, FA, posting, or team-transfer semantics exist. No source facts were fabricated.
Initial draft team assignment remains existing draft/pro-entry history semantics and is unchanged.

## RETIREMENT_SUPPORT
PASS.
Existing `should_retire()` decision semantics remain unchanged. Existing state mutation in `retire()` now emits `career_retired` exactly once and preserves final `phase=RETIRED`, `roster_level=RETIRED`, and `retirement_age` in the normal save state.

## DEDUPE / PERSISTENCE
- Milestones create no duplicate durable milestone history. Exact-once derives from the persisted authoritative counting stat crossing the threshold; after save/load the threshold remains passed.
- Awards reuse existing `player.awards` durable identity via `existing_history_kind='player.awards'` and `existing_dedupe_key='awards:<year>:<index>'`.
- Retirement creates no second retirement history store; the normal persistent career state is the durable truth.
- Existing history/dedupe behavior for older source facts remains unchanged.

## ORDERING
Existing ordering contract remains:
`simulated_date -> game_number -> phase -> local_ordinal`.

Milestones are emitted immediately after the actual FIRST batting-line mutation and before later postgame injury/form/roster transitions. Multiple thresholds crossed by one game all remain as distinct facts in deterministic declaration/local-ordinal order. Week/month composition preserves internal game execution order; no last-event-wins behavior is introduced.

## DETERMINISM / SAVE_LOAD
- No new source-fact RNG was introduced.
- same seed + same state + same actions => same milestone/source-fact sequence.
- save/load then same action => same source facts, terminal serialized state, and RNG state in targeted validation.
- threshold crossing prevents replay duplicates after persisted state has passed a milestone.

## 04 COMPATIBILITY
03 did not add narrative mapping for the new fact types.
`AdvanceSummary.source_facts` remains lossless. The current legacy `canonical_timeline_for_advance()` projection now projects only fact types already known to 04 so additive 03 fact vocabulary cannot crash existing API/UI presentation. `canonical_event_from_source_fact()` remains strict. 04 still owns new CanonicalEventDTO category/title/summary/importance/retention mapping.

## TESTS
New `tests/test_nextgen_career_source_facts.py` covers:
- first H/HR/RBI milestones exact once, including multiple milestones in one game
- H 99->101 and HR 99->100 threshold crossing without skipped/duplicate facts
- month aggregation preserves career_hits_100 and deterministic coordinates
- save/load + same-seed/action fact/state/RNG equivalence
- award facts at authoritative finalization and existing award persistence
- retirement fact exact once
- unsupported team movement semantics produce no fabricated facts

Existing season lifecycle tests continue to cover season growth/finalization transition semantics.
API vertical slice and related production integration tests pass after additive-fact compatibility guarding.

## CI / BASELINE BLOCKER
Branch validation on run `34665058563` after compatibility fix:
- packaging/compile = PASS
- external durable store = PASS
- FastAPI entrypoint = PASS
- API vertical slice = PASS
- related production integration = PASS
- all 7 new next-generation source-fact tests = PASS
- full discovery had one unrelated failure: `test_balance_v04.BalanceV04Tests.test_draft_distribution_not_extreme`.

Task-start main `3a4fc58...` workflow run `34664821095` fails the exact same test with the exact same deterministic undrafted rate `0.056666666666666664` versus legacy `> 0.10` assertion. Therefore this is a pre-existing main baseline blocker, not caused by this source-fact PR. 03 does not tune draft/rating/gameplay to hide it.

Latest code head `62c28b9c5afe9bb6870450c4699186158afbfc95` again passes compile, external store, API vertical slice, and production integration before reaching the same inherited full-suite blocker.

## EXACT_04_HANDOFF
04 may now normalize these additional authoritative facts:
- `career_milestone_reached`: read `state_delta.milestone_key`, `stat`, `previous_value`, `milestone_value`, `current_value`.
- `award_granted`: read `state_delta.award_key` and reuse `existing_history_kind/existing_dedupe_key`.
- `career_retired`: read before/after career states plus `state_delta.retirement_reason` and `retirement_age`.

04 must not infer these from period-end snapshots, must not create simulation RNG, and must preserve existing source ordering/dedupe coordinates. Current production projection intentionally leaves these unmapped until 04 adds presentation semantics.

## UNSUPPORTED_SEMANTICS
Not invented:
- pitcher first win/save or pitcher counting milestones
- streak milestones
- personal-best event semantics
- rookie award / Best Nine where no authority exists
- trade / release
- contract signing / salary / service time
- FA / posting
- team transfer
- rivalry narrative
- full Futures/minor-league simulation

## GATES
- SOURCE_FACT_CONTRACT = PASS
- MILESTONE_FACTS = PASS
- AWARD_FACTS = PASS
- TEAM_MOVEMENT_FACTS = OPEN
- RETIREMENT_FACTS = PASS
- EXACT_ONCE = PASS
- ORDERING = PASS
- DETERMINISM = PASS
- SAVE_LOAD_EQUIVALENCE = PASS
- 04_NEW_FACT_NORMALIZATION = OPEN
- REPO_GLOBAL_CI = BLOCKED_BY_PREEXISTING_DRAFT_DISTRIBUTION_BASELINE

## READY_FOR_04
YES. Authoritative facts exist; 04 presentation/normalization for the three new fact types is the next owner action.
