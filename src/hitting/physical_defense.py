"""Phase 2D O(1) airborne defensive-opportunity and catch shadow model.

This module is diagnostic/shadow-only. Legacy defense in ``src.hitting.defense``
remains authoritative for gameplay outcomes and canonical RNG consumption.
The model intentionally avoids route simulation, nearest-fielder search, frame
stepping, and iterative physics. All per-BIP work is fixed-cost O(1).
"""
from __future__ import annotations

from dataclasses import dataclass
import math

from .stadium import WallInteraction
from .trajectory import BattedBallTrajectory

# Engineering baselines informed by the Phase-2D research pack. These are not
# claimed as measured KBO averages or calibrated KBO coefficients.
LF_ANCHOR_X_FT = -131.66
LF_ANCHOR_Y_FT = 258.39
CF_ANCHOR_X_FT = 0.0
CF_ANCHOR_Y_FT = 315.0
RF_ANCHOR_X_FT = 131.66
RF_ANCHOR_Y_FT = 258.39

LF_CF_BOUNDARY_DEG = -15.0
CF_RF_BOUNDARY_DEG = 15.0
DIRECTION_RADIAL_THRESHOLD_FT = 10.0
NEAR_WALL_DISTANCE_FT = 20.0

BASE_LOGIT_INTERCEPT = 2.0
TIME_LOGIT_PER_S = 1.35
DISTANCE_LOGIT_PER_FT = -0.075
DIRECTION_LOGIT = {
    "in": 0.35,
    "lateral": 0.0,
    "back": -0.45,
}
TRAJECTORY_CLASS_LOGIT = {
    "line_drive": -0.15,
    "fly_ball": 0.0,
    "popup": 0.10,
}
WALL_LOGIT_PENALTY = -0.65
DEFENSE_LOGIT_PER_RATING_POINT = 0.025
DEFENSE_LOGIT_ADJUSTMENT_LIMIT = 1.0
PROBABILITY_EPSILON = 1e-9

_ALLOWED_DIRECTIONS = {"in", "lateral", "back", "invalid"}
_ALLOWED_AIR_CLASSES = frozenset(TRAJECTORY_CLASS_LOGIT)


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _sigmoid(value: float) -> float:
    if value >= 60.0:
        return 1.0
    if value <= -60.0:
        return 0.0
    return 1.0 / (1.0 + math.exp(-value))


def _logit(probability: float) -> float:
    p = _clamp(probability, PROBABILITY_EPSILON, 1.0 - PROBABILITY_EPSILON)
    return math.log(p / (1.0 - p))


@dataclass(frozen=True)
class DefensiveOpportunity:
    valid: bool
    defender_position: str
    opportunity_type: str
    catch_x_ft: float
    catch_y_ft: float
    nominal_start_x_ft: float
    nominal_start_y_ft: float
    required_distance_ft: float
    opportunity_time_s: float
    direction_class: str
    near_wall: bool
    baseline_catch_probability: float
    defender_rating: float
    adjusted_catch_probability: float

    def __post_init__(self) -> None:
        numeric = (
            self.catch_x_ft,
            self.catch_y_ft,
            self.nominal_start_x_ft,
            self.nominal_start_y_ft,
            self.required_distance_ft,
            self.opportunity_time_s,
            self.baseline_catch_probability,
            self.defender_rating,
            self.adjusted_catch_probability,
        )
        if not all(math.isfinite(value) for value in numeric):
            raise ValueError("defensive opportunity values must be finite")
        if self.required_distance_ft < 0.0 or self.opportunity_time_s < 0.0:
            raise ValueError("defensive opportunity distance/time cannot be negative")
        if self.direction_class not in _ALLOWED_DIRECTIONS:
            raise ValueError("unsupported defensive direction class")
        if not 0.0 <= self.baseline_catch_probability <= 1.0:
            raise ValueError("baseline catch probability outside [0, 1]")
        if not 0.0 <= self.adjusted_catch_probability <= 1.0:
            raise ValueError("adjusted catch probability outside [0, 1]")


@dataclass(frozen=True)
class DefensiveResolution:
    valid: bool
    opportunity: DefensiveOpportunity
    catch_probability: float
    roll: float | None
    physical_out_shadow: bool

    def __post_init__(self) -> None:
        if not math.isfinite(self.catch_probability):
            raise ValueError("catch probability must be finite")
        if not 0.0 <= self.catch_probability <= 1.0:
            raise ValueError("catch probability outside [0, 1]")
        if self.roll is not None:
            if not math.isfinite(self.roll) or not 0.0 <= self.roll < 1.0:
                raise ValueError("defensive shadow roll must be finite in [0, 1)")
        if not self.valid and self.physical_out_shadow:
            raise ValueError("invalid defensive resolution cannot create a physical out")


def _invalid_opportunity(*, defender_rating: float, opportunity_type: str) -> DefensiveOpportunity:
    rating = defender_rating if math.isfinite(defender_rating) else 100.0
    return DefensiveOpportunity(
        valid=False,
        defender_position="NONE",
        opportunity_type=opportunity_type,
        catch_x_ft=0.0,
        catch_y_ft=0.0,
        nominal_start_x_ft=0.0,
        nominal_start_y_ft=0.0,
        required_distance_ft=0.0,
        opportunity_time_s=0.0,
        direction_class="invalid",
        near_wall=False,
        baseline_catch_probability=0.0,
        defender_rating=rating,
        adjusted_catch_probability=0.0,
    )


def _owner_and_anchor(catch_x_ft: float, catch_y_ft: float) -> tuple[str, float, float]:
    spray_angle_deg = math.degrees(math.atan2(catch_x_ft, catch_y_ft))
    if spray_angle_deg < LF_CF_BOUNDARY_DEG:
        return "LF", LF_ANCHOR_X_FT, LF_ANCHOR_Y_FT
    if spray_angle_deg > CF_RF_BOUNDARY_DEG:
        return "RF", RF_ANCHOR_X_FT, RF_ANCHOR_Y_FT
    return "CF", CF_ANCHOR_X_FT, CF_ANCHOR_Y_FT


def _direction_class(
    *,
    catch_x_ft: float,
    catch_y_ft: float,
    start_x_ft: float,
    start_y_ft: float,
) -> str:
    move_x = catch_x_ft - start_x_ft
    move_y = catch_y_ft - start_y_ft
    start_radius = math.hypot(start_x_ft, start_y_ft)
    if start_radius <= 1e-12:
        return "lateral"
    outward_x = start_x_ft / start_radius
    outward_y = start_y_ft / start_radius
    radial_component = move_x * outward_x + move_y * outward_y
    if radial_component > DIRECTION_RADIAL_THRESHOLD_FT:
        return "back"
    if radial_component < -DIRECTION_RADIAL_THRESHOLD_FT:
        return "in"
    return "lateral"


def _probabilities(
    *,
    trajectory_class: str,
    required_distance_ft: float,
    opportunity_time_s: float,
    direction_class: str,
    near_wall: bool,
    defender_rating: float,
) -> tuple[float, float]:
    baseline_logit = (
        BASE_LOGIT_INTERCEPT
        + TIME_LOGIT_PER_S * opportunity_time_s
        + DISTANCE_LOGIT_PER_FT * required_distance_ft
        + DIRECTION_LOGIT[direction_class]
        + TRAJECTORY_CLASS_LOGIT[trajectory_class]
        + (WALL_LOGIT_PENALTY if near_wall else 0.0)
    )
    baseline = _clamp(_sigmoid(baseline_logit), 0.0, 1.0)
    rating_adjustment = _clamp(
        (defender_rating - 100.0) * DEFENSE_LOGIT_PER_RATING_POINT,
        -DEFENSE_LOGIT_ADJUSTMENT_LIMIT,
        DEFENSE_LOGIT_ADJUSTMENT_LIMIT,
    )
    adjusted = _sigmoid(_logit(baseline) + rating_adjustment)
    return baseline, _clamp(adjusted, 0.0, 1.0)


def build_defensive_opportunity(
    *,
    trajectory: BattedBallTrajectory | None,
    wall_interaction: WallInteraction | None,
    defender_rating: float,
    is_fair_shadow: bool,
) -> DefensiveOpportunity:
    """Build one deterministic O(1) airborne catch opportunity.

    Ground-like balls remain explicitly outside Phase-2D V1. Wall-clearing or
    wall-intersecting flight paths are also left unresolved rather than being
    converted into a false catch opportunity before wall rebound physics exists.
    """
    if not math.isfinite(defender_rating):
        return _invalid_opportunity(
            defender_rating=100.0,
            opportunity_type="invalid_defender_rating",
        )
    if trajectory is None:
        return _invalid_opportunity(
            defender_rating=defender_rating,
            opportunity_type="missing_trajectory",
        )
    if not trajectory.valid:
        return _invalid_opportunity(
            defender_rating=defender_rating,
            opportunity_type="invalid_trajectory",
        )
    if trajectory.trajectory_class not in _ALLOWED_AIR_CLASSES:
        return _invalid_opportunity(
            defender_rating=defender_rating,
            opportunity_type="ground_not_modeled_v1",
        )
    if not is_fair_shadow:
        return _invalid_opportunity(
            defender_rating=defender_rating,
            opportunity_type="shadow_foul",
        )
    if wall_interaction is None:
        return _invalid_opportunity(
            defender_rating=defender_rating,
            opportunity_type="missing_wall_context",
        )

    wall_values = (
        wall_interaction.wall_radius_ft,
        wall_interaction.wall_height_ft,
        wall_interaction.ball_height_at_wall_ft,
        wall_interaction.clearance_ft,
    )
    if not all(math.isfinite(value) for value in wall_values):
        return _invalid_opportunity(
            defender_rating=defender_rating,
            opportunity_type="invalid_wall_context",
        )
    if wall_interaction.wall_radius_ft <= 0.0 or wall_interaction.wall_height_ft <= 0.0:
        return _invalid_opportunity(
            defender_rating=defender_rating,
            opportunity_type="invalid_wall_context",
        )
    if wall_interaction.clears_wall or wall_interaction.physical_hr_shadow:
        return _invalid_opportunity(
            defender_rating=defender_rating,
            opportunity_type="over_wall",
        )
    if wall_interaction.reaches_wall:
        return _invalid_opportunity(
            defender_rating=defender_rating,
            opportunity_type="wall_intersection_unmodeled_v1",
        )

    catch_x = trajectory.landing_x_ft
    catch_y = trajectory.landing_y_ft
    opportunity_time = trajectory.hang_time_s
    if not all(math.isfinite(value) for value in (catch_x, catch_y, opportunity_time)):
        return _invalid_opportunity(
            defender_rating=defender_rating,
            opportunity_type="invalid_catch_geometry",
        )
    if opportunity_time < 0.0:
        return _invalid_opportunity(
            defender_rating=defender_rating,
            opportunity_type="invalid_catch_geometry",
        )

    defender, start_x, start_y = _owner_and_anchor(catch_x, catch_y)
    required_distance = math.hypot(catch_x - start_x, catch_y - start_y)
    if not math.isfinite(required_distance) or required_distance < 0.0:
        return _invalid_opportunity(
            defender_rating=defender_rating,
            opportunity_type="invalid_required_distance",
        )

    direction = _direction_class(
        catch_x_ft=catch_x,
        catch_y_ft=catch_y,
        start_x_ft=start_x,
        start_y_ft=start_y,
    )
    radial_catch_distance = math.hypot(catch_x, catch_y)
    wall_gap = wall_interaction.wall_radius_ft - radial_catch_distance
    near_wall = 0.0 <= wall_gap <= NEAR_WALL_DISTANCE_FT

    baseline, adjusted = _probabilities(
        trajectory_class=trajectory.trajectory_class,
        required_distance_ft=required_distance,
        opportunity_time_s=opportunity_time,
        direction_class=direction,
        near_wall=near_wall,
        defender_rating=defender_rating,
    )
    if not math.isfinite(baseline) or not math.isfinite(adjusted):
        return _invalid_opportunity(
            defender_rating=defender_rating,
            opportunity_type="invalid_probability",
        )

    return DefensiveOpportunity(
        valid=True,
        defender_position=defender,
        opportunity_type="air_catch",
        catch_x_ft=catch_x,
        catch_y_ft=catch_y,
        nominal_start_x_ft=start_x,
        nominal_start_y_ft=start_y,
        required_distance_ft=required_distance,
        opportunity_time_s=opportunity_time,
        direction_class=direction,
        near_wall=near_wall,
        baseline_catch_probability=baseline,
        defender_rating=defender_rating,
        adjusted_catch_probability=adjusted,
    )


def resolve_defensive_shadow(
    opportunity: DefensiveOpportunity,
    *,
    roll: float | None,
) -> DefensiveResolution:
    """Resolve one child-RNG shadow roll without touching gameplay authority."""
    if not opportunity.valid:
        return DefensiveResolution(
            valid=False,
            opportunity=opportunity,
            catch_probability=0.0,
            roll=None,
            physical_out_shadow=False,
        )
    if roll is None or not math.isfinite(roll) or not 0.0 <= roll < 1.0:
        return DefensiveResolution(
            valid=False,
            opportunity=opportunity,
            catch_probability=opportunity.adjusted_catch_probability,
            roll=None,
            physical_out_shadow=False,
        )
    probability = opportunity.adjusted_catch_probability
    return DefensiveResolution(
        valid=True,
        opportunity=opportunity,
        catch_probability=probability,
        roll=roll,
        physical_out_shadow=bool(roll < probability),
    )
