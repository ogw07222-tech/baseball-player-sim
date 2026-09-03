"""Pitch-by-pitch hitter simulation and compact game simulation."""
from __future__ import annotations

from dataclasses import dataclass
import math

from . import config
from .player import Player
from .records import BattingLine
from .rng import RNG
from .traits import has_trait

PA_RESULTS = ("strikeout", "walk", "hit_by_pitch", "out", "single", "double", "triple", "home_run")


def sigmoid(value: float) -> float:
    if value >= 60:
        return 1.0
    if value <= -60:
        return 0.0
    return 1.0 / (1.0 + math.exp(-value))


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
        return cls(rng.gauss(level, 7.5), rng.gauss(level, 8.0), rng.gauss(level, 7.0), "L" if rng.random() < 0.28 else "R")


def _trait_contact_modifier(player: Player, pitcher: PitcherProfile, pitch_type: str, zone: str, high_velocity: bool, strikes: int, pressure: bool) -> float:
    effect = config.TRAIT_EFFECT
    delta = 0.0
    if pitch_type == "fastball":
        delta += effect if has_trait(player.traits, "fastball_specialist") else 0.0
        delta -= effect if has_trait(player.traits, "fastball_weakness") else 0.0
    else:
        delta += effect if has_trait(player.traits, "breaking_ball_response") else 0.0
        delta -= effect if has_trait(player.traits, "breaking_ball_weakness") else 0.0
    if high_velocity:
        delta += effect if has_trait(player.traits, "high_velocity_strength") else 0.0
        delta -= effect if has_trait(player.traits, "high_velocity_weakness") else 0.0
    if zone == "low":
        delta += effect if has_trait(player.traits, "low_pitch_strength") else 0.0
        delta -= effect if has_trait(player.traits, "low_pitch_weakness") else 0.0
    if zone == "inside":
        delta += effect if has_trait(player.traits, "inside_pitch_strength") else 0.0
        delta -= effect if has_trait(player.traits, "inside_pitch_weakness") else 0.0
    if pitcher.handedness == "L":
        delta += effect if has_trait(player.traits, "vs_lhp_strength") else 0.0
        delta -= effect if has_trait(player.traits, "vs_lhp_weakness") else 0.0
    else:
        delta += effect if has_trait(player.traits, "vs_rhp_strength") else 0.0
        delta -= effect if has_trait(player.traits, "vs_rhp_weakness") else 0.0
    if strikes == 2 and has_trait(player.traits, "two_strike_strength"):
        delta += effect * 0.75
    if pressure:
        delta += effect if has_trait(player.traits, "clutch") else 0.0
        delta -= effect if has_trait(player.traits, "pressure_weakness") else 0.0
    return delta


def _condition_modifiers(player: Player) -> tuple[float, float]:
    contact = 0.0
    power = 0.0
    if player.form == "slump":
        contact -= config.FORM_CONTACT_DELTA
        power -= config.FORM_POWER_DELTA
    elif player.form == "hot":
        contact += config.FORM_CONTACT_DELTA * 0.75
        power += config.FORM_POWER_DELTA * 0.75
    fatigue_penalty = max(0.0, player.fatigue - 55.0) / 7.0
    return contact - fatigue_penalty, power - fatigue_penalty * 0.8


def _ball_in_play_result(player: Player, pitcher: PitcherProfile, contact_eff: float, power_eff: float, rng: RNG) -> str:
    if rng.random() >= logistic_range(contact_eff - pitcher.movement, 0.20, 0.46, 28.0):
        return "out"
    if rng.random() < logistic_range(power_eff - pitcher.movement, 0.030, 0.210, 27.0):
        return "home_run"
    extra_base = logistic_range(power_eff - pitcher.movement, 0.12, 0.34, 34.0)
    roll = rng.random()
    triple_share = logistic_range(player.stats.speed - 100.0, 0.008, 0.055, 30.0)
    if roll < triple_share:
        return "triple"
    if roll < triple_share + extra_base:
        return "double"
    return "single"


def simulate_plate_appearance(player: Player, pitcher: PitcherProfile, rng: RNG, pressure: bool = False) -> str:
    balls = 0
    strikes = 0
    condition_contact, condition_power = _condition_modifiers(player)
    for _ in range(24):
        if rng.random() < 0.0012:
            return "hit_by_pitch"
        pitch_type = "fastball" if rng.random() < 0.58 else "breaking"
        zone_roll = rng.random()
        zone = "low" if zone_roll < 0.28 else "inside" if zone_roll < 0.48 else "other"
        high_velocity = pitch_type == "fastball" and pitcher.stuff >= 104 and rng.random() < 0.55
        is_strike = rng.random() < logistic_range(pitcher.control - 100.0, 0.43, 0.64, 28.0)
        discipline = player.stats.discipline
        swing_probability = logistic_range(100.0 - discipline, 0.58, 0.78, 45.0) if is_strike else logistic_range(100.0 - discipline, 0.10, 0.38, 30.0)
        if rng.random() >= swing_probability:
            if is_strike:
                strikes += 1
                if strikes >= 3:
                    return "strikeout"
            else:
                balls += 1
                if balls >= 4:
                    return "walk"
            continue
        trait_mod = _trait_contact_modifier(player, pitcher, pitch_type, zone, high_velocity, strikes, pressure)
        contact_eff = player.stats.contact + condition_contact + trait_mod
        power_eff = player.stats.power + condition_power + trait_mod * 0.25
        if rng.random() >= logistic_range(contact_eff - pitcher.stuff, 0.55, 0.95, 30.0):
            strikes += 1
            if strikes >= 3:
                return "strikeout"
            continue
        foul_probability = 0.34 if strikes < 2 else 0.49
        if rng.random() < foul_probability:
            if strikes < 2:
                strikes += 1
            continue
        return _ball_in_play_result(player, pitcher, contact_eff, power_eff, rng)
    return "out"


def _run_rbi_values(result: str, rng: RNG) -> tuple[int, int]:
    if result == "home_run":
        rbi = 1 + (1 if rng.random() < 0.32 else 0) + (1 if rng.random() < 0.14 else 0)
        return 1, rbi
    if result in {"double", "triple"}:
        return (1 if rng.random() < 0.28 else 0, 1 if rng.random() < 0.48 else 0)
    if result == "single":
        return (1 if rng.random() < 0.20 else 0, 1 if rng.random() < 0.30 else 0)
    if result in {"walk", "hit_by_pitch"}:
        return (1 if rng.random() < 0.10 else 0, 0)
    return 0, 0


def _maybe_steal(player: Player, line: BattingLine, reached_base: bool, rng: RNG) -> None:
    if not reached_base:
        return
    attempt = logistic_range(player.stats.speed - 100.0, 0.015, 0.16, 30.0)
    if has_trait(player.traits, "steal_sense"):
        attempt *= 1.30
    if rng.random() >= attempt:
        return
    success = logistic_range(player.stats.speed - 100.0, 0.56, 0.88, 28.0)
    if has_trait(player.traits, "steal_sense"):
        success = min(0.94, success + 0.06)
    if rng.random() < success:
        line.SB += 1
    else:
        line.CS += 1


def simulate_player_game(player: Player, opponent_level: float, rng: RNG, line: BattingLine, pa_count: int | None = None) -> None:
    pitcher = PitcherProfile.from_level(opponent_level, rng)
    line.G += 1
    appearances = pa_count if pa_count is not None else rng.weighted_choice(((3, 0.12), (4, 0.58), (5, 0.25), (6, 0.05)))
    for index in range(appearances):
        result = simulate_plate_appearance(player, pitcher, rng, pressure=index >= 3 and rng.random() < 0.28)
        runs, rbi = _run_rbi_values(result, rng)
        line.record_pa(result, runs=runs, rbi=rbi)
        _maybe_steal(player, line, result in {"single", "walk", "hit_by_pitch"}, rng)
