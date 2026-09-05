# Pitcher Calibration Summary

## Source of truth

- main HEAD: `44b4bbb9113e351ceb35aac75f02a8ee6eab3723`
- final stress calibration run HEAD: `abf0c9f607e21b930549cda1af4c0cf994698310`
- H3.2.1 Balance Lab source: `b7b8aafde0a50e687310dbe03b872087a569e08c`
- H3.2.1 hitter formula diff: **NONE**
- persistent inning / base-state changes: **NONE**
- growth source: production `src/growth.py` and `src/pitching/growth.py`

## KBO target and frozen objective

Target season is **2025 KBO regular season**. The calibration target was fixed before search: AVG .2616, OBP .3385, SLG .3887, OPS .7272, BB% 9.149%, K% 19.687%, HR% 2.127%, 1B% 16.398%, 2B% 4.006%, 3B% 0.371%, BABIP .3122.

Frozen tolerances were never loosened after observing results: AVG .010, OBP .010, SLG .020, BB% 1.0 pp, K% 1.5 pp, HR% 0.5 pp, 1B% 1.0 pp, 2B% 0.4 pp, 3B% 0.15 pp, BABIP .012.

Final stress search used the production growth system to build **1,000 hitters + 1,000 pitchers**, 80 candidates x 25,000 PA, followed by 5 seeds x 100,000 PA for the best candidate. This was intentionally still a pre-final calibration stage; the 50M-100M PA promotion stage is not justified when earlier gates fail.

## Best stress candidate — REJECTED

Normalized loss: **1.4310**.

Coefficients:

- `w_control_zone = 0.4700404619`
- `w_velocity_contact = 1.9215650737`
- `w_breaking_contact = 0.8344318885`
- `w_stuff_quality = 0.6692438928`
- `w_breaking_quality = 0.1354616683`

Multi-seed means:

| Metric | Simulation | 2025 KBO | Result |
|---|---:|---:|---|
| AVG | .2589 | .2616 | PASS |
| OBP | .3013 | .3385 | FAIL |
| SLG | .3973 | .3887 | PASS |
| OPS | .6987 | .7272 | report-only |
| BB% | 5.734% | 9.149% | FAIL |
| K% | 22.728% | 19.687% | FAIL |
| HR% | 2.874% | 2.127% | FAIL |
| 1B% | 17.222% | 16.398% | PASS |
| 2B% | 4.180% | 4.006% | PASS |
| 3B% | 0.126% | 0.371% | FAIL |
| BABIP | .3135 | .3122 | PASS |

The stress search can nearly recover AVG/BABIP, but only by pushing Velocity influence to an intentionally extreme value. This does not constitute a valid fit.

## Monotonicity and Stuff dominance

Stress-candidate +10 deltas:

- Velocity: K% `+1.42 pp`, AVG `-.0359`, SLG `-.0579`, BB% approximately unchanged. Direction is correct but magnitude is excessive.
- Stuff: SLG `-.0226`, AVG `-.0098`, BB% approximately unchanged. Stuff does not become a universal K/BB/HR suppressor.
- Control: BB% `-.343 pp`; K% `-.153 pp`. BB direction is correct, but the requested small indirect positive K direction is not reliably present.
- Breaking: K% `+.470 pp`, AVG `-.0196`, SLG `-.0323`.
- Stuff universal-dominance detector: **false**.

The stress candidate therefore fails the semantic/sensitivity gate even though Stuff itself is not universally dominant.

## Archetypes and Velocity–Stuff synergy

| Archetype | OPS allowed |
|---|---:|
| Balanced Ace | .406 |
| Breaking Specialist | .598 |
| Command Starter | .744 |
| High Stuff / Low Weapons | .743 |
| Power Pitcher | .370 |

Velocity–Stuff diagnostic:

- A: V150 / S70 -> OPS `.405`
- B: V70 / S150 -> OPS `.747`
- C: V120 / S120 -> OPS `.501`

The intended balanced combined-strength behavior fails under the stress-fit coefficients. Power Pitcher and Balanced Ace are unrealistically overpowering while the one-sided high-Stuff profile can outperform the balanced profile. **Reject.**

## Percentile matrix

Growth-population current-ability percentiles:

- Hitters P20/P50/P80/P95: `75.60 / 83.21 / 92.00 / 100.06`
- Pitchers P20/P50/P80/P95: `76.03 / 83.46 / 90.65 / 98.96`

The representative 4x4 matrix shows substantial tail instability; cells span roughly OPS `.62` to `.99`, and higher-percentile matchup ordering is not consistently sane. The full matrix is retained in `pitcher_calibration_final.json`.

## Starter / reliever effort model

The effort model is isolated from base ratings. Starter reference uses effort 0 and fatigue multiplier 1.00. Reliever reference uses effort 1, +4 effective Velocity, +4 effective Stuff, and fatigue multiplier 1.90. Fatigue cost is convex in effort and Stamina reduces same-effort fatigue.

For the same base V120 / S120 / Stamina100 pitcher:

| Role | Pitches | Est. BF | Fatigue | Eff V | Eff Stuff |
|---|---:|---:|---:|---:|---:|
| Starter | 15 | 3.9 | .150 | 120.00 | 120.00 |
| Starter | 30 | 7.8 | .300 | 120.00 | 120.00 |
| Starter | 60 | 15.6 | .600 | 119.93 | 119.93 |
| Starter | 90 | 23.4 | .900 | 119.25 | 119.21 |
| Reliever | 15 | 3.9 | .285 | 124.00 | 124.00 |
| Reliever | 30 | 7.8 | .570 | 123.98 | 123.98 |
| Reliever | 60 | 15.6 | 1.140 | 122.55 | 122.48 |
| Reliever | 90 | 23.4 | 1.710 | 120.63 | 120.46 |

This gives the intended **stronger early / more expensive workload** behavior without mutating base ratings. Manager substitution AI remains out of scope.

## Extreme safety and zero-direct-effect contracts

Ratings `30, 50, 70, 100, 130, 160, 200, 250` are exercised by unit tests. H3.2.1 remains the owner of probability clamping; the adapter introduces no division path. Talent has zero direct gameplay effect. Neutral-PA Stamina and Resilience have zero direct effect.

## Growth diagnostic — report only

- Velocity peak age: **28** vs sanity expectation 23-27
- Stuff peak age: **31** vs 25-29
- Breaking peak age: **32** vs 26-30
- Control peak age: **32** vs 27-31
- Overall effectiveness peak: **31** vs 26-29

Several production growth peaks are later than the requested sanity bands. Per task scope, growth was **not modified**.

## Final gates

### PITCHER_MONTE_CARLO_CALIBRATION_READY = NOT_READY

Reasons:

- frozen full-league KBO tolerances do not all pass;
- the stress fit requires pathological Velocity influence;
- sensitivity, archetype diversity, percentile-tail sanity and Velo-Stuff synergy fail;
- Control -> K indirect direction is not established;
- therefore the final 50M-100M PA promotion stage was not run.

### PITCHER_EFFORT_MODEL_READY = READY

- higher effort raises effective Velocity and Stuff;
- higher effort raises fatigue faster with a convex cost curve;
- base ratings never mutate;
- Stamina modulates workload;
- starter/reliever usage profiles diverge naturally in the diagnostic workload.

## Known limitation / next required contract

The dominant blocker is a scale mismatch: the current production growth population centers in the low/mid-80s, while H3.2.1's mathematical neutral reference is 100. Trying to absorb that entire mismatch only through pitcher PA weights produces pathological sensitivities and broken archetypes.

**Do not promote the stress coefficients to production.** The next calibration task should define a principled gameplay-scale adapter/reference contract between raw growth ratings and H3.2.1 inputs while leaving the frozen H3.2.1 formulas unchanged, then rerun this same frozen KBO objective.
