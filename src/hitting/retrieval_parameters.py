"""Phase 2E-B retrieval / physical hit-type engineering parameters.

All values in this module are V1 engineering baselines. They are not claimed to
be KBO-measured averages. Runtime uses fixed O(1) algebra only and consumes no
RNG.
"""
from __future__ import annotations

import math

RETRIEVAL_MODEL_VERSION = "phase2e_b_v1"

# Canonical 90-ft diamond in the project's CF=+Y, RF=+X coordinate system.
BASE_LEG_FT = 90.0
BASE_AXIS_FT = BASE_LEG_FT / math.sqrt(2.0)
HOME_X_FT = 0.0
HOME_Y_FT = 0.0
FIRST_BASE_X_FT = BASE_AXIS_FT
FIRST_BASE_Y_FT = BASE_AXIS_FT
SECOND_BASE_X_FT = 0.0
SECOND_BASE_Y_FT = BASE_AXIS_FT * 2.0
THIRD_BASE_X_FT = -BASE_AXIS_FT
THIRD_BASE_Y_FT = BASE_AXIS_FT

# Fixed ownership thresholds. Adjacent roles are metadata only in V1.
HOME_REGION_MAX_RADIUS_FT = 35.0
MOUND_REGION_MAX_RADIUS_FT = 90.0
INFIELD_MAX_RADIUS_FT = 185.0
MOUND_CENTER_HALF_ANGLE_DEG = 20.0
INFIELD_LINE_SECTOR_DEG = 28.0
OUTFIELD_CENTER_SECTOR_DEG = 15.0

# Derived engineering nominal anchors. OF anchors follow the research pack's
# 290 ft @ +/-27 deg and 315 ft CF recommendations. IF anchors are symmetric
# midpoints derived from published neutral Statcast standard-position zones.
def _polar(radius_ft: float, angle_deg: float) -> tuple[float, float]:
    angle = math.radians(angle_deg)
    return radius_ft * math.sin(angle), radius_ft * math.cos(angle)

NOMINAL_DEFENDER_ANCHORS_FT = {
    "C": (0.0, -5.0),
    "P": (0.0, 60.5),
    "3B": _polar(107.5, -32.5),
    "SS": _polar(145.0, -13.5),
    "2B": _polar(145.0, 13.5),
    "1B": _polar(107.5, 32.5),
    "LF": _polar(290.0, -27.0),
    "CF": _polar(315.0, 0.0),
    "RF": _polar(290.0, 27.0),
}

ROLE_CLASS = {
    "C": "PC",
    "P": "PC",
    "1B": "IF",
    "2B": "IF",
    "3B": "IF",
    "SS": "IF",
    "LF": "OF",
    "CF": "OF",
    "RF": "OF",
}

# Retrieval timing: reaction + distance/effective speed + pickup/transfer.
REACTION_BASELINE_S = {"PC": 0.45, "IF": 0.55, "OF": 0.65}
EFFECTIVE_FIELDER_SPEED_FPS = {"PC": 18.0, "IF": 21.0, "OF": 22.0}
PICKUP_TRANSFER_BASELINE_S = {"PC": 0.55, "IF": 0.65, "OF": 0.80}

# Bounded defense-rating effect. Rating 100 is neutral. Rating affects range/read
# only; throw speed is intentionally not driven by the same scalar in V1.
DEFENSE_RATING_REFERENCE = 100.0
DEFENSE_RATING_FULL_EFFECT_POINTS = 40.0
REACTION_RATING_MAX_FRACTION = 0.20
SPEED_RATING_MAX_FRACTION = 0.12
REACTION_MIN_S = 0.25
REACTION_MAX_S = 1.10
FIELDER_SPEED_MIN_FPS = 14.0
FIELDER_SPEED_MAX_FPS = 27.0

# Throw timing. Speeds are effective direct-throw engineering baselines, not
# Statcast maximum arm-strength values.
MPH_TO_FPS = 5280.0 / 3600.0
EFFECTIVE_THROW_SPEED_MPH = {"PC": 70.0, "IF": 72.0, "OF": 78.0}
THROW_RELEASE_DELAY_S = {"PC": 0.35, "IF": 0.45, "OF": 0.65}
RELAY_DISTANCE_THRESHOLD_FT = 220.0
RELAY_PENALTY_S = 0.65

# Runner timing. Existing production hitter speed is reused with a bounded
# multiplier; no new rating scale is introduced.
RUNNER_SPEED_REFERENCE = 100.0
RUNNER_TIME_PER_RATING_POINT = 0.005
RUNNER_TIME_MULTIPLIER_MIN = 0.82
RUNNER_TIME_MULTIPLIER_MAX = 1.18
HOME_START_DELAY_S = 0.55
FIRST_LEG_REFERENCE_S = 3.65
BASE_LEG_REFERENCE_S = 3.45
TURN_PENALTY_S = 0.18

TIME_EPSILON_S = 1e-9
MAX_VALID_TIME_S = 60.0
