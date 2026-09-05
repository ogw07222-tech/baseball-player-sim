"""Derived hitter career-rating -> H3 gameplay-rating normalization.

Raw ratings remain the persisted/display career state. This module is the
single conversion boundary before existing H3.2.1 math; it does not mutate raw
PlayerStats and it deliberately contains no outcome formula.
"""
from __future__ import annotations
from dataclasses import dataclass
import math

GAMEPLAY_REFERENCE = 100.0

# Measured age-26/28/30 mixed production references after the validated hitter
# C/P/D developmental re-centering (30k cohort, seed 91901, 2026-09-06).
CONTACT_RAW_REFERENCE = 109.26405555555556
POWER_RAW_REFERENCE = 109.10451111111111
DISCIPLINE_RAW_REFERENCE = 108.80516666666666
# Speed is not re-centered in Stage A; this is its measured production prime.
SPEED_RAW_REFERENCE = 98.10803333333332

# Linear remains the baseline contract. C/P/D slopes are validated by overnight
# Monte Carlo before production wiring; Speed is validated separately against
# the full baserunning value paths.
CONTACT_GAMEPLAY_PER_RAW = 0.60
POWER_GAMEPLAY_PER_RAW = 0.60
DISCIPLINE_GAMEPLAY_PER_RAW = 0.60
SPEED_GAMEPLAY_PER_RAW = 0.60


def _linear(raw: float, reference: float, slope: float) -> float:
    value = GAMEPLAY_REFERENCE + (float(raw) - reference) * slope
    if not math.isfinite(value):
        raise ValueError("non-finite hitter rating")
    return value


def normalize_contact(raw: float) -> float:return _linear(raw,CONTACT_RAW_REFERENCE,CONTACT_GAMEPLAY_PER_RAW)
def normalize_power(raw: float) -> float:return _linear(raw,POWER_RAW_REFERENCE,POWER_GAMEPLAY_PER_RAW)
def normalize_discipline(raw: float) -> float:return _linear(raw,DISCIPLINE_RAW_REFERENCE,DISCIPLINE_GAMEPLAY_PER_RAW)
def normalize_speed(raw: float) -> float:return _linear(raw,SPEED_RAW_REFERENCE,SPEED_GAMEPLAY_PER_RAW)

@dataclass(frozen=True)
class HitterGameplaySnapshot:
    contact: float
    power: float
    discipline: float
    speed: float

def normalize_hitter(contact: float,power: float,discipline: float,speed: float)->HitterGameplaySnapshot:
    return HitterGameplaySnapshot(normalize_contact(contact),normalize_power(power),normalize_discipline(discipline),normalize_speed(speed))
