"""Phase 2E-A ground-travel engineering parameters.

These constants are structural V1 baselines informed by the Phase-2E research
pack. They are not claimed to be measured KBO coefficients. Runtime use is
fixed-cost O(1) and deterministic.
"""

GROUND_MODEL_VERSION = "phase2e_a_neutral_v1"
SURFACE_CLASS_NEUTRAL = "neutral"

HANG_TIME_EPSILON_S = 1e-4
WALL_RADIUS_EPSILON_FT = 1e-6

# Average-horizontal-speed -> first-impact horizontal-speed correction.
# Phase 2B stores realized first-impact distance/time, so only a small downward
# correction is applied rather than reconstructing another flight model.
IMPACT_SPEED_CORRECTION = {
    "ground_like": 0.96,
    "line_drive": 0.90,
    "fly_ball": 0.84,
    "popup": 0.72,
}

# One representative bounce only. These horizontal-retention values are
# engineering baselines and intentionally are not copied from Pennbounce total
# surface-pace/COR measurements.
POST_IMPACT_SPEED_RETENTION = {
    "ground_like": 0.58,
    "line_drive": 0.52,
    "fly_ball": 0.45,
    "popup": 0.35,
}

# Representative airborne/skipping distance after the first major impact.
# d_bounce = v_post * fixed class time proxy.
BOUNCE_TIME_PROXY_S = {
    "ground_like": 0.12,
    "line_drive": 0.18,
    "fly_ball": 0.15,
    "popup": 0.10,
}

ROLLOUT_SPEED_RETENTION = {
    "ground_like": 0.82,
    "line_drive": 0.75,
    "fly_ball": 0.55,
    "popup": 0.35,
}

# Effective neutral-surface rolling/sliding deceleration. This is a gameplay
# engineering parameter, not a universal baseball-field physical constant.
EFFECTIVE_ROLLOUT_DECELERATION_FTPS2 = 35.0

MAX_IMPACT_HORIZONTAL_SPEED_FPS = 220.0
MAX_GROUND_TRAVEL_DISTANCE_FT = 450.0
