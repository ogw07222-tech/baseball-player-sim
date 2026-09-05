# H3.2.1 Production Port

## Source
- Initial production branch base: `2b8eba28d5e2c4008840970d044d0aae258e73f6`
- Latest `main` exercised by the final PR merge-ref CI: `48070ab2a4c3d5793ead6dbbfc239668331a518a`
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
**NONE** to the validated H3.2.1 gameplay formulas.

The production port is regression-tested against the Balance-Lab neutral model.
The same-seed neutral core event-count parity test passes, preserving validated
RNG ordering and event math. The final draft calibration touched only the career
layer (`src/config.py` draft score spread); no `src/hitting/*` formula changed.

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

The production candidate therefore:
- connects validated SB/CS to the legacy player-only loop through an isolated H3.2.1 context adapter;
- exposes the validated advancement/DP formulas as real `GameState` APIs for a future full-team inning engine;
- does **not** fabricate advancement/DP events in the current player-only career loop.

This is a known architectural limitation, not a formula deviation or current merge blocker.

## Save compatibility
`BattingLine` adds optional fields with zero defaults:
`ROE`, `GDP`, `SB_attempts`, `DP_avoided`, `XBT`, `XBT_attempts`,
`first_to_third`, `second_to_home`.

`BattingLine.from_dict()` defaults all new keys to zero, so older save payloads
remain loadable. Existing save serialization includes the new fields on the next
save without requiring a schema-version bump.

Save/load round-trip, old-field defaulting and RNG reproducibility tests pass.

## H3.2.1 balance regression
Production HittingEngine, neutral C/P/D/S=100, pitcher=100, defense=100,
100,000 PA, seed 20260905:
- AVG: `0.261151`
- OBP: `0.320370`
- SLG: `0.398793`
- OPS: `0.719163`
- HR/PA: `0.027700`
- BB/PA: `0.080150`
- K/PA: `0.213480`

The production core also passes a same-seed exact event-count parity test against
the Balance-Lab H3.1 core.

## Final high-school / draft calibration
The H3.2.1 gameplay formulas were frozen while the high-school/draft career layer
was recalibrated independently.

Final generation distributions from the deterministic 10,000-player / 10,000-NPC run:
- Player current ability: mean `79.710`, SD `9.726`.
- NPC current ability: mean `69.609`, SD `7.028`.
- Player mean > NPC mean: **PASS**.
- Player SD > NPC SD: **PASS**.

Final draft architecture:
- Performance configured weight: `0.80`
- Scouting: `0.10`
- Position: `0.06`
- Health: `0.02`
- Context: `0.02`
- Direct current ability: `0.00`
- Scout projection compression: `0.20`
- Draft score center: `83.0`
- Draft component scale: `15.0`
- Draft score spread: **`48.5`**
- Draft random SD: `3.0`
- Draft thresholds: **unchanged** (`105.0 / 97.0 / 86.8 / 76.2`)

Final deterministic 10k draft distribution:
- 1R: `14.49%` (target 8-15%)
- 2-3R: `12.88%` (target 12-20%)
- 4-7R: `26.99%` (target 25-35%)
- 8-11R: `29.92%` (target 20-30%)
- Undrafted: `15.72%` (target 10-25%)

Realized mean absolute contribution:
- Performance: `78.68%`
- Scouting: `12.67%`
- Position: `6.29%`
- Health: `1.82%`
- Context: `0.54%`
- Direct current ability: `0%`

The original ~42% undrafted blocker is resolved without changing draft thresholds
or H3.2.1 gameplay formulas.

### Final calibration search
The last failure was isolated to the 8-11R upper band. Tested candidates:

| Scout compression | Score spread | 1R | 2-3R | 4-7R | 8-11R | Undrafted | Performance | Scouting | Result |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 0.20 | 48.00 | 14.17% | 12.87% | 27.15% | 30.28% | 15.53% | 78.68% | 12.67% | FAIL: 8-11R |
| 0.24 | 48.00 | 14.07% | 12.93% | 27.02% | 30.01% | 15.97% | 76.74% | 14.83% | FAIL: 8-11R |
| 0.245 | 48.00 | 14.08% | 12.92% | 26.97% | 30.03% | 16.00% | 76.50% | 15.09% | FAIL: 8-11R + scouting |
| 0.20 | 48.25 | 14.31% | 12.89% | 27.07% | 30.09% | 15.64% | 78.68% | 12.67% | FAIL: 8-11R |
| **0.20** | **48.50** | **14.49%** | **12.88%** | **26.99%** | **29.92%** | **15.72%** | **78.68%** | **12.67%** | **PASS** |

The selected solution is intentionally minimal: retain the contribution-safe
`0.20` scouting compression and change only `DRAFT_SCORE_SPREAD` from `48.0` to
`48.5`. Score center, component scale, random SD, component weights and thresholds
remain unchanged.

## Draft philosophy regression
All draft-performance cross tests pass:
- elite production beats poor production,
- strong performance can beat high projection with mediocre performance,
- direct current-ability draft weight is zero,
- deterministic seed is reproducible,
- small-PA reliability shrinkage is preserved,
- position-aware hitter weights remain active,
- Catcher special-case path remains explicit and operational,
- Pitcher performance extension marker remains explicit and pending.

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

## Final CI evidence
PR #11 candidate `c3ebae8763337bfec5b0ec8e1eee0ec03d078cf9` was exercised by GitHub Actions
against latest `main` through the PR merge ref.

Run #172:
- Web build: **PASS**
- Web tests: **PASS**
- Python compile: **PASS**
- Full unit suite: **79/79 PASS**
- Auto-career smoke: **PASS**
- Balance smoke: **PASS**
- Deterministic 10k high-school/draft calibration: **PASS**
- Draft calibration artifact: **generated and uploaded**

## Remaining risks
- The project still lacks a full-team persistent inning simulator; advancement and DP APIs cannot yet be exercised through teammate runner state in the current player-only career loop.
- HBP generation is not part of the validated H3.1 neutral math and therefore is schema-compatible but not generated by the neutral H3 path.
- `steal_sense` remains intentionally disabled in H3.2.1 production math pending separate validation.
- Existing real-player ratings were not refit in this production port.
- Catcher-specific receiving/framing/blocking/game-calling evaluation and pitcher draft performance remain explicit future extension points.

None of these items changes the validated H3.2.1 formulas or blocks the current production-port integration gate.

## Promotion recommendation
`PRODUCTION_PORT_READY`

Merge recommendation: **YES**, once PR #11's final documentation-only HEAD remains CI-green and mergeable.

This task does not merge PR #11 automatically.
