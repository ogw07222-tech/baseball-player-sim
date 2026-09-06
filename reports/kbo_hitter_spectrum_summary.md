# KBO Hitter Spectrum Summary

Status: `KBO_BROAD_PLAYER_SPECTRUM_NOT_READY`

Primary season: **2025**.

Implemented contract:

- eligible primary set: `PA >= 100`
- robust secondary set: `PA >= 300`
- performance stratification: P0-10 / P10-25 / P25-50 / P50-75 / P75-90 / P90-100
- performance score uses AVG, OBP, SLG, BB%, K%, HR%, BABIP together; OPS alone does not define buckets
- bottom 25% is explicitly retained
- league summaries and sampling are PA-weighted
- 100-299 PA rows use fixed pseudo-count shrinkage toward the 2025 league context while preserving observed source values
- usage labels distinguish role 100-299 PA, regular 300-449, regular 450-549, and everyday 550+
- inverse fitting uses the broad-spectrum source and fixed shrinkage targets via `infer_hitters_broad.py`

This file is an execution-status placeholder because GitHub-hosted jobs for this branch currently receive no runner and execute zero steps. The workflow-generated report replaces this status when the pipeline actually runs.
