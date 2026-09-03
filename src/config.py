"""Prototype balance configuration.

DESIGN.md remains the game-design source of truth. Numeric values in this file
are provisional defaults intended for simulation/balance iteration.
"""
from __future__ import annotations

STAT_MIN = 0
STAT_NAMES = (
    "contact", "power", "discipline", "speed", "defense",
    "throwing", "stamina", "durability", "mentality", "talent",
)
HITTER_STAT_NAMES = tuple(name for name in STAT_NAMES if name != "talent")
POSITIONS = ("C", "1B", "2B", "3B", "SS", "LF", "CF", "RF", "DH")
BATS_THROWS = ("R/R", "R/L", "L/R", "L/L", "S/R", "S/L")
START_AGE = 18
START_YEAR = 2026
SAVE_VERSION = 1

INITIAL_STAT_DISTRIBUTIONS: dict[str, tuple[float, float]] = {
    "contact": (58.0, 14.0), "power": (52.0, 16.0), "discipline": (50.0, 14.0),
    "speed": (68.0, 18.0), "defense": (60.0, 15.0), "throwing": (62.0, 16.0),
    "stamina": (72.0, 14.0), "durability": (75.0, 16.0), "mentality": (52.0, 18.0),
}
POSITION_ADJUSTMENTS: dict[str, dict[str, int]] = {
    "SS": {"speed": 8, "defense": 10, "throwing": 8, "power": -5},
    "CF": {"speed": 10, "defense": 8, "throwing": 3},
    "1B": {"power": 10, "speed": -12, "defense": -4},
    "C": {"throwing": 10, "durability": 8, "speed": -12},
    "3B": {"power": 6, "throwing": 7},
    "2B": {"contact": 4, "defense": 7, "speed": 5},
    "LF": {"power": 6, "throwing": 5}, "RF": {"power": 6, "throwing": 5},
    "DH": {"contact": 5, "power": 10, "defense": -15, "speed": -8},
}
TALENT_MIXTURE = (
    (0.85, 85.0, 17.0, 35), (0.12, 125.0, 15.0, 90),
    (0.025, 160.0, 17.0, 120), (0.005, 205.0, 30.0, 150),
)
TRAIT_POSITIVE_SHARE = 0.50
TRAIT_DEFAULT_WEIGHT = 1.0
TRAIT_WEIGHTS: dict[str, float] = {"fast_growth": 0.65, "slow_growth": 0.65, "injury_risk": 0.70, "clutch": 0.75}
TRAIT_EFFECT = 8.0

GROWTH_BASE_STDDEV = 3.3
GROWTH_TALENT_REFERENCE = 100.0
GROWTH_TALENT_SCALE = 0.020
GROWTH_CURRENT_STAT_DAMPING = 0.0025
GROWTH_EXPLOSION_BASE_CHANCE = 0.012
GROWTH_EXPLOSION_TALENT_SCALE = 0.00007
GROWTH_EXPLOSION_MIN_BONUS = 4
GROWTH_EXPLOSION_MAX_BONUS = 14
AGE_GROWTH_BIAS = {(0, 22): 4.6, (23, 27): 2.7, (28, 31): 0.1, (32, 35): -1.35, (36, 200): -2.8}
AGING_MULTIPLIER = {
    "contact": 0.80, "power": 0.95, "discipline": 0.35, "speed": 1.55,
    "defense": 1.05, "throwing": 0.90, "stamina": 1.30, "durability": 1.40, "mentality": 0.20,
}

HIGH_SCHOOL_TOURNAMENTS = ("청룡기", "황금사자기", "대통령배", "봉황대기")
HIGH_SCHOOL_PITCHER_LEVEL = (55, 75)
KBO_FIRST_TEAM_GAMES = 144
KBO_FARM_GAMES = 120
KBO_TEAMS = (
    {"name": "KIA 타이거즈", "first_team_level": 101, "farm_level": 83, "depth": 100},
    {"name": "삼성 라이온즈", "first_team_level": 100, "farm_level": 82, "depth": 99},
    {"name": "LG 트윈스", "first_team_level": 103, "farm_level": 84, "depth": 104},
    {"name": "두산 베어스", "first_team_level": 100, "farm_level": 83, "depth": 101},
    {"name": "KT 위즈", "first_team_level": 100, "farm_level": 82, "depth": 99},
    {"name": "SSG 랜더스", "first_team_level": 101, "farm_level": 82, "depth": 100},
    {"name": "롯데 자이언츠", "first_team_level": 99, "farm_level": 81, "depth": 98},
    {"name": "한화 이글스", "first_team_level": 101, "farm_level": 84, "depth": 103},
    {"name": "NC 다이노스", "first_team_level": 99, "farm_level": 82, "depth": 98},
    {"name": "키움 히어로즈", "first_team_level": 96, "farm_level": 80, "depth": 91},
)
POSITION_COMPETITION = {"C": 4, "1B": 1, "2B": 3, "3B": 2, "SS": 5, "LF": 0, "CF": 4, "RF": 1, "DH": -2}
SLUMP_BASE_CHANCE_PER_GAME = 0.0040
HOT_STREAK_BASE_CHANCE_PER_GAME = 0.0045
FORM_MIN_GAMES = 4
FORM_MAX_GAMES = 18
FORM_CONTACT_DELTA = 7
FORM_POWER_DELTA = 5
INJURY_BASE_CHANCE_PER_GAME = 0.0016
FATIGUE_PER_GAME_BASE = 7.0
FATIGUE_REST_RECOVERY = 12.0
DRAFT_WEIGHTS = {"current_ability": 0.34, "scouted_talent": 0.28, "performance": 0.25, "position": 0.08, "health": 0.05}
POSITION_DRAFT_VALUE = {"C": 9, "SS": 10, "CF": 7, "2B": 5, "3B": 4, "RF": 2, "LF": 1, "1B": 0, "DH": -4}
RETIREMENT_HARD_AGE = 45
