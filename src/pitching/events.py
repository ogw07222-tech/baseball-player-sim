"""Future-compatible pitcher event role filtering without adding event content."""
from __future__ import annotations

def role_eligible(eligible_roles:tuple[str,...],player_role:str)->bool:
    return "all" in eligible_roles or player_role in eligible_roles

HITTER_ONLY=("hitter",)
PITCHER_ONLY=("pitcher",)
ALL_PLAYERS=("all",)
