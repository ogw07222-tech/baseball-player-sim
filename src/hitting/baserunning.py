"""Validated H3.2.1 production baserunning formulas and game-state adapters.

Probability functions are frozen from Balance-Lab commit
b7b8aafde0a50e687310dbe03b872087a569e08c. The state-mutating helpers below
only connect those probabilities to a real inning/base state; they do not
retune the validated curves.
"""
from __future__ import annotations
from dataclasses import dataclass
import math
from . import parameters as P

def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))

def sigmoid(value: float) -> float:
    if value >= 60: return 1.0
    if value <= -60: return 0.0
    return 1.0 / (1.0 + math.exp(-value))

@dataclass
class GameState:
    inning: int = 1
    outs: int = 0
    score_diff: int = 0
    first_occupied: bool = False
    second_occupied: bool = False
    third_occupied: bool = False

    def steal_eligible(self) -> bool:
        return self.outs < 3 and self.first_occupied and not self.second_occupied

@dataclass(frozen=True)
class StealResult:
    attempted: bool
    success: bool

@dataclass(frozen=True)
class StateTransition:
    attempted: bool
    success: bool
    outs_added: int = 0
    runs_scored: int = 0

def situational_attempt_modifier(state: GameState) -> float:
    modifier = 0.0
    if abs(state.score_diff) <= 1:
        modifier += P.STEAL_CONTEXT_CLOSE_BONUS
        if state.inning >= 7:
            modifier += P.STEAL_CONTEXT_LATE_CLOSE_BONUS
    if state.outs == 2:
        modifier += P.STEAL_CONTEXT_TWO_OUT_BONUS
    if state.score_diff >= 4:
        modifier += P.STEAL_CONTEXT_BIG_LEAD_PENALTY
    elif state.score_diff <= -4:
        modifier += P.STEAL_CONTEXT_BIG_DEFICIT_PENALTY
    return modifier

def steal_attempt_probability(speed: float, state: GameState) -> float:
    if not state.steal_eligible():
        return 0.0
    gate = sigmoid((speed - P.STEAL_GATE_CENTER) / P.STEAL_GATE_SCALE)
    core = P.STEAL_ATTEMPT_MAX * sigmoid(
        (speed - P.STEAL_ATTEMPT_CENTER) / P.STEAL_ATTEMPT_SCALE
    )
    context = clamp(
        situational_attempt_modifier(state) * P.STEAL_CONTEXT_PROBABILITY_SCALE,
        -P.STEAL_CONTEXT_LIMIT, P.STEAL_CONTEXT_LIMIT,
    )
    return clamp(
        P.STEAL_ATTEMPT_FLOOR + gate * (core + context),
        0.0001, P.STEAL_ATTEMPT_MAX,
    )

def steal_success_probability(
    speed: float, state: GameState, running_defense: float = 100.0
) -> float:
    base = P.STEAL_SUCCESS_MIN + (P.STEAL_SUCCESS_MAX - P.STEAL_SUCCESS_MIN) * sigmoid(
        (speed - P.STEAL_SUCCESS_CENTER) / P.STEAL_SUCCESS_SCALE
    )
    adjustment = -(running_defense - 100.0) * P.STEAL_RUNNING_DEFENSE_WEIGHT
    if abs(state.score_diff) <= 1 and state.inning >= 7:
        adjustment += P.STEAL_SUCCESS_CLOSE_PENALTY
    if state.outs == 2:
        adjustment += P.STEAL_SUCCESS_TWO_OUT_BONUS
    return clamp(
        base + adjustment, P.STEAL_SUCCESS_FLOOR, P.STEAL_SUCCESS_CEILING
    )

def first_to_third_probability(speed: float, recovery: float = 100.0) -> float:
    probability = P.FIRST_TO_THIRD_MIN + (
        P.FIRST_TO_THIRD_MAX - P.FIRST_TO_THIRD_MIN
    ) * sigmoid((speed - P.FIRST_TO_THIRD_CENTER) / P.FIRST_TO_THIRD_SCALE)
    return clamp(probability - (recovery - 100.0) * P.RECOVERY_WEIGHT, .12, .78)

def second_to_home_probability(speed: float, recovery: float = 100.0) -> float:
    probability = P.SECOND_TO_HOME_MIN + (
        P.SECOND_TO_HOME_MAX - P.SECOND_TO_HOME_MIN
    ) * sigmoid((speed - P.SECOND_TO_HOME_CENTER) / P.SECOND_TO_HOME_SCALE)
    return clamp(probability - (recovery - 100.0) * P.RECOVERY_WEIGHT, .16, .84)

def dp_completion_probability(speed: float) -> float:
    return P.DP_COMPLETION_MIN + (
        P.DP_COMPLETION_MAX - P.DP_COMPLETION_MIN
    ) * (1.0 - sigmoid((speed - P.DP_COMPLETION_CENTER) / P.DP_COMPLETION_SCALE))

def resolve_steal(
    speed: float, state: GameState, rng, running_defense: float = 100.0
) -> StealResult:
    attempt = steal_attempt_probability(speed, state)
    if attempt <= 0.0 or rng.random() >= attempt:
        return StealResult(False, False)
    success = rng.random() < steal_success_probability(speed, state, running_defense)
    return StealResult(True, success)

def resolve_first_to_third(speed: float, recovery: float, rng) -> bool:
    return rng.random() < first_to_third_probability(speed, recovery)

def resolve_second_to_home(speed: float, recovery: float, rng) -> bool:
    return rng.random() < second_to_home_probability(speed, recovery)

def resolve_double_play(speed: float, rng) -> bool:
    """True means the defense completes the double play."""
    return rng.random() < dp_completion_probability(speed)

# ---- Production state adapters -------------------------------------------------
# These helpers are intentionally thin. They mutate only base/out state and use
# the frozen probability functions above.

def apply_steal_to_state(
    speed: float,
    state: GameState,
    rng,
    running_defense: float = 100.0,
) -> StateTransition:
    result = resolve_steal(speed, state, rng, running_defense)
    if not result.attempted:
        return StateTransition(False, False)
    if result.success:
        state.first_occupied = False
        state.second_occupied = True
        return StateTransition(True, True)
    state.first_occupied = False
    state.outs = min(3, state.outs + 1)
    return StateTransition(True, False, outs_added=1)

def apply_first_to_third_to_state(
    speed: float,
    state: GameState,
    rng,
    recovery: float = 100.0,
) -> StateTransition:
    if state.outs >= 3 or not state.first_occupied or state.third_occupied:
        return StateTransition(False, False)
    success = resolve_first_to_third(speed, recovery, rng)
    if success:
        state.first_occupied = False
        state.third_occupied = True
    return StateTransition(True, success)

def apply_second_to_home_to_state(
    speed: float,
    state: GameState,
    rng,
    recovery: float = 100.0,
) -> StateTransition:
    if state.outs >= 3 or not state.second_occupied:
        return StateTransition(False, False)
    success = resolve_second_to_home(speed, recovery, rng)
    if success:
        state.second_occupied = False
        return StateTransition(True, True, runs_scored=1)
    return StateTransition(True, False)

def apply_double_play_to_state(
    batter_speed: float,
    state: GameState,
    rng,
) -> StateTransition:
    if state.outs >= 2 or not state.first_occupied:
        return StateTransition(False, False)
    completed = resolve_double_play(batter_speed, rng)
    if completed:
        state.first_occupied = False
        state.outs = min(3, state.outs + 2)
        return StateTransition(True, True, outs_added=2)
    # DP avoided: one out is recorded and the batter-runner occupies first after
    # the lead runner is retired. Detailed runner identity belongs to the future
    # team inning engine, not this probability layer.
    state.first_occupied = True
    state.outs = min(3, state.outs + 1)
    return StateTransition(True, False, outs_added=1)
