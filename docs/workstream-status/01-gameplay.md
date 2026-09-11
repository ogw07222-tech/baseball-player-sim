# 01 - Gameplay Engine

WORKSTREAM: 01 - Gameplay Engine
UPDATED_AT: 2026-09-12
SOURCE_OF_TRUTH: task-start latest main@b030a9612e780d1f3225e8ca9bdc1b6dd8b9bed9; canonical integrated Phase2B baseline@9d406589d6c71a92fa91843047116200c12826b3; PR #61
STATE: READY_FOR_05_PHASE2C_VALIDATION
CURRENT_TASK: Phase 2C stadium geometry, wall interaction, and physical-HR shadow
RESULT: PASS_IMPLEMENTATION / 05_VALIDATION_OPEN

## SOURCE_STATE
- Phase2B PR #60 was already integrated before this task. Canonical integrated Phase2B baseline: `9d406589d6c71a92fa91843047116200c12826b3`.
- Actual latest main at task start: `b030a9612e780d1f3225e8ca9bdc1b6dd8b9bed9`.
- The commits after the Phase2B baseline touched only 05/08 docs/status and Phase2D research; no production gameplay files changed.
- New branch created from exact latest main: `feature/phase2c-stadium-wall-shadow`.
- PR: #61 `Gameplay: Phase 2C stadium wall and physical HR shadow`.
- Production/test candidate before this status-only commit: `aeb8237d836119333430d096797ddbcb2a216b85`.

## PRODUCTION FLOW / AUTHORITY
Production flow is now:
`Phase1 contact -> Phase2A BattedBallState -> Phase2B BattedBallTrajectory -> Phase2C WallInteraction shadow -> legacy _batted_ball/_is_home_run/defense/XBH -> PersistentInningEngine`.

Phase2C is real production-path data, but diagnostic/shadow only.
Still authoritative and unchanged:
- Phase1 pitch/count/swing/contact/foul/HBP/BB/K semantics;
- Phase2A physical `is_fair` remains shadow-only;
- legacy `_is_home_run()`;
- legacy defense catch/error;
- legacy direct 1B/2B/3B resolver;
- runner advancement.

`src/hitting/model.py` was not changed, so legacy result calls and canonical RNG order are untouched.

## STADIUM SCHEMA
New production file: `src/hitting/stadium.py`.

Frozen `StadiumGeometry`:
- `stadium_id`
- `season`
- `is_real_stadium`
- `source_quality` (`VERIFIED`, `APPROXIMATED`, `CONFLICTING`)
- five fixed `wall_radius_ft` anchors
- five fixed `wall_height_ft` anchors

Canonical angles are fixed at `-45, -22.5, 0, +22.5, +45 deg`.
Runtime `wall_at_spray()` uses explicit four-sector if-dispatch and one linear interpolation. There is no per-BIP anchor scan, polygon ray cast, frame step, integration, or iterative solve.

Canonical spatial unit is feet. Spray convention remains CF=0, LF negative, RF positive.

### Fixtures
`GENERIC_ENGINEERING_BASELINE`:
- id `generic_neutral_v1`
- non-real / `APPROXIMATED`
- radii from required engineering baseline 100/115/122/115/100 m, converted to feet
- wall height 3.0 m at all five anchors
- explicitly not labeled a KBO average.

Representative real-park-like validation fixtures:
- `JAMSIL_LIKE_2026`: 100 / 112.5 / 125 / 112.5 / 100 m; 2.6 m wall; `CONFLICTING` because source reports wall around 2.6 vs older 2.7 m and power alleys are synthesized.
- `GOCHEOK_LIKE_2026`: 99 / 110.5 / 122 / 110.5 / 99 m; 4.0 m wall; `APPROXIMATED` because power alleys are synthesized.
- `DAEJEON_ASYMMETRIC_2026`: 99 / 115 / 122 / 112 / 95 m; asymmetric right side; ordinary 2.4 m / approximate right-side 8 m Monster-Wall sectors; `APPROXIMATED` because exact Monster-Wall angular extent is not source-verified.

The production shadow currently uses only the generic stadium because the current production game-provider contract does not carry a canonical stadium id into gameplay. Real fixtures exist for validation and future wiring, not authoritative game assignment.

## HEIGHT AT WALL
Modified production file: `src/hitting/trajectory.py`.

`BattedBallTrajectory` now stores `apex_distance_fraction` (0 for non-positive LA, 0.5 for positive LA V1) and exposes:
`height_at_horizontal_distance(distance_ft)`.

The query is deterministic O(1) and uses a pair of algebraic parabolic segments:
- exactly 3 ft at launch (`r=0`);
- exactly the existing Phase2B stored apex at the stored apex fraction;
- exactly 0 ft at first-ground carry distance;
- 0 beyond first impact;
- non-positive-LA ground-like trajectories use one descending parabola from the launch apex.

No Phase2B carry/hang/apex coefficient was retuned. The height profile is a geometric completion of the existing trajectory summary for wall queries.

## WALL INTERACTION
Frozen `WallInteraction`:
- `stadium_id`
- `wall_radius_ft`
- `wall_height_ft`
- `reaches_wall`
- `ball_height_at_wall_ft`
- `clearance_ft`
- `clears_wall`
- `wall_contact`
- `physical_hr_shadow`

Resolver contract:
- `reaches_wall = carry >= wall_radius`;
- height is queried only when the trajectory reaches the wall;
- `clearance = ball_height_at_wall - wall_height`;
- `clears_wall = reaches_wall and clearance > 0`;
- `wall_contact` uses a 0.25-ft diagnostic tolerance around the wall top;
- `physical_hr_shadow = is_fair_shadow AND spray within [-45,+45] AND clears_wall`.

Therefore distance alone can never create a physical-HR shadow. A fair trajectory that reaches the wall below the top is explicitly non-HR in the shadow model.

## PHYSICAL STATE WIRING
Modified `src/hitting/physical.py`:
- `BattedBallState` gains optional `wall_interaction`.
- after Phase2B trajectory generation, every normal production BIP resolves a generic-stadium wall shadow and attaches it.
- the established Phase2B test/diagnostic seam may intentionally patch trajectory generation to `None`; Phase2C now preserves that seam by also skipping wall work when trajectory is absent. Production trajectory generation remains non-null.

No RNG is used by trajectory height, stadium lookup, or wall resolution.

## DETERMINISM / REGRESSION
Dedicated paired tests disable Phase2C wall resolution test-only and compare the same canonical seed:
- 20,000 PA final-result counters: exact identical;
- parent RNG final state: exact identical;
- Phase2A physical fields: unchanged;
- Phase2B trajectory: exact unchanged.

Existing Phase2B trajectory-disabled compatibility tests PASS after the explicit `trajectory is None -> wall shadow also None` seam handling.

Phase1 fixed-seed 40k diagnostic in final CI remained unchanged:
- Swing 48.0969%; Z-Swing 70.4183%; Chase 20.9709%.
- BB 9.4625%; K 17.6475%; HBP 1.285%.
- Looking-K share 40.558%; pitches/PA 3.2401.
- H/PA 24.51%; HR/PA 2.835%.
- 3-0 Swing 5.336%.

Legacy HR rate is unchanged because `physical_hr_shadow` is never consulted by `_is_home_run()`.

## TESTS / CI
Final production/test candidate: `aeb8237d836119333430d096797ddbcb2a216b85`.
GitHub Actions run `34644632178`:
- Web build/tests PASS.
- compile / dependency / durable-store / API gates PASS.
- related production integration: 31/31 PASS.
- Phase1 dedicated/regression tests PASS.
- Phase2A tests PASS.
- Phase2B tests PASS, including trajectory-disabled compatibility and paired 50k PA / games invariance.
- Phase2C dedicated tests PASS:
  - generic anchor/interpolation;
  - variable wall-height interpolation / Daejeon asymmetry;
  - launch/apex/ground/beyond-flight height profile;
  - reaches / below / clears / impossible-HR geometry;
  - higher-wall and farther-wall monotonicity;
  - symmetric-park mirror;
  - deterministic interaction;
  - production BIP attachment;
  - Phase2B state / parent-RNG invariance;
  - paired final-result invariance;
  - 50k wall-query O(1) guardrail.
- KBO 11-inning and protected gameplay formula tests PASS.
- Full Python discover: 404 tests, 403 PASS, 1 FAIL.
- Sole failure is the pre-existing/out-of-scope `test_balance_v04.test_draft_distribution_not_extreme` (`undrafted=5.667%`, historical assertion requires >10%); no gameplay path is involved.

## PERFORMANCE
Same-process Phase2C paired 20k-PA benchmark from run `34644632178`:
- wall-shadow disabled baseline: 1.9775 s
- Phase2C enabled: 1.8246 s
- ratio: `0.9226x`

The apparent speedup is runner noise. The conclusion is no slowdown signal.

Existing Phase2B paired benchmark in the same run also remained healthy:
- 50k PA trajectory-disabled / enabled ratio: `1.0533x`
- game ratio: `0.9927x`.

Direct 50,000 wall queries pass a loose 5 s CI guard. Runtime work per BIP is fixed-sector interpolation + one algebraic height query + comparisons: O(1), no loops over geometry at runtime.

## KNOWN LIMITATIONS
- `physical_hr_shadow` is diagnostic only and must not replace legacy HR before independent 05 validation and a separate authority-cutover decision.
- physical `is_fair` is still conditioned on already-legacy-BIP contact and remains non-authoritative (`FAIR_FOUL = WATCH`).
- production currently uses the generic stadium only; canonical per-game stadium assignment is not yet wired.
- Jamsil/Gocheok power alleys are engineering interpolations; Daejeon Monster-Wall angular extent is approximate.
- height profile is an algebraic V1 completion of Phase2B carry/apex, not a CFD path or wall-bounce model.
- no park factors, weather/wind/altitude, wall bounce, defense/catch, physical XBH replacement, or runner-advancement changes.

## HANDOFF TO 05
05 can now replace its `PRE2C_BASELINE_LOCKED / CANDIDATE_NOT_YET_AVAILABLE` state with independent validation of PR #61.
Validate the exact PR head reported after this status commit, including:
1. production generic-stadium `physical_hr_shadow` rate and wall reach/clearance distributions;
2. shadow outcomes under Generic/Jamsil-like/Gocheok-like/Daejeon fixtures using the same frozen trajectory population;
3. LF/LC/CF/RC/RF sector rates and Daejeon asymmetry;
4. higher wall / farther wall non-increasing HR-shadow property;
5. zero impossible HR shadows when carry < wall radius or ball height <= wall height;
6. symmetric-park mirrored spray equality;
7. exact Phase1/Phase2A/Phase2B/legacy result regression;
8. deterministic replay / no parent RNG consumption;
9. same-run 50k+ PA and 500+ game performance if 05 needs a heavy performance gate.

Do not tune HR rate or trajectory coefficients as part of Phase2C validation. Shadow-vs-legacy disagreement is diagnostic evidence, not a reason to tune blindly.

## NEXT STAGE
- PHASE2C implementation is complete at 01 and ready for 05 independent validation.
- Phase2D Catch Probability implementation remains blocked until 05 records Phase2C signoff.

## GATES
- STADIUM_LOOKUP = PASS
- HEIGHT_AT_WALL = PASS
- WALL_INTERSECTION = PASS
- HR_GEOMETRY = PASS_STRUCTURAL / WATCH_05_DISTRIBUTION
- ASYMMETRY = PASS
- MIRROR = PASS
- PHASE2B_REGRESSION = PASS
- PHASE1_REGRESSION = PASS
- LEGACY_RESULT_INVARIANCE = PASS
- DETERMINISM = PASS
- PERFORMANCE = PASS
- FAIR_FOUL = WATCH
- FULL_PYTHON_SUITE = BLOCKED_ONLY_BY_OUT_OF_SCOPE_DRAFT_GATE_403_OF_404_PASS
- PHASE2C_IMPLEMENTATION = PASS
- PHASE2C_05_VALIDATION = OPEN
- READY_FOR_05 = YES
- PHASE2D_ALLOWED = PENDING_05_SIGNOFF
