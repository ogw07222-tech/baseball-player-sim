# KBO Pitcher Spectrum Summary

Status: `KBO_BROAD_PLAYER_SPECTRUM_NOT_READY`

Primary season: **2025**.

Implemented contract:

- eligible primary set: `BF >= 100`
- robust secondary set: `BF >= 300`
- starter and reliever performance quantiles are computed separately
- primary performance score uses K%, BB%, HR%, opponent AVG, opponent SLG, and BABIP; ERA is auxiliary only
- role labels: starter / reliever / swingman
- usage labels distinguish starter workload, swingman, low/middle relief, setup/high-usage relief, and closer where supported
- league summaries and sampling are BF-weighted
- low-BF rows use fixed pseudo-count shrinkage while preserving original observed values
- measured average fastball velocity remains authoritative; performance never changes raw Velocity
- `PitcherFirstTeamUsageSnapshot` provides a calibration-only role-aware BF/IP/G/GS usage proxy because production has no pitcher CareerEngine equivalent yet
- inverse fitting uses the broad-spectrum source and fixed shrinkage targets via `infer_pitchers_broad.py`

The role-aware usage provider is explicitly a proxy and not presented as real production first-team BF. This report remains NOT_READY until the full workflow executes with live source coverage.
