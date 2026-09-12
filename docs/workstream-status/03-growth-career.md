# 03 - Growth & Career

WORKSTREAM: 03 - Growth & Career
UPDATED_AT: 2026-09-12
TASK_START_MAIN: 3a4fc58a3c56d9042561494a08a676762fb4661d
CURRENT_MAIN: 763502b009585a1756a50994e0e1fe51c0e062e1
PR64_VALIDATED_HEAD: 2a20fe86b87b3a6cf83caa3958202c937d98839d
PR64_MERGE_COMMIT: ab26ab04d42fe5a67ee5cc52462de57b77d33eff
STATE: INTERACTIVE_EVENT_EFFECT_AUTHORITY_IMPLEMENTED
CURRENT_TASK: Interactive Event authoritative effect application
RESULT: PASS_WITH_PREEXISTING_GLOBAL_CI_BLOCKER

## SOURCE_OF_TRUTH_REAUDIT
- Task started from main `3a4fc58a3c56d9042561494a08a676762fb4661d` and exact PR #64 Interactive Event System P1 HEAD `2a20fe86b87b3a6cf83caa3958202c937d98839d`.
- PR #64 merged during this task as `ab26ab04d42fe5a67ee5cc52462de57b77d33eff`; latest audited main `763502b009585a1756a50994e0e1fe51c0e062e1` contains that merge plus documentation-only follow-up.
- 04 remains EVENT authority for occurrence, catalog, choice text, declarative `EventChoiceEffect`, pending/resolved/expired state, and deterministic child-event generation.
- 03 now owns authoritative interpretation/application of supported effect requests into existing career state.
- No API endpoint, frontend implementation, event occurrence tuning, catalog expansion, or Career Timeline presentation is included.

## IMPLEMENTATION
BRANCH: `feature/interactive-event-authoritative-effects`
PR: #66 `Growth/Career: authoritative Interactive Event effect application`
VALIDATED_CODE_HEAD: `a6ce48c9fc7a96d9e30b1741ac0570dd8f223adb`

New 03-owned `src/interactive_event_effects.py` defines:
- `UnsupportedInteractiveEffect`
- `ActiveCareerEffect`
- `InteractiveCareerEffectState`
- `resolve_interactive_event_authoritatively(...)`
- per-game fatigue/form application
- per-game growth/development accrual
- exact game-duration expiry
- season-boundary cleanup.

`ProductionAdvanceService.resolve_interactive_event(...)` delegates to this authority. 04's direct `resolve_interactive_event(...)` remains EVENT-record-only and does not mutate Player/Career state.

## EFFECT_AUTHORITY
Authoritative resolution order:
1. require an active professional season;
2. locate existing EVENT without creating persistence state;
3. require `status == pending`;
4. validate `choice_id`;
5. validate and plan every effect request with zero mutation;
6. create/reuse 03 effect state only after all validation passes;
7. apply the complete planned active-effect set;
8. mark the EVENT resolved through the 04 EVENT-state resolver;
9. persist EVENT state and 03 effect state together through the normal save payload.

Unexpected failure after mutation begins restores the EVENT/effect snapshots. Invalid event, invalid choice, resolved-event replay, and unsupported effect requests are side-effect free.

## SUPPORTED_EFFECTS
### training_focus
Mapped into the existing season `GrowthModifiers` contract. No rating is directly incremented.

Supported target mappings:
- `hitting` -> contact / power / discipline
- `defense` -> defense / throwing
- `defense_range` -> defense / speed
- `throwing` -> throwing
- `all` / `player` -> all current growable ratings
- `weakest_rating` -> concrete weakest growable stat resolved at choice time
- `strongest_rating` -> concrete strongest growable stat resolved at choice time
- `coach_recommendation` / `player_routine` -> existing generic growable-rating pathway only.

### development_modifier
Uses the same existing `GrowthModifiers` mean/variance pathway and therefore affects later canonical season growth rather than creating immediate rating deltas.

### fatigue_modifier
Uses authoritative `Player.fatigue`, applied after normal rest/game fatigue and clamped to the existing 0..100 domain.

### form_modifier
Uses the existing `Player.form` / `form_games_remaining` state machine. A modifier that actually completes a non-normal form state produces the existing `form_transition` CareerSourceFact.

## UNSUPPORTED_EFFECTS
Rejected rather than fabricated:
- all `temporary_trait_request` requests: production Traits are durable and there is no authoritative temporary-Trait/public-stance overlay;
- secondary/primary-position training semantics;
- versatility development semantics;
- role-readiness / primary-role development semantics;
- any unknown target, magnitude, effect type, or non-positive/missing duration for a temporary effect.

Consequently some PR #64 catalog choices are intentionally not yet authoritatively resolvable, notably media public-stance requests and position-practice requests. 04/06/07 must surface unsupported resolution rather than silently pretending an effect was applied.

## MAGNITUDE_MAPPING
These are deterministic plumbing mappings, not final balance claims; 05 owns later calibration.

Training growth mean credit per committed game:
- high: +0.025
- medium: +0.018
- balanced: +0.010
- low: +0.005
- partial: +0.008
- maintain: 0

Development mean credit per committed game:
- upside_medium: +0.020
- upside_small: +0.010
- small: +0.008
- opportunity_cost_small: -0.008
- opportunity_cost_medium: -0.015

Development variance:
- variance_medium: existing season variance multiplier x1.001 per active game.

Fatigue delta per active game:
- cost_small: +1
- cost_medium: +2
- recovery_small: -1
- recovery_medium: -2
- recovery_large: -3

Form duration adjustment per active game when applicable:
- stability_up: slump -1 game
- breakthrough_chance: slump -1 game
- momentum_decay_small: hot -1 game
- variance_small / variance_medium: non-normal duration +1 game.

No magnitude maps directly to permanent rating points.

## TEMPORARY_DURATION
- Canonical duration unit is committed games.
- A resolved effect starts on the next committed game because EVENT generation/resolution is outside the already-completed game mutation.
- Every active effect decrements exactly once per committed game and expires at zero.
- Effects persist across save/load with exact `games_remaining`.
- Active effect state is cleared on season finalization/start-next-season so hidden permanent effects cannot leak into the next season.

## TRADEOFF_PRESERVATION
Existing 04 trade-off requests remain separate active effects. Examples:
- intensive training can combine development upside with fatigue cost;
- rest can combine fatigue recovery with development opportunity cost;
- defensive specialization can combine targeted development with hitting opportunity cost.
03 does not collapse a multi-effect choice into a single favorable scalar.

## CAREER_SOURCE_FACT_INTEROP
- Resolving an EVENT or choosing training does not itself emit a CareerSourceFact.
- Growth/fatigue/development ledger changes are EVENT effects, not automatic Career Timeline records.
- Existing CareerSourceFact authorities remain responsible for real career-worthy transitions.
- Current explicit interop: if a form modifier causes an actual non-normal -> normal transition, the existing `form_transition` fact is emitted from the authoritative mutation.
- No story prose or timeline rendering is generated by 03.

## SAVE_LOAD / DETERMINISM
- Optional `interactive_career_effect_state` is added to the canonical save payload.
- Old saves without this field load as an empty effect state.
- Pending/resolved EVENT state remains the 04 persisted state.
- Active effect target/magnitude/parameters/source event and exact remaining games are persisted.
- Resolved EVENT status prevents duplicate effect application after save/load.
- Resolution/ticking consume no new randomness; same save + seed + event state + choice produces the same authoritative state and RNG state.

## TEST_COVERAGE
`tests/test_interactive_event_authoritative_effects.py` covers:
- valid pending choice application and resolution
- invalid event zero mutation
- invalid choice zero mutation
- resolved EVENT cannot mutate twice
- unsupported effect atomic rejection
- training focus -> existing GrowthModifiers, no direct rating delta
- fatigue modifier -> Player.fatigue
- form modifier -> existing form state plus real-transition CareerSourceFact only
- development modifier -> existing GrowthModifiers
- exact multi-duration game expiry
- pending/resolved EVENT + active-effect save/load
- duplicate prevention after save/load
- old save compatibility
- deterministic replay / RNG identity
- direct 04 resolution remains Player-pure
- ProductionAdvanceService authority delegation.

Validated code HEAD `a6ce48c9fc7a96d9e30b1741ac0570dd8f223adb`, workflow #959 / run `34667294941`:
- Python packaging PASS
- compile PASS
- external durable store PASS
- FastAPI entrypoint smoke PASS
- API vertical slice PASS
- related production integration PASS
- all 14 new authority tests PASS
- all PR #64 Interactive Event P1 tests PASS
- web build/tests PASS
- full unit discovery ran 440 tests with exactly one unrelated pre-existing failure: `test_balance_v04.BalanceV04Tests.test_draft_distribution_not_extreme` (undrafted fraction 0.056666..., legacy assertion requires >0.10). The same baseline failure existed before this task; 03 did not tune draft distribution to hide it.

## EXACT_07_HANDOFF
07 should wire EVENT choice resolution through `ProductionAdvanceService.resolve_interactive_event(...)` inside the existing SessionStore authoritative transaction.

Required transport semantics:
- expected revision/CAS check before commit;
- EVENT state and `interactive_career_effect_state` commit atomically with the engine save;
- stale revision or unsupported/invalid choice commits neither EVENT status nor effect state;
- idempotency replay returns the stored committed resolution response and must not call the resolver again;
- a second core call against an already-resolved EVENT is an error and never reapplies effects.

No HTTP endpoint is implemented by 03.

## EXACT_06_HANDOFF
06 may render the 04-owned pending EVENT/choices and send the selected `event_id + choice_id` to 07. UI must never apply or predict authoritative career mutations itself.

Until all catalog request families gain production semantics, unsupported-choice resolution must be surfaced explicitly rather than shown as successfully applied. 04 may later gate catalog eligibility against authoritative capability, but that policy is outside this PR.

## GATES
- EVENT_EFFECT_AUTHORITY = PASS
- EFFECT_VALIDATION = PASS
- ATOMIC_RESOLUTION = PASS
- DUPLICATE_RESOLUTION = PASS
- TEMPORARY_EFFECTS = PASS
- SAVE_LOAD = PASS
- DETERMINISM = PASS
- CAREER_SEPARATION = PASS
- TASK_SPECIFIC_TESTS = PASS
- REPO_GLOBAL_CI = BLOCKED_BY_PREEXISTING_DRAFT_DISTRIBUTION_BASELINE

## READY_FOR_07_06
YES for supported authoritative effect families and explicit unsupported-error handling.

## NEXT_ACTION
- 07: transactionally expose `ProductionAdvanceService.resolve_interactive_event(...)` with CAS/idempotency.
- 06: render pending EVENT choices and resolution feedback; do not mutate career state client-side.
- 04/03 future work: add authoritative capability only when real position/role/temporary-Trait semantics exist; do not fabricate them solely to make every catalog choice resolvable.
