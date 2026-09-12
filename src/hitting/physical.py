"""Phase 2 physical initial-state generation for fair-contact migration.

Phase 2A owns EV/LA/timing/spray generation. Phase 2B attaches a deterministic
O(1) first-ground trajectory. Phase 2C attaches an O(1) generic-stadium wall
interaction / physical-HR shadow. Phase 2D attaches an O(1) airborne defensive
opportunity and child-RNG catch shadow. Phase 2E-A attaches deterministic O(1)
post-impact ground travel / final-location metadata while all legacy gameplay
remains canonical authority.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
import math
from typing import TYPE_CHECKING

from ..rng import RNG
from . import physical_parameters as P

if TYPE_CHECKING:
    from .trajectory import BattedBallTrajectory
    from .stadium import WallInteraction
    from .physical_defense import DefensiveOpportunity, DefensiveResolution
    from .ground_travel import GroundTravelState


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


@dataclass(frozen=True)
class BattedBallState:
    """Stable Phase-2 initial state plus trajectory/wall/defense/ground metadata.

    Units/conventions:
    - ``exit_velocity``: miles per hour.
    - ``launch_angle`` / ``spray_angle``: degrees.
    - ``timing``: normalized scalar in [-1, +1], negative=late, positive=early.
    - spray: center field 0°, left-field side negative, right-field side positive.
    - pitch locations are normalized batter-relative coordinates where
      x=-1 is inside, x=+1 outside, y=-1 low, y=+1 high.
    - trajectory/wall/defense/ground distances and coordinates are feet; time is seconds.
    """

    exit_velocity: float
    launch_angle: float
    timing: float
    spray_angle: float
    is_fair: bool
    contact_quality: float
    pitch_location_x: float
    pitch_location_y: float
    batter_side: str
    trajectory: BattedBallTrajectory | None = None
    wall_interaction: WallInteraction | None = None
    defensive_opportunity: DefensiveOpportunity | None = None
    defensive_resolution: DefensiveResolution | None = None
    ground_travel: GroundTravelState | None = None

    def __post_init__(self) -> None:
        values = (
            self.exit_velocity,
            self.launch_angle,
            self.timing,
            self.spray_angle,
            self.contact_quality,
            self.pitch_location_x,
            self.pitch_location_y,
        )
        if not all(math.isfinite(value) for value in values):
            raise ValueError("batted-ball physical state must be finite")
        if not P.EXIT_VELOCITY_MIN_MPH <= self.exit_velocity <= P.EXIT_VELOCITY_MAX_MPH:
            raise ValueError("exit_velocity outside Phase-2A bounds")
        if not P.LAUNCH_ANGLE_MIN_DEG <= self.launch_angle <= P.LAUNCH_ANGLE_MAX_DEG:
            raise ValueError("launch_angle outside Phase-2A bounds")
        if not P.TIMING_MIN <= self.timing <= P.TIMING_MAX:
            raise ValueError("timing outside normalized bounds")
        if not P.SPRAY_ANGLE_MIN_DEG <= self.spray_angle <= P.SPRAY_ANGLE_MAX_DEG:
            raise ValueError("spray_angle outside Phase-2A bounds")
        if not 0.0 <= self.contact_quality <= 1.0:
            raise ValueError("contact_quality outside [0, 1]")
        if self.batter_side not in {"L", "R"}:
            raise ValueError("batter_side must be L or R")


def pitch_location_from_zone(zone: str) -> tuple[float, float]:
    """Map the current coarse pitch-zone label to normalized contact location."""
    x = -1.0 if zone == "inside" else 1.0 if zone == "outside" else 0.0
    y = 1.0 if zone == "high" else -1.0 if zone == "low" else 0.0
    return x, y


def is_fair_spray(
    spray_angle: float,
    *,
    left_foul_line: float = P.FOUL_LINE_LEFT_DEG,
    right_foul_line: float = P.FOUL_LINE_RIGHT_DEG,
) -> bool:
    """Return fair/foul from the canonical center-field-zero spray convention."""
    return left_foul_line <= spray_angle <= right_foul_line


def _fork_seed(parent_rng, namespace: int = 0x503241) -> int:
    """Fingerprint parent state without consuming it."""
    if hasattr(parent_rng, "get_state"):
        state = parent_rng.get_state()
    elif hasattr(parent_rng, "getstate"):
        state = parent_rng.getstate()
    else:
        raise TypeError("parent_rng must expose get_state() or getstate()")
    internal = state[1]
    indices = (0, 1, 7, 31, 127, 313, len(internal) - 2, len(internal) - 1)
    seed = namespace & 0xFFFFFFFFFFFFFFFF
    for index in indices:
        word = int(internal[index]) & 0xFFFFFFFFFFFFFFFF
        seed ^= word
        seed = (seed * 0x100000001B3) & 0xFFFFFFFFFFFFFFFF
    return seed


def _timing(
    rng: RNG,
    *,
    hitter_contact: float,
    pitch_velocity_quality: float,
    pitch_location_x: float,
    pitch_location_y: float,
) -> float:
    mean = (
        pitch_velocity_quality * P.TIMING_PITCH_SPEED_SHIFT
        + pitch_location_x * P.TIMING_HORIZONTAL_LOCATION_SHIFT
        + pitch_location_y * P.TIMING_VERTICAL_LOCATION_SHIFT
    )
    sigma = _clamp(
        P.TIMING_BASE_SD
        - (hitter_contact - 100.0) * P.TIMING_CONTACT_SD_PER_POINT,
        P.TIMING_SD_MIN,
        P.TIMING_SD_MAX,
    )
    return _clamp(rng.gauss(mean, sigma), P.TIMING_MIN, P.TIMING_MAX)


def _contact_quality(
    rng: RNG,
    *,
    hitter_contact: float,
    timing: float,
    pitch_hittable_quality: float,
    pitch_movement_quality: float,
    pitch_location_quality: float,
) -> float:
    value = (
        P.CONTACT_QUALITY_BASE
        + (hitter_contact - 100.0) * P.CONTACT_QUALITY_CONTACT_GAIN_PER_POINT
        + pitch_hittable_quality * P.CONTACT_QUALITY_HITTABLE_GAIN
        - abs(timing) * P.CONTACT_QUALITY_TIMING_PENALTY
        - max(0.0, pitch_movement_quality) * P.CONTACT_QUALITY_MOVEMENT_PENALTY
        + pitch_location_quality * P.CONTACT_QUALITY_LOCATION_GAIN
        + rng.gauss(0.0, P.CONTACT_QUALITY_NOISE_SD)
    )
    return _clamp(value, 0.0, 1.0)


def _exit_velocity(
    rng: RNG,
    *,
    hitter_power: float,
    contact_quality: float,
    pitch_velocity_quality: float,
) -> float:
    noise_sd = max(
        2.5,
        P.EXIT_VELOCITY_NOISE_SD_MPH
        - contact_quality * P.EXIT_VELOCITY_QUALITY_NOISE_REDUCTION,
    )
    value = (
        P.EXIT_VELOCITY_BASE_MPH
        + contact_quality * P.EXIT_VELOCITY_QUALITY_GAIN_MPH
        + (hitter_power - 100.0) * P.EXIT_VELOCITY_POWER_GAIN_PER_POINT
        + pitch_velocity_quality * P.EXIT_VELOCITY_PITCH_SPEED_GAIN
        + rng.gauss(0.0, noise_sd)
    )
    return _clamp(value, P.EXIT_VELOCITY_MIN_MPH, P.EXIT_VELOCITY_MAX_MPH)


def _launch_angle(
    rng: RNG,
    *,
    hitter_contact: float,
    hitter_power: float,
    contact_quality: float,
    pitch_location_y: float,
) -> float:
    profile = _clamp(
        (hitter_power - hitter_contact) * P.LAUNCH_ANGLE_PROFILE_GAIN_PER_POINT,
        -P.LAUNCH_ANGLE_PROFILE_LIMIT_DEG,
        P.LAUNCH_ANGLE_PROFILE_LIMIT_DEG,
    )
    mean = (
        P.LAUNCH_ANGLE_BASE_DEG
        + pitch_location_y * P.LAUNCH_ANGLE_VERTICAL_LOCATION_GAIN
        + (contact_quality - 0.5) * P.LAUNCH_ANGLE_QUALITY_GAIN
        + profile
    )
    sigma = (
        P.LAUNCH_ANGLE_NOISE_BASE_SD_DEG
        + (1.0 - contact_quality) * P.LAUNCH_ANGLE_LOW_QUALITY_EXTRA_SD_DEG
    )
    return _clamp(
        rng.gauss(mean, sigma),
        P.LAUNCH_ANGLE_MIN_DEG,
        P.LAUNCH_ANGLE_MAX_DEG,
    )


def _spray_angle(
    rng: RNG,
    *,
    timing: float,
    batter_side: str,
    pitch_location_x: float,
    approach: str,
) -> float:
    pull_sign = -1.0 if batter_side == "R" else 1.0
    approach_bias = (
        P.SPRAY_APPROACH_BIAS_DEG if approach == "pull"
        else -P.SPRAY_APPROACH_BIAS_DEG if approach == "opposite"
        else 0.0
    )
    batter_relative = (
        timing * P.SPRAY_TIMING_GAIN_DEG
        + pitch_location_x * P.SPRAY_HORIZONTAL_LOCATION_GAIN_DEG
        + approach_bias
        + rng.gauss(0.0, P.SPRAY_NOISE_SD_DEG)
    )
    return _clamp(
        pull_sign * batter_relative,
        P.SPRAY_ANGLE_MIN_DEG,
        P.SPRAY_ANGLE_MAX_DEG,
    )


def generate_batted_ball_state(
    *,
    hitter_contact: float,
    hitter_power: float,
    batter_side: str,
    approach: str,
    pitch_zone: str,
    pitch_velocity_quality: float,
    pitch_movement_quality: float,
    pitch_location_quality: float,
    pitch_hittable_quality: float,
    parent_rng,
    defender_rating: float = 100.0,
) -> BattedBallState:
    """Generate Phase-2A/B/C/D/E-A shadow state without consuming canonical RNG."""
    side = "L" if batter_side == "L" else "R"
    pitch_x, pitch_y = pitch_location_from_zone(pitch_zone)
    rng = RNG(_fork_seed(parent_rng))
    timing = _timing(
        rng,
        hitter_contact=hitter_contact,
        pitch_velocity_quality=pitch_velocity_quality,
        pitch_location_x=pitch_x,
        pitch_location_y=pitch_y,
    )
    quality = _contact_quality(
        rng,
        hitter_contact=hitter_contact,
        timing=timing,
        pitch_hittable_quality=pitch_hittable_quality,
        pitch_movement_quality=pitch_movement_quality,
        pitch_location_quality=pitch_location_quality,
    )
    exit_velocity = _exit_velocity(
        rng,
        hitter_power=hitter_power,
        contact_quality=quality,
        pitch_velocity_quality=pitch_velocity_quality,
    )
    launch_angle = _launch_angle(
        rng,
        hitter_contact=hitter_contact,
        hitter_power=hitter_power,
        contact_quality=quality,
        pitch_location_y=pitch_y,
    )
    spray_angle = _spray_angle(
        rng,
        timing=timing,
        batter_side=side,
        pitch_location_x=pitch_x,
        approach=approach,
    )
    state = BattedBallState(
        exit_velocity=exit_velocity,
        launch_angle=launch_angle,
        timing=timing,
        spray_angle=spray_angle,
        is_fair=is_fair_spray(spray_angle),
        contact_quality=quality,
        pitch_location_x=pitch_x,
        pitch_location_y=pitch_y,
        batter_side=side,
    )

    from .trajectory import generate_batted_ball_trajectory
    trajectory = generate_batted_ball_trajectory(state)
    # Preserve the Phase-2B test/diagnostic seam that can intentionally disable
    # trajectory generation. Production generation returns a trajectory, but a
    # disabled trajectory also disables all downstream shadow work.
    if trajectory is None:
        return replace(
            state,
            trajectory=None,
            wall_interaction=None,
            defensive_opportunity=None,
            defensive_resolution=None,
            ground_travel=None,
        )

    # Phase 2C production shadow uses the explicit generic engineering stadium
    # until a later game/stadium context contract selects a real fixture.
    from .stadium import GENERIC_ENGINEERING_BASELINE, resolve_wall_interaction
    wall = resolve_wall_interaction(
        trajectory=trajectory,
        spray_angle_deg=state.spray_angle,
        is_fair_shadow=state.is_fair,
        stadium=GENERIC_ENGINEERING_BASELINE,
    )

    # Phase 2E-A is deterministic metadata only and consumes no RNG. It reuses
    # the canonical first-ground trajectory and Phase-2C wall radius.
    from .ground_travel import generate_ground_travel_state
    ground_travel = generate_ground_travel_state(
        trajectory=trajectory,
        wall_interaction=wall,
        spray_angle_deg=state.spray_angle,
    )

    # Phase 2D is shadow-only. Probability is deterministic; the single catch
    # roll comes from a separate fork namespace and therefore never advances the
    # canonical gameplay parent RNG stream or the Phase-2A physical fork.
    from .physical_defense import build_defensive_opportunity, resolve_defensive_shadow
    opportunity = build_defensive_opportunity(
        trajectory=trajectory,
        wall_interaction=wall,
        defender_rating=defender_rating,
        is_fair_shadow=state.is_fair,
    )
    defense_roll = RNG(_fork_seed(parent_rng, namespace=0x503244)).random()
    resolution = resolve_defensive_shadow(opportunity, roll=defense_roll)
    return replace(
        state,
        trajectory=trajectory,
        wall_interaction=wall,
        defensive_opportunity=opportunity,
        defensive_resolution=resolution,
        ground_travel=ground_travel,
    )
