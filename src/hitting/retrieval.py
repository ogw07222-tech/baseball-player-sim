"""Phase 2E-B deterministic O(1) retrieval and physical hit-type shadow model.

The model consumes Phase-2E-A final ball location plus Phase-2D catch shadow.
It performs one fixed retriever ownership decision, one retrieval-time estimate,
three hypothetical base-arrival timing checks, and zero RNG calls. Legacy hit,
defense, runner-advancement, scoring, and stat authority remain unchanged.
"""
from __future__ import annotations

from dataclasses import dataclass
import math

from .ground_travel import GroundTravelState
from .physical_defense import DefensiveResolution
from . import retrieval_parameters as P

_ALLOWED_RESULTS = {None, "OUT", "1B", "2B", "3B"}


@dataclass(frozen=True)
class RetrievalState:
    valid: bool
    defender_position: str | None
    adjacent_position: str | None
    defender_start_x_ft: float
    defender_start_y_ft: float
    ball_x_ft: float
    ball_y_ft: float
    retrieval_distance_ft: float
    reaction_time_s: float
    effective_fielder_speed_fps: float
    movement_time_s: float
    pickup_transfer_time_s: float
    total_retrieval_time_s: float
    defender_rating: float
    retrieval_model_version: str
    invalid_reason: str | None = None

    def __post_init__(self) -> None:
        numeric = (
            self.defender_start_x_ft,
            self.defender_start_y_ft,
            self.ball_x_ft,
            self.ball_y_ft,
            self.retrieval_distance_ft,
            self.reaction_time_s,
            self.effective_fielder_speed_fps,
            self.movement_time_s,
            self.pickup_transfer_time_s,
            self.total_retrieval_time_s,
            self.defender_rating,
        )
        if not all(math.isfinite(value) for value in numeric):
            raise ValueError("retrieval values must be finite")
        nonnegative = (
            self.retrieval_distance_ft,
            self.reaction_time_s,
            self.effective_fielder_speed_fps,
            self.movement_time_s,
            self.pickup_transfer_time_s,
            self.total_retrieval_time_s,
        )
        if any(value < 0.0 for value in nonnegative):
            raise ValueError("retrieval distance/time/speed cannot be negative")
        if self.valid and self.effective_fielder_speed_fps <= 0.0:
            raise ValueError("valid retrieval requires positive fielder speed")
        if self.retrieval_model_version != P.RETRIEVAL_MODEL_VERSION:
            raise ValueError("unsupported retrieval model version")


@dataclass(frozen=True)
class BaseDefenseTiming:
    target_base: str
    target_x_ft: float
    target_y_ft: float
    throw_distance_ft: float
    effective_throw_speed_fps: float
    transfer_release_time_s: float
    relay_penalty_s: float
    total_throw_time_s: float
    defense_arrival_time_s: float

    def __post_init__(self) -> None:
        numeric = (
            self.target_x_ft,
            self.target_y_ft,
            self.throw_distance_ft,
            self.effective_throw_speed_fps,
            self.transfer_release_time_s,
            self.relay_penalty_s,
            self.total_throw_time_s,
            self.defense_arrival_time_s,
        )
        if not all(math.isfinite(value) for value in numeric):
            raise ValueError("base-defense timing must be finite")
        if self.target_base not in {"1B", "2B", "3B"}:
            raise ValueError("unsupported base target")
        if self.throw_distance_ft < 0.0:
            raise ValueError("throw distance cannot be negative")
        if self.effective_throw_speed_fps <= 0.0:
            raise ValueError("throw speed must be positive")
        if min(self.transfer_release_time_s, self.relay_penalty_s, self.total_throw_time_s, self.defense_arrival_time_s) < 0.0:
            raise ValueError("throw/arrival times cannot be negative")


@dataclass(frozen=True)
class PhysicalHitResolution:
    valid: bool
    retrieval: RetrievalState
    defense_1b: BaseDefenseTiming | None
    defense_2b: BaseDefenseTiming | None
    defense_3b: BaseDefenseTiming | None
    runner_time_1b_s: float
    runner_time_2b_s: float
    runner_time_3b_s: float
    margin_1b_s: float
    margin_2b_s: float
    margin_3b_s: float
    physical_result_shadow: str | None
    invalid_reason: str | None = None

    def __post_init__(self) -> None:
        numeric = (
            self.runner_time_1b_s,
            self.runner_time_2b_s,
            self.runner_time_3b_s,
            self.margin_1b_s,
            self.margin_2b_s,
            self.margin_3b_s,
        )
        if not all(math.isfinite(value) for value in numeric):
            raise ValueError("physical hit timing values must be finite")
        if min(self.runner_time_1b_s, self.runner_time_2b_s, self.runner_time_3b_s) < 0.0:
            raise ValueError("runner times cannot be negative")
        if self.physical_result_shadow not in _ALLOWED_RESULTS:
            raise ValueError("Phase-2E-B cannot produce unsupported result or HR")


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _invalid_retrieval(reason: str, *, defender_rating: float = 100.0) -> RetrievalState:
    safe_rating = defender_rating if math.isfinite(defender_rating) else P.DEFENSE_RATING_REFERENCE
    return RetrievalState(
        valid=False,
        defender_position=None,
        adjacent_position=None,
        defender_start_x_ft=0.0,
        defender_start_y_ft=0.0,
        ball_x_ft=0.0,
        ball_y_ft=0.0,
        retrieval_distance_ft=0.0,
        reaction_time_s=0.0,
        effective_fielder_speed_fps=0.0,
        movement_time_s=0.0,
        pickup_transfer_time_s=0.0,
        total_retrieval_time_s=0.0,
        defender_rating=safe_rating,
        retrieval_model_version=P.RETRIEVAL_MODEL_VERSION,
        invalid_reason=reason,
    )


def _invalid_resolution(reason: str, retrieval: RetrievalState | None = None) -> PhysicalHitResolution:
    retrieval = retrieval or _invalid_retrieval(reason)
    return PhysicalHitResolution(
        valid=False,
        retrieval=retrieval,
        defense_1b=None,
        defense_2b=None,
        defense_3b=None,
        runner_time_1b_s=0.0,
        runner_time_2b_s=0.0,
        runner_time_3b_s=0.0,
        margin_1b_s=0.0,
        margin_2b_s=0.0,
        margin_3b_s=0.0,
        physical_result_shadow=None,
        invalid_reason=reason,
    )


def owner_for_location(ball_x_ft: float, ball_y_ft: float) -> tuple[str, str | None]:
    """Return deterministic primary/adjacent retriever from fixed depth/sector rules."""
    if not math.isfinite(ball_x_ft) or not math.isfinite(ball_y_ft):
        raise ValueError("ball location must be finite")
    radial = math.hypot(ball_x_ft, ball_y_ft)
    angle = math.degrees(math.atan2(ball_x_ft, ball_y_ft)) if radial > 0.0 else 0.0

    if radial <= P.HOME_REGION_MAX_RADIUS_FT:
        return "C", "P"
    if radial <= P.MOUND_REGION_MAX_RADIUS_FT:
        if abs(angle) <= P.MOUND_CENTER_HALF_ANGLE_DEG:
            return "P", "SS" if angle < 0.0 else "2B"
        return ("3B", "P") if angle < 0.0 else ("1B", "P")
    if radial <= P.INFIELD_MAX_RADIUS_FT:
        if angle <= -P.INFIELD_LINE_SECTOR_DEG:
            return "3B", "SS"
        if angle < 0.0:
            return "SS", "3B"
        if angle < P.INFIELD_LINE_SECTOR_DEG:
            return "2B", "1B"
        return "1B", "2B"
    if angle < -P.OUTFIELD_CENTER_SECTOR_DEG:
        return "LF", "CF"
    if angle > P.OUTFIELD_CENTER_SECTOR_DEG:
        return "RF", "CF"
    return "CF", "LF" if angle < 0.0 else "RF"


def _rating_adjusted_retrieval_terms(defender_position: str, defender_rating: float) -> tuple[float, float, float]:
    if defender_position not in P.ROLE_CLASS:
        raise ValueError("unsupported defender position")
    if not math.isfinite(defender_rating):
        raise ValueError("defender rating must be finite")
    role_class = P.ROLE_CLASS[defender_position]
    rating_effect = _clamp(
        (defender_rating - P.DEFENSE_RATING_REFERENCE) / P.DEFENSE_RATING_FULL_EFFECT_POINTS,
        -1.0,
        1.0,
    )
    reaction = _clamp(
        P.REACTION_BASELINE_S[role_class] * (1.0 - P.REACTION_RATING_MAX_FRACTION * rating_effect),
        P.REACTION_MIN_S,
        P.REACTION_MAX_S,
    )
    speed = _clamp(
        P.EFFECTIVE_FIELDER_SPEED_FPS[role_class] * (1.0 + P.SPEED_RATING_MAX_FRACTION * rating_effect),
        P.FIELDER_SPEED_MIN_FPS,
        P.FIELDER_SPEED_MAX_FPS,
    )
    pickup = P.PICKUP_TRANSFER_BASELINE_S[role_class]
    return reaction, speed, pickup


def build_retrieval_state(
    *,
    ground_travel: GroundTravelState | None,
    defender_rating: float,
) -> RetrievalState:
    if ground_travel is None:
        return _invalid_retrieval("missing_ground_travel", defender_rating=defender_rating)
    if not ground_travel.valid:
        return _invalid_retrieval("invalid_ground_travel", defender_rating=defender_rating)
    if not math.isfinite(defender_rating):
        return _invalid_retrieval("invalid_defender_rating")
    ball_x = ground_travel.final_x_ft
    ball_y = ground_travel.final_y_ft
    if not math.isfinite(ball_x) or not math.isfinite(ball_y):
        return _invalid_retrieval("non_finite_final_location", defender_rating=defender_rating)

    try:
        defender, adjacent = owner_for_location(ball_x, ball_y)
        start_x, start_y = P.NOMINAL_DEFENDER_ANCHORS_FT[defender]
        distance = math.hypot(ball_x - start_x, ball_y - start_y)
        reaction, speed, pickup = _rating_adjusted_retrieval_terms(defender, defender_rating)
        movement = distance / speed
        total = reaction + movement + pickup
    except (KeyError, ValueError, OverflowError):
        return _invalid_retrieval("invalid_retrieval_derivation", defender_rating=defender_rating)

    derived = (start_x, start_y, distance, reaction, speed, pickup, movement, total)
    if not all(math.isfinite(value) for value in derived):
        return _invalid_retrieval("non_finite_retrieval_derivation", defender_rating=defender_rating)
    if distance < 0.0 or reaction < 0.0 or speed <= 0.0 or pickup < 0.0 or movement < 0.0 or total < 0.0:
        return _invalid_retrieval("invalid_retrieval_bounds", defender_rating=defender_rating)
    if total > P.MAX_VALID_TIME_S:
        return _invalid_retrieval("retrieval_time_out_of_bounds", defender_rating=defender_rating)

    return RetrievalState(
        valid=True,
        defender_position=defender,
        adjacent_position=adjacent,
        defender_start_x_ft=start_x,
        defender_start_y_ft=start_y,
        ball_x_ft=ball_x,
        ball_y_ft=ball_y,
        retrieval_distance_ft=distance,
        reaction_time_s=reaction,
        effective_fielder_speed_fps=speed,
        movement_time_s=movement,
        pickup_transfer_time_s=pickup,
        total_retrieval_time_s=total,
        defender_rating=defender_rating,
        retrieval_model_version=P.RETRIEVAL_MODEL_VERSION,
        invalid_reason=None,
    )


def throw_timing_to_base(retrieval: RetrievalState, target_base: str) -> BaseDefenseTiming:
    if not retrieval.valid or retrieval.defender_position is None:
        raise ValueError("valid retrieval required for throw timing")
    targets = {
        "1B": (P.FIRST_BASE_X_FT, P.FIRST_BASE_Y_FT),
        "2B": (P.SECOND_BASE_X_FT, P.SECOND_BASE_Y_FT),
        "3B": (P.THIRD_BASE_X_FT, P.THIRD_BASE_Y_FT),
    }
    if target_base not in targets:
        raise ValueError("unsupported target base")
    target_x, target_y = targets[target_base]
    role_class = P.ROLE_CLASS[retrieval.defender_position]
    speed_fps = P.EFFECTIVE_THROW_SPEED_MPH[role_class] * P.MPH_TO_FPS
    if not math.isfinite(speed_fps) or speed_fps <= 0.0:
        raise ValueError("invalid effective throw speed")
    distance = math.hypot(target_x - retrieval.ball_x_ft, target_y - retrieval.ball_y_ft)
    release = P.THROW_RELEASE_DELAY_S[role_class]
    relay = P.RELAY_PENALTY_S if distance > P.RELAY_DISTANCE_THRESHOLD_FT else 0.0
    total_throw = release + distance / speed_fps + relay
    arrival = retrieval.total_retrieval_time_s + total_throw
    return BaseDefenseTiming(
        target_base=target_base,
        target_x_ft=target_x,
        target_y_ft=target_y,
        throw_distance_ft=distance,
        effective_throw_speed_fps=speed_fps,
        transfer_release_time_s=release,
        relay_penalty_s=relay,
        total_throw_time_s=total_throw,
        defense_arrival_time_s=arrival,
    )


def runner_arrival_times(runner_speed_rating: float) -> tuple[float, float, float]:
    if not math.isfinite(runner_speed_rating):
        raise ValueError("runner speed rating must be finite")
    multiplier = _clamp(
        1.0 - (runner_speed_rating - P.RUNNER_SPEED_REFERENCE) * P.RUNNER_TIME_PER_RATING_POINT,
        P.RUNNER_TIME_MULTIPLIER_MIN,
        P.RUNNER_TIME_MULTIPLIER_MAX,
    )
    first = P.HOME_START_DELAY_S + P.FIRST_LEG_REFERENCE_S * multiplier
    extra_leg = P.BASE_LEG_REFERENCE_S * multiplier + P.TURN_PENALTY_S
    second = first + extra_leg
    third = second + extra_leg
    if not all(math.isfinite(value) and 0.0 <= value <= P.MAX_VALID_TIME_S for value in (first, second, third)):
        raise ValueError("invalid runner timing")
    return first, second, third


def resolve_physical_hit_shadow(
    *,
    ground_travel: GroundTravelState | None,
    defensive_resolution: DefensiveResolution | None,
    defender_rating: float,
    runner_speed_rating: float,
) -> PhysicalHitResolution:
    """Resolve deterministic OUT/1B/2B/3B shadow without gameplay authority."""
    if defensive_resolution is not None and defensive_resolution.valid and defensive_resolution.physical_out_shadow:
        retrieval = _invalid_retrieval("air_caught", defender_rating=defender_rating)
        return PhysicalHitResolution(
            valid=True,
            retrieval=retrieval,
            defense_1b=None,
            defense_2b=None,
            defense_3b=None,
            runner_time_1b_s=0.0,
            runner_time_2b_s=0.0,
            runner_time_3b_s=0.0,
            margin_1b_s=0.0,
            margin_2b_s=0.0,
            margin_3b_s=0.0,
            physical_result_shadow="OUT",
            invalid_reason=None,
        )

    retrieval = build_retrieval_state(ground_travel=ground_travel, defender_rating=defender_rating)
    if not retrieval.valid:
        return _invalid_resolution(retrieval.invalid_reason or "invalid_retrieval", retrieval)
    try:
        runner_1b, runner_2b, runner_3b = runner_arrival_times(runner_speed_rating)
        defense_1b = throw_timing_to_base(retrieval, "1B")
        defense_2b = throw_timing_to_base(retrieval, "2B")
        defense_3b = throw_timing_to_base(retrieval, "3B")
    except (ValueError, OverflowError):
        return _invalid_resolution("invalid_timing_derivation", retrieval)

    margin_1b = defense_1b.defense_arrival_time_s - runner_1b
    margin_2b = defense_2b.defense_arrival_time_s - runner_2b
    margin_3b = defense_3b.defense_arrival_time_s - runner_3b
    if not all(math.isfinite(value) for value in (margin_1b, margin_2b, margin_3b)):
        return _invalid_resolution("non_finite_timing_margin", retrieval)

    # Deterministic tie rule: defense_time <= runner_time means defense wins.
    if margin_1b <= 0.0:
        result = "OUT"
    elif margin_2b <= 0.0:
        result = "1B"
    elif margin_3b <= 0.0:
        result = "2B"
    else:
        result = "3B"

    return PhysicalHitResolution(
        valid=True,
        retrieval=retrieval,
        defense_1b=defense_1b,
        defense_2b=defense_2b,
        defense_3b=defense_3b,
        runner_time_1b_s=runner_1b,
        runner_time_2b_s=runner_2b,
        runner_time_3b_s=runner_3b,
        margin_1b_s=margin_1b,
        margin_2b_s=margin_2b,
        margin_3b_s=margin_3b,
        physical_result_shadow=result,
        invalid_reason=None,
    )
