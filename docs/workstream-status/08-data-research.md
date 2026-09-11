# 08 - Baseball Data & Research

WORKSTREAM: 08 - Baseball Data & Research
UPDATED_AT: 2026-09-11
SOURCE_OF_TRUTH: main@dc664631905c38a768820eb2dd6876f5ef3f8b6c
STATE: ACTIVE
CURRENT_TASK: KBO Pitch / Batted-Ball / Run-Conversion Reference Pack
RESULT: FAIL_WATCH_WITH_STRONG_REFERENCE_FINDINGS_AND_OPEN_TRACKING_GAPS

## LAST_COMPLETED
- Public data provenance/usage policy and detailed dataset provenance matrix remain in place.
- `docs/kbo-shared-evidence-baseline.md` provides common 02/03/04/05 references.
- `docs/kbo-roster-age-pitcher-workload-baseline.md` and pass2 provide roster/workload evidence.
- `docs/kbo-simulation-realism-comparison-2026-09-11.md` compares the canonical full-game environment against completed 2022-2025 KBO.
- Added `docs/kbo-pitch-batted-ball-run-conversion-reference.md` with pitch-tracking, XBH/power, HBP/GDP/SF/error, run-conversion, park-effect, and owner-routing evidence.

## SIMULATION_SOURCE
- 05 Balance Lab expanded offense/pitch diagnostic: Actions run `34580783735`, checkout `21a7621763a85268a4e2fb68cad9194854c4c601`, seed `20260906`.
- Samples: 10,000 neutral full games; 200,000 neutral hitter-vs-neutral pitcher PAs; 200,000 `Player.random` prospect hitter-vs-neutral pitcher PAs.
- Neutral pitch structure: zone 55.149%, swing 47.473%, chase 21.253%, Z-swing 68.797%, whiff/swing 27.385%, contact/swing 72.615%, Z-contact 74.644%, O-contact 64.540%, called strike/pitch 17.208%, BB 8.060%, K 21.247%, HR/PA 2.737%, looking-K share 54.43%.
- Generated prospect trace: chase 33.569%, whiff 30.799%, BB 4.984%, K 26.067%.
- 10k event structure: HBP 0, GDP 1.0289/game, SF 0.1351/game, R/H .44263, R/PA .105225, 2B/PA 3.892%, 3B/PA .193%, HR/PA 2.713%, XBH/H 28.593%, TB/H 1.5223, ISO .1354.

## CURRENT_FINDINGS
- Completed 2022-2025 KBO aggregate references: HBP/game ~1.044; HBP/PA ~1.33%; GDP/game ~1.426; SF/game ~0.655; errors/game ~1.529; 2B/PA ~4.02%; 3B/PA ~0.38%; HR/PA ~2.06%; XBH/H ~27.71%; TB/H ~1.470; ISO ~.125; R/H ~.5268; R/PA ~.1228.
- Simulation 2B/PA is close (-3.2%) and XBH/H is close (+3.2%) -> PASS.
- Simulation 3B/PA is ~49% low -> FAIL; HR/PA is ~31.7% high -> FAIL. Power structure is skewed toward HR rather than suffering a generic XBH shortage.
- HBP is structurally absent versus recent KBO ~1.04/game / ~1.33% of PA -> FAIL. It is a material missing on-base path but cannot by itself be assigned the full run-scoring deficit without KBO-specific run expectancy or sensitivity evidence.
- GDP is ~28% low -> FAIL/WATCH; SF is ~79% low -> FAIL. Error/ROE comparison remains OPEN because 05 does not expose them.
- R/H is ~16% low and R/PA ~14.3% low -> RUN_CONVERSION FAIL remains confirmed.
- No definition-aligned public recent KBO league aggregate was recovered for first-to-third, second-to-home, first-to-home on double, XBT, advancement-on-outs, or SF opportunity conversion. Baserunning attribution remains OPEN.
- Best currently available KBO plate-discipline reference is 2026 in-progress secondary pitch tracking: roughly Swing 44.8%, Chase 26.7-27%, Z-Swing 64.3%, Whiff/swing 21%, Z-Contact 86.9% over the current tracked environment. This is not a completed official season aggregate.
- Neutral Swing 47.47% is moderately high -> WATCH; neutral Chase 21.25% is low -> WATCH; generated Chase 33.57% is high -> FAIL; neutral Whiff 27.39% is high -> FAIL/WATCH; neutral Z-Contact 74.64% is materially low -> FAIL.
- Direct league Zone% was not recovered. An algebraically implied ~48% from current separately averaged swing/chase/Z-swing values suggests neutral 55.15% may be high, but definition/weighting mismatch keeps ZONE_RATE at OPEN/WATCH.
- No matched KBO aggregate was recovered for SwStr%, called-strike%, CSW%, first-pitch strike%, 0-2/3-0/3-2 reached rates.
- Recent 2025 KBO-attributed team evidence shows KIA led the league in looking strikeouts with 306 of 1,128 strikeouts looking (~27.1%) at the cited snapshot. Simulation looking-K share 54.43% is unsupported and roughly double even that high-looking-K team share -> strong FAIL signal.
- Simulation eligible-deep-air-ball -> HR conversion 26.66% has no definition-aligned KBO public counterpart. Direct comparison remains OPEN; HR/PA and approximately aligned HR/BIP proxies are high.
- KBO play-by-play batted-ball type data show 2022-2025 approximate GB/FB structure, but type coverage is only ~70-74%, out-heavy, and not comparable to launch-angle tracking; use as trend context only.
- Park effects are materially large across KBO venues. Current run park-factor reference spans roughly 1.206 at Daejeon to .888 at Jamsil; historical/event-specific HR factors can be much wider. Park omission matters for team/player variance and tails but does not by itself explain a +31.7% league-average HR bias in a neutral league simulation.

## DEFINITION / SOURCE QUALITY
- High confidence: 2022-2025 HBP/GDP/SF/hit-type/run totals derived from completed KBO-sourced league/team aggregates; denominator definitions are explicit.
- Medium/low confidence: current 2026 pitch-tracking aggregate from a secondary KBO tracking presentation; season incomplete and aggregation may be qualified-hitter arithmetic rather than pitch-weighted league total.
- OPEN rather than guessed: completed-season official Zone/O-Swing/Z-Swing/Contact/CStr/CSW/F-Strike/count-reach aggregates; exact deep-air HR conversion; runner advancement transition rates.
- No MLB benchmark was substituted for unavailable KBO metrics.

## OWNER HANDOFF
- 01 Gameplay Engine: review HBP absence, looking-K share, low Z-contact/high whiff structure, HR-before-defense/no-park contract, low GDP/SF, and expose base-state transition/LOB/ROE/opportunity denominators before any tuning.
- 02 Ratings & Generation: neutral chase is low while raw generated prospects are high; neutral whiff already high. Compare a mature production-roster rating population under the same diagnostic before attributing production bias to rating generation.
- 05 Balance Lab: next measurement-only run should expose direct CSW, true first-pitch-strike result, called strikes on takes, HBP/ROE/error/LOB, GDP and SF opportunities, base-state transition counters, and stable deep-air HR eligibility denominator. No constant changes requested.
- 00 Game Design HQ: no immediate tuning decision. Cross-system design decision is needed only if explicit parks are added or a single calibration reference environment must be locked.

## BLOCKERS
- No completed 2022-2025 official league plate-discipline aggregate with all requested zone/swing/contact fields was recovered.
- Direct `eligible deep air ball -> HR` KBO metric does not exist in a definition-aligned public source recovered here.
- Public recent KBO runner-advancement transition aggregates were not recovered.
- Simulation error/ROE/LOB and opportunity-level GDP/SF/base-running counters are not yet exposed.

## OPEN_ITEMS
- Recover a licensed/authoritative completed-season KBO plate-discipline aggregate, preferably Sports Info Solutions/Sports2i or an official KBO tracking export, with explicit denominator definitions.
- Build KBO play-by-play aggregate runner transition probabilities if public-use conditions permit; retain only compact derived aggregates.
- Recover or derive recent completed-season LOB/team-game and SF/GDP opportunity rates under matched definitions.
- Obtain a stable recent HR park-factor pack or multi-year event-specific park factors if explicit park modeling is considered.

## NEXT_ACTION
- Highest value next step is a matched KBO plate-discipline source with completed-season Zone/O-Swing/Z-Swing/Contact/SwStr/CStr/CSW/F-Strike definitions. In parallel, 05 should expose runner-state/opportunity diagnostics so 08 can derive matching KBO transition references.

## RELATED_DOCS
- `docs/kbo-pitch-batted-ball-run-conversion-reference.md`
- `docs/kbo-simulation-realism-comparison-2026-09-11.md`
- `docs/kbo-shared-evidence-baseline.md`

## GATES
- PUBLIC_DATA_POLICY = PASS
- COMPLETED_KBO_BATTED_BALL_TOTALS = PASS
- KBO_PITCH_TRACKING_REFERENCE = PARTIAL_OPEN
- NEUTRAL_ZONE_RATE = OPEN_WATCH
- NEUTRAL_SWING_RATE = WATCH_HIGH
- NEUTRAL_CHASE_RATE = WATCH_LOW
- GENERATED_CHASE_RATE = FAIL_HIGH
- NEUTRAL_WHIFF_RATE = FAIL_WATCH_HIGH
- NEUTRAL_Z_CONTACT = FAIL_LOW
- LOOKING_K_SHARE = FAIL_HIGH
- SIM_2B_RATE = PASS
- SIM_3B_RATE = FAIL_LOW
- SIM_HR_RATE = FAIL_HIGH
- SIM_HBP = FAIL_MISSING
- SIM_GDP = FAIL_WATCH_LOW
- SIM_SF = FAIL_LOW
- RUN_CONVERSION = FAIL_LOW
- RUNNER_ADVANCEMENT_ATTRIBUTION = OPEN
- PARK_EFFECT_IMPORTANCE = PASS_FOR_DISTRIBUTION
- PARK_OMISSION_EXPLAINS_HR_PLUS_30 = NO
- KBO_PITCH_BATTED_BALL_RUN_CONVERSION_PACK = FAIL_WATCH_WITH_OPEN_GAPS
