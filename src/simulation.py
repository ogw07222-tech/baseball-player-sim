"""Production H3.2.1 gameplay integration.

Public simulation APIs are preserved. Neutral hitting math comes from validated
H3.1; H3.2.1 steal/advancement/DP formulas are used by the game adapter.
"""
from __future__ import annotations
from dataclasses import dataclass
import math
from . import config
from .hitting import parameters as hitting_parameters
from .hitting.baserunning import (
    GameState,
    resolve_double_play,
    resolve_first_to_third,
    resolve_second_to_home,
    resolve_steal,
)
from .hitting.model import (
    HitterSnapshot,
    HittingEngine,
    Pitch,
    PitcherSnapshot,
    PlateAppearanceOutcome,
)
from .player import Player
from .records import BattingLine
from .rng import RNG
from .traits import has_trait

PA_RESULTS = (
    "strikeout", "walk", "hit_by_pitch", "out", "fielders_choice",
    "reached_on_error", "single", "double", "triple", "home_run",
)

def sigmoid(v: float) -> float:
    if v >= 60: return 1.0
    if v <= -60: return 0.0
    return 1.0 / (1.0 + math.exp(-v))

def logistic_range(diff: float, low: float, high: float, scale: float) -> float:
    return low + (high - low) * sigmoid(diff / scale)

@dataclass(frozen=True)
class PitcherProfile:
    stuff: float
    control: float
    movement: float
    handedness: str

    @classmethod
    def from_level(cls, level: float, rng: RNG) -> "PitcherProfile":
        return cls(
            rng.gauss(level, 7.5),
            rng.gauss(level, 8.0),
            rng.gauss(level, 7.0),
            "L" if rng.random() < .28 else "R",
        )

def _trait_contact_modifier(
    p: Player,
    pitcher: PitcherProfile,
    pitch_type: str,
    zone: str,
    high_velocity: bool,
    strikes: int,
    pressure: bool,
) -> float:
    effect = config.TRAIT_EFFECT
    delta = 0.0
    if pitch_type == "fastball":
        delta += effect if has_trait(p.traits, "fastball_specialist") else 0.0
        delta -= effect if has_trait(p.traits, "fastball_weakness") else 0.0
    else:
        delta += effect if has_trait(p.traits, "breaking_ball_response") else 0.0
        delta -= effect if has_trait(p.traits, "breaking_ball_weakness") else 0.0
    if high_velocity:
        delta += effect if has_trait(p.traits, "high_velocity_strength") else 0.0
        delta -= effect if has_trait(p.traits, "high_velocity_weakness") else 0.0
    if zone == "low":
        delta += effect if has_trait(p.traits, "low_pitch_strength") else 0.0
        delta -= effect if has_trait(p.traits, "low_pitch_weakness") else 0.0
    if zone == "inside":
        delta += effect if has_trait(p.traits, "inside_pitch_strength") else 0.0
        delta -= effect if has_trait(p.traits, "inside_pitch_weakness") else 0.0
    if pitcher.handedness == "L":
        delta += effect if has_trait(p.traits, "vs_lhp_strength") else 0.0
        delta -= effect if has_trait(p.traits, "vs_lhp_weakness") else 0.0
    else:
        delta += effect if has_trait(p.traits, "vs_rhp_strength") else 0.0
        delta -= effect if has_trait(p.traits, "vs_rhp_weakness") else 0.0
    if strikes == 2 and has_trait(p.traits, "two_strike_strength"):
        delta += effect * .75
    if pressure:
        delta += effect if has_trait(p.traits, "clutch") else 0.0
        delta -= effect if has_trait(p.traits, "pressure_weakness") else 0.0
    return delta

def _condition_modifiers(p: Player) -> tuple[float, float]:
    contact = power = 0.0
    if p.form == "slump":
        contact -= config.FORM_CONTACT_DELTA
        power -= config.FORM_POWER_DELTA
    elif p.form == "hot":
        contact += config.FORM_CONTACT_DELTA * .75
        power += config.FORM_POWER_DELTA * .75
    fatigue = max(0.0, p.fatigue - 55.0) / 7.0
    return contact - fatigue, power - fatigue * .8

def _hitter_snapshot(p: Player) -> HitterSnapshot:
    bats = (p.bats_throws or "R/R").split("/", 1)[0]
    handedness = "L" if bats == "L" else "R"
    return HitterSnapshot(
        contact=p.effective_stat("contact"),
        power=p.effective_stat("power"),
        discipline=p.effective_stat("discipline"),
        speed=p.effective_stat("speed"),
        handedness=handedness,
        approach="balanced",
    )

def _pitcher_snapshot(pitcher: PitcherProfile) -> PitcherSnapshot:
    return PitcherSnapshot(
        stuff=pitcher.stuff,
        control=pitcher.control,
        movement=pitcher.movement,
        handedness=pitcher.handedness,
    )

def simulate_plate_appearance_outcome(
    p: Player,
    pitcher: PitcherProfile,
    rng: RNG,
    pressure: bool = False,
    defense_level: float = 100.0,
) -> PlateAppearanceOutcome:
    condition_contact, condition_power = _condition_modifiers(p)

    def modifier(pitch: Pitch, strikes: int) -> tuple[float, float]:
        trait = _trait_contact_modifier(
            p,
            pitcher,
            pitch.pitch_type,
            pitch.zone,
            pitch.velocity_quality > .35,
            strikes,
            pressure,
        )
        return condition_contact + trait, condition_power + trait * .25

    engine = HittingEngine(
        _hitter_snapshot(p),
        _pitcher_snapshot(pitcher),
        defense_level,
        rng,
        modifier,
    )
    return engine.simulate_plate_appearance()

def simulate_plate_appearance(
    p: Player,
    pitcher: PitcherProfile,
    rng: RNG,
    pressure: bool = False,
) -> str:
    """Backward-compatible public PA API."""
    return simulate_plate_appearance_outcome(p, pitcher, rng, pressure).result

def _run_rbi_values(result: str, rng: RNG) -> tuple[int, int]:
    if result == "home_run":
        rbi = 1 + (1 if rng.random() < .32 else 0) + (1 if rng.random() < .14 else 0)
        return 1, rbi
    if result in {"double", "triple"}:
        return (1 if rng.random() < .28 else 0, 1 if rng.random() < .48 else 0)
    if result == "single":
        return (1 if rng.random() < .20 else 0, 1 if rng.random() < .30 else 0)
    if result in {"walk", "hit_by_pitch"}:
        return (1 if rng.random() < .10 else 0, 0)
    return 0, 0

def _abstract_game_state(
    rng: RNG, appearance_index: int, appearances: int
) -> GameState:
    """Compatibility adapter until the project has a full-team inning engine.

    Callers with a real base/inning state can pass ``game_state`` directly to
    ``simulate_player_game``. Existing career callers omit it and use this
    deterministic abstract state.
    """
    progress = appearance_index / max(1, appearances - 1)
    inning = max(1, min(9, 1 + int(progress * 8)))
    outs = rng.randint(0, 2)
    score_diff = int(round(max(-6, min(6, rng.gauss(0, 2.25)))))
    first = rng.random() < .20
    second = rng.random() < .12
    third = rng.random() < .07
    return GameState(inning, outs, score_diff, first, second, third)

def _apply_pre_pa_double_play(
    p: Player, outcome: PlateAppearanceOutcome, state: GameState,
    line: BattingLine, rng: RNG
) -> PlateAppearanceOutcome:
    ball = outcome.batted_ball
    if (
        outcome.result != "out"
        or ball is None
        or ball.ball_type != "ground_ball"
        or not state.first_occupied
        or state.outs >= 2
    ):
        return outcome
    if resolve_double_play(p.effective_stat("speed"), rng):
        line.GDP += 1
        state.outs = min(3, state.outs + 2)
        state.first_occupied = False
        return outcome
    line.DP_avoided += 1
    state.outs = min(3, state.outs + 1)
    state.first_occupied = True
    return PlateAppearanceOutcome(
        "fielders_choice",
        batted_ball=ball,
        raw_candidate=outcome.raw_candidate,
        resolved_candidate=outcome.resolved_candidate,
    )

def _apply_post_reach_baserunning(
    p: Player,
    result: str,
    state: GameState,
    line: BattingLine,
    rng: RNG,
    recovery: float,
) -> None:
    speed = p.effective_stat("speed")
    if result in {"single", "walk", "hit_by_pitch", "reached_on_error", "fielders_choice"}:
        state.first_occupied = True
    elif result == "double":
        state.second_occupied = True
    elif result == "triple":
        state.third_occupied = True
    else:
        return

    if state.steal_eligible():
        steal = resolve_steal(speed, state, rng, recovery)
        if steal.attempted:
            line.SB_attempts += 1
            if steal.success:
                line.SB += 1
                state.first_occupied = False
                state.second_occupied = True
            else:
                line.CS += 1
                state.first_occupied = False
                state.outs = min(3, state.outs + 1)

    if state.first_occupied and rng.random() < hitting_parameters.FIRST_TO_THIRD_OPP_RATE:
        line.XBT_attempts += 1
        if resolve_first_to_third(speed, recovery, rng):
            line.XBT += 1
            line.first_to_third += 1
            state.first_occupied = False
            state.third_occupied = True
    if state.second_occupied and rng.random() < hitting_parameters.SECOND_TO_HOME_OPP_RATE:
        line.XBT_attempts += 1
        if resolve_second_to_home(speed, recovery, rng):
            line.XBT += 1
            line.second_to_home += 1
            line.R += 1
            state.second_occupied = False

def simulate_player_game(
    p: Player,
    opponent_level: float,
    rng: RNG,
    line: BattingLine,
    pa_count: int | None = None,
    game_state: GameState | None = None,
) -> None:
    pitcher = PitcherProfile.from_level(opponent_level, rng)
    line.G += 1
    appearances = (
        pa_count if pa_count is not None
        else rng.weighted_choice(((3, .12), (4, .58), (5, .25), (6, .05)))
    )
    for index in range(appearances):
        state = game_state if game_state is not None else _abstract_game_state(
            rng, index, appearances
        )
        outcome = simulate_plate_appearance_outcome(
            p,
            pitcher,
            rng,
            pressure=index >= 3 and rng.random() < .28,
            defense_level=opponent_level,
        )
        outcome = _apply_pre_pa_double_play(p, outcome, state, line, rng)
        runs, rbi = _run_rbi_values(outcome.result, rng)
        line.record_pa(outcome.result, runs=runs, rbi=rbi)
        _apply_post_reach_baserunning(
            p, outcome.result, state, line, rng, opponent_level
        )
