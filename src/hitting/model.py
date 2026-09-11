"""Production pitch-to-batted-ball engine.

Phase 1 owns pitch/count/swing/contact/foul semantics. Phase 2A now generates a
shadow physical initial state for every legacy fair-contact BIP while preserving
the existing HR/XBH/defense result resolver until later Phase-2 stages.
"""
from __future__ import annotations
from dataclasses import dataclass
import math
from typing import Callable
from . import parameters as P
from .defense import catch_probability, clamp, difficulty_tier, suppress_candidate
from .physical import BattedBallState, generate_batted_ball_state

@dataclass(frozen=True)
class HitterSnapshot:
    contact: float
    power: float
    discipline: float
    speed: float
    handedness: str = "R"
    approach: str = "balanced"

@dataclass(frozen=True)
class PitcherSnapshot:
    stuff: float = 100.0
    control: float = 100.0
    movement: float = 100.0
    handedness: str = "R"

@dataclass(frozen=True)
class Pitch:
    is_strike: bool
    zone: str
    pitch_type: str
    velocity_quality: float
    movement_quality: float
    location_quality: float
    hittable_quality: float

@dataclass(frozen=True)
class BattedBall:
    contact_quality: float
    exit_quality: float
    ball_type: str
    direction: str
    depth: str
    distance: float
    difficulty_score: float
    difficulty_tier: str
    physical_state: BattedBallState | None = None

@dataclass(frozen=True)
class PlateAppearanceOutcome:
    result: str
    batted_ball: BattedBall | None = None
    infield_hit: bool = False
    error: bool = False
    raw_candidate: str | None = None
    resolved_candidate: str | None = None

PitchStatModifier = Callable[[Pitch, int], tuple[float, float]]

def sigmoid(value: float) -> float:
    if value >= 60: return 1.0
    if value <= -60: return 0.0
    return 1.0 / (1.0 + math.exp(-value))

def soft_delta(raw: float, softness: float) -> float:
    delta = raw - P.STAT_REFERENCE
    if delta <= 0:
        return delta
    return softness * math.log1p(delta / softness)

class HittingEngine:
    def __init__(
        self,
        hitter: HitterSnapshot,
        pitcher: PitcherSnapshot,
        defense: float,
        rng,
        pitch_stat_modifier: PitchStatModifier | None = None,
    ) -> None:
        self.hitter = hitter
        self.pitcher = pitcher
        self.defense = defense
        self.rng = rng
        self.pitch_stat_modifier = pitch_stat_modifier

    def _pitch(self) -> Pitch:
        roll = self.rng.random()
        cumulative = 0.0
        zone = "low"
        for name, weight in P.ZONE_WEIGHTS.items():
            cumulative += weight
            if roll <= cumulative:
                zone = name
                break
        is_strike = self.rng.random() < clamp(
            P.STRIKE_RATE + (self.pitcher.control - 100) * 0.0006, .45, .66
        )
        pitch_type = "fastball" if self.rng.random() < P.PITCH_TYPE_FASTBALL else "breaking"
        velocity = self.rng.gauss((self.pitcher.stuff - 100) / 22, .30)
        movement = self.rng.gauss((self.pitcher.movement - 100) / 22, .32)
        location = self.rng.gauss((self.pitcher.control - 100) / 28, .34)
        hittable = P.ZONE_HITTABLE[zone] + location * .16 - abs(movement) * .12
        if not is_strike:
            hittable += P.BALL_HITTABLE_PENALTY
        return Pitch(
            is_strike, zone, pitch_type, velocity, movement, location, hittable
        )

    def _count_swing_adjustment(self, pitch: Pitch, balls: int, strikes: int) -> float:
        """Return additive situational count effect without replacing player identity."""
        zone_swing, chase = P.COUNT_SWING_MODIFIERS.get((balls, strikes), (0.0, 0.0))
        return zone_swing if pitch.is_strike else chase

    def _swing_probability(self, pitch: Pitch, balls: int, strikes: int) -> float:
        discipline_delta = self.hitter.discipline - 100.0
        count = self._count_swing_adjustment(pitch, balls, strikes)
        if pitch.is_strike:
            zone_bonus = (
                .075 if pitch.zone == "middle"
                else -.015 if pitch.zone in {"high", "low", "outside"}
                else .02
            )
            return clamp(
                P.ZONE_SWING_BASE
                + discipline_delta * P.DISCIPLINE_ZONE_WEIGHT
                + zone_bonus + count,
                P.ZONE_SWING_MIN, P.ZONE_SWING_MAX,
            )
        return clamp(
            P.BALL_CHASE_BASE
            - discipline_delta * P.DISCIPLINE_CHASE_WEIGHT
            + pitch.hittable_quality * .055 + count,
            P.CHASE_MIN, P.CHASE_MAX,
        )

    def _two_strike_take_rescue_probability(self, pitch: Pitch) -> float:
        """Late protection chance for a taken in-zone pitch with two strikes."""
        if not pitch.is_strike:
            return 0.0
        discipline_delta = clamp(self.hitter.discipline - 100.0, -30.0, 40.0)
        hittable = clamp(pitch.hittable_quality, -0.50, 1.00)
        return clamp(
            P.TWO_STRIKE_TAKE_RESCUE_BASE
            + hittable * P.TWO_STRIKE_TAKE_RESCUE_HITTABLE_WEIGHT
            + discipline_delta * P.TWO_STRIKE_TAKE_RESCUE_DISCIPLINE_WEIGHT,
            P.TWO_STRIKE_TAKE_RESCUE_MIN,
            P.TWO_STRIKE_TAKE_RESCUE_MAX,
        )

    def _hit_by_pitch_probability(self, pitch: Pitch) -> float:
        if pitch.is_strike:
            return 0.0
        control_delta = self.pitcher.control - 100.0
        probability = P.HBP_OUT_OF_ZONE_BASE
        if control_delta < 0:
            probability += -control_delta * P.HBP_CONTROL_WILDNESS_WEIGHT
        else:
            probability -= control_delta * P.HBP_CONTROL_COMMAND_WEIGHT
        return clamp(probability, P.HBP_MIN, P.HBP_MAX)

    def _is_hit_by_pitch(self, pitch: Pitch) -> bool:
        if pitch.is_strike:
            return False
        return self.rng.random() < self._hit_by_pitch_probability(pitch)

    def _contact_resolution(
        self, pitch: Pitch, strikes: int, protective_swing: bool = False
    ) -> tuple[str, float, float]:
        contact_delta = 0.0
        power_delta = 0.0
        if self.pitch_stat_modifier is not None:
            contact_delta, power_delta = self.pitch_stat_modifier(pitch, strikes)
        contact = self.hitter.contact + contact_delta
        cdelta = soft_delta(contact, P.CONTACT_POSITIVE_SOFT)
        difficulty = (
            (self.pitcher.stuff - 100) * .006
            + pitch.velocity_quality * .16
            + pitch.movement_quality * .18
            - pitch.hittable_quality * P.CONTACT_HITTABLE_WEIGHT
        )
        contact_score = cdelta * P.CONTACT_SCALE - difficulty
        touch_probability = clamp(P.BIP_BASE + contact_score * .22, .28, .965)
        if protective_swing:
            touch_probability = clamp(
                touch_probability * P.TWO_STRIKE_PROTECTIVE_TOUCH_SCALE,
                P.TWO_STRIKE_PROTECTIVE_TOUCH_MIN,
                P.TWO_STRIKE_PROTECTIVE_TOUCH_MAX,
            )
        if self.rng.random() > touch_probability:
            if protective_swing:
                rescue = P.TWO_STRIKE_PROTECTIVE_MISS_TO_FOUL
            else:
                rescue = (
                    P.MISS_TO_FOUL_ZONE_BASE
                    if pitch.is_strike else P.MISS_TO_FOUL_BALL_BASE
                )
                if strikes == 2:
                    discipline_delta = clamp(self.hitter.discipline - 100.0, -20.0, 40.0)
                    rescue += P.TWO_STRIKE_FOUL_RESCUE_BASE
                    rescue += discipline_delta * P.TWO_STRIKE_FOUL_DISCIPLINE_WEIGHT
            if self.rng.random() < clamp(rescue, 0.0, P.MISS_TO_FOUL_CAP):
                return "foul", contact_delta, power_delta
            return "miss", contact_delta, power_delta
        foul_probability = clamp(
            P.FOUL_BASE - pitch.hittable_quality * .07
            + max(0, -contact_score) * .05,
            .22, .52,
        )
        if protective_swing:
            foul_probability = clamp(
                foul_probability + P.TWO_STRIKE_PROTECTIVE_FOUL_BONUS,
                P.TWO_STRIKE_PROTECTIVE_FOUL_MIN,
                P.TWO_STRIKE_PROTECTIVE_FOUL_MAX,
            )
        if self.rng.random() < foul_probability:
            return "foul", contact_delta, power_delta
        return "bip", contact_delta, power_delta

    def _direction(self, pitch: Pitch) -> tuple[str, float]:
        left, center, right = P.APPROACH_BASE[self.hitter.approach]
        pull, opposite = left, right
        quality_bonus = 0.0
        if pitch.zone == "inside":
            pull += P.LOCATION_DIRECTION_SHIFT
            opposite -= P.LOCATION_DIRECTION_SHIFT * .65
            if self.hitter.approach == "pull":
                quality_bonus += P.APPROACH_MATCH_QUALITY_BONUS
            elif self.hitter.approach == "opposite":
                quality_bonus -= P.APPROACH_FORCE_PENALTY
        elif pitch.zone == "outside":
            opposite += P.LOCATION_DIRECTION_SHIFT
            pull -= P.LOCATION_DIRECTION_SHIFT * .65
            if self.hitter.approach == "opposite":
                quality_bonus += P.APPROACH_MATCH_QUALITY_BONUS
            elif self.hitter.approach == "pull":
                quality_bonus -= P.APPROACH_FORCE_PENALTY
        probabilities = [max(.02, pull), max(.02, center), max(.02, opposite)]
        total = sum(probabilities)
        probabilities = [value / total for value in probabilities]
        roll = self.rng.random()
        side = (
            "left" if roll < probabilities[0]
            else "center" if roll < probabilities[0] + probabilities[1]
            else "right"
        )
        if self.hitter.handedness == "L":
            side = "right" if side == "left" else "left" if side == "right" else side
        return side, quality_bonus

    def _batted_ball(
        self,
        pitch: Pitch,
        contact_delta: float,
        power_delta: float,
        physical_state: BattedBallState | None = None,
    ) -> BattedBall:
        side, approach_bonus = self._direction(pitch)
        contact = self.hitter.contact + contact_delta
        power = self.hitter.power + power_delta
        cdelta = soft_delta(contact, P.CONTACT_POSITIVE_SOFT)
        quality = (
            cdelta * P.QUALITY_CONTACT_WEIGHT
            + pitch.hittable_quality * P.QUALITY_HITTABLE_WEIGHT
            - (self.pitcher.movement - 100) * P.QUALITY_MOVEMENT_WEIGHT
            + approach_bonus
            + self.rng.gauss(0, P.QUALITY_NOISE_SD)
        )
        pdelta = soft_delta(power, P.POWER_POSITIVE_SOFT)
        exit_quality = (
            quality * P.EXIT_QUALITY_WEIGHT
            + pdelta * P.POWER_SCALE * P.EXIT_POWER_WEIGHT
            + self.rng.gauss(0, P.EXIT_NOISE_SD)
        )
        roll = self.rng.random()
        line_probability = clamp(.22 + quality * .055, .12, .34)
        fly_probability = clamp(.34 + quality * .035 + pdelta * .0005, .23, .48)
        ball_type = (
            "line_drive" if roll < line_probability
            else "fly_ball" if roll < line_probability + fly_probability
            else "ground_ball"
        )
        deep_score = exit_quality + (
            .20 if ball_type == "fly_ball"
            else -.15 if ball_type == "ground_ball"
            else .05
        )
        depth = (
            "deep" if deep_score > P.DEEP_THRESHOLD
            else "medium" if deep_score > P.MEDIUM_THRESHOLD
            else "shallow"
        )
        distance = abs(self.rng.gauss(.70 if side == "center" else .78, .25))
        type_bonus = (
            P.DIFFICULTY_GROUND_BONUS if ball_type == "ground_ball"
            else P.DIFFICULTY_LINE_BONUS if ball_type == "line_drive"
            else P.DIFFICULTY_FLY_BONUS
        )
        depth_bonus = (
            P.DIFFICULTY_DEEP_BONUS if depth == "deep"
            else P.DIFFICULTY_SHALLOW_BONUS if depth == "shallow"
            else 0.0
        )
        score = (
            quality * P.DIFFICULTY_QUALITY_WEIGHT
            + exit_quality * P.DIFFICULTY_EXIT_WEIGHT
            + distance * P.DIFFICULTY_DISTANCE_WEIGHT
            + type_bonus + depth_bonus - .52
        )
        return BattedBall(
            quality, exit_quality, ball_type, side, depth, distance,
            score, difficulty_tier(score), physical_state,
        )

    def _is_home_run(self, ball: BattedBall) -> bool:
        if ball.ball_type == "ground_ball" or ball.depth != "deep":
            return False
        multiplier = P.HR_FLY_MULT if ball.ball_type == "fly_ball" else P.HR_LINE_MULT
        probability = sigmoid(
            (ball.exit_quality - P.HR_LOGIT_CENTER) / P.HR_LOGIT_SCALE
        ) * multiplier
        return self.rng.random() < clamp(probability, 0, .42)

    def _infield_hit_probability(self, tier: str) -> float:
        if tier == "ROUTINE":
            return 0.0
        delta = (
            (self.hitter.speed - 100.0)
            - (self.defense - 100.0) * P.INFIELD_HIT_DEFENSE_WEIGHT
        )
        if delta >= 0:
            probability = P.INFIELD_HIT_BASE + (
                P.INFIELD_HIT_HIGH - P.INFIELD_HIT_BASE
            ) * (1 - math.exp(-delta / P.INFIELD_HIT_UP_SCALE))
        else:
            probability = P.INFIELD_HIT_LOW + (
                P.INFIELD_HIT_BASE - P.INFIELD_HIT_LOW
            ) * math.exp(delta / P.INFIELD_HIT_DOWN_SCALE)
        if tier == "EASY":
            probability *= P.INFIELD_HIT_EASY_FACTOR
        return clamp(probability, 0, P.INFIELD_HIT_HIGH)

    def _raw_hit_candidate(self, ball: BattedBall) -> str:
        quality = ball.contact_quality
        exit_quality = ball.exit_quality
        double_probability = clamp(
            P.DOUBLE_BASE
            + max(0, quality) * P.DOUBLE_QUALITY_WEIGHT
            + max(0, exit_quality) * P.DOUBLE_EXIT_WEIGHT
            + (P.DOUBLE_DEEP_BONUS if ball.depth == "deep" else 0)
            + (P.DOUBLE_LINE_BONUS if ball.ball_type == "line_drive" else 0),
            .01, .48,
        )
        gap = ball.direction != "center" and ball.depth == "deep"
        triple_candidate = (
            P.TRIPLE_CANDIDATE_GAP_BONUS if gap and exit_quality > .55 else 0.0
        )
        roll = self.rng.random()
        if roll < triple_candidate:
            return "3B_candidate"
        if roll < triple_candidate + double_probability:
            return "2B_candidate"
        return "1B_candidate"

    def _speed_resolve(self, candidate: str, ball: BattedBall) -> str:
        speed = self.hitter.speed
        if candidate in {"1B_candidate", "1B_suppressed"}:
            if speed > 100 and ball.ball_type != "ground_ball" and ball.depth != "shallow":
                stretch = clamp(
                    (speed - 100.0) * P.FAST_SINGLE_TO_DOUBLE_PER_POINT,
                    0, P.FAST_SINGLE_TO_DOUBLE_MAX,
                )
                if self.rng.random() < stretch:
                    return "double"
            return "single"
        if candidate in {"2B_candidate", "2B_candidate_suppressed", "3B_candidate"}:
            automatic = (
                (ball.depth == "deep" and ball.exit_quality > .82)
                or ball.exit_quality > 1.18
            )
            if not automatic and speed < 100:
                downgrade = clamp(
                    P.SLOW_DOUBLE_DOWNGRADE_AT_100
                    + (100 - speed) * P.SLOW_DOUBLE_DOWNGRADE_PER_POINT,
                    0, P.SLOW_DOUBLE_DOWNGRADE_MAX,
                )
                if self.rng.random() < downgrade:
                    return "single"
            speed_up = max(0.0, speed - 85.0)
            triple = P.FAST_TRIPLE_BASE + (
                P.FAST_TRIPLE_MAX - P.FAST_TRIPLE_BASE
            ) * (1 - math.exp(-speed_up / P.FAST_TRIPLE_SOFT))
            triple = clamp(triple, .005, P.FAST_TRIPLE_MAX)
            if automatic:
                triple *= P.AUTO_DOUBLE_TRIPLE_FACTOR
            if candidate == "3B_candidate":
                triple = clamp(triple + .08, 0, .34)
            if ball.depth != "deep":
                triple *= .40
            if self.rng.random() < triple:
                return "triple"
            return "double"
        raise ValueError(candidate)

    def simulate_plate_appearance(self) -> PlateAppearanceOutcome:
        balls = strikes = 0
        for _ in range(20):
            pitch = self._pitch()
            if self._is_hit_by_pitch(pitch):
                return PlateAppearanceOutcome("hit_by_pitch")
            swing_probability = self._swing_probability(pitch, balls, strikes)
            protective_swing = False
            if self.rng.random() >= swing_probability:
                if (
                    pitch.is_strike
                    and strikes == 2
                    and self.rng.random() < self._two_strike_take_rescue_probability(pitch)
                ):
                    protective_swing = True
                else:
                    if pitch.is_strike:
                        strikes += 1
                        if strikes >= 3:
                            return PlateAppearanceOutcome("strikeout")
                    else:
                        balls += 1
                        if balls >= 4:
                            return PlateAppearanceOutcome("walk")
                    continue
            if protective_swing:
                contact_result, contact_delta, power_delta = self._contact_resolution(
                    pitch, strikes, protective_swing=True
                )
            else:
                contact_result, contact_delta, power_delta = self._contact_resolution(
                    pitch, strikes
                )
            if contact_result == "miss":
                strikes += 1
                if strikes >= 3:
                    return PlateAppearanceOutcome("strikeout")
                continue
            if contact_result == "foul":
                if strikes < 2:
                    strikes += 1
                continue

            physical_state = generate_batted_ball_state(
                hitter_contact=self.hitter.contact + contact_delta,
                hitter_power=self.hitter.power + power_delta,
                batter_side=self.hitter.handedness,
                approach=self.hitter.approach,
                pitch_zone=pitch.zone,
                pitch_velocity_quality=pitch.velocity_quality,
                pitch_movement_quality=pitch.movement_quality,
                pitch_location_quality=pitch.location_quality,
                pitch_hittable_quality=pitch.hittable_quality,
                parent_rng=self.rng,
            )
            ball = self._batted_ball(
                pitch, contact_delta, power_delta, physical_state=physical_state
            )
            if self._is_home_run(ball):
                return PlateAppearanceOutcome("home_run", batted_ball=ball)

            tier = ball.difficulty_tier
            if self.rng.random() < catch_probability(tier, self.defense):
                if (
                    ball.ball_type == "ground_ball"
                    and self.rng.random() < self._infield_hit_probability(tier)
                ):
                    return PlateAppearanceOutcome(
                        "single", batted_ball=ball, infield_hit=True
                    )
                return PlateAppearanceOutcome("out", batted_ball=ball)

            if tier == "ROUTINE" and self.rng.random() < P.ROUTINE_MISS_ERROR_RATE:
                return PlateAppearanceOutcome("reached_on_error", batted_ball=ball, error=True)
            if tier == "EASY" and self.rng.random() < P.EASY_MISS_ERROR_RATE:
                return PlateAppearanceOutcome("reached_on_error", batted_ball=ball, error=True)

            raw = self._raw_hit_candidate(ball)
            resolved = (
                suppress_candidate(raw, self.defense, self.rng.random())
                if raw in {"3B_candidate", "2B_candidate"} else raw
            )
            result = self._speed_resolve(resolved, ball)
            return PlateAppearanceOutcome(
                result,
                batted_ball=ball,
                raw_candidate=raw,
                resolved_candidate=resolved,
            )
        return PlateAppearanceOutcome("out")