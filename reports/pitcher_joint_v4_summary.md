# Pitcher Joint Calibration v4

Gate: `PITCHER_JOINT_CALIBRATION_V4_NOT_READY`

v4 reuses the frozen Velocity v2 physical path, physical caps, SCB raw scale and frozen 2025 KBO target/tolerances. Hitter profiles are converted through the approved raw→gameplay normalization before H3. Failed coefficients remain calibration-only.

## Best candidate
`{"w_breaking_contact": 0.33058095887517397, "w_breaking_quality": 0.14678763924635163, "w_control_zone": 0.1625073024797727, "w_stuff_contact": 0.09824857514191548, "w_stuff_quality": 0.5045669577007901}`

## Metrics
- AVG: 0.240581
- OBP: 0.295440
- SLG: 0.365190
- OPS: 0.660630
- BB%: 0.072239
- K%: 0.224049
- HR%: 0.024796
- 1B%: 0.158412
- 2B%: 0.038768
- 3B%: 0.001225
- BABIP: 0.292238
- HardContact%: 0.080674

## Semantic gates
- control_owns_bb: FAIL
- control_avg_not_pathological: PASS
- control_slg_not_pathological: PASS
- stuff_reduces_hard_contact: PASS
- stuff_not_universal: PASS
- breaking_increases_k: PASS
- breaking_more_k_than_stuff: PASS
- breaking_not_universal: PASS
