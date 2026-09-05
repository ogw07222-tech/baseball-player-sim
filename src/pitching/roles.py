"""Pitcher usage roles. Roles never mutate base stats."""
from __future__ import annotations
from dataclasses import dataclass
from . import parameters as P

PITCHER_ROLES=("starter","reliever")

@dataclass(frozen=True)
class RoleModifiers:
    stamina_drain:float
    velocity_bonus:float
    stuff_bonus:float


def role_modifiers(role:str)->RoleModifiers:
    if role=="starter": return RoleModifiers(P.STARTER_DRAIN,0.0,0.0)
    if role=="reliever": return RoleModifiers(P.RELIEVER_DRAIN,P.RELIEVER_VELOCITY_BONUS,P.RELIEVER_STUFF_BONUS)
    raise ValueError(f"unknown pitcher role: {role}")
