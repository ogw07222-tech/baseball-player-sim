# 01 - Gameplay Engine

WORKSTREAM: 01 - Gameplay Engine
UPDATED_AT: 2026-09-11
SOURCE_OF_TRUTH: main@0607b76ae9d9ac8fe3302896a7066091b510d26f
STATE: AUDIT_COMPLETE
CURRENT_TASK: Offensive Event Structure Root-Cause Audit
RESULT: WATCH_WITH_CONFIRMED_HBP_GAP_AND_FULL_COUNT_BIAS

## SOURCE CHECK
- Repository currently contains canonical gameplay status at `docs/workstream-status/01-gameplay.md`; no `01-gameplay-engine.md` file exists, so this canonical file was updated rather than creating a duplicate.
- 05 expanded diagnostic source is `docs/workstream-status/05-balance-lab.md`, including 10k neutral games + 200k neutral PA + 200k generated-hitter PA measurements.
- Changes after diagnostic execution do not modify the audited core `src/hitting/model.py`, `src/hitting/parameters.py`, `src/hitting/baserunning.py`, `src/natural_events.py`, `src/inning.py`, or production PA adapter semantics.

## PA PIPELINE
- `simulate_plate_appearance_outcome()` builds `HitterSnapshot` / `PitcherSnapshot`, condition/trait modifiers, then delegates to `HittingEngine.simulate_plate_appearance()`.
- Each pitch: `_pitch()` -> binary strike/ball generation from `STRIKE_RATE + control*0.0006` (clamped .45-.66), independent descriptive zone label, pitch type and pitch-quality draws.
- `_swing_probability()` then applies zone swing or chase behavior, hitter discipline, zone label and count modifier.
- Swing path: `_contact_resolution()` -> miss / foul / BIP. Miss adds a strike; foul adds a strike only below two strikes; BIP enters `_batted_ball()`.
- Take path: strike increments strikes and may end in looking K; ball increments balls and may end in BB.
- BIP path: `_batted_ball()` -> `_is_home_run()` first -> defense catch/infield-hit/error logic -> non-HR raw 1B/2B/3B candidate -> defense suppression for 2B/3B candidate -> speed resolution.
- `PersistentInningEngine.resolve_plate_appearance()` maps terminal PA outcome into base/out/run state.

## K ROOT CAUSE
- Neutral engine itself is sufficient to produce elevated K: 05 measured neutral K 21.247% versus recent KBO ~18.76%; generated hitter ratings amplify this further but are not required for the bias.
- No hidden double-counting was found: a terminal strikeout comes from either taken strike #3 or swing-and-miss strike #3; fouls at two strikes do not add a third strike.
- Looking-K pressure is structurally material. Neutral in-zone swing is only ~68.8%; two strikes add only +2.5 percentage points, so a substantial fraction of two-strike strikes can still be taken for automatic K. 05 measured K split 54.4% looking / 45.6% swinging.
- Neutral contact has no extra two-strike miss-to-foul protection because that additional protection activates only when discipline > 100. Reference discipline 100 gets ordinary contact/foul behavior only.
- Count logic contains a confirmed composition bias: `count = +0.025 if strikes == 2 else -0.018 if balls == 3`. Therefore 3-2 receives the two-strike aggression bonus and does not receive the three-ball take modifier. Relative to other three-ball counts, full count swing/chase is +4.3 percentage points before clamps. This specifically shifts out-of-zone 3-2 pitches away from walk outcomes and toward swing outcomes, including swinging K.
- Pitcher control changes binary zone probability by 0.06 percentage points per raw control point until clamped; it also changes location quality/hittability. Zone label itself is sampled independently of binary strike/ball status.

## BB ROOT CAUSE
- Walk path is structurally simple and not double-counted: four taken out-of-zone pitches terminate as BB.
- BB is suppressed by the same high-strike / early-K pressure that limits deep counts; 05 measured only 4.559% reaching 3-0 and 9.266% reaching 3-2.
- Confirmed full-count bias above is a direct BB-suppression mechanism: at 3-2, the code increases chase instead of using the three-ball take adjustment. An out-of-zone pitch that would be more likely taken at 3-0/3-1 becomes more likely swung at on 3-2.
- Neutral BB 8.060% is already below recent KBO ~9.07%; lower generated discipline further increases chase and suppresses BB, but ratings are an amplifier rather than the sole cause.

## HBP GAP
- `hit_by_pitch` is supported by public result enums, `BattingLine.record_pa`, inning force advancement, hitter HBP counting, pitcher HBP counting, aggregation and save-compatible stat fields.
- `HittingEngine.simulate_plate_appearance()` has no generation branch for HBP. Therefore production full-game HBP is structurally impossible and observed HBP=0 is an engine implementation gap.
- Minimal future HBP contract: resolve HBP immediately after pitch generation/location-risk evaluation and before swing/take/contact logic; terminal result `hit_by_pitch`; no AB, HBP +1, batter forced to first with existing walk/HBP force logic, RBI only on forced run, pitcher HBP +1. Any rate/model constants require 08 evidence + 05 validation and are not chosen in this audit.
- HBP must consume deterministic RNG only inside the canonical pitch stream so same-seed replay remains exact; existing stat serialization already supports HBP.

## HR ARCHITECTURE
- Eligible HR ball = non-ground, `depth == deep`; conversion uses only batted-ball `exit_quality`, fly/line multiplier, random draw, and a hard probability cap of .42.
- Exit quality already embeds hitter power, contact quality, pitch hittability, pitcher movement effects and noise. Pitcher stuff/control influence upstream pitch/contact paths rather than a separate HR suppression stage.
- HR is intentionally resolved before catch defense. That is architecturally defensible for over-the-fence HR: normal fielder defense should not convert a true HR into an out.
- No park factor / fence geometry / venue environment exists in the HR decision. This is a fidelity gap, but absence of park variation cannot by itself prove why the league-average HR rate is high unless the implicit neutral park baseline is shown to be too homer-friendly.
- Current evidence favors B (eligible deep-air-ball -> HR conversion) as the main gameplay-path suspect, with A/C still possible upstream. 05 measured ~26.7% HR conversion among eligible deep air balls and near-invariant conversion across neutral/generated hitter populations. D is not supported as "defense omission"; park omission is a separate environment gap. Final empirical judgment remains dependent on 08 batted-ball/park references.

## RUN CONVERSION / RUNNER STATE
- Walk/HBP use correct force-advance semantics through `force_batter_to_first()`; HBP generation is missing.
- Single: runner on third scores automatically; runner on second attempts home using the second-to-home curve; runner on first attempts third only if third is free, otherwise advances to second.
- Double: runners on second/third score automatically; runner on first may score based on speed/recovery/depth; otherwise reaches third.
- Triple and HR score all existing runners.
- Sacrifice fly/tag-up and ground-out advancement exist through `natural_events.py`.
- ROE exists in production: catch failure on routine/easy chances can resolve to `reached_on_error`, and inning/stat accounting supports it.
- Important simplification: on a ground-ball out with a runner on first and <2 outs, production always enters the DP/force-out branch; if DP is not completed, the lead runner is retired and the batter occupies first. There is no alternate batter-out/runner-advances-to-second groundout branch. This can suppress some run-conversion sequences even if aggregate GDP is near realistic.
- `FIRST_TO_THIRD_OPP_RATE`, `SECOND_TO_HOME_OPP_RATE`, and `DP_OPP_RATE` remain validation-era parameters but the persistent inning resolver attempts eligible first-to-third / second-to-home / DP resolution directly from actual event state rather than sampling those opportunity constants. This is an intentional integration simplification that requires empirical event-rate validation, not silent retuning.

## OBSERVABILITY AUDIT
- 05 diagnostic note understates existing visibility. `ProductionGameResult.player_lines[*].batting_line` retains full `BattingLine`, including ROE, GDP, XBT, XBT_attempts, first_to_third, second_to_home and SF.
- The reduced `PlayerGameLine.stats -> HitterCountingStats` adapter omits ROE/XBT/first-to-third/second-to-home. The diagnostic used that reduced adapter, which is why those counters appeared unavailable.
- Therefore ROE/XBT/first-to-third/second-to-home can be measured now without changing gameplay by reading `line.batting_line` directly.
- LOB and base-state-specific scoring/conversion are genuinely not exposed in final result payloads. Minimal future observability should snapshot per-event base occupancy/outs/runs before and after resolution or add a diagnostic-only engine observer; it must not consume RNG or mutate gameplay state.
- No instrumentation code PR was created in this audit because the highest-value missing counters (ROE/XBT/first-to-third/second-to-home) already exist in `BattingLine`. First rerun 05 with the correct source object; only add LOB/base-state instrumentation if that still leaves the run-conversion root cause unresolved.

## ENGINE DEFECT VS CALIBRATION
- Confirmed engine implementation gap: HBP cannot be generated.
- Confirmed count-composition defect/bias candidate: 3-2 ignores the three-ball take modifier because two-strike modifier takes precedence.
- K/BB absolute rates also depend on calibrated strike, swing/chase, contact, foul and rating distributions; no probability constant is changed here.
- HR-high is not caused by missing doubles/triples. Architecture supports them. Conditional HR conversion is the leading gameplay calibration suspect; park model is absent but not proven to explain the mean excess.
- Run-low is composite: missing HBP + low BB + high K are confirmed contributors; groundout/runner-sequencing simplifications and exact LOB contribution need direct measurement.

## REQUESTS TO 05
1. Rerun full-game aggregation reading `PlayerGameLine.batting_line` directly and report ROE/game, XBT attempts/success, first-to-third attempts/success, second-to-home attempts/success, GDP/eligible-groundout context where measurable, SF/tag-up attempts/success.
2. Extend PA trace by count: for every count, zone%, swing%, chase%, contact%, whiff%, foul%, terminal K/BB/BIP; specifically compare 3-0, 3-1, 3-2 and all two-strike counts.
3. Report full-count out-of-zone pitch outcomes: take->BB, swing->foul/BIP/whiff-K.
4. Report HR pipeline denominators: BIP -> air ball -> deep air ball -> HR, split fly/line and exit-quality buckets.
5. If run conversion remains unexplained after existing BattingLine counters, add RNG-free diagnostic snapshots for pre/post base occupancy + outs + runs to derive LOB and base-state scoring matrices.

## REQUESTS TO 08
1. Recent KBO count-specific swing/chase/contact/whiff/called-strike references, especially two-strike and full-count behavior.
2. Looking-K vs swinging-K share under matched definition.
3. HBP per PA/game and, if available, pitcher/batter handedness and control/location correlates for a future HBP model.
4. HR per BIP, fly/line/deep-air-ball HR conversion, launch/contact-quality proxy distributions and park-factor / venue HR variation.
5. Runner advancement: first-to-third on singles, second-to-home on singles, first-to-home on doubles, tag-up scoring, GDP opportunity/completion, ROE, LOB and runs-per-baserunner/base-state references.

## QUESTIONS TO 02
1. For mature production KBO rosters, what are PA-weighted distributions of Contact, Discipline, Power and Speed, not age-18 `Player.random` only?
2. What fraction of PA is taken by hitters with Discipline <100 / Contact <100 / Power >100, and how does that differ by lineup role/age?
3. Does raw 100 represent a neutral KBO regular for each hitting skill, or only a generator reference point? Current 02 status already says raw 100 has no universal percentile semantics.
4. Provide neutral-vs-mature-population sensitivity inputs without recentering ratings so 01/05 can separate formula bias from roster-distribution bias.

## BLOCKERS
- Matched KBO count-state and deep-air-ball HR conversion references from 08.
- Mature production roster PA-weighted rating distributions from 02.
- LOB/base-state conversion measurement if existing BattingLine counters do not close the run-conversion gap.

## RELATED_EVIDENCE
- 05 offense diagnostic: Actions run 34580783735, source 21a7621763a85268a4e2fb68cad9194854c4c601.
- 08 recent KBO comparison: runs -15.4%, hits +0.8%, HR +30.3%, BB -11.4%, K +12.5% versus completed 2022-2025 mean.

## GATES
- K_ENGINE_BIAS = WATCH
- BB_ENGINE_BIAS = WATCH
- HBP_PATH = MISSING
- HR_CONVERSION_PATH = WATCH
- RUNNER_ADVANCEMENT = WATCH
- GAMEPLAY_TUNING_ALLOWED = NO
