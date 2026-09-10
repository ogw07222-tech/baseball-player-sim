# 02 - Player Ratings & Generation

WORKSTREAM: 02 - Player Ratings & Generation
UPDATED_AT: 2026-09-10
SOURCE_OF_TRUTH: main@f19bf424c910bfa66bf05cc20d20a930f27f8c88
STATE: ACTIVE
CURRENT_TASK: Rating Generation R1 Monte Carlo completed and verified; R1V/reference alignment next
RESULT: OPEN

## LAST_COMPLETED
- Executed Rating Generation R1 from production-equivalent generation code at execution source `main@9aa458735721570581f4968060590acf3fc9c957`.
- Verified through latest pre-status-update main `f19bf424c910bfa66bf05cc20d20a930f27f8c88` that all intervening changes after R1 publication do not modify rating/generation implementation or the R1 reports.
- Measured 200k hitter player, 200k hitter NPC, 200k pitcher player, and 200k pitcher NPC generation-only samples across seeds 20260910-20260914.
- Added dedicated 50k player + 50k NPC catcher diagnostics; every catcher archetype has >10k pooled observations.
- Published all eight expected R1 reports under `reports/rating_r1_*`.
- No production rating, gameplay, growth, aging, draft, fatigue, UI, or save-schema value was changed.

## CURRENT_FINDINGS
- Hitter player CA mean/SD = 79.7395 / 9.8163; hitter NPC = 69.7347 / 6.9449.
- Pitcher player CA mean/SD = 79.4899 / 8.8808; pitcher NPC = 69.9888 / 6.1765.
- Player CA >=100 differs by system: hitter 1.955%, pitcher 1.075%; raw 100 is not a matched cross-system percentile.
- CA-Talent correlations are effectively zero in all four main cohorts (absolute r <= 0.003), passing the provisional |r| < 0.35 target.
- Maximum distinct raw-skill correlation remains well below collapse threshold: hitter player ~0.260; pitcher player ~0.430; no |r| >= 0.95 collapse.
- Position adjustments materially separate hitter profiles; pitcher and catcher archetypes are materially represented and distinct.
- Dedicated catcher player Game Calling mean/SD = 85.70 / 15.21; P10/P50/P90/P99 = 66/86/105/121; max 151. Catcher NPC mean/SD = 82.72 / 15.08.
- Non-talent >=170 values are extremely rare at age 18: 10 hitter-player observations total; none in hitter NPC or pitcher cohorts. No non-talent raw skill reached 200.
- No evaluated diagnostic player had two separate raw skills >=150 simultaneously.
- Strict seed-stability rule remains FAIL: 53/62 population-rating rows exceed the literal 0.5-point range criterion, driven mainly by integer quantile movement rather than unstable means/SDs.
- KBO comparison is only partial: 08 has roster composition, age bounds, workload extreme bands, and TrackMan measurement provenance, but player-level broad spectra and primary velocity distribution remain incomplete.

## BLOCKERS
- 05 independent rerun from an actual latest-main checkout is still needed because the original R1 compute used a source-equivalent local harness reconstructed from connector-fetched production modules/constants.
- The absolute 0.5-point seed-quantile stability rule requires validation-method review before it can be treated as a generator-quality gate.
- Provenance-clean KBO player-level hitter/pitcher broad-spectrum datasets with requested PA/BF restrictions are incomplete.
- Primary/licensed KBO league fastball mean/SD/percentile distribution remains OPEN.
- Catcher receiving/framing/game-management observational proxies remain incomplete.
- Rating-to-gameplay normalization remains a 01 boundary and was not touched.

## OPEN_ITEMS
- Have 05 reproduce R1 directly from production modules in Codespaces and compare report-level metrics.
- Replace or justify the strict absolute seed-stability tolerance using Monte Carlo SE / quantile confidence intervals.
- Complete KBO broad-spectrum reference sets before any R2 recentering.
- Revalidate Velocity Scale v2 physical mapping only after primary/licensed velocity distribution is available.
- Keep hitter normalization and Stuff/Control/Breaking recentering frozen until raw-scale/reference contract validation is complete.

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
