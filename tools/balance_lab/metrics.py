"""Shared metric helpers for Balance Lab.

Keep generic aggregation/validation here. Do not duplicate plate-appearance or
career simulation logic from `src/`.
"""

from __future__ import annotations

from dataclasses import dataclass
from statistics import mean
from typing import Iterable


@dataclass(frozen=True)
class MetricSummary:
    count: int
    mean: float
    minimum: float
    maximum: float


def summarize(values: Iterable[float]) -> MetricSummary:
    materialized = [float(value) for value in values]
    if not materialized:
        raise ValueError("values must contain at least one observation")
    return MetricSummary(
        count=len(materialized),
        mean=mean(materialized),
        minimum=min(materialized),
        maximum=max(materialized),
    )
