# 05 - Balance Lab

WORKSTREAM: 05 - Balance Lab
UPDATED_AT: 2026-09-11
SOURCE_OF_TRUTH: task-start main@34ac1fc35b5616fade75721221e95aeea3398232; PR #58 head@6580d542bc90532e56c11a1f946d1dd399da81e5; production-code checkpoint@ac30469f00096ff6090c0143313dd7a940ace955; canonical validation checkout@49e7657ddd099adc34e8e3559896dda027af1608
STATE: DONE
CURRENT_TASK: Phase 1 final canonical signoff
RESULT: PASS

## FINAL_DECISION
- PHASE1 = PASS.
- PHASE1_STATE = CLOSED.
- PR #58 = INTEGRATION_READY from 05 validation perspective.
- PHASE2_PHYSICAL_BATTED_BALL = ALLOWED.
- Phase 2 implementation was not performed in this task.
- Known physical HR/XBH/trajectory/defense/park limitations remain Phase-2 scope and are not reclassified as Phase-1 regressions.

## SOURCE_STATE
- Task-start latest main: `34ac1fc35b5616fade75721221e95aeea3398232`.
- Latest PR #58 at signoff: `6580d542bc90532e56c11a1f946d1dd399da81e5`, OPEN / mergeable.
- 01 identifies exact Phase-1 production-code checkpoint `ac30469f00096ff6090c0143313dd7a940ace955`.
- PR HEAD is four commits ahead of that production checkpoint only through `docs/workstream-status/01-gameplay.md` and one-line protected-formula expectation updates in three tests; no later `src/` gameplay change exists.
- Latest PR CI `34600893464`: web/build, compile, durable/API and related production-integration gates PASS; overall workflow failure remains the pre-existing out-of-scope draft-distribution assertion.

## CANONICAL_EXECUTION
- Independent branch: `validation/phase1-final-signoff-05`.
- Validation checkout: `49e7657ddd099adc34e8e3559896dda027af1608`.
- Production gameplay code in this checkout is the exact PR #58 production checkpoint `ac30469f00096ff6090c0143313dd7a940ace955`; 05 only layered validation instrumentation/workflow and synchronized the current PR protected-formula test expectations.
- GitHub Actions run `34602493140`: SUCCESS.
- Seed policy: base seed `20260911`; deterministic offset streams for neutral/generated diagnostic populations.
- Samples: neutral 200,000 PA; generated prospects 200,000 PA; discipline buckets 200,000 generated PA; production full games 10,000.
- Artifact: `phase1-final-signoff-34602493140-49e7657ddd099adc34e8e3559896dda027af1608`, ID `10264344999`, digest `sha256:431909d892a8c70385651dc00662fa92f17ce589c3ba22817023d4e3ceed460f`.
- Canonical run PASS: compile; count-specific neutral 200k; neutral/generated 200k + production 10k; discipline buckets; Phase-1 deterministic/count regressions; targeted production integration regressions; artifact upload.

## NEUTRAL_200K
Dedicated count stream, seed `20260911`:
- Zone 54.975%; Swing 48.050%; Z-Swing 70.208%; Chase 20.995%.
- Contact/Swing 77.275%; Z-Contact 79.696%; O-Contact 67.387%; Whiff/Swing 22.725%.
- Called strike/pitch 16.378%; swinging strike/pitch 10.919%; foul/pitch 15.138%; two-strike foul/PA 13.409%.
- Pitches/PA 3.251.
- BB 9.359%; K 17.835%; HBP 1.315%.
- Looking-K share 41.144%; swinging-K share 58.856%.
- H/PA 24.412%; HR/PA 2.780%.
- Independent offset-stream offense diagnostic is consistent: BB 9.399%, K 17.874%, HBP 1.297%, looking-K 40.398%, H/PA 24.221%, HR/PA 2.781%.

## COUNT_SPECIFIC_FINAL
| Count | Reach/PA* | Swing | Z-Swing | Chase | Protective swing/reach | Looking K/reach | Swinging K/reach |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 3-0 | 8.761% | 4.646% | 5.916% | 3.081% | 0.000% | 0.000% | 0.000% |
| 3-1 | 15.528% | 31.556% | 46.526% | 12.871% | 0.000% | 0.000% | 0.000% |
| 3-2 | 20.024% | 52.001% | 80.329% | 17.167% | 2.604% | 6.485% | 7.896% |
| 0-2 | 36.402% | 56.983% | 84.532% | 22.826% | 2.012% | 5.219% | 8.454% |
| 1-2 | 20.364% | 56.210% | 83.610% | 21.981% | 4.547% | 11.052% | 16.773% |
| 2-2 | 15.159% | 54.246% | 81.210% | 21.044% | 4.862% | 12.461% | 15.984% |

`*` Reach/PA is the dedicated count-tracer opportunity metric; signoff relies on within-count rates and relational behavior, not cross-tool absolute reach comparability.

- 3-0 Swing near target ~5%, nonzero: PASS (`4.646%`).
- 3-0 < 3-1: PASS.
- 3-1 remains near established ~31%: PASS (`31.556%`).
- 3-2 protection/selectivity preserved: PASS (`Z-Swing 80.329%`, Chase 17.167%).
- 0-2/1-2/2-2 protection preserved with Z-Swing 81–85% and Chase 21–23%: PASS.

## GENERATED_PROSPECT_200K
- Zone 55.018%; Swing 49.310%; Z-Swing 66.974%; Chase 27.706%.
- Contact/Swing 74.242%; Z-Contact 77.439%; O-Contact 64.787%; Whiff/Swing 25.758%.
- Called strike/pitch 18.170%; swinging strike/pitch 12.702%; foul/pitch 15.301%; two-strike foul/PA 13.991%.
- Pitches/PA 3.243.
- BB 7.320%; K 22.247%; HBP 1.337%.
- Looking-K share 41.189%; swinging-K share 58.811%.
- H/PA 17.507%; HR/PA 1.535%.
- Generated Chase remains in the accepted ~27–28% region and does not regress toward the former ~33.6% pathology.

## DISCIPLINE_BUCKETS_200K
| Bucket | Definition | PA | Chase | Swing | BB | K | HBP | Looking-K share |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Low | Discipline <=66 | 68,619 | 31.868% | 49.974% | 6.039% | 24.234% | 1.360% | 42.480% |
| Mid | 67–79 | 62,647 | 27.943% | 49.367% | 7.167% | 22.092% | 1.306% | 41.756% |
| High | >=80 | 68,734 | 23.318% | 48.293% | 8.844% | 20.184% | 1.365% | 41.029% |

- Chase monotonicity Low > Mid > High: PASS.
- BB rises and K falls with discipline: PASS.
- Player differentiation retained.

## PRODUCTION_10K
Seed `20260911`, 10,000 full production-provider games:
- PA/game 80.449; Runs/game 9.5594; Hits/game 19.3175; HR/game 2.1883.
- BB/game 7.6208; K/game 14.4689; HBP/game 1.0592.
- BB/PA 9.473%; K/PA 17.985%; HBP/PA 1.317%; H/PA 24.012%; HR/PA 2.720%.
- AVG .2698; SLG .4099; ISO .1402.
- No distribution collapse/explosion: runs P10/P25/P50/P75/P90/P95/P99 = 4/6/9/12/16/18/23; hits 13/16/19/23/26/29/33; BB 4/6/7/9/12/13/15; K 10/12/14/17/19/20/23; HBP 0/0/1/2/2/3/4; PA 71/75/80/85/91/95/103.

## COMPARISONS
Previous independent 05 heavy candidate -> final:
- Neutral looking-K 54.405% -> 41.144%; generated 55.143% -> 41.189%: blocker materially resolved.
- Generated Chase 27.749% -> 27.706%: stable.
- Neutral BB 9.138% -> 9.359%; K 18.579% -> 17.835%; HBP 1.249% -> 1.315%.
- Production Runs/game 9.293 -> 9.559; BB/game 7.394 -> 7.621; K/game 14.757 -> 14.469; HBP/game 1.051 -> 1.059.
- H/PA 23.889% -> 24.012%; HR/PA 2.696% -> 2.720%: no Phase-1 offense collapse or HR step-change.

Latest 01 heavy -> final 05:
- Dedicated neutral stream reproduces 01 at seed `20260911`: 3-0 4.646%, 3-1 31.556%, 3-2 52.001%, BB 9.359%, K 17.835%, HBP 1.315%, looking-K 41.144%, Chase 20.995%, pitches/PA 3.251.
- Generated also reproduces 01: Chase 27.706%, BB 7.320%, K 22.247%, HBP 1.337%, looking-K 41.189%, pitches/PA 3.243.
- 01 supplemental 2k -> 05 10k stable: Runs/game 9.532 -> 9.559; BB/PA 9.352% -> 9.473%; K/PA 18.148% -> 17.985%; HBP/PA 1.352% -> 1.317%; HR/PA 2.706% -> 2.720%.

## KBO_REFERENCE_CONTEXT
- Recent completed-season KBO center from 08: Runs/game ~9.617; Hits/game ~18.237; HR/game ~1.610; BB/game ~7.103; K/game ~14.684; PA/game ~78.283; HBP/PA ~1.33%; BB% ~9.07%; K% ~18.76%; HR/PA ~2.06%.
- Production BB/K/HBP and runs environment are acceptable for Phase-1 exit. Hits/PA is mildly high but not a new regression.
- 2026 in-progress secondary pitch tracking puts Chase around 26.7–27%, Swing ~44.8%, Z-Swing ~64.3%, Whiff/swing ~21%; this is contextual, not an official completed-season reference.
- Exact modern league-wide KBO looking-K share remains unavailable. Available evidence includes a 2025 KBO-attributed snapshot where even the team leading the league in looking strikeouts had ~27.1% looking share; older reporting is around the mid-20s. Therefore ~41% remains WATCH for realism, but the Phase-1 regression blocker at 54–55% is decisively removed.

## REGRESSION_FINDINGS
- Deterministic/count regression suite: PASS in canonical run `34602493140`.
- Targeted production integration suite: PASS in canonical run `34602493140` after synchronizing only the three latest PR protected-formula expectation tests; no production gameplay code was changed by 05.
- Latest PR-head CI still has one unrelated draft-distribution failure outside gameplay; not weakened or modified.
- Mature production roster population remains OPEN because the canonical provider still uses a deterministic neutral lineup fallback.
- Physical HR bias remains known: HR/PA 2.720% vs recent KBO center ~2.06%, HR resolves before defense, and park geometry is absent. This is Phase-2 scope; the final Phase-1 HR/PA moved only +0.024 percentage point from previous 05 heavy.

## FINAL_GATES
- COUNT_BEHAVIOR = PASS
- 3_ZERO_SELECTIVITY = PASS
- THREE_BALL_BEHAVIOR = PASS
- TWO_STRIKE_PROTECTION = PASS
- LOOKING_K = PASS_WITH_WATCH
- GENERATED_CHASE = PASS
- DISCIPLINE_MONOTONICITY = PASS
- BB_ENVIRONMENT = PASS
- K_ENVIRONMENT = PASS
- HBP_ENVIRONMENT = PASS
- PITCHES_PER_PA = PASS
- FOUL_SURVIVAL = PASS
- H_PER_PA = PASS_WITH_WATCH
- RUN_ENVIRONMENT = PASS
- DETERMINISM = PASS
- INTEGRATION_REGRESSION = PASS
- MATURE_ROSTER_POPULATION = OPEN
- PHYSICAL_HR_REALISM = PHASE2_FAIL_WATCH / NON_BLOCKING_FOR_PHASE1

## ROUTING
- 01 Gameplay Engine: Phase 1 closed from 05 validation; PR #58 integration-ready; no further Phase-1 tuning requested.
- 02 Ratings & Generation: no Phase-1 blocker; preserve discipline differentiation when a mature production roster becomes canonical.
- 08 Baseball Data & Research: continue matched completed-season plate-discipline / looking-K research.
- 00 Game Design HQ / 01: Phase 2 Physical Batted-Ball Engine design and implementation may begin after normal integration workflow.
