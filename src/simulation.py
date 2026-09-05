"""Production H3.2.1 gameplay integration.

Public simulation APIs are preserved. Neutral hitting math comes from validated
H3.1. H3.2.1 baserunning formulas live in ``src.hitting.baserunning``.

The current career engine is player-centric rather than a full-team inning
simulator. Legacy callers therefore use an isolated compatibility steal context;
advancement and double-play formulas are exposed for a future real base-state
engine and are not faked inside the player-only loop.
"""
from __future__ import annotations
from dataclasses import dataclass
import hashlib
import math
from . import config
from .hitting import parameters as hitting_parameters
from .hitting.baserunning import GameState, resolve_steal
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
    if result in {"walk", "hit_by_pitch", "reached_on_error"}:
        return (1 if rng.random() < .10 else 0, 0)
    return 0, 0

def _fork_rng(rng: RNG, namespace: str) -> RNG:
    """Create a deterministic child stream without consuming career RNG state."""
    payload = (namespace + "|" + repr(rng.get_state())).encode("utf-8")
    seed = int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")
    return RNG(seed)

def _compat_steal_state(rng: RNG) -> GameState:
    """Mirror the validated H3.2 context sampler for legacy career callers."""
    inning = rng.randint(1, 9)
    x = rng.random()
    outs = 0 if x < .34 else 1 if x < .69 else 2
    score_diff = int(round(max(-6, min(6, rng.gauss(0, 2.25)))))
    return GameState(
        inning=inning,
        outs=outs,
        score_diff=score_diff,
        first_occupied=True,
        second_occupied=rng.random() < hitting_parameters.STEAL_SECOND_BASE_OCCUPIED_RATE,
        third_occupied=False,
    )

def _maybe_compat_steal(
    p: Player,
    line: BattingLine,
    result: str,
    parent_rng: RNG,
    appearance_index: int,
    appearances: int,
    running_defense: float = 100.0,
) -> None:
    """Legacy adapter: apply only validated SB/CS without inventing teammate state."""
    if result not in {"single", "walk", "hit_by_pitch", "reached_on_error"}:
        return
    run_rng = _fork_rng(parent_rng, f"h321-steal:{appearance_index}:{appearances}")
    state = _compat_steal_state(run_rng)
    steal = resolve_steal(p.effective_stat("speed"), state, run_rng, running_defense)
    if not steal.attempted:
        return
    line.SB_attempts += 1
    if steal.success:
        line.SB += 1
    else:
        line.CS += 1

def simulate_player_game(
    p: Player,
    opponent_level: float,
    rng: RNG,
    line: BattingLine,
    pa_count: int | None = None,
    game_state: GameState | None = None,
) -> None:
    """Simulate the player's game while preserving the established public API.

    ``game_state`` is reserved for the future full-team inning integration. The
    current career engine has no runner identities between teammate PAs, so it
    cannot safely apply H3.2.1 advancement/DP events here without inventing
    state. Callers with a real inning engine should use ``src.hitting.baserunning``
    directly with the actual runner's Speed.
    """
    del game_state
    pitcher = PitcherProfile.from_level(opponent_level, rng)
    line.G += 1
    appearances = (
        pa_count if pa_count is not None
        else rng.weighted_choice(((3, .12), (4, .58), (5, .25), (6, .05)))
    )
    for index in range(appearances):
        outcome = simulate_plate_appearance_outcome(
            p,
            pitcher,
            rng,
            pressure=index >= 3 and rng.random() < .28,
            defense_level=opponent_level,
        )
        runs, rbi = _run_rbi_values(outcome.result, rng)
        line.record_pa(outcome.result, runs=runs, rbi=rbi)
        _maybe_compat_steal(
            p,
            line,
            outcome.result,
            rng,
            index,
            appearances,
            100.0,
        )
