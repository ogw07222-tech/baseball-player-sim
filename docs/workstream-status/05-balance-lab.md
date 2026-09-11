# 05 - Balance Lab

WORKSTREAM: 05 - Balance Lab
UPDATED_AT: 2026-09-11
SOURCE_OF_TRUTH: task-start main@2fadd1e2295cdb42b8da70adb845c4b1fa9d9a20; diagnostic run@21a7621763a85268a4e2fb68cad9194854c4c601
STATE: DONE
CURRENT_TASK: Expanded Offensive + Pitch Outcome Decomposition
RESULT: DIAGNOSTIC_COMPLETE_WITH_RUNNER_STATE_GAPS

## EXECUTION
- Validation only; no gameplay/rating/growth/event/pitcher-usage probability constant changed.
- Added `tools/offense_pitch_diagnostic.py`, which observes the production `HittingEngine` call path through a subclass and uses `ProductionGameProvider` directly for full games.
- First Actions run `34580650741` failed before useful simulation measurement because the diagnostic assumed `ROE` existed on `HitterCountingStats`; classified as harness/schema failure only.
- Corrected schema-only instrumentation and completed Actions run `34580783735` on exact checkout `21a7621763a85268a4e2fb68cad9194854c4c601`.
- Parameters: canonical seed `20260906`; 10,000 neutral full games; 200,000 neutral hitter-vs-neutral pitcher PAs; 200,000 `Player.random` prospect-hitter-vs-neutral-pitcher PAs.
- Artifact: `heavy-validation-34580783735-21a7621763a85268a4e2fb68cad9194854c4c601`, artifact ID `10191530907`.
- Heavy workflow was restored to manual `workflow_dispatch` only after the run; reusable suite `offense_diag` remains available.

## HIT_TYPE_DECOMPOSITION_10K
- Totals: PA 773,202; AB 708,945; H 183,810; 1B 131,253; 2B 30,090; 3B 1,491; HR 20,976; XBH 52,557; TB 279,810; R 81,360; RBI 81,199; BB 62,906; SO 165,189; HBP 0; GDP 10,289; SF 1,351.
- Identity `H = 1B + 2B + 3B + HR` = PASS.
- 1B/PA 16.975%; 2B/PA 3.892%; 3B/PA 0.193%; HR/PA 2.713%; XBH/PA 6.797%; XBH/H 28.593%; TB/H 1.5223.
- AVG .2593; SLG .3947; ISO .1354.
- Game distributions: runs P10/P25/P50/P75/P90/P95/P99 = 3/5/8/11/14/16/20; hits = 12/15/18/22/25/27/32; HR = 0/1/2/3/4/5/6; BB = 3/4/6/8/10/11/13; K = 12/14/16/19/21/23/26; PA = 68/72/77/82/87/91/99.

## XBH_CODE_AUDIT
- Distinct `single`, `double`, `triple`, `home_run` outcomes exist in the production HittingEngine and inning/base resolver.
- HR is resolved first from deep non-ground contact using exit quality; non-HR hits then enter explicit 1B/2B/3B candidate generation.
- 2B candidate probability uses contact quality, exit quality, depth, and line-drive state; 3B candidate requires deep gap contact and sufficient exit quality. Speed can stretch singles, downgrade slow doubles, and convert candidates to triples.
- Defense/catch resolution occurs after HR determination, so a ball already classified as HR is not suppressed by field defense. No park factor exists in the audited HR decision path.
- Neutral 200k PA trace: raw 1B candidates 32,406; raw 2B candidates 9,516; raw 3B candidates 155; resolved 1B 33,742; 2B 7,955; 3B 380. The engine is not single/HR-only.

## RUN_CONVERSION
- R/H 0.44263; R/PA 0.105225; R/XBH 1.5480; TB/R 3.4392.
- Recent 2022-25 KBO aggregate reference gives approximate R/H 0.5273 and R/PA 0.12285; simulation is ~16.1% lower in runs per hit and ~14.3% lower in runs per PA.
- GDP = 1.0289/game; SF = 0.1351/game = ~1.048 per 600 PA.
- HBP = 0/game while 08's recent KBO mean is ~1.044 HBP/game. The production HittingEngine PA path currently has no HBP-generating branch despite counting-stat support, so this is a concrete missing on-base/run-conversion pathway.
- ProductionGameResult exposes GDP/SF but not ROE/XBT/first-to-third/second-to-home/LOB. Exact base-state-specific advancement and LOB diagnosis therefore remains OPEN rather than inferred.

## PITCH_STRUCTURE_NEUTRAL_200K
- PA 200,000; pitches 641,552; in-zone 353,808; out-of-zone 287,744.
- Zone rate 55.149%; first-pitch in-zone 55.10%.
- Swings 304,564 (47.473%); takes 336,988 (52.527%).
- In-zone swing 68.797%; out-of-zone swing/chase 21.253%.
- Called strikes 110,398 = 17.208%/pitch; swinging strikes 83,405 = 13.001%/pitch; fouls 79,773 = 12.434%/pitch; balls in play 141,386 = 22.038%/pitch.
- Contact on swing 72.615%; whiff on swing 27.385%; in-zone contact 74.644%; out-zone contact 64.540%.
- 0-2 reached 18.299%; 3-0 reached 4.559%; 3-2 reached 9.266%.
- PA outcomes: BB 8.060%; K 21.247%; HR 2.737%; H/PA 24.050%; 2B/PA 3.978%; 3B/PA 0.190%.
- K split: swinging 45.57%; looking 54.43%.
- HR/BIP 3.872%; HR among eligible deep air balls 26.663%.

## TWO_POPULATION_DIAGNOSTIC
- Neutral hitter 100 vs neutral pitcher 100: zone 55.149%, swing 47.473%, chase 21.253%, whiff 27.385%, BB 8.060%, K 21.247%, HR 2.737%, H/PA 24.050%, 2B/PA 3.978%, 3B/PA 0.190%.
- `Player.random` prospect hitters vs neutral pitcher 100: zone 54.989%, swing 50.730%, chase 33.569%, whiff 30.799%, BB 4.984%, K 26.067%, HR 1.526%, H/PA 16.894%, 2B/PA 2.591%, 3B/PA 0.085%.
- The generated-prospect trace is an isolation diagnostic, not a claim that it equals a mature KBO roster population. It shows rating distribution can strongly amplify chase/K and suppress BB/contact, while zone rate is unchanged.
- HR conditional conversion among eligible deep air balls is nearly population-invariant: neutral 26.663% vs generated 26.010%; the generated population's lower HR% comes mainly from producing fewer eligible deep air balls.

## ROOT_CAUSE_FINDINGS
- K_HIGH = composite. Neutral ratings alone already produce 21.247% K versus 18.76% recent KBO mean, so core engine behavior is sufficient to create the bias. Both called-strike and swinging-strike pathways contribute (54.4% looking / 45.6% swinging K). Lower-discipline/contact generated ratings further worsen chase, whiff, 0-2 counts, and K.
- BB_LOW = composite. Neutral ratings already produce 8.06% BB versus 9.07% KBO mean. PAs reach 3-0 only 4.56% and 3-2 9.27%; the strike/K pathways terminate many PAs before deep ball counts. Generated prospect discipline worsens this sharply via 33.57% chase and 4.98% BB.
- HR_HIGH = primarily gameplay HR conversion/contact-quality path, not absence of doubles/triples. Non-HR XBH are substantial and SLG is near the KBO mean, while neutral HR/PA 2.713% exceeds KBO 2.06%. HR is decided before defense and has no park factor in the audited path; eligible-deep-air-ball HR conversion is ~26.7%. Whether that conditional rate itself is empirically excessive requires 08 batted-ball/park reference data.
- RUNS_LOW = composite, but non-HR XBH shortage is not the leading explanation. Hits are realistic, SLG .395 is near recent KBO .390, and 2B/3B are explicitly present. Concrete contributors are missing HBP, low BB, and high K; remaining sequencing/LOB/base-state advancement contribution is OPEN because those denominators are not exposed by ProductionGameResult.

## STATUS
- EXTRA_BASE_HIT_STRUCTURE = WATCH: distinct and nontrivial 2B/3B paths exist; HR share is high and the HR-before-defense/no-park path needs empirical comparison.
- RUN_CONVERSION = FAIL: R/H and R/PA are materially low and HBP is structurally absent; exact sequencing/runner-state attribution remains partially OPEN.
- ZONE_RATE = OPEN: measured robustly at ~55.15%, but no matched KBO zone-rate reference is yet established here.
- SWING_RATE = OPEN: neutral 47.47% and generated 50.73% measured; matched KBO pitch-tracking reference needed.
- WHIFF_RATE = OPEN/WATCH: neutral 27.39% and generated 30.80% measured; high-K signal is consistent but exact KBO-aligned whiff benchmark is needed.
- CALLED_STRIKE_RATE = OPEN/WATCH: 17.21%/pitch neutral, 19.37% generated; contributes materially to looking K, but matched external baseline is needed.

## ROUTING
- 01 Gameplay Engine: inspect PA termination mix, HBP absence, HR-before-defense/no-park contract, and deeper event/base-state instrumentation; do not tune until design/reference review.
- 02 Ratings & Generation: generated-prospect discipline/contact distribution strongly amplifies chase/whiff/K and suppresses BB/H; determine whether mature production roster ratings share that distribution before attributing production realism bias to ratings.
- 03 Growth & Career: no direct defect identified in this diagnostic; only relevant if mature-career rating distributions are later shown to differ incorrectly from intended aging/growth outcomes.
- 08 Baseball Data & Research: obtain matched KBO zone%, swing%, chase%, contact%, whiff%, called-strike%, deep-air-ball/HR conversion, 2B/3B/XBH structure, GDP/SF/error/HBP, and runner-advancement/LOB baselines.

## GATES
- OFFENSE_PITCH_DIAGNOSTIC_EXECUTED = PASS
- HIT_TYPE_IDENTITY = PASS
- EXTRA_BASE_HIT_STRUCTURE = WATCH
- RUN_CONVERSION = FAIL
- ZONE_RATE = OPEN
- SWING_RATE = OPEN
- WHIFF_RATE = OPEN_WATCH
- CALLED_STRIKE_RATE = OPEN_WATCH
- PRODUCTION_CONSTANTS_CHANGED = NO
