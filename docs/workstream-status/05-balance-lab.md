# 05 - Balance Lab

WORKSTREAM: 05 - Balance Lab
UPDATED_AT: 2026-09-12
SOURCE_OF_TRUTH: pre2C integrated Phase2B main@9d406589d6c71a92fa91843047116200c12826b3; task-start main@cb16f9b462ca8fc2bc565a139f87bd8b00c15a9e; PR61 validated head@d0951ad8d2873edaa4f88e8aa41cd78d550ac1cd; canonical 05 revalidation checkout@4edf985bdeaeb07a2ac919401d55b3570764b3f9
STATE: PASS
CURRENT_TASK: Revalidate PR #61 after invalid-trajectory impossible-HR fix
RESULT: PHASE2C_VALIDATION_PASS / PHASE2D_ALLOWED_YES / INTEGRATION_READY_YES

## FINAL_DECISION
- SOURCE_IDENTITY = PASS.
- PHASE2C_VALIDATION = PASS.
- PHASE2D_ALLOWED = YES after PR #61 integration.
- INTEGRATION_READY = YES for exact validated PR #61 HEAD `d0951ad8d2873edaa4f88e8aa41cd78d550ac1cd`.
- Previous sole blocker (`trajectory.valid=False` could produce physical HR shadow) is fixed and independently retested.
- No production code, stadium geometry, trajectory coefficients, HR rates, fair/foul rules, or tuning values were modified by 05.

## SOURCE_STATE_AND_IDENTITY
- Canonical pre-Phase2C baseline: integrated Phase2B main `9d406589d6c71a92fa91843047116200c12826b3`.
- Task-start latest main: `cb16f9b462ca8fc2bc565a139f87bd8b00c15a9e`.
- Previous failed PR #61 HEAD: `b3dd53e7fbb82a75b3586240a35fe4d59c381a7b`.
- Current validated PR #61 HEAD: `d0951ad8d2873edaa4f88e8aa41cd78d550ac1cd`.
- Production correction commit: `7b862e00ec7bd33ca4f82f0e59d86675705ebe85`.
- Production diff from previous failed HEAD is only `src/hitting/stadium.py`, +13 lines: invalid trajectories return a non-reaching/non-clearing/non-contact/non-HR WallInteraction.
- Current HEAD then adds `tests/test_phase2c_invalid_trajectory.py`; no further production change.
- Validation branch `validation/phase2c-revalidate-05` was created directly from the current PR HEAD.
- Canonical validation checkout: `4edf985bdeaeb07a2ac919401d55b3570764b3f9`.
- Validation checkout production blobs exactly matched current PR HEAD:
  - stadium.py `780e067781c7ad24bf9bdfe60d1f6cbcb23adec0`
  - trajectory.py `f22b84a1cab56be16983d787547e5eeb5b092e03`
  - physical.py `752395dd4462a07d93df618d3bde04ebad3ebf9a`
  - model.py `2718635ccb9e53fbed63f0d5d5ba2ad7c17ac8e1`
  - physical_parameters.py `57026c6ec6a84ad795247ce205c053d0568bca64`
  - trajectory_parameters.py `622a7ebbc186407d47818727fbd3aa21262baae2`
- `VALIDATED_PRODUCTION_CODE == PR61_CURRENT_MERGE_TARGET_PRODUCTION_CODE` = YES.

## CANONICAL_REVALIDATION_RUN
- Actions run `34663768232`: SUCCESS.
- Job `103471439183`: SUCCESS.
- Artifact ID `10288427931`.
- Artifact digest `sha256:d5871b1e0bd14c2a9a81c5f09fa38783450dcabf88ff133f54d9bb4cdec83b75`.
- Seed `20260911`.
- Corpus: 200,000 PA -> 142,885 physical BIP states.
- Phase1 regression: 200k PA diagnostics + 10,000 production games.
- Phase2A regression: 200k physical states + sensitivity checks.
- Phase2B regression: 200k trajectory states.
- Determinism: duplicate 250 full games.
- Performance: same-run actual pre2C git worktree vs current candidate, 50k PA + 500 games.
- Identity, diff scope, compile, blocker pack, Phase1/2A/2B regressions, targeted Phase2C tests, deterministic replay, performance, and artifact upload all PASSed.

## BLOCKER_RETEST_AND_IMPOSSIBLE_HR
Exact previous failing probe:
- trajectory `valid=False`, carry 430 ft, apex 110 ft;
- spray 0 deg, fair;
- wall radius 350 ft, wall height 8 ft.
Result after fix:
- physical_hr_shadow = false.
- reaches_wall = false.
- clears_wall = false.
- wall_contact = false.
- ball_height_at_wall_ft = 0.0.
- clearance_ft = -8.0.

Full impossible-HR pack:
- wall not reached -> HR false: PASS.
- reaches wall but below wall -> HR false: PASS.
- negative radius rejected: PASS.
- non-finite geometry rejected: PASS.
- trajectory.valid=False -> HR false: PASS.
- IMPOSSIBLE_HR = PASS.

## STADIUM_AND_HR_SHADOW_REGRESSION
The same deterministic 142,885-BIP corpus produces exactly the same normal valid-trajectory park rates as the previous candidate; the invalid guard does not perturb production distributions.

Per BIP:
- Generic: wall reached 0.41152%; physical HR shadow 0.10848%.
- Jamsil-like: wall reached 0.46611%; physical HR shadow 0.15117%.
- Gocheok-like: wall reached 0.67887%; physical HR shadow 0.13787%.
- Daejeon asymmetric: wall reached 0.59768%; physical HR shadow 0.10988%.

Controlled sensitivity remains unchanged:
- 350 ft radius / 8 ft wall: 1,153 HR shadows.
- same radius / 16 ft wall: 510.
- 375 ft radius / 8 ft wall: 245.
- greater wall height -> HR non-increasing: PASS.
- greater wall radius -> HR non-increasing: PASS.

Daejeon asymmetry remains structurally visible:
- LF wall reached 2.2062%, HR shadow 0.8537%.
- RF wall reached 3.4886%, HR shadow 0.1766%.
- ASYMMETRY = PASS (fixture remains APPROXIMATED for exact real-park calibration).

Controlled generic +/-30 deg mirror:
- wall radius equal, wall height equal, ball height equal, HR result equal.
- MIRROR = PASS.

Height-at-wall smoke remains exact:
- launch 3.0 ft.
- queried apex 64.286409 ft = stored apex.
- first impact 0.
- beyond first impact 0.
- all finite.
- HEIGHT_AT_WALL = PASS.

## PHASE1_REGRESSION
Fixed seed/sample remains canonical:
- Runs/game 9.5594; Hits/game 19.3175; HR/game 2.1883; BB/game 7.6208; K/game 14.4689; HBP/game 1.0592.
- 1B/PA 17.162674%; 2B/PA 3.944238%; 3B/PA 0.185086%; HR/PA 2.720108%.
- neutral Swing 48.1686%; Z-Swing 70.3280%; Chase 20.9574%; Contact/Swing 77.2130%; BB 9.3990%; K 17.8735%; HBP 1.2965%; Looking-K 40.3978%.
- PHASE1_REGRESSION = PASS.

## PHASE2A_REGRESSION
Exactly retained:
- EV mean/SD 84.05575 / 6.29527 mph.
- LA mean/SD 9.95008 / 19.20555 deg.
- Timing mean/SD -0.00077 / 0.34168.
- Spray mean/SD 0.06213 / 17.63648 deg.
- PHASE2A regression PASS.

## PHASE2B_REGRESSION
Exactly retained:
- carry mean/SD 180.3103 / 121.2608 ft; P5/P50/P95 7.1196 / 230.2328 / 331.4052; max 445.0522.
- hang mean/SD 2.6020 / 2.1001 s; P5/P50/P95 .06437 / 2.71058 / 6.03283; max 7.35794.
- apex mean/SD 22.1454 / 28.6009 ft; P5/P50/P95 3 / 8.5617 / 84.4738; max 260.
- 100 mph / 29 deg = 397 ft; best carry angle = 29 deg.
- PHASE2B_REGRESSION = PASS.

## DETERMINISM
- Same wall input exact equal: PASS.
- Duplicate 250-game sequence exact equal: PASS.
- Final RNG state exact equal: PASS.
- DETERMINISM = PASS.

## PERFORMANCE
Same-run paired measurement:
- pre2C Phase2B: 81.0677 us/PA; 10.5485 ms/game.
- fixed Phase2C: 87.3867 us/PA; 10.9547 ms/game.
- delta: +7.79% per PA; +3.85% per game.
- Previous Phase2C measurement was +5.74% per PA / +3.52% per game, so the bool validity guard did not produce a material regression; observed variance is runner/microbenchmark noise at the same general cost scale.
- PERFORMANCE = PASS_WITH_CUMULATIVE_WATCH for later Phase2D cumulative physics cost.

## DATA_QUALITY
- Generic remains APPROXIMATED engineering fixture, not KBO calibration authority.
- Jamsil remains CONFLICTING.
- Gocheok/Daejeon convenience fixtures retain APPROXIMATED components where geometry is synthesized.
- No exact real-KBO calibration claim is made from these shadow results.

## GATES
- SOURCE_IDENTITY = PASS
- STADIUM_GEOMETRY = PASS_WITH_DATA_QUALITY_WATCH
- HEIGHT_AT_WALL = PASS
- WALL_INTERSECTION = PASS
- HR_SHADOW = PASS
- IMPOSSIBLE_HR = PASS
- ASYMMETRY = PASS
- MIRROR = PASS
- PHASE2B_REGRESSION = PASS
- PHASE1_REGRESSION = PASS
- DETERMINISM = PASS
- PERFORMANCE = PASS_WITH_CUMULATIVE_WATCH

## HANDOFF_TO_07
- Exact independently validated PR #61 HEAD: `d0951ad8d2873edaa4f88e8aa41cd78d550ac1cd`.
- 05 validation says PR #61 is integration-ready at that exact HEAD.
- 07 should use an expected-head check and must not merge a later production-mutated HEAD without renewed 05 identity validation.
- After merge, Phase2D may proceed from the integrated Phase2C baseline.
