"""Derived hitter career-rating -> H3 gameplay-rating normalization.

Raw ratings remain the persisted/display career state. This module is the
single conversion boundary before existing H3.2.1 math; it does not mutate raw
PlayerStats and it deliberately contains no outcome formula.
"""
from __future__ import annotations
from dataclasses import dataclass
import math

GAMEPLAY_REFERENCE = 100.0

# Measured age-26/28/30 mixed production-grown references after the validated
# development-only C/P/D re-centering (30k cohort, 2026-09-06).
CONTACT_RAW_REFERENCE = 108.14008888888888
POWER_RAW_REFERENCE = 108.34556666666667
DISCIPLINE_RAW_REFERENCE = 108.38894444444445
# Speed was deliberately not re-centered. Its full-value H3.2.1 baserunning
# validation supports the existing raw population reference.
SPEED_RAW_REFERENCE = 98.0770111111111

# Selected linear contract. The 0.60 slope preserves raw display separation
# while keeping prime gameplay inputs clustered around H3's mathematical 100.
CONTACT_GAMEPLAY_PER_RAW = 0.60
POWER_GAMEPLAY_PER_RAW = 0.60
DISCIPLINE_GAMEPLAY_PER_RAW = 0.60
SPEED_GAMEPLAY_PER_RAW = 0.60


def _linear(raw: float, reference: float, slope: float) -> float:
    value = GAMEPLAY_REFERENCE + (float(raw) - reference) * slope
    if not math.isfinite(value):
        raise ValueError("non-finite hitter rating")
    return value


def normalize_contact(raw: float) -> float:
    return _linear(raw, CONTACT_RAW_REFERENCE, CONTACT_GAMEPLAY_PER_RAW)


def normalize_power(raw: float) -> float:
    return _linear(raw, POWER_RAW_REFERENCE, POWER_GAMEPLAY_PER_RAW)


def normalize_discipline(raw: float) -> float:
    return _linear(raw, DISCIPLINE_RAW_REFERENCE, DISCIPLINE_GAMEPLAY_PER_RAW)


def normalize_speed(raw: float) -> float:
    return _linear(raw, SPEED_RAW_REFERENCE, SPEED_GAMEPLAY_PER_RAW)


@dataclass(frozen=True)
class HitterGameplaySnapshot:
    contact: float
    power: float
    discipline: float
    speed: float


def normalize_hitter(
    contact: float,
    power: float,
    discipline: float,
    speed: float,
) -> HitterGameplaySnapshot:
    return HitterGameplaySnapshot(
        normalize_contact(contact),
        normalize_power(power),
        normalize_discipline(discipline),
        normalize_speed(speed),
    )
