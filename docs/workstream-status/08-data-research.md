# 08 - Baseball Data & Research

WORKSTREAM: 08 - Baseball Data & Research
UPDATED_AT: 2026-09-10
SOURCE_OF_TRUTH: main@9807004ff1dc00a5bb88bca49bebadd7a87f1f99
STATE: ACTIVE
CURRENT_TASK: KBO roster / age / pitcher workload baseline pack
RESULT: PARTIAL_PASS_OPEN

## LAST_COMPLETED
- Public data provenance/usage policy added under `data/README.md`.
- Detailed KBO dataset provenance matrix added and linked from main.
- Added `docs/kbo-shared-evidence-baseline.md` for common 02/03/04/05 reference data.
- Added `docs/kbo-roster-age-pitcher-workload-baseline.md` with modern position/rookie distribution, age bounds, completed-2025 workload tail anchors, official velocity-system provenance, and longitudinal cohort methodology.

## CURRENT_FINDINGS
- 2026 KBO official registration: 621 players; 317 pitchers (51.05%), 50 catchers (8.05%), 138 infielders (22.22%), 116 outfielders (18.68%). This closes the modern registered-player position-share gap for 02.
- 2026 rookies: 52 players (8.37% of the 621 registered population); 28 pitchers, 14 infielders, 8 outfielders, 2 catchers.
- Official roster-age bounds remain usable: 2026 18y1m19d to 42y1m15d; 2025 18y1m19d to 42y6m16d. Mean/median/percentiles and position-age distributions remain OPEN.
- Completed 2025 player leaderboards provide extreme workload anchors: top GS leaders reached 30-31 starts, with the top-five GS group spanning about 5.46-6.58 IP/start.
- Completed 2025 high-appearance zero-start relievers reached 75-82 games; the top-five appearance group spans about 0.58-1.04 IP/appearance. These are extreme sanity bands, not percentile estimates.
- Full P10/P50/P90/P95 starter/reliever distributions and role IP shares remain OPEN because no redistribution-safe complete player-level `G/GS/IP/BF` aggregate was obtained.
- KBO officially adopted TrackMan as the league pitch-velocity measurement system for 2025, improving measurement provenance. A primary league-wide average/SD/percentile velocity distribution is still not publicly recovered.
- Debut-age/career-length cohort design is now predeclared with player-ID entity matching, active-season and calendar-span definitions, right-censoring, left-truncation controls, and metric-specific peak-age rules.

## BLOCKERS
- KBO annual roster attachments/public pages do not currently provide a compact redistribution-safe age histogram; bulk extraction was deliberately avoided under public-repo policy.
- No complete licensed/reproducible 2025 player-level `G/GS/IP/BF` dataset was available in this pass for percentile calculation.
- KBO public material confirms TrackMan as the official measurement system but does not expose a league-wide velocity distribution suitable for direct aggregation.
- No provenance-safe longitudinal KBO career cohort has yet been materialized.

## OPEN_ITEMS
- Recover roster age mean/median/P10/P25/P75/P90 and position-age splits from an aggregate-permitted source.
- Build completed-2025 starter/reliever P10/P50/P90/P95, role counts, total-IP shares, and BF distributions using the declared role classifier once an appropriate player-level source is available.
- Find a primary or explicitly licensed TrackMan-derived KBO fastball average/SD/percentile source; keep average and maximum velocity separate.
- Materialize the debut-age/career-length longitudinal cohort with censoring metadata.
- Continue explicit-PA/IP low/middle/elite performance percentile research for 02/05.

## DEPENDENCIES
- 02: position and rookie distribution are now usable for registered-player generation comparisons; age bounds usable as plausibility constraints; full age/usage/velocity distributions remain OPEN.
- 03: longitudinal debut-age/career-length/peak-age methodology is ready; numerical career distributions remain OPEN.
- 04: unchanged; award/rule evidence remains usable from shared baseline.
- 05: 2025 league baseline remains usable; new extreme starter/reliever workload sanity bands are usable, but central percentile workload targets remain OPEN.

## NEXT_ACTION
- Highest priority: obtain a redistribution-safe complete 2025 player-level pitching summary to calculate role/workload percentiles; second priority is an aggregate-permitted roster age distribution.

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
- STARTER_RELIEVER_WORKLOAD_PERCENTILES = OPEN
- VELOCITY_MEASUREMENT_PROVENANCE = PASS
- VELOCITY_DISTRIBUTION_BASELINE = OPEN
- CAREER_LONGITUDINAL_METHODOLOGY = PASS
- CAREER_LONGITUDINAL_NUMERICAL_BASELINE = OPEN
- KBO_ROSTER_AGE_WORKLOAD_PACK = PARTIAL_PASS_OPEN
