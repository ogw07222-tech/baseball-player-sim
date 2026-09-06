# KBO First-Team Population Summary

Gate: `KBO_FIRST_TEAM_POPULATION_CONTRACT_NOT_READY`

## Contract implemented

- primary unit: player-season
- source: production `CareerEngine`
- retain only seasons with `first_team.PA > 0`
- hitter league weighting: first-team PA
- zero-PA farm/development players: excluded from league calibration weight
- raw ratings remain canonical; approved hitter normalization is derived at gameplay time

## Planned full diagnostic

- 600 careers/seed × 3 seeds = 1,800 production careers
- up to 18 pro seasons/career
- 1.7M neutral H3 PA/seed = 5.1M PA total
- 4,000 best-available representative generated pitchers

The user-requested 100k–250k full `CareerEngine` careers are not claimed as executed. Real roster/game simulation makes that target substantially more expensive than a generated snapshot Monte Carlo. The workflow records the actual sample size and requires multi-seed stability rather than silently substituting a fake 100k count.

## Pitcher usage limitation

The repository currently has pitcher generation/growth/FastSim but no hitter-equivalent pitcher career roster flow that records first-team BF/IP by player-season. Therefore generated pitcher calibration rows are explicitly labelled `best_available_age_mix_proxy_no_pitcher_career_usage_engine`; no BF/IP usage is fabricated.

## Execution status

The GitHub-hosted runner was not allocated on either the original attempt or the explicit failed-job rerun (`runner_id=0`, zero steps). Therefore the neutral-offense and seed-stability diagnostics have not executed on this branch and the gate remains NOT_READY.
