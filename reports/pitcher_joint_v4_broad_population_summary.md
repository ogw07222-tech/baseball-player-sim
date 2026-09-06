# Pitcher Joint v4 — Broad Population Summary

Gate: `PITCHER_JOINT_CALIBRATION_V4_NOT_RUN`

The broad-population rerun is guarded by `KBO_BROAD_PLAYER_SPECTRUM_READY`.

Required input contract:

- hitter sampling: production CareerEngine first-team PA-weighted population
- pitcher sampling: role-aware BF-weighted calibration population
- real-spectrum coverage: bottom / middle / top hitters plus starter / reliever buckets
- Velocity: frozen physical path, not searched
- search variables: Control zone, Stuff quality/contact, Breaking contact/quality only
- frozen KBO target and tolerance set unchanged

Current execution status: GitHub-hosted jobs were created but received no runner and executed zero steps, so no coefficient result is promoted.
