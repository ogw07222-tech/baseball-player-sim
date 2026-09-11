# 01 - Gameplay Engine

WORKSTREAM: 01 - Gameplay Engine
UPDATED_AT: 2026-09-11
SOURCE_OF_TRUTH: task-start main@b764e4b32dcdc4af9947e83b9732e41b8be6d396; implementation PR #58
STATE: READY_FOR_05_VALIDATION
CURRENT_TASK: Phase 1 count-specific situational swing modifiers
RESULT: COUNT_SITUATIONAL_PASS / PHASE1_HEAVY_VALIDATION_OPEN

## SCOPE
- Phase 1 only: count-specific situational swing behavior layered on existing player identity, pitch location, pitch quality, contact/foul, and HBP systems.
- Physical batted-ball model remains unchanged: no exit velocity, launch angle, spray angle, trajectory, park, HR, 2B/3B, defense, baserunning, rating-generation, growth, or event/story tuning.
- MISS is never converted directly to HIT/BIP.

## TASK-START STATE
- Latest main at task start: `b764e4b32dcdc4af9947e83b9732e41b8be6d396`.
- PR #58 remained OPEN, mergeable, and the appropriate Phase-1 branch: `feature/phase1-plate-discipline-contact`.
- Pre-task runtime count logic used generalized independent two-strike / three-ball terms rather than explicit count situations.
- Pre-task zone-swing clamp floor was 0.34, which prevented a genuinely strong 3-0 take tendency regardless of how negative a count modifier became.

## COUNT MODEL
Runtime now uses a sparse explicit additive table. Unlisted counts receive `(0.0, 0.0)` and therefore retain the existing neutral model.

`COUNT_SWING_MODIFIERS[(balls, strikes)] = (zone_swing, chase)`:
- 2-0: `(-0.035, -0.030)` — modest hitter-count selectivity.
- 0-2: `(+0.100, +0.005)` — strong zone protection, almost no chase increase.
- 1-2: `(+0.085, +0.000)` — zone protection without chase inflation.
- 2-2: `(+0.065, -0.005)` — moderate zone protection, slightly selective chase.
- 3-0: `(-0.470, -0.145)` — strong situational suppression, not hard-zero.
- 3-1: `(-0.220, -0.090)` — substantial selectivity while allowing hittable strikes.
- 3-2: `(+0.045, -0.045)` — strike protection plus three-ball selectivity simultaneously.

Player identity remains in the probability equation:
- Zone swing still includes `ZONE_SWING_BASE + discipline effect + location effect + count modifier`.
- Chase still includes `BALL_CHASE_BASE - discipline effect + pitch hittability effect + count modifier`.
- Same-count discipline ordering remains monotonic in tests.
- Zone-swing clamp is now parameterized at `[0.06, 0.91]`; the lower floor change exists only so strong 3-0 suppression can be represented. Neutral-count probabilities are far above that floor.

## COUNT-SPECIFIC MEASUREMENT
Deterministic neutral-vs-neutral diagnostic, seed `20260911`, 40,000 PA. These are representative implementation measurements, not the final 05 heavy calibration result.

| Count | Reach/PA | Swing | Z-Swing | Chase |
| --- | ---: | ---: | ---: | ---: |
| 0-2 | 35.865% | 53.369% | 77.685% | 23.137% |
| 1-2 | 20.208% | 52.866% | 77.269% | 21.181% |
| 2-2 | 14.883% | 50.667% | 74.608% | 20.690% |
| 2-0 | 12.165% | 45.520% | 65.792% | 19.283% |
| 3-0 | 8.530% | 15.064% | 20.708% | 8.269% |
| 3-1 | 15.360% | 31.738% | 47.585% | 12.688% |
| 3-2 | 19.430% | 47.367% | 71.870% | 18.374% |

Observed behavioral gates:
- 3-0 Swing < 3-1 Swing: PASS.
- 3-1 Swing < comparable neutral 1-1: PASS (`31.74% < 46.84%`).
- 3-2 Z-Swing > 3-0 Z-Swing: PASS (`71.87% > 20.71%`).
- 3-2 Chase remains below 0-2 and below neutral-count chase region: PASS.
- 0-2/1-2/2-2 protection is concentrated in Z-Swing rather than large chase inflation: PASS.
- 3-0 is strongly suppressed but not absolute zero: PASS.

## GLOBAL BEFORE / AFTER
Prior PR #58 provisional neutral sensitivity was a 100k run with a different seed, so the comparison is directional rather than an exact paired A/B.

Prior provisional -> count-specific 40k:
- Zone: 55.10% -> 55.137%.
- Swing: 48.23% -> 47.253%.
- Z-Swing: 70.06% -> 68.721%.
- Chase: 21.45% -> 20.869%.
- Contact/Swing: 78.31% -> 78.485%.
- Whiff/Swing: 21.69% -> 21.515%.
- Z-Contact: 80.92% -> 81.114%.
- O-Contact: 67.82% -> 67.845%.
- Called strike/pitch: 16.50% -> 17.246%.
- Swinging strike/pitch: 10.46% -> 10.166%.
- Foul/pitch: 15.40% -> 15.003%.
- Pitches/PA: 3.23 -> 3.225.
- BB: 8.33% -> 9.063%.
- K: 18.13% -> 18.368%.
- Looking-K share: 53.34% -> 54.703%.
- HBP: 1.28% -> 1.358%.
- H/PA: 24.55% -> 24.17%.
- HR/PA: 2.80% -> 2.83%.

Interpretation:
- Count behavior moved in the intended baseball direction without PA-length or offense explosion.
- H/PA decreased modestly and HR/PA stayed effectively flat in this representative sample; no HR/XBH model parameter was touched.
- BB rose while overall K stayed near the prior Phase-1 provisional level.
- Looking-K share rose to 54.70% in this 40k sample. Reducing looking-K remains an explicit Phase-1 heavy-validation/tuning watch item; this subtask must not be treated as final Phase-1 calibration acceptance.

## REGRESSION / CI
PR #58 code checkpoint `f6c74a0191041d41ffc3e20a3a839130ee7d668e`.
GitHub Actions run `34594997988`:
- Web build/tests PASS.
- Compile, Python dependency contract, durable-store tests, API entrypoint, API vertical-slice PASS.
- Related production integration: 31/31 PASS.
- New `test_phase1_count_situational` coverage PASS: sparse table, 3-0/3-1/3-2 ordering, two-strike protection without chase explosion, same-count discipline identity, nonzero 3-0 differentiation, frozen batted-ball/HR constants, and actual 40k count/global measurement guardrails.
- Existing two-strike foul survival, HBP path, deterministic replay, save/load, count/game invariants, natural-event sanity, and gameplay monotonicity tests shown in the suite PASS.
- Full Python discover: 358 tests, 357 PASS, 1 FAIL.
- Sole failure remains out-of-scope `test_balance_v04.test_draft_distribution_not_extreme` (`undrafted=6.0%`, historical assertion >10%). That test calls `Player.random()` + `CareerEngine.evaluate_draft()` and no gameplay path; this task did not alter generation or draft evaluation and the same gate already failed earlier on PR #58. It is intentionally not weakened here.
- Because that unrelated unit failure stops the workflow, later auto-career/balance/draft workflow steps are skipped. Do not classify the overall workflow as green; classify the gameplay/count-specific and production-integration gates as green.

## 05 HANDOFF
After PR #58 integration, rerun canonical Phase-1 validation with consistent seeds/sample definitions:
1. Neutral 100 vs neutral 100: >=200k PA and 10k full games.
2. Generated prospect hitters vs neutral pitcher: >=200k PA.
3. Representative mature production roster population if available.
4. For every population report count reach, Swing%, Z-Swing%, and Chase% for at least 3-0, 3-1, 3-2, 0-2, 1-2, and 2-2; retain all-count table if practical.
5. Global metrics: Zone, Swing, Z-Swing, Chase, Contact, Z/O-Contact, Whiff, called/swinging strike, foul, two-strike foul, BB, K, looking/swinging-K split, HBP, pitches/PA, H/PA, HR/PA, runs/game.
6. Explicit gates: 3-0 remains strongly suppressed without erasing player differentiation; generated low-discipline chase does not re-expand; no PA/pitch-count explosion; no material H/HR/runs explosion.
7. Specifically re-evaluate looking-K share. Current 40k count-specific sample is 54.70%, so final Phase-1 PASS requires deciding whether further called-strike/2-strike tuning is needed rather than assuming this subtask solved it.
8. Validate deterministic replay, legal counts, no infinite PA, safety-cap hits=0, and full-game invariants.

## OPEN ITEMS
- 05 canonical heavy validation is required before declaring the entire Phase 1 calibrated for production.
- Looking-K share remains OPEN and is the primary global side-effect watch item from this subtask.
- Mature-roster population comparison depends on available 02/05 production population tooling/data.
- The unrelated draft-distribution unit gate remains outside 01 scope.
- Phase 2 Physical Batted-Ball Engine remains blocked until Phase-1 heavy validation is accepted.

## RELATED PRS
- #58 open — Phase 1 plate discipline and contact calibration; this count-specific work is integrated into the same branch/PR.

## GATES
- COUNT_SITUATIONAL_MODIFIER_STRUCTURE = PASS
- COUNT_SPECIFIC_BEHAVIOR = PASS
- PLAYER_IDENTITY_WITHIN_COUNT = PASS
- TWO_STRIKE_PROTECTION_WITHOUT_CHASE_EXPLOSION = PASS
- FAIR_CONTACT_HR_XBH_MODEL_CHANGED = NO
- HBP_REGRESSION = PASS
- TWO_STRIKE_FOUL_REGRESSION = PASS
- GAMEPLAY_INTEGRATION_REGRESSION = PASS
- GLOBAL_OFFENSE_EXPLOSION = NOT_OBSERVED_IN_40K
- LOOKING_K_SHARE = OPEN_HEAVY
- FULL_PYTHON_SUITE = BLOCKED_BY_OUT_OF_SCOPE_DRAFT_GATE_357_OF_358_PASS
- PHASE1_05_HEAVY_VALIDATION = OPEN
- PHASE2_ALLOWED = NO_UNTIL_05_VALIDATION
