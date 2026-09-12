"""Phase 2C O(1) stadium geometry and physical-HR shadow resolution.

The geometry layer is diagnostic/shadow-only in Phase 2C. Legacy HR, defense,
XBH, runner advancement, and Phase-1 fair/foul semantics remain authoritative.
All canonical distances/heights are feet and spray angles use Phase-2A's
center-field-zero convention (LF negative, RF positive).
"""
from __future__ import annotations

from dataclasses import dataclass
import math

from .trajectory import BattedBallTrajectory

M_TO_FT = 3.280839895013123
FAIR_ANGLE_MIN_DEG = -45.0
FAIR_ANGLE_MAX_DEG = 45.0
WALL_CONTACT_TOLERANCE_FT = 0.25

QUALITY_VERIFIED = "VERIFIED"
QUALITY_APPROXIMATED = "APPROXIMATED"
QUALITY_CONFLICTING = "CONFLICTING"
_ALLOWED_QUALITIES = {QUALITY_VERIFIED, QUALITY_APPROXIMATED, QUALITY_CONFLICTING}


@dataclass(frozen=True)
class StadiumGeometry:
    """Fixed five-anchor radial outfield geometry.

    Anchors are always ordered at -45, -22.5, 0, +22.5, +45 degrees. Runtime
    lookup uses explicit fixed-sector dispatch; it never scans an anchor array.
    """

    stadium_id: str
    season: int | None
    is_real_stadium: bool
    source_quality: str
    wall_radius_ft: tuple[float, float, float, float, float]
    wall_height_ft: tuple[float, float, float, float, float]

    def __post_init__(self) -> None:
        if self.source_quality not in _ALLOWED_QUALITIES:
            raise ValueError("unsupported stadium source quality")
        values = self.wall_radius_ft + self.wall_height_ft
        if len(self.wall_radius_ft) != 5 or len(self.wall_height_ft) != 5:
            raise ValueError("Phase-2C V1 stadium geometry requires five anchors")
        if not all(math.isfinite(value) and value > 0.0 for value in values):
            raise ValueError("stadium anchors must be finite positive feet values")

    @staticmethod
    def _lerp(value0: float, value1: float, t: float) -> float:
        return value0 + (value1 - value0) * t

    def wall_at_spray(self, spray_angle_deg: float) -> tuple[float, float]:
        """Return wall radius/height with O(1) fixed-sector interpolation."""
        angle = max(FAIR_ANGLE_MIN_DEG, min(FAIR_ANGLE_MAX_DEG, spray_angle_deg))
        radii = self.wall_radius_ft
        heights = self.wall_height_ft
        if angle <= -22.5:
            t = (angle + 45.0) / 22.5
            return self._lerp(radii[0], radii[1], t), self._lerp(heights[0], heights[1], t)
        if angle <= 0.0:
            t = (angle + 22.5) / 22.5
            return self._lerp(radii[1], radii[2], t), self._lerp(heights[1], heights[2], t)
        if angle <= 22.5:
            t = angle / 22.5
            return self._lerp(radii[2], radii[3], t), self._lerp(heights[2], heights[3], t)
        t = (angle - 22.5) / 22.5
        return self._lerp(radii[3], radii[4], t), self._lerp(heights[3], heights[4], t)


@dataclass(frozen=True)
class WallInteraction:
    stadium_id: str
    wall_radius_ft: float
    wall_height_ft: float
    reaches_wall: bool
    ball_height_at_wall_ft: float
    clearance_ft: float
    clears_wall: bool
    wall_contact: bool
    physical_hr_shadow: bool

    def __post_init__(self) -> None:
        numeric = (
            self.wall_radius_ft,
            self.wall_height_ft,
            self.ball_height_at_wall_ft,
            self.clearance_ft,
        )
        if not all(math.isfinite(value) for value in numeric):
            raise ValueError("wall interaction values must be finite")
        if self.wall_radius_ft <= 0.0 or self.wall_height_ft <= 0.0:
            raise ValueError("wall geometry must be positive")


def resolve_wall_interaction(
    *,
    trajectory: BattedBallTrajectory,
    spray_angle_deg: float,
    is_fair_shadow: bool,
    stadium: StadiumGeometry,
) -> WallInteraction:
    """Resolve physical wall geometry without changing gameplay authority."""
    wall_radius, wall_height = stadium.wall_at_spray(spray_angle_deg)
    if not trajectory.valid:
        return WallInteraction(
            stadium_id=stadium.stadium_id,
            wall_radius_ft=wall_radius,
            wall_height_ft=wall_height,
            reaches_wall=False,
            ball_height_at_wall_ft=0.0,
            clearance_ft=-wall_height,
            clears_wall=False,
            wall_contact=False,
            physical_hr_shadow=False,
        )

    reaches = trajectory.horizontal_distance_ft >= wall_radius
    ball_height = trajectory.height_at_horizontal_distance(wall_radius) if reaches else 0.0
    clearance = ball_height - wall_height if reaches else -wall_height
    clears = reaches and clearance > 0.0
    contact = reaches and abs(clearance) <= WALL_CONTACT_TOLERANCE_FT
    within_fair_geometry = FAIR_ANGLE_MIN_DEG <= spray_angle_deg <= FAIR_ANGLE_MAX_DEG
    physical_hr = bool(is_fair_shadow and within_fair_geometry and clears)
    return WallInteraction(
        stadium_id=stadium.stadium_id,
        wall_radius_ft=wall_radius,
        wall_height_ft=wall_height,
        reaches_wall=reaches,
        ball_height_at_wall_ft=ball_height,
        clearance_ft=clearance,
        clears_wall=clears,
        wall_contact=contact,
        physical_hr_shadow=physical_hr,
    )


def _ft(values_m: tuple[float, float, float, float, float]) -> tuple[float, float, float, float, float]:
    return tuple(value * M_TO_FT for value in values_m)  # module-load only


# Engineering baseline only: not a measured or arithmetic KBO average.
GENERIC_ENGINEERING_BASELINE = StadiumGeometry(
    stadium_id="generic_neutral_v1",
    season=None,
    is_real_stadium=False,
    source_quality=QUALITY_APPROXIMATED,
    wall_radius_ft=_ft((100.0, 115.0, 122.0, 115.0, 100.0)),
    wall_height_ft=_ft((3.0, 3.0, 3.0, 3.0, 3.0)),
)

# Representative fixtures. Missing power-alley values are engineering
# interpolations and therefore prevent these convenience fixtures from being
# labeled fully VERIFIED even where line/CF source anchors are verified.
JAMSIL_LIKE_2026 = StadiumGeometry(
    stadium_id="jamsil_like_2026",
    season=2026,
    is_real_stadium=True,
    source_quality=QUALITY_CONFLICTING,
    wall_radius_ft=_ft((100.0, 112.5, 125.0, 112.5, 100.0)),
    wall_height_ft=_ft((2.6, 2.6, 2.6, 2.6, 2.6)),
)

GOCHEOK_LIKE_2026 = StadiumGeometry(
    stadium_id="gocheok_like_2026",
    season=2026,
    is_real_stadium=True,
    source_quality=QUALITY_APPROXIMATED,
    wall_radius_ft=_ft((99.0, 110.5, 122.0, 110.5, 99.0)),
    wall_height_ft=_ft((4.0, 4.0, 4.0, 4.0, 4.0)),
)

# The published Daejeon five-distance shape is asymmetric. The exact angular
# start/end of the 8 m Monster Wall is not source-verified in the research pack,
# so RC/RF height anchors below are explicitly APPROXIMATED for V1 validation.
DAEJEON_ASYMMETRIC_2026 = StadiumGeometry(
    stadium_id="daejeon_asymmetric_2026",
    season=2026,
    is_real_stadium=True,
    source_quality=QUALITY_APPROXIMATED,
    wall_radius_ft=_ft((99.0, 115.0, 122.0, 112.0, 95.0)),
    wall_height_ft=_ft((2.4, 2.4, 2.4, 8.0, 8.0)),
)
