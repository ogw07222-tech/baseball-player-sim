# 05 - Balance Lab

WORKSTREAM: 05 - Balance Lab
UPDATED_AT: 2026-09-12
SOURCE_OF_TRUTH: Phase2C integrated baseline@3a4fc58a3c56d9042561494a08a676762fb4661d; PR65 validated HEAD@65d58a6d3cc9aec92258d88908d7ae01c5403c41; canonical 05 checkout@f68d049e7a20dedfad990ef37cac8413a5583c63
STATE: PASS_WITH_WATCHES
CURRENT_TASK: Phase 2D physical defensive catch shadow independent validation
RESULT: PHASE2D_VALIDATION_PASS / MERGE_ALLOWED_YES_FROM_05

## FINAL_DECISION
- VALIDATED_HEAD = `65d58a6d3cc9aec92258d88908d7ae01c5403c41`.
- SOURCE_IDENTITY = PASS.
- PHASE2D_VALIDATION = PASS.
- MERGE_ALLOWED = YES from 05 gameplay-validation perspective for the exact validated HEAD only.
- Phase2D remains shadow-only; no physical defense authority switch is approved.
- Explicit WATCHES: fixed primary-owner discontinuity at +/-15 deg, uncalibrated absolute catch-probability level / 38.64% legacy disagreement, and +31.36% PA / +23.37% game incremental same-run runtime cost.
- No production formula, defense coefficient, rating scale, legacy resolver, stadium geometry, trajectory formula, or draft balance code was modified by 05.

## SOURCE_STATE_AND_IDENTITY
- Task-start and validation baseline main: `3a4fc58a3c56d9042561494a08a676762fb4661d` (integrated Phase2C).
- PR #65: `Gameplay: Phase 2D physical defensive catch shadow`.
- PR branch: `feature/phase2d-defensive-catch-shadow`.
- Exact validated current PR HEAD: `65d58a6d3cc9aec92258d88908d7ae01c5403c41`.
- 01 implementation/test checkpoint: `144e2b811ebe0cfade8aca5653c53eb8a30c19aa`; checkpoint -> current HEAD changes only `docs/workstream-status/01-gameplay.md`, so production/test code is identical.
- PR production changes are limited to `src/hitting/model.py`, `src/hitting/physical.py`, and new `src/hitting/physical_defense.py`.
- Legacy authority files are unchanged by PR #65: `src/hitting/defense.py`, `src/hitting/parameters.py`, `src/hitting/baserunning.py`.
- Validation checkout production blob identity against PR HEAD PASSed:
  - `model.py` = `585d4cd0eb4c5464d02fe0805d359b0e9cafe39d`
  - `physical.py` = `7a970329ebb36fc382041b893a73e54f48340568`
  - `physical_defense.py` = `6004aa2d125f509399cad8adfeaf010e8c6f1d02`
  - `defense.py` = `279f6282ef41c53e709839dbbe791e16836eaf53`
  - `parameters.py` = `3876b4221f53b7d4b7cc6069d9425004fc9f311a`
  - `baserunning.py` = `2a383ce61fb6938ae30973be210159baa1d76726`
- Phase2D primary test blob: `tests/test_phase2d_defensive_shadow.py` = `920e54720e4eff662880a5506ea28e0963537498`.
- Production integration test blobs: game provider `726c3e50c4d10b382b4e82fb63f23f9e1cf2f2e8`; consolidation `13d2937e1d26427b202817faa110866da1807f03`; stat aggregation `16b06b529d14d28379a6892b0514b8ed2ca86d1e`.
- During finalization main advanced to `ab26ab04d42fe5a67ee5cc52462de57b77d33eff` by merge of PR #64 Interactive Event System P1. That divergence changes only interactive-events/persistence/production-advance files and tests/docs, not `src/hitting/*`. PR #65 raw GitHub state remains mergeable=true/rebaseable=true, mergeable_state=unstable due CI status; 07 must recheck current main and exact HEAD before merge.

## CANONICAL_VALIDATION_RUN
- Validation branch: `validation/phase2d-candidate-05`.
- Canonical validation checkout: `f68d049e7a20dedfad990ef37cac8413a5583c63`.
- Actions run: `34666864381` — SUCCESS.
- Job: `103480415590` — SUCCESS.
- Artifact ID: `10289002773`.
- Artifact digest: `sha256:332a68d907dba04a19b6b2a751db7b0ed900b0feea6ff175c2a7c443815650a9`.
- Seed: `20260912`.
- Main Phase2D corpus: 200,000 neutral PA -> 142,770 physical BIP states.
- Exact base-vs-candidate regression: 200,000 PA + 1,000 production games.
- Determinism: duplicate 20,000 PA physical-defense sequence.
- Performance: same Actions job, exact Phase2C base worktree vs Phase2D candidate, 50,000 PA + 500 games each.

## OPPORTUNITY_POPULATION
200k PA -> 142,770 physical BIP states:
- valid DefensiveOpportunity: 69,813 = 48.8989%.
- invalid: 72,957 = 51.1011%.
Invalid reasons:
- `ground_not_modeled_v1`: 71,694.
- `shadow_foul`: 761.
- `wall_intersection_unmodeled_v1`: 358.
- `over_wall`: 144.
- no generated missing/invalid trajectory case in the production corpus.
Trajectory-class valid rate:
- ground_like: 0 / 71,694 = 0%.
- line_drive: 39,541 / 40,158 = 98.4636%.
- fly_ball: 27,560 / 28,173 = 97.8242%.
- popup: 2,712 / 2,745 = 98.7978%.
- OPPORTUNITY_POPULATION = PASS.

## OWNERSHIP
Among 69,813 valid opportunities:
- LF 13,264 = 18.9993%.
- CF 43,107 = 61.7464%.
- RF 13,442 = 19.2543%.
Spray buckets route cleanly to the expected side/center owner.
Boundary probe:
- -15.001 deg -> LF; -15.000/-14.999 -> CF.
- +14.999/+15.000 -> CF; +15.001 -> RF.
- The hard V1 owner switch is therefore exactly at the designed +/-15 deg boundary.
- Controlled boundary P changes from about 0.8358 on CF side to 0.9379 on LF/RF side because required distance/anchor changes discontinuously. This is an expected V1 primary-owner artifact, not a sign error, but must remain a WATCH before authority migration.
- OWNERSHIP = PASS_WITH_BOUNDARY_WATCH.

## MIRROR
16 controlled symmetric +/-spray cases spanning 220/260/300/340 ft radii and 18/25/35/42 deg:
- LF <-> RF owner mirror exact.
- required-distance delta = 0 in every case.
- direction class exact equal.
- baseline probability delta = 0.
- adjusted probability delta = 0.
- MIRROR = PASS.

## PHYSICAL_DISTRIBUTIONS
Valid opportunities n=69,813.
Required distance (ft):
- mean 58.0864; median 56.0892.
- P10 23.8049; P25 38.2179; P75 74.1049; P90 90.8332; P95 104.7403; P99 149.8071.
- max 301.6699.
Opportunity time (s):
- mean 4.4637; median 4.3598.
- P10 3.0394; P25 3.5348; P75 5.2967; P90 6.0589; P95 6.4275; P99 6.8811.
- max 7.3369.
Direction shares:
- in 66.7254%; lateral 15.7922%; back 17.4824%.
Near-wall:
- 1,054 / 69,813 = 1.5097%.
- near-wall distance mean/median 78.9444 / 77.4407 ft vs non-wall 57.7667 / 55.6057 ft.
- near-wall time mean/median 4.8336 / 4.8775 s vs non-wall 4.4580 / 4.3458 s.
Position distance mean/median:
- LF 50.8873 / 49.7241 ft.
- CF 62.5010 / 61.3456 ft.
- RF 51.0331 / 49.9431 ft.
- PHYSICAL_DISTRIBUTIONS = PASS; no non-finite/degenerate tail found.

## CATCH_PROBABILITY
Production corpus uses neutral defense=100, so baseline and adjusted P are identical by construction.
Adjusted P n=69,813:
- mean 0.889637; median 0.979012.
- P1 .06372; P5 .38574; P10 .63719; P25 .89516; P75 .99585; P90 .99893; P95 .99952; P99 .99986.
- min .0000122; max .9999868.
- exact 0 saturation 0%; exact 1 saturation 0%.
By class mean P:
- line_drive .83889.
- fly_ball .97653.
- popup .74656 (wide/bimodal physical geometry mix; P10 .0467, median .9535).
Distance bucket mean P is monotone in population summary: <25 ft .9975, 25-50 .9865, 50-75 .9279, 75-100 .7421, 100-150 .4942, 150+ .1637.
Time bucket mean P rises from 2-3 s .6183 through 5-6 s .9805; 6+ s population mean drops to .9019 because that observational bucket mixes much harder/longer-distance trajectories. Controlled time sweep still passes monotonicity.
- CATCH_PROBABILITY = PASS_WITH_CALIBRATION_WATCH. Absolute level is engineering-only and is not approved as KBO calibration.

## MONOTONICITY
Independent controlled multi-point sweeps:
- required distance increase -> P non-increasing: PASS.
- opportunity time increase -> P non-decreasing: PASS.
- defense rating increase -> P non-decreasing: PASS.
- direction ordering back <= lateral <= in: PASS (controlled P .92588 <= .95143 <= .96528).
- near-wall <= identical non-wall: PASS (.98817 <= .99379).
- MONOTONICITY = PASS.

## RATING_SENSITIVITY
Frozen valid opportunity population and frozen shadow roll:
- rating 60: mean P .81989, median .94493, shadow-out 82.023%; routine conversion 92.111%, borderline 36.561%, extreme 3.623%.
- rating 80: mean P .85794, median .96586, shadow-out 85.838%; routine 94.807%, borderline 47.450%, extreme 5.647%.
- rating 100: mean P .88964, median .97901, shadow-out 89.031%; routine 96.654%, borderline 58.712%, extreme 8.950%.
- rating 120: mean P .91545, median .98716, shadow-out 91.583%; routine 97.926%, borderline 68.569%, extreme 13.532%.
- rating 140: mean P .93604, median .99218, shadow-out 93.613%; routine 98.714%, borderline 77.188%, extreme 20.085%.
Rating ordering is strict and poor defenders do not collapse routine plays; elite rating does not turn the frozen extreme set into routine conversion.
- RATING_SENSITIVITY = PASS_WITH_CALIBRATION_WATCH.

## IMPOSSIBLE_OUT
Independent forced edge cases all produce invalid resolution with `roll=None`, `physical_out_shadow=False`, P=0:
- trajectory None.
- trajectory.valid=False.
- ground_like.
- shadow foul.
- missing wall context.
- over-wall / physical-HR path.
- wall intersection without rebound model.
- non-finite defender rating.
- IMPOSSIBLE_OUT = PASS.

## LEGACY_AND_PHASE2ABC_REGRESSION
Exact Phase2C-base vs Phase2D-candidate fingerprint comparison at seed 20260912:
- 200,000 PA BIP count equal: 142,770.
- PA outcome counters exact equal: single 34,433; double 7,881; triple 386; HR 5,526; out 93,267; ROE 1,277; BB 18,888; K 35,724; HBP 2,618.
- final parent PA RNG state exact equal.
- Phase2A/B/C state fingerprint exact equal: `3490976d71da1ced7de80055bef1ee11b84a60bfdacecd12cbc9bde28e377c7f`.
- 1,000-game totals exact equal: PA 79,884; H 19,001; 1B 13,500; 2B 3,114; 3B 147; HR 2,240; BB 7,360; SO 14,755; HBP 1,062; R 9,358; ROE 541; GDP 1,127; SF 170; XBT 5,207 / 11,289 attempts; first-to-third 2,251; second-to-home 1,664.
- game sequence hash exact equal: `7658d1774250faf21cbdc1d67cba4681c8f6a70543a0f4bc92af16581cbe22bb`.
- final game RNG exact equal.
- LEGACY_REGRESSION = PASS.
- PHASE2ABC_REGRESSION = PASS.

## DETERMINISM
Duplicate candidate 20,000-PA replay:
- 14,245 physical BIP states each.
- exact opportunity+resolution sequence hash equal: `55378fb7dbcf9f51dd2ca3710e4d6fbebb0a071052745c0e001ff7013a4193d1`.
- parent RNG final state exact equal.
- DETERMINISM = PASS.

## PERFORMANCE
Same-run paired GitHub runner, exact Phase2C base vs candidate:
- Phase2C base: 57.4290 us/PA; 7.1228 ms/game.
- Phase2D candidate: 75.4397 us/PA; 8.7876 ms/game.
- delta: +31.3617% per PA; +23.3723% per game.
Code audit confirms fixed owner branch + fixed arithmetic/logistic calculation + one child-RNG roll; no frame loop, pathfinding, nearest-player search, dynamic scan, iterative physics, or timestep integration.
- PERFORMANCE = WATCH. Complexity is O(1), but measured incremental cost is material and cumulative Phase2 physics performance should be profiled/optimized before or during later authority migration. This is not a correctness blocker for current shadow-only Phase2D.

## SHADOW_VS_LEGACY
Valid airborne opportunities n=69,813 confusion matrix:
- legacy OUT / physical OUT: 40,339.
- legacy OUT / physical SAFE: 5,158.
- legacy SAFE / physical OUT: 21,816.
- legacy SAFE / physical SAFE: 2,500.
- overall disagreement: 38.6375%.
Disagreement by class:
- fly_ball 35.4753%; line_drive 40.4390%; popup 44.5059%.
By position:
- LF 37.3191%; CF 39.6223%; RF 36.7802%.
By near-wall:
- non-wall 38.5782%; near-wall 42.5047%.
By required distance:
- <25 ft 37.2335%; 25-50 36.2545%; 50-75 37.3115%; 75-100 41.2800%; 100-150 49.9864%; 150+ 65.2299%.
By opportunity time:
- 2-3 s 47.2626%; 3-4 40.4090%; 4-5 36.6553%; 5-6 35.3431%; 6+ 38.3868%.
- SHADOW_DISAGREEMENT = MEASURED_HIGH / WATCH. This is not a tuning gate and no coefficients were changed. Before physical defense authority cutover, disagreement root causes and empirical calibration must be revisited.

## GLOBAL_CI_CONTEXT
- Actual PR HEAD GitHub Actions overall Python job fails in the full-suite step; Phase2D-specific and production-integration steps before it pass.
- Independently reproduced known draft-balance failure: `BalanceV04Tests.test_draft_distribution_not_extreme`, undrafted `0.056666666666666664` vs historical assertion `> 0.10`.
- This is draft/generation balance, not Phase2D gameplay-path logic; 05 did not modify it.
- The lightweight 05 full-suite context run intentionally did not install API/Postgres dependencies, so it also reports expected environment-only FastAPI/Postgres import failures and is not used as a canonical whole-repo CI replacement. Phase2D targeted suites, Phase2ABC regressions, deterministic regression and independent corpus all pass.
- GLOBAL_CI_OUT_OF_SCOPE_FAILURE = VERIFIED_DRAFT_BALANCE_FAILURE; CI remains globally red/unstable until separately resolved or policy-handled.

## HANDOFF_TO_07
- Exact independently validated PR: #65 `Gameplay: Phase 2D physical defensive catch shadow`.
- Exact validated HEAD: `65d58a6d3cc9aec92258d88908d7ae01c5403c41`.
- 05 gameplay validation = PASS for that exact HEAD.
- 07 must recheck HEAD and current main before integration. Main advanced after the validation baseline through PR #64, but that divergence does not touch `src/hitting/*`; raw GitHub currently reports PR #65 mergeable/rebaseable with `mergeable_state=unstable` because CI is red.
- If PR #65 production blobs move, or conflict resolution changes any validated production/test blob, renewed 05 source-identity validation is required.
- Do not interpret this PASS as physical-defense authority approval; Phase2D remains shadow-only.
