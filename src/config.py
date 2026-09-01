"""Temporary balance parameters for Phase 1.

These values are implementation defaults, not finalized game-design canon.
Keep balance knobs here so later simulation tuning can change them without
rewriting domain logic.
"""

STAT_MIN = 0
STAT_NAMES = (
    "contact", "power", "discipline", "speed", "defense",
    "throwing", "stamina", "durability", "mentality", "talent",
)

# TODO(balance): Initial distributions are intentionally provisional.
INITIAL_STAT_MEAN = 75.0
INITIAL_STAT_STDDEV = 18.0
INITIAL_TALENT_MEAN = 90.0
INITIAL_TALENT_STDDEV = 30.0
INITIAL_AGE_MIN = 18
INITIAL_AGE_MAX = 22

# Random trait count. No canonical maximum has been decided yet.
# This only controls generation in the prototype.
INITIAL_TRAIT_COUNT_WEIGHTS = ((0, 0.25), (1, 0.40), (2, 0.25), (3, 0.10))

# TODO(balance): Growth model constants are provisional and isolated here.
GROWTH_BASE_STDDEV = 3.0
GROWTH_TALENT_REFERENCE = 100.0
GROWTH_TALENT_SCALE = 0.012
GROWTH_CURRENT_STAT_DAMPING = 0.0025
GROWTH_EXPLOSION_BASE_CHANCE = 0.015
GROWTH_EXPLOSION_TALENT_SCALE = 0.00008
GROWTH_EXPLOSION_MIN_BONUS = 4
GROWTH_EXPLOSION_MAX_BONUS = 15

AGE_GROWTH_BIAS = {
    (0, 22): 2.0,
    (23, 27): 1.0,
    (28, 31): 0.0,
    (32, 35): -1.5,
    (36, 200): -3.0,
}

# Aging multipliers make physical tools decline earlier while discipline and
# mentality remain comparatively stable. Values are tuning parameters only.
AGING_MULTIPLIER = {
    "contact": 1.0,
    "power": 1.0,
    "discipline": 0.45,
    "speed": 1.55,
    "defense": 1.05,
    "throwing": 0.95,
    "stamina": 1.35,
    "durability": 1.40,
    "mentality": 0.25,
}
