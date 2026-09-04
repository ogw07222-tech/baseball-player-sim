"""H3/H3.1 experimental batted-ball model. Never imported by production src/."""
from .model import H31Model, simulate_profile
from .profiles import H3HitterProfile, H3PitcherProfile, H3DefenseProfile

__all__ = ["H31Model", "simulate_profile", "H3HitterProfile", "H3PitcherProfile", "H3DefenseProfile"]
