"""Experimental pitcher calibration lab.

This package is intentionally isolated from production gameplay.  It adapts the
frozen H3.2.1 hitter engine without changing any ``src/hitting`` formula.
"""

from .adapter import CalibrationWeights, PitcherPAAdapter
from .effort import EffortModel, EffortProfile

__all__ = [
    "CalibrationWeights",
    "PitcherPAAdapter",
    "EffortModel",
    "EffortProfile",
]
