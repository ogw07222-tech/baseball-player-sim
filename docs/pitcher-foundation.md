# Pitcher Foundation

## Source
- main: `d114c3d05e5afd7012b32c27213f240f3a256137`
- PR #11: merged
- experimental validation commit: `4e16feb4648370201e83e17a1303af833b0f9bd7`
- production branch: `feature/pitcher-foundation`

## Visible pitcher stats
Velocity, Stuff, Control, Breaking, Stamina, Resilience, Talent.

Starter/Reliever is a usage role, never a second stat system. Base stats do not mutate when role changes.

## Architecture
`src/pitching/model.py` owns PitcherStats, Pitcher, generation, matchup probabilities, PitchingLine and FastSim outing resolution.
`roles.py` owns role modifiers. `fatigue.py` owns in-game/recovery fatigue. `growth.py` reuses the existing weak growth constants. `performance.py` owns the league-relative pitcher score foundation. `events.py` provides role-filter compatibility only; no pitcher event library is added.

## Validated calibration
Neutral 500k PA: .261 AVG / .320 OBP / .400 SLG / .720 OPS, K 21.43%, BB 8.05%, HR 2.73%.
Player generation: ability 79.55 +/- 8.87. NPC: 70.04 +/- 6.16.
Starter neutral: 6.34 IP/app. Reliever neutral: 0.98 IP/app with +4 Velocity/+4 Stuff and 1.38x drain.

## Formula roles
- Velocity: K leverage, slight hard-contact suppression; BB neutral.
- Stuff: K plus contact-quality suppression.
- Control: primary BB suppression.
- Breaking: K plus HR/SLG suppression.
- Stamina: outing length/fatigue only.
- Resilience: recovery only.

## Performance score
K%, BB%, HR%, FIP-like and role-relative workload are reliability-shrunk and mapped to the shared `100 + 15 * index` scale. Starter workload has more weight; reliever rate stats have more weight. There is no automatic starter/reliever bonus.

## Compatibility
The existing hitter Player/PlayerStats/save schema remains unchanged. Pitcher models serialize independently and do not alter old saves. Catcher interaction is an explicit zero-effect extension object. No full catcher system or high-school world is implemented.

## Known limitations
- No persistent rotation/bullpen manager.
- No full player-career selection path for pitchers yet.
- No pitcher event content beyond role-filter compatibility.
- No catcher receiving/framing/game-calling model.
- Growth age offsets are foundation calibration, not historical-realism final tuning.

Promotion recommendation is determined after full repository CI and hitter regression.
