# 04 - Events & Story

WORKSTREAM: 04 - Events & Story
UPDATED_AT: 2026-09-10
SOURCE_OF_TRUTH: main@e642fa2545bdc05ad8cc2b363b7bd199173409b1
STATE: ACTIVE
CURRENT_TASK: First production narrative/event expansion batch selection
RESULT: PARTIAL

## LAST_COMPLETED
- Re-audited latest main event scheduler, eligibility, cooldown, once-per-season, pending choice/auto flow, temporary/seasonal modifiers, permanent effects, injury/breakthrough events, Traits, career histories, save/load, and deterministic-seed tests.
- Confirmed the existing v0.4 scheduler is usable as a production prototype foundation, but narrative coverage is concentrated in PRO in-season training/performance/breakthrough events.
- Selected the first bounded production expansion theme: Draft / Entry / First-Team Debut Career Spine.

## CURRENT_FINDINGS
- Scheduler controls are functional: pending events, once-per-season, career-once, event cooldowns, global minimum gap, phase gates, weighted eligibility, interactive choice, and auto choice are implemented.
- `temporary_ranges` are actually season-long modifiers cleared at season end; there is no generic games/days/until-state-change temporary-effect contract yet.
- Event outcomes can directly mutate permanent ratings, season modifiers, growth modifiers, injury, fatigue, form, and Traits. Large breakthrough events therefore remain too tightly coupled to simulation state ownership for further expansion.
- Injury, awards, draft, roster transitions, debut year, coach changes, Trait history, team history, and event history exist as separate records rather than one unified narrative ledger/news pipeline.
- Same-code same-seed behavior is covered, including save/load RNG-state preservation, but all systems currently share one RNG stream; narrative-only RNG isolation remains open.
- Trait catalog supports positive/negative polarity only; Trait lifecycle changes at season end can occur without a causal narrative event.
- No production contract/FA/transfer state owner was identified in the audited core flow, so those story stages remain blocked on 03 Growth & Career ownership.

## CAREER_COVERAGE
- High school: PARTIAL — tournaments/MVP simulated, no general narrative event/news spine.
- Draft: PARTIAL — draft result persisted, no first-class history/news event contract.
- Entry: PARTIAL — team assignment/team_history exists, no structured career story output.
- Farm: PARTIAL — FARM gameplay and farm-development event exist, but roster/story transitions are not logged uniformly.
- First-team debut: PARTIAL — debut_year is set, but no dedicated debut event/news/history entry.
- Role competition: PARTIAL — roster reconsideration exists, no promotion/demotion story contract.
- Slump: PARTIAL — form state and slump-response event exist, but trigger is not performance-history-derived narrative.
- Breakout: PARTIAL — breakthrough events exist but often create the state via direct +stat effects instead of observing simulation results.
- Injury: PARTIAL — injuries and injury events exist, histories are separate and recovery causality is weak.
- Return: PARTIAL — injury-return choice event exists, but generic recovery completion is not a unified story signal.
- Awards: PARTIAL — awards are calculated/persisted, but award news/history integration is missing.
- Contract: MISSING — production state owner not found in audited core flow.
- Transfer: MISSING — production state owner not found in audited core flow.
- Late career: PARTIAL — aging/retirement probability exists, little narrative support.
- Retirement: PARTIAL — retirement state exists, no retirement story/news entry.

## SELECTED_NEXT_BATCH
### Draft / Entry / First-Team Debut Career Spine
Reason:
- Largest early-career narrative gap with already-existing authoritative simulation state.
- Minimal gameplay-formula risk and minimal arbitrary stat mutation.
- Establishes reusable observational/system-mirror event contracts before deeper slump/breakout or injury redesign.
- Provides an end-to-end pattern for 03-owned state -> 04 history/news -> 06 presentation -> 07 persistence/integration.

Initial contracts:
1. `draft_selected` / `draft_undrafted_entry`
   - Trigger: successful `evaluate_draft()` state transition.
   - Eligibility: HIGH_SCHOOL -> PRO only; career-once.
   - Probability: 1.0 system event; no scheduler random roll.
   - Choices: none in first batch.
   - Effects: none on ratings/gameplay; mirror authoritative draft/team state only.
   - Duration: instant.
   - Cooldown/repeat: career-once, deterministic dedupe key by career + draft year.
   - Output: structured history entry + template news.
2. `pro_entry`
   - Trigger: team assignment / roster_level becomes FARM after draft.
   - Eligibility: drafted or undrafted-entry player with team set; career-once.
   - Probability: 1.0 system event.
   - Choices/effects: none; observational only.
   - Duration: instant.
   - Output: entry/team history and template news; may merge with draft entry at presentation layer but remains separate fact.
3. `first_team_callup`
   - Trigger: FARM -> FIRST authoritative roster transition from career system.
   - Eligibility: current level FARM, resulting level FIRST.
   - Probability: 1.0 after transition; no additional random roll.
   - Choices/effects: none in first batch.
   - Duration: instant.
   - Cooldown/repeat: repeatable across seasons, dedupe same transition/game; optional news importance reduced after first career call-up.
   - Output: history entry + call-up news.
4. `first_team_debut`
   - Trigger: first actual FIRST-level game appearance, not merely roster promotion.
   - Eligibility: debut_year unset before appearance / no prior debut ledger entry.
   - Probability: 1.0 career-once.
   - Choices/effects: none; no rating/gameplay mutation.
   - Duration: instant.
   - Output: high-importance career history entry + debut news.
5. `farm_demotion`
   - Trigger: FIRST -> FARM authoritative roster transition.
   - Eligibility: actual roster transition only.
   - Probability: 1.0 mirror event.
   - Choices/effects: none in first batch.
   - Cooldown/repeat: repeatable; dedupe identical transition/game, presentation suppression for excessive churn.
   - Output: history entry; news importance depends on established status/career PA.

## EFFECT_OWNERSHIP
- 03 Growth & Career owns draft/career progression, roster assignment, future contract/FA/team move, aging and retirement state.
- 04 Events & Story owns observational event definitions, dedupe/cooldown/presentation importance, structured history/news facts, and optional later choices that call explicit 03 commands rather than mutating 03 state directly.
- 01 Gameplay Engine remains owner of gameplay probability/outcomes; this batch must not change gameplay formulas.

## DEPENDENCIES
- 03: expose/confirm authoritative draft completion, FARM<->FIRST transition, actual first-team appearance, future contract/FA/team-change hooks.
- 06: consume structured career history/news entries; no narrative logic in frontend.
- 07: persistence/migration wiring and integration regression; preserve old saves and deterministic resume.
- 00: approve career-spine importance/news frequency policy if cross-system design changes are needed.

## VALIDATION_REQUIREMENTS
- Draft/entry/debut system events never mutate player ratings, gameplay probabilities, growth, injury, fatigue, form, or Traits.
- Exactly one draft result and one first-team debut entry per career.
- Call-up/demotion entries correspond exactly to authoritative roster transitions and do not duplicate at the same game/year.
- Save/load before and after any spine event yields identical subsequent state/history.
- Same seed + same actions yields identical structured career-spine history.
- Generating template news must consume no gameplay RNG and ideally no shared simulation RNG.
- Auto and interactive progression produce identical factual spine events when underlying simulation state is identical.
- Existing v0.4 event-flow tests remain green.

## BLOCKERS
- Generic contract/FA/transfer narrative remains blocked until 03 owns and exposes those states.
- True temporary-duration effects and breakthrough ownership cleanup should be handled in a later contract batch, not mixed into this first expansion.
- Unified CareerLedger schema is recommended but may be introduced minimally for this batch if 07 confirms backward-compatible persistence strategy.

## OPEN_ITEMS
- Decide whether the first implementation introduces a small append-only `CareerHistoryEntry`/ledger now or adapts `event_history` with a typed observational entry while preserving migration simplicity.
- Define stable template keys and facts payload for 06 without frontend coupling.
- Define subsystem RNG policy; at minimum template rendering must be deterministic without advancing gameplay RNG.
- Later batches: award/milestone mirror events, injury/recovery narrative depth, performance-derived slump/breakout, Trait lifecycle causality.

## NEXT_ACTION
- Prepare a bounded implementation task for `Draft / Entry / First-Team Debut Career Spine`: add typed observational/system-mirror history contracts, hook them to existing authoritative transitions, add deterministic template news output, persistence/save-load coverage, and targeted tests without changing gameplay formulas or rating/growth balance.

## RELATED_PRS
- None assigned for this batch yet.

## RELATED_BRANCHES
- main

## GATES
- EVENT_SYSTEM_AUDIT = PASS_WITH_GAPS
- NEXT_EVENT_CONTRACT = PASS
- FIRST_PRODUCTION_EXPANSION_BATCH = SELECTED
- CAREER_SPINE_IMPLEMENTATION = OPEN
- CONTRACT_FA_STORY = BLOCKED_ON_03
- NARRATIVE_RNG_ISOLATION = OPEN
