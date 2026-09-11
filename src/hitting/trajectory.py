"""Phase 2B O(1) analytical/algebraic batted-ball trajectory layer.

The trajectory is descriptive/shadow-only in Phase 2B. Legacy HR/XBH/defense
resolution remains authoritative. Runtime stepping, numerical integration, and
iterative root solving are intentionally absent.
"""
from __future__ import annotations

from dataclasses import dataclass
import math

from .physical import BattedBallState
from . import trajectory_parameters as P


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


@dataclass(frozen=True)
class BattedBallTrajectory:
    """First-ground trajectory summary in canonical field coordinates.

    Coordinate convention:
    - home plate = (0, 0)
    - center field = +Y
    - left field = negative X
    - right field = positive X
    - spray 0 deg = +Y

    All distances/heights are feet; time is seconds.
    """

    horizontal_distance_ft: float
    hang_time_s: float
    apex_height_ft: float
    landing_x_ft: float
    landing_y_ft: float
    trajectory_class: str
    valid: bool = True

    def __post_init__(self) -> None:
        values = (
            self.horizontal_distance_ft,
            self.hang_time_s,
            self.apex_height_ft,
            self.landing_x_ft,
            self.landing_y_ft,
        )
        if not all(math.isfinite(value) for value in values):
            raise ValueError("trajectory values must be finite")
        if self.horizontal_distance_ft < P.DISTANCE_MIN_FT:
            raise ValueError("horizontal distance cannot be negative")
        if self.hang_time_s < P.HANG_TIME_MIN_S:
            raise ValueError("hang time cannot be negative")
        if self.apex_height_ft < P.APEX_MIN_FT:
            raise ValueError("apex height cannot be negative")
        if self.trajectory_class not in {"ground_like", "line_drive", "fly_ball", "popup"}:
            raise ValueError("unsupported trajectory_class")

    @property
    def carry_distance_ft(self) -> float:
        return self.horizontal_distance_ft

    @property
    def first_ground_impact_distance_ft(self) -> float:
        return self.horizontal_distance_ft


def _first_ground_impact(exit_velocity_mph: float, launch_angle_deg: float) -> tuple[float, float]:
    """Exact first ground intersection of a 3-ft launch, with fixed x attenuation."""
    speed = max(0.0, exit_velocity_mph) * P.MPH_TO_FPS
    theta = math.radians(launch_angle_deg)
    vx = max(0.0, speed * math.cos(theta))
    vy = speed * math.sin(theta)
    root = math.sqrt(max(0.0, vy * vy + 2.0 * P.GRAVITY_FTPS2 * P.LAUNCH_HEIGHT_FT))
    if vy >= 0.0:
        time_s = (vy + root) / P.GRAVITY_FTPS2
    else:
        # Algebraically equivalent rationalized root avoids cancellation for
        # steeply negative launch angles.
        time_s = (2.0 * P.LAUNCH_HEIGHT_FT) / max(1e-12, root - vy)
    distance_ft = vx * time_s * P.GROUND_HORIZONTAL_ATTENUATION
    return max(0.0, distance_ft), max(0.0, time_s)


def _air_carry(exit_velocity_mph: float, launch_angle_deg: float) -> float:
    """Fixed-cost pre-fit baseball carry surrogate with ~29 deg optimum."""
    speed_ratio = _clamp(exit_velocity_mph / 100.0, 0.30, 1.25)
    angle_offset = launch_angle_deg - P.AIR_CARRY_PEAK_LA_DEG
    base_100 = max(
        P.AIR_CARRY_MIN_BASE_FT,
        P.AIR_CARRY_AT_100_PEAK_FT
        - P.AIR_CARRY_CURVATURE_FT_PER_DEG2 * angle_offset * angle_offset,
    )
    distance = base_100 * (speed_ratio ** P.AIR_CARRY_SPEED_EXPONENT)
    return _clamp(distance, P.DISTANCE_MIN_FT, P.AIR_CARRY_MAX_FT)


def _air_hang_time(exit_velocity_mph: float, launch_angle_deg: float) -> float:
    speed_ratio = _clamp(exit_velocity_mph / 100.0, 0.30, 1.25)
    angle = _clamp(launch_angle_deg, 0.0, 85.0)
    base_100 = (
        P.AIR_HANG_BASE_S
        + P.AIR_HANG_LINEAR_S_PER_DEG * angle
        + P.AIR_HANG_QUADRATIC_S_PER_DEG2 * angle * angle
    )
    time_s = max(0.0, base_100) * (speed_ratio ** P.AIR_HANG_SPEED_EXPONENT)
    return _clamp(time_s, P.HANG_TIME_MIN_S, P.AIR_HANG_MAX_S)


def _smooth_air_weight(launch_angle_deg: float) -> float:
    if launch_angle_deg <= 0.0:
        return 0.0
    if launch_angle_deg >= P.AIR_BLEND_FULL_DEG:
        return 1.0
    t = launch_angle_deg / P.AIR_BLEND_FULL_DEG
    return t * t * (3.0 - 2.0 * t)


def _apex_height(exit_velocity_mph: float, launch_angle_deg: float) -> float:
    speed = max(0.0, exit_velocity_mph) * P.MPH_TO_FPS
    vy = speed * math.sin(math.radians(launch_angle_deg))
    if vy <= 0.0:
        return P.LAUNCH_HEIGHT_FT
    vacuum_gain = (vy * vy) / (2.0 * P.GRAVITY_FTPS2)
    apex = P.LAUNCH_HEIGHT_FT + vacuum_gain * P.APEX_AERO_SCALE
    return _clamp(apex, P.LAUNCH_HEIGHT_FT, P.APEX_MAX_FT)


def _trajectory_class(launch_angle_deg: float) -> str:
    if launch_angle_deg < 10.0:
        return "ground_like"
    if launch_angle_deg < 25.0:
        return "line_drive"
    if launch_angle_deg < 50.0:
        return "fly_ball"
    return "popup"


def generate_batted_ball_trajectory(state: BattedBallState) -> BattedBallTrajectory:
    """Return deterministic first-ground trajectory from the Phase-2A state.

    EV/LA/spray are the only trajectory drivers. Timing/contact quality are not
    applied again because their influence is already embedded in Phase-2A EV/LA.
    """
    ev = state.exit_velocity
    la = state.launch_angle

    ground_distance, ground_time = _first_ground_impact(ev, la)
    air_distance = _air_carry(ev, la)
    air_time = _air_hang_time(ev, la)
    weight = _smooth_air_weight(la)

    distance = ground_distance + (air_distance - ground_distance) * weight
    hang_time = ground_time + (air_time - ground_time) * weight
    distance = _clamp(distance, P.DISTANCE_MIN_FT, P.AIR_CARRY_MAX_FT)
    hang_time = _clamp(hang_time, P.HANG_TIME_MIN_S, P.AIR_HANG_MAX_S)
    apex = _apex_height(ev, la)

    spray = math.radians(state.spray_angle)
    landing_x = distance * math.sin(spray)
    landing_y = distance * math.cos(spray)

    return BattedBallTrajectory(
        horizontal_distance_ft=distance,
        hang_time_s=hang_time,
        apex_height_ft=apex,
        landing_x_ft=landing_x,
        landing_y_ft=landing_y,
        trajectory_class=_trajectory_class(la),
        valid=True,
    )
