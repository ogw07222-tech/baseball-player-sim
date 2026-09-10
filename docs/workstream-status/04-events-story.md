# 04 - Events & Story

WORKSTREAM: 04 - Events & Story
UPDATED_AT: 2026-09-10
SOURCE_OF_TRUTH: main@4fa27947a72853ff17eeb373c8f0082341f40d02
STATE: ACTIVE
CURRENT_TASK: Draft / Entry / First-Team Debut Career Spine v1 implementation
RESULT: PASS_WITH_OPEN_INTEGRATION

## LAST_COMPLETED
- Implemented bounded observational/system-mirror career spine on `feature/career-spine-v1` / PR #39.
- Added append-only `Player.career_history` with backward-compatible default `[]`.
- Added typed schema v1 and deterministic template news in `src/career_story.py`.
- Implemented `draft_selected`, `draft_undrafted_entry`, `pro_entry`, `first_team_callup`, `first_team_debut`, and `farm_demotion`.
- Rebased the unchanged feature tree onto current latest main after concurrent docs/research-only main advances.
- CI run #610 on the validated code tree passed Python unit tests, Auto career smoke, Balance smoke, high-school/draft calibration gate, artifact upload, web build, and web tests.

## HISTORY_SCHEMA
`CareerHistoryEntry` v1 is append-only and contains:
- `schema_version`
- `event_id`, `event_type=system_mirror`
- `year`, `age`, `career_stage`, `kind`, `importance`
- `dedupe_key`, `trigger`, `eligibility`, `repeat_contract`
- `team`, `game_number`
- `facts`
- `news` (`template_key`, `headline`, `body`)
- `effects=[]`
- `source_owner=03-growth-career`
- `observer_owner=04-events-story`

Repeat contracts:
- `career_once`: draft result, pro entry, first-team debut.
- `transition_repeat`: first-team call-up and farm demotion; duplicate transition keys are suppressed deterministically.

## IMPLEMENTED_CONTRACTS
- `draft_selected`: authoritative selected draft result -> career-once history/news, zero simulation effect.
- `draft_undrafted_entry`: authoritative undrafted-entry result -> career-once history/news, zero simulation effect.
- `pro_entry`: authoritative team assignment/FARM entry -> career-once history/news, zero simulation effect.
- `first_team_callup`: FARM -> FIRST authoritative transition -> repeatable history/news, year/game/from/to dedupe.
- `first_team_debut`: first actual FIRST-team game appearance -> career-once history/news.
- `farm_demotion`: FIRST -> FARM authoritative transition -> repeatable history/news, year/game/from/to dedupe.

## HOOKS
- `CareerEngine.evaluate_draft()` observes the completed `CareerEngineBase.evaluate_draft()` transition.
- `CareerEngine.start_pro_season()` observes authoritative season-start FARM/FIRST assignment changes.
- `CareerEngine._reconsider_roster()` records before/after levels around existing roster logic.
- Debut detection uses actual FIRST-team appearance (`first_team.G == 1`) plus zero completed-career FIRST-team games; it does not rely on `debut_year` alone.

## RNG_AND_MUTATION
- `render_career_news()` accepts no RNG.
- `record_observational_event()` accepts no RNG.
- All new history entries use `effects=[]`.
- No rating/stat, gameplay probability, growth, fatigue, injury, form, Trait, or roster-decision formula is mutated by this layer.
- Broader v0.4 systems still share their pre-existing RNG stream; this new observational/news path is RNG-free.

## VALIDATION
CI run #610 on feature code tree `2d31a3d59ebe305f9f639b81be3334260e7a61fa`:
- Python full unit suite = PASS
- Existing v0.4 event tests = PASS as part of full unit suite
- Career Spine v1 targeted tests = PASS as part of full unit suite
- Auto career smoke = PASS
- Balance smoke = PASS
- High-school / draft calibration gate = PASS
- Draft calibration artifact upload = PASS
- Web build/tests = PASS

Targeted coverage includes:
- draft result exactly once
- pro entry exactly once
- debut exactly once
- callup/demotion mirror authoritative transitions
- duplicate transition suppression
- save/load history equality
- old-save missing `career_history` -> `[]`
- same seed/actions identical history
- auto/interactive factual history equality
- zero gameplay mutation
- RNG-free deterministic template rendering

## BACKWARD_COMPATIBILITY
- Existing `event_history` is unchanged.
- Existing team/award/injury/Trait histories are unchanged.
- `career_history` is additive; old saves load it as `[]`.
- No hard save migration is required.
- Existing v0.4 pending-event/cooldown/once-per-season semantics are not rewritten.

## OWNERSHIP
- 03 Growth & Career: draft/team/FARM/FIRST/lifecycle authoritative state.
- 04 Events & Story: observational history, deterministic dedupe, template news.
- 01 Gameplay Engine: gameplay probabilities/outcomes remain untouched.
- 06 Web UI: consume structured history/news only; no narrative trigger logic in frontend.
- 07 Integration & GitHub: merge/integration regression for PR #39.

## OPEN_ITEMS
- PR #39 production merge/integration.
- 06 presentation wiring for `career_history`.
- Contract/FA/transfer narrative remains blocked on future 03 authoritative states.
- Full subsystem RNG separation remains outside this bounded batch.

## NEXT_ACTION
- After PR #39 integration, implement `Award / Milestone News Spine v1` using the same authoritative-state -> observational history -> RNG-free template-news pattern.

## RELATED_PRS
- #39 — Add Draft / Entry / First-Team Debut Career Spine v1

## RELATED_BRANCHES
- `feature/career-spine-v1`
- `main`

## GATES
- EVENT_SYSTEM_AUDIT = PASS_WITH_GAPS
- CAREER_SPINE_SCHEMA = PASS
- CAREER_SPINE_IMPLEMENTATION = PASS
- ZERO_GAMEPLAY_MUTATION = PASS
- CAREER_SPINE_BACKCOMPAT = PASS
- CAREER_SPINE_FINAL_CI = PASS
- CONTRACT_FA_STORY = BLOCKED_ON_03
- NARRATIVE_RNG_ISOLATION = PARTIAL
