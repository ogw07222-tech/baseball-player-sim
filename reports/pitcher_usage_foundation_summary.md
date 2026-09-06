# Pitcher Usage / Dynamic Role Foundation Summary

## Scope

Pitcher usage, role, rotation, bullpen-selection and consecutive-use fatigue orchestration only. No pitch-outcome probability, raw rating, H3.2.1, Velocity-v2, Stuff/Control/Breaking calibration, catcher gameplay, growth-core or web formula is changed.

- latest main observed at task start: `1800dc8d145dc9155763ea1a32099f6dafb87d18`
- compatible stack base: PR #28 / `feature/production-game-provider-integration@e95c813170ba906fd8450648e21dcee1f87f6a76`
- working branch: `feature/dynamic-pitcher-usage-foundation`
- draft PR: #32
- final publication HEAD: use PR #32 head; this document is part of that head

## Architecture

`src/pitcher_usage.py` owns persistent season usage state. `src/pitcher_usage_game_provider.py` is a drop-in PR #28 full-game provider that keeps `PersistentInningEngine` and existing gameplay probabilities but replaces the fixed six-inning handoff. `src/pitcher_usage_advance.py` composes the dynamic provider with the existing date-advance service. `src/persistence.py` stores the usage state as an optional backward-compatible payload.

The existing PR #28 fixed-six provider remains available for explicit compatibility. The new dynamic usage-aware path is the candidate replacement and does not modify protected probability modules.

## Role model

Season assignment roles: STARTER, LONG_RELIEF, MIDDLE_RELIEF, SETUP, CLOSER, SWINGMAN. Roles are usage assignments, not immutable pitcher identities. Role changes never mutate Velocity, Stuff, Control or Breaking.

## Rotation policy

The fallback staff uses five starters. A starter needs four full rest days and is normally eligible on the fifth calendar day after the prior start. If the normal rotation is exhausted, SWINGMAN/LONG_RELIEF can spot start before an exhausted rotation fallback is used.

## Promotion / demotion and hysteresis

Role evaluation uses the most recent five relevant outings and only supported counting events: R, BF, H, BB, SO, HR and outs. Starter evaluation additionally considers average outs/start and repeated early exits. A bad single game is insufficient.

- role evaluation interval: 10 days
- minimum post-switch hold: 18 days
- minimum post-switch appearances before another change: 4
- starter demotion candidate: at least 3 recent starts plus sustained poor signal or repeated early exits
- reliever promotion candidate: at least 4 recent relief outings or 20 BF, stamina >= 88, strong recent signal
- switch only when the replacement starter-candidate score exceeds the incumbent candidate by >= 0.28

## Consecutive-use fatigue

Fatigue load and recovery debt are stored separately.

| Consecutive usage | Workload multiplier |
|---|---:|
| first day | 1.00x |
| second day | 1.30x |
| third day | 1.75x |
| fourth+ | 2.40x |

Additional recovery debt is added on the second/third/fourth consecutive day. Heavy back-to-back relief (previous >=30 pitches and current >=20) receives an additional debt penalty. Therefore 15+14+12 pitches over three consecutive days is not treated as one 41-pitch outing.

PR #28 does not expose exact pitch count through `PitcherCountingStats`; this foundation uses a documented `4.0 pitches/BF` workload fallback. It affects usage/fatigue orchestration only, not pitch outcomes.

## Availability

AVAILABLE / LIMITED / TIRED / UNAVAILABLE. Availability combines fatigue load, recovery debt, recent five-day workload and consecutive-day usage. Three straight days makes the next normal day unavailable. UNAVAILABLE pitchers are excluded from normal selection and enter only the emergency pool after usable unused relievers are exhausted.

## Starter exit

The dynamic provider is not tied to a fixed six-inning ceiling. It combines estimated pitch workload, BF, outs, runs, H+BB traffic, inning and stamina metadata. Severe collapse can exit before six; a clean efficient start can continue beyond six. No new pitch-outcome modifier is applied.

## Bullpen selector

Deterministic role-aware priorities: CLOSER late/close, SETUP seventh/eighth high leverage, MIDDLE_RELIEF middle innings, LONG_RELIEF early exit/multi-inning, SWINGMAN spot start/long relief. LIMITED/TIRED and recovery stress reduce priority. No ML/RL manager logic is used.

## Save compatibility

`pitcher_usage_state` is optional. Old saves without it load normally and no save-version bump is required. Stored state includes current/previous role, switch metadata, starter/relief appearances, consecutive use, last appearance/start, fatigue load, recovery debt and recent outings.

## 500-season usage-orchestration sanity

500 x 144-game synthetic usage seasons, seed family starting `20260906`. This is not gameplay calibration; supported counting lines are synthesized only to exercise manager/workload orchestration.

| Metric | Result |
|---|---:|
| mean individual role changes / team-season | 8.792 |
| median individual role changes / team-season | 8.0 |
| pitchers with 0 role changes | 45.85% |
| pitchers with 1 role change | 39.57% |
| pitchers with 2+ role changes | 14.58% |
| average starter IP/start | 5.868 |
| mean 2-day streak count/team-season | 87.694 |
| mean 3-day streak count/team-season | 12.050 |
| mean 4-day streak count/team-season | 0.076 |
| unavailable normal-use violations | 0 |
| bullpen exhaustion events/team-season | 0.002 |
| starts per pitcher/team-season | 12.0 |
| relief appearances per pitcher/team-season | 39.318 |

85.4% of pitchers finish with zero or one role change. Three-day streaks remain possible but uncommon relative to relief usage; four straight days are rare/emergency territory.

## Regression / protected files

PR #28 base -> this branch diff does not include existing `src/pitching/*`, H3 hitting files, config, stats, growth or web. Protected pitch-outcome and calibration modules are untouched.

Local foundation checks before publication:
- usage-module unit tests: 6/6 PASS
- required production-foundation test module: syntax/compile PASS locally; repository execution requires PR #28 stack runner
- 500-season sanity: PASS under the distributions above

GitHub Actions run `34021278500` did **not execute repository tests**: both `web-tests` and `unit-tests` ended with `runner_id=0` and zero steps. The runner failure is therefore infrastructure/runner availability, not a reported assertion or import failure. Full provider/advance/save integration remains unverified by CI.

## Known limitations

1. PR #28 has no canonical persistent pitcher roster. The dynamic provider supplies stable deterministic team pitcher identities as an integration fallback; a future roster provider can replace it without changing usage math.
2. Exact pitch count is absent, so workload uses BF x 4 until pitch accounting lands.
3. Pitcher injury integration waits for a canonical pitcher roster/player lifecycle; no new injury formula is invented here.
4. Fatigue currently affects storage/availability/selection only. No new tired-pitcher outcome modifier is created.
5. PR #28 is an unmerged stack dependency; PR #32 should remain draft/stacked until that order resolves.
6. GitHub runner unavailability prevented full-stack test execution in this pass.

## Gates

- `PITCHER_DYNAMIC_ROLE_READY = READY`
- `PITCHER_ROTATION_READY = READY`
- `PITCHER_CONSECUTIVE_FATIGUE_READY = READY`
- `PITCHER_BULLPEN_USAGE_READY = NOT_READY` — dynamic provider integration code exists, but full-game CI did not execute
- `PITCHER_GAMEPLAY_FATIGUE_EFFECT_READY = NOT_RUN`

## Next step

When a runner is available, execute the complete PR #28 test suite plus `tests/test_pitcher_usage_foundation.py`. If that passes, promote `PITCHER_BULLPEN_USAGE_READY` to READY. Do not merge automatically; after PR #28 lands, rebase/retarget PR #32 and rerun exact provider/advance/save tests.
