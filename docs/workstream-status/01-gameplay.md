# 01 - Gameplay Engine

WORKSTREAM: 01 - Gameplay Engine
UPDATED_AT: 2026-09-11
SOURCE_OF_TRUTH: task-start main@34ac1fc35b5616fade75721221e95aeea3398232; PR #58 production-code checkpoint@feb2920fe35922f167bc750ec1eaff096393ed6e; code/test checkpoint@27859c86cea0fe7449ae952c0cde57cc296f9562
STATE: READY_FOR_05_FINAL_SIGNOFF
CURRENT_TASK: Phase 1 final blocker — two-strike looking-K reduction
RESULT: PASS

## SCOPE
- Phase 1 only: reduce excessive called strikeouts on two-strike in-zone takes without undoing the accepted count-specific swing model.
- Preserve sparse count modifiers, 3-0/3-1 selectivity, generated chase improvement, BB/K/HBP environment, discipline identity, two-strike foul survival, and deterministic replay.
- No HR/XBH/exit-quality/launch/spray/trajectory/defense/park/baserunning/rating-generation/growth/event tuning.
- MISS is never converted directly to HIT/BIP.

## TASK-START STATE
- Latest main at task start: `34ac1fc35b5616fade75721221e95aeea3398232` (`docs: record independent Phase 1 heavy validation`).
- PR #58 remained OPEN and mergeable on `feature/phase1-plate-discipline-contact`.
- 05 canonical heavy validation on the previous Phase-1 candidate classified count behavior, generated chase, BB/K, HBP, and discipline monotonicity as acceptable, but left Phase 1 OPEN because looking-K remained excessive.
- Pre-fix neutral 200k: K 18.579%, looking-K share 54.405%, swinging-K share 45.595%, BB 9.138%, HBP 1.249%, Chase 20.952%.
- Pre-fix generated 200k: K 22.817%, looking-K share 55.143%, Chase 27.749%.
- Pre-fix two-strike looking-K/reach: 0-2 14.202%, 1-2 15.618%, 2-2 17.068%, 3-2 17.158%.

## ROOT CAUSE
- The blocker was not 3-0/3-1 selectivity.
- Across 0-2 / 1-2 / 2-2 / 3-2, an in-zone pitch that lost the normal swing roll remained a pure take. With two strikes, that take immediately became strike three and a looking K.
- Raising all swing probabilities or chase would have damaged already-passing Phase-1 behavior, so the fix targets only the terminal two-strike in-zone take path.

## IMPLEMENTATION
The accepted `COUNT_SWING_MODIFIERS` table is unchanged:
- 2-0: `(-0.035, -0.030)`
- 0-2: `(+0.100, +0.005)`
- 1-2: `(+0.085, +0.000)`
- 2-2: `(+0.065, -0.005)`
- 3-0: `(-0.470, -0.145)`
- 3-1: `(-0.220, -0.090)`
- 3-2: `(+0.045, -0.045)`

Added a bounded late two-strike take-rescue path:
- Trigger eligibility: `strikes == 2`, `pitch.is_strike`, and the original normal swing roll chose TAKE.
- Out-of-zone pitches are never rescued, so Chase math and three-ball selectivity are not directly changed.
- Rescue probability is bounded 18%–42% and depends modestly on hitter discipline and pitch hittability.
- Better-recognized/easier strikes are more likely to receive a late protection attempt.
- The rescued attempt is not a normal offensive swing. It uses a strongly reduced touch probability and a high foul tendency so the primary redistribution is called-K -> swinging-K / foul survival rather than called-K -> fair-ball hit.
- Normal swings, normal contact resolution, fair-contact quality, HR/XBH, defense and baserunning remain unchanged.

Production parameters:
- `TWO_STRIKE_TAKE_RESCUE_BASE = 0.280`
- `TWO_STRIKE_TAKE_RESCUE_HITTABLE_WEIGHT = 0.080`
- `TWO_STRIKE_TAKE_RESCUE_DISCIPLINE_WEIGHT = 0.0010`
- rescue bounds `[0.18, 0.42]`
- protective touch scale `0.25`, bounds `[0.10, 0.38]`
- protective miss-to-foul `0.06`
- protective foul bonus `0.30`, bounds `[0.45, 0.78]`

## FINAL HEAVY VALIDATION
Validation-only branch `validation/phase1-looking-k-final` was based on the exact production-code checkpoint `feb2920fe35922f167bc750ec1eaff096393ed6e`. The validation workflow itself was isolated from PR #58 and is not intended for integration.

GitHub Actions heavy run `34599008227`: SUCCESS.
Sample contract:
- Neutral hitter 100 vs neutral pitcher 100: 200,000 PA.
- Generated prospect hitter population vs neutral pitcher: 200,000 PA.
- Production full games: 10,000 games.
- Seed: `20260906`.

### Neutral 200k
- Zone: 55.028%
- Swing: 48.212%
- Z-Swing: 70.471%
- Chase: 20.976%
- Contact/Swing: 77.289%
- Z-Contact: 79.677%
- O-Contact: 67.470%
- Whiff/Swing: 22.711%
- Called strike/pitch: 16.249%
- Swinging strike/pitch: 10.950%
- Foul/pitch: 15.260%
- Two-strike foul/PA: 13.432%
- Protective swing/PA: 3.009%
- Pitches/PA: 3.253
- BB: 9.206%
- K: 17.916%
- HBP: 1.314%
- H/PA: 24.514%
- HR/PA: 2.746%
- Looking-K share: 40.785%
- Swinging-K share: 59.215%

Compared with the pre-fix 05 heavy candidate:
- Looking-K share: 54.405% -> 40.785% (-13.620 pp).
- Chase: 20.952% -> 20.976% (effectively unchanged).
- K: 18.579% -> 17.916%; the corresponding 10k production K/PA is 18.027%, so the target ~18–19% environment remains represented.
- BB/HBP remain in the accepted Phase-1 region.

### Generated prospects 200k
- Swing: 49.304%
- Z-Swing: 66.955%
- Chase: 27.730%
- Contact/Swing: 74.299%
- Z-Contact: 77.482%
- O-Contact: 64.905%
- Whiff/Swing: 25.701%
- Called strike/pitch: 18.175%
- Swinging strike/pitch: 12.672%
- Foul/pitch: 15.351%
- Two-strike foul/PA: 14.147%
- Protective swing/PA: 3.354%
- Pitches/PA: 3.247
- BB: 7.285%
- K: 22.331%
- HBP: 1.295%
- Looking-K share: 41.796%
- Swinging-K share: 58.204%
- Generated Chase is preserved: 27.749% pre-fix -> 27.730% post-fix.

### Production 10k full games
- PA/game: 80.259
- Runs/game: 9.537
- Hits/game: 19.321
- HR/game: 2.221
- BB/game: 7.474
- K/game: 14.469
- HBP/game: 1.065
- BB/PA: 9.312%
- K/PA: 18.027%
- HBP/PA: 1.327%
- H/PA: 24.073%
- HR/PA: 2.767%
- AVG: .2700
- SLG: .4117
- ISO: .1417

Relative to the prior 05 10k run, runs/game (9.293 -> 9.537) and HR/PA (2.696% -> 2.767%) moved modestly upward despite no physical hitting parameter change. This is not an offense explosion in the current sample but should remain a 05 watch item during final acceptance.

## TWO-STRIKE COUNT RESULTS — NEUTRAL 200k
| Count | Reach/PA | Swing | Take | Z-Swing | Chase | Protective swing/reach | Looking-K/reach | Swinging-K/reach |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0-2 | 36.665% | 56.890% | 43.110% | 84.649% | 22.294% | 2.201% | 5.167% | 8.546% |
| 1-2 | 20.401% | 55.751% | 44.249% | 83.279% | 21.801% | 4.664% | 11.193% | 16.911% |
| 2-2 | 15.283% | 54.778% | 45.222% | 81.945% | 21.031% | 4.871% | 12.072% | 16.312% |
| 3-2 | 20.017% | 51.422% | 48.578% | 79.624% | 17.278% | 2.518% | 6.637% | 7.496% |

Looking-K/reach improvement versus pre-fix:
- 0-2: 14.202% -> 5.167%
- 1-2: 15.618% -> 11.193%
- 2-2: 17.068% -> 12.072%
- 3-2: 17.158% -> 6.637%

Accepted count structure remains intact:
- 3-0: Swing 15.081%, Z-Swing 21.150%, Chase 7.599%, protective rescue 0.
- 3-1: Swing 31.816%, Z-Swing 46.854%, Chase 13.666%, protective rescue 0.
- The rescue therefore does not undo three-ball selectivity.

## TESTS / REGRESSION
Final PR code/test checkpoint: `27859c86cea0fe7449ae952c0cde57cc296f9562`.
Regular CI run `34599298416`:
- Web build/tests PASS.
- Compile PASS.
- Dependency contract PASS.
- External durable-store tests PASS.
- API entrypoint/vertical-slice PASS.
- Related production integration: 31/31 PASS.
- Phase-1 count/two-strike tests PASS, including:
  - sparse modifier table unchanged,
  - 3-0/3-1 ordering,
  - rescue is in-zone only,
  - discipline-sensitive rescue,
  - hittability-sensitive strike recognition,
  - protective swing is lower-touch/high-foul rather than a fair-contact bonus,
  - generated chase contract remains structurally untouched,
  - frozen HR/XBH/physical parameters,
  - 40k deterministic count/global sanity.
- Existing deterministic replay, HBP path, two-strike foul survival, save/load, natural-event, inning/game, and integration regressions shown in the suite PASS.
- Full Python discover: 361 tests, 360 PASS, 1 FAIL.
- Sole failure remains the pre-existing/out-of-scope `test_balance_v04.test_draft_distribution_not_extreme` (`undrafted=5.667%`, historical assertion >10%). The failure does not exercise the gameplay engine and predates this blocker fix. It was not weakened or modified.
- The workflow is therefore not globally green due to that unrelated draft gate; the Gameplay / Phase-1 / production-integration gates are green.

## 05 HANDOFF
05 should canonicalize/final-sign-off this blocker on the PR #58 candidate or post-integration main rather than retune it immediately.
Required confirmation:
1. Looking-K remains around the ~41% region rather than reverting toward 54–55%.
2. Neutral/production K remains around the accepted ~18% environment.
3. Generated Chase remains near the already-accepted ~27.7% level with discipline monotonicity preserved.
4. BB/HBP remain stable.
5. Count ordering and 3-0/3-1 selectivity remain intact.
6. Re-check the modest production offense shift (runs/game 9.537, HR/PA 2.767%) as a watch item, noting that HR/XBH/physical batted-ball parameters are unchanged.
7. Confirm deterministic replay and full-game invariants on the final integration SHA.

## OPEN ITEMS
- Phase-1 looking-K blocker is closed at the 01 implementation/validation level.
- 05 final canonical signoff remains required before project-wide Phase 1 is declared closed.
- The legacy draft-distribution test remains outside 01 scope.
- Phase 2 Physical Batted-Ball Engine must not start until 05 records final Phase-1 acceptance.

## RELATED PRS
- #58 OPEN / mergeable — Phase 1 plate discipline and contact calibration, including the final two-strike looking-K blocker fix.

## GATES
- COUNT_SITUATIONAL_MODIFIER_STRUCTURE = PASS_UNCHANGED
- THREE_ZERO_THREE_ONE_SELECTIVITY = PASS
- TWO_STRIKE_TAKE_RESCUE = PASS
- LOOKING_K_SHARE = PASS_01_HEAVY
- NEUTRAL_K_ENVIRONMENT = PASS
- PRODUCTION_K_ENVIRONMENT = PASS
- GENERATED_CHASE = PASS_PRESERVED
- BB_HBP_ENVIRONMENT = PASS
- DISCIPLINE_IDENTITY = PASS
- TWO_STRIKE_FOUL_SURVIVAL = PASS
- DETERMINISTIC_GAMEPLAY = PASS
- FAIR_CONTACT_HR_XBH_PHYSICAL_MODEL_CHANGED = NO
- GAMEPLAY_INTEGRATION_REGRESSION = PASS
- FULL_PYTHON_SUITE = BLOCKED_BY_OUT_OF_SCOPE_DRAFT_GATE_360_OF_361_PASS
- PHASE1_05_FINAL_SIGNOFF = OPEN
- PHASE2_ALLOWED = PENDING_05_SIGNOFF
