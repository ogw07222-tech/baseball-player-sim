# 05 - Balance Lab

WORKSTREAM: 05 - Balance Lab
UPDATED_AT: 2026-09-10
SOURCE_OF_TRUTH: main@e0ee4e9a12d8bc806c30dcdd58ea2acb88029932
STATE: BLOCKED
CURRENT_TASK: Heavy Production Sanity Gate completion
RESULT: OPEN

## LAST_COMPLETED
- Production implementation regression evidence remains green: 253/253 Python unit tests PASS, Auto career smoke PASS, Balance smoke PASS, natural-event 100k sanity PASS, catcher unit-generation gates PASS, and web tests/build PASS on the unchanged production implementation lineage after PR #33/#36.
- Current main `e0ee4e9a12d8bc806c30dcdd58ea2acb88029932` was re-checked before/after heavy work. Compared with `9aa458735721570581f4968060590acf3fc9c957`, changes are documentation and web presentation only; no `src/`, `tests/`, or `tools/` gameplay-validation code changed.
- Heavy pitcher-usage logic was reconstructed locally from the exact main source and executed with seed `20260906`, 500 seasons × 144 games. Core result: avg starter IP/start 5.8677; mean role switches/team-season 8.792; unavailable-use violations 0; mean bullpen-exhaustion events 0.002/season.
- Validation-only extended pitcher aggregation over the same 500 seasons found starter-IP/start season-average median 5.8773, SD 0.1800, P90 6.0972, P95 6.1667, P99 6.2477, min 5.1968, max 6.4074. Relief appearances/pitcher-season mean 39.318, median 34, SD 31.761, P90 82, P95 101, P99 109, max 116. 4-day-use events occurred in 35/500 seasons; bullpen exhaustion occurred in 1/500 seasons; unavailable-use violation seasons 0/500.
- Heavy catcher-generation logic was reconstructed locally from the exact main generation/config/catcher source and executed with seed `20260906`, 200,000 catcher samples. Defense mean 83.032, SD 17.328, P10/50/90/95/99 = 61/83/105/111/123, min/max 1/162, 170+ = 0. Throwing mean 92.466, SD 18.312, P10/50/90/95/99 = 69/92/116/123/135, min/max 16/174, 170+ = 3, 200+ = 0. Game Calling mean 85.707, SD 15.200, P10/50/90/95/99 = 66/86/105/111/121, min/max 13/157, 170+/200+ = 0. Invalid values = 0.
- Catcher archetype share: defensive 21.99%, strong_arm 17.87%, game_manager 19.99%, balanced 25.05%, offensive 15.10%. Correlations: defense-throwing 0.204, defense-game_calling 0.271, throwing-game_calling 0.173; no covariance collapse detected.

## CURRENT_FINDINGS
- `PR33_UNIT_REGRESSION = PASS` remains supported.
- Pitcher workload/rotation heavy evidence shows no unavailable-use invariant violations and very rare bullpen exhaustion. Distribution tails are broad, not collapsed. However relief-appearance tails are wide (P95 101, P99 109, max 116 appearances/pitcher-season); this is a balance observation, not a tuning action or automatic FAIL without a matched real-KBO baseline.
- Catcher heavy distribution is healthy under current structural guards: no invalid/negative values, no 200+ values, essentially no 170+ tail except 3 throwing samples in 200k, expected archetype proportions, and weak-to-moderate inter-rating correlations rather than identity/collapse.
- The required canonical `production_game_provider_sanity.py --games 10000` command could not be executed in this chat's local sandbox because `github.com` DNS resolution is blocked and the full repository dependency graph cannot be obtained through local git. GitHub Actions was intentionally not used as a heavy-compute workaround.
- Because the mandatory 10,000-game full-game provider run is still missing, `PRODUCTION_SANITY` and `PRODUCTION_READINESS` cannot be honestly closed to PASS.

## BLOCKERS
- Canonical 10,000-game full-game provider heavy run is not executed on a real current-main checkout.
- The locally reconstructed pitcher/catcher runs are strong validation evidence but are not a substitute for executing the repository commands verbatim in a full checkout/Codespaces environment.

## OPEN_ITEMS
- In Codespaces/local current-main checkout, execute: `python tools/production_game_provider_sanity.py --games 10000 --seed 20260906 --output reports/integration-local/full-game.json`.
- Re-run the canonical `python tools/pitcher_usage_sanity.py --seasons 500 --seed 20260906` and `python tools/catcher_generation_sanity.py --samples 200000 --seed 20260906` in the same checkout to confirm equivalence with the reconstructed local results.
- For full-game output, record completion rate, cap/safety hits, runs/game, innings, PA/game, score/state/counting violations, deterministic replay, and requested P10/P50/P90/P95/P99/min/max/tail summaries.
- If full-game canonical run is clean and reconstructed-vs-canonical pitcher/catcher results match, close `PRODUCTION_SANITY` and `PRODUCTION_READINESS` to PASS; otherwise route the defect by owner without tuning here.

## DEPENDENCIES
- 07: if the full-game command fails due runtime/integration/tooling rather than simulation behavior.
- 01: if the 10k full-game run exposes gameplay/state/counting defects.
- 02: only if canonical catcher generation diverges or distribution guards fail.
- 08: for matched KBO interpretation of workload tails such as 100+ relief appearances.

## NEXT_ACTION
- Run the three canonical heavy commands verbatim in Codespaces/local on current main, prioritizing the still-missing 10k full-game provider run; compare pitcher/catcher outputs to the reconstructed evidence above and then close the gate.

## RELATED_PRS
- #33 merged
- #36 merged

## RELATED_BRANCHES
- main

## GATES
- PR33_UNIT_REGRESSION = PASS
- PRODUCTION_SANITY = OPEN
- PRODUCTION_READINESS = OPEN
