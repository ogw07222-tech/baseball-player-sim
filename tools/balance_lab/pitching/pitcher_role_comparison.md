# Pitcher Role Comparison

Starter and reliever use identical base stats. Role changes only usage interpretation.

Validated modifiers:
- Starter drain multiplier 1.00, Velocity/Stuff bonus +0/+0
- Reliever drain multiplier 1.38, Velocity/Stuff bonus +4/+4

Neutral base pitcher Monte Carlo:
|Role|IP/app|BF/app|Pitches/app|K%|BB%|HR%|ERA|WHIP|Eff V|Eff Stuff|
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|Starter|6.344|28.20|105.7|21.20%|8.24%|2.73%|4.00|1.45|99.38|99.38|
|Reliever|0.982|4.33|16.2|22.24%|8.33%|2.67%|3.93|1.41|104.00|104.00|

Stamina sensitivity (starter IP/app): 60=5.914, 80=6.171, 100=6.389, 120=6.565, 140=6.707.

Recovery model is role load divided by `12 + 0.08*Resilience`; higher Resilience monotonically reduces recovery days.

PASS: same-player role philosophy, reliever output boost, shorter outing, faster in-game drain, stamina workload monotonicity and resilience recovery monotonicity.
