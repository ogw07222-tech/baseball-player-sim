# 08 - Baseball Data & Research

WORKSTREAM: 08 - Baseball Data & Research
UPDATED_AT: 2026-09-11
SOURCE_OF_TRUTH: main@61b1430e9090c89342125d8dca7bd4a8f9c5dd4b
STATE: ACTIVE
CURRENT_TASK: Compare simulation statistics against real KBO records
RESULT: FAIL_WITH_STRONG_LOCAL_MATCHES_AND_OPEN_GAPS

## LAST_COMPLETED
- Public data provenance/usage policy and detailed dataset provenance matrix remain in place.
- `docs/kbo-shared-evidence-baseline.md` provides common 02/03/04/05 references.
- `docs/kbo-roster-age-pitcher-workload-baseline.md` and pass2 provide roster/workload evidence.
- Added `docs/kbo-simulation-realism-comparison-2026-09-11.md` comparing the canonical 10,000-game simulation baseline against completed 2022-2025 KBO environments.

## SIMULATION_SOURCE
- Canonical comparison target is 05 Balance Lab GitHub Actions run `34488552895`, simulation SHA `7112ce550e0933a80b0c75701de46fbd03047077`, seed `20260906`, 10,000 games.
- Current-main production/career integration changes do not alter the core full-game simulation modules, so the 10k distribution remains valid by simulation-code identity.
- Key simulation values: runs/game 8.1360, hits/game 18.3810, HR/game 2.0976, BB/game 6.2906, K/game 16.5189, PA/game 77.3202, extra innings 10.50%, draws 3.49%, walk-offs 7.31%.

## CURRENT_FINDINGS
- Completed 2022-2025 KBO mean environment: runs/game 9.617, hits/game 18.237, HR/game 1.610, BB/game 7.103, K/game 14.684, PA/game 78.283.
- Simulation runs/game is 15.4% below the completed-season mean and below every 2022-2025 season -> FAIL.
- Hits/game is only 0.8% above the completed-season mean and H/PA is within recent KBO range -> PASS.
- HR/game is 30.3% above the 2022-2025 mean and above even the 2024 high-HR environment -> FAIL.
- BB/game is 11.4% below the recent mean and below every completed season in the reference window -> FAIL.
- K/game is 12.5% above the recent mean and above every completed season in the reference window -> FAIL.
- PA/game is close (-1.2% vs 2022-2025 mean) but slightly below the completed-season range -> WATCH.
- Aligned simulation rates: H/PA 23.77% PASS; BB/PA 8.14% FAIL; K/PA 21.36% FAIL; HR/PA 2.71% FAIL.
- Structural conclusion: the simulation is not simply low-offense. It has realistic hit volume but simultaneously low walks, high strikeouts, high home runs, and low runs. Event composition and run conversion must be decomposed before any tuning.
- Simulation regular-season max innings 11 and 12+ inning games 0 -> rule semantics PASS for current KBO rule.
- Draw frequency 3.49% vs completed 2025 3.06% -> WATCH.
- Extra-inning frequency 10.50% vs 2024 official 59/720 = 8.19% under the prior 12-inning rule -> WATCH with rule-definition mismatch noted.
- Walk-off rate 7.31% vs 2022-2025 secondary-reference mean ~6.56% -> WATCH.
- Simulation AVG/OBP/SLG/OPS/ISO/BABIP, HBP, errors, shutouts, aligned ERA/WHIP/K9/BB9/HR9, team parity, and matched real tail frequencies remain OPEN because required simulation or real game-level denominator fields are not yet available.

## REAL_KBO_REFERENCE
- Primary calibration reference period for this audit: completed regular seasons 2022, 2023, 2024, 2025.
- KBO official records/rules were preferred; completed team aggregates were cross-checked/derived from Yagoonara tables identifying `koreabaseball.com` as source.
- 2026 is incomplete and was used only as contextual confirmation, not as the calibration target.
- 2025 regular-season extra-inning cap is 11 innings; 2022-2024 used the prior 12-inning cap.

## CALIBRATION_ROUTING
- 05: measurement-only decomposition is highest priority. Emit PA/AB/R/H/1B/2B/3B/HR/TB/BB/IBB/HBP/SO/SF/SAC/GDP/E/ER and matched rate/distribution/tail counters before tuning.
- 01: after 05 decomposition, perform sensitivity-only analysis of BB/K/contact/HR pathways plus non-HR XBH, runner advancement, GDP, errors, baserunning, sacrifice and sequencing.
- 02: compare fixed-neutral-rating simulation with current generated-rating population to isolate formula bias from rating-distribution bias; inspect contact/power/discipline tails without changing scales.
- 03 + 05: split scoring/event rates by inning bands and starter/reliever context to test whether role/fatigue behavior suppresses late-game scoring.
- 00: decide multi-year recent-KBO target vs explicit single-season target only after sensitivity evidence if a cross-system calibration target must be locked.

## BLOCKERS
- Canonical full-game artifact does not yet expose enough batting accounting fields for direct AVG/OBP/SLG/OPS/ISO/BABIP comparison.
- It does not expose aligned pitching ERA/WHIP/K9/BB9/HR9 aggregates.
- Matched real KBO game-log percentile/extreme-tail aggregates are not yet built for 20+ runs, 15+ team runs, 100+ PA, shutouts and errors.
- Canonical independent-game artifact does not provide team-season standings/run-differential distributions for parity comparison.

## OPEN_ITEMS
- Ask 05 for a measurement-only expanded canonical simulation summary with complete batting/pitching accounting and P10/P25/P50/P75/P90/P95/P99 event distributions.
- Build recent KBO game-log aggregate tails under matched definitions: shutouts, 15+ team-run games, 20+ total-run games, 100+ PA games, HBP/errors, extra innings and walk-offs.
- Recover exact completed-2025 extra-inning game count under the 11-inning rule.
- Build 2022-2025 team-season win%, run differential and scoring/allowance distributions for parity validation.

## DEPENDENCIES
- 01: event probability and game-flow sensitivity once 05 exposes the decomposition.
- 02: neutral-vs-generated rating-population isolation for BB/K/HR/H and runs/PA biases.
- 03: workload/fatigue context only if inning/role split shows late-game scoring suppression.
- 05: immediate owner of expanded Monte Carlo measurement output; no production tuning requested yet.
- 00: calibration-target policy only if multi-year vs single-year reference requires a project-level choice.

## NEXT_ACTION
- Highest priority: 05 measurement-only expanded full-game summary. In parallel, 08 should build matched real KBO game-log tail distributions and exact completed-2025 extra-inning frequency.

## RELATED_PRS
- #35 merged

## RELATED_BRANCHES
- main

## GATES
- PUBLIC_DATA_POLICY = PASS
- DATASET_PROVENANCE_MATRIX = PASS
- RECENT_KBO_MULTIYEAR_REFERENCE = PASS
- RUN_ENVIRONMENT_REALISM = FAIL
- HIT_VOLUME_REALISM = PASS
- BB_ENVIRONMENT_REALISM = FAIL
- K_ENVIRONMENT_REALISM = FAIL
- HR_ENVIRONMENT_REALISM = FAIL
- PA_ENVIRONMENT_REALISM = WATCH
- EXTRA_INNING_DRAW_REALISM = WATCH
- WALKOFF_REALISM = WATCH
- BATTING_RATE_STAT_COMPARISON = OPEN
- PITCHING_RATE_STAT_COMPARISON = OPEN
- REAL_GAME_TAIL_DISTRIBUTION = OPEN
- TEAM_PARITY_COMPARISON = OPEN
- OVERALL_KBO_STATISTICAL_REALISM = FAIL_WITH_STRONG_LOCAL_MATCHES
