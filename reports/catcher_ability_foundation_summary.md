# Catcher Ability Foundation Summary

## 1. Branch

`feature/catcher-ability-foundation`

## 2. Base SHA

`1800dc8d145dc9155763ea1a32099f6dafb87d18` (`main` at branch creation)

## 3. Final HEAD

Authoritative final HEAD is the head SHA of the Draft PR / branch after this report commit. The exact SHA is intentionally not self-embedded because changing this file changes the commit SHA; completion metadata records it externally.

## 4. Changed files

- `src/stats.py`
- `src/player.py`
- `src/growth.py`
- `src/catcher.py` (new)
- `src/catcher_growth.py` (new)
- `tests/test_catcher_foundation.py` (new)
- `docs/catcher-ability-foundation.md` (new)
- `reports/catcher_ability_foundation_summary.md` (new)

## 5. Catcher schema

Final catcher ability system:

- Defense: existing shared raw/display field, catcher context includes receiving, blocking, difficult-pitch handling, WP/PB mitigation potential and general catcher fielding.
- Throwing: existing shared raw/display field, catcher context includes arm, transfer/release, accuracy and stolen-base-prevention potential.
- Game Calling: new integer raw/display field, default `0` for backward compatibility / non-catchers.

No `Catching`, `Receiving`, or `Blocking` field was introduced.

`C` was already supported in `config.POSITIONS`; no position-enum change was needed.

## 6. Generation distribution

A deterministic 200,000-catcher Monte Carlo mirror of the committed generation constants/algorithm was run with seed `20260906`. Repository CI also contains a 100,000-catcher distribution regression test.

| Rating | Mean | SD | P10 | P25 | P50 | P75 | P90 | P95 | P99 | Min | Max |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Defense | 83.10 | 17.40 | 61 | 71 | 83 | 95 | 105 | 112 | 123 | 12 | 159 |
| Throwing | 92.43 | 18.30 | 69 | 80 | 92 | 105 | 116 | 123 | 135 | 13 | 176 |
| Game Calling | 85.65 | 15.20 | 66 | 75 | 86 | 96 | 105 | 111 | 121 | 20 | 155 |

Extreme frequencies:

| Rating | >=150 | >=170 | >=200 |
|---|---:|---:|---:|
| Defense | 9 / 200,000 (0.0045%) | 0 | 0 |
| Throwing | 202 / 200,000 (0.1010%) | 4 / 200,000 (0.0020%) | 0 |
| Game Calling | 1 / 200,000 (0.0005%) | 0 | 0 |

Observed generation correlations in the same run:

- Defense / Throwing: ~0.20
- Defense / Game Calling: ~0.27
- Throwing / Game Calling: ~0.17

This is intentionally weakly positive rather than independent or nearly identical.

## 7. Archetype distribution

Archetype weights are generation-only and do not add gameplay effects.

| Archetype | Weight | Defense mean | Throwing mean | Game Calling mean |
|---|---:|---:|---:|---:|
| balanced | 25% | 83.03 | 92.95 | 84.97 |
| defensive | 22% | 88.06 | 91.00 | 87.67 |
| game_manager | 20% | 83.92 | 89.81 | 91.71 |
| offensive | 15% | 76.06 | 88.04 | 78.15 |
| strong_arm | 18% | 82.12 | 100.01 | 83.63 |

The offensive archetype does not modify Contact/Power/Discipline/Speed in this foundation; it is comparatively offense-led only because catcher-defense ratings are more modest.

## 8. Age / growth sanity

Game Calling growth is connected only for `position == "C"` through `src/catcher_growth.py`. It reuses the existing mentality/general-skill growth distribution as the base, preserving current talent, development-profile, experience, trait, damping and aging philosophy. The adapter adds only a small skill-development bias through age 31 and slightly lower variance.

Game Calling is deliberately excluded from generic growth explosions. Full peak-age calibration is deferred to a later validation task; this foundation only establishes a non-pathological, experience-heavy growth path.

## 9. Save compatibility

- No save-version bump.
- `PlayerStats.game_calling` defaults to `0`.
- `PlayerStats.from_dict()` accepts old stats dictionaries with no Game Calling field.
- `Player.as_dict()` / `Player.from_dict()` round-trip Game Calling and optional catcher archetype.
- Existing `persistence.load_game()` delegates through `Player.from_dict()`, so old save payloads remain loadable.

## 10. Hitter regression

- Contact / Power / Discipline / Speed generation code and distributions are unchanged.
- Non-catcher generation consumes no additional RNG calls in the catcher adapter.
- `current_ability()` explicitly excludes Game Calling, preventing draft/hitter current-ability recalibration in this task.
- Protected H3.2.1 hitting model / parameter / baserunning files are untouched.

## 11. Pitcher regression

No file under `src/pitching/` is modified. No pitcher rating or pitcher growth field references Game Calling. The new catcher tests assert that no `src/pitching/*.py` source contains a Game Calling integration.

## 12. Untouched gameplay files

Unmodified by this branch:

- `src/hitting/model.py`
- `src/hitting/parameters.py`
- `src/hitting/baserunning.py`
- `src/hitting/normalization.py` if present on the base
- `src/pitching/*`
- `src/inning.py` if present on the base
- `src/game_provider.py` if present on the base
- `src/stat_aggregation.py` if present on the base
- `src/time_advance.py` if present on the base
- KBO calibration tools/reports/data
- web UI

## 13. Tests

New required test coverage includes:

- `test_catcher_position_supported`
- `test_catcher_has_game_calling`
- `test_non_catcher_backward_compatible`
- `test_old_save_without_game_calling_loads`
- `test_game_calling_roundtrip_save`
- `test_catcher_generation_distribution` (100,000 catchers)
- `test_catcher_archetype_diversity`
- `test_game_calling_growth_foundation`
- `test_no_hitting_formula_changes`
- `test_no_pitching_formula_changes`
- `test_no_inning_engine_changes`

Existing repository test suites are left unchanged and are expected to run through the normal GitHub Actions workflow.

## 14. CI

Draft PR CI is the authoritative executable regression evidence. At report authoring time the branch had not yet completed PR-triggered GitHub Actions; final workflow/status is recorded in the PR and completion response rather than guessed here.

## 15. Known limitations

- No catcher gameplay formula exists yet.
- No WP/PB, receiving/framing, stolen-base deterrence, CS probability, or pitch-selection modifier is implemented.
- Game Calling is not yet calibrated against real catcher outcomes.
- Full mature/prime distribution and peak-age tuning remain a separate validation task.
- Catcher archetypes are generation identities only; no gameplay effect is attached.

## 16. Next step

After this foundation is reviewed, run a separate Catcher Gameplay Calibration / Integration task covering Defense -> receiving/blocking/WP-PB, Throwing -> attempt deterrence + CS success, and Game Calling -> decision-quality/mistake-risk modulation without mutating pitcher raw ratings.

## Gates

- `CATCHER_ABILITY_SCHEMA_READY = READY`
- `CATCHER_GENERATION_READY = READY`
- `CATCHER_GROWTH_FOUNDATION_READY = READY`
- `CATCHER_SAVE_COMPATIBILITY_READY = READY`
- `CATCHER_GAMEPLAY_INTEGRATION_READY = NOT_RUN`
