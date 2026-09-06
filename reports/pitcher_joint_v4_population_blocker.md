# Pitcher Joint v4 — Population Contract Blocker

## Status

`PITCHER_JOINT_CALIBRATION_V4_NOT_READY`

This is a calibration-input blocker report. It does **not** change H3.2.1 formulas, Velocity v2, physical velocity caps, hitter normalization, pitcher raw ratings, frozen KBO targets/tolerances, or production pitcher coefficients.

## Finding

The current Joint v3/v4 calibration population builder is not a KBO first-team PA population. It samples developing players from a fixed age mixture and gives every sampled hitter equal PA weight.

With the approved hitter normalization, that mixed-age calibration population has gameplay means:

- Contact: 92.85
- Power: 93.53
- Discipline: 92.73
- Speed: 90.70

Against a completely neutral H3 pitcher, before any Stuff / Control / Breaking suppression is applied, 300,000 PA produced:

- AVG .2311
- OBP .2866
- SLG .3484
- OPS .6350
- BB 7.01%
- K 23.44%
- HR 2.219%
- BABIP .2837

The frozen 2025 KBO reference is AVG .2616 / OBP .3385 / SLG .3887 / BB 9.149% / K 19.687% / BABIP .3122.

Therefore the current population is already much too weak offensively at a neutral matchup. Normal pitcher suppression coefficients cannot repair that gap without violating stat semantics or making pitcher effects negative/pathological.

## Production mismatch

Production career flow does not give arbitrary developing prospects equal KBO PA.

`CareerEngine` / `CareerSeasonMixin` uses:

- initial first-team selection based on current ability, team depth, position competition and draft status;
- `FIRST` vs `FARM` roster state;
- periodic promotion/demotion reconsideration;
- different first-team/farm play probabilities;
- separate first-team and farm PA accumulation.

Accordingly, KBO offensive calibration should be based on **production first-team selected player-seasons weighted by first-team PA**, not equal-weight random prospects.

A calibration-only sampler has been prepared at:

`tools/pitcher_joint_v4/first_team_population.py`

It drives the real `CareerEngine`, records each pre-season raw snapshot, and weights it by that season's actual first-team PA before applying the approved derived hitter normalization.

## Formal v4 evidence

The first completed full Joint v4 computation (60 candidates × 100k PA, top 5 × 1M PA × 5 seeds, 300k semantic diagnostics) finished its Monte Carlo work before a report-only `OPS` tolerance serialization bug terminated the job.

Recovered best candidate metrics from that completed run:

- AVG .2406
- OBP .2954
- SLG .3652
- OPS .6606
- BB 7.224%
- K 22.405%
- HR 2.480%
- BABIP .2922

The multi-seed SDs were very small, so this is a stable structural miss rather than Monte Carlo noise.

Semantic result:

- Control owns BB: **FAIL**
- Control AVG/SLG side effects: PASS
- Stuff reduces hard contact: PASS
- Stuff not universal: PASS
- Breaking increases K: PASS
- Breaking more K-oriented than Stuff: PASS
- Breaking not universal: PASS

Physical velocity remained healthy (mean about 144.86 km/h, SD about 3.33 km/h, P99 about 152.91 km/h, max about 154.98 km/h), so Velocity is not the blocker.

## Required next calibration contract

Before another S/C/B coefficient search:

1. Generate production careers.
2. Retain hitter player-season snapshots with first-team PA > 0.
3. Weight hitter sampling by first-team PA.
4. Build an equivalent production-representative pitcher usage population when pitcher career/role usage is available.
5. Confirm neutral-pitcher offense for the selected hitter pool is near the intended H3/KBO domain.
6. Only then rerun the frozen Joint v4 objective.

Do **not** solve this by:

- increasing hitter normalization slope to chase league AVG;
- weakening/negating Stuff, Control or Breaking;
- changing Velocity;
- changing H3.2.1 formulas;
- relaxing KBO tolerances.

The immediate blocker is the calibration population contract, not the validated hitter display/gameplay contract.
