# 02 - Player Ratings & Generation

WORKSTREAM: 02 - Player Ratings & Generation
UPDATED_AT: 2026-09-10
SOURCE_OF_TRUTH: main@c4bbab3c7b3be6d5e4fe315ac58276bbd8746938
STATE: ACTIVE
CURRENT_TASK: Production rating contract audit completed; next calibration experiment specified
RESULT: OPEN

## LAST_COMPLETED
- Re-audited current production hitter, pitcher, and catcher rating/generation structures against latest main.
- Confirmed talent is generated separately from current ability for hitters and pitchers.
- Confirmed catcher Game Calling schema/generation/save compatibility is in production; CLI label fix from PR #36 is merged.
- Classified historical PR #20-#27 findings as REUSABLE / NEEDS_REVALIDATION / OBSOLETE.
- Defined the bounded next calibration experiment without changing gameplay coefficients or production rating values.

## CURRENT_FINDINGS
- Raw ratings are non-negative integers with no production upper cap; 100 is not a universal population-center contract.
- Hitter PlayerStats generation uses independent stat draws plus a shared cohort offset, position adjustments, and a separate talent mixture. Current ability is a weighted average of non-talent hitter ratings and excludes Game Calling.
- Pitcher generation uses a separate raw schema (Velocity/Stuff/Control/Breaking/Stamina/Resilience), shared offset, archetype adjustments, and separate talent. Pitcher current ability excludes talent.
- Catcher generation reuses Defense/Throwing and adds Game Calling through five catcher archetypes. Game Calling is intentionally outside gameplay probability math at this stage.
- Gameplay engines use mathematical reference 100 internally, while generated starting populations are centered materially below that reference. Therefore raw rating 100 cannot currently be interpreted as a universal hitter/pitcher/catcher percentile or KBO first-team average.
- Hitter and pitcher raw scales are structurally usable but not yet cross-calibrated to a common KBO first-team reference population.
- Current main has no canonical raw Velocity -> physical km/h mapping. Historical Velocity mappings remain calibration references only.
- Position/archetype adjustments create real distribution differences, but full production covariance/tail validation across all positions/archetypes has not yet been rerun on latest main.
- Serialization is backward compatible for hitter/catcher PlayerStats; pitcher serialization is explicit in Pitcher/PitcherStats. CLI exposes Game Calling after merged PR #36; dashboard/presentation still omits Game Calling.

## BLOCKERS
- No current-main KBO first-team reference dataset with sufficiently explicit provenance and sample restrictions has been accepted for the next calibration pass.
- Current-main full population Monte Carlo covering hitter/pitcher/catcher means, SDs, percentiles, covariance, position/archetype splits, and extreme tails has not yet been executed.
- Raw-rating-to-gameplay normalization semantics remain a 01 - Gameplay Engine boundary question and must not be solved by rating-side coefficient tuning.

## OPEN_ITEMS
- Decide, after empirical comparison, whether rating 100 should represent a KBO first-team central reference, a display reference only, or remain a raw latent scale with an explicit gameplay adapter.
- Measure latest-main starting distributions for protagonist/prospect and NPC cohorts by position and archetype.
- Measure CA/Talent independence and identify unrealistic high-high/low-high combinations rather than relying on marginal means alone.
- Revalidate historical Velocity Scale v2 physical mapping against current-main pitcher generation/growth before any production promotion.
- Revalidate Stuff/Control/Breaking recentering and hitter normalization assumptions only after the raw-scale population contract is measured.
- Build a provenance-clean KBO first-team broad-spectrum dataset and real-player inverse-rating validation set.
- Resolve dashboard/presentation Game Calling exposure separately from rating calibration.

## DEPENDENCIES
- 08: provide provenance-clean KBO reference contracts for hitters, pitchers, velocity, catcher proxies, positions, roles, ages, and first-team usage weights.
- 05: execute latest-main rating-generation Monte Carlo and distribution/covariance/tail validation exactly against the experiment contract below.
- 01: answer gameplay-side normalization/interface questions; no gameplay coefficients are to be changed by 02.

## NEXT_ACTION
Run Calibration Experiment R1 on latest main with production ratings frozen. R1 measures the current raw-scale population first; only after R1 + 08 reference data are available should 02 design a candidate recentering/normalization experiment.

R1 contract:
- Source: exact latest-main SHA captured at execution start.
- Populations: hitter prospect/player cohort, hitter high-school NPC cohort, pitcher player cohort, pitcher NPC cohort, catcher subset of both hitter cohorts.
- Positions: all C/1B/2B/3B/SS/LF/CF/RF/DH; pitcher archetypes: power/command/breaking/workhorse/wild_flamethrower/balanced; catcher archetypes: defensive/strong_arm/game_manager/balanced/offensive.
- Sample restrictions: generation-only at START_AGE=18 for baseline; do not mix farm/first-team career survivors into the starting-population report. Any later KBO first-team comparison must be usage-weighted and reported separately.
- Seeds: fixed family 20260910, 20260911, 20260912, 20260913, 20260914; report per-seed and pooled results.
- Monte Carlo size: hitters 200,000 player + 200,000 NPC; pitchers 200,000 player + 200,000 NPC; ensure at least 20,000 catchers and at least 10,000 observations for every pitcher/catcher archetype in pooled samples.
- Metrics: mean, SD, min/max, P1/P5/P10/P25/P50/P75/P90/P95/P99/P99.9 for every raw rating and current ability; 100/120/130/150/170/200+ exceedance rates; complete Pearson correlation matrix; CA-Talent correlation; position/archetype conditional means/SDs/percentiles; top-tail joint combinations.
- Extreme-combination diagnostics: count implausible simultaneous tails such as top-1% speed + bottom-1% durability, top-1% power + top-1% speed, pitcher top-1% Velocity + top-1% Control, and any 170+/200+ multi-rating combinations. These are diagnostics, not automatic failures until 08 baselines exist.
- Parameters under test: no production values are changed in R1. The experiment tests whether current INITIAL_STAT_DISTRIBUTIONS, cohort shared-offset SDs, POSITION_ADJUSTMENTS, pitcher BASE_MEANS/BASE_SDS, pitcher archetype adjustments, catcher archetype deltas/Game Calling generation, and TALENT_MIXTURE produce acceptable shapes.
- Frozen: all gameplay probability coefficients, H3.2.1 hitter formulas, pitcher outcome coefficients, growth/aging, draft formulas, fatigue/role effects, save schema, UI.
- Provisional structural gates before real-data matching: deterministic seed reproducibility PASS; no invalid negative values PASS; no perfect/near-perfect |r| >= 0.95 collapse between distinct raw skills; every declared archetype materially represented; report any >=200 generated value and any >=170 frequency instead of silently clipping; Talent-CA |r| < 0.35 target unless evidence justifies stronger dependence.
- Real-data fit gates after 08 dataset lands: compare KBO first-team central tendency, SD, P10/P50/P90/P95/P99 and role/position splits; use usage-weighted distributions and Wasserstein/quantile errors rather than mean alone. Numeric tolerances remain OPEN until 08 establishes source/sample uncertainty.
- Expected reports: rating_r1_summary.md, rating_r1_hitter_distribution.csv, rating_r1_pitcher_distribution.csv, rating_r1_catcher_distribution.csv, rating_r1_covariance.csv, rating_r1_position_archetype.csv, rating_r1_extreme_tails.csv, rating_r1_seed_stability.json.

Historical classification:
- REUSABLE: physical-velocity-layer concept; separation of Velocity physical calibration from S/C/B gameplay calibration; usage-weighted KBO first-team population concept; broad-spectrum quantile/tail validation; multi-metric real-player inverse-rating methodology; requirement to preserve provenance and low/middle/high player spectrum.
- NEEDS_REVALIDATION: Velocity Scale v2 numeric mapping and raw reference point; physical km/h slope/compression; S/C/B recenter target; hitter raw->gameplay normalization candidate; prime-pitcher center target; KBO first-team generated-spectrum alignment; inverse real-player inferred rating values; broad-spectrum numerical gates.
- OBSOLETE: Velocity v1 mapping from PR #20; any NOT_READY S/C/B gameplay coefficients; any assumption that historical draft/open branches are production-ready; any direct reuse of old inferred-rating CSV values without provenance re-check; any assumption that raw rating 100 already equals KBO average or that hitter/pitcher 100 have matched percentiles.

08 data request contract:
- Hitters: one recent complete KBO season, first-team player-season rows with PA, age, primary/played position, AVG/OBP/SLG, BB%, K%, HR%, BABIP, SB/CS where available; provide PA>=100 primary and PA>=300 robustness subsets.
- Pitchers: same season, BF/IP/G/GS, role classification, K%, BB%, HR%, opponent AVG/SLG, BABIP if available; BF>=100 primary and BF>=300 robustness subsets.
- Velocity: measured average fastball km/h per pitcher with measurement provider, minimum sample criterion, starter/reliever split, and same-pitcher role split where possible; average and max velocity must remain separate fields.
- Catcher: catcher innings/games plus public defensive proxies such as CS/attempt, passed-ball/wild-pitch context, framing or receiving proxy when redistribution permits; clearly label unavailable metrics.
- Population context: KBO first-team age distribution, position usage distribution, roster/usage denominator, rookie/debut-age references.
- Provenance: source/provider, season, access date, row-level or table-level source identifier, sample restriction, missingness notes, redistribution constraints.

05 validation request contract:
- Execute R1 without tuning production parameters.
- Report pooled and all five seed-family results; flag seed instability if any key mean/SD/quantile moves by more than 0.5 raw rating or tail-rate relative variation exceeds 20% for events with at least 100 pooled occurrences.
- Explicit PASS/FAIL/OPEN for reproducibility, distribution width, covariance collapse, archetype diversity, position separation, Talent/CA separation, 170+/200+ extreme tails, and catcher Game Calling distribution.
- Do not translate ratings into gameplay outcomes and do not recommend gameplay coefficient changes.

## RELATED_PRS
- #20 Velocity v1 calibration: reference only; final gate NOT_READY; numeric mapping obsolete.
- #22 Velocity Scale v2: reference only; methodology reusable, numeric mapping requires revalidation.
- #23 Pitcher physical safety + joint S/C/B diagnostics: reference only; searched gameplay coefficients not reusable.
- #24 Hitter normalization diagnostics: reference only; candidate requires revalidation.
- #25 KBO first-team population + inverse-rating calibration: methodology reusable; inferred values require revalidation.
- #27 Broad player spectrum calibration: methodology reusable; gates remained NOT_READY.
- #30 Catcher foundation: production content now integrated through later main consolidation.
- #33 Production integration consolidation: merged; catcher foundation is production.
- #36 CLI Game Calling label fix: merged.

## RELATED_BRANCHES
- main
- Historical feature/velocity-scale-calibration, feature/velocity-scale-v2-calibration, feature/pitcher-joint-calibration-v2, feature/hitter-gameplay-normalization, feature/kbo-first-team-rating-inference, feature/kbo-broad-player-spectrum are reference-only.

## GATES
- PRODUCTION_RATING_CONTRACT_AUDITED = PASS
- RAW_100_UNIVERSAL_SEMANTICS = OPEN
- HITTER_PITCHER_SCALE_COMPARABILITY = OPEN
- CATCHER_SCHEMA_GENERATION = PASS
- RATING_SERIALIZATION = PASS
- RATING_UI_EXPOSURE = OPEN
- HISTORICAL_CALIBRATION_CLASSIFIED = PASS
- NEXT_CALIBRATION_EXPERIMENT_DEFINED = PASS
- KBO_REFERENCE_DATA_READY = OPEN
- CURRENT_MAIN_R1_MONTE_CARLO = NOT_RUN
- PRODUCTION_RECENTER_OR_NORMALIZATION_READY = OPEN
