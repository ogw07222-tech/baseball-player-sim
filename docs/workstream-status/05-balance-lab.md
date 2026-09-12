# 05 - Balance Lab

WORKSTREAM: 05 - Balance Lab
UPDATED_AT: 2026-09-12
SOURCE_OF_TRUTH: production main@47ada4fe9f1d95da2760d7a8d56a8900aab6fdc3
STATE: FAIL_WITH_NON_EVENT_GLOBAL_CI_WATCH
CURRENT_TASK: Interactive Event P1 final production validation
RESULT: INTERACTIVE_EVENT_P1_FAIL / P1_CLOSE_ALLOWED_NO

## FINAL_DECISION
- VALIDATED_MAIN_HEAD = `47ada4fe9f1d95da2760d7a8d56a8900aab6fdc3`.
- INTERACTIVE_EVENT_P1 = FAIL.
- P1_CLOSE_ALLOWED = NO.
- Blocking reason is not transaction integrity, RNG, persistence, API, UI build, or raw performance. The production catalog exposes materially frequent EVENTs whose choices cannot be authoritatively resolved by 03; those pending EVENTs persist across seasons, accumulate to the max-pending cap, and eventually suppress future EVENT generation.
- No event chance, cooldown, effect magnitude, catalog entry, gameplay/growth formula, or production code was tuned or modified by 05.

## CANONICAL_VALIDATION_EVIDENCE
- Validation-only branch: `validation/interactive-event-p1-final-05`.
- Canonical final validation checkout: `896f8b6088b1c7d08431fa76d649f5ac21333df7`.
- Actions run: `34673576025` — SUCCESS.
- Job: `103499336875` — SUCCESS.
- Artifact: `10291617959`.
- Artifact digest: `sha256:9504d7660ef25b5b89bbc23beb247c0d6481391204eb8bdcc47bd8b5ae8eaf0c`.
- Production identity assertion against `47ada4fe...` passed for `src`, `web`, `tests`, and `requirements-api.txt`; validation branch adds validation files only.

## SAMPLE_SIZE
- Event-frequency/category/archetype generation cohort: 500 deterministic 144-game seasons.
- Queue cohorts: 500 unattended seasons + 500 authoritative-resolution seasons.
- Multiseason queue probe: 200 seeds x 4 seasons = 800 seasons.
- Long-term effect paired cohort: 80 event-vs-no-event season pairs.
- RNG purity: 40 paired 144-game seasons.
- Performance: 120 seasons = 17,280 games each side, interleaved paired benchmark.
- Full Python regression: 478 tests, 477 pass / 1 known unrelated failure / 5 skipped.
- Web: 6 test files / 44 tests PASS plus production build PASS.

## EVENT_FREQUENCY
500-season record-only generation cohort:
- mean 4.946 EVENT/season; median 6.
- P10 3; P25 4; P75 6; P90 6; min 0; max 6.
- zero-event season rate 0.4%.
- season-cap(6) hit rate 52.0%.
- Frequency is not sparse, but median=P75=P90=cap and a majority of seasons hit the cap, so the observed distribution is materially cap-truncated.
- EVENT_FREQUENCY = WATCH; no chance/cap tuning performed.

## CATEGORY_AND_ARCHETYPE_DISTRIBUTION
2,473 generated EVENTs:
- training 832 = 33.64%.
- team_role 774 = 31.30%.
- media 405 = 16.38%.
- coach 322 = 13.02%.
- recovery 131 = 5.30%.
- form 9 = 0.364%.
Per-season category diversity: mean 3.57; median 4; P10 2; P90 5.
All ten catalog archetypes were technically reached, but form archetypes are practically dormant in this corpus:
- `slump_response`: 3 / 2,473 = 0.121%, absent in 99.4% of seasons.
- `hot_streak_routine`: 6 / 2,473 = 0.243%, absent in 98.8% of seasons.
Other archetype counts: batting training 164, defense training 301, weakness 367, coach 322, role competition 383, position practice 391, media 405, fatigue management 131.
- CATEGORY_DIVERSITY = WATCH.
- ARCHETYPE_REACHABILITY = WATCH (all reachable, but both form archetypes are near-never under measured production-state eligibility).

## COOLDOWN_AND_DEDUPE
Across the 500-season generation cohort:
- duplicate event_id: 0.
- duplicate dedupe_key: 0.
- season-cap bypass: 0.
- per-archetype cap bypass: 0.
- once-per-season bypass: 0.
- event cooldown violation: 0.
- category cooldown violation: 0.
Current catalog has `coach_method_trial` and `position_practice` once-per-season; there are no once-per-career catalog archetypes at this production head.
- COOLDOWN_DEDUPE = PASS.

## CHOICE_SUPPORT_MATRIX
Production P1 catalog contains 30 total choices:
- SUPPORTED by 03 authority: 22 = 73.33%.
- UNSUPPORTED_BY_03: 8 = 26.67%.
Unsupported choices:
- `role_competition/compete`: unsupported `development_modifier` target `role_readiness`.
- `role_competition/versatile`: unsupported `development_modifier` target `versatility` (plus unsupported role semantics).
- all three `position_practice` choices: unsupported `secondary_position` / `primary_position` semantics.
- all three `media_interview` choices: `temporary_trait_request` / public-stance semantics are unsupported.
Consequently:
- `position_practice` = ALL choices unsupported.
- `media_interview` = ALL choices unsupported.
- `role_competition` exposes two unsupported choices and one currently resolvable choice (`steady`).
- SUPPORTED_CHOICE_COVERAGE = FAIL for a close-ready P1 catalog.

## UNSUPPORTED_EXPOSURE_AND_QUEUE_BLOCKER
In the 2,473-event generation cohort:
- generated EVENTs containing >=1 unsupported choice: 47.6749%.
- generated EVENTs with ALL choices unsupported: 32.1876%.
The current UI renders every backend choice with the same actionable resolve button; unsupported choices are not pre-disabled/capability-tagged. API failure is explicit/atomic, but this does not make the catalog usable.
Single-season queue measurements:
- fully unattended: 93.2% of seasons reached pending cap=3 at least once; pending count was at cap for 51.00% of game states; final pending median=3.
- authoritative supported-choice resolution: final pending mean=1.576, median=2, consisting of all-unsupported EVENTs; queue did not yet hit 3 within most first seasons.
Multiseason production lifecycle probe, resolving every supported EVENT and leaving only all-unsupported EVENTs pending:
- season 1: generated mean 5.03; pending mean 1.585; pending=3 rate 0%.
- season 2: generated mean 2.625; pending mean 2.77; pending=3 rate 80.0%.
- season 3: generated mean 0.455; zero-generation seasons 80.0%; pending=3 rate 98.5%.
- season 4: generated mean 0.05; zero-generation seasons 98.5%; pending=3 rate 99.5%.
Final pending types are exclusively `position_practice` and `media_interview`; pending EVENT history survives season resets while the generator blocks whenever pending count reaches 3.
- UNSUPPORTED_EXPOSURE = FAIL.
- PENDING_QUEUE = FAIL.
This is the reproducible P1 blocker.

## EFFECT_MAGNITUDE_AND_LONG_TERM
Supported planned effects only:
- growth mean-credit configured total per effect plan: median +0.14, P10 -0.112, P90 +0.35, min -0.168, max +0.42 before canonical season-growth mapping.
- fatigue configured total: min -15, max +14; authoritative 0..100 clamp probe passed.
- active-effect durations: median 10 committed games; range 5..21.
- exact duration expiration probe PASS; no hidden active-effect persistence after expiration.
80 paired event-vs-no-event seasons (first supported choice policy):
- season-end current-ability delta mean +0.3142; median +0.3333; P10 0; P90 +0.6917; min -1.4167; max +0.8750.
- mean absolute per-rating delta mean 0.3398; max pair 3.0909.
- pre-finalization fatigue delta median 0; mean -0.064; min -30.75; max +14.
- form-state difference at season end 0% in this cohort.
No one-season runaway accumulation was observed, but these mappings remain engineering values rather than calibrated career-balance targets, and a healthy full-career impact cannot be certified while queue saturation stops the EVENT system in later seasons.
- EFFECT_MAGNITUDE = WATCH.
- LONG_TERM_IMPACT = WATCH.

## TRADEOFFS
Supported mappings preserve explicit multi-effect costs where authored (training upside/fatigue, recovery/development cost, defense specialization/hitting opportunity cost). However no player utility function exists, and unsupported role/position/media choices prevent a full catalog dominance proof. No tuning was attempted.
- TRADEOFFS = OPEN.

## DETERMINISM_AND_RNG_PURITY
- duplicate authoritative season replay canonical serialized hash exact equal: `9ab48357c358b348aa724eff658529985ece9bfe274e885259f89f0474512e5f`.
- 40 observational EVENT-enabled vs generation-disabled paired seasons: 0 exact core-state/RNG failures.
- generation uses deterministic hash-derived rolls and does not advance canonical RNG; authoritative effect resolution/ticking consumes no new RNG.
- DETERMINISM = PASS.
- RNG_PURITY = PASS.

## SAVE_LOAD_AND_ADVANCE_COMPOSITION
Existing production tests plus independent roundtrip validate persistence of pending/resolved EVENT records, active effects, remaining games, cooldown/count state, and old-save compatibility. Same next action after load is deterministic.
Exact event coordinates were independently observed for:
- `next_game`: game 1 / 2026-04-01.
- `week`: generated at constituent game 1 / 2026-04-01 within a 6-game command.
- `month`: generated at constituent game 1 / 2026-04-01 within a 26-game command.
Thus period commands do not synthesize EVENT only at period end.
- SAVE_LOAD = PASS.
- ADVANCE_COMPOSITION = PASS.

## API_UI_VERTICAL_SLICE_AND_TRANSACTIONS
Current production integration tests PASS for:
- state/advance pending_events transport.
- pending EVENT -> resolve request -> authoritative effect -> resolved removal -> remaining queue.
- valid resolution revision +1.
- stale revision rejected with no mutation.
- same idempotency replay returns same response and applies effect once.
- same idempotency key with conflicting payload rejected.
- second resolve rejected without second effect.
- invalid event_id / choice_id / malformed authoritative fields rejected without partial mutation.
- unsupported effect returns explicit `UNSUPPORTED_EVENT_EFFECT` without mutation.
Web production build PASS and 44/44 Vitest tests PASS, including 12 Interactive Event UI tests. The UI correctly displays backend errors and prevents duplicate dispatch while a request is in flight.
- RESOLVE_TRANSACTION = PASS.
- IDEMPOTENCY = PASS.
- API_UI_VERTICAL_SLICE = PASS_WITH_UNSUPPORTED_USABILITY_BLOCKER (represented by UNSUPPORTED_EXPOSURE=FAIL).

## EVENT_CAREER_SEPARATION
- EVENT transport remains `pending_events: InteractiveEvent[]`.
- CAREER transport remains `notable_events: CanonicalEventDTO[]`.
- choice resolution itself does not emit a CareerSourceFact.
- only real authoritative career transitions (e.g. actual form transition) feed CAREER facts.
- frontend EVENT panel is distinct from Career/Season presentation.
- EVENT_CAREER_SEPARATION = PASS.

## PERFORMANCE
Interleaved same-process benchmark, 120 seasons / 17,280 games each side using identical lightweight game provider:
- EVENT-generation/eligibility enabled: 345.18 us/game.
- generation patched out: 346.84 us/game.
- measured delta: -0.48% (noise-level; no measurable regression).
Catalog scan is small fixed-size O(catalog) work and pending-size check is bounded at the P1 cap.
- PERFORMANCE = PASS.

## REGRESSION_AND_GLOBAL_CI
Canonical validation workflow SUCCESS.
- targeted Interactive Event Python integration tests PASS.
- web production build PASS.
- web tests 44/44 PASS.
- full Python discover: 478 tests; exactly one failure, 5 skipped.
Sole failure remains pre-existing unrelated `test_balance_v04.BalanceV04Tests.test_draft_distribution_not_extreme`: deterministic undrafted rate 0.0566667 vs old assertion >0.10. No Interactive Event, gameplay, growth, injury, roster, save/load, API, web, or physical-engine test failed.
- REGRESSION = PASS for Interactive Event P1 attribution.
- GLOBAL_CI_UNRELATED_DRAFT_BALANCE = WATCH / out of scope.

## FINAL_GATES
- EVENT_GENERATION = PASS
- EVENT_FREQUENCY = WATCH
- CATEGORY_DIVERSITY = WATCH
- ARCHETYPE_REACHABILITY = WATCH
- COOLDOWN_DEDUPE = PASS
- PENDING_QUEUE = FAIL
- SUPPORTED_CHOICE_COVERAGE = FAIL
- UNSUPPORTED_EXPOSURE = FAIL
- EFFECT_MAGNITUDE = WATCH
- LONG_TERM_IMPACT = WATCH
- TRADEOFFS = OPEN
- DETERMINISM = PASS
- RNG_PURITY = PASS
- SAVE_LOAD = PASS
- ADVANCE_COMPOSITION = PASS
- RESOLVE_TRANSACTION = PASS
- IDEMPOTENCY = PASS
- EVENT_CAREER_SEPARATION = PASS
- PERFORMANCE = PASS
- REGRESSION = PASS

## BLOCKERS_AND_OWNER_HANDOFFS
Primary P1 blocker:
1. 04/03 contract mismatch leaves `position_practice` and `media_interview` entirely unresolvable; `role_competition` is partially unresolvable.
2. 06 displays those unsupported choices as normal actionable choices; explicit post-click error handling is correct but does not prevent unusable EVENTs.
3. Persistent pending state plus max_pending=3 means unsupported events accumulate across seasons and suppress future generation.
Owner routing, without prescribing a tuning solution:
- 04: catalog/generation/capability exposure contract; ensure generated P1 EVENTs have a close-ready supported-choice contract.
- 03: authoritative semantics if/when real public-stance, position, versatility, role-readiness/primary-role support is intentionally implemented.
- 06: capability-aware choice presentation if the backend exposes such capability; current generic error display alone does not solve all-unsupported EVENT usability.
- 07: persistence/API transaction behavior is currently PASS; coordinate capability contract transport if 04/03/06 change it.
- 05: rerun the same close validation after the blocker is corrected; do not tune frequency/effect coefficients as part of that correction unless separately authorized.

INTERACTIVE_EVENT_P1 = FAIL
P1_CLOSE_ALLOWED = NO
NEXT_ACTION = 04 + 03 correction contract, then 06/07 integration as required, then 05 revalidation.
