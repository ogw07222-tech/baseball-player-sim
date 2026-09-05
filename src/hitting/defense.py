"""H3.1 validated defense resolution for production."""
from __future__ import annotations
from . import parameters as P

def clamp(value: float, low: float=0.0, high: float=1.0) -> float:
    return max(low, min(high, value))

def difficulty_tier(score: float) -> str:
    if score < -0.78: return "ROUTINE"
    if score < -0.28: return "EASY"
    if score < 0.28: return "AVERAGE"
    if score < 0.78: return "HARD"
    if score < 1.28: return "VERY_HARD"
    return "EXCEPTIONAL"

def catch_probability(tier: str, defense: float) -> float:
    base = P.DIFFICULTY_BASE_CATCH[tier]
    adjustment = (defense - 100.0) * P.DIFFICULTY_DEFENSE_LEVERAGE[tier]
    low, high = P.DIFFICULTY_CATCH_BOUNDS[tier]
    return clamp(base + adjustment, low, high)

def suppress_candidate(candidate: str, defense: float, roll: float) -> str:
    delta = defense - 100.0
    if candidate == "3B_candidate":
        probability = clamp(P.DAMAGE_BASE_3B_TO_2B + delta * P.DAMAGE_DEFENSE_SCALE,.02,P.DAMAGE_MAX_3B_TO_2B)
        return "2B_candidate_suppressed" if roll < probability else candidate
    if candidate == "2B_candidate":
        probability = clamp(P.DAMAGE_BASE_2B_TO_1B + delta * P.DAMAGE_DEFENSE_SCALE,.02,P.DAMAGE_MAX_2B_TO_1B)
        return "1B_suppressed" if roll < probability else candidate
    return candidate
