# 01 - Gameplay Engine

WORKSTREAM: 01 - Gameplay Engine
UPDATED_AT: 2026-09-12
SOURCE_OF_TRUTH: task-start main@3a4fc58a3c56d9042561494a08a676762fb4661d; PR #65 code/test checkpoint@144e2b811ebe0cfade8aca5653c53eb8a30c19aa
STATE: READY_FOR_05_PHASE2D_VALIDATION
CURRENT_TASK: Phase 2D physical defensive opportunity / catch shadow implementation
RESULT: PASS_IMPLEMENTATION / 05_VALIDATION_OPEN

## SOURCE_STATE
- Actual latest main at task start: `3a4fc58a3c56d9042561494a08a676762fb4661d` (`Merge PR #61: Phase 2C stadium wall and physical HR shadow`).
- Phase2A, Phase2B and Phase2C are integrated in this baseline.
- No Phase2D gameplay PR existed at task start.
- Branch: `feature/phase2d-defensive-catch-shadow`.
- PR: #65 `Gameplay: Phase 2D physical defensive catch shadow`.
- Code/test checkpoint validated by CI: `144e2b811ebe0cfade8aca5653c53eb8a30c19aa`.
- CI merge-ref: `f8973666019d4c299711944c69f582f057e414f5` against main `3a4fc58...`.

## PRODUCTION FLOW / AUTHORITY
Production metadata flow is now:
`Phase1 contact -> Phase2A BattedBallState -> Phase2B BattedBallTrajectory -> Phase2C WallInteraction -> Phase2D DefensiveOpportunity -> DefensiveResolution shadow -> existing legacy resolver`.

Phase2D is shadow-only.
Still authoritative and unchanged:
- legacy `_is_home_run()`;
- legacy `src/hitting/defense.py` catch/error probability and RNG use;
- legacy 1B/2B/3B resolver;
- runner advancement;
- Phase1 fair/foul and two-strike foul semantics.

`PlateAppearanceOutcome.result` never consults Phase2D metadata.

## PHASE2D STATE
New production module: `src/hitting/physical_defense.py`.

Frozen `DefensiveOpportunity` fields:
- `valid`
- `defender_position`
- `opportunity_type`
- `catch_x_ft`, `catch_y_ft`
- `nominal_start_x_ft`, `nominal_start_y_ft`
- `required_distance_ft`
- `opportunity_time_s`
- `direction_class`
- `near_wall`
- `baseline_catch_probability`
- `defender_rating`
- `adjusted_catch_probability`

Frozen `DefensiveResolution` fields:
- `valid`
- `opportunity`
- `catch_probability`
- `roll`
- `physical_out_shadow`

`BattedBallState` now optionally stores both objects.

## OWNERSHIP / NOMINAL ANCHORS
Phase2D V1 uses deterministic fixed OF responsibility sectors; no nearest-fielder loop or roster traversal.
- spray < -15 deg -> LF
- -15..+15 deg -> CF
- spray > +15 deg -> RF

Engineering baseline anchors in feet:
- LF `(-131.66, 258.39)`
- CF `(0.0, 315.0)`
- RF `(+131.66, 258.39)`

These are structural/research-informed engineering baselines, not measured KBO averages.
Required distance is one O(1) Euclidean distance from the fixed anchor to the Phase2B landing/catch coordinate.

## OPPORTUNITY TIME / DIRECTION
- Phase2B `hang_time_s` is used as the V1 opportunity-time proxy; it is not claimed to be definition-identical to Statcast opportunity time.
- movement direction is the radial component of anchor->catch displacement:
  - `in`: toward home;
  - `lateral`;
  - `back`: away from home.
- fixed 10-ft radial threshold separates lateral from in/back.
- probability offsets structurally satisfy `back <= lateral <= in` for equal time/distance/context.

## WALL CONTEXT
Phase2D reuses Phase2C `WallInteraction`; no new wall geometry engine exists.
- catch-point radial distance within 20 ft inside the queried wall is `near_wall`.
- near-wall applies a non-positive logit penalty and therefore cannot improve catch probability.
- trajectories that already reach/interact with the wall are intentionally not treated as ordinary landing-point catches in V1, because rebound/catch-point physics is not implemented.
- over-wall / physical-HR-shadow paths are invalid defensive opportunities.

## PROBABILITY ARCHITECTURE
V1 structural baseline is one fixed logistic surrogate:
`baseline_logit = 2.0 + 1.35*time_s - 0.075*required_distance_ft + direction + trajectory_class + wall_penalty`.

Direction offsets:
- in `+0.35`
- lateral `0.0`
- back `-0.45`

Trajectory-class offsets:
- line drive `-0.15`
- fly ball `0.0`
- popup `+0.10`

Wall-adjacent penalty: `-0.65` logit.

Average-defender baseline is converted to probability, then current production defense scalar adjusts log odds:
- reference rating 100;
- `+0.025` logit per rating point;
- adjustment clamped to `[-1,+1]` logit.

This separation prevents an elite rating from turning an extreme impossible opportunity into a routine catch solely through unbounded rating lift, and prevents a poor rating from collapsing routine opportunities without limit. Coefficients are engineering baselines, not KBO-exact calibration.

Required structural properties are covered by tests:
- finite and [0,1] bounded;
- more time non-decreasing P;
- more distance non-increasing P;
- higher defense non-decreasing P;
- `back <= lateral <= in`;
- near-wall <= equivalent non-wall.

## DEFENSE RATING CONTRACT
No rating-system recalibration was performed.
`HittingEngine.defense` is passed unchanged into Phase2D as `defender_rating` metadata.
No per-position lineup traversal or new roster provider was added.
The typed interface can later accept individual defender ratings from 02/07 integration without changing the Phase2D probability state schema.

## RNG ISOLATION
Phase2D probability calculation is deterministic.
The shadow catch decision uses exactly one child RNG roll from dedicated fork namespace `0x503244`.
The fork fingerprints the parent RNG state without advancing it.
Phase2A retains its existing separate namespace `0x503241`.

Therefore:
- same parent state / same physical state -> exact same Phase2D metadata and roll;
- parent gameplay RNG state is unchanged by Phase2D;
- disabling the Phase2D shadow resolution produces the same legacy result sequence and final canonical RNG state.

## INVALID / OUT-OF-SCOPE STATE
Fail-safe invalid opportunities are explicit and never produce a physical out.
Handled invalid/not-applicable cases include:
- missing trajectory;
- `trajectory.valid == False`;
- ground-like trajectory (`ground_not_modeled_v1`);
- shadow foul;
- missing/non-finite/invalid wall context;
- physical over-wall path;
- wall-intersection path without rebound model;
- non-finite defender rating / catch geometry / probability.

For invalid opportunity:
- probability is finite and safe;
- resolution is invalid;
- `roll=None`;
- `physical_out_shadow=False`.

## CHANGED PRODUCTION FILES
- new `src/hitting/physical_defense.py` — Phase2D schema, ownership, probability and resolution.
- modified `src/hitting/physical.py` — attach Phase2D metadata; dedicated child RNG namespace.
- modified `src/hitting/model.py` — pass existing `self.defense` scalar into Phase2D generator only.

Legacy production files intentionally unchanged:
- `src/hitting/defense.py` blob remains `279f6282ef41c53e709839dbbe791e16836eaf53`.
- `src/hitting/parameters.py` remains `3876b4221f53b7d4b7cc6069d9425004fc9f311a`.
- `src/hitting/baserunning.py` remains `2a383ce61fb6938ae30973be210159baa1d76726`.

Approved Phase2D model wiring blob is `src/hitting/model.py = 585d4cd0eb4c5464d02fe0805d359b0e9cafe39d`; protected snapshot tests were updated only for this explicit wiring checkpoint.

## TESTS / CI
Code/test checkpoint: `144e2b811ebe0cfade8aca5653c53eb8a30c19aa`.
GitHub Actions run: `34666196039`.

PASS:
- web build/tests;
- Python dependency contract / compile;
- durable-store and API gates;
- related production integration: 31/31;
- all Phase1 count/foul/HBP/regression tests;
- all Phase2A tests including parent-RNG purity and constant-time guard;
- all Phase2B tests including paired 50k PA/games invariance and O(1) guard;
- all Phase2C tests including invalid-trajectory HR guard, wall geometry, mirror, deterministic replay and wall O(1) guard;
- all 13 Phase2D targeted tests:
  - finite/bounds;
  - distance monotonicity;
  - time monotonicity;
  - rating monotonicity;
  - direction ordering;
  - wall ordering;
  - LF/RF mirror;
  - invalid trajectory no out;
  - ground-like not modeled V1;
  - wall-intersection / over-wall fail-safe;
  - same-state deterministic replay + parent RNG purity;
  - production scalar-defense wiring;
  - legacy outcome/RNG invariance with shadow resolution disabled.

Full Python discover: 419 tests, 418 PASS, 1 FAIL.
Sole failure remains the pre-existing/out-of-scope `test_balance_v04.BalanceV04Tests.test_draft_distribution_not_extreme`: `undrafted=0.056666...`, historical assertion requires `>0.10`. Phase2D does not touch generation/draft balance.

## PERFORMANCE
No Phase2D benchmark tuning was performed.
Architecture is fixed-cost O(1) per BIP:
- one fixed ownership dispatch;
- one Euclidean distance;
- fixed direction math;
- fixed wall comparison;
- fixed logistic/logit arithmetic;
- one child RNG construction/roll;
- no frame loop, timestep, pathfinding, nearest-player scan, numerical integration or iterative solve.

Existing same-run regression guards remained healthy:
- Phase2B paired 50k PA ratio `1.3729x`, below its existing test guard; game ratio `1.2070x`.
- Phase2C paired ratio `0.9504x`.
These are CI-runner measurements, not Phase2D calibration benchmarks. 05 should run its own paired Phase2D benchmark on a larger controlled corpus.

## KNOWN LIMITATIONS
- primary deterministic OF owner only; no adjacent gap defender blend in V1.
- fixed nominal OF anchors are engineering baselines, not KBO-measured positioning distributions.
- no actual fielder path/route simulation or dynamic defensive positioning.
- wall-intersection/rebound catch opportunities are intentionally unresolved.
- ground bounce/roll, retrieval, throw-to-first and physical 1B/2B/3B authority are Phase2E+.
- current production still uses the Phase2C generic stadium context rather than per-game stadium assignment.
- physical HR/fair-foul/defensive-out remain shadow-only.
- Phase2D coefficients need independent distribution validation before any authority migration.

## HANDOFF TO 05
Independent validation target:
- PR #65 `Gameplay: Phase 2D physical defensive catch shadow`.
- Validate the exact final PR HEAD reported after this status-only commit; production code identity should match code/test checkpoint `144e2b811ebe0cfade8aca5653c53eb8a30c19aa` except this status document.

Required 05 gates:
1. source/blob identity against PR #65;
2. opportunity-valid rate by trajectory class;
3. LF/CF/RF responsibility and symmetric LF/RF mirror distributions;
4. required-distance/time/direction distributions;
5. catch-P finite/bounds and monotonicity;
6. rating sensitivity without impossible-opportunity reversal or routine collapse;
7. near-wall non-increasing property;
8. invalid/ground/wall-path physical-out zero invariant;
9. exact legacy Phase1/2A/2B/2C/final-result regression;
10. deterministic replay and parent-RNG non-consumption;
11. paired 50k+ PA and representative full-game Phase2D performance.

Do not tune gameplay outcomes or make physical defense authoritative during validation.

## GATES
- PHASE2D_TYPED_STATE = PASS
- DEFENDER_OWNERSHIP_O1 = PASS
- PROBABILITY_FINITE_BOUNDS = PASS
- DISTANCE_MONOTONICITY = PASS
- TIME_MONOTONICITY = PASS
- RATING_MONOTONICITY = PASS
- DIRECTION_ORDERING = PASS
- WALL_ORDERING = PASS
- MIRROR = PASS
- INVALID_STATE_FAIL_SAFE = PASS
- RNG_PURITY = PASS
- LEGACY_RESULT_INVARIANCE = PASS
- PHASE2C_REGRESSION = PASS
- PHASE2B_REGRESSION = PASS
- PHASE2A_REGRESSION = PASS
- PHASE1_REGRESSION = PASS
- PRODUCTION_INTEGRATION = PASS
- PERFORMANCE_ARCHITECTURE = PASS_O1
- FULL_PYTHON_SUITE = BLOCKED_ONLY_BY_OUT_OF_SCOPE_DRAFT_GATE_418_OF_419_PASS
- PHASE2D_IMPLEMENTATION = PASS
- PHASE2D_05_VALIDATION = OPEN
- READY_FOR_05 = YES
