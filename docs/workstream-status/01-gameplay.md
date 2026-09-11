# 01 - Gameplay Engine

WORKSTREAM: 01 - Gameplay Engine
UPDATED_AT: 2026-09-11
SOURCE_OF_TRUTH: task-start main@b764e4b32dcdc4af9947e83b9732e41b8be6d396; implementation PR #58
STATE: READY_FOR_05_VALIDATION
CURRENT_TASK: Phase 1 Plate Discipline / Strike / Contact Calibration
RESULT: IMPLEMENTATION_PASS_HEAVY_VALIDATION_OPEN

## SCOPE
- Phase 1 only: pitch/count/swing/contact/foul/strikeout/HBP structure.
- Physical batted-ball model remains unchanged: no exit velocity, launch angle, spray angle, trajectory, park, HR, 2B/3B, defense, rating-generation, growth, event, or pitcher-usage tuning.

## BASELINE
05 neutral diagnostic before Phase 1:
- Zone 55.149%; Swing 47.473%; Chase 21.253%; Z-Swing 68.797%.
- Whiff/Swing 27.385%; Z-Contact 74.644%; O-Contact 64.540%.
- BB 8.060%; K 21.247%; looking-K share 54.43%; HBP 0.
- H/PA 24.050%; HR/PA 2.737%.

## IMPLEMENTATION
- Count model: replaced mutually-exclusive `strikes == 2 else balls == 3` adjustment with independent two-strike protection and three-ball selectivity terms. Full count receives both.
- Neutral out-of-zone chase baseline moves 0.245 -> 0.255 while discipline chase slope compresses 0.0045 -> 0.0025 to keep neutral chase stable/slightly higher and reduce low-discipline blow-up.
- Count adjustments:
  - 0-2 / 1-2 / 2-2: zone +0.090, chase +0.005.
  - 3-0: zone -0.050, chase -0.070.
  - 3-1: zone -0.015, chase -0.050.
  - 3-2: zone +0.075, chase -0.045; two-strike protection and three-ball selectivity both remain active.
- Contact/whiff: existing fair-contact `touch_probability` and all batted-ball-quality formulas are unchanged. A bounded share of failed touch checks is rescued to FOUL only: stronger in-zone, weaker out-of-zone, with a small additional two-strike survival term. MISS is never converted directly to HIT/BIP.
- HBP: new terminal pitch-level path on out-of-zone pitches before swing/take/contact; neutral per-out-of-zone-pitch baseline 0.009 with modest pitcher-control sensitivity; existing `hit_by_pitch` stat/base advancement and pitcher accounting are reused.
- PA safety loop remains capped at 20 pitches; two-strike foul still cannot become strike three.

## PROVISIONAL SENSITIVITY
Deterministic 100k neutral formula sensitivity on the Phase 1 contract; this is implementation guidance, not the canonical 05 heavy result:
- Zone 55.10%; Swing 48.23%; Z-Swing 70.06%; Chase 21.45%.
- Contact/Swing 78.31%; Whiff/Swing 21.69%; Z-Contact 80.92%; O-Contact 67.82%.
- Called strike/pitch 16.50%; swinging strike/pitch 10.46%; foul/pitch 15.40%.
- Pitches/PA 3.23; K 18.13%; looking-K share 53.34%; BB 8.33%; HBP 1.28%.
- H/PA 24.55%; HR/PA 2.80%.
- Compared with 05 baseline: K -3.12pp, whiff -5.69pp, Z-contact +6.28pp, BB +0.27pp, chase +0.19pp, H/PA +0.50pp, HR/PA +0.06pp. No provisional offense explosion, but H/HR/runs require 05 heavy confirmation.
- Discipline chase sensitivity is intentionally compressed: neutral remains near prior level while low-discipline examples move materially downward relative to the old slope.

## OBSERVABILITY
`tools/offense_pitch_diagnostic.py` now emits:
- Zone/Swing/Z-Swing/Chase/Contact/Z-Contact/O-Contact/Whiff.
- called strike, swinging strike, foul, two-strike foul, pitches/PA.
- 0-2, 3-0, 3-1, 3-2 reach.
- K plus looking/swinging split, BB, HBP, H/PA, HR/PA.
- Full-game runs and full `BattingLine` ROE/GDP/SF/XBT/first-to-third/second-to-home counters.

## REGRESSION
PR #58 CI run `34593444847` at code checkpoint `40de9f46b1a19b7be5fb88a29f8ecd6144fdea09`:
- Web build/tests PASS.
- Compile, dependency contract, external durable-store tests, API entrypoint and vertical-slice tests PASS.
- Related production integration: 31/31 PASS.
- Phase 1 dedicated tests PASS: independent full-count terms, bounded chase separation, HBP placement/control sensitivity, two-strike foul survival, neutral 100k offense bounds, rating monotonicity, deterministic seed, save compatibility.
- Full Python discover: 351 tests executed; 350 PASS, 1 FAIL.
- Sole failure: legacy `test_balance_v04.test_draft_distribution_not_extreme` (`undrafted=4.33%`, historical assertion >10%). The test calls only `Player.random()` + `CareerEngine.evaluate_draft()` and never gameplay; PR #58 changes neither player generation nor draft evaluation. It is classified as a pre-existing/out-of-scope draft calibration gate and is intentionally not weakened in 01.
- Because the full-suite command stops on that unrelated failure, downstream workflow smoke/gates after the unit step were skipped in that run. Existing production gameplay/integration coverage before that gate is PASS.

## 05 HANDOFF
After PR #58 integration, rerun canonical diagnostic with the same seed/definitions and at minimum:
1. Neutral 100 vs neutral 100: 200k PA + 10k full games.
2. Generated prospect hitters vs neutral pitcher: 200k PA.
3. Representative mature production roster PA-weighted population if available.
4. Report Zone%, Swing%, Z-Swing%, Chase%, Contact%, Z/O-Contact%, Whiff/Swing, called-strike%, swinging-strike%, foul%, two-strike-foul%, pitches/PA, 0-2/3-0/3-1/3-2 reach, K%, looking/swinging K share, BB%, HBP%, H/PA, HR/PA, runs/game.
5. Explicitly compare offense side effects: H/PA, HR/PA, runs/game and PA length; flag any material explosion before Phase 2.
6. Validate deterministic replay, legal counts, no infinite PA, safety-cap hits=0, full-game invariants.

## OPEN ITEMS
- 05 canonical heavy validation is required before declaring Phase 1 calibrated for production.
- Mature-roster population comparison remains dependent on 02/05 data availability.
- The unrelated draft-distribution unit gate remains outside 01 scope and should be routed to its owning calibration workstream rather than relaxed here.
- Phase 2 physical batted-ball work must not begin until 05 confirms Phase 1 event composition and offense side effects are acceptable.

## RELATED PRS
- #58 open — Phase 1 plate discipline and contact calibration.

## GATES
- COUNT_MODEL = PASS
- CHASE_MODEL = PASS_IMPLEMENTATION / OPEN_HEAVY
- CONTACT_WHIFF_MODEL = PASS_IMPLEMENTATION / OPEN_HEAVY
- TWO_STRIKE_FOUL = PASS_IMPLEMENTATION / OPEN_HEAVY
- HBP_PATH = PRESENT
- PHYSICAL_BATTED_BALL_CHANGED = NO
- GAMEPLAY_INTEGRATION_REGRESSION = PASS
- FULL_PYTHON_SUITE = BLOCKED_BY_PREEXISTING_DRAFT_GATE_350_OF_351_PASS
- PHASE1_05_HEAVY_VALIDATION = OPEN
- PHASE2_ALLOWED = NO_UNTIL_05_VALIDATION
