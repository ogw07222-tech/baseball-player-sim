# Phase 2E-A ground travel / bounce / rollout reference

Access date: 2026-09-12 (Asia/Seoul)

Purpose: research/reference pack for `01 - Gameplay Engine` Phase 2E-A first-ground-impact -> representative bounce -> rollout -> final-location surrogate, and for `05 - Balance Lab` validation. Research only. No production gameplay coefficient, hit-type formula, or physical outcome authority is changed here.

Task-start source of truth: `main@18dfd017c0aeb2cbda0f29f31cea0bd4f0806bd1` (Phase 2D merged).

Runtime constraints assumed here:
- O(1) per BIP;
- no timestep/frame stepping;
- no repeated bounce loop;
- no numerical integration loop;
- no collision iteration;
- no field-mesh traversal;
- fixed algebra / small lookup / fixed branch table only.

Status labels:
- **VERIFIED**: strong empirical or peer-reviewed support for the stated claim/reference.
- **PARTIAL**: useful quantitative evidence exists but is not definition-identical to the desired runtime coefficient.
- **QUALITATIVE**: robust direction/order relationship but no justified scalar coefficient.
- **OPEN**: no sufficiently aligned public baseball value recovered.

---

## REFERENCE_STATUS

| Lane | Status | Summary |
|---|---|---|
| Surface-dependent baseball rebound/pace | **VERIFIED/PARTIAL** | Penn State baseball-field studies measured strong surface and incidence-angle effects on outbound speed after first impact |
| Natural grass vs skinned dirt ordering | **VERIFIED** | dirt/skinned infield plays faster than natural turf in controlled baseball tests |
| Exact normal/tangential baseball-ground restitution | **OPEN** | public field tests generally publish total pace/COR, not a universal horizontal/vertical decomposition |
| Spin effect on ground bounce | **QUALITATIVE** | friction/spin changes horizontal speed transfer and bounce regime; wet-grass baseball study confirms friction/incident-angle interaction |
| Baseball roll deceleration coefficient | **OPEN** | no modern KBO/MLB universal m/s^2 value recovered; field condition matters materially |
| Constant-deceleration rollout surrogate | **RECOMMENDED** | O(1), monotonic, easy to calibrate, physically interpretable via v^2 = v0^2 - 2 a d |
| One representative bounce | **RECOMMENDED** | preserves major ordering while avoiding repeated-contact simulation; exact bounce count is not modeled |
| Neutral surface V1 | **RECOMMENDED** | current project has no grass/dirt polygon map; coarse surface inference from radial depth alone would create false precision |
| KBO calibration | **OPEN** | no KBO-specific public post-impact pace/roll-distance pack recovered |

---

## IMPACT_PHYSICS

### Baseball-field surface pace evidence

Penn State baseball-field research developed the `Pennbounce` apparatus to fire real baseballs at playing surfaces at game-relevant speeds/angles and measure inbound/outbound speed. In this literature the reported `COR` / surface pace is effectively the ratio of outbound baseball speed to inbound speed for the tested impact, not a pure normal-component rigid-body restitution coefficient.

Useful quantitative references:

- Early controlled comparison: skinned infield surface pace around **0.598**, natural turfgrass around **0.378**, synthetic systems between them. Surface effect was highly significant and impact-angle effect was also significant.
- A broader field survey using a **25 deg impact angle** and ~90 mph test speed reported natural turfgrass mean surface pace around **0.4787** (range ~0.4285-0.5334 in the sampled fields), corresponding to roughly 53% speed loss across the first surface interaction.
- In the same survey context, infilled synthetic surfaces lost roughly 48% of initial speed and skinned surfaces roughly 43% at the 25 deg test condition.
- A dedicated non-turfed basepath study reported average surface pace around **0.562** at 25 deg, i.e. roughly 44% speed reduction.
- A later controlled natural-turf experiment reported mean COR/surface pace around **0.445 +/- 0.061**, showing substantial field-condition variability even within natural grass systems.

**Interpretation for Phase 2E-A:**
- first-ground impact should remove a large fraction of translational speed;
- surface type matters materially;
- impact angle matters;
- exact `horizontal_speed_retention = COR` is **not** justified because the published pace metric is not a clean horizontal component coefficient.

### Vertical vs horizontal loss

A baseball-ground impact couples normal restitution, friction, and spin. Public baseball-field pace work does not provide one universal pair `(e_vertical, retention_horizontal)` that can be safely copied into production.

A Korean experimental/physics analysis of wet grass found that horizontal-speed loss after baseball bounce depends on incident angle and surface friction, and that wet grass can preserve more horizontal speed for certain shallow impact angles. This supports a friction-regime effect rather than one universal horizontal multiplier.

Therefore:
- `vertical energy loss is large` -> **QUALITATIVE/strong**;
- `horizontal speed is also substantially reduced, with surface/angle dependence` -> **VERIFIED structural**;
- exact KBO vertical/tangential coefficients -> **OPEN**.

### Spin

Topspin/backspin changes the tangential contact state and therefore horizontal-speed transfer/bounce behavior. Baseball-specific public ground-impact coefficient surfaces were not recovered, so Phase 2E-A should not introduce a spin-resolved contact solver.

Research implication:
- spin can be represented implicitly through trajectory/batted-ball class if needed;
- do not claim a fixed topspin/backspin coefficient without source support;
- explicit spin should remain future calibration, not a V1 blocker.

---

## IMPACT_SPEED_PROXY

Current constraint: Phase 2B does not store explicit velocity-at-impact.

### Candidate A — `EV * cos(LA) * fixed aerodynamic retention`

- Complexity: O(1), trivial.
- Realism: low-medium.
- Strength: monotonic in EV for fixed LA.
- Weakness: one retention factor cannot represent short grounders and long/high flights; drag loss depends strongly on flight duration/trajectory.
- Recommendation: **not primary**.

### Candidate B — `first_impact_distance / hang_time` average horizontal speed, then fixed correction

- Complexity: O(1), one division + small correction lookup/branch.
- Realism: medium-high for this project because it uses the realized canonical Phase 2B distance/time rather than reconstructing a second trajectory.
- Strength: automatically remains coupled to current Phase 2B trajectory output and atmosphere surrogate.
- Weakness: average horizontal speed is greater than terminal horizontal speed when drag slows the ball, so a downward correction is required.
- Monotonicity: generally good if correction is constrained positive/monotonic.
- Calibration: straightforward from offline trajectory examples later.
- Recommendation: **PRIMARY**.

### Candidate C — trajectory-class retained-speed multiplier

- Complexity: O(1), fixed branch.
- Realism: medium-low.
- Weakness: discontinuities at class boundaries and insufficient EV/LA resolution.
- Recommendation: bootstrap fallback only.

### Candidate D — small EV x LA impact-speed surface

- Complexity: O(1), fixed bilinear lookup.
- Realism: high if generated from a trusted offline trajectory model.
- Weakness: can diverge from the actual Phase 2B realized carry/hang output if maintained independently.
- Recommendation: good future calibration layer, but less desirable than B for initial canonical consistency.

### Research recommendation

**RECOMMENDED_IMPACT_SPEED_MODEL:**

`v_impact_horizontal_proxy = (first_impact_distance / max(hang_time, epsilon)) * impact_speed_correction(class or small LA bucket)`

where the correction is explicitly a calibration parameter/small lookup and not set by 08.

Rationale:
- uses already-produced Phase 2B state;
- fixed O(1) arithmetic;
- avoids a second independent flight model;
- preserves smooth dependence on realized trajectory;
- can later be replaced/refined by an EV x LA correction surface without interface breakage.

If Phase 2B later exposes an O(1) impact-velocity descriptor directly, that should supersede this proxy.

---

## BOUNCE_MODEL

### Why one representative bounce is defensible

Real baseball ground travel may contain multiple bounces/sliding/rolling transitions, but the gameplay-relevant ordering is dominated by:
1. incoming horizontal speed;
2. surface pace / energy loss on first major impact;
3. impact angle / trajectory class;
4. remaining rollout resistance.

Penn State results show the **first surface interaction alone** commonly removes ~40-60% of speed under representative test conditions, making that first impact the dominant discrete event for a lightweight surrogate.

### Recommended one-bounce state

Inputs:
- `v_impact_horizontal_proxy`;
- trajectory class / incoming LA or impact-angle proxy;
- neutral `surface_pace` parameter;
- optional fixed bounce-shape class.

Outputs:
- `post_impact_horizontal_speed`;
- `bounce_distance`;
- `rollout_start_speed`;
- then analytical rollout.

Recommended architecture:

`post_impact_horizontal_speed = v_impact_horizontal_proxy * retained_speed(surface, impact_class)`

`bounce_distance = fixed_bounce_distance_surface(v_impact_horizontal_proxy, impact_class)`

`rollout_start_speed = post_impact_horizontal_speed * post_bounce_roll_retention(impact_class)`

The two latter functions may be tiny fixed lookup surfaces / fitted algebraic surrogates. No bounce loop is needed.

Do **not** copy the Pennbounce 0.38-0.60 surface-pace values directly into `horizontal retained_speed`; use them only as order-of-magnitude evidence that the first impact should have a large effect.

### Ball-type ordering

Expected ordering at equal first-impact location is not identical across ball types because incoming speed and angle differ:

- **hard grounder:** high horizontal component, shallow impact; can retain meaningful pace after bounce and travel far;
- **soft grounder:** low horizontal component; short post-impact travel;
- **line-drive first bounce:** often high total speed but steeper than a classic grounder; substantial rebound/roll possible, surface loss larger than a shallow skimmer depending on impact regime;
- **fly-ball landing:** lower horizontal speed at impact relative to initial EV and steeper descent; bounce may be visible but rollout typically less than a hard grounder of similar initial EV;
- **popup landing:** low horizontal component, steep impact, typically short horizontal travel after landing.

This is **QUALITATIVE structural evidence**, not a sourced league ordering table.

---

## ROLLOUT_MODEL

### Candidate A — constant deceleration

Use:

`v^2 = v0^2 - 2 a d`

so stop distance is:

`d_roll = v0^2 / (2 a_roll)`

Pros:
- O(1);
- no loop/integration;
- monotonic by construction;
- physically interpretable as an effective rolling/sliding resistance;
- easy to calibrate to future observed stopping-distance data;
- stable for large season simulations.

Cons:
- real turf resistance is speed-, moisture-, grass-, spin-, and slip-state dependent;
- `a_roll` is an effective gameplay parameter, not a universal physical constant.

**Recommendation: PRIMARY.**

### Candidate B — fixed retained-distance multiplier

Pros: cheapest possible.
Cons: weak physics; does not preserve the natural quadratic dependence of stopping distance on initial speed; difficult to reason about extremes.
Recommendation: reject as primary.

### Candidate C — small lookup surface

Pros: can encode nonlinearity/surface effects while remaining O(1).
Cons: needs calibration data not currently available for KBO.
Recommendation: future refinement.

### Candidate D — other analytical surrogate

A combined `d_roll = alpha * v0^2 + beta * v0` can be fit later while preserving O(1), but without calibration data it adds unjustified degrees of freedom.

### Research recommendation

**RECOMMENDED_ROLLOUT_MODEL = constant effective deceleration.**

`a_roll` remains a calibration parameter. No authoritative KBO/MLB universal baseball roll deceleration in m/s^2 was recovered; therefore exact numeric tuning is **OPEN**.

---

## BALL_TYPE_EFFECTS

Phase 2E-A should reuse the following Phase 2B outputs/state, in priority order:

1. **first impact distance** — canonical spatial starting point;
2. **hang time / time to first impact** — needed for impact-speed proxy B;
3. **EV and LA** — useful for sanity and correction bucket selection;
4. **trajectory class** — useful for fixed impact/bounce regime branches;
5. **spray direction** — determines final ground-travel vector.

`EV alone` is insufficient because two balls with the same initial EV but different LA/hang time can arrive at the ground with very different horizontal pace.

`first impact distance alone` is also insufficient because a soft flare and a hard liner can first land at a similar depth with very different incoming speed.

---

## SURFACE_EFFECTS

### Empirical evidence

Baseball-specific field testing consistently finds:
- natural grass slower than skinned dirt;
- synthetic turf generally intermediate/faster than natural turf depending system;
- surface hardness, compaction, moisture, thatch/rootzone condition can alter pace;
- wet-grass behavior can differ by impact angle because friction regimes change.

Thus surface class is physically meaningful.

### Phase 2E-A V1 decision

The project currently lacks a reliable grass/dirt polygon map. Inferring surface only from radial landing depth would misclassify many infield/baseline/foul-territory locations and create fake precision.

Therefore:

**SURFACE_MODEL = NEUTRAL_V1**

with an interface reserved for future:

`surface_class: neutral | grass | dirt | synthetic`

When actual field-surface polygons or trustworthy coarse zones exist, grass/dirt can be added without changing the ground-travel contract.

A coarse surface class based solely on trajectory/landing depth is **not recommended** at this stage.

---

## WALL_BOUNDARY

Phase 2C already provides spray-dependent wall radius/height.

For Phase 2E-A ground travel, detailed wall rebound physics is unnecessary.

### A. Clamp final position at wall

Pros: simplest.
Cons: loses information about the fact that a wall contact occurred.

### B. Deterministic wall-stop state — **RECOMMENDED**

If unconstrained final radial distance exceeds the wall radius in that spray direction:
- set final radial position to the wall contact radius;
- set `wall_ground_contact = true`;
- terminate ground travel at wall;
- no rebound distance in V1.

Pros:
- O(1);
- stable;
- preserves a semantically useful state for Phase 2E-B retrieval/hit-type logic;
- avoids inventing wall-material restitution coefficients.

### C. Simple retained rebound distance

Pros: adds realism for caroms.
Cons: requires wall material/angle/geometry calibration and can change retrieval ordering significantly; no current KBO wall-rebound pack.

Recommendation: defer.

**WALL_GROUND_INTERACTION = deterministic wall-stop state.**

---

## RECOMMENDED_PHASE2E_A_MODEL

Research-only architecture:

1. Validate first-ground-impact state.
2. Compute incoming horizontal-speed proxy:
   `v_in = (first_impact_distance / hang_time) * impact_speed_correction`.
3. Apply one representative impact/bounce retention:
   `v_post = v_in * retained_speed(impact_class, neutral_surface)`.
4. Compute one fixed/algebraic bounce distance from a small class surface.
5. Set rollout-start speed.
6. Compute rollout analytically:
   `d_roll = v_roll^2 / (2 * a_roll)`.
7. `total_ground_travel = bounce_distance + d_roll`.
8. Advance along the existing spray unit vector.
9. If wall radius is crossed, clamp to wall and mark deterministic wall-stop state.
10. Return final location + travel diagnostics.

All steps are fixed-cost O(1). No runtime bounce/timestep loops are required.

Suggested observables:
- `impact_horizontal_speed_proxy`;
- `post_impact_horizontal_speed`;
- `bounce_distance`;
- `rollout_start_speed`;
- `rollout_distance`;
- `ground_travel_distance`;
- `final_ground_x/y`;
- `wall_ground_contact`;
- `surface_class`;
- `ground_model_version`.

---

## MONOTONICITY_REQUIREMENTS

Unless an explicit wall/boundary interaction intervenes:

- higher impact-horizontal-speed proxy -> **non-decreasing** total ground travel;
- higher retained-speed coefficient -> **non-decreasing** travel;
- higher effective rolling resistance/deceleration -> **non-increasing** rollout;
- identical mirrored spray -> identical travel magnitude with mirrored X coordinate;
- invalid/no first-ground-impact trajectory -> no valid Phase 2E-A ground state;
- all travel distances >= 0;
- final radial distance >= first-impact radial distance;
- wall-stop state may cap final radial distance at the wall;
- increasing initial speed must not produce shorter rollout under identical surface/class state;
- zero rollout-start speed -> zero rollout distance.

Potential exception:
- if a future model changes impact regime based on incident angle/spin, a faster incoming ball could enter a different bounce regime; V1 should avoid such discontinuous regime switches unless explicitly calibrated.

---

## VALIDATION_TARGETS

`05 - Balance Lab` should validate before tuning:

### Deterministic unit/sweep checks
- fixed LA/class, impact-speed sweep -> travel non-decreasing;
- fixed speed, retained-speed sweep -> travel non-decreasing;
- fixed speed, `a_roll` sweep -> rollout non-increasing;
- mirror spray -> equal scalar travel, mirrored X;
- zero/near-zero speed stability;
- extreme EV/LA inputs produce finite, non-negative outputs;
- invalid Phase 2B state does not create ground state;
- wall clamp never returns position beyond stadium wall.

### Distribution outputs
- `impact_horizontal_speed_proxy` percentiles by trajectory class;
- post-impact retained-speed ratio distribution;
- bounce distance distribution;
- rollout distance distribution;
- total ground travel distribution;
- final radial-depth distribution;
- wall-ground-contact rate;
- class splits: hard GB / soft GB / LD-first-bounce / FB landing / PU landing.

### Empirical sanity references
- first impact should commonly cause substantial speed loss; a neutral model that preserves ~95-100% of incoming speed on ordinary bounces is implausible relative to Penn State baseball-field testing;
- natural-grass-like fixture should play slower than skinned-dirt-like fixture if/when surface variants are added;
- surface sensitivity should be measurable but not interpreted as KBO-calibrated until KBO data exists.

No KBO league distance/roll target is currently available for hard PASS/FAIL.

---

## DATA_GAPS

1. KBO-specific baseball surface pace / rebound measurements.
2. KBO grass vs dirt vs artificial-turf ground-ball speed data.
3. Modern MLB/KBO post-impact horizontal-speed distributions.
4. Baseball rolling deceleration / stop-distance distributions in game conditions.
5. Spin-resolved baseball-ground impact surfaces.
6. Field-condition effects by moisture/temperature at professional parks.
7. Reliable infield/outfield surface polygons for current KBO parks.
8. Wall-carom restitution by stadium/wall type.

`KBO_CALIBRATION = OPEN`.

---

## SOURCES

### High-priority baseball-surface sources

1. Brosnan, McNitt, Schlossberg (2007), *An apparatus to evaluate the pace of baseball field playing surfaces*, Journal of Testing and Evaluation 35(6), 676-681. Penn State summary/PDF.
   - Measures real baseball inbound/outbound velocity across synthetic, natural turfgrass, and skinned infield surfaces at multiple velocities/angles.
   - Source: https://pure.psu.edu/en/publications/an-apparatus-to-evaluate-the-pace-of-baseball-field-playing-surfa/

2. Penn State / ASA-CSSA-SSSA conference abstract, *An Apparatus to Evaluate Ball Bounce on Baseball Field Playing Surfaces*.
   - Reports skinned infield COR/pace ~0.598, natural turfgrass ~0.378; significant surface and impact-angle effects.
   - Source: https://crops.confex.com/scisoc/2005am/techprogram/P4509.HTM

3. Penn State baseball field survey / annual report.
   - 25 deg / ~90 mph testing; natural turfgrass mean ~47.87% outbound/inbound speed, fastest ~53.339%, slowest ~42.853%; natural grass slower than infill and skinned surfaces.
   - Source: https://plantscience.psu.edu/research/centers/turf/research/annual-reports/2005/2005arr.pdf

4. Brosnan et al., non-turfed basepath surface characterization.
   - Average pace/COR ~0.562 at 25 deg; field soil composition and compaction effects.
   - Source: https://plantscience.psu.edu/research/centers/ssrc/documents/brosnannonturf.pdf

5. *Effects of Surface Conditions on Baseball Playing Surface Pace*, Journal of Testing and Evaluation.
   - Controlled natural-turf experiment mean COR ~0.445 +/- 0.061; synthetic systems roughly ~0.51-0.56 in listed treatments; demonstrates condition/system variability.

6. Korean physics experiment, *Difficulty of fielding a ground ball after rain*.
   - Shows horizontal-speed loss after baseball bounce depends on incident angle and grass friction; wet grass can shift the friction-regime boundary and preserve more speed for shallow impacts.
   - Source: https://www.kci.go.kr/kciportal/landing/article.kci?arti_id=ART002593565

### Supporting sources

7. Farlow (2018), *The Effects of Surface Pace in Baseball*, Linfield College physics thesis.
   - Reports larger energy loss on turf than dirt in its experiment and emphasizes kinetic-friction contribution; useful supporting evidence, lower authority than peer-reviewed Penn State work.
   - Source: https://digitalcommons.linfield.edu/physstud_theses/39/

8. Oklahoma State University Extension turfgrass curriculum.
   - General sports-turf principle: smoother surface allows farther ball roll; roll distance depends on mowing/conditions/weather.
   - Source: https://extension.okstate.edu/fact-sheets/turfgrass-a-middle-school-curriculum

---

## FINAL_DECISION

`PHASE2E_A_RESEARCH = READY`

`RECOMMENDED_IMPACT_SPEED_MODEL = FIRST_IMPACT_DISTANCE_DIV_HANG_TIME_WITH_SMALL_CALIBRATABLE_CORRECTION`

`RECOMMENDED_BOUNCE_MODEL = ONE_REPRESENTATIVE_BOUNCE_FIXED_ALGEBRA_OR_SMALL_LOOKUP`

`RECOMMENDED_ROLLOUT_MODEL = CONSTANT_EFFECTIVE_DECELERATION_V2_OVER_2A`

`SURFACE_MODEL = NEUTRAL_V1`

`WALL_GROUND_INTERACTION = DETERMINISTIC_WALL_STOP_AT_PHASE2C_RADIUS`

`KBO_CALIBRATION = OPEN`

`IMPLEMENTATION_HANDOFF_TO_01 = YES`
