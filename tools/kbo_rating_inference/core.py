from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, Sequence

from src.hitting.normalization import normalize_hitter
from src.pitching.physical_velocity import (
    base_avg_kmh,
    gameplay_velocity,
    raw_to_uncapped_avg_kmh,
)

HITTER_TOLERANCES = {
    "AVG": 0.010,
    "OBP": 0.012,
    "SLG": 0.020,
    "BB_pct": 0.010,
    "K_pct": 0.015,
    "HR_pct": 0.005,
    "BABIP": 0.015,
    "SB_attempt_pct": 0.015,
    "SB_success": 0.080,
}

PITCHER_TOLERANCES = {
    "K_pct": 0.015,
    "BB_pct": 0.010,
    "HR_pct": 0.005,
    "OPP_AVG": 0.012,
    "OPP_SLG": 0.025,
    "BABIP": 0.018,
}

HITTER_OBJECTIVE_WEIGHTS = {
    "AVG": 1.2,
    "OBP": 1.0,
    "SLG": 1.15,
    "BB_pct": 1.0,
    "K_pct": 1.0,
    "HR_pct": 0.9,
    "BABIP": 0.55,
    "SB_attempt_pct": 0.75,
    "SB_success": 0.50,
}

PITCHER_OBJECTIVE_WEIGHTS = {
    "K_pct": 1.25,
    "BB_pct": 1.25,
    "HR_pct": 0.75,
    "OPP_AVG": 1.0,
    "OPP_SLG": 1.0,
    "BABIP": 0.45,
}


def robust_loss(actual: dict[str, float], simulated: dict[str, float], tolerances: dict[str, float], weights: dict[str, float]) -> float:
    """Fixed-tolerance Huber-like loss; missing optional metrics are ignored."""
    total = 0.0
    weight_total = 0.0
    for key, weight in weights.items():
        if key not in actual or key not in simulated:
            continue
        av = actual[key]
        sv = simulated[key]
        if av is None or sv is None or not math.isfinite(float(av)) or not math.isfinite(float(sv)):
            continue
        z = (float(sv) - float(av)) / tolerances[key]
        az = abs(z)
        penalty = 0.5 * z * z if az <= 2.0 else 2.0 * az - 2.0
        total += weight * penalty
        weight_total += weight
    return total / weight_total if weight_total else float("inf")


def weighted_quantile(values: Sequence[float], weights: Sequence[float], q: float) -> float:
    if not values or len(values) != len(weights):
        raise ValueError("values/weights mismatch")
    pairs = sorted((float(v), float(w)) for v, w in zip(values, weights) if float(w) > 0)
    if not pairs:
        raise ValueError("no positive weights")
    target = max(0.0, min(1.0, q)) * sum(w for _, w in pairs)
    acc = 0.0
    for value, weight in pairs:
        acc += weight
        if acc >= target:
            return value
    return pairs[-1][0]


def weighted_summary(values: Iterable[float], weights: Iterable[float]) -> dict[str, float]:
    xs = [float(x) for x in values]
    ws = [float(w) for w in weights]
    if len(xs) != len(ws) or not xs:
        raise ValueError("invalid weighted sample")
    sw = sum(ws)
    if sw <= 0:
        raise ValueError("non-positive total weight")
    mean = sum(x * w for x, w in zip(xs, ws)) / sw
    variance = sum(w * (x - mean) ** 2 for x, w in zip(xs, ws)) / sw
    out = {"mean": mean, "sd": math.sqrt(max(0.0, variance))}
    for pct in (10, 25, 50, 75, 90, 95, 99):
        out[f"p{pct}"] = weighted_quantile(xs, ws, pct / 100.0)
    return out


def inverse_velocity_raw(avg_fastball_kmh: float, lo: float = 30.0, hi: float = 250.0) -> float:
    """Invert frozen Velocity v2 uncapped/base mapping without changing the mapping."""
    target = float(avg_fastball_kmh)
    if not math.isfinite(target):
        raise ValueError("non-finite velocity")
    if target < raw_to_uncapped_avg_kmh(lo) or target > base_avg_kmh(hi):
        raise ValueError("velocity outside frozen inverse search domain")
    left, right = lo, hi
    for _ in range(80):
        mid = (left + right) / 2.0
        value = base_avg_kmh(mid)
        if value < target:
            left = mid
        else:
            right = mid
    return (left + right) / 2.0


def velocity_contract(avg_fastball_kmh: float) -> dict[str, float]:
    raw = inverse_velocity_raw(avg_fastball_kmh)
    physical = base_avg_kmh(raw)
    return {
        "avg_fastball_kmh": physical,
        "raw_velocity": raw,
        "gp_velocity": gameplay_velocity(physical),
    }


def normalized_hitter(raw_contact: float, raw_power: float, raw_discipline: float, raw_speed: float) -> dict[str, float]:
    gp = normalize_hitter(raw_contact, raw_power, raw_discipline, raw_speed)
    return {
        "gp_contact": gp.contact,
        "gp_power": gp.power,
        "gp_discipline": gp.discipline,
        "gp_speed": gp.speed,
    }


def shrink_rate(successes: float, opportunities: float, league_rate: float, pseudo_count: float) -> float:
    """Simple documented empirical-Bayes style pseudo-count shrinkage."""
    n = max(0.0, float(opportunities))
    pc = max(0.0, float(pseudo_count))
    return (float(successes) + pc * float(league_rate)) / (n + pc) if n + pc else float(league_rate)


@dataclass(frozen=True)
class CandidateFit:
    ratings: tuple[float, ...]
    loss: float
    simulated: dict[str, float]


def confidence_from_alternatives(best_loss: float, alternative_losses: Sequence[float]) -> str:
    if not alternative_losses:
        return "low"
    second = min(alternative_losses)
    gap = second - best_loss
    if best_loss <= 1.0 and gap >= 0.30:
        return "high"
    if best_loss <= 2.5 and gap >= 0.10:
        return "medium"
    return "low"
