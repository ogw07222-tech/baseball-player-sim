# 02 - Player Ratings & Generation

WORKSTREAM: 02 - Player Ratings & Generation
UPDATED_AT: 2026-09-10
SOURCE_OF_TRUTH: main@9807004ff1dc00a5bb88bca49bebadd7a87f1f99
STATE: ACTIVE
CURRENT_TASK: Rating Generation R1 Monte Carlo executed; independent validation/reference alignment next
RESULT: OPEN

## LAST_COMPLETED
- Executed Rating Generation R1 against the rating/generation contract unchanged from execution source `main@9aa458735721570581f4968060590acf3fc9c957`; verified through `main@9807004ff1dc00a5bb88bca49bebadd7a87f1f99` that intervening changes did not touch rating/generation implementation.
- Measured 200k hitter player, 200k hitter NPC, 200k pitcher player, and 200k pitcher NPC generation-only samples across seeds 20260910-20260914.
- Added dedicated 50k player + 50k NPC catcher diagnostics so every catcher archetype has >10k pooled observations.
- Published all eight R1 expected reports under `reports/rating_r1_*`.
- No production rating, gameplay, growth, aging, draft, fatigue, UI, or save-schema value was changed.

## CURRENT_FINDINGS
- Hitter player CA mean/SD = 79.7395 / 9.8163; hitter NPC = 69.7347 / 6.9449.
- Pitcher player CA mean/SD = 79.4899 / 8.8808; pitcher NPC = 69.9888 / 6.1765.
- Player CA >=100 differs by system: hitter 1.96%, pitcher 1.07%. Raw 100 is therefore not a matched cross-system percentile.
- CA-Talent correlations are effectively zero in all four main cohorts (absolute r <= 0.003), strongly passing the provisional |r| < 0.35 separation target.
- Maximum distinct raw-skill correlation is well below collapse threshold: hitter player ~0.260; pitcher player ~0.430. No |r| >= 0.95 collapse exists.
- Position adjustments materially separate hitter profiles; all six pitcher archetypes and all five catcher archetypes are materially represented and distinct.
- Dedicated catcher player Game Calling: mean 85.70, SD 15.21, P10/P50/P90/P99 = 66/86/105/121, max 151. Catcher NPC mean 82.72, SD 15.08.
- Non-talent >=170 values are extremely rare at age 18: 10 hitter-player observations total across Speed/Throwing/Durability; none in hitter NPC or pitcher cohorts. No non-talent raw skill reached 200.
- No evaluated hitter/pitcher/catcher diagnostic player had two separate raw skills >=150 simultaneously.
- The literal existing seed-stability rule is too strict for observed discrete quantiles: 53/62 population-rating rows are flagged because at least one per-seed mean/SD/P10/P50/P90/P99 range exceeds 0.5. Main-cohort means and SDs are stable, while integer quantiles move by 1-3 points. Under the authoritative rule the seed-stability gate is FAIL pending independent 05 review.
- Cross-system CA centers near 80/70 are encouraging, but per-stat centers, widths, and the percentile meaning of raw 100 remain non-universal.
- 08 provides a usable 2026 registered-position baseline and age bounds plus workload extreme bands; direct raw-scale KBO alignment remains blocked by player-level broad spectra and primary velocity distribution gaps.

## BLOCKERS
- 05 independent rerun from an actual latest-main checkout is needed because this session's local environment could not network-clone GitHub; R1 compute used a source-equivalent harness transcribed from connector-fetched production modules/constants.
- The current absolute 0.5-point seed-quantile stability rule fails heavily and needs validation-method review before it can be used as a generator-quality criterion.
- No provenance-clean full KBO player-level hitter/pitcher broad-spectrum dataset with the requested usage restrictions is yet available.
- Primary/licensed 2025 TrackMan-derived league fastball mean/SD/percentile distribution remains OPEN.
- Catcher receiving/framing/game-management observational proxies remain incomplete.
- Rating-to-gameplay normalization remains a 01 boundary and was not touched.

## OPEN_ITEMS
- Have 05 reproduce R1 directly from production modules in Codespaces and compare report-level metrics.
- Determine whether seed-stability tolerance should use confidence intervals/Monte Carlo SE instead of absolute integer-quantile movement.
- Compare R1 position generation with 08's roster-position baseline only as context; do not force equal-position generator diagnostics to match roster shares.
- Build player-level KBO broad-spectrum reference sets before any R2 recentering.
- Revalidate Velocity Scale v2 physical mapping only after a primary/licensed KBO velocity distribution is available.
- Keep hitter normalization and S/C/B recentering frozen until the raw scale/reference contract is validated.

## DEPENDENCIES
- 05: independent R1 reproduction/validation from actual checkout; review seed-stability criterion; no tuning.
- 08: player-level hitter/pitcher broad spectra, first-team position usage, primary velocity distribution, catcher defensive/receiving proxies, fuller age distribution.
- 01: raw-rating -> gameplay normalization/interface questions only; no gameplay coefficients changed by 02.

## NEXT_ACTION
Run `R1V - Independent Validation / Reference Alignment`: 05 reproduces R1 from latest-main production modules, 08 fills remaining KBO reference gaps, then 02 defines R2 candidate scale alignment. Do not change production ratings before R1V is complete.

## RELATED_PRS
- #20-#27 remain experimental/reference only.
- #33 merged production integration/catcher foundation.
- #36 merged CLI Game Calling exposure fix.

## RELATED_BRANCHES
- main
- Historical calibration branches remain reference-only.

## GATES
- PRODUCTION_RATING_CONTRACT_AUDITED = PASS
- R1_MONTE_CARLO_EXECUTED = PASS
- R1_REPRODUCIBILITY_SPOT_CHECK = PASS
- R1_NONNEGATIVE_GENERATION = PASS
- R1_COVARIANCE_COLLAPSE = PASS
- R1_TALENT_CA_SEPARATION = PASS
- R1_POSITION_ARCHETYPE_SEPARATION = PASS
- R1_CATCHER_GAME_CALLING_STRUCTURE = PASS
- R1_GROSS_EXTREME_PILEUP = PASS
- R1_SEED_STABILITY_STRICT = FAIL
- R1_DISTRIBUTION_WIDTH_REALISM = OPEN
- R1_EXTREME_TAIL_REALISM = OPEN
- RAW_100_UNIVERSAL_SEMANTICS = OPEN
- HITTER_PITCHER_SCALE_COMPARABILITY = OPEN
- KBO_REFERENCE_DATA_READY = OPEN
- KBO_RAW_SCALE_ALIGNMENT_READY = OPEN
- PRODUCTION_RECENTER_OR_NORMALIZATION_READY = OPEN
