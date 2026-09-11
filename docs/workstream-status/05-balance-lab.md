# 05 - Balance Lab

WORKSTREAM: 05 - Balance Lab
UPDATED_AT: 2026-09-12
SOURCE_OF_TRUTH: task-start main@88adb4abee199210ac5523d558792d120e630519; PR59 merge-target head@26ef621342a92b190000d0784fc39874407f052e; canonical current-head validation@10f983546a456bc85aa4e09f83c1e6956932d339; full-suite context validation@60c88d4474a7e0fc9f4cb1662002879af86fd373
STATE: DONE
CURRENT_TASK: PR #59 current-head Phase 2A revalidation and final signoff
RESULT: PASS_WITH_FAIR_FOUL_AND_PERFORMANCE_WATCH

## FINAL_DECISION
- PHASE2A_CURRENT_HEAD = PASS.
- PR59_INTEGRATION_READY = YES from 05 validation perspective.
- PHASE2B_ALLOWED_AFTER_MERGE = YES.
- The prior 05 SHA mismatch is closed: the exact production blobs currently proposed by PR #59 were independently validated.
- No production coefficient tuning or `src/` modification was performed by 05.
- FAIR_FOUL remains WATCH because the field is shadow-only on a population already classified as legacy BIP.
- PERFORMANCE remains WATCH, not FAIL: current raw GitHub-runner wall times are materially slower than the previous run, but the slowdown is broad across the runner workload and no isolated Phase2A/RNG compatibility regression was detected.

## SOURCE_STATE
- Latest main at task start: `88adb4abee199210ac5523d558792d120e630519` (`docs: record Phase 2B trajectory research status`).
- PR #59: OPEN / mergeable / non-draft.
- PR #59 current merge-target HEAD: `26ef621342a92b190000d0784fc39874407f052e`.
- Prior 05 validated production checkpoint: `d8b7efc40b150b987867e4240d0127f4bcaf09f3`.
- Relative to the prior checkpoint, the only production source change is `src/hitting/physical.py`: parent RNG state access now accepts project `get_state()` and stdlib-compatible `getstate()`; unsupported objects raise a predictable `TypeError`.
- `src/hitting/model.py` is unchanged from the prior checkpoint.
- `src/hitting/physical_parameters.py` is unchanged from the prior checkpoint; no EV/LA/timing/spray coefficient changed.

## PRODUCTION_IDENTITY
PR #59 current-head production blobs:
- `src/hitting/physical.py` = `26ff07ee4ba6da43581218c6b425295a08aac3b8`.
- `src/hitting/model.py` = `2718635ccb9e53fbed63f0d5d5ba2ad7c17ac8e1`.
- `src/hitting/physical_parameters.py` = `57026c6ec6a84ad795247ce205c053d0568bca64`.

Canonical validation branch:
- `validation/pr59-current-head-05` was created directly from PR #59 HEAD `26ef621342a92b190000d0784fc39874407f052e`.
- Canonical validation checkout `10f983546a456bc85aa4e09f83c1e6956932d339` adds validation-only tooling/workflow on top of that source.
- The first workflow gate compares all three production blobs in the validation checkout against the exact PR #59 HEAD using Git object identity; it PASSed.
- Therefore `VALIDATED_PRODUCTION_CODE == MERGE_TARGET_PRODUCTION_CODE` = YES.

## CANONICAL_CURRENT_HEAD_VALIDATION
- GitHub Actions run `34633493502`: SUCCESS.
- Job `103375740413`.
- Seed `20260911` for canonical offense/physical distributions.
- Samples: neutral 200,000 PA; generated 200,000 PA; production 10,000 games; physical production sample 200,000 PA; controlled sensitivity 20,000 states/population; deterministic physical 20,000 PA; performance 50,000 PA + 500 games.
- Artifact ID `10276903232`.
- Artifact digest `sha256:f9c78d731f539a951eeaf6a7bb059c3829eac7344abcbc220f2422fd0404229a`.
- Identity, compile, RNG compatibility, physical distribution, Phase1 environment/performance, targeted Phase2A tests, Phase1 count regression, and production integration tests all PASSed.

## RNG_COMPATIBILITY
Project `src.rng.RNG` parent:
- parent state unchanged after first physical-state generation: PASS.
- parent state unchanged after repeated generation: PASS.
- repeated same parent state produces exactly the same `BattedBallState`: PASS.
- eight subsequent parent draws exactly match an untouched same-seed control RNG: PASS.
- Therefore parent draw count / canonical stream is unchanged.

Stdlib `random.Random` parent:
- `getstate()` path is accepted: PASS.
- parent state unchanged after first and second physical-state generation: PASS.
- repeated same parent state produces exactly the same `BattedBallState`: PASS.
- eight subsequent parent draws exactly match an untouched same-seed control: PASS.

Unsupported parent RNG:
- object exposed draw methods but neither `get_state()` nor `getstate()`.
- observed error: `TypeError("parent_rng must expose get_state() or getstate()")`.
- observed parent draw calls: 0.
- predictable failure semantics: PASS.
- hidden parent consumption: NONE.

## PHASE2A_DISTRIBUTIONS
Production RHH sample: 200,000 PA -> 142,885 attached `BattedBallState` samples.

Exit velocity (mph):
- mean 84.05575; SD 6.29527.
- P1/P5/P25/P50/P75/P95/P99 = 68.9634 / 73.5697 / 79.8643 / 84.1584 / 88.3563 / 94.2247 / 98.3288.
- min/max 53.7720 / 111.2481.
- 3,987 unique values at 0.01 mph precision; no degenerate clustering or bound explosion.

Launch angle (deg):
- mean 9.95008; SD 19.20555.
- P1/P5/P25/P50/P75/P95/P99 = -35.4004 / -21.7678 / -2.8762 / 10.0340 / 22.8877 / 41.4639 / 54.4000.
- min/max -65 / 85.
- descriptive bins only: <10 GB-like 49.9332%; 10-25 LD-like 28.4837%; 25-50 FB-like 19.7823%; >=50 popup-like 1.8007%.
- 10,760 unique values at 0.01-degree precision; no one-bin/category collapse.

Timing:
- mean -0.00077; SD 0.34168.
- P5/P50/P95 = -0.56523 / -0.00019 / 0.56116.
- late (<-0.20) 27.9756%; on-time [-0.20,0.20] 44.1488%; early (>0.20) 27.8756%.
- lower/upper hard-bound pileup 0.1876% / 0.1806%; no material boundary collapse.

Spray:
- mean 0.06213 deg; SD 17.63648 deg.
- P5/P25/P50/P75/P95 = -29.0732 / -11.8486 / 0.1236 / 12.0173 / 29.0064.
- left (<-15) 19.6935%; center [-15,15] 60.3737%; right (>15) 19.9328%.
- +/-75 deg boundary pileup ~0.0014% each.
- RHH early timing mean spray -14.0927 deg; late +14.0752 deg.
- LHH quarter-sample direction mirrors this relationship.

Comparison to prior 05 Phase2A checkpoint:
- EV, LA, timing, spray, handedness and fair/foul outputs are materially identical; under the same project RNG path the canonical measured values are identical.
- This matches the source diff: no physical coefficients or model integration changed, only parent-state accessor compatibility.

## SENSITIVITY
Controlled 20,000-state populations:
- Power 70 -> 140: EV mean +7.000 mph; EV P95 +7.000 mph.
- Contact 70 -> 140: timing SD 0.377277 -> 0.276341.
- RHH inside vs outside: mean spray -12.3666 deg vs +12.3232 deg.
- same-seed handedness mirror: max and mean `abs(R spray + L spray)` = 0.0.
- No sign reversal or structural sensitivity regression observed.

## PHASE1_REGRESSION
Same seed/sample harness reproduces the existing pre-Phase2 / previous Phase2A production environment exactly.

Neutral 200k:
- Swing 48.1686%.
- Z-Swing 70.3280%.
- Chase 20.9574%.
- Contact/Swing 77.2130%; Whiff/Swing 22.7870%.
- BB/PA 9.3990%; K/PA 17.8735%; HBP/PA 1.2965%.
- Looking-K share 40.3978%.
- H/PA 24.2210%; HR/PA 2.7805%.

Production 10k games:
- PA/game 80.449.
- Runs/game 9.5594.
- Hits/game 19.3175.
- HR/game 2.1883.
- BB/game 7.6208.
- K/game 14.4689.
- HBP/game 1.0592.
- 1B/PA 17.1627%; 2B/PA 3.9442%; 3B/PA 0.1851%; HR/PA 2.7201%.

- Phase1 count regression suite PASS.
- targeted production integration suites PASS.
- No evidence that the `get_state()` / `getstate()` compatibility extension changes canonical gameplay output.

## DETERMINISM
- duplicate project-RNG physical state from the same parent state: exact equal.
- duplicate stdlib-Random physical state from the same parent state: exact equal.
- duplicate 20,000 production PA physical-state sequence: exact equal; 14,271 states generated in each run.
- corresponding final PA result-count aggregate: exact equal.
- neutral 20,000 PA Phase1 snapshot: exact equal.
- 250 full games with identical seed: exact equal.
- parent-stream next draws equal untouched control for both supported parent RNG interfaces.

## PERFORMANCE
Previous Phase2A validation run (`34623705971`):
- 50k PA = 2.8085 s = 56.170 us/PA.
- 500 games = 2.9296 s = 5.859 ms/game.

Current PR #59-head validation run (`34633493502`):
- 50k PA = 4.3288 s = 86.577 us/PA.
- 500 games = 4.5775 s = 9.155 ms/game.
- 144-game extrapolation ~1.318 s.

Interpretation:
- Raw cross-run wall clock is materially slower, so 05 does not relabel this as an unconditional PASS.
- However the broader runner workload is also slower: the same 200k physical distribution step took about 29 s in the current run vs about 20 s in the previous run, while source-level compatibility change only adds accessor selection before the same parent-state fingerprinting work.
- The dedicated Phase2A constant-time unit guard PASSes on current HEAD.
- All gameplay and physical outputs remain exact-identical under the project RNG path.
- No isolated evidence currently attributes the wall-clock delta to the RNG interface compatibility change.
- PERFORMANCE = WATCH due non-paired shared-runner benchmark noise; not a detected production regression.

## FAIR_FOUL
- Production RHH shadow sample: fair 98.9670%, foul 1.0330%.
- LHH quarter sample: fair 98.8507%, foul 1.1493%.
- This is intentionally unchanged from prior validation.
- `BattedBallState` is generated only after legacy contact resolution has already produced `bip`; therefore this is a conditional shadow property, not an all-contact or league fair/foul estimate.
- FAIR_FOUL remains WATCH until an authoritative migration explicitly defines physical fair/foul placement relative to legacy foul resolution.

## FULL_TEST_CONTEXT
Primary current-head 05 run `34633493502`:
- production identity PASS.
- compile PASS.
- RNG compatibility PASS.
- physical distributions PASS.
- Phase1 environment/performance harness PASS.
- targeted Phase2A tests PASS.
- Phase1 count regression PASS.
- targeted production integration PASS.

The first lightweight full-suite context capture lacked the repository API dependency install and therefore contained unrelated import errors. It is not used for the final suite classification.

Official-dependency full-suite context:
- validation checkout `60c88d4474a7e0fc9f4cb1662002879af86fd373`; production identity against PR #59 HEAD asserted again and PASSed.
- GitHub Actions run `34634079663`: SUCCESS as an evidence-collection workflow.
- installed `requirements-api.txt`, used Postgres 16 test service, compile PASS.
- `python -m unittest discover -s tests -v`: 376 tests, 375 PASS, 1 FAIL.
- sole failure: `test_balance_v04.BalanceV04Tests.test_draft_distribution_not_extreme`.
- This is the previously known draft-distribution assertion and does not exercise Phase2A physical batted-ball or RNG compatibility.
- Artifact ID `10277383133`, digest `sha256:7ceaeb18e9c5af2068bd0e2b06f97bc3d8f10c7ed3cd6637e605719d971686e7`.

## GATES
- VALIDATION_MATCH = PASS
- RNG_INTERFACE_COMPATIBILITY = PASS
- PARENT_RNG_NON_CONSUMPTION = PASS
- PHASE2A_STRUCTURAL = PASS
- PHASE1_REGRESSION = PASS
- DETERMINISM = PASS
- PERFORMANCE = WATCH
- FAIR_FOUL = WATCH

## FINAL
- PHASE2A_CURRENT_HEAD = PASS
- PR59_INTEGRATION_READY = YES
- PHASE2B_ALLOWED_AFTER_MERGE = YES

## HANDOFF_TO_01_07
- No production correction is required from 05 for PR #59 current HEAD.
- Preserve the no-parent-consumption contract for both supported RNG interfaces.
- Unsupported RNG parents should continue to fail before drawing from the parent stream.
- FAIR_FOUL remains a Phase2B+ migration design watch; do not make the current shadow flag authoritative without relocating/defining the classification boundary.
- Performance should be rechecked with a paired same-run old-vs-current microbenchmark if later Phase2 work materially expands physical-state computation; current evidence does not isolate a compatibility regression.
- 07 may integrate PR #59 against current main subject to its normal merge/conflict checks.
