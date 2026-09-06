# Production Integration Consolidation

## Source of truth

- Repository: `ogw07222-tech/baseball-player-sim`
- Consolidation base: `main@1477fc3aecf9224d1b34f77a5d755880c9c88bfe`
- Branch: `feature/production-integration-consolidation`

Source PR heads selected for integration:

- #18 persistent inning: `db2183c53d91af008c2e1daa2a4e63074bc229d3` — already merged into main; not replayed.
- #21 natural events: `82192e6545ecc59e96112e1df2383d70e204c916`.
- #26 stat aggregation/advance: `a99562c795196f960756aac11223587b8e1fdc18`.
- #28 production full-game provider: `e95c813170ba906fd8450648e21dcee1f87f6a76`.
- #30 catcher ability foundation: `c0867599f9b8ea6f5318ffbf33da7823796b56a5`.
- #32 dynamic pitcher usage: `74f08be0b4ab2f4628da9b2b37af2013915a3631`.

Calibration/diagnostic branches #20/#22/#23/#24/#25/#27 are explicitly excluded.

## Canonical production flow

`ProductionAdvanceService`
→ `CareerGameAdvanceProvider`
→ `DynamicPitcherGameProvider`
→ `PersistentInningEngine`
→ `ProductionGameResult`
→ exact stat aggregation
→ `AdvancePipelineState`

The fixed-six `ExistingProfilePitcherProvider` remains only as an explicitly injected low-level compatibility provider. It is not the default career/date-advance path.

`PitcherUsageProductionAdvanceService` is retained as a compatibility alias of `ProductionAdvanceService`; it does not own a second orchestration pipeline.

## Absorbed functionality

### Persistent inning / natural events

The #18 persistent runner identity, base state, batting order, inning progression, walkoff and extra-inning semantics are retained. #21 adds SF/tag-up, first-to-home on doubles, refined fielder's choice, conservative ground-out advancement and a disabled-by-default WP/PB contract. Normal simulation does not generate WP/PB.

### Exact aggregation / advance

Hitter counting support: G, PA, AB, R, H, 1B, 2B, 3B, HR, RBI, BB, HBP, SO, SB, CS, GDP, SF.

Pitcher counting support: G, GS, BF, outs, H, R, HR, BB, HBP, SO plus only exact supported optional fields. ER and official W/L/SV/HLD remain unsupported rather than fabricated where provenance is insufficient.

Week/month advance is composed from actual scheduled full games. Consolidation tightens the persistent date cursor so bulk advance finishes on the same final scheduled-game date as N repeated one-game calls, making counting totals, recent history, date and pitcher-usage state compositionally equivalent.

### Full-game provider

Nine-player offense, exact final score/team result, exact user hitter extraction and event-based pitcher counting are retained from #28.

### Dynamic pitcher usage

#32 supersedes #28's fixed-six generic bullpen default with STARTER/LONG_RELIEF/MIDDLE_RELIEF/SETUP/CLOSER/SWINGMAN roles, five-man rotation, rest eligibility, role reassignment/hysteresis, fatigue/recovery debt, consecutive-day handling, availability states, role-aware bullpen choice, emergency fallback and dynamic starter exit. Raw pitcher ratings and pitch-outcome probabilities are never mutated.

### Catcher foundation

Catcher abilities are Defense, Throwing and Game Calling. Game Calling is backward-compatible (`0` when absent / for non-catchers), generation/growth foundation only. No WP/PB, steal deterrence, caught-stealing, framing or pitcher-rating gameplay effect is added here.

## Conflict resolutions

1. PR #18 was already merged, so it was not replayed.
2. PR #21's `records.py` is used only to add optional `SF` support on top of the already-main H3.2.1 diagnostics.
3. PR #28/#32 `persistence.py` is consolidated to support both optional `advance_state` and `pitcher_usage_state`.
4. #32 dynamic usage is the canonical advance provider. #28's generic bullpen remains explicit compatibility only.
5. #26's period-end cursor behavior is narrowed at the production adapter: persistent state date follows the last actually simulated scheduled game, matching repeated one-game composition.
6. #30 catcher changes are additive to the current generation foundation; Game Calling remains excluded from current-ability calibration and from gameplay formulas.

## Protected formula contract

The following latest-main Git blobs must remain byte-identical:

- `src/hitting/model.py`: `b2f2f70a91c2534a99cf6ce299764804ef3484d6`
- `src/hitting/parameters.py`: `f249ecf46bcebe057d774188b873b1d41335d90a`
- `src/hitting/baserunning.py`: `2a383ce61fb6938ae30973be210159baa1d76726`
- `src/hitting/defense.py`: `279f6282ef41c53e709839dbbe791e16836eaf53`

No failed Pitcher Joint v2 coefficients or excluded calibration branch files are promoted.

## Save compatibility

No save-version bump is required. Missing optional fields reconstruct safely:

- `game_calling` → `0`
- `catcher_archetype` → `None`
- missing `advance_state` → legacy behavior until production advance is initialized
- missing `pitcher_usage_state` → fresh usage state when the canonical service is initialized
- missing newer BattingLine counters including SF → `0`

## Codespaces / local verification

Run the complete integration gate with:

```bash
bash tools/run_production_integration_checks.sh
```

Focused commands:

```bash
python -m compileall -q src tests tools
python -m unittest tests.test_persistent_inning tests.test_natural_baseball_events tests.test_stat_aggregation_advance tests.test_production_game_provider tests.test_production_game_provider_contracts tests.test_pitcher_usage_foundation tests.test_catcher_foundation tests.test_production_integration_consolidation -v
python -m unittest discover -s tests -v
python tools/natural_event_sanity.py
python tools/production_game_provider_sanity.py --games 10000 --seed 20260906 --output reports/integration-local/full-game.json
python tools/pitcher_usage_sanity.py --seasons 500 --seed 20260906
python tools/catcher_generation_sanity.py --samples 200000 --seed 20260906
cd web && npm ci && npm run test && npm run build
```

## Inherited sanity evidence

The source implementations supplied the following pre-consolidation validation evidence:

- Natural events: 100,061 events / 97,835 PA; SF 179; tag-up 374/1,784; 1B→Home on double 865/1,428; GDP 1,356; XBT 5,847; WP 0; PB 0.
- Pitcher usage: 500 x 144-game orchestration seasons; 5.868 starter IP/start; 2-day streaks 87.694/team-season; 3-day 12.050; 4-day 0.076; unavailable normal-use violations 0; bullpen exhaustion 0.002/team-season.
- Catcher generation: 200k source validation means Defense 83.10, Throwing 92.43, Game Calling 85.65; non-catchers retain neutral catcher-only state.

These source results are historical evidence, not a substitute for running the consolidation commands above.

## Known limitations

- The deterministic neutral lineup/staff and temporary non-Monday 144-game date provider remain integration fallbacks pending canonical roster/schedule systems.
- Exact pitch count is unavailable in the full-game counting contract; #32 usage load retains the documented BF×4 fallback. This does not alter pitch outcomes.
- ER and official pitcher decisions remain unsupported where exact provenance is unavailable.
- WP/PB occurrence remains disabled; catcher gameplay effects are intentionally not integrated.
- No calibration retuning is part of this consolidation.

## Promotion rule

This branch remains Draft until compile/import, focused integration tests, full unit regression, compositional advance checks and sanity runs execute successfully. GitHub runner startup/quota failure must be reported as infrastructure non-execution rather than code failure.
