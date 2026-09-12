"""03 Growth & Career authority for applying 04 InteractiveEvent effect requests.

04 owns event occurrence, choices and declarative requests. This module owns the
translation from those requests into existing career state. It deliberately
keeps EVENT resolution separate from CAREER timeline presentation.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Mapping

from . import config
from .growth import GROWABLE_STATS
from .interactive_events import (
    EVENT_STATUS_PENDING,
    EventChoiceEffect,
    InteractiveEventResolution,
    InteractiveEventState,
    event_state_for_engine,
)


class UnsupportedInteractiveEffect(ValueError):
    """The request has no authoritative interpretation in current production semantics."""


@dataclass(frozen=True)
class ActiveCareerEffect:
    effect_type: str
    target: str
    magnitude: str
    games_remaining: int
    source_event_id: str
    parameters: Mapping[str, object] = field(default_factory=dict)

    def as_dict(self) -> dict[str, object]:
        return {
            "effect_type": self.effect_type,
            "target": self.target,
            "magnitude": self.magnitude,
            "games_remaining": self.games_remaining,
            "source_event_id": self.source_event_id,
            "parameters": dict(self.parameters),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> "ActiveCareerEffect":
        return cls(
            effect_type=str(data["effect_type"]),
            target=str(data["target"]),
            magnitude=str(data["magnitude"]),
            games_remaining=int(data["games_remaining"]),
            source_event_id=str(data["source_event_id"]),
            parameters=dict(data.get("parameters", {})),
        )


@dataclass
class InteractiveCareerEffectState:
    active_effects: list[ActiveCareerEffect] = field(default_factory=list)

    def as_dict(self) -> dict[str, object]:
        return {"active_effects": [effect.as_dict() for effect in self.active_effects]}

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> "InteractiveCareerEffectState":
        return cls([ActiveCareerEffect.from_dict(dict(v)) for v in data.get("active_effects", [])])


def effect_state_for_engine(engine: object) -> InteractiveCareerEffectState:
    state = getattr(engine, "interactive_career_effect_state", None)
    if isinstance(state, InteractiveCareerEffectState):
        return state
    state = InteractiveCareerEffectState()
    setattr(engine, "interactive_career_effect_state", state)
    return state


# Semantic magnitude -> existing system parameter. These values are plumbing
# constants, not balance claims; 05 owns later calibration.
TRAINING_MEAN_PER_GAME = {
    "high": 0.025,
    "medium": 0.018,
    "balanced": 0.010,
    "low": 0.005,
    "partial": 0.008,
    "maintain": 0.0,
}
DEVELOPMENT_MEAN_PER_GAME = {
    "upside_medium": 0.020,
    "upside_small": 0.010,
    "small": 0.008,
    "opportunity_cost_small": -0.008,
    "opportunity_cost_medium": -0.015,
}
DEVELOPMENT_VARIANCE_PER_GAME = {"variance_medium": 1.001}
FATIGUE_DELTA_PER_GAME = {
    "cost_small": 1.0,
    "cost_medium": 2.0,
    "recovery_small": -1.0,
    "recovery_medium": -2.0,
    "recovery_large": -3.0,
}
FORM_DURATION_DELTA = {
    "stability_up": {"slump": -1},
    "breakthrough_chance": {"slump": -1},
    "momentum_decay_small": {"hot": -1},
    "variance_small": {"slump": 1, "hot": 1},
    "variance_medium": {"slump": 1, "hot": 1},
}


def _rating_targets(player: object, target: str) -> tuple[str, ...]:
    if target == "hitting":
        return ("contact", "power", "discipline")
    if target in {"defense", "defense_range"}:
        return ("defense", "speed") if target == "defense_range" else ("defense", "throwing")
    if target == "throwing":
        return ("throwing",)
    if target in {"all", "player"}:
        return tuple(GROWABLE_STATS)
    if target == "weakest_rating":
        return (min(GROWABLE_STATS, key=lambda key: (getattr(player.stats, key), key)),)
    if target == "strongest_rating":
        return (max(GROWABLE_STATS, key=lambda key: (getattr(player.stats, key), key)),)
    if target in {"coach_recommendation", "player_routine"}:
        return tuple(GROWABLE_STATS)
    raise UnsupportedInteractiveEffect(f"unsupported development target: {target}")


def _plan_effect(player: object, event_id: str, effect: EventChoiceEffect) -> ActiveCareerEffect:
    if effect.duration is None or effect.duration <= 0:
        raise UnsupportedInteractiveEffect(f"temporary effect requires positive game duration: {effect.effect_type}")
    if effect.effect_type == "training_focus":
        if effect.magnitude not in TRAINING_MEAN_PER_GAME:
            raise UnsupportedInteractiveEffect(f"unsupported training magnitude: {effect.magnitude}")
        targets = _rating_targets(player, effect.target)
        return ActiveCareerEffect(effect.effect_type, effect.target, effect.magnitude, effect.duration, event_id, {
            "mean_per_game": TRAINING_MEAN_PER_GAME[effect.magnitude], "stats": list(targets)
        })
    if effect.effect_type == "development_modifier":
        targets = _rating_targets(player, effect.target)
        if effect.magnitude in DEVELOPMENT_MEAN_PER_GAME:
            return ActiveCareerEffect(effect.effect_type, effect.target, effect.magnitude, effect.duration, event_id, {
                "mean_per_game": DEVELOPMENT_MEAN_PER_GAME[effect.magnitude], "stats": list(targets)
            })
        if effect.magnitude in DEVELOPMENT_VARIANCE_PER_GAME:
            return ActiveCareerEffect(effect.effect_type, effect.target, effect.magnitude, effect.duration, event_id, {
                "variance_per_game": DEVELOPMENT_VARIANCE_PER_GAME[effect.magnitude], "stats": list(targets)
            })
        raise UnsupportedInteractiveEffect(f"unsupported development magnitude: {effect.magnitude}")
    if effect.effect_type == "fatigue_modifier":
        if effect.target != "player" or effect.magnitude not in FATIGUE_DELTA_PER_GAME:
            raise UnsupportedInteractiveEffect(f"unsupported fatigue request: {effect.target}/{effect.magnitude}")
        return ActiveCareerEffect(effect.effect_type, effect.target, effect.magnitude, effect.duration, event_id, {
            "fatigue_delta_per_game": FATIGUE_DELTA_PER_GAME[effect.magnitude]
        })
    if effect.effect_type == "form_modifier":
        if effect.magnitude not in FORM_DURATION_DELTA:
            raise UnsupportedInteractiveEffect(f"unsupported form magnitude: {effect.magnitude}")
        if effect.target not in {"player", "pressure", "role_execution"}:
            raise UnsupportedInteractiveEffect(f"unsupported form target: {effect.target}")
        return ActiveCareerEffect(effect.effect_type, effect.target, effect.magnitude, effect.duration, event_id, {
            "duration_delta": dict(FORM_DURATION_DELTA[effect.magnitude])
        })
    if effect.effect_type == "temporary_trait_request":
        # Current Player.traits are durable traits only. There is no authoritative
        # temporary-trait overlay consumed by gameplay/growth, so fabricating one
        # would create semantics that production does not have.
        raise UnsupportedInteractiveEffect("temporary Trait semantics are not implemented in production")
    raise UnsupportedInteractiveEffect(f"unsupported interactive effect type: {effect.effect_type}")


def _locate_pending_choice(state: InteractiveEventState, event_id: str, choice_id: str):
    event = next((event for event in state.events if event.event_id == event_id), None)
    if event is None:
        raise KeyError(f"unknown interactive event: {event_id}")
    if event.status != EVENT_STATUS_PENDING:
        raise RuntimeError(f"interactive event is not pending: {event_id}")
    choice = next((choice for choice in event.choices if choice.choice_id == choice_id), None)
    if choice is None:
        raise ValueError(f"invalid choice for {event_id}: {choice_id}")
    return event, choice


def resolve_interactive_event_authoritatively(
    *, engine: object, event_id: str, choice_id: str, resolved_at: date | None
) -> InteractiveEventResolution:
    """Validate all requests, apply them atomically, then mark the EVENT resolved.

    No CareerSourceFact is emitted merely because a choice was made. Existing
    career mutation paths remain responsible for facts when a real transition
    (for example form_transition) actually occurs later.
    """
    session = getattr(engine, "current_session", None)
    if session is None:
        raise RuntimeError("interactive event effects require an active professional season")
    event_state = event_state_for_engine(engine)
    _, choice = _locate_pending_choice(event_state, event_id, choice_id)
    plans = tuple(_plan_effect(engine.player, event_id, effect) for effect in choice.preview_effects)

    # All validation is complete before the first authoritative mutation.
    effect_state = effect_state_for_engine(engine)
    event_snapshot = event_state.as_dict()
    effects_snapshot = effect_state.as_dict()
    try:
        effect_state.active_effects.extend(plans)
        # 04 resolve mutates only the EVENT record. Calling it last guarantees
        # that an invalid/unsupported effect can never leave a resolved event.
        return event_state.resolve(event_id, choice_id, resolved_at)
    except Exception:
        engine.interactive_event_state = InteractiveEventState.from_dict(event_snapshot)
        engine.interactive_career_effect_state = InteractiveCareerEffectState.from_dict(effects_snapshot)
        raise


def _apply_growth_tick(engine: object, effect: ActiveCareerEffect) -> None:
    session = getattr(engine, "current_session", None)
    if session is None:
        return
    params = dict(effect.parameters)
    stats = tuple(str(v) for v in params.get("stats", []))
    if "mean_per_game" in params:
        amount = float(params["mean_per_game"])
        for stat_name in stats:
            session.growth_modifiers.add_mean(stat_name, amount)
    if "variance_per_game" in params:
        session.growth_modifiers.variance_multiplier *= float(params["variance_per_game"])


def apply_interactive_pre_form_effects(engine: object) -> None:
    """Apply active fatigue/form effects after base rest/game fatigue but before form update."""
    state = effect_state_for_engine(engine)
    player = engine.player
    for effect in state.active_effects:
        params = dict(effect.parameters)
        if effect.effect_type == "fatigue_modifier":
            player.fatigue = max(0.0, min(100.0, player.fatigue + float(params["fatigue_delta_per_game"])))
        elif effect.effect_type == "form_modifier" and player.form_games_remaining > 0:
            delta_by_form = dict(params.get("duration_delta", {}))
            delta = int(delta_by_form.get(player.form, 0))
            if delta:
                player.form_games_remaining = max(0, player.form_games_remaining + delta)
                if player.form_games_remaining == 0 and player.form != "normal":
                    before = player.form
                    player.form = "normal"
                    emit = getattr(engine, "_emit_source_fact", None)
                    if callable(emit):
                        emit(
                            "form_transition",
                            before={"form": before, "games_remaining": 1},
                            after={"form": "normal", "games_remaining": 0},
                            authoritative_state_delta={"form": {"before": before, "after": "normal"}},
                        )


def advance_interactive_effects_one_game(engine: object) -> None:
    """Accrue development effects for one committed game and expire durations exactly."""
    state = effect_state_for_engine(engine)
    remaining: list[ActiveCareerEffect] = []
    for effect in state.active_effects:
        if effect.effect_type in {"training_focus", "development_modifier"}:
            _apply_growth_tick(engine, effect)
        games_left = effect.games_remaining - 1
        if games_left > 0:
            remaining.append(ActiveCareerEffect(
                effect.effect_type,
                effect.target,
                effect.magnitude,
                games_left,
                effect.source_event_id,
                dict(effect.parameters),
            ))
    state.active_effects = remaining


def clear_season_interactive_effects(engine: object) -> None:
    """Season-bound temporary effects cannot silently leak into the next season."""
    state = effect_state_for_engine(engine)
    state.active_effects.clear()
