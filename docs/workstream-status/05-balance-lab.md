# 05 - Balance Lab

WORKSTREAM: 05 - Balance Lab
UPDATED_AT: 2026-09-11
SOURCE_OF_TRUTH: task-start main@b764e4b32dcdc4af9947e83b9732e41b8be6d396; PR58@25e6771a41ab0bffc94ca7d8838a47d3cf5493ea; validation run@88fedf18411c9bbd43080653edf5844d3c7f1bad
STATE: DONE
CURRENT_TASK: Phase 1 independent heavy validation after count-specific swing calibration
RESULT: PHASE1_OPEN_LOOKING_K_BLOCKER

## EXECUTION
- Validation only. No count modifier, chase baseline/slope, contact/foul/HBP probability, HR/XBH, rating/generation, growth, event, or pitcher-usage production constant was changed by 05.
- Task-start main: `b764e4b32dcdc4af9947e83b9732e41b8be6d396`.
- PR #58 production candidate: `feature/phase1-plate-discipline-contact@25e6771a41ab0bffc94ca7d8838a47d3cf5493ea`, OPEN and mergeable at validation start.
- 05 created `validation/phase1-heavy-05` directly from PR #58 HEAD and added validation-only instrumentation/workflow; production simulation source remains the PR #58 candidate.
- GitHub Actions run `34597106109` completed SUCCESS on validation checkout `88fedf18411c9bbd43080653edf5844d3c7f1bad`.
- Artifact: `phase1-heavy-34597106109-88fedf18411c9bbd43080653edf5844d3c7f1bad`, ID `10261414463`, SHA256 `af88c5a9e04d2acf06b21027072df6f5d0680863711dcbe04eed75504095c5c3`.
- Seed: `20260906` base deterministic policy.
- Samples: neutral 200,000 PA; generated-prospect 200,000 PA; 10,000 production full games.
- Representative mature production roster = OPEN. `ProductionGameProvider` still defaults to `DeterministicNeutralLineupProvider`; no canonical mature-roster lineup provider is available without inventing a non-production population.

## NEUTRAL_200K
- Zone 55.037%; Swing 47.314%; Z-Swing 68.851%; Chase 20.952%.
- Contact/Swing 78.219%; Z-Contact 80.974%; O-Contact 67.135%; Whiff/Swing 21.781%.
- Swinging strike/pitch 10.305%; called strike/pitch 17.143%; foul/pitch 15.122%; two-strike fouls 12.776 per 100 PA.
- Pitches/PA 3.2456.
- BB 9.138%; K 18.579%; HBP 1.249%; H/PA 24.341%; HR/PA 2.790%.
- K split: swinging 45.595%, looking 54.405%.

## GENERATED_PROSPECT_200K
- Zone 55.052%; Swing 48.299%; Z-Swing 65.077%; Chase 27.749%.
- Contact/Swing 75.473%; Z-Contact 79.062%; O-Contact 65.162%; Whiff/Swing 24.527%.
- Swinging strike/pitch 11.847%; called strike/pitch 19.226%; foul/pitch 15.184%; two-strike fouls 13.423 per 100 PA.
- Pitches/PA 3.2321.
- BB 7.156%; K 22.817%; HBP 1.285%; H/PA 17.400%; HR/PA 1.559%.
- K split: swinging 44.857%, looking 55.143%.
- Previous generated-prospect chase reference was ~33.57%; current 27.75% is -5.82 percentage points (~17.3% relative reduction). Generated chase pathology is materially improved.

## DISCIPLINE_BUCKET_CHASE
Generated prospect thresholds from this sample: low <=66, high >=80.
- Low discipline: 68,338 PA probe; Chase 32.026%; Swing 48.828%; K 24.986%; BB 6.038%.
- Mid discipline: 63,042 PA; Chase 27.705%; Swing 48.287%; K 22.924%; BB 7.194%.
- High discipline: 68,620 PA; Chase 23.466%; Swing 47.656%; K 20.825%; BB 8.401%.
- SAME_COUNT / population discipline ordering = PASS: better discipline still materially reduces chase; differentiation was not erased.
- Low-discipline tail remains high but no longer causes the entire generated population to sit near the prior ~33.6% chase level.

## COUNT_SPECIFIC_NEUTRAL_200K
| Count | Reach/PA | Swing | Z-Swing | Chase | Contact | Whiff/Swing | Foul/Swing | Called strike/pitch | Looking-K / reach | Swinging-K / reach |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 3-0 | 4.382% | 14.982% | 20.939% | 7.276% | 78.903% | 21.097% | 31.531% | 44.592% | 0 | 0 |
| 3-1 | 7.704% | 31.678% | 46.221% | 13.752% | 78.918% | 21.082% | 32.555% | 29.692% | 0 | 0 |
| 3-2 | 9.926% | 47.948% | 73.422% | 17.139% | 78.218% | 21.782% | 31.822% | 14.549% | 17.158% | 12.317% |
| 0-2 | 18.339% | 53.240% | 78.574% | 22.355% | 78.677% | 21.323% | 32.329% | 11.771% | 14.202% | 13.698% |
| 1-2 | 20.474% | 52.113% | 76.508% | 22.019% | 78.646% | 21.354% | 32.594% | 12.974% | 15.618% | 13.395% |
| 2-2 | 15.251% | 50.772% | 74.288% | 21.407% | 78.457% | 21.543% | 32.363% | 14.278% | 17.068% | 13.075% |

Representative neutral 1-1 Swing = 47.343%, Z-Swing 68.322%, Chase 21.215%.

## COUNT_RELATIONAL_GATES
- 3-0 Swing < 3-1 Swing: 14.98% < 31.68% = PASS.
- 3-1 Swing < representative neutral 1-1: 31.68% < 47.34% = PASS.
- 3-2 Z-Swing >> 3-0 Z-Swing: 73.42% vs 20.94% = PASS.
- 3-2 Chase does not explode: 17.14%, below 0-2/1-2/2-2 ~21-22% = PASS.
- 0-2/1-2/2-2 protection is primarily zone protection: Z-Swing 74-79% while Chase remains ~21-22% = PASS.
- Discipline identity/monotonicity = PASS.

## LOOKING_K_DECOMPOSITION
Neutral 200k PA: 37,158 total K; 20,216 looking and 16,942 swinging by terminal two-strike count reconstruction, matching the measured 54.405% looking share.
Looking-K origin share:
- 0-2: 5,209 = 25.77% of looking Ks.
- 1-2: 6,395 = 31.63%.
- 2-2: 5,206 = 25.75%.
- 3-2: 3,406 = 16.85%.
- 3-0 and 3-1 produce zero terminal K directly because they are not two-strike counts.

Root-cause conclusion:
- The ~54-55% looking-K share is NOT primarily a direct consequence of 3-0/3-1 selectivity.
- It is generated by the two-strike take/called-strike termination path across all four two-strike counts.
- Per-reach terminal looking-K is ~14.2% at 0-2, 15.6% at 1-2, 17.1% at 2-2, and 17.2% at 3-2.
- Therefore a further 01 review should focus on two-strike strike recognition/take/called-strike semantics while preserving the successful 3-0/3-1 and chase improvements.

## FULL_PRODUCTION_10K
Seed `20260906`, 10,000 neutral production games through `ProductionGameProvider`:
- PA/game 80.0257.
- Runs/game 9.2931.
- Hits/game 19.1173.
- HR/game 2.1573.
- BB/game 7.3938.
- K/game 14.7568.
- HBP/game 1.0507.
- BB/PA 9.239%; K/PA 18.440%; HBP/PA 1.313%; H/PA 23.889%; HR/PA 2.696%.
- AVG .2677; SLG .4068; ISO .1391.
- Runs P10/P25/P50/P75/P90/P95/P99 = 4/6/9/12/16/18/23; max 32.
- Hits = 13/15/19/23/26/28/32; max 43.
- BB = 4/5/7/9/11/13/15; max 20.
- K = 10/12/15/17/19/21/23; max 28.
- HBP = 0/0/1/2/2/3/4; max 7.
- PA = 70/74/79/85/91/95/102; max 121.

## KBO_REFERENCE_COMPARISON
Completed 2022-25 KBO reference center: runs/game 9.617; hits/game 18.237; HR/game 1.610; BB/game 7.103; K/game 14.684; PA/game 78.283; HBP/PA ~1.33%; BB% ~9.07%; K% ~18.76%; HR% ~2.06%.
- Runs/game 9.293 = -3.4% -> PASS/WATCH, large improvement from pre-Phase1 8.136.
- Hits/game 19.117 = +4.8% -> WATCH.
- BB/game 7.394 = +4.1%; BB/PA 9.239% -> PASS.
- K/game 14.757 = +0.5%; K/PA 18.440% -> PASS.
- HBP/game 1.051 and HBP/PA 1.313% -> PASS versus ~1.044/game / ~1.33% reference.
- HR/game 2.157 and HR/PA 2.696% remain materially high -> FAIL, but physical HR model is explicitly unchanged Phase-1 non-scope.
- PA/game 80.026 = +2.2% -> WATCH.

2026 in-progress secondary pitch-tracking context only: Swing ~44.8%, Chase ~26.7-27.0%, Z-Swing ~64.3%, Whiff/swing ~21.0%, Z-Contact ~86.9%. This is not an official completed-season target.
- Neutral chase 20.95% remains low vs this secondary reference; generated 27.75% is close.
- Neutral/generated Z-Contact 80.97/79.06% remain below the secondary ~86.9% reference -> WATCH.
- Neutral Whiff 21.78% is close; generated 24.53% remains high -> WATCH.

Looking-K reference remains imperfect but strongly adverse: no exact recent league-wide matched split is available; a 2025 KBO-attributed snapshot reports KIA, which led the league in looking Ks, at only 27.1% looking share. Older league reporting is also around the mid-20s. The current 54-55% simulation share is therefore unsupported and remains a strong blocker even though the exact modern league mean is OPEN.

## REGRESSION_FINDINGS
- Count-specific behavioral contract = PASS.
- Generated chase pathology materially resolved = PASS/WATCH.
- BB/K environment = PASS in 10k production aggregate.
- HBP path = PASS and aligns closely with KBO reference.
- Pitches/PA ~3.23-3.25; no pitch-count explosion = PASS.
- No major H/PA collapse: 10k H/PA 23.889% vs recent KBO ~23.29% = PASS/WATCH.
- No Phase-1 HR explosion relative to prior model, but pre-existing physical HR bias remains FAIL and is Phase-2/non-scope.
- Mature production roster population = OPEN because no canonical production roster lineup provider exists yet.
- Looking-K share = FAIL/WATCH and blocks Phase1 exit.

## PHASE1_EXIT_GATE
PHASE1 = OPEN.
Reason: all intended count behavior is stable, generated chase pathology is materially improved, BB/K/HBP and run environment are substantially improved, and no major H/PA regression occurred. However neutral and generated heavy samples retain ~54-55% looking-K share. The model cause is identifiable in the two-strike take/called-strike path, and available KBO evidence does not support this level. One more 01 handoff is required before Phase 1 can be closed.

Phase 2 Physical Batted-Ball Engine = BLOCKED pending Phase1 PASS.

## 01_HANDOFF
- Preserve the current sparse count-specific ordering and generated-chase improvement; do not undo 3-0/3-1 selectivity to solve looking K.
- Focus review on two-strike strike-recognition/take/called-strike terminal behavior at 0-2, 1-2, 2-2, and 3-2.
- Preserve overall K% near current production 18.44%, BB% near 9.24%, HBP ~1.31%, and current discipline monotonicity while reducing the looking-K share.
- Do not change physical HR/XBH/defense/park logic until Phase1 is explicitly revalidated and passed.

## GATES
- PHASE1_COUNT_SPECIFIC_BEHAVIOR = PASS
- GENERATED_CHASE_PATHOLOGY = PASS_WATCH
- DISCIPLINE_CHASE_MONOTONICITY = PASS
- BB_K_ENVIRONMENT = PASS
- HBP_PATH = PASS
- PITCHES_PER_PA = PASS
- H_PER_PA_REGRESSION = PASS_WATCH
- HR_PHASE1_REGRESSION = PASS / PREEXISTING_PHYSICAL_HR_BIAS = FAIL
- LOOKING_K_SHARE = FAIL_WATCH
- MATURE_PRODUCTION_ROSTER = OPEN
- PHASE1 = OPEN
- PHASE2_PHYSICAL_BATTED_BALL = BLOCKED
