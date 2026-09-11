# 01 - Gameplay Engine

WORKSTREAM: 01 - Gameplay Engine
UPDATED_AT: 2026-09-11
SOURCE_OF_TRUTH: main@34ac1fc35b5616fade75721221e95aeea3398232; PR #58 production-code checkpoint@ac30469f00096ff6090c0143313dd7a940ace955; final code/test checkpoint@783503bf51ba102b4e6a823e6d371efdc98fd2cd
STATE: READY_FOR_05_FINAL_SIGNOFF
CURRENT_TASK: Final Phase 1 adjustment — neutral 3-0 Swing ~5%
RESULT: PASS

## SCOPE
- Final Phase-1-only adjustment: reduce neutral-population 3-0 Swing from ~15% to ~5% without making 3-0 a hard-zero rule.
- Preserve hitter identity from discipline, approach/location/hittability, 3-1 behavior, 3-2 protection/selectivity, 0-2/1-2/2-2 protection, generated chase improvement, two-strike take rescue, looking-K fix, BB/K/HBP environment, foul survival, discipline monotonicity, and deterministic replay.
- No changes to two-strike rescue logic, contact probability, foul conversion, HBP, HR/XBH/physical batted-ball, defense, park, ratings/generation, growth, or events.

## TASK-START STATE
- Latest main at task start: `34ac1fc35b5616fade75721221e95aeea3398232`.
- PR #58 remained OPEN / mergeable on `feature/phase1-plate-discipline-contact`.
- Previous accepted 01 candidate after the looking-K fix had neutral 3-0 Swing about 15%, with Z-Swing about 21% and Chase about 7–8%.
- Previous looking-K candidate remained healthy globally: neutral K 17.916%, looking-K 40.785%, generated Chase 27.730%, production 10k K/PA 18.027%.

## IMPLEMENTATION
Only the 3-0 entry in the sparse count table changed:

`COUNT_SWING_MODIFIERS[(3, 0)]`
- before: `(-0.470, -0.145)`
- after: `(-0.670, -0.185)`

Everything else in `COUNT_SWING_MODIFIERS` is unchanged:
- 2-0: `(-0.035, -0.030)`
- 0-2: `(+0.100, +0.005)`
- 1-2: `(+0.085, +0.000)`
- 2-2: `(+0.065, -0.005)`
- 3-1: `(-0.220, -0.090)`
- 3-2: `(+0.045, -0.045)`

Global probability bounds are unchanged:
- `ZONE_SWING_MIN = 0.06`
- `ZONE_SWING_MAX = 0.91`
- `CHASE_MIN = 0.015`
- `CHASE_MAX = 0.54`

Therefore the change is strictly situational to 3-0. The existing probability equation still includes hitter discipline plus pitch location/hittability, so player differentiation is retained and the behavior is not hard-zero.

The approved `src/hitting/parameters.py` blob is now `3876b4221f53b7d4b7cc6069d9425004fc9f311a`. Existing protected-blob regression snapshots were updated only to acknowledge this intentional Phase-1 parameter checkpoint; no other protected formula SHA was changed.

## FINAL HEAVY VALIDATION
Validation-only branch `validation/phase1-3-0-final` used the exact production-code checkpoint `ac30469f00096ff6090c0143313dd7a940ace955`.

GitHub Actions run `34600082446`: SUCCESS.
Seed: `20260911`.
Samples:
- Neutral hitter 100 vs neutral pitcher 100: 200,000 PA.
- Generated prospect hitter population vs neutral pitcher: 200,000 PA.
- Supplemental neutral production full games: 2,000 games.

### Neutral 200k count behavior
| Count | Reach/PA | Swing | Z-Swing | Chase |
| --- | ---: | ---: | ---: | ---: |
| 3-0 | 8.761% | 4.646% | 5.916% | 3.081% |
| 3-1 | 15.528% | 31.556% | 46.526% | 12.871% |
| 3-2 | 20.024% | 52.001% | 80.329% | 17.167% |

Required relationships:
- neutral 3-0 Swing ≈5%: PASS (`4.646%`).
- 3-0 < 3-1: PASS.
- 3-1 remains in its prior ~31% region: PASS.
- 3-2 remains in its prior ~51–52% region with protection/selectivity intact: PASS.

### 3-0 detailed behavior
A validation-only count-detail probe on branch `validation/phase1-3-0-countdetail` measured the same neutral 200k contract.
GitHub Actions run `34600349524`: SUCCESS.

3-0:
- Reach/PA: 8.761%
- Swing: 4.646%
- Z-Swing: 5.916%
- Chase: 3.081%
- Contact/Swing: 76.17%
- Called strike/pitch at 3-0: 51.91%

The nonzero swing and contact rates confirm this is strong selectivity rather than a hard-zero take rule.

## GLOBAL ENVIRONMENT — NEUTRAL 200k
- Swing: 48.050%
- Z-Swing: 70.208%
- Chase: 20.995%
- BB: 9.359%
- K: 17.835%
- Looking-K share: 41.144%
- Swinging-K share: 58.856%
- HBP: 1.315%
- Pitches/PA: 3.251

Interpretation:
- Global swing/chase environment is effectively unchanged from the accepted looking-K candidate.
- Looking-K remains around the fixed ~41% region and does not regress toward the previous 54–55% blocker.
- BB increased only modestly and remains around the intended ~9% environment.
- Neutral K remains near the accepted ~18% environment.

## GENERATED PROSPECT 200k
- Chase: 27.706%
- BB: 7.320%
- K: 22.247%
- HBP: 1.337%
- Looking-K share: 41.189%
- Swinging-K share: 58.811%
- Swing: 49.310%
- Z-Swing: 66.974%
- Pitches/PA: 3.243

Generated Chase is preserved versus the prior accepted ~27.73% candidate and shows no re-expansion pathology.

## SUPPLEMENTAL 2K FULL-GAME CHECK
- PA/game: 80.197
- Runs/game: 9.532
- Hits/game: 19.295
- HR/game: 2.171
- BB/game: 7.500
- K/game: 14.555
- HBP/game: 1.084
- BB/PA: 9.352%
- K/PA: 18.148%
- HBP/PA: 1.352%
- H/PA: 24.060%
- HR/PA: 2.706%
- AVG: .2701
- SLG: .4095
- ISO: .1395

No global offense explosion is observed, and no physical batted-ball parameter changed.

## REGRESSION / CI
Final code/test checkpoint: `783503bf51ba102b4e6a823e6d371efdc98fd2cd`.
GitHub Actions run `34600614407`:
- Web build/tests PASS.
- Compile PASS.
- Dependency / durable-store / API entrypoint / vertical-slice PASS.
- Related production integration: 31/31 PASS.
- Phase-1 count regression PASS, including exact 3-0 modifier, 3-0 nonzero behavior, 3-0/3-1/3-2 ordering, sparse count-table contract, discipline identity, and all two-strike rescue safeguards.
- Existing deterministic replay, discipline monotonicity, HBP, two-strike foul survival, KBO inning rules, natural-event invariants, save/load, and gameplay integration tests PASS.
- 40k deterministic count sanity independently measured 3-0 Swing 5.336%, Z-Swing 6.202%, Chase 4.272%; 3-1 Swing 30.774%; 3-2 Swing 51.052%.
- Full Python discover: 361 tests, 360 PASS, 1 FAIL.
- Sole failure remains the pre-existing/out-of-scope `test_balance_v04.test_draft_distribution_not_extreme` (`undrafted=5.667%`, historical assertion >10%). It does not exercise gameplay and was not modified.
- Therefore the overall workflow is not globally green only because of the unrelated draft gate; Gameplay / Phase-1 / production-integration regressions are green.

## 05 HANDOFF
05 should perform the final canonical signoff on the PR #58 candidate or post-integration main after this 3-0 change.
Confirm:
1. Neutral 3-0 Swing remains around ~5%, with nonzero player differentiation.
2. 3-1 remains around the established ~31% behavior and 3-2 around ~51–52%.
3. Generated Chase remains near ~27.7%.
4. Neutral/production K remains around ~18%, BB around ~9%, HBP around ~1.3%.
5. Looking-K remains near ~41% and does not regress.
6. No material offense explosion or deterministic/full-game invariant regression.

## OPEN ITEMS
- This final 3-0 adjustment is closed at the 01 implementation/validation level.
- 05 final canonical signoff remains required before project-wide Phase 1 is declared closed.
- The legacy draft-distribution test remains outside 01 scope.
- Phase 2 Physical Batted-Ball Engine must not start until 05 records final Phase-1 acceptance.

## RELATED PRS
- #58 OPEN / mergeable — Phase 1 plate discipline and contact calibration, including looking-K blocker fix and final 3-0 selectivity adjustment.

## GATES
- THREE_ZERO_NEUTRAL_SWING_TARGET = PASS
- THREE_ZERO_HARD_ZERO = NO
- THREE_ZERO_PLAYER_IDENTITY = PASS
- THREE_ONE_BEHAVIOR = PASS_PRESERVED
- THREE_TWO_BEHAVIOR = PASS_PRESERVED
- TWO_STRIKE_PROTECTION = PASS_UNCHANGED
- TWO_STRIKE_TAKE_RESCUE = PASS_UNCHANGED
- LOOKING_K_FIX = PASS_PRESERVED
- GENERATED_CHASE = PASS_PRESERVED
- BB_K_HBP_ENVIRONMENT = PASS
- DISCIPLINE_MONOTONICITY = PASS
- TWO_STRIKE_FOUL_SURVIVAL = PASS
- DETERMINISTIC_REPLAY = PASS
- PHYSICAL_BATTED_BALL_CHANGED = NO
- GAMEPLAY_INTEGRATION_REGRESSION = PASS
- FULL_PYTHON_SUITE = BLOCKED_BY_OUT_OF_SCOPE_DRAFT_GATE_360_OF_361_PASS
- PHASE1_05_FINAL_SIGNOFF = OPEN
- PHASE2_ALLOWED = PENDING_05_SIGNOFF
