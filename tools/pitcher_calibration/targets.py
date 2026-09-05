"""Frozen 2025 KBO full-league targets for pitcher calibration.

Source totals are the 10 KBO regular-season team batting lines. The source page
states its data source is koreabaseball.com. Targets/tolerances are fixed before
candidate search; they must not be loosened after observing results.
"""
from __future__ import annotations

KBO_TARGET_SEASON = 2025
KBO_TOTALS = {
    "PA": 55996,
    "AB": 49021,
    "H": 12824,
    "1B": 9182,
    "2B": 2243,
    "3B": 208,
    "HR": 1191,
    "BB": 5123,
    "HBP": 806,
    "SO": 11024,
    "SF": 451,
    "SAC": 594,
}

KBO_TARGETS = {
    "AVG": 0.2616021705,
    "OBP": 0.3384956950,
    "SLG": 0.3887313600,
    "OPS": 0.7272270551,
    "BB%": 0.0914886778,
    "K%": 0.1968712051,
    "HR%": 0.0212693764,
    "1B%": 0.1639759983,
    "2B%": 0.0400564326,
    "3B%": 0.0037145510,
    "BABIP": 0.3122366267,
}

TOLERANCES = {
    "AVG": 0.010,
    "OBP": 0.010,
    "SLG": 0.020,
    "BB%": 0.010,
    "K%": 0.015,
    "HR%": 0.005,
    "1B%": 0.010,
    "2B%": 0.004,
    "3B%": 0.0015,
    "BABIP": 0.012,
}

OBJECTIVE_WEIGHTS = {
    "AVG": 1.0,
    "OBP": 1.0,
    "SLG": 1.0,
    "BB%": 1.0,
    "K%": 1.0,
    "HR%": 1.0,
    "1B%": 0.75,
    "2B%": 0.75,
    "3B%": 0.50,
    "BABIP": 0.75,
}

# Search ranges are deliberately broad because the production growth population
# has a league median around the low/mid-80s while H3.2.1's mathematical neutral
# reference is 100. We keep raw ratings intact and let this isolated adapter map
# that existing scale; no hitter formula or growth distribution is recentered.
SEARCH_RANGES = {
    "w_control_zone": (0.40, 4.00),
    "w_velocity_contact": (0.03, 0.70),
    "w_breaking_contact": (0.02, 0.70),
    "w_stuff_quality": (0.03, 0.70),
    "w_breaking_quality": (0.02, 0.60),
}
