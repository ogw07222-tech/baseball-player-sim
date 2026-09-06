# KBO Broad Spectrum Calibration — Execution Status

## Current status

The broad-spectrum implementation is present, but calibration execution has **not** occurred.

Observed GitHub Actions behavior on branch `feature/kbo-broad-player-spectrum`:

- workflow run `34017664447` was created for `kbo-rating-inference`
- both `pilot-pipeline` and `contract-tests` jobs ended in failure state
- the connector reports **no executed steps** for either job
- this matches the runner-allocation failure already observed on PR #25

Therefore this is classified as an **execution-infrastructure blocker**, not a calibration/test failure.

No READY gate is promoted from unexecuted code.

## Frozen contracts preserved

- H3.2.1 formulas: unchanged
- hitter display/gameplay normalization: unchanged
- Velocity v2 physical mapping: unchanged
- S/C/B raw recenter: unchanged
- frozen KBO objective/tolerances: unchanged

## Implemented broad-spectrum pipeline

1. collect 2025 KBO hitter/pitcher source tables
2. retain hitters >=100 PA and pitchers >=100 BF
3. performance-stratify hitters across six quantile buckets
4. stratify starter and reliever pitchers separately across five quantile buckets
5. preserve bottom buckets rather than trimming them
6. apply fixed pseudo-count shrinkage to lower-usage rows
7. fit hitter ratings with broad/shrinkage-aware inverse search
8. fix measured pitcher Velocity and fit S/C/B only when the Joint context is valid
9. build a role-aware pitcher BF/IP/G/GS calibration-only usage provider
10. compare generated vs real spectra overall and by bottom/middle/top segments
11. compute rating/metric rank correlations and rating tails
12. gate Joint v4 on broad-spectrum readiness before coefficient search
