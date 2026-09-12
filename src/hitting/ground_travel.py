"""Phase 2E-A deterministic O(1) post-impact ground-travel shadow model.

This layer starts from the canonical Phase-2B first-ground state and reuses the
Phase-2C wall radius. It never changes gameplay authority, never consumes RNG,
and never simulates repeated bounces, rolling timesteps, field meshes, or wall
rebounds.
"""
from __future__ import annotations

from dataclasses import dataclass
import math

from . import ground_travel_parameters as P
from .stadium import WallInteraction
from .trajectory import BattedBallTrajectory

_ALLOWED_CLASSES = frozenset(P.IMPACT_SPEED_CORRECTION)


@dataclass(frozen=True)
class GroundTravelState:
    valid: bool
    surface_class: str
    impact_horizontal_speed_fps: float
    post_impact_horizontal_speed_fps: float
    bounce_distance_ft: float
    rollout_start_speed_fps: float
    rollout_distance_ft: float
    ground_travel_distance_ft: float
    first_impact_x_ft: float
    first_impact_y_ft: float
    final_x_ft: float
    final_y_ft: float
    final_radial_distance_ft: float
    wall_ground_contact: bool
    ground_model_version: str
    invalid_reason: str | None = None

    def __post_init__(self) -> None:
        numeric = (
            self.impact_horizontal_speed_fps,
            self.post_impact_horizontal_speed_fps,
            self.bounce_distance_ft,
            self.rollout_start_speed_fps,
            self.rollout_distance_ft,
            self.ground_travel_distance_ft,
            self.first_impact_x_ft,
            self.first_impact_y_ft,
            self.final_x_ft,
            self.final_y_ft,
            self.final_radial_distance_ft,
        )
        if not all(math.isfinite(value) for value in numeric):
            raise ValueError("ground-travel values must be finite")
        nonnegative = (
            self.impact_horizontal_speed_fps,
            self.post_impact_horizontal_speed_fps,
            self.bounce_distance_ft,
            self.rollout_start_speed_fps,
            self.rollout_distance_ft,
            self.ground_travel_distance_ft,
            self.final_radial_distance_ft,
        )
        if any(value < 0.0 for value in nonnegative):
            raise ValueError("ground-travel speed/distance cannot be negative")
        if self.surface_class != P.SURFACE_CLASS_NEUTRAL:
            raise ValueError("Phase-2E-A V1 supports neutral surface only")
        if self.ground_model_version != P.GROUND_MODEL_VERSION:
            raise ValueError("unsupported ground-travel model version")


def rollout_distance_ft(speed_fps: float, deceleration_ftps2: float) -> float:
    """Return O(1) stop distance under constant positive effective deceleration."""
    if not math.isfinite(speed_fps) or speed_fps < 0.0:
        raise ValueError("rollout speed must be finite and non-negative")
    if not math.isfinite(deceleration_ftps2) or deceleration_ftps2 <= 0.0:
        raise ValueError("rollout deceleration must be finite and positive")
    if speed_fps == 0.0:
        return 0.0
    return (speed_fps * speed_fps) / (2.0 * deceleration_ftps2)


def impact_horizontal_speed_proxy(
    *,
    first_impact_distance_ft: float,
    hang_time_s: float,
    trajectory_class: str,
) -> float:
    """Estimate horizontal speed at first impact from realized Phase-2B state."""
    if trajectory_class not in _ALLOWED_CLASSES:
        raise ValueError("unsupported trajectory class")
    if not math.isfinite(first_impact_distance_ft) or first_impact_distance_ft < 0.0:
        raise ValueError("first-impact distance must be finite and non-negative")
    if not math.isfinite(hang_time_s) or hang_time_s <= P.HANG_TIME_EPSILON_S:
        raise ValueError("hang time is not valid for impact-speed proxy")
    average_horizontal = first_impact_distance_ft / hang_time_s
    corrected = average_horizontal * P.IMPACT_SPEED_CORRECTION[trajectory_class]
    return max(0.0, min(P.MAX_IMPACT_HORIZONTAL_SPEED_FPS, corrected))


def _invalid_state(reason: str) -> GroundTravelState:
    return GroundTravelState(
        valid=False,
        surface_class=P.SURFACE_CLASS_NEUTRAL,
        impact_horizontal_speed_fps=0.0,
        post_impact_horizontal_speed_fps=0.0,
        bounce_distance_ft=0.0,
        rollout_start_speed_fps=0.0,
        rollout_distance_ft=0.0,
        ground_travel_distance_ft=0.0,
        first_impact_x_ft=0.0,
        first_impact_y_ft=0.0,
        final_x_ft=0.0,
        final_y_ft=0.0,
        final_radial_distance_ft=0.0,
        wall_ground_contact=False,
        ground_model_version=P.GROUND_MODEL_VERSION,
        invalid_reason=reason,
    )


def generate_ground_travel_state(
    *,
    trajectory: BattedBallTrajectory | None,
    wall_interaction: WallInteraction | None,
    spray_angle_deg: float,
    effective_deceleration_ftps2: float = P.EFFECTIVE_ROLLOUT_DECELERATION_FTPS2,
) -> GroundTravelState:
    """Return deterministic post-first-impact travel and final ground location."""
    if trajectory is None:
        return _invalid_state("missing_trajectory")
    if not trajectory.valid:
        return _invalid_state("invalid_trajectory")
    if trajectory.trajectory_class not in _ALLOWED_CLASSES:
        return _invalid_state("unsupported_trajectory_class")
    if wall_interaction is None:
        return _invalid_state("missing_wall_context")

    geometry = (
        trajectory.first_ground_impact_distance_ft,
        trajectory.landing_x_ft,
        trajectory.landing_y_ft,
        trajectory.hang_time_s,
        wall_interaction.wall_radius_ft,
        spray_angle_deg,
        effective_deceleration_ftps2,
    )
    if not all(math.isfinite(value) for value in geometry):
        return _invalid_state("non_finite_input")
    if trajectory.first_ground_impact_distance_ft < 0.0:
        return _invalid_state("negative_first_impact_distance")
    if trajectory.hang_time_s <= P.HANG_TIME_EPSILON_S:
        return _invalid_state("invalid_hang_time")
    if wall_interaction.wall_radius_ft <= P.WALL_RADIUS_EPSILON_FT:
        return _invalid_state("invalid_wall_radius")
    if effective_deceleration_ftps2 <= 0.0:
        return _invalid_state("invalid_rollout_deceleration")

    # If the airborne trajectory has already reached the wall, the canonical
    # first-ground point is not physically available as the start of this V1
    # ground-travel layer. Wall rebound/carom is explicitly out of scope.
    if wall_interaction.reaches_wall:
        return _invalid_state("air_wall_precedes_ground")

    try:
        impact_speed = impact_horizontal_speed_proxy(
            first_impact_distance_ft=trajectory.first_ground_impact_distance_ft,
            hang_time_s=trajectory.hang_time_s,
            trajectory_class=trajectory.trajectory_class,
        )
        post_impact_speed = impact_speed * P.POST_IMPACT_SPEED_RETENTION[trajectory.trajectory_class]
        bounce_distance = post_impact_speed * P.BOUNCE_TIME_PROXY_S[trajectory.trajectory_class]
        rollout_start_speed = post_impact_speed * P.ROLLOUT_SPEED_RETENTION[trajectory.trajectory_class]
        rollout_distance = rollout_distance_ft(rollout_start_speed, effective_deceleration_ftps2)
    except (ValueError, OverflowError):
        return _invalid_state("invalid_derived_ground_state")

    derived = (impact_speed, post_impact_speed, bounce_distance, rollout_start_speed, rollout_distance)
    if not all(math.isfinite(value) and value >= 0.0 for value in derived):
        return _invalid_state("invalid_derived_ground_state")

    ground_travel = min(
        P.MAX_GROUND_TRAVEL_DISTANCE_FT,
        bounce_distance + rollout_distance,
    )
    first_x = trajectory.landing_x_ft
    first_y = trajectory.landing_y_ft
    first_radial = math.hypot(first_x, first_y)
    if not math.isfinite(first_radial):
        return _invalid_state("invalid_first_impact_geometry")

    unconstrained_radial = first_radial + ground_travel
    wall_radius = wall_interaction.wall_radius_ft
    final_radial = min(unconstrained_radial, wall_radius)
    wall_contact = bool(unconstrained_radial >= wall_radius)

    spray = math.radians(spray_angle_deg)
    unit_x = math.sin(spray)
    unit_y = math.cos(spray)
    final_x = final_radial * unit_x
    final_y = final_radial * unit_y
    if not all(math.isfinite(value) for value in (final_x, final_y, final_radial)):
        return _invalid_state("invalid_final_geometry")

    # Report actual realized post-impact travel after deterministic wall clamp.
    realized_ground_travel = max(0.0, final_radial - first_radial)
    return GroundTravelState(
        valid=True,
        surface_class=P.SURFACE_CLASS_NEUTRAL,
        impact_horizontal_speed_fps=impact_speed,
        post_impact_horizontal_speed_fps=post_impact_speed,
        bounce_distance_ft=bounce_distance,
        rollout_start_speed_fps=rollout_start_speed,
        rollout_distance_ft=rollout_distance,
        ground_travel_distance_ft=realized_ground_travel,
        first_impact_x_ft=first_x,
        first_impact_y_ft=first_y,
        final_x_ft=final_x,
        final_y_ft=final_y,
        final_radial_distance_ft=final_radial,
        wall_ground_contact=wall_contact,
        ground_model_version=P.GROUND_MODEL_VERSION,
        invalid_reason=None,
    )
