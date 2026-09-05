"""Position-aware high-school performance scoring for KBO draft evaluation.

This module is intentionally outside ``src.hitting``: H3.2.1 gameplay math is
frozen. Draft scoring consumes observed game results and converts them to a
league-relative common score shared by hitter and pitcher evaluators.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Mapping, Sequence

from . import config
from .records import BattingLine

CATCHER_EVALUATION_PENDING = "CATCHER_EVALUATION_PENDING"
HITTER_POSITION_AWARE = "HITTER_POSITION_AWARE"
PITCHER_ROLE_AWARE = "PITCHER_ROLE_AWARE"


@dataclass(frozen=True)
class DraftPerformanceScore:
    score: float
    index: float
    reliability: float
    overall_percentile: float
    position_percentile: float
    evaluation_mode: str
    metric_z: dict[str, float]


@dataclass(frozen=True)
class DraftEvaluation:
    score: float
    performance: DraftPerformanceScore
    component_scores: dict[str, float]
    component_index: dict[str, float]
    contribution_points: dict[str, float]
    noise: float


def _normal_percentile(z: float) -> float:
    return 100.0 * 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def _observed_metrics(line: BattingLine) -> dict[str, float]:
    pa = max(1, line.PA)
    return {
        "obp": line.OBP,
        "iso": max(0.0, line.SLG - line.AVG),
        "hr_rate": line.HR / pa,
        "bb_rate": line.BB / pa,
        "k_rate": line.SO / pa,
        "baserunning": (line.SB - 1.4 * line.CS) / pa,
    }


def _metric_z(line: BattingLine, reliability: float) -> dict[str, float]:
    observed = _observed_metrics(line)
    out: dict[str, float] = {}
    for name, (mean, stddev, direction) in config.HIGH_SCHOOL_PERFORMANCE_BASELINES.items():
        adjusted = mean + reliability * (observed[name] - mean)
        out[name] = direction * (adjusted - mean) / stddev if stddev else 0.0
    return out


def _weighted_index(metric_z: Mapping[str, float], weights: Mapping[str, float]) -> float:
    total = sum(weights.values())
    if total <= 0:
        raise ValueError("performance weights must have positive total")
    return sum(metric_z[name] * weight for name, weight in weights.items()) / total


def score_hitter_performance(line: BattingLine, position: str) -> DraftPerformanceScore:
    if position not in config.POSITIONS:
        raise ValueError(f"unsupported position: {position}")
    k = config.HIGH_SCHOOL_PERFORMANCE_RELIABILITY_PA
    reliability = line.PA / (line.PA + k) if line.PA > 0 else 0.0
    metric_z = _metric_z(line, reliability)
    overall_index = _weighted_index(metric_z, config.OVERALL_HITTER_PERFORMANCE_WEIGHTS)
    if position == "C":
        weights = config.CATCHER_LEGACY_PERFORMANCE_WEIGHTS
        mode = CATCHER_EVALUATION_PENDING
    else:
        weights = config.POSITION_PERFORMANCE_WEIGHTS[position]
        mode = HITTER_POSITION_AWARE
    position_index = _weighted_index(metric_z, weights)
    score = 100.0 + 15.0 * position_index
    return DraftPerformanceScore(
        score=score,
        index=position_index,
        reliability=reliability,
        overall_percentile=_normal_percentile(overall_index),
        position_percentile=_normal_percentile(position_index),
        evaluation_mode=mode,
        metric_z=metric_z,
    )


def scout_projection_score(scouted_talent: float) -> float:
    return 100.0 + (scouted_talent - 100.0) * 0.20


def position_value_score(position: str) -> float:
    return 100.0 + float(config.POSITION_DRAFT_VALUE.get(position, 0.0))


def health_score(durability: float) -> float:
    return 100.0 + (durability - 100.0) * 0.25


def tournament_context_score(tournament_results: Sequence[Mapping[str, object]]) -> float:
    champions = sum(bool(result.get("champion")) for result in tournament_results)
    mvps = sum(bool(result.get("mvp")) for result in tournament_results)
    return 100.0 + min(18.0, champions * 3.0 + mvps * 5.0)


def evaluate_hitter_draft(
    line: BattingLine,
    position: str,
    scouted_talent: float,
    durability: float,
    tournament_results: Sequence[Mapping[str, object]],
    rng,
) -> DraftEvaluation:
    performance = score_hitter_performance(line, position)
    component_scores = {
        "performance": performance.score,
        "scouting": scout_projection_score(scouted_talent),
        "position": position_value_score(position),
        "health": health_score(durability),
        "context": tournament_context_score(tournament_results),
    }
    component_index = {
        name: (component_scores[name] - config.DRAFT_COMPONENT_REFERENCE) / config.DRAFT_COMPONENT_SCALE
        for name in component_scores
    }
    contribution_points = {
        name: config.DRAFT_SCORE_SPREAD * config.DRAFT_WEIGHTS[name] * component_index[name]
        for name in component_scores
    }
    noise = rng.gauss(0.0, config.DRAFT_RANDOM_SD)
    score = config.DRAFT_SCORE_CENTER + sum(contribution_points.values()) + noise
    return DraftEvaluation(
        score=score,
        performance=performance,
        component_scores=component_scores,
        component_index=component_index,
        contribution_points=contribution_points,
        noise=noise,
    )


def score_pitcher_performance(line, role: str = "starter") -> DraftPerformanceScore:
    """Map the pitcher foundation onto the shared 100 + 15*index score type."""
    from .pitching.performance import score_pitcher_performance as _score
    result = _score(line, role)
    return DraftPerformanceScore(
        score=result.score,
        index=result.index,
        reliability=result.reliability,
        overall_percentile=result.percentile,
        position_percentile=result.percentile,
        evaluation_mode=PITCHER_ROLE_AWARE,
        metric_z=result.metric_z,
    )
