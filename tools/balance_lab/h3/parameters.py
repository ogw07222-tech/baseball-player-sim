"""Central H3.1 experimental parameters.

All numbers in this module are test-side tuning constants. Nothing here is a
production contract.
"""

STAT_REFERENCE = 100.0

# Swing / plate discipline.
ZONE_SWING_BASE = 0.67
BALL_CHASE_BASE = 0.245
DISCIPLINE_ZONE_WEIGHT = 0.0015
DISCIPLINE_CHASE_WEIGHT = 0.0045
TWO_STRIKE_PROTECTION_WEIGHT = 0.0065
TWO_STRIKE_PROTECTION_CAP = 0.25

# Pitch generation.
STRIKE_RATE = 0.550
PITCH_TYPE_FASTBALL = 0.57
ZONE_WEIGHTS = {
    "inside": 0.18,
    "middle": 0.23,
    "outside": 0.20,
    "high": 0.19,
    "low": 0.20,
}
ZONE_HITTABLE = {
    "inside": 0.22,
    "middle": 0.72,
    "outside": 0.14,
    "high": -0.12,
    "low": -0.10,
}
BALL_HITTABLE_PENALTY = -0.82

# Contact and quality. Positive stat deltas use a soft saturation so the model
# retains high-stat diminishing returns without creating a low-stat dead zone.
CONTACT_SCALE = 0.0055
CONTACT_POSITIVE_SOFT = 70.0
CONTACT_HITTABLE_WEIGHT = 0.58
CONTACT_MOVEMENT_WEIGHT = 0.0058
CONTACT_NOISE_SD = 0.36
BIP_BASE = 0.725
FOUL_BASE = 0.36

QUALITY_CONTACT_WEIGHT = 0.0040
QUALITY_HITTABLE_WEIGHT = 0.62
QUALITY_MOVEMENT_WEIGHT = 0.0047
QUALITY_NOISE_SD = 0.48

# Approach / direction.
APPROACH_BASE = {
    "pull": (0.55, 0.30, 0.15),
    "balanced": (0.33, 0.34, 0.33),
    "opposite": (0.20, 0.30, 0.50),
}
LOCATION_DIRECTION_SHIFT = 0.14
APPROACH_MATCH_QUALITY_BONUS = 0.10
APPROACH_FORCE_PENALTY = 0.08

# Batted-ball shape / exit quality.
POWER_SCALE = 0.0108
POWER_POSITIVE_SOFT = 85.0
EXIT_QUALITY_WEIGHT = 0.74
EXIT_POWER_WEIGHT = 0.58
EXIT_NOISE_SD = 0.34

# Home run: defense-independent. Requires air ball + depth + strong exit.
HR_LOGIT_CENTER = 0.86
HR_LOGIT_SCALE = 0.30
HR_FLY_MULT = 1.00
HR_LINE_MULT = 0.38

# Fielding difficulty tier base catch rates. Defense then modifies these with
# tier-specific leverage and hard ceilings/floors.
DIFFICULTY_BASE_CATCH = {
    "ROUTINE": 0.991,
    "EASY": 0.958,
    "AVERAGE": 0.550,
    "HARD": 0.430,
    "VERY_HARD": 0.150,
    "EXCEPTIONAL": 0.040,
}
DIFFICULTY_DEFENSE_LEVERAGE = {
    "ROUTINE": 0.00011,
    "EASY": 0.00032,
    "AVERAGE": 0.00135,
    "HARD": 0.00400,
    "VERY_HARD": 0.00175,
    "EXCEPTIONAL": 0.00155,
}
DIFFICULTY_CATCH_BOUNDS = {
    "ROUTINE": (0.965, 0.9985),
    "EASY": (0.900, 0.994),
    "AVERAGE": (0.48, 0.80),
    "HARD": (0.20, 0.67),
    "VERY_HARD": (0.04, 0.32),
    "EXCEPTIONAL": (0.008, 0.24),
}

# Difficulty score construction. Larger means harder.
DIFFICULTY_QUALITY_WEIGHT = 0.90
DIFFICULTY_EXIT_WEIGHT = 0.78
DIFFICULTY_DISTANCE_WEIGHT = 0.42
DIFFICULTY_GROUND_BONUS = -0.22
DIFFICULTY_LINE_BONUS = 0.12
DIFFICULTY_FLY_BONUS = 0.02
DIFFICULTY_DEEP_BONUS = 0.20
DIFFICULTY_SHALLOW_BONUS = -0.10

# Damage suppression on uncaught non-HR balls.
DAMAGE_DEFENSE_SCALE = 0.0060
DAMAGE_BASE_3B_TO_2B = 0.19
DAMAGE_BASE_2B_TO_1B = 0.14
DAMAGE_MAX_3B_TO_2B = 0.63
DAMAGE_MAX_2B_TO_1B = 0.50

# Error logic. Average+ misses are hits, not errors.
ROUTINE_MISS_ERROR_RATE = 0.985
EASY_MISS_ERROR_RATE = 0.86

# Speed model.
# Slow players lose some stretch doubles; fast players gain triples. Automatic
# doubles are much less speed-sensitive.
STRETCH_DOUBLE_SHARE = 0.58
SLOW_DOUBLE_DOWNGRADE_AT_100 = 0.020
SLOW_DOUBLE_DOWNGRADE_PER_POINT = 0.0120
SLOW_DOUBLE_DOWNGRADE_MAX = 0.72
FAST_TRIPLE_BASE = 0.020
FAST_TRIPLE_MAX = 0.235
FAST_TRIPLE_SOFT = 45.0
AUTO_DOUBLE_TRIPLE_FACTOR = 0.32

# Candidate extra-base creation (before defense suppression and speed conversion).
DOUBLE_BASE = 0.112
DOUBLE_QUALITY_WEIGHT = 0.075
DOUBLE_EXIT_WEIGHT = 0.090
DOUBLE_DEEP_BONUS = 0.055
DOUBLE_LINE_BONUS = 0.035
TRIPLE_CANDIDATE_GAP_BONUS = 0.018
DEEP_THRESHOLD = 0.56
MEDIUM_THRESHOLD = -0.10

# Offensive value (validation only; wOBA-like linear weights / PA).
OFFENSIVE_WEIGHTS = {
    "BB": 0.69,
    "HBP": 0.72,
    "1B": 0.89,
    "2B": 1.27,
    "3B": 1.62,
    "HR": 2.10,
    "ROE": 0.70,
}

FAST_SINGLE_TO_DOUBLE_PER_POINT = 0.0220
FAST_SINGLE_TO_DOUBLE_MAX = 0.34

# Infield-hit race after a ground ball is fielded. Routine balls are excluded.
INFIELD_HIT_BASE = 0.030
INFIELD_HIT_LOW = 0.002
INFIELD_HIT_HIGH = 0.140
INFIELD_HIT_UP_SCALE = 42.0
INFIELD_HIT_DOWN_SCALE = 30.0
INFIELD_HIT_DEFENSE_WEIGHT = 0.35
INFIELD_HIT_EASY_FACTOR = 0.65
