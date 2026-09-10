# 05 - Balance Lab

WORKSTREAM: 05 - Balance Lab
UPDATED_AT: 2026-09-10
SOURCE_OF_TRUTH: main@0ad44e02ce401f772c778a792f595fecee58c7f6
STATE: BLOCKED
CURRENT_TASK: Close Production Sanity Gate with canonical 10k full-game run
RESULT: OPEN

## LAST_COMPLETED
- Latest main was re-checked at task start as `0ad44e02ce401f772c778a792f595fecee58c7f6`.
- Production implementation regression evidence remains green: 253/253 Python unit tests PASS, Auto career smoke PASS, Balance smoke PASS, natural-event 100k sanity PASS, catcher unit-generation gates PASS, and web tests/build PASS on the production implementation lineage after PR #33/#36.
- Previous heavy pitcher-usage validation remains usable because subsequent changes do not alter the production simulation implementation: seed `20260906`, 500 seasons × 144 games; starter IP/start mean 5.8677, median 5.8773, SD 0.1800, P90 6.0972, P95 6.1667, P99 6.2477, min 5.1968, max 6.4074; role switches/team-season mean 8.792; unavailable-use violations 0; bullpen exhaustion 1/500 seasons; relief appearances/pitcher-season mean 39.318, median 34, SD 31.761, P90 82, P95 101, P99 109, max 116.
- Previous heavy catcher-generation validation remains usable: seed `20260906`, 200,000 samples; Defense mean/SD 83.032/17.328, Throwing 92.466/18.312, Game Calling 85.707/15.200; 200+ tails 0 across all three ratings, Throwing 170+ = 3/200k, invalid values = 0; archetype proportions matched configuration and covariance did not collapse.

## CURRENT_FINDINGS
- `PR33_UNIT_REGRESSION = PASS` remains supported.
- The mandatory canonical full-game heavy command is still not executable from this ChatGPT runtime because the available GitHub connector exposes repository inspection/write APIs but no Codespaces command-execution action, while the local execution sandbox cannot obtain a complete GitHub checkout via `git clone`/raw download due network/DNS restrictions.
- No committed `reports/integration-local/full-game.json` matching the required 10,000-game seed-20260906 run was found on latest main.
- Because the canonical 10,000-game run has not actually executed in a complete current-main checkout, completion rate, cap-hit count, full-game percentile/tail distributions, deterministic replay, and impossible-state/counting-violation counts cannot be claimed as measured evidence here.
- GitHub Actions was not used as heavy compute, per workstream policy.

## BLOCKERS
- No tool available in this chat can execute shell commands inside the user's Codespace or local machine.
- Local sandbox GitHub network access is unavailable, preventing reconstruction of a trustworthy complete repository checkout for the canonical full-game command.

## OPEN_ITEMS
- In an actual current-main Codespaces/local checkout, run exactly: `python tools/production_game_provider_sanity.py --games 10000 --seed 20260906 --output reports/integration-local/full-game.json`.
- Record completion rate, runs/game distribution, innings/game distribution, PA/game distribution, P10/P50/P90/P95/P99, min/max, cap/safety hits, impossible state/counting violations, deterministic replay result, and extreme-tail frequencies.
- If completion = 100%, cap hits = 0, invariant violations = 0, deterministic replay = PASS, and no obvious distribution collapse is found, close `PRODUCTION_SANITY = PASS` and `PRODUCTION_READINESS = PASS`.
- If a defect appears, route without tuning: 01 gameplay/state/counting, 02 ratings/generation, 03 growth/career, 07 runtime/integration, 08 baseline/data.

## DEPENDENCIES
- 01: gameplay/state/counting defect from canonical 10k full-game run.
- 02: rating/generation defect if discovered in reruns.
- 03: growth/career only if a career-layer failure is exposed.
- 07: runtime/integration/tooling defect or report plumbing.
- 08: empirical run-environment/workload baseline interpretation.

## NEXT_ACTION
- Execute the canonical 10,000-game full-game sanity command in a real current-main Codespaces/local checkout and return the generated JSON (or paste its output) for final Balance Lab percentile/tail analysis and gate closure.

## RELATED_PRS
- #33 merged
- #36 merged

## RELATED_BRANCHES
- main

## GATES
- PR33_UNIT_REGRESSION = PASS
- PRODUCTION_SANITY = OPEN
- PRODUCTION_READINESS = OPEN
