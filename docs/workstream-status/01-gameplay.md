# 01 - Gameplay Engine

WORKSTREAM: 01 - Gameplay Engine
UPDATED_AT: 2026-09-12
SOURCE_OF_TRUTH: task-start main@47ada4fe9f1d95da2760d7a8d56a8900aab6fdc3; PR #70 code/test checkpoint@6d201690ff7ba56f5fda30663e0cf73678a8ee58
STATE: READY_FOR_05_PHASE2E_B_VALIDATION
CURRENT_TASK: Phase 2E-B Retrieval / Physical Hit-Type Shadow
RESULT: PASS_IMPLEMENTATION / PERFORMANCE_WATCH / 05_VALIDATION_OPEN

## SOURCE_STATE
- Actual latest main at task start: `47ada4fe9f1d95da2760d7a8d56a8900aab6fdc3`.
- Phase2A/B/C/D/E-A were integrated in this baseline; later UI/research documentation was also present.
- No open Phase2E gameplay PR existed at task start.
- Branch: `feature/phase2e-b-retrieval-hit-shadow`.
- PR: #70 `Gameplay: Phase 2E-B retrieval and physical hit-type shadow`.
- Code/test checkpoint validated by CI: `6d201690ff7ba56f5fda30663e0cf73678a8ee58`.
- GitHub Actions run: `34673895739`.

## PRODUCTION FLOW / AUTHORITY
Production physical metadata flow:
`Phase1 contact -> Phase2A BattedBallState -> Phase2B trajectory -> Phase2C wall -> Phase2E-A GroundTravelState -> Phase2D DefensiveResolution -> Phase2E-B retrieval/timing PhysicalHitResolution -> existing legacy resolver`.

Phase2E-B is shadow-only. Authoritative gameplay remains unchanged:
- `PlateAppearanceOutcome.result`;
- legacy HR;
- legacy defense/catch/error;
- legacy single/double/triple resolution;
- runner advancement / runs / scoring;
- stat aggregation;
- Phase1 fair/foul semantics.

Phase2E-B never creates HR. Phase2C remains the physical-HR shadow domain.

## TYPED STATE
New immutable production states in `src/hitting/retrieval.py`:

`RetrievalState`:
- valid, defender_position, adjacent_position;
- defender nominal start x/y and final-ball x/y;
- retrieval distance;
- reaction time, effective fielder speed, movement time, pickup/transfer time, total retrieval time;
- defender rating;
- model version and explicit invalid reason.

`BaseDefenseTiming`:
- target base / coordinate;
- throw distance;
- effective throw speed;
- transfer/release time;
- relay penalty;
- total throw time;
- total defense-arrival time.

`PhysicalHitResolution`:
- valid + retrieval state;
- 1B/2B/3B hypothetical defense timings;
- runner cumulative 1B/2B/3B arrival times;
- timing margins `defense_arrival - runner_arrival`;
- physical result shadow: only `OUT`, `1B`, `2B`, `3B`, or `None` when invalid;
- explicit invalid reason.

`BattedBallState` now exposes optional `retrieval_state` and `physical_hit_resolution` metadata.

## OWNERSHIP_MODEL
V1 uses fixed radial-depth + spray sectors. No nearest-player loop, roster scan, movement/path simulation, or runtime primary-vs-adjacent comparison exists.

Engineering sectors:
- <=35 ft: C primary, P adjacent;
- <=90 ft: center P, side sectors 3B/1B;
- <=185 ft: 3B / SS / 2B / 1B fixed spray sectors;
- >185 ft: LF / CF / RF fixed spray sectors.

Adjacent defender is metadata only in V1.
Fixed nominal anchors include:
- P `(0, 60.5)` ft, C `(0,-5)` ft;
- symmetric IF anchors at 107.5/145 ft engineering midpoints;
- LF/RF = 290 ft @ +/-27 deg;
- CF = 315 ft.

These are research-informed engineering baselines, not measured KBO average positions.

## RETRIEVAL_MODEL
`retrieval_time = reaction + retrieval_distance / effective_fielder_speed + pickup_transfer`.

Role classes are intentionally small: `PC`, `IF`, `OF`.
No acceleration or fielder-route simulation is performed.
All derivation is fixed O(1) algebra.

## DEFENDER_RATING_MODEL
Existing production scalar `HittingEngine.defense` is reused; rating scale itself is untouched.
Rating 100 is neutral. Adjustment saturates over +/-40 rating points.
Higher defense structurally yields:
- non-increasing reaction time;
- non-decreasing effective retrieval speed.

Bounds:
- reaction floor/ceiling: 0.25..1.10 s;
- effective speed: 14..27 ft/s.

Throw speed intentionally does not reuse defense rating strongly; it is position-role baseline only, preserving a future arm-rating interface.

## THROW_MODEL
Canonical 90-ft diamond:
- 1B = `(90/sqrt(2), 90/sqrt(2))`;
- 2B = `(0, 180/sqrt(2))`;
- 3B = `(-90/sqrt(2), 90/sqrt(2))`.

For each target independently:
`throw_time = role release delay + throw_distance/effective_throw_speed + optional fixed relay penalty`.

Effective engineering throw baselines:
- PC 70 mph;
- IF 72 mph;
- OF 78 mph.

If throw distance >220 ft, a fixed 0.65 s relay penalty applies. No relay chain is simulated.

## RUNNER_MODEL
Production `HitterSnapshot.speed` is passed unchanged into the Phase2E-B timing model. No new runner rating scale is introduced.

V1 timing:
- home-start delay + first-leg reference for 1B;
- subsequent 90-ft reference legs + fixed turn penalty for 2B/3B;
- bounded speed-derived time multiplier in `[0.82, 1.18]`.

Higher existing hitter speed therefore cannot increase runner arrival time.

## HIT_RESOLUTION_MODEL
If Phase2D has a valid `physical_out_shadow=True`:
- Phase2E-B returns physical shadow `OUT`;
- retrieval is explicitly not applicable (`air_caught`);
- no base throw timing is needed.

Otherwise one Phase2E-A final location produces one retrieval state. From that same state Phase2E-B computes hypothetical defense arrival at 1B/2B/3B independently.

Margin convention:
`margin = defense_arrival_time - runner_arrival_time`.
- margin >0: runner beats defense;
- margin <=0: defense wins, including exact tie.

Resolution:
- 1B margin <=0 -> OUT;
- 1B safe, 2B margin <=0 -> 1B;
- 2B safe, 3B margin <=0 -> 2B;
- otherwise -> 3B.

There is no continuous throw sequence and no HR creation.

## RNG / DETERMINISM
Phase2E-B RNG usage = ZERO.
- no parent RNG consumption;
- no new child namespace;
- Phase2A child-fork semantics unchanged;
- Phase2D child RNG namespace/decision unchanged.

Dedicated enabled-vs-disabled regression verifies exact equality of:
- legacy PA result sequence;
- parent RNG final state;
- Phase2A fields;
- Phase2B trajectory;
- Phase2C wall state;
- Phase2D opportunity/resolution;
- Phase2E-A GroundTravelState.

## INVALID / FAIL-SAFE
Invalid states are explicit and cannot create a gameplay or shadow OUT by accident. Covered cases include:
- missing/invalid GroundTravelState;
- non-finite final location or defender rating;
- unsupported owner/role derivation;
- invalid/negative retrieval terms;
- non-positive effective fielder or throw speed;
- invalid runner timing;
- non-finite base timing/margins.

Invalid result is `valid=False`, `physical_result_shadow=None`, with finite safe fields and explicit `invalid_reason`.

## CHANGED PRODUCTION FILES
- new `src/hitting/retrieval.py` — blob `5b18688098f35edf3775c92c102b2ca4d860069b`;
- new `src/hitting/retrieval_parameters.py` — blob `317f3ab822b3165f8ad07be84dfb508a72dd7501`;
- modified `src/hitting/physical.py` — blob `74718c24f25341eaff9f1bb453ba5f70009c1d44`;
- modified `src/hitting/model.py` — blob `eaeb4d1b6e024d8d64fd6aa1b47a30aaf879aaca`, only adding existing hitter speed to Phase2E-B metadata input.

Protected snapshots were updated only to approve the explicit new model wiring blob. Legacy parameters, defense and baserunning blobs remain unchanged.

## TESTS / CI
Final code/test checkpoint: `6d201690ff7ba56f5fda30663e0cf73678a8ee58`.
GitHub Actions run: `34673895739`.

PASS:
- web build/tests;
- Python dependency / compile;
- durable store / API gates;
- related production integration 31/31;
- Phase1 regression;
- Phase2A regression;
- Phase2B numerical/determinism/outcome regression;
- Phase2C wall regression;
- Phase2D defensive shadow regression;
- Phase2E-A ground-travel regression;
- all 19 Phase2E-B targeted tests.

Phase2E-B targeted coverage includes:
- representative C/P/3B/SS/2B/1B/LF/CF/RF ownership;
- LF/RF mirror;
- retrieval distance monotonicity;
- defense-rating monotonicity and extreme bounds;
- throw-distance monotonicity and relay threshold;
- runner-speed monotonicity;
- Phase2D catch short-circuit;
- controlled OUT / 1B / 2B / 3B timing cases;
- HR exclusion;
- invalid-ground fail-safe;
- exact determinism;
- production existing speed/defense wiring;
- Phase2E-B enabled/disabled legacy result, parent RNG and upstream metadata exact invariance;
- direct 50k fixed-cost resolution guard;
- distribution smoke preventing single-owner/result collapse.

Full Python discover: 497 tests, 496 PASS, 1 FAIL.
Sole failure is the pre-existing/out-of-scope `test_balance_v04.BalanceV04Tests.test_draft_distribution_not_extreme`: undrafted `0.056666...`; historical assertion requires `>0.10`.

## PERFORMANCE_ARCHITECTURE / WATCH
Phase2E-B production path is O(1):
- fixed ownership branches;
- one retrieval Euclidean distance;
- bounded rating algebra;
- three fixed hypothetical base-distance calculations;
- no timestep, fielder simulation, nearest-player loop, roster scan, pathfinding, relay loop, repeated throw or numerical integration;
- zero RNG.

Direct 50,000 Phase2E-B resolution guard PASS (<5 s loose CI guard; final CI ~1.0 s for the targeted test).

A prior Phase2B-era test disabled trajectory generation to estimate Phase2B overhead. After Phase2C/D/E-A/E-B, that switch now disables the entire downstream Phase2 stack, so its old `<1.60x` threshold no longer isolates Phase2B. The test was corrected to retain exact result/RNG regression and cumulative timing telemetry, while Phase2B's own direct 50k trajectory guard remains the stage-owned performance gate.

Final cumulative telemetry on the shared runner:
- 50k PA: baseline `2.9349 s`, full trajectory-enabled Phase2 stack `5.0484 s`, ratio `1.7201x`;
- 250 games: baseline `1.8308 s`, full Phase2 stack `2.6382 s`, ratio `1.4410x`;
- Phase2C isolated paired telemetry in same run: ratio `1.0278x`.

Therefore:
- Phase2E-B fixed-cost architecture = PASS;
- cumulative Phase2 runtime = WATCH pending 05 controlled paired benchmark;
- no production coefficient/runtime tuning was performed merely to satisfy a stale Phase2B-era threshold.

05 must measure Phase2E-B incremental cost separately and cumulative Phase2 cost on 50k+ PA / 500+ games.

## KNOWN_LIMITATIONS
- deterministic primary retriever only; adjacent defender is metadata, not compared at runtime;
- fixed anchors/sector thresholds are engineering baselines, not KBO measurements;
- moving-ball interception before Phase2E-A final location is not modeled;
- no acceleration, route efficiency, bobble/error or throw-accuracy model;
- no cutoff/relay chain, only one fixed relay penalty;
- no dedicated arm rating wiring yet;
- no force-state graph, double play, tag-up or existing-runner resolution;
- no physical HR authority; no physical 1B/2B/3B authority;
- no gameplay balance tuning or KBO coefficient calibration.

## HANDOFF TO 05
Independent target:
- PR #70 `Gameplay: Phase 2E-B retrieval and physical hit-type shadow`.
- Validate exact final PR HEAD reported after this status-only commit; production code identity should match code/test checkpoint `6d201690ff7ba56f5fda30663e0cf73678a8ee58` except this status document.

Required 05 validation:
1. source/blob identity;
2. retriever ownership distribution by radial depth/spray and LF/RF mirror;
3. retrieval distance/time distributions by role and defense rating;
4. reaction/speed bound pileup and monotonic sweeps;
5. throw distance/time and relay-threshold behavior;
6. runner timing by production speed rating;
7. physical shadow OUT/1B/2B/3B distribution, including invalid and Phase2D-caught shares;
8. no HR invariant;
9. exact Phase1/2A/2B/2C/2D/E-A/final-result/RNG regression;
10. Phase2E-B incremental paired 50k+ PA and 500+ games performance plus cumulative Phase2 cost;
11. no tuning or authority migration during validation.

## GATES
- OWNERSHIP_MODEL = PASS
- RETRIEVAL_MODEL = PASS_STRUCTURAL
- DEFENDER_RATING_MODEL = PASS_BOUNDED
- THROW_MODEL = PASS_STRUCTURAL
- RUNNER_MODEL = PASS_STRUCTURAL
- HIT_RESOLUTION_MODEL = PASS_STRUCTURAL
- CONTROLLED_OUT_1B_2B_3B = PASS
- HR_EXCLUSION = PASS
- INVALID_STATE_FAIL_SAFE = PASS
- DETERMINISM = PASS
- RNG_USAGE = ZERO
- LEGACY_RESULT_INVARIANCE = PASS
- PHASE2E_A_REGRESSION = PASS
- PHASE2D_REGRESSION = PASS
- PHASE2C_REGRESSION = PASS
- PHASE2B_REGRESSION = PASS
- PHASE2A_REGRESSION = PASS
- PHASE1_REGRESSION = PASS
- PRODUCTION_INTEGRATION = PASS
- PERFORMANCE_ARCHITECTURE = PASS_O1
- CUMULATIVE_PHASE2_PERFORMANCE = WATCH
- FULL_PYTHON_SUITE = BLOCKED_ONLY_BY_OUT_OF_SCOPE_DRAFT_GATE_496_OF_497_PASS
- PHASE2E_B_IMPLEMENTATION = PASS
- PHASE2E_B_05_VALIDATION = OPEN
- READY_FOR_05 = YES
