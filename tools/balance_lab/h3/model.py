"""H3.1 test-side pitch -> batted-ball -> defense pipeline."""
from __future__ import annotations
from dataclasses import dataclass
import math
import random
from . import parameters as P
from .metrics import H3Line
from .profiles import H3DefenseProfile, H3HitterProfile, H3PitcherProfile


def _clamp(x: float, lo: float=0.0, hi: float=1.0) -> float:
    return max(lo, min(hi, x))


def _sigmoid(x: float) -> float:
    if x >= 60: return 1.0
    if x <= -60: return 0.0
    return 1.0/(1.0+math.exp(-x))


def _soft_delta(raw: float, softness: float) -> float:
    d = raw - P.STAT_REFERENCE
    if d <= 0:
        return d
    return softness * math.log1p(d/softness)


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


class H31Model:
    def __init__(self, hitter: H3HitterProfile, pitcher: H3PitcherProfile | None=None,
                 defense: H3DefenseProfile | None=None, seed: int=1):
        self.hitter = hitter
        self.pitcher = pitcher or H3PitcherProfile()
        self.defense = defense or H3DefenseProfile()
        self.rng = random.Random(seed)

    def _pitch(self) -> Pitch:
        r = self.rng.random(); acc = 0.0; zone = "low"
        for name, weight in P.ZONE_WEIGHTS.items():
            acc += weight
            if r <= acc:
                zone = name; break
        is_strike = self.rng.random() < _clamp(P.STRIKE_RATE + (self.pitcher.control-100)*0.0006, .45, .66)
        pitch_type = "fastball" if self.rng.random() < P.PITCH_TYPE_FASTBALL else "breaking"
        velocity = self.rng.gauss((self.pitcher.stuff-100)/22, .30)
        movement = self.rng.gauss((self.pitcher.movement-100)/22, .32)
        location = self.rng.gauss((self.pitcher.control-100)/28, .34)
        hittable = P.ZONE_HITTABLE[zone] + location*.16 - abs(movement)*.12
        if not is_strike: hittable += P.BALL_HITTABLE_PENALTY
        return Pitch(is_strike, zone, pitch_type, velocity, movement, location, hittable)

    def _swing_probability(self, pitch: Pitch, balls: int, strikes: int) -> float:
        d = self.hitter.discipline - 100.0
        count = 0.025 if strikes == 2 else (-0.018 if balls == 3 else 0.0)
        if pitch.is_strike:
            zone_bonus = .075 if pitch.zone == "middle" else -.015 if pitch.zone in {"high","low","outside"} else .02
            return _clamp(P.ZONE_SWING_BASE + d*P.DISCIPLINE_ZONE_WEIGHT + zone_bonus + count, .34, .91)
        return _clamp(P.BALL_CHASE_BASE - d*P.DISCIPLINE_CHASE_WEIGHT + pitch.hittable_quality*.055 + count, .015, .54)

    def _contact_resolution(self, pitch: Pitch, strikes: int) -> tuple[str, float]:
        cdelta = _soft_delta(self.hitter.contact, P.CONTACT_POSITIVE_SOFT)
        difficulty = ((self.pitcher.stuff-100)*0.006 + pitch.velocity_quality*.16 + pitch.movement_quality*.18 - pitch.hittable_quality*P.CONTACT_HITTABLE_WEIGHT)
        contact_score = cdelta*P.CONTACT_SCALE - difficulty
        p_touch = _clamp(P.BIP_BASE + contact_score*.22, .28, .965)
        if self.rng.random() > p_touch:
            if strikes == 2 and self.hitter.discipline > 100:
                protect = min(P.TWO_STRIKE_PROTECTION_CAP,(self.hitter.discipline-100)*P.TWO_STRIKE_PROTECTION_WEIGHT)
                if self.rng.random() < protect: return "foul", pitch.hittable_quality
            return "miss", pitch.hittable_quality
        foul = _clamp(P.FOUL_BASE - pitch.hittable_quality*.07 + max(0, -contact_score)*.05, .22, .52)
        if self.rng.random() < foul: return "foul", pitch.hittable_quality
        return "bip", pitch.hittable_quality

    def _direction(self, pitch: Pitch) -> tuple[str, float]:
        left, center, right = P.APPROACH_BASE[self.hitter.approach]; pull, opp = left, right; quality_bonus = 0.0
        if pitch.zone == "inside":
            pull += P.LOCATION_DIRECTION_SHIFT; opp -= P.LOCATION_DIRECTION_SHIFT*.65
            if self.hitter.approach == "pull": quality_bonus += P.APPROACH_MATCH_QUALITY_BONUS
            elif self.hitter.approach == "opposite": quality_bonus -= P.APPROACH_FORCE_PENALTY
        elif pitch.zone == "outside":
            opp += P.LOCATION_DIRECTION_SHIFT; pull -= P.LOCATION_DIRECTION_SHIFT*.65
            if self.hitter.approach == "opposite": quality_bonus += P.APPROACH_MATCH_QUALITY_BONUS
            elif self.hitter.approach == "pull": quality_bonus -= P.APPROACH_FORCE_PENALTY
        probs = [max(.02,pull), max(.02,center), max(.02,opp)]; s = sum(probs); probs = [x/s for x in probs]
        r = self.rng.random(); side = "left" if r < probs[0] else "center" if r < probs[0]+probs[1] else "right"
        if self.hitter.handedness == "L": side = "right" if side == "left" else "left" if side == "right" else side
        return side, quality_bonus

    @staticmethod
    def _quality_tier(q: float) -> str:
        if q < -0.85: return "weak"
        if q < -0.20: return "poor"
        if q < 0.40: return "average"
        if q < 1.00: return "solid"
        return "barrel"

    @staticmethod
    def _difficulty_tier(score: float) -> str:
        if score < -0.78: return "ROUTINE"
        if score < -0.28: return "EASY"
        if score < 0.28: return "AVERAGE"
        if score < 0.78: return "HARD"
        if score < 1.28: return "VERY_HARD"
        return "EXCEPTIONAL"

    def _batted_ball(self, pitch: Pitch) -> BattedBall:
        side, approach_bonus = self._direction(pitch)
        cdelta = _soft_delta(self.hitter.contact, P.CONTACT_POSITIVE_SOFT)
        quality = (cdelta*P.QUALITY_CONTACT_WEIGHT + pitch.hittable_quality*P.QUALITY_HITTABLE_WEIGHT - (self.pitcher.movement-100)*P.QUALITY_MOVEMENT_WEIGHT + approach_bonus + self.rng.gauss(0, P.QUALITY_NOISE_SD))
        pdelta = _soft_delta(self.hitter.power, P.POWER_POSITIVE_SOFT)
        exit_q = quality*P.EXIT_QUALITY_WEIGHT + pdelta*P.POWER_SCALE*P.EXIT_POWER_WEIGHT + self.rng.gauss(0,P.EXIT_NOISE_SD)
        r = self.rng.random(); p_line = _clamp(.22 + quality*.055, .12, .34); p_fly = _clamp(.34 + quality*.035 + pdelta*.0005, .23, .48)
        ball_type = "line_drive" if r < p_line else "fly_ball" if r < p_line+p_fly else "ground_ball"
        deep_score = exit_q + (.20 if ball_type == "fly_ball" else -.15 if ball_type == "ground_ball" else .05)
        depth = "deep" if deep_score > P.DEEP_THRESHOLD else "medium" if deep_score > P.MEDIUM_THRESHOLD else "shallow"
        distance = abs(self.rng.gauss(0.70 if side == "center" else .78, .25))
        type_bonus = P.DIFFICULTY_GROUND_BONUS if ball_type == "ground_ball" else P.DIFFICULTY_LINE_BONUS if ball_type == "line_drive" else P.DIFFICULTY_FLY_BONUS
        depth_bonus = P.DIFFICULTY_DEEP_BONUS if depth == "deep" else P.DIFFICULTY_SHALLOW_BONUS if depth == "shallow" else 0.0
        diff = quality*P.DIFFICULTY_QUALITY_WEIGHT + exit_q*P.DIFFICULTY_EXIT_WEIGHT + distance*P.DIFFICULTY_DISTANCE_WEIGHT + type_bonus + depth_bonus - .52
        return BattedBall(quality, exit_q, ball_type, side, depth, distance, diff, self._difficulty_tier(diff))

    def _is_home_run(self, ball: BattedBall) -> bool:
        if ball.ball_type == "ground_ball" or ball.depth != "deep": return False
        mult = P.HR_FLY_MULT if ball.ball_type == "fly_ball" else P.HR_LINE_MULT
        p = _sigmoid((ball.exit_quality-P.HR_LOGIT_CENTER)/P.HR_LOGIT_SCALE) * mult
        return self.rng.random() < _clamp(p, 0, .42)

    def _catch_probability(self, tier: str) -> float:
        base = P.DIFFICULTY_BASE_CATCH[tier]; adj = (self.defense.defense-100.0)*P.DIFFICULTY_DEFENSE_LEVERAGE[tier]; lo, hi = P.DIFFICULTY_CATCH_BOUNDS[tier]
        return _clamp(base + adj, lo, hi)

    def _infield_hit_probability(self, tier: str) -> float:
        if tier == "ROUTINE": return 0.0
        diff=(self.hitter.speed-100.0) - (self.defense.defense-100.0)*P.INFIELD_HIT_DEFENSE_WEIGHT
        if diff >= 0: prob=P.INFIELD_HIT_BASE + (P.INFIELD_HIT_HIGH-P.INFIELD_HIT_BASE)*(1-math.exp(-diff/P.INFIELD_HIT_UP_SCALE))
        else: prob=P.INFIELD_HIT_LOW + (P.INFIELD_HIT_BASE-P.INFIELD_HIT_LOW)*math.exp(diff/P.INFIELD_HIT_DOWN_SCALE)
        if tier == "EASY": prob *= P.INFIELD_HIT_EASY_FACTOR
        return _clamp(prob,0,P.INFIELD_HIT_HIGH)

    def _raw_hit_candidate(self, ball: BattedBall) -> str:
        q = ball.contact_quality; e = ball.exit_quality
        p2 = _clamp(P.DOUBLE_BASE + max(0,q)*P.DOUBLE_QUALITY_WEIGHT + max(0,e)*P.DOUBLE_EXIT_WEIGHT + (P.DOUBLE_DEEP_BONUS if ball.depth == "deep" else 0) + (P.DOUBLE_LINE_BONUS if ball.ball_type == "line_drive" else 0), .01, .48)
        gap = ball.direction != "center" and ball.depth == "deep"; p3raw = P.TRIPLE_CANDIDATE_GAP_BONUS if gap and e > .55 else 0.0; r = self.rng.random()
        if r < p3raw: return "3B_candidate"
        if r < p3raw+p2: return "2B_candidate"
        return "1B_candidate"

    def _damage_suppress(self, candidate: str) -> str:
        d = self.defense.defense - 100.0
        if candidate == "3B_candidate":
            p = _clamp(P.DAMAGE_BASE_3B_TO_2B + d*P.DAMAGE_DEFENSE_SCALE, .02, P.DAMAGE_MAX_3B_TO_2B)
            if self.rng.random() < p: return "2B_candidate_suppressed"
        elif candidate == "2B_candidate":
            p = _clamp(P.DAMAGE_BASE_2B_TO_1B + d*P.DAMAGE_DEFENSE_SCALE, .02, P.DAMAGE_MAX_2B_TO_1B)
            if self.rng.random() < p: return "1B_suppressed"
        return candidate

    def _speed_resolve(self, candidate: str, ball: BattedBall, line: H3Line) -> str:
        s = self.hitter.speed
        if candidate in {"1B_candidate", "1B_suppressed"}:
            if s > 100 and ball.ball_type != "ground_ball" and ball.depth != "shallow":
                stretch = _clamp((s-100.0)*P.FAST_SINGLE_TO_DOUBLE_PER_POINT, 0, P.FAST_SINGLE_TO_DOUBLE_MAX)
                if self.rng.random() < stretch:
                    line.single_to_double_upgrades += 1; return "2B"
            return "1B"
        if candidate in {"2B_candidate", "2B_candidate_suppressed", "3B_candidate"}:
            line.double_candidates += 1
            if candidate == "3B_candidate": line.raw_trip_candidates += 1
            else: line.raw_double_candidates += 1
            automatic = (ball.depth == "deep" and ball.exit_quality > .82) or ball.exit_quality > 1.18
            if not automatic:
                line.stretch_double_candidates += 1
                if s < 100:
                    downgrade = _clamp(P.SLOW_DOUBLE_DOWNGRADE_AT_100 + (100-s)*P.SLOW_DOUBLE_DOWNGRADE_PER_POINT, 0, P.SLOW_DOUBLE_DOWNGRADE_MAX)
                    if self.rng.random() < downgrade:
                        line.double_downgrades += 1; return "1B"
            speed_up = max(0.0, s-85.0); triple = P.FAST_TRIPLE_BASE + (P.FAST_TRIPLE_MAX-P.FAST_TRIPLE_BASE)*(1-math.exp(-speed_up/P.FAST_TRIPLE_SOFT)); triple = _clamp(triple, .005, P.FAST_TRIPLE_MAX)
            if automatic: triple *= P.AUTO_DOUBLE_TRIPLE_FACTOR
            if candidate == "3B_candidate": triple = _clamp(triple + .08, 0, .34)
            if ball.depth != "deep": triple *= .40
            if self.rng.random() < triple:
                line.triple_conversions += 1; return "3B"
            return "2B"
        raise ValueError(candidate)

    def plate_appearance(self, line: H3Line) -> None:
        line.pa += 1; balls = strikes = 0
        for _ in range(20):
            pitch = self._pitch(); swing_p = self._swing_probability(pitch, balls, strikes)
            if self.rng.random() >= swing_p:
                if pitch.is_strike:
                    strikes += 1
                    if strikes >= 3: line.ab += 1; line.so += 1; line.outs += 1; return
                else:
                    balls += 1
                    if balls >= 4: line.bb += 1; return
                continue
            line.swings += 1; line.swing_pitch_quality_sum += pitch.hittable_quality
            if not pitch.is_strike: line.chases += 1
            outcome, _ = self._contact_resolution(pitch, strikes)
            if outcome == "miss":
                strikes += 1
                if strikes >= 3: line.ab += 1; line.so += 1; line.outs += 1; return
                continue
            if outcome == "foul":
                if strikes < 2: strikes += 1
                continue
            ball = self._batted_ball(pitch); line.bip += 1; line.ab += 1; line.contact_quality_sum += ball.contact_quality; line.contact_quality_count += 1; line.directions[ball.direction] += 1; line.types[ball.ball_type] += 1; line.depths[ball.depth] += 1
            q_tier = self._quality_tier(ball.contact_quality); line.quality_tiers[q_tier] += 1
            if self._is_home_run(ball): line.h += 1; line.hr += 1; return
            tier = ball.difficulty_tier; line.difficulty_attempts[tier] += 1; line.quality_attempts[q_tier] += 1
            if self.rng.random() < self._catch_probability(tier):
                if ball.ball_type == "ground_ball" and self.rng.random() < self._infield_hit_probability(tier):
                    line.h += 1; line.singles += 1; line.infield_hits_by_difficulty[tier] += 1; return
                line.difficulty_catches[tier] += 1; line.quality_catches[q_tier] += 1; line.outs += 1; return
            line.difficulty_misses[tier] += 1
            if tier == "ROUTINE" and self.rng.random() < P.ROUTINE_MISS_ERROR_RATE: line.roe += 1; line.errors_by_difficulty[tier] += 1; return
            if tier == "EASY" and self.rng.random() < P.EASY_MISS_ERROR_RATE: line.roe += 1; line.errors_by_difficulty[tier] += 1; return
            line.hits_on_miss_by_difficulty[tier] += 1; candidate = self._raw_hit_candidate(ball); suppressed = self._damage_suppress(candidate)
            if candidate == "3B_candidate" and suppressed.startswith("2B"): line.damage_3b_to_2b += 1
            if candidate == "2B_candidate" and suppressed.startswith("1B"): line.damage_2b_to_1b += 1
            result = self._speed_resolve(suppressed, ball, line); line.h += 1
            if result == "1B": line.singles += 1
            elif result == "2B": line.doubles += 1
            else: line.triples += 1
            return
        line.ab += 1; line.outs += 1

    def simulate(self, pa: int) -> H3Line:
        line = H3Line()
        for _ in range(pa): self.plate_appearance(line)
        return line


def simulate_profile(hitter: H3HitterProfile, pa: int, seed: int=1, pitcher: H3PitcherProfile | None=None, defense: float=100.0) -> H3Line:
    return H31Model(hitter, pitcher, H3DefenseProfile(defense), seed).simulate(pa)
