# H3.2.1 Production Port

## Source
- Main base: `2b8eba28d5e2c4008840970d044d0aae258e73f6`
- Balance-Lab source branch: `test/h31-balance-lab-integration`
- Balance-Lab source commit: `b7b8aafde0a50e687310dbe03b872087a569e08c`
- Production integration branch: `feature/h32-production-integration`
- Pull request: `#11`

## Scope
This port moves the validated H3.1 pitch/contact/batted-ball/defense model and
H3.2.1 baserunning formulas into production `src/` without importing
`tools.balance_lab` from production code.

The legacy public simulation entry points remain available:
- `simulate_plate_appearance(...) -> str`
- `simulate_player_game(...)`

New production APIs include:
- `simulate_plate_appearance_outcome(...)`
- `src.hitting.baserunning.GameState`
- `apply_steal_to_state(...)`
- `apply_first_to_third_to_state(...)`
- `apply_second_to_home_to_state(...)`
- `apply_double_play_to_state(...)`

## Production architecture
- `src/hitting/parameters.py`: frozen validated H3.1/H3.2/H3.2.1 constants.
- `src/hitting/model.py`: pitch, swing, contact, quality, batted-ball, HR and hit-candidate resolution.
- `src/hitting/defense.py`: difficulty-tier catch and damage suppression.
- `src/hitting/baserunning.py`: frozen H3.2.1 probabilities plus thin real-`GameState` mutation adapters.
- `src/simulation.py`: Player/trait/form compatibility adapter and legacy player-game entry points.
- `src/records.py`: backward-compatible optional SB/CS/baserunning diagnostics.

## Formula changes
**NONE** to the validated neutral-profile formulas.

The production port was checked against the Balance-Lab H3.1 neutral model with
the same seed/profile. A regression test compares event counts directly and
passes, demonstrating that the production neutral hitting core preserves the
validated RNG ordering and event math.

Production-only wrappers:
1. Existing trait/form/fatigue effects are applied as per-pitch Contact/Power input adjustments. They are zero for the neutral Balance-Lab regression profile.
2. The legacy `steal_sense` trait is intentionally not stacked onto the frozen H3.2.1 steal equations. Reintroducing it requires a new Balance-Lab validation pass.
3. Baserunning uses a deterministic child RNG stream for the legacy player-only career loop, so SB/CS resolution does not consume or shift the parent career RNG.

## Game-state integration limitation
The current career engine simulates one player's plate appearances, not every
teammate PA in a persistent inning. Therefore it does not yet own runner
identities/base states required to correctly resolve teammate-driven:
- 1B -> 3B advancement,
- 2B -> Home advancement,
- ground-ball double plays.

The earlier integration draft fabricated these events from the hitter's own PA.
That adapter was removed. The final production candidate instead:
- connects validated SB/CS to the legacy player-only loop through an isolated H3.2 context sampler;
- exposes the validated advancement/DP formulas as real `GameState` APIs for a future full-team inning engine;
- does **not** invent advancement/DP events in the current career loop.

This preserves formula validity and avoids double counting or false runner state.

## Save compatibility
`BattingLine` adds optional fields with zero defaults:
`ROE`, `GDP`, `SB_attempts`, `DP_avoided`, `XBT`, `XBT_attempts`,
`first_to_third`, `second_to_home`.

`BattingLine.from_dict()` defaults all new keys to zero, so older save payloads
remain loadable. Existing save serialization includes the new fields on the next
save without requiring a schema-version bump.

Existing save/load round-trip and older-save compatibility tests pass.

## Balance regression
Production HittingEngine, neutral C/P/D/S=100, pitcher=100, defense=100,
100,000 PA, seed 20260905:
- AVG: `0.261151`
- OBP: `0.320370`
- SLG: `0.398793`
- OPS: `0.719163`
- HR/PA: `0.027700`
- BB/PA: `0.080150`
- K/PA: `0.213480`

In addition to tolerance-band regression, the production core now has a same-seed
**exact event-count parity test** against the Balance-Lab H3.1 model. It passes.

## Production gameplay regression
The H3.2.1 production tests pass for:
- Contact monotonicity,
- Power monotonicity,
- Discipline monotonicity,
- Speed monotonicity,
- Defense monotonicity,
- low-Speed steal suppression,
- steal-success monotonicity,
- high-Speed steal diminishing returns,
- advancement monotonicity,
- DP-avoidance monotonicity,
- Routine/Exceptional defense bounds,
- finite and bounded probabilities through raw stat 30..220,
- deterministic hitting seed,
- exact neutral Balance-Lab event parity,
- real `GameState` mutation adapters,
- compatibility baserunning not consuming parent career RNG,
- old `BattingLine` save defaults.

## Repository CI result
Latest inspected PR #11 code run:
- Web build/tests: **PASS**
- Python compile: **PASS**
- H3.1 Balance-Lab tests: **PASS**
- H3.2.1 production-port tests: **PASS**
- Existing event/growth/player/presentation tests: **PASS**
- Existing full-career smoke: **PASS**
- Existing save/load round-trip: **PASS**

The suite ran 68 tests and only one existing v0.4 balance regression failed:
- `test_balance_v04.BalanceV04Tests.test_draft_distribution_not_extreme`
- observed undrafted fraction: **0.42**
- existing required maximum: **< 0.35**

An earlier wrapper version produced 0.44. Correcting baserunning RNG/context
reduced it only to 0.42, confirming that the remaining shift is primarily a
career-balance consequence of replacing the old production hitting model with
H3.2.1 rather than a baserunning-wrapper defect.

`evaluate_draft()` derives a performance component from the newly simulated
high-school OPS/HR, so a new production hitting distribution necessarily changes
draft outcomes unless the high-school/draft layer is recalibrated.

Per the formula-freeze rule, this port does **not** retune H3.2.1, alter draft
thresholds, change growth/career parameters, weaken the existing test, or refit
real-player ratings merely to obtain a green CI result.

## Remaining risks / blockers
- **BLOCKER:** deterministic high-school/draft regression currently produces 42% undrafted versus the existing `<35%` guard.
- The project still lacks a full-team inning simulator; advancement and DP math is production-ready as an API but cannot yet be exercised correctly by the player-only career loop.
- HBP generation is not part of the validated H3.1 neutral math and therefore is schema-compatible but not generated by the new neutral H3 path.
- `steal_sense` remains intentionally disabled in H3.2.1 production math pending separate validation.
- Existing real-player ratings were not refit in this port.

## Promotion recommendation
`PRODUCTION_PORT_NOT_READY`

Do **not** merge PR #11 into `main` yet.

Recommended next step: run a separate high-school/draft career calibration pass
using the H3.2.1 gameplay formulas as frozen input. That follow-up may adjust the
career/draft calibration layer if justified, but must not silently retune the
validated H3.2.1 gameplay equations.
