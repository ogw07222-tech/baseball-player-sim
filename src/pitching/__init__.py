"""Pitcher foundation API."""
from .model import (
    CatcherExtension, HitterMatchupProfile, Pitcher, PitcherStats, PitchingLine,
    generate_pitcher, generate_pitcher_stats, outcome_probabilities,
    simulate_batter_faced, simulate_outing,
)
from .fatigue import effective_stats, outing_pitch_cap, recovery_days
from .growth import apply_pitcher_season_growth, growth_distribution
from .performance import score_pitcher_performance
from .roles import PITCHER_ROLES, role_modifiers

__all__=(
    "CatcherExtension","HitterMatchupProfile","Pitcher","PitcherStats","PitchingLine",
    "generate_pitcher","generate_pitcher_stats","outcome_probabilities","simulate_batter_faced","simulate_outing",
    "effective_stats","outing_pitch_cap","recovery_days","apply_pitcher_season_growth","growth_distribution",
    "score_pitcher_performance","PITCHER_ROLES","role_modifiers",
)
