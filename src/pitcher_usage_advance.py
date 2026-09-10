"""Backward-compatible alias for the canonical dynamic production advance path.

The consolidation makes ``ProductionAdvanceService`` usage-aware by default.
This name remains only so stacked PR #32 callers/tests keep importing safely;
it does not own a second advance implementation.
"""
from __future__ import annotations

from .production_advance import ProductionAdvanceService


class PitcherUsageProductionAdvanceService(ProductionAdvanceService):
    """Compatibility alias; canonical behavior lives in ProductionAdvanceService."""

    pass
