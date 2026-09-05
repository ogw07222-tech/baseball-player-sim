"""Derived hitter career-rating -> H3 gameplay-rating normalization.

Raw ratings remain the persisted/display career state.  This module is the
single conversion boundary before existing H3.2.1 math; it does not mutate raw
PlayerStats and it deliberately contains no outcome formula.
"""
from __future__ import annotations
from dataclasses import dataclass
import math

GAMEPLAY_REFERENCE = 100.0

# Measured 26-30 production-grown raw references (30k cohort, 2026-09-06).
CONTACT_RAW_REFERENCE = 94.2742
POWER_RAW_REFERENCE = 92.78481111111111
DISCIPLINE_RAW_REFERENCE = 87.34492222222222
SPEED_RAW_REFERENCE = 98.0363888888889

# Provisional linear slopes; calibration tooling may revise these values, but
# the architecture stays linear unless explicit double-compression/extreme
# diagnostics prove a mild nonlinear tail is required.
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


def normalize_hitter(contact: float, power: float, discipline: float, speed: float) -> HitterGameplaySnapshot:
    return HitterGameplaySnapshot(
        normalize_contact(contact), normalize_power(power),
        normalize_discipline(discipline), normalize_speed(speed),
    )
