# Rating Generation R1 Monte Carlo Summary

Execution source: `main@9aa458735721570581f4968060590acf3fc9c957`

Before publication, `main` advanced to `9807004ff1dc00a5bb88bca49bebadd7a87f1f99`; comparison showed only documentation/status changes and no rating/generation implementation change. R1 therefore remains valid for that later HEAD.

## Scope

R1 is generation measurement only. No production rating, gameplay coefficient, H3.2.1 constant, pitcher outcome coefficient, growth, aging, draft, fatigue, UI, or save-schema value was changed.

The local environment could not network-clone GitHub. Compute therefore used a source-equivalent local harness transcribed directly from connector-fetched execution-HEAD `src/rng.py`, `src/stats.py`, `src/config.py`, `src/catcher.py`, `src/pitching/model.py`, and `src/pitching/parameters.py`. It preserved Python `random.Random`, weighted-choice ordering, Gaussian draws, truncation/rounding, shared offsets, position adjustments, talent mixture, archetypes, and current-ability formulas. A repeated-seed 5,000-row spot check for representative hitter/pitcher player/NPC cohorts reproduced exactly.

Baseline hitters were allocated equally/cyclically across all nine supported positions because production defines no population-level position sampling weights. The pooled hitter result is therefore an equal-position generator diagnostic, not a KBO roster-share estimate. Dedicated catcher-only subsets were generated separately and are not mixed into the 200k hitter pools.

## Samples

- hitter player/prospect: 200,000
- hitter NPC: 200,000
- pitcher player: 200,000
- pitcher NPC: 200,000
- dedicated catcher player diagnostic: 50,000
- dedicated catcher NPC diagnostic: 50,000
- seeds: 20260910, 20260911, 20260912, 20260913, 20260914
- baseline: START_AGE=18 generation-only

## Central distributions

| Population | CA mean | SD | P10 | P50 | P90 | P99 | CA >=100 |
|---|---:|---:|---:|---:|---:|---:|---:|
| hitter player | 79.740 | 9.816 | 67.16 | 79.74 | 92.32 | 102.61 | 1.955% |
| hitter NPC | 69.735 | 6.945 | 60.85 | 69.72 | 78.66 | 85.86 | 0.001% |
| pitcher player | 79.490 | 8.881 | 68.10 | 79.49 | 90.85 | 100.20 | 1.075% |
| pitcher NPC | 69.989 | 6.176 | 62.07 | 69.98 | 77.91 | 84.36 | 0% |

Player/NPC CA centers line up surprisingly closely between hitter and pitcher systems, but rating 100 is not a matched percentile: player CA >=100 is 1.955% for hitters versus 1.075% for pitchers. Universal raw-100 semantics remain OPEN.

## Talent separation

CA-Talent Pearson r:
- hitter player -0.0009
- hitter NPC -0.0021
- pitcher player -0.0027
- pitcher NPC +0.0014

All are effectively zero and pass the provisional `|r| < 0.35` target. Talent itself has a deliberate long mixture tail (player hitter P99 173, max 303; pitcher player P99 174, max 310) and must not be interpreted as current performance.

## Covariance

Maximum distinct raw-skill absolute correlations:
- hitter player: 0.260 (Speed-Defense)
- hitter NPC: 0.152 (Speed-Defense)
- pitcher player: 0.430 (Velocity-Stuff)
- pitcher NPC: 0.280 (Velocity-Stuff)

No distinct raw pair approaches the `|r| >= 0.95` collapse threshold. Covariance-collapse gate: PASS.

## Position/archetype variation

Position adjustments materially separate hitter profiles. Examples in player cohort: 1B Power 85.0 / Speed 73.2; SS Power 70.1 / Speed 93.1 / Defense 89.8; CF Speed 94.9; DH Power 85.2 / Defense 65.0.

Pitcher archetypes are materially distinct. Player means include Power Velocity 90.0 / Stuff 85.1 / Control 69.1; Command Control 89.1; Breaking Breaking 90.1; Wild Flamethrower Velocity 94.1 / Control 63.1; Workhorse Stamina 95.3 / Resilience 92.2.

All six pitcher archetypes are well represented. Dedicated catcher pooled player+NPC counts also exceed 10k for every archetype: balanced 24,807; defensive 22,009; game_manager 20,075; strong_arm 18,101; offensive 15,008.

## Catcher Game Calling

Dedicated catcher player: mean 85.700, SD 15.205, P10/P50/P90/P99 66/86/105/121, max 151. Dedicated catcher NPC: mean 82.722, SD 15.084, P99 118, max 146. Game Calling remains a distinct non-collapsed dimension. Structural gate PASS; real-world calibration remains OPEN.

## Extreme tails

Non-talent raw >=170 counts in main 200k cohorts: hitter player 10 total (Speed 4, Throwing 2, Durability 4); hitter NPC 0; pitcher player 0; pitcher NPC 0. No non-talent raw skill reached 200. No evaluated hitter/pitcher/catcher diagnostic player had two separate evaluated skills >=150 simultaneously.

Selected joint-tail rates: hitter player top-1% Power + top-1% Speed 0.0210%; hitter player top-1% Speed + bottom-1% Durability 0.0040%; pitcher player top-1% Velocity + top-1% Control 0.0160%; pitcher player top-1% Velocity + top-1% Stuff 0.1325%.

Gross elite multi-rating pile-up: PASS. Realism of 150/170 tails versus actual KBO: OPEN.

## Seed stability

The authoritative R1 rule flags a population/rating row if any per-seed mean, SD, P10, P50, P90, or P99 range exceeds 0.5 raw rating. Under that literal rule, 53/62 population-rating rows are flagged. Main 40k-per-seed hitter/pitcher cohort means and SDs are stable, but integer-valued quantiles commonly move by 1-3 points. Dedicated catcher 10k-per-seed diagnostics are noisier, especially Talent-tail quantiles.

Therefore `R1_SEED_STABILITY_STRICT = FAIL`. This is not grounds for production tuning; it is a validation-method issue for 05 to review with Monte Carlo uncertainty/confidence intervals.

## KBO comparison readiness

08 currently provides a completed-2025 league outcome baseline and a 2026 registered-player position baseline: 621 registered players, Pitcher 51.05%, Catcher 8.05%, Infielder 22.22%, Outfielder 18.68%; plus roster age bounds and pitcher workload extreme bands. TrackMan is confirmed as the official KBO velocity measurement system from 2025.

These references are contextual only for R1. START_AGE=18 raw generation cannot be directly compared with league AVG/OBP/SLG/K/BB without crossing into gameplay calibration. Still OPEN: player-level broad hitter/pitcher spectra under explicit PA/BF restrictions, first-team playing-time position spectrum, primary/licensed league fastball mean/SD/percentiles, catcher receiving/framing/game-management proxies, and full age percentiles.

## Structural gates

- deterministic reproducibility: PASS
- non-negative generation: PASS
- covariance collapse: PASS
- Talent/current ability separation: PASS
- position separation: PASS
- pitcher archetype representation/diversity: PASS
- catcher archetype representation/diversity: PASS
- catcher Game Calling structural distribution: PASS
- gross elite multi-rating pile-up: PASS
- strict seed stability: FAIL
- distribution-width realism vs KBO: OPEN
- extreme-tail realism vs KBO: OPEN
- hitter/pitcher universal raw-100 semantics: OPEN
- production recenter/normalization readiness: OPEN

## Recommended next experiment

Run `R1V - Independent Validation / Reference Alignment` before any R2 tuning. 05 should reproduce R1 from an actual latest-main checkout in Codespaces using production modules directly and compare report-level metrics. 08 should complete player-level spectrum, primary velocity distribution, and catcher-proxy gaps. After those are available, 02 can define R2 candidate scale alignment while keeping gameplay coefficients in 01.
