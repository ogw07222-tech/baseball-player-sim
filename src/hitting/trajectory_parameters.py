"""Phase 2B lightweight trajectory-surrogate parameters.

These constants define an O(1) generic neutral-atmosphere V1 trajectory model.
They are intentionally isolated from Phase-2A EV/LA/spray generation and from
legacy HR/XBH/defense result resolution.
"""

# Canonical units: feet, seconds, mph at the Phase-2A boundary.
MPH_TO_FPS = 1.4666666666666666
GRAVITY_FTPS2 = 32.17405
LAUNCH_HEIGHT_FT = 3.0

# Negative / near-zero launch-angle first-ground approximation.
# Short flights use exact vacuum vertical intersection plus a small fixed
# horizontal attenuation. No bounce, roll, friction, or pickup is modeled.
GROUND_HORIZONTAL_ATTENUATION = 0.97

# Blend short first-impact kinematics into the aerodynamic air-ball surrogate.
AIR_BLEND_FULL_DEG = 8.0

# Pre-fit algebraic carry surface. The 100 mph / 29 deg anchor is the research
# sanity point (~397 ft aerodynamic versus ~571 ft vacuum), not an HR target.
AIR_CARRY_PEAK_LA_DEG = 29.0
AIR_CARRY_AT_100_PEAK_FT = 397.0
AIR_CARRY_CURVATURE_FT_PER_DEG2 = 0.18
AIR_CARRY_MIN_BASE_FT = 25.0
AIR_CARRY_SPEED_EXPONENT = 1.65
AIR_CARRY_MAX_FT = 550.0

# Ground-level flight-time surrogate at 100 mph, then weak EV scaling.
# Shape is fitted to broad baseball-flight references and deliberately peaks
# below absurd popup durations.
AIR_HANG_BASE_S = 1.20
AIR_HANG_LINEAR_S_PER_DEG = 0.175
AIR_HANG_QUADRATIC_S_PER_DEG2 = -0.00125
AIR_HANG_SPEED_EXPONENT = 0.25
AIR_HANG_MAX_S = 9.0

# Apex uses the analytical vertical-velocity baseline with a fixed aerodynamic
# reduction. It is descriptive only until later defense/wall stages.
APEX_AERO_SCALE = 0.78
APEX_MAX_FT = 260.0

# Defensive sanity bounds; these are numerical guards, not calibration targets.
DISTANCE_MIN_FT = 0.0
HANG_TIME_MIN_S = 0.0
APEX_MIN_FT = 0.0
