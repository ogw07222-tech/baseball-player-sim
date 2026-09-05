"""Velocity-only diagnostic adapter over frozen production H3.2.1."""
from __future__ import annotations

from collections import Counter
import random

from src.hitting.model import HitterSnapshot, HittingEngine, PitcherSnapshot
from .model import VelocityGameplayContract

NEUTRAL_HITTER = HitterSnapshot(100.0, 100.0, 100.0, 100.0)
NEUTRAL_PITCHER = PitcherSnapshot(stuff=100.0, control=100.0, movement=100.0)


def make_engine(kmh: float, scale: float, seed: int) -> HittingEngine:
    contract = VelocityGameplayContract(gameplay_points_per_kmh=scale)
    delta = contract.contact_delta(kmh)

    def velocity_only_modifier(_pitch, _strikes):
        return delta, 0.0

    return HittingEngine(
        NEUTRAL_HITTER,
        NEUTRAL_PITCHER,
        100.0,
        random.Random(seed),
        pitch_stat_modifier=velocity_only_modifier,
    )


def pa_metrics(kmh: float, scale: float, n: int, seed: int) -> dict[str, float]:
    engine = make_engine(kmh, scale, seed)
    counts: Counter[str] = Counter()
    for _ in range(n):
        counts[engine.simulate_plate_appearance().result] += 1
    bb = counts["walk"]
    so = counts["strikeout"]
    hr = counts["home_run"]
    one = counts["single"]
    two = counts["double"]
    three = counts["triple"]
    hits = one + two + three + hr
    ab = max(1, n - bb)
    return {
        "PA": float(n),
        "AVG": hits / ab,
        "SLG": (one + 2 * two + 3 * three + 4 * hr) / ab,
        "K%": so / n,
        "BB%": bb / n,
        "HR%": hr / n,
    }


def pitch_contact_metrics(kmh: float, scale: float, n: int, seed: int) -> dict[str, float]:
    """Neutral-count swing/contact diagnostic using the frozen H3 methods."""
    engine = make_engine(kmh, scale, seed)
    swings = touches = whiffs = 0
    for _ in range(n):
        pitch = engine._pitch()
        if engine.rng.random() >= engine._swing_probability(pitch, 0, 0):
            continue
        swings += 1
        result, _, _ = engine._contact_resolution(pitch, 0)
        if result == "miss":
            whiffs += 1
        else:
            touches += 1
    return {
        "swings": float(swings),
        "Contact%": touches / max(1, swings),
        "Whiff%": whiffs / max(1, swings),
    }
