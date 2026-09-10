# Data provenance and usage notes

This directory contains calibration inputs and derived simulation datasets used by Baseball Player Career Simulator.

## What is original to this project

The following values are project-generated outputs rather than official KBO ratings:

- `contact`, `power`, `discipline`, `speed`, `defense`, `throwing`, `stamina`, `durability`, `mentality`, `talent`
- Monte Carlo outputs such as `mc1000_*`
- fit/error/status fields
- simulation policy/configuration values

These fields are estimates produced for game-simulation and calibration purposes. They are not official KBO evaluations and should not be presented as such.

## Real-world reference data

Some files include real-world factual references such as player names, team names, season identifiers, and batting-stat targets (for example AVG/OBP/SLG/OPS and rate statistics). These are used only as calibration/reference facts for the simulation model.

The repository does not claim ownership of third-party league, team, player, or statistical-source material. KBO, club, and player names/trademarks belong to their respective rights holders.

For verification of real-world KBO records and statistics, prefer the official KBO records/statistics service or the original statistical source from which a value was collected. If a specific upstream source imposes attribution, redistribution, or other usage conditions, those upstream conditions continue to apply.

## Provenance limitation

The early `kbo_2026_real_hitter_ratings_v*.csv` calibration files did not preserve a per-row source URL in git history. Therefore this repository does not assert that every target statistic in those historical calibration snapshots originated from one single provider.

Before using these files outside this hobby/research project, independently verify the referenced real-world statistics and the applicable terms of the source you rely on.

## Public-repository policy

For new real-world datasets added after this notice:

1. Record the source/provider and access date in the dataset, adjacent metadata, or this file.
2. Keep third-party factual inputs separate from project-derived ratings and simulation outputs.
3. Do not commit paywalled, access-controlled, or license-restricted bulk datasets unless redistribution is permitted.
4. Prefer storing only the minimal factual fields needed for calibration.
5. When redistribution rights are uncertain, store reproducible transformation code/instructions instead of copied bulk source data.

This notice is a provenance and project-usage statement, not a grant of rights over third-party data.
