# 01 - Gameplay Engine

WORKSTREAM: 01 - Gameplay Engine
UPDATED_AT: 2026-09-12
SOURCE_OF_TRUTH: task-start main@39aa1f1d619ad1a4d3b4595d3b3aa6e6e6fdb2ca; latest observed main@ef95f1cef5752b1e74667bc087427dd884d88f37; PR #60
STATE: READY_FOR_05_PHASE2B_VALIDATION
CURRENT_TASK: Phase 2B analytical trajectory and landing-position implementation
RESULT: PASS_IMPLEMENTATION / 05_VALIDATION_OPEN

## SOURCE_STATE
- PR #59 Phase 2A was confirmed merged before Phase2B work began. Merge commit / task-start latest main: `39aa1f1d619ad1a4d3b4595d3b3aa6e6e6fdb2ca`.
- New branch created from that actual main: `feature/phase2b-analytical-trajectory`.
- PR: #60 `Gameplay: Phase 2B analytical trajectory and landing position`.
- Implementation / test checkpoint: `6f50473f2a6df90382037b75d617b81373b2f34b`.
- During work main advanced to `ef95f1cef5752b1e74667bc087427dd884d88f37` through two 08 research/status-only commits (`phase2c-kbo-stadium-wall-geometry-reference.md` and 08 status); no production gameplay source changed. PR #60 is mergeable against current main.

## PHASE2A CONTRACT PRESERVED
Phase2A remains authoritative for physical initial state:
- EV in mph.
- launch angle / spray angle in degrees.
- normalized timing.
- contact quality / coarse pitch metadata / handedness.
- physical `is_fair` remains shadow-only after legacy foul filtering.

Phase2A parent-RNG fork/non-consumption contract is unchanged. Phase2B trajectory uses no RNG at all and does not alter EV/LA/timing/spray generation.

## TRAJECTORY MODEL
New files:
- `src/hitting/trajectory.py`
- `src/hitting/trajectory_parameters.py`

Modified production file:
- `src/hitting/physical.py` only; `src/hitting/model.py` remains unchanged so the legacy HR/XBH/defense call chain and RNG order are untouched.

Runtime is fixed-cost O(1):
- no frame stepping;
- no timestep loop;
- no numerical integration loop;
- no iterative root solve;
- no external dependency.

### Low / negative LA
A 3-ft launch-height first-ground intersection is solved analytically:
- convert mph to ft/s;
- `vy = v*sin(theta)`, `vx = v*cos(theta)`;
- positive vertical root from `z(t)=h+vy*t-0.5*g*t^2=0`;
- for negative `vy`, a rationalized equivalent form avoids cancellation;
- horizontal first-impact distance is `vx*t*0.97`.

This branch intentionally stops at first ground impact. Bounce, roll, friction and fielder pickup are not modeled.

### Positive air-ball surrogate
For positive air balls Phase2B uses a deterministic algebraic EVxLA surrogate derived from the 08 lightweight-trajectory research constraints rather than raw vacuum projectile range.

Carry at 100 mph is shaped around a high-20s optimum:
- peak LA = `29 deg`;
- anchor = `397 ft` at `100 mph / 29 deg`;
- angle surface = `max(25, 397 - 0.18*(LA-29)^2)`;
- EV scaling = `(EV/100)^1.65`, bounded to Phase2A EV domain and max 550 ft.

This anchor is a trajectory sanity reference, not HR-rate tuning. Carry is deliberately lower at 45 deg than at 29 deg, unlike a vacuum model.

Ground/air transition from 0 to 8 deg uses fixed smoothstep blending so near-zero LA is continuous without loops.

### Hang time
Air-ball ground-flight time uses a fixed algebraic surface:
- at 100 mph: `1.20 + 0.175*LA - 0.00125*LA^2` seconds;
- weak EV scaling `(EV/100)^0.25`;
- bounded to 0-9 s;
- low LA blends against exact first-impact flight time.

### Apex
- vertical-velocity analytical baseline from the same EV/LA;
- positive vertical vacuum height gain multiplied by fixed `0.78` aerodynamic reduction;
- launch height = 3 ft;
- bounded to 260 ft;
- negative LA apex is the 3-ft launch height.

These carry/hang/apex coefficients are V1 structural surrogates. 05/08 validation must judge distribution realism before Phase2C uses trajectory for authoritative wall decisions.

## OUTPUT SCHEMA
`BattedBallTrajectory` is frozen/typed and contains:
- `horizontal_distance_ft`
- `hang_time_s`
- `apex_height_ft`
- `landing_x_ft`
- `landing_y_ft`
- `trajectory_class` (`ground_like`, `line_drive`, `fly_ball`, `popup`) — descriptive metadata only
- `valid`

Compatibility aliases:
- `carry_distance_ft`
- `first_ground_impact_distance_ft`

`BattedBallState` now has optional `trajectory: BattedBallTrajectory | None`; every real production BIP produced through `generate_batted_ball_state()` receives a non-null trajectory in Phase2B.

## COORDINATE SYSTEM
Canonical unit: feet.
- home plate = `(0,0)`;
- center field = `+Y`;
- left field = negative `X`;
- right field = positive `X`;
- spray angle `0 deg` = center field.

Conversion:
- `landing_x = distance * sin(spray)`;
- `landing_y = distance * cos(spray)`.

Therefore mirrored `+theta/-theta` spray at identical EV/LA has identical distance/y and opposite-sign x.

## PRODUCTION WIRING / LEGACY BRIDGE
Production flow is now:
`Phase1 contact -> Phase2A BattedBallState -> Phase2B BattedBallTrajectory -> legacy _batted_ball -> legacy HR -> legacy defense -> legacy 1B/2B/3B -> PersistentInningEngine`.

Trajectory is real production-path data, not diagnostic dead code. However it is non-authoritative for final result resolution in Phase2B.

Still authoritative and unchanged:
- Phase1 miss/foul/BIP, HBP, BB/K and count semantics;
- physical `is_fair` is shadow-only;
- legacy `_is_home_run()`;
- legacy defense catch/error;
- legacy direct 1B/2B/3B candidate/speed resolver;
- existing runner advancement.

No `src/hitting/model.py` change was required, preserving protected model formula blobs and canonical RNG ordering.

## FUTURE DEFENSE CONTRACT
Phase2B provides all geometry needed for the approved future probabilistic defense contract without fielder frame simulation:
- landing x/y;
- hang time;
- EV / LA from parent state;
- descriptive trajectory class;
- spray sector from parent state.

Phase2D can combine these with relevant defender defense/range ratings to produce one catch probability and one RNG decision. No timestep fielder position/route state should be added.

## DETERMINISM / REGRESSION
Trajectory generation is a pure deterministic function of `BattedBallState` and consumes zero RNG.

Dedicated paired CI test disables trajectory generation test-only and compares it with Phase2B enabled under the exact same seeds:
- 50,000 neutral PA result counters: exact equal;
- parent RNG final state: exact equal;
- 250 production game `(away_score, home_score, innings_played, event_count)` summaries: exact equal.

Phase2A regression test compares 500 deterministic states with trajectory disabled vs enabled and confirms EV, LA, timing, spray, fair flag and contact quality are exact-identical.

Phase1 40k fixed-seed diagnostic in the same CI remained unchanged:
- Swing 48.0969%; Z-Swing 70.4183%; Chase 20.9709%.
- BB 9.4625%; K 17.6475%; HBP 1.285%.
- Looking-K share 40.558%; pitches/PA 3.2401.
- H/PA 24.51%; HR/PA 2.835%.
- 3-0 Swing 5.336%.

## TESTS / CI
PR #60 implementation checkpoint: `6f50473f2a6df90382037b75d617b81373b2f34b`.
GitHub Actions run `34636773955`:
- Web build/tests PASS.
- compile / dependency / durable-store / API gates PASS.
- related production integration: 31/31 PASS.
- all Phase2A dedicated tests PASS.
- all Phase2B dedicated tests PASS (12/12).
- KBO 11-inning regression PASS.
- Phase1 count/contact/foul/HBP/determinism regressions PASS.
- protected gameplay/formula tests PASS; model.py is unchanged.
- full Python discover: 388 tests, 387 PASS, 1 FAIL.
- sole failure remains pre-existing/out-of-scope `test_balance_v04.test_draft_distribution_not_extreme` (`undrafted=5.667%`, historical assertion requires >10%); no gameplay path is involved.

The overall workflow is therefore not globally green only because the unrelated draft gate stops later workflow steps; Phase2B/gameplay/production-integration gates are green.

## PERFORMANCE
Same-process paired benchmark from run `34636773955`:
- 50k PA baseline with trajectory test-disabled: 3.6770 s.
- 50k PA Phase2B enabled: 3.6635 s.
- ratio: `0.9963x`.
- 250 production games baseline: 2.3434 s.
- 250 production games Phase2B enabled: 2.2138 s.
- ratio: `0.9447x`.

The apparent speedup is shared-runner noise; the relevant conclusion is no measurable slowdown signal. A separate 50,000 direct-trajectory guard also PASSes under a loose 6 s CI cap. Runtime complexity remains fixed O(1) per BIP.

## KNOWN LIMITATIONS
- Carry/hang/apex surfaces are lightweight V1 surrogates, not CFD and not yet KBO-calibrated trajectory distributions.
- Wind, temperature, altitude, humidity, spin axis and seam effects are deferred.
- `trajectory_class` is descriptive only and does not replace legacy ball_type.
- Physical fair/foul remains conditioned on an already-legacy-BIP population and is non-authoritative (`FAIR_FOUL = WATCH`).
- No stadium geometry, wall intersection, physical HR, fielder catch probability, physical XBH resolution, bounce/roll or runner advancement integration exists yet.
- Distance/hang/apex numerical caps are safety guards, not outcome targets.

## 05 HANDOFF
05 may validate PR #60 / implementation checkpoint `6f50473...` now.
Minimum Phase2B validation:
1. Production-path distributions of carry, hang time, apex and landing radius/coordinates.
2. EVxLA grid / fixed-EV angle sweeps verifying max carry near high-20s rather than 45 deg.
3. 100 mph / 29 deg approximately 397-ft sanity anchor; do not treat it as league HR tuning.
4. Low/negative LA first-impact grid versus 08 derived examples.
5. High-LA hang/apex tails and absurd-value/bound pileup checks.
6. +/- spray mirror symmetry and CF x~=0.
7. Phase2A EV/LA/timing/spray distributions exact-regression check.
8. Phase1 / legacy 1B/2B/3B/HR/runs fixed-seed exact-regression check.
9. Same-run paired performance; do not judge solely from cross-run shared-runner variance.

Do not tune HR/XBH/defense/runner outcomes during Phase2B validation.

## PHASE2C HANDOFF
- Phase2C stadium/wall design research is already available from 08, but production implementation remains blocked on 05 Phase2B trajectory validation/signoff.
- Phase2C should consume trajectory landing/carry/apex plus stadium geometry, while keeping defense/XBH migration for later stages.
- Physical fair/foul must remain shadow-only unless a separate explicit foul-boundary migration is designed and validated.

## RELATED PRS
- #59 merged before Phase2B task start.
- #60 OPEN / mergeable — Phase 2B analytical trajectory and landing position.

## GATES
- TRAJECTORY_FINITE = PASS
- CARRY_BEHAVIOR = PASS_STRUCTURAL / WATCH_05_REALISM
- HANG_TIME = PASS_STRUCTURAL / WATCH_05_REALISM
- APEX_HEIGHT = PASS_STRUCTURAL / WATCH_05_REALISM
- LANDING_COORDINATES = PASS
- MIRROR_SYMMETRY = PASS
- GROUND_IMPACT = PASS
- PHASE2A_REGRESSION = PASS
- PHASE1_REGRESSION = PASS
- LEGACY_RESULT_INVARIANCE = PASS
- DETERMINISM = PASS
- PERFORMANCE = PASS
- FAIR_FOUL = WATCH
- FULL_PYTHON_SUITE = BLOCKED_ONLY_BY_OUT_OF_SCOPE_DRAFT_GATE_387_OF_388_PASS
- PHASE2B_05_VALIDATION = OPEN
- PHASE2B = PASS_IMPLEMENTATION / OPEN_05
- PHASE2C_ALLOWED = PENDING_05_SIGNOFF
