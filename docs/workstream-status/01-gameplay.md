# 01 - Gameplay Engine

WORKSTREAM: 01 - Gameplay Engine
UPDATED_AT: 2026-09-12
SOURCE_OF_TRUTH: task-start main@584e5902d6187355631563fd0edb97a6e16483e9; latest observed main@835587210161c4f26bf433cd98ad0d92ada4cad3; PR #59
STATE: READY_FOR_INTEGRATION
CURRENT_TASK: Phase 2A Physical Batted-Ball Engine implementation
RESULT: PASS

## SOURCE_STATE
- Phase 2A implementation branch was created from integrated Phase-1 main `584e5902d6187355631563fd0edb97a6e16483e9` exactly as required; no PR #58 feature branch was reused.
- Branch: `feature/phase2a-physical-batted-ball`.
- PR: #59 `Gameplay: Phase 2A physical batted-ball initial state`.
- Core production wiring checkpoint is the Phase2A model/physical implementation introduced before the later research/status merge; final code/test checkpoint including RNG compatibility is `6a6d30d7ae33c8b1a5443d557f48eddd88a575b6`.
- During work, main advanced only through Phase-2A research/status documentation. The branch incorporated the Phase-2A research reference merge at `53687c952afdf39713a4be71f24a910eec0c62de`; later main `835587210161c4f26bf433cd98ad0d92ada4cad3` additionally updates 05 validation status only.

## CURRENT_ENGINE_BOUNDARY
Production flow remains:
`Pitch -> Phase1 swing/take/HBP -> Phase1 contact miss/foul/bip -> Phase2A initial state on BIP -> legacy BattedBall/result resolver -> PersistentInningEngine`.

Phase-1 semantics remain authoritative for:
- pitch selection / count behavior / swing / chase;
- contact probability / miss / foul / two-strike survival;
- HBP / BB / K / two-strike take rescue.

Legacy authority remains for:
- ground/line/fly category;
- depth/direction compatibility fields;
- direct HR probability;
- legacy defense catch/error;
- direct 1B/2B/3B candidate and speed resolution.

## PHASE2A_IMPLEMENTATION
New production files:
- `src/hitting/physical.py`
- `src/hitting/physical_parameters.py`

Modified production integration:
- `src/hitting/model.py`

New tests:
- `tests/test_phase2a_physical_batted_ball.py`

Protected gameplay blob expectations were advanced only for the intentionally changed `src/hitting/model.py` in:
- `tests/test_production_game_provider.py`
- `tests/test_production_integration_consolidation.py`
- `tests/test_stat_aggregation_advance.py`

### BattedBallState
Immutable `@dataclass(frozen=True)` fields:
- `exit_velocity`: mph
- `launch_angle`: degrees
- `timing`: normalized `[-1,+1]`, negative late / positive early
- `spray_angle`: degrees, center field 0, left-field negative, right-field positive
- `is_fair`: spray-derived shadow fair/foul flag
- `contact_quality`: normalized `[0,1]`
- `pitch_location_x`: batter-relative normalized coarse horizontal location (`-1` inside, `+1` outside)
- `pitch_location_y`: normalized coarse vertical location (`-1` low, `+1` high)
- `batter_side`: `L/R`

The schema is intentionally trajectory-ready; Phase 2B can extend/compose hang time, distance, landing coordinates and apex without changing the Phase-1 PA contract.

### Exit Velocity
- Generated from latent contact quality + hitter power + pitch velocity quality + controlled noise.
- Hitter Contact influences contact-quality consistency rather than mapping raw rating directly to mph.
- Power shifts EV mean/upper tail; no `rating 100 == fixed mph` contract exists.
- Provisional bounded range: 30–125 mph.

### Launch Angle
- Continuous degrees, not a categorical GB/LD/FB roll.
- Depends on contact quality, coarse pitch vertical location, mild bounded hitter profile term and stochastic variation.
- Provisional range: -65° to +85°.

### Timing
- Continuous scalar `[-1,+1]`.
- Uses pitch velocity quality and coarse pitch location; hitter Contact changes timing variance.
- Both early and late contact are produced.

### Spray
- Fixed field convention: CF=0°, LF negative, RF positive.
- Uses timing + batter-relative horizontal pitch location + approach bias + noise, then mirrors by handedness.
- Early RHH contact trends pull/LF; late RHH trends opposite/RF; LHH mirrors exactly in controlled same-state tests.
- Provisional range: -75° to +75°.

### Fair/Foul
- `is_fair` is derived deterministically from spray angle with inclusive foul-line boundaries `[-45°, +45°]`.
- Strong physical foul states are possible.
- IMPORTANT: this field is shadow-only in Phase 2A. Existing Phase-1 foul resolution remains authoritative because the physical state is intentionally generated only after legacy contact has already returned `bip`.
- Making physical fair/foul authoritative later requires an explicit migration step before/around the legacy foul filter plus all-contact/count-split validation.

## LEGACY_RESULT_BRIDGE
Every real production `contact_result == "bip"` now generates `BattedBallState` and attaches it to `BattedBall.physical_state` before legacy result resolution.

Current bridge:
`Phase1 BIP -> generate BattedBallState -> legacy _batted_ball -> legacy _is_home_run -> legacy defense -> legacy 1B/2B/3B`.

Therefore Phase2A is not dead/diagnostic-only code, while final results remain bit-for-bit legacy-compatible under the canonical RNG stream.

## RNG / DETERMINISM
- Physical generation fingerprints/forks the parent RNG state and uses a child `RNG`; it does not consume the canonical parent stream.
- New draws occur only for physical state after a real BIP; take/miss/foul/HBP paths do not run the generator.
- Project `RNG.get_state()` and direct stdlib `random.Random.getstate()` callers are both supported after the CI-discovered compatibility fix.
- Same parent state produces identical physical state; parent RNG state remains identical before/after generation.
- Existing same-seed full-game and save/load deterministic regressions PASS.

## VALIDATION
### 01 PR CI
Final code/test checkpoint: `6a6d30d7ae33c8b1a5443d557f48eddd88a575b6`.
GitHub Actions run `34624052417`:
- Web build/tests PASS.
- compile / dependency / durable-store / API gates PASS.
- related production integration: 31/31 PASS.
- Phase2A dedicated tests: 15/15 PASS.
- pitcher-calibration stdlib RNG compatibility tests PASS after fix.
- KBO 11-inning regressions PASS.
- Phase1 count/contact/HBP/two-strike/determinism regressions PASS.
- Full Python: 376 tests, 375 PASS, 1 FAIL.
- Sole failure is the pre-existing out-of-scope `test_balance_v04.test_draft_distribution_not_extreme` (`undrafted=5.667%`, historical assertion requires >10%); no gameplay path is involved and it was not weakened.

Representative Phase1 40k diagnostic in the same CI remained stable:
- BB 9.4625%; K 17.6475%; HBP 1.285%.
- Looking-K share 40.558%; Chase 20.971%; Z-Swing 70.418%; pitches/PA 3.2401.
- 3-0 Swing 5.336%.

### 05 independent validation
Latest main 05 status independently validated the Phase2A production candidate and records `RESULT: PASS_WITH_FAIR_FOUL_WATCH` / `PHASE2A_VALIDATION = PASS`.
- Frozen production-code candidate: `d8b7efc40b150b987867e4240d0127f4bcaf09f3`.
- Validation checkout: `be2763a3c55b6f47c1d6a15487bdc5fe507911ba`.
- Actions run `34623705971`: SUCCESS.
- The later 01 RNG compatibility fix only accepts the stdlib accessor variant; it does not alter the project-RNG child seed, physical coefficients, canonical RNG consumption or production distribution contract. Final 01 CI confirms compatibility/regression after that fix.

05 measured on production-path physical states:
- EV mean 84.056 mph, SD 6.295, P5/P50/P95 73.570/84.158/94.225.
- LA mean 9.950°, SD 19.206, continuous/non-collapsed.
- Timing mean ~0, SD 0.342 with early/on-time/late all populated.
- Spray mean ~0°, SD 17.636; early/late and handedness directional contracts PASS.
- Phase1 offense baseline reproduced exactly at frozen seed/sample because canonical RNG is not consumed.

Fair/foul remains WATCH only because Phase2A state is conditioned on already-legacy-BIP contact: physical fair is ~99% in that conditional sample and must not be interpreted as an all-contact foul-rate model.

## PERFORMANCE
05 shared-runner measurement:
- pre-Phase2 50k PA: 2.7492 s (54.984 us/PA)
- Phase2A 50k PA: 2.8085 s (56.170 us/PA)
- PA delta: +2.16%
- pre-Phase2 500 games: 3.2970 s
- Phase2A 500 games: 2.9296 s (runner noise dominates at game scale; no slowdown signal)

Dedicated unit guard generates 20,000 physical states under a loose 12 s cap and PASSes; the observed CI segment is sub-second scale. No numerical integration, frame loop, external dependency or variable-complexity solver exists in Phase2A.

## KNOWN_LIMITATIONS
- EV/LA/Timing/Spray coefficients are provisional, not final KBO calibration.
- Physical `is_fair` is non-authoritative shadow state after legacy foul filtering.
- Pitch location remains categorical/coarse (`inside/middle/outside/high/low`), not exact plate coordinates.
- Production hitter `approach` remains effectively `balanced` unless a future canonical source supplies a profile.
- No distance, hang time, apex, landing point, trajectory, wall/stadium interaction, fielder movement/reach, physical catch/error, or physical HR/XBH resolution yet.
- Legacy HR/2B/3B/defense results remain authoritative.
- No new persistence schema for transient BattedBallState is introduced.

## 05 / PHASE2B HANDOFF
- 05 Phase2A validation: COMPLETE / PASS_WITH_FAIR_FOUL_WATCH.
- Phase2B trajectory design/implementation: ALLOWED by 05.
- Do not tune Phase2A EV/LA/spray coefficients as part of Phase2B without a separate evidence/calibration decision.
- Preserve child-RNG/no-canonical-consumption contract unless an explicit migration decision changes it.
- Do not make physical `is_fair` authoritative during Phase2B trajectory work without first relocating/duplicating initial-state generation around the Phase1 foul boundary and validating all-contact foul/count semantics.

## RELATED PRS
- #58 merged before Phase2A task start.
- #59 OPEN — Phase 2A physical batted-ball initial state.

## GATES
- PHASE1_REGRESSION = PASS
- BATTED_BALL_STATE = PASS
- EV_GENERATION = PASS
- LA_GENERATION = PASS
- TIMING_GENERATION = PASS
- SPRAY_GENERATION = PASS
- FAIR_FOUL = PASS_SHADOW / WATCH_AUTHORITY_MIGRATION
- DETERMINISM = PASS
- PERFORMANCE = PASS
- PRODUCTION_PATH_WIRING = PASS
- LEGACY_RESULT_BRIDGE = PASS
- FULL_PYTHON_SUITE = BLOCKED_ONLY_BY_OUT_OF_SCOPE_DRAFT_GATE_375_OF_376_PASS
- PHASE2A_05_VALIDATION = PASS_WITH_FAIR_FOUL_WATCH
- PHASE2A = PASS
- PHASE2B_ALLOWED = YES
