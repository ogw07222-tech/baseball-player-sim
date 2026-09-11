# 05 - Balance Lab

WORKSTREAM: 05 - Balance Lab
UPDATED_AT: 2026-09-12
SOURCE_OF_TRUTH: pre-Phase2 gameplay main@584e5902d6187355631563fd0edb97a6e16483e9; Phase2A production-code checkpoint@d8b7efc40b150b987867e4240d0127f4bcaf09f3; latest Phase2A branch at final review@53687c952afdf39713a4be71f24a910eec0c62de; baseline validation@570cff4c6a9f8c27dabbf81fcc77a86f881c7b5d; candidate validation@be2763a3c55b6f47c1d6a15487bdc5fe507911ba
STATE: DONE
CURRENT_TASK: Physical Batted-Ball Phase 2 baseline lock and Phase 2A validation harness
RESULT: PASS_WITH_FAIR_FOUL_WATCH

## SOURCE_STATE
- Task-start latest integrated gameplay main: `584e5902d6187355631563fd0edb97a6e16483e9`.
- Phase 2A branch initially pointed to the same SHA, so the pre-Phase2 baseline was measured first.
- During validation, `feature/phase2a-physical-batted-ball` advanced. The frozen production-code checkpoint independently validated by 05 is `d8b7efc40b150b987867e4240d0127f4bcaf09f3`.
- The later branch merge `53687c952afdf39713a4be71f24a910eec0c62de` adds Phase-2A research/status documents only relative to `d8b7efc...`; production physical/gameplay code is unchanged.
- Current main at final status sync was `b5cf33fb3927aba1ab4b3d65b568d6fe019d5afb`; this is a research/status-doc advancement after the baseline gameplay SHA, not a gameplay-code change.

## PRE_PHASE2_BASELINE_LOCK
- Validation branch: `validation/phase2a-baseline-05`.
- Validation checkout: `570cff4c6a9f8c27dabbf81fcc77a86f881c7b5d` layered only validation tooling/workflow on main `584e5902...`.
- GitHub Actions run `34623088622`: SUCCESS.
- Artifact ID `10272893775`, digest `sha256:4c30bbc2b441711107720d475cff3d92057d3c7f27de538bba263d69e01a2459`.
- Seed `20260911`; neutral 200,000 PA; generated 200,000 PA; production 10,000 games; variance seeds `20260911/12/13` with 1,000 games each; performance probe 50,000 PA + 500 games.
- Compile, baseline/harness, Phase-1 deterministic/count regression, production-integration regression, artifact upload all PASS.

## PRE_PHASE2_PA_BASELINE
Neutral 200k:
- Zone 55.1162%; Swing 48.1686%; Z-Swing 70.3280%; Chase 20.9574%.
- Contact/Swing 77.2130%; Whiff/Swing 22.7870%.
- BB/PA 9.3990%; K/PA 17.8735%; HBP/PA 1.2965%.
- H/PA 24.2210%; HR/PA 2.7805%; Looking-K share 40.3978%.
- Pitches/PA 3.2499; called strike/pitch 16.3541%; swinging strike/pitch 10.9762%; foul/pitch 15.2130%; 2-strike foul/PA 13.5460%.

Generated 200k reference:
- Swing 49.3103%; Z-Swing 66.9739%; Chase 27.7058%; Contact/Swing 74.2415%; Whiff/Swing 25.7585%.
- BB 7.3195%; K 22.2465%; HBP 1.3365%; H/PA 17.5065%; HR/PA 1.5345%; Looking-K 41.1885%.

## PRE_PHASE2_PRODUCTION_10K
- PA/game 80.449; Runs/game 9.5594; Hits/game 19.3175; HR/game 2.1883; BB/game 7.6208; K/game 14.4689; HBP/game 1.0592.
- 1B/PA 17.1627%; 2B/PA 3.9442%; 3B/PA 0.1851%; HR/PA 2.7201%; H/PA 24.0121%.
- XBH/H 28.5249%; AVG .26978; SLG .40994; ISO .14016; BABIP .31081.
- ROE/PA 0.6571%; SF/PA 0.2042%; GDP/PA 1.4260%; XBT/PA 6.5839%; XBT success 45.3943%.

Per-game P5/P25/P50/P75/P95:
- Runs: 3 / 6 / 9 / 12 / 18.
- Hits: 11 / 16 / 19 / 23 / 29.
- HR: 0 / 1 / 2 / 3 / 5.
- K: 9 / 12 / 14 / 17 / 20.
- BB: 3 / 6 / 7 / 9 / 13.
- PA: 68 / 75 / 80 / 85 / 95.

Seed-to-seed 1k-game ranges:
- Runs/game 9.358-9.534; Hits/game 19.001-19.387; HR/game 2.138-2.240; BB/game 7.360-7.593; K/game 14.541-14.755.
- BB/PA 9.213-9.426%; K/PA 18.085-18.471%; HR/PA 2.654-2.804%.

## PHASE2A_CANDIDATE_VALIDATION
- Frozen production-code source: `d8b7efc40b150b987867e4240d0127f4bcaf09f3`.
- 05 validation branch: `validation/phase2a-candidate-05`; validation checkout `be2763a3c55b6f47c1d6a15487bdc5fe507911ba` adds validation-only tools/workflow.
- GitHub Actions run `34623705971`: SUCCESS.
- Artifact ID `10274050130`, digest `sha256:ee8b9040ad91807133fe287b13e91083f7d0869ee96e33de40f972fe864875e8`.
- Physical distribution probe, Phase-1 200k/10k regression, Phase2A unit tests, Phase1 count tests, production integration tests all PASS.
- Phase2A architecture is shadow-state only: `BattedBallState` is attached after legacy BIP contact; legacy HR/XBH/defense resolver remains authoritative. Physical generation fingerprints/forks parent RNG and does not consume the canonical RNG stream.

## PHASE2A_DISTRIBUTIONS
Production-path RHH sample: 200,000 PA -> 142,885 BattedBallState samples.

Exit velocity (mph):
- mean 84.056; SD 6.295.
- P1/P5/P25/P50/P75/P95/P99 = 68.963 / 73.570 / 79.864 / 84.158 / 88.356 / 94.225 / 98.329.
- min/max 53.772 / 111.248.
- No bound pileup or degenerate clustering observed.

Launch angle (deg):
- mean 9.950; SD 19.206.
- P1/P5/P25/P50/P75/P95/P99 = -35.400 / -21.768 / -2.876 / 10.034 / 22.888 / 41.464 / 54.400.
- min/max -65 / 85.
- Descriptive bins only, not calibration targets: <10 GB-like 49.93%; 10-25 LD-like 28.48%; 25-50 FB-like 19.78%; >=50 popup-like 1.80%.
- 10,760 unique values at 0.01-degree precision; no one-bin/category collapse.

Timing:
- mean -0.00077; SD 0.34168; P5/P50/P95 = -0.565 / -0.0002 / 0.561.
- late (<-0.20) 27.98%; on-time [-0.20,0.20] 44.15%; early (>0.20) 27.88%.
- lower/upper hard-bound pileup 0.188% / 0.181%: small tails, not mass collapse.

Spray (deg, center=0):
- mean 0.062; SD 17.636; P5/P25/P50/P75/P95 = -29.073 / -11.849 / 0.124 / 12.017 / 29.006.
- left (<-15) 19.69%; center [-15,15] 60.37%; right (>15) 19.93%.
- +/-75-degree boundary pileup about 0.0014% each: no boundary collapse.
- Early RHH timing mean spray -14.093 vs late +14.075: expected pull/opposite tendency is present.

Handedness:
- LHH quarter production sample has mirrored directional tendency: early +13.908 vs late -14.097.
- Direct same-state mirror probe: max and mean `abs(R spray + L spray)` = 0.0; fair rate identical 99.505% in the paired direct sample.

Fair/foul shadow field:
- Production R sample fair 98.967%, foul 1.033%; L sample fair 98.851%, foul 1.149%.
- This is NOT a league contact fair/foul estimate because Phase2A state is generated only after legacy contact resolution has already classified the pitch as BIP. It is therefore a conditional shadow-state diagnostic and remains WATCH before any later stage makes physical `is_fair` authoritative.

## SENSITIVITY
20,000-state controlled populations:
- Power 70 -> 140: EV mean +7.000 mph and P95 +7.000 mph. Direction is monotonic and not sign-reversed.
- Contact 70 -> 140: timing SD 0.3773 -> 0.2763. Higher contact narrows timing spread without flipping distribution semantics.
- RHH inside vs outside: mean spray -12.367 vs +12.323 degrees. Directional tendency is strong and correctly ordered under the current convention.
- Handedness mirror is exact in controlled same-seed probes.

## PHASE1_REGRESSION
- Candidate Phase2A run reproduces the locked pre-Phase2 offense baseline exactly for the same seed/sample harness: neutral/generated PA rates, production 10k totals/rates/distributions, and 3-seed variance rows are identical.
- Therefore Swing, Z-Swing, Chase, BB, K, HBP, Looking-K, H/HR, Runs/game and 1B/2B/3B did not move at all in this shadow-state checkpoint.
- This confirms the child-RNG design did not perturb unrelated canonical PA/game paths.
- Dedicated Phase1 count regression and targeted production-integration suites also PASS.

## DETERMINISM
Pre-Phase2 baseline:
- duplicate neutral 20k PA result object = exact equal.
- duplicate 250 full games = exact equal.

Phase2A candidate:
- duplicate 20k production PA physical-state sequence = exact equal (`14,271` generated states).
- corresponding final PA result-count aggregate = exact equal.
- duplicate Phase1 20k and full 250-game harness = exact equal.
- Existing production save/load/integration tests PASS. A dedicated serialized mid-game BattedBallState save/load contract does not exist because the state is transient within a PA; no new save schema was introduced.

## PERFORMANCE
Shared GitHub runner measurements; use as relative evidence, not a hard deterministic benchmark:
- Pre-Phase2: 50k PA = 2.7492 s = 54.984 us/PA; 500 games = 3.2970 s = 6.594 ms/game; 144-game extrapolation = 0.950 s.
- Phase2A: 50k PA = 2.8085 s = 56.170 us/PA; 500 games = 2.9296 s = 5.859 ms/game; 144-game extrapolation = 0.844 s.
- PA microbenchmark delta +2.16%; game benchmark delta -11.14% (faster, indicating shared-runner noise dominates at game scale).
- No evidence of a material runtime regression. Phase2A generator is constant-time and its dedicated unit performance guard also PASSes.

## GATES
- PRE_PHASE2_BASELINE_LOCKED = PASS
- EV_DISTRIBUTION = PASS
- LA_DISTRIBUTION = PASS_WITH_WATCH_FOR_EXTERNAL_REALISM_CALIBRATION
- TIMING_DISTRIBUTION = PASS
- SPRAY_DISTRIBUTION = PASS
- FAIR_FOUL = WATCH
- PHASE1_REGRESSION = PASS
- DETERMINISM = PASS
- PERFORMANCE = PASS

## PHASE2A_VALIDATION
- PHASE2A_VALIDATION = PASS.
- Structural distributions are continuous/non-degenerate; sensitivity directions are correct; handedness mirror sanity passes; canonical RNG/output is unchanged; performance impact is small/noisy.
- EV/LA absolute realism is not declared calibrated: Phase2A parameters explicitly remain provisional and should be compared against the research reference pack before later authoritative outcome migration.
- FAIR_FOUL is the only explicit WATCH because the production-path sample is conditioned on the legacy BIP classifier.

## PHASE2B_ALLOWED
- PHASE2B_ALLOWED = YES.
- This means Phase2B design/implementation may proceed. It does NOT authorize making the current Phase2A `is_fair` field authoritative without first defining where physical fair/foul classification sits relative to legacy foul resolution.
- Do not tune EV/LA/spray coefficients, ratings, or HR/2B/3B outcome constants from this validation alone.

## HANDOFF_TO_01
MEASURED:
- Phase2A physical state distributions are non-degenerate and structurally monotonic.
- Phase1 offense environment is exact-identical under fixed seed because physical generation does not consume canonical RNG.
- Runtime shows only +2.16% in the PA microprobe and no game-level slowdown signal.
- Physical `is_fair` is ~99% fair on production-attached states because those states are created only after legacy `contact_result == BIP`.

ROOT_CAUSE_HYPOTHESIS / DESIGN WATCH:
- `is_fair` currently describes a shadow spray-derived property of an already legacy-fair BIP population; it is not an all-contact fair/foul classifier. This is expected for Phase2A non-authoritative wiring but would become a semantic error if later used as an authoritative foul decision without moving/duplicating state generation before legacy foul filtering.

HANDOFF:
- 01 may proceed to Phase2B.
- Preserve the child-RNG/no-canonical-RNG-consumption contract until an explicit migration decision says otherwise.
- Before any stage routes real outcomes through physical fair/foul, explicitly define pre/post-legacy-foul placement and add all-contact/count-split fair/foul validation.
- Keep EV/LA/spray coefficient calibration separate from resolver migration; 05 found no evidence requiring tuning in Phase2A.
