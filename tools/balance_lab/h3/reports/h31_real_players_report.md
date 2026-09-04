# H3.1 Real-Player Transfer Validation

This is a validation-only transfer test. Existing `kbo_2026_real_hitter_ratings_v3.csv` ratings are used unchanged; H3.1 ratings are **not** refit here.

## Conditions

- 30 hitters
- 600,000 PA per hitter
- 18,000,000 total PA
- average opponent defense = 100
- balanced approach assumption
- right-handed assumption because v3 data does not contain handedness
- fixed deterministic seed per player

## Aggregate error

| Metric | MAE |
|---|---:|
| AVG | 0.0194 |
| OBP | 0.0197 |
| SLG | 0.0436 |
| OPS | 0.0503 |
| HR rate | 1.23%p |
| BB rate | 0.76%p |
| K rate | 4.55%p |

Validation-only fit-status counts: **9 good / 17 usable / 4 poor**.

## Closest OPS transfers

| Player | Target OPS | H3.1 OPS | Abs error |
|---|---:|---:|---:|
| 박찬호 | .748 | .748 | .0003 |
| 문현빈 | .845 | .844 | .0012 |
| 김주원 | .838 | .842 | .0035 |
| 박재현 | .796 | .800 | .0037 |
| 김호령 | .744 | .748 | .0040 |
| 김현수 | .736 | .731 | .0049 |
| 홍창기 | .674 | .680 | .0063 |
| 손성빈 | .702 | .695 | .0065 |

## Largest OPS mismatches

| Player | Target OPS | H3.1 OPS | Abs error |
|---|---:|---:|---:|
| 나성범 | .932 | .746 | .1861 |
| 힐리어드 | .924 | .738 | .1859 |
| 오스틴 | 1.090 | .916 | .1738 |
| 정수빈 | .701 | .804 | .1025 |
| 김도영 | 1.038 | .939 | .0990 |

## Interpretation

The H3.1 structure is numerically stable across all 30 existing player profiles, but v3 ratings do not transfer one-to-one. BB-rate transfer is relatively good; K-rate and several high-SLG profiles show the largest structural mismatch. This is expected because v3 ratings were calibrated against an earlier probability model. A later H3.1-specific rating calibration should be a separate tuning pass rather than changing this validation result.
