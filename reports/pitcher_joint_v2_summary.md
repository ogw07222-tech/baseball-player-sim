# Pitcher Physical Velocity Cap + Joint Calibration v2 Summary

## Source / scope

- repository: `ogw07222-tech/baseball-player-sim`
- latest main at branch start: `44b4bbb9113e351ceb35aac75f02a8ee6eab3723`
- branch base: Velocity Scale v2 READY HEAD `c405b3e9c1ec2633fabd0f033c0c923b165bd6af`
- branch: `feature/pitcher-joint-calibration-v2`
- Velocity v2 mapping: **FROZEN**
- physical -> gameplay scale: **1.50 H3 points / km/h, frozen**
- H3.2.1 hitter formula changes: **NONE**

This task adds a physical-velocity safety layer and then calibrates only Stuff / Control / Breaking. Velocity is not a search coefficient.

## Physical velocity safety design

Production responsibility is isolated in `src/pitching/physical_velocity.py`.

Pipeline:

`raw Velocity -> v2 base avg km/h -> base soft cap -> effort/fatigue -> effective soft cap -> gameplay normalization`

Raw Velocity is never mutated by the cap.

Chosen safety constants:

- base average soft start: **160.0 km/h**
- base soft scale: **4.0 km/h**
- base average absolute safety ceiling: **164.0 km/h**
- effective average soft start: **164.0 km/h**
- effective soft scale: **3.0 km/h**
- effective average absolute safety ceiling: **167.0 km/h**
- single-pitch max hard safety ceiling: **170.0 km/h**

The base/effective soft functions approach their ceilings smoothly rather than creating a hard-clamp pile-up. Single-pitch max remains separately clamped because it is a stochastic safety ceiling rather than the primary rating anchor.

## 100,000-career velocity stress

Stress cohort uses the same `player=True` pitcher generation cohort used by Velocity Scale v2 and current production pitcher growth through age 45. Current pitcher events do not directly mutate Velocity; therefore event-driven Velocity growth is not present in current production and is documented as a future regression case.

| metric | P99 | P99.9 | P99.99 | max | exact-cap fraction |
|---|---:|---:|---:|---:|---:|
| Raw Velocity | 126 | 136 | 148 | 159 | n/a |
| Base avg km/h | 153.949 | 156.492 | 159.421 | **161.332** | **0.0000%** |
| Effective avg km/h (+4 stress effort) | 157.949 | 160.492 | 163.421 | **164.922** | **0.0000%** |
| Single-pitch max km/h | 166.245 | 169.110 | 170.000 | **170.000** | **0.046%** |

There are no 180-200 km/h simulated average fastballs. The base/effective caps show no boundary mass spike. The max-pitch hard ceiling is touched only by a tiny stochastic tail.

### Gate A

**PHYSICAL_VELOCITY_SAFETY_READY**

Reasons:

- no 180-200 km/h average output
- elite 159-165 km/h average tail remains distinguishable
- raw stat is preserved
- base/effective safety uses smooth compression
- no base/effective exact-cap pile-up in 100k careers
- effort remains capable of increasing early-outing physical velocity
- fatigue reduces physical velocity without mutating raw Velocity
- cap/unit tests pass

## KBO physical-velocity regression during joint fit

2,000-pitcher full-age calibration population:

- mean: **144.959 km/h**
- SD: **3.280 km/h**
- P10: 140.692
- P25: 142.602
- P50: 144.849
- P75: 147.151
- P90: 149.149
- P95: 150.496
- P99: 152.641
- max: 155.739

Reference 2025 public KBO distribution snapshot: mean about 145.45 km/h, SD about 3.72 km/h. The physical Velocity distribution remains within the frozen regression gate.

## Prime raw-scale diagnostic

A 30,000-player `player=True`, age-28 production diagnostic gives:

- Velocity mean **95.80**, SD 11.68
- Stuff mean **96.86**, SD 16.97
- Control mean **91.97**, SD 18.61
- Breaking mean **95.74**, SD 17.90
- Stamina mean 97.98
- Resilience mean 96.66
- weighted pitcher ability mean **95.55**, SD 10.16

The requested pitcher-prime raw center of about **110** is therefore **not met** by current production generation/growth.

Velocity is a deliberate exception: forcing raw Velocity to ~110 while keeping the frozen v2 physical mapping would shift league average fastball velocity toward roughly 149-150 km/h and break the KBO physical distribution. Velocity should remain physically anchored; S/C/B raw-scale comparability needs a separate generation/growth decision before production promotion.

## Joint Monte Carlo

Population:

- hitters: 2,000 current-production growth-generated hitters
- pitchers: 2,000 current-production growth-generated `player=True` pitchers
- search: 30 candidates x 100,000 PA
- validation: top 3 x 1,000,000 PA x 5 seeds
- diagnostic sensitivity: 300,000 PA

Frozen 2025 KBO offense targets/tolerances were reused without modification.

### Best candidate

- `w_control_zone = 0.7250417401`
- `w_stuff_quality = 0.5925985469`
- `w_stuff_contact = 0.2175392219`
- `w_breaking_contact = 0.6995581820`
- `w_breaking_quality = 0.5671943695`

Multi-seed mean:

| metric | simulation | KBO target | result |
|---|---:|---:|---|
| AVG | **.2071** | .2616 | FAIL |
| OBP | **.2540** | .3385 | FAIL |
| SLG | **.3112** | .3887 | FAIL |
| OPS | .5651 | .7272 | report only |
| BB% | **5.918%** | 9.149% | FAIL |
| K% | **24.912%** | 19.687% | FAIL |
| HR% | **2.105%** | 2.127% | PASS |
| 1B% | 13.998% | 16.398% | FAIL |
| 2B% | 3.274% | 4.006% | FAIL |
| 3B% | 0.103% | 0.371% | FAIL |
| BABIP | **.2591** | .3122 | FAIL |

Seed stability is high (for example AVG SD about 0.000082 and K% SD about 0.000223), so this is a stable model mismatch rather than Monte Carlo noise.

## Monotonicity / identity diagnostics

At neutral 146 km/h:

### Stuff +20

- AVG -0.0257
- SLG -0.0504
- K +0.255 pp
- BB +0.018 pp
- HR -0.580 pp
- HardContact -2.265 pp

Stuff does not own BB and does not become universal across every metric, but the current candidate suppresses overall offense too strongly.

### Control +20

- BB **-0.758 pp**
- K **-0.734 pp**
- AVG +0.0242
- SLG +0.0411
- HR +0.377 pp

Control is the strongest BB owner, but its H3 zone-path side effects are too large: K moves in the wrong direction and AVG/SLG increase materially rather than only slightly. This is a semantic blocker.

### Breaking +20

- AVG -0.0403
- SLG -0.0734
- K **+1.008 pp**
- BB +0.101 pp
- HR -0.751 pp
- HardContact -2.871 pp

Breaking has the intended stronger K/whiff identity relative to Stuff, but it is too dominant in run suppression at the coefficient magnitude needed to compensate for the current raw population scale.

### Frozen Velocity regression

- +3 km/h: AVG -0.0090, SLG -0.0145, K +0.333 pp, BB +0.008 pp
- +5 km/h: AVG -0.0142, SLG -0.0227, K +0.563 pp, BB +0.025 pp
- +8 km/h: AVG -0.0216, SLG -0.0354, K +0.919 pp, BB +0.033 pp

The physical Velocity path remains monotonic and its direct BB effect remains negligible.

## Archetype diagnostics

OPS allowed by the best candidate:

- Power Pitcher (155 km/h / Stuff 125 / Control 90 / Breaking 90): **.598**
- Command Starter (145 / 100 / 140 / 120): **.713**
- Breaking Specialist (144 / 110 / 100 / 145): **.467**
- High Stuff / Low Weapons (143 / 150 / 100 / 80): **.664**
- Balanced Ace (151 / 125 / 125 / 125): **.524**

The Breaking Specialist is much too dominant and the archetype spread is not production-sane.

Velocity-Stuff synergy diagnostic:

- A: 158 km/h + Stuff 75 -> OPS **.727**
- B: 142 km/h + Stuff 150 -> OPS **.564**
- C: 151 km/h + Stuff 120 -> OPS **.613**

High Stuff is still too powerful relative to the balanced profile; the requested balanced-combination behavior is not established.

## Why the joint gate fails

The failure is structural rather than sampling noise:

1. current prime pitcher raw ability centers around ~95.5, not the requested ~110;
2. current growth-generated hitter/pitcher scales are not jointly centered on the H3 mathematical reference;
3. compensating through larger S/C/B coefficients recreates the old pathology: exaggerated Breaking/Stuff effects and broken archetypes;
4. Control's frozen H3 zone pathway produces substantial offense side effects when made strong enough to repair the population BB deficit.

Per the failure policy, this branch does **not** loosen tolerances, increase Velocity influence, remove the velocity cap, retune H3 hitter formulas, or promote a universal Stuff buff.

### Gate B

**PITCHER_JOINT_CALIBRATION_V2_NOT_READY**

## Tests / CI

The dedicated pitcher-joint-v2 workflow completed successfully on the calibration run and repository-wide CI for the same development sequence remained green. Required velocity-cap and semantic structural tests are included in `tests/test_pitcher_joint_v2.py`.

## Known limitations

- Current production has no pitcher-specific legendary/event Velocity mutation path, so the 100k career stress covers current implemented growth/talent/archetype/aging plus an explicit high-effort physical stress. The safety layer is independent of that omission and protects future high raw ratings.
- Same-player starter/reliever physical velocity evidence remains insufficient to canonicalize a permanent role bonus. The cap architecture supports such a parameter later without mutating raw Velocity.
- `player=True` is used because Velocity v2 READY was calibrated on that cohort. A future league-roster generation contract should explicitly define how player/NPC pitcher cohorts correspond to KBO roster quality.

## Merge recommendation

- **Physical velocity safety layer: recommend promotion after Velocity Scale v2 is merged.**
- **Joint S/C/B coefficients: do not promote.**

Recommended next calibration prerequisite: define a pitcher raw-scale contract for Stuff/Control/Breaking (targeting prime ~110 if that remains the design requirement) without altering the frozen physical Velocity distribution, then rerun this exact joint objective.