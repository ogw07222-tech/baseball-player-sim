# 08 - Baseball Data & Research

WORKSTREAM: 08 - Baseball Data & Research
UPDATED_AT: 2026-09-10
SOURCE_OF_TRUTH: main@c277df00a191575214009b93311d5b54c633d5c3
STATE: ACTIVE
CURRENT_TASK: KBO roster / age / pitcher workload baseline pack — second-pass verification
RESULT: PARTIAL_PASS_OPEN

## LAST_COMPLETED
- Public data provenance/usage policy and detailed dataset provenance matrix remain in place.
- `docs/kbo-shared-evidence-baseline.md` provides common 02/03/04/05 references.
- `docs/kbo-roster-age-pitcher-workload-baseline.md` established the first focused roster/workload pack.
- Added `docs/kbo-roster-age-pitcher-workload-baseline-pass2.md` with second-pass source verification and BF-exposure heavy-sanity bands.

## CURRENT_FINDINGS
- 2026 KBO official registered-player population remains 621: 317 pitchers (51.05%), 50 catchers (8.05%), 138 infielders (22.22%), 116 outfielders (18.68%).
- 2026 rookies remain 52 (8.37% of registered population): 28 P, 14 IF, 8 OF, 2 C.
- Official age bounds remain usable: 2026 18y1m19d–42y1m15d; 2025 18y1m19d–42y6m16d. Mean/median/percentiles and position-age splits remain OPEN.
- Completed-2025 high-GS starter tail remains 30–31 GS and 5.46–6.58 IP/start; second pass adds 23.13–26.20 BF/start for the observed top-five GS group.
- Completed-2025 zero-start reliever extreme tail remains 75–82 G and 0.58–1.04 IP/app; second pass adds 2.48–4.16 BF/app for the observed top-five appearance group.
- KBO official public tables expose G/IP/TBF and detailed pitching fields, but GS is not consistently exposed in the same rendered public table. Full role percentiles therefore still require a complete secondary/licensed GS-bearing source or game-log reconstruction.
- Full P10/P50/P90/P95 starter/reliever workload distributions, role counts, and starter/bullpen IP shares remain OPEN; no percentile was inferred from leaderboard snippets.
- KBO officially adopted TrackMan as the official pitch-velocity measurement system from 2025. Average velocity and maximum velocity are explicitly treated as separate measures; no primary league-wide mean/SD/percentile distribution was recovered.
- Debut-age/career-length methodology remains fixed: stable player ID, first KBO regular-season appearance, calendar-span plus active-season measures, right-censoring, left-truncation controls, Kaplan–Meier when appropriate, and predeclared peak metric/PA-IP minimum.

## BLOCKERS
- No aggregate-permitted modern KBO age histogram/central tendency source was recovered.
- No complete redistribution-safe/licensed 2025 player-level G/GS/IP/BF universe was recovered for central percentile calculation.
- No primary/licensed league-wide TrackMan fastball distribution was recovered.
- No provenance-safe longitudinal numerical KBO career cohort has yet been materialized.

## OPEN_ITEMS
- Recover roster age mean/median/P10/P25/P75/P90, position-age splits, and young-player shares from an aggregate-permitted source.
- Obtain or reconstruct a complete 2025 G/GS/IP/BF pitcher universe and calculate role counts, IP shares, BF shares, and P10/P50/P90/P95 under the declared project classifier with sensitivity checks.
- Find a primary or explicitly licensed TrackMan-derived league fastball mean/SD/percentile source; keep average and maximum velocity separate.
- Materialize debut-age/career-length cohorts with censoring metadata.

## DEPENDENCIES
- 02: registered-player position and rookie distributions are PASS and usable for R1 comparison; age central distribution remains OPEN.
- 03: longitudinal cohort/censoring methodology is PASS; numerical lifecycle distributions remain OPEN.
- 04: unchanged; award/rule evidence from shared baseline remains usable.
- 05: completed-2025 extreme workload sanity bands now include both IP and BF exposure; central role percentiles remain OPEN.

## NEXT_ACTION
- Highest priority: complete 2025 pitcher universe with G/GS/IP/BF for percentile and role-share aggregation. Second: aggregate-permitted modern roster age distribution. Third: primary/licensed TrackMan velocity distribution.

## RELATED_PRS
- #35 merged

## RELATED_BRANCHES
- main

## GATES
- PUBLIC_DATA_POLICY = PASS
- DATASET_PROVENANCE_MATRIX = PASS
- 2025_MATCHED_LEAGUE_BASELINE = PASS
- ROSTER_POSITION_DISTRIBUTION_BASELINE = PASS
- ROSTER_ROOKIE_SHARE_BASELINE = PASS
- ROSTER_AGE_BOUNDS = PASS
- ROSTER_AGE_DISTRIBUTION = OPEN
- STARTER_RELIEVER_EXTREME_WORKLOAD_SANITY = PASS
- STARTER_RELIEVER_BF_EXPOSURE_SANITY = PASS
- STARTER_RELIEVER_WORKLOAD_PERCENTILES = OPEN
- VELOCITY_MEASUREMENT_PROVENANCE = PASS
- VELOCITY_AVERAGE_MAX_SEPARATION = PASS
- VELOCITY_DISTRIBUTION_BASELINE = OPEN
- CAREER_LONGITUDINAL_METHODOLOGY = PASS
- CAREER_LONGITUDINAL_NUMERICAL_BASELINE = OPEN
- KBO_ROSTER_AGE_WORKLOAD_PACK = PARTIAL_PASS_OPEN
