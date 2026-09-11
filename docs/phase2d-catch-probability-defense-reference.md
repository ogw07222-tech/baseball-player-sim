# Phase 2D catch probability and defensive-range reference

Access date: 2026-09-12 (Asia/Seoul)

Purpose: research/reference pack for `01 - Gameplay Engine` Phase 2D defense abstraction and `05 - Balance Lab` validation. Research only; no production gameplay coefficient, rating mapping, or error probability is changed here.

Task-start source of truth: `main@9d406589d6c71a92fa91843047116200c12826b3`.

Runtime constraints assumed:
- no frame-by-frame fielder movement;
- no route/path simulation;
- no nearest-player search loop;
- fixed defender lookup;
- one probability evaluation;
- one RNG roll;
- O(1) per BIP.

Status labels:
- **VERIFIED**: strong official source/definition.
- **PARTIAL**: useful evidence exists but cannot be transferred directly to KBO coefficients.
- **QUALITATIVE**: monotonic/structural evidence without scalar calibration.
- **OPEN**: no suitable public reference recovered.

---

## REFERENCE_STATUS

| Lane | Status | Summary |
|---|---|---|
| MLB outfield Catch Probability structure | **VERIFIED** | distance needed, opportunity time, direction and wall proximity are official Statcast inputs |
| MLB outfield difficulty bins | **VERIFIED** | five-star catch-probability bands are public |
| MLB outfield player skill/range structure | **VERIFIED** | OAA accumulates actual result minus expected catch probability; Jump decomposes reaction/burst/route |
| MLB infield OAA structure | **VERIFIED** | intercept distance/time, throw/base distance and runner speed enter the model |
| KBO catch-probability surface | **OPEN** | no public KBO Statcast-equivalent play-level probability surface recovered |
| KBO range-based defense evidence | **PARTIAL** | official KBO Defense Award uses UZR/KUZR plus official records; raw probability surface is not public |
| O(1) phase-2D abstraction | **RESEARCH-READY** | nominal-position distance proxy + probability surface/logistic + rating shift satisfies constraints |

---

## STATCAST_CATCH_MODEL

### Official MLB outfield Catch Probability

MLB Statcast defines outfield Catch Probability from four primary components:

1. **Distance needed** — shortest/optimal distance from the outfielder's starting position to the catch point.
2. **Opportunity time** — time available to reach the ball.
3. **Direction** — movement direction matters; going back is harder than equivalent forward movement.
4. **Wall proximity/context** — near-wall opportunities receive an added difficulty adjustment.

The official model intentionally uses *distance needed*, not actual distance covered, so a bad route does not make the opportunity appear more difficult than it objectively was.

Official difficulty bands currently presented by Statcast:
- **5 Star:** 0-25% catch probability
- **4 Star:** 30-50%
- **3 Star:** 55-75%
- **2 Star:** 80-90%
- **1 Star:** 95%
- >95% is easier than the one-star bucket.

Since 2019 public Catch Probability is rounded/reported in 5-point bands because 1-percentage-point precision overstates model certainty.

### OAA relationship

Outfield OAA is the cumulative result of each opportunity relative to its Catch Probability:
- catching a 75% opportunity contributes +0.25 outs above average;
- missing it contributes -0.75.

This is important for Phase 2D architecture: **baseline BIP difficulty and defender skill are conceptually separable.** The probability surface should first represent average-player difficulty; player rating then shifts actual conversion around that baseline.

### Opportunity time definition caveat

Official Catch Probability opportunity time starts at pitch release rather than bat contact, allowing pre-contact reads/positioning information to matter. Phase 2D currently receives trajectory/hang time after contact, so it cannot reproduce that exact definition without an additional constant/read allowance.

Therefore:
- project `hang_time` is a valid dominant difficulty proxy;
- it is **not definition-identical** to Statcast `opportunity_time`;
- any constant conversion/read allowance is a future calibration parameter owned by 01/00.

---

## OUTFIELD_CATCH_FACTORS

### Strongly supported factors

For a no-movement-simulation engine, the strongest reduced variables are:

- `hang_time_s`
- `landing_x`, `landing_y` or equivalent depth + spray
- `nominal_fielder_start_x/y`
- derived `required_distance`
- movement direction class / depth relation
- wall proximity
- defender range/fielding rating

EV and LA matter primarily because they produce hang time, trajectory shape, and landing position. Once those physical outputs are available, **EV/LA should usually be secondary inputs**, not duplicate the same information at full strength.

### Why required-distance proxy is preferable to raw depth only

Statcast uses true player start positions. Phase 2D will not track them dynamically, but MLB publishes standard outfield positioning zones under neutral conditions:
- LF: approximately 260-320 ft from home and angle -33° to -21°;
- CF: approximately 280-350 ft and angle -8° to +7°;
- RF: approximately 260-320 ft and angle +21° to +33°;
with -45° the third-base foul line and +45° the first-base foul line.

This supports a **fixed nominal start anchor per OF position**. One Euclidean distance calculation from anchor to landing/catch point then provides an O(1) `required_distance_proxy`.

Advantages:
- preserves the actual Statcast difficulty logic better than `landing_depth` alone;
- no route simulation;
- no player search;
- easy handedness/spray handling because landing coordinates already exist;
- can later be park/strategy adjusted without changing the model contract.

### Direction adjustment

Statcast explicitly adjusts balls requiring the fielder to go back. The 360° space around the fielder is divided into six 60° sections; the official 'going back' region is the 60° wedge centered directly away from home plate.

Phase 2D does not need six public-facing direction classes, but a reduced categorical modifier is defensible:
- `in/toward_home`
- `lateral`
- `back/away_from_home`

Expected monotonicity:
- same time + same distance: `back` <= `lateral` <= `in` catch probability.

Exact multipliers remain **OPEN**.

### Wall proximity

Official MLB Catch Probability added wall difficulty in 2018. Example: a wall-adjacent Kevin Kiermaier play changed from ~49% under the old time/distance/direction model to ~6% after wall context was included.

Therefore wall context is too large to ignore completely when Phase 2C geometry is active.

Recommended Phase 2D input:
- `wall_distance_from_catch_point` or simple `near_wall:boolean/bucket`.

No full wall-collision simulation is required.

### Player skill / Jump evidence

MLB Statcast `Jump` decomposes outfield range into:
- **Reaction**: first ~1.5 s;
- **Burst**: next ~1.5 s;
- **Route**: directness over the first 3 s.

Elite seasonal Jump values have historically been roughly +3 to +4 ft above average, with current leaderboards also showing several feet of spread between strong and weak outfielders. This is evidence that defender skill should move conversion probability materially on borderline opportunities, but not overturn physical impossibilities.

Use: **MEDIUM confidence** for the statement `rating effect is meaningful near the decision boundary`; **LOW confidence** for any direct feet-per-rating mapping.

---

## INFIELD_GROUND_FACTORS

MLB official OAA treats infielders differently from outfielders. Inputs include:
- distance to the ball's intercept point;
- time available to get there;
- distance from intercept point to the target base;
- batter/runner Sprint Speed on force plays.

This confirms that an outfield fly-catch surface should **not** simply be reused for ground balls.

Phase 2D scope does not require rolling/bounce physics, so a reduced infield model can use:

- `spray_angle / landing-or-impact sector`
- `EV` or a transformed `ground_speed_class`
- `first_ground_impact_depth`
- fixed nominal IF sector/position
- defender fielding/range rating
- optional batter speed later if throw-to-first is modeled

### Ground-ball abstraction

Recommended decomposition:

`GB difficulty = function(direction_sector, EV/speed class, impact_depth, defender_position_role)`

then:

`P(out_on_grounder | average defender)`

followed by rating adjustment.

This is not intended to simulate ball rolling. It approximates whether the ground ball enters a fieldable region before becoming a hit.

### KBO evidence

KBO's official Defense Award explicitly uses a range-adjusted advanced metric developed with Sports2i:
- official fielding/range records are common inputs;
- infielders and outfielders receive adjusted KUZR/KBO UZR components;
- the correction uses additional data collected by official KBO scorers, including unrecorded exceptional plays and errors.

This strongly supports separating **range/coverage quality** from ordinary error accounting in the project, but the underlying KBO probability surface is not public.

KBO's public basic defense table provides errors, putouts, assists, double plays and fielding percentage. These are useful aggregate validation outcomes but not catch-difficulty calibration data.

---

## DEFENDER_RATING_EFFECT

The project should not map the current rating scale directly from this research pack. Required relationship only:

1. higher defender rating => non-decreasing catch/out probability for the same BIP;
2. rating effect is largest on intermediate-difficulty opportunities;
3. near-0% physically impossible plays should remain near 0 even for elite defenders;
4. near-100% routine plays should remain near 100 for most competent defenders;
5. rating should not materially alter trajectory or landing coordinates.

Confidence:
- monotonicity: **HIGH**
- strongest effect in middle probability bands: **MEDIUM-HIGH**
- exact probability-point shift per rating: **OPEN / LOW**
- direct conversion of Statcast Jump feet into project ratings: **NOT RECOMMENDED**

A logistic formulation naturally satisfies the 'largest marginal effect near the middle' requirement.

---

## POSITION_RESPONSIBILITY

### Outfield

Recommended fixed primary ownership sectors:
- LF: negative-angle left side
- CF: central band
- RF: positive-angle right side

But a hard three-sector cut creates discontinuities near LF/CF and CF/RF boundaries. Better options:

**Option A — fixed primary owner only**
- cheapest/simplest;
- exactly one defender lookup;
- discontinuous near boundaries.

**Option B — fixed primary owner + predeclared adjacent blend**
- still O(1);
- at sector edges, interpolate two defenders' effective range or choose a fixed best-of-two responsibility rule;
- smoother spatial behavior.

Research recommendation: **Option B**, with no search. Each location bucket knows its one or two eligible positions in advance.

Example concept:
- deep LF line -> LF only
- LF-CF gap -> LF/CF blended
- straight CF -> CF only
- RF-CF gap -> CF/RF blended
- RF line -> RF only

### Infield

Use a static angular/depth responsibility table, not nearest-player pathfinding:
- 3B side
- SS zone
- 2B zone
- 1B side

Gap/boundary buckets may similarly have two predetermined eligible defenders. Pitcher/catcher responsibility can remain outside Phase 2D V1 unless bunts/very short BIP need explicit handling.

### Why this is defensible

MLB OAA already reports defense by **field location role**, not merely lineup-card position, and Baseball Savant exposes granular role zones such as 'close to line', 'straight up' and infield holes. This supports a fixed location-role abstraction when exact starting positions are intentionally not simulated.

---

## RECOMMENDED_CATCH_MODEL

### Candidate A — single logistic function

Example architecture, not production coefficients:

`z = base_difficulty(time, required_distance, direction, wall, type) + rating_adjustment`

`P = sigmoid(z)`

Pros:
- O(1)
- stable and bounded [0,1]
- monotonic constraints are easy
- rating shift can be additive in log-odds
- smooth around boundaries

Cons:
- one simple linear logit may underfit nonlinear time-distance surfaces.

### Candidate B — piecewise probability surface + rating logit shift

1. lookup/interpolate an **average-defender baseline probability** from a small fixed table keyed by:
   - OF: hang-time bucket × required-distance bucket × direction/wall class;
   - IF: EV/speed bucket × direction/depth bucket.
2. convert `P_base` to logit.
3. add defender-rating adjustment.
4. sigmoid once.

Pros:
- O(1)
- closest to Statcast concept of empirical comparable-opportunity catch rates
- easy to calibrate from future KBO/MLB-derived aggregate surfaces
- monotonic table constraints can be audited explicitly
- one RNG roll afterward

Cons:
- needs a calibration table.

### Candidate C — direct fixed lookup with rating dimension

A full `(difficulty × rating)` table is fast but harder to maintain and recalibrate; rating monotonicity can be guaranteed but dimensionality expands quickly.

### Research recommendation

**Primary recommendation: Candidate B — baseline probability surface + logistic defender adjustment.**

Runtime:
1. fixed defender responsibility lookup;
2. derive required-distance proxy / difficulty bucket;
3. fixed-table interpolation/lookup;
4. one rating adjustment;
5. one sigmoid or bounded transform;
6. one RNG roll.

This satisfies all performance constraints and preserves a clean separation between BIP difficulty and defender skill.

Secondary acceptable option: Candidate A if Phase 2D wants minimal implementation first, provided coefficients are later calibrated and monotonicity is tested.

---

## ERROR_MODEL

Catch/out probability and fielding error represent related but distinct phenomena.

Evidence:
- Statcast Catch Probability/OAA is fundamentally a **range/opportunity difficulty** framework.
- Official KBO fielding evaluation combines UZR/KUZR-type range evidence with ordinary official records/errors rather than treating them as the same statistic.

Preferred long-term separation:

1. `reachable/catchable` or baseline out probability;
2. `attempt success` driven by range/difficulty + defender rating;
3. error/misplay probability for balls that were reasonably fieldable.

However Phase 2D V1 may combine (1)+(2) into one catch/out probability.

Recommendation:
- **Do not permanently fold errors into the same probability.**
- If implementation simplicity requires V1 combined success, preserve an outcome/interface flag so later `fielding_error` can be split without redesigning the BIP model.

Why: the current project already has an observed error/ROE validation gap, and merging all failed catches with hits would make that impossible to calibrate later.

---

## PHASE2D_VALIDATION_TARGETS

### Structural / hard invariants

- same BIP, higher defender rating must never reduce `P_out`;
- same defender/direction, more hang/opportunity time should not reduce OF catch probability;
- same time, larger required distance should not increase probability;
- back/away difficulty should be >= comparable forward difficulty;
- near-wall modifier should never make the identical opportunity easier unless explicitly justified;
- probability finite and bounded [0,1];
- deterministic probability before RNG for identical state/seed.

### Distribution measurements

Measure:
- catch/out rate by BIP class: GB / LD / FB / PU;
- OF catch rate by hang-time bucket;
- OF catch rate by required-distance/depth bucket;
- OF catch rate by direction class;
- wall-adjacent vs non-wall catch conversion;
- IF ground-out rate by EV bucket;
- IF ground-out rate by direction/sector/depth;
- conversion by defender rating bucket;
- primary position: 1B/2B/SS/3B/LF/CF/RF;
- adjacent-gap outcomes;
- BABIP before vs after Phase 2D;
- 1B/2B/3B distribution impact;
- error/ROE rate if separated.

### MLB sanity buckets

When validating an MLB-like difficulty surface, official Catch Probability star bands provide useful labels:
- 0-25 difficult/5-star
- 30-50 four-star
- 55-75 three-star
- 80-90 two-star
- 95 one-star/routine-ish

These are **MLB difficulty labels**, not KBO target shares.

### KBO aggregate validation

KBO official/public values currently support only broad aggregate checks such as:
- errors / fielding percentage;
- putouts / assists;
- team defense environment;
- future UZR/KUZR rank/award plausibility if comparable data becomes available.

No KBO catch-rate-by-hang-time target is currently authorized.

---

## DATA_GAPS

Highest-value open items:
1. KBO play-level outfield catch probability or tracking-derived time-distance surface;
2. KBO nominal OF/IF starting positions by situation;
3. KBO BIP conversion by landing zone / spray / depth;
4. KBO ground-out probability by EV and direction;
5. transparent KUZR/UZR raw calibration details;
6. KBO error probability by opportunity difficulty;
7. MLB public machine-readable time×distance catch-rate grid suitable for deriving an initial surface under usage constraints.

These gaps affect numeric calibration, not architecture.

---

## HANDOFF_TO_01

### Implementation prior

Use separate OF and IF difficulty models.

**OF contract:**
`landing_x/y + hang_time + fixed nominal OF start + direction/wall context -> P_base_avg -> defender rating adjustment -> one RNG`

Recommended nominal-position method:
- fixed LF/CF/RF anchors;
- compute one Euclidean required-distance proxy;
- no movement simulation.

**IF/GB contract:**
`spray/impact sector + EV/speed class + impact depth + fixed IF role -> P_base_avg -> rating adjustment -> one RNG`

Position responsibility:
- fixed ownership table;
- predeclared adjacent fielder blend in gaps;
- never perform nearest-defender search.

Preferred model:
- small empirical/piecewise baseline surface;
- rating adjustment in log-odds/logistic space.

Do not bind any existing project rating scale numerically from this report.

### Future-proofing

Preserve separate fields for:
- `base_catch_probability`
- `defender_adjusted_probability`
- `responsible_position`
- `difficulty_bucket`
- optional `error_probability`

This will make 05 diagnosis and later KBO calibration far easier.

---

## HANDOFF_TO_05

After Phase 2D implementation, run measurement-only validation first.

Minimum report:
- overall BIP out/catch rate;
- OF vs IF conversion;
- GB/LD/FB/PU conversion;
- OF catch rate by hang-time and required-distance buckets;
- IF ground-out rate by EV/direction/depth;
- each position's opportunity/conversion share;
- catch probability distribution P10/P25/P50/P75/P90;
- actual conversion vs model probability calibration curve;
- defender-rating monotonicity sweep;
- wall-context sensitivity;
- BABIP and hit-type changes;
- error/ROE if separated.

Critical tests:
- identical BIP, low/average/high rating sweep;
- identical time, increasing distance sweep;
- identical distance, increasing time sweep;
- OF direction sweep (in/lateral/back);
- gap-sector ownership continuity;
- extreme EV/LA/landing coordinates remain finite and bounded.

Overall gate:
**PHASE2D_CATCH_PROBABILITY_REFERENCE = VERIFIED_FOR_ARCHITECTURE_PARTIAL_FOR_KBO_CALIBRATION**.
