# 05 - Balance Lab

WORKSTREAM: 05 - Balance Lab
UPDATED_AT: 2026-09-12
SOURCE_OF_TRUTH: integrated Phase2A baseline@39aa1f1d619ad1a4d3b4595d3b3aa6e6e6fdb2ca; Phase2B current branch head@72980c04c3e2f6b66a2d215f45287d1de90c6bc8; Phase2B production checkpoint@6f50473f2a6df90382037b75d617b81373b2f34b; pre2B validation@84e121e0d34d115b481c7ec67096c350d50d38af; candidate validation@3e457c8203172b033d4ba3f94da468df28c5550c
STATE: DONE
CURRENT_TASK: Phase 2B trajectory / landing independent validation
RESULT: PASS_WITH_PERFORMANCE_WATCH

## FINAL_DECISION
- PHASE2B_VALIDATION = PASS.
- PHASE2C_ALLOWED = YES.
- SOURCE_IDENTITY = PASS.
- TRAJECTORY_DISTRIBUTION = PASS.
- EV_LA_BEHAVIOR = PASS.
- GROUND_IMPACT = PASS.
- HIGH_LA = PASS.
- COORDINATES = PASS.
- PHASE1_REGRESSION = PASS.
- PHASE2A_REGRESSION = PASS.
- DETERMINISM = PASS.
- PERFORMANCE = WATCH.
- No trajectory coefficients or production gameplay source were modified by 05.

## SOURCE_STATE
- Canonical integrated Phase2A pre-2B baseline: `39aa1f1d619ad1a4d3b4595d3b3aa6e6e6fdb2ca` (`Merge PR #59: Phase 2A physical batted-ball initial state`).
- During this task main advanced to `ef95f1cef5752b1e74667bc087427dd884d88f37`, but the diff after `39aa1f1d...` is research/status documentation only; production gameplay code is unchanged.
- Phase2B branch: `feature/phase2b-analytical-trajectory`.
- Latest Phase2B branch HEAD at final validation review: `72980c04c3e2f6b66a2d215f45287d1de90c6bc8`.
- `72980c04...` differs from production checkpoint `6f50473f2a6df90382037b75d617b81373b2f34b` only by `docs/workstream-status/01-gameplay.md`.
- Therefore the Phase2B production code actually validated by 05 is also the production code of the latest branch HEAD.

## SOURCE_IDENTITY
Canonical validation checkout:
- branch: `validation/phase2b-candidate-05`.
- checkout SHA: `3e457c8203172b033d4ba3f94da468df28c5550c`.
- Production files are inherited unchanged from frozen Phase2B production checkpoint `6f50473f...`; 05 added validation-only tools/workflow.
- Workflow compared validation checkout blobs directly against Phase2B current HEAD `72980c04...` and PASSed.

Validated production blobs:
- `src/hitting/physical.py` = `92c7daa904cd7eeca9d65859b3e64741525f1a11`.
- `src/hitting/model.py` = `2718635ccb9e53fbed63f0d5d5ba2ad7c17ac8e1`.
- `src/hitting/physical_parameters.py` = `57026c6ec6a84ad795247ce205c053d0568bca64`.
- `src/hitting/trajectory.py` = `c0538123996e2fdb93a6d6cbc87802f045a953c1`.
- `src/hitting/trajectory_parameters.py` = `622a7ebbc186407d47818727fbd3aa21262baae2`.

## PRE2B_BASELINE
Pre-2B validation:
- validation checkout `84e121e0d34d115b481c7ec67096c350d50d38af`.
- GitHub Actions run `34636469829`: SUCCESS.
- artifact ID `10278502499`, digest `sha256:3f5f027a91eb9606634f07a316658df59a3337d11824f497915b9a859e0944da`.
- seed `20260911`.
- neutral 200,000 PA; generated 200,000 PA; production 10,000 games; Phase2A physical 200,000 PA; performance 50,000 PA + 500 games.
- Phase1/count, Phase2A, production integration regressions PASS.

Canonical production 10k baseline:
- PA/game 80.449.
- Runs/game 9.5594.
- Hits/game 19.3175.
- HR/game 2.1883.
- BB/game 7.6208.
- K/game 14.4689.
- HBP/game 1.0592.
- 1B/PA 17.1627%; 2B/PA 3.9442%; 3B/PA 0.1851%; HR/PA 2.7201%.
- AVG .26978; SLG .40994; ISO .14016; BABIP .31081.
- duplicate neutral 20k PA and 250 full games were exact deterministic replays.

Canonical Phase2A physical baseline, 200k production PA -> 142,885 states:
- EV mean/SD 84.05575 / 6.29527 mph; P5/P50/P95 73.5697 / 84.1584 / 94.2247.
- LA mean/SD 9.95008 / 19.20555 deg; P5/P50/P95 -21.7678 / 10.0340 / 41.4639.
- Timing mean/SD -0.00077 / 0.34168.
- Spray mean/SD 0.06213 / 17.63648 deg.

## PHASE2B_CANDIDATE_RUN
- GitHub Actions run `34637280919`: SUCCESS.
- job `103388148935`.
- artifact ID `10278572737`, digest `sha256:c5ae23097b6b7069121b9dfbe213ac19c9fe748e643a8435fd8736a7041e0556`.
- Production identity, compile, trajectory distributions, Phase1 200k/10k environment, Phase2A physical regression, targeted Phase2B tests, Phase1/Phase2A tests, production integration, and paired performance benchmark all completed successfully.

## TRAJECTORY_DISTRIBUTIONS
Production 200k PA -> 142,885 trajectories; every attached Phase2A physical state has a trajectory.

Carry distance (ft):
- mean 180.3103; SD 121.2608.
- P1/P5/P25/P50/P75/P95/P99 = 4.059 / 7.120 / 33.205 / 230.233 / 282.089 / 331.405 / 361.970.
- min/max = 1.349 / 445.052.
- >=500 ft rate = 0; >=600 ft rate = 0.

Hang time (s):
- mean 2.6020; SD 2.1001.
- P1/P5/P25/P50/P75/P95/P99 = 0.0418 / 0.0644 / 0.2809 / 2.7106 / 4.3536 / 6.0328 / 6.7193.
- min/max = 0.0249 / 7.3579.
- >=9 s rate = 0.

Apex height (ft):
- mean 22.1454; SD 28.6009.
- P1/P5/P25/P50/P75/P95/P99 = 3 / 3 / 3 / 8.562 / 30.709 / 84.474 / 128.081.
- min/max = 3 / 260.
- max-guard contact rate = ~0.00070% (1 of 142,885), so no material guard pileup.

Landing:
- X mean 0.118 ft, SD 63.361; P5/P50/P95 -111.939 / 0.084 / 112.275; min/max -325.731 / 316.614.
- Y/depth mean 172.043 ft, SD 116.629; P5/P50/P95 6.751 / 215.651 / 321.872; min/max 0.991 / 444.797.
- radial distribution is exactly the carry-distance distribution by coordinate construction.

## EV_LA_GRID
Controlled EV 80/90/100/110 mph and LA -10/0/10/20/30/40/50 deg:
- At every positive-air angle, carry rises monotonically with EV.
- Carry peaks around 29-30 deg, not 45 deg.
- 100 mph / 29 deg = 397.0 ft, 5.224 s, 64.29 ft apex.
- 100 mph / 30 deg = 396.82 ft, 5.325 s, 68.19 ft apex.
- 100 mph / 45 deg = 350.92 ft; therefore the raw-vacuum 45-degree maximum artifact is absent.
- 100 mph sweep 0-60 deg has best carry exactly at 29 deg / 397.0 ft.
- 110 mph / 30 deg = 464.40 ft; 110 mph / 50 deg = 371.71 ft, so high-LA popup-like states do not become distance-maximizers.

## GROUND_LOW_LA
Representative 90 mph results:
- -15 deg: 10.44 ft, 0.084 s, 3.0 ft apex.
- -10 deg: 15.21 ft, 0.121 s, 3.0 ft apex.
- -5 deg: 25.90 ft, 0.203 s, 3.0 ft apex.
- 0 deg: 55.29 ft, 0.432 s, 3.0 ft apex.
These closely reproduce the 08 analytical first-ground reference and remain finite/nonnegative across EV 80/90/100/110.

## HIGH_LA
At 100 mph:
- 40 deg: 375.22 ft, 6.200 s, 110.73 ft apex.
- 50 deg: 317.62 ft, 6.825 s, 156.01 ft apex.
- 60 deg: 224.02 ft, 7.200 s, 198.56 ft apex.
- Hang/apex increase with high LA while carry falls beyond the high-20s optimum.
- No infinite carry, negative values, or popup-as-HR-distance pathology observed.
- 100 mph / 50 deg is broadly consistent with the 08 high-fly smoke reference; exact KBO calibration remains OPEN by design.

## COORDINATES
100 mph / 30 deg at spray -30/-15/0/+15/+30 deg:
- radial distance is constant at 396.82 ft for every spray angle.
- +/-30 deg X coordinates = -198.41 / +198.41 ft exactly mirrored.
- +/-30 deg Y = 343.656 ft exactly equal.
- center spray X = 0.0.
- Coordinate invariants PASS.

## PHASE1_REGRESSION
Candidate and canonical pre-2B baseline metric payloads are exact-equal for fixed seed/sample conditions.
- neutral/global swing, Z-swing, Chase, contact, BB, K, HBP unchanged.
- production 10k PA/game, Runs/game, Hits/game, HR/game, BB/game, K/game, HBP/game unchanged.
- 1B/2B/3B/HR rates unchanged.
- full-game deterministic replay unchanged.
- Phase1 count tests and production integration tests PASS.

## PHASE2A_REGRESSION
Candidate Phase2A physical distribution JSON is exact-equal to canonical pre-2B physical baseline:
- EV unchanged.
- LA unchanged.
- Timing unchanged.
- Spray unchanged.
- handedness/sensitivity diagnostics unchanged.
- 20k production physical state sequence and result-count aggregate remain exact deterministic replays.
- New trajectory field is deterministic and does not consume RNG.

## DETERMINISM
- Same controlled `BattedBallState` -> exact-equal `BattedBallTrajectory`.
- Same seed -> Phase2A physical sequence exact-equal.
- Same seed -> Phase1 outcome aggregate exact-equal.
- Same seed -> 250 full games exact-equal.
- Trajectory computation contains no RNG, runtime stepping, or iterative integration.

## PERFORMANCE
Paired same-run benchmark on the same GitHub runner, baseline worktree first then candidate:
- Phase2A baseline: 88.413 us/PA; 9.312 ms/game.
- Phase2B candidate: 103.222 us/PA; 10.498 ms/game.
- relative delta: +16.75% per PA; +12.75% per game.
- candidate 144-game extrapolated absolute runtime is ~1.512 s vs baseline ~1.341 s for this synthetic workload.

Assessment:
- This paired result is more credible than previous cross-run noise and indicates a measurable O(1) trajectory-attachment cost.
- Absolute runtime remains small and no pathological scaling is observed, so this is not a Phase2B FAIL.
- PERFORMANCE = WATCH. Preserve O(1) algebraic trajectory cost and re-measure cumulative overhead as Phase2C/stadium/defense layers are added.

## RESEARCH_SANITY
08 reference smoke comparison:
- 100 mph / 29 deg: candidate 397.0 ft vs aerodynamic reference ~397 ft and vacuum ~571 ft -> PASS.
- 100 mph carry maximum at 29 deg, not vacuum 45 deg -> PASS.
- recurring 500+ / 600+ ft production trajectories: 0 / 0 -> PASS.
- 90 mph low-LA first-impact values closely match analytical reference -> PASS.
- high-LA hang/apex remain in broad baseball-like ranges and carry decreases after optimum -> PASS.
- No NaN/Inf/pathological extreme grid values observed.
- These are structural smoke gates, not KBO-specific coefficient calibration.

## GATES
- SOURCE_IDENTITY = PASS
- TRAJECTORY_DISTRIBUTION = PASS
- EV_LA_BEHAVIOR = PASS
- GROUND_IMPACT = PASS
- HIGH_LA = PASS
- COORDINATES = PASS
- PHASE1_REGRESSION = PASS
- PHASE2A_REGRESSION = PASS
- DETERMINISM = PASS
- PERFORMANCE = WATCH

## HANDOFF_TO_01
MEASURED:
- Phase2B trajectory/landing structure passes distribution, EV-LA, low-LA, high-LA, coordinate, determinism and research-smoke validation.
- Phase1 gameplay and Phase2A EV/LA/timing/spray are exact unchanged under fixed seed.
- Paired runtime overhead is +16.75%/PA and +12.75%/game, with low absolute synthetic workload cost.

ROOT_CAUSE / WATCH:
- The performance delta is attributable to attaching and calculating an O(1) trajectory for every legacy BIP; no RNG or final resolver change is involved.
- The model is intentionally a surrogate anchored near 100 mph/29 deg; 05 has not established full KBO-specific trajectory calibration.

HANDOFF:
- No coefficient correction is required for Phase2B exit.
- 01 may proceed to Phase2C design/implementation.
- Keep trajectory shadow/non-authoritative until the stadium/wall migration contract explicitly consumes it.
- Preserve exact legacy result invariance until a later authoritative resolver migration is approved.
- Track cumulative performance in Phase2C because Phase2B already adds a measurable ~13-17% relative cost in the paired micro/full-game workload.
