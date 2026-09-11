"""Authoritative, presentation-free career transition facts owned by 03.

Facts are emitted at the mutation point where career state changes. They contain
no narrative text, importance, UI ordering policy, or transport DTO semantics;
04 may normalize them into presentation events later.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Mapping


@dataclass(frozen=True, init=False)
class CareerSourceFact:
    fact_type: str
    season: int | None
    game_number: int | None
    simulated_date: date | None
    phase: str
    local_ordinal: int
    player_id: str | None
    team_id: str | None
    before_state: Mapping[str, object] = field(default_factory=dict)
    after_state: Mapping[str, object] = field(default_factory=dict)
    state_delta: Mapping[str, object] = field(default_factory=dict)
    existing_history_kind: str | None = None
    existing_dedupe_key: str | None = None
    persistence_hint: str | None = None

    def __init__(
        self,
        fact_type: str,
        season: int | None,
        game_number: int | None,
        simulated_date: date | None,
        phase: str,
        local_ordinal: int,
        player_id: str | None = None,
        team_id: str | None = None,
        before_state: Mapping[str, object] | None = None,
        after_state: Mapping[str, object] | None = None,
        state_delta: Mapping[str, object] | None = None,
        existing_history_kind: str | None = None,
        existing_dedupe_key: str | None = None,
        persistence_hint: str | None = None,
        *,
        player_identifier: str | None = None,
        team_identifier: str | None = None,
        before: Mapping[str, object] | None = None,
        after: Mapping[str, object] | None = None,
        authoritative_state_delta: Mapping[str, object] | None = None,
        existing_identity: str | None = None,
    ) -> None:
        canonical_player = player_id if player_id is not None else player_identifier
        canonical_team = team_id if team_id is not None else team_identifier
        canonical_before = dict(before_state if before_state is not None else before or {})
        canonical_after = dict(after_state if after_state is not None else after or {})
        canonical_delta = dict(state_delta if state_delta is not None else authoritative_state_delta or {})
        canonical_history = existing_history_kind
        if canonical_history is None and persistence_hint in {
            "career_history",
            "injury_history",
            "event_history",
            "trait_history",
            "growth_history",
        }:
            canonical_history = persistence_hint
        canonical_dedupe = existing_dedupe_key if existing_dedupe_key is not None else existing_identity

        object.__setattr__(self, "fact_type", fact_type)
        object.__setattr__(self, "season", season)
        object.__setattr__(self, "game_number", game_number)
        object.__setattr__(self, "simulated_date", simulated_date)
        object.__setattr__(self, "phase", phase)
        object.__setattr__(self, "local_ordinal", int(local_ordinal))
        object.__setattr__(self, "player_id", canonical_player)
        object.__setattr__(self, "team_id", canonical_team)
        object.__setattr__(self, "before_state", canonical_before)
        object.__setattr__(self, "after_state", canonical_after)
        object.__setattr__(self, "state_delta", canonical_delta)
        object.__setattr__(self, "existing_history_kind", canonical_history)
        object.__setattr__(self, "existing_dedupe_key", canonical_dedupe)
        object.__setattr__(self, "persistence_hint", persistence_hint)

    @property
    def occurred_at(self) -> date | None:
        return self.simulated_date

    # Compatibility aliases are object-only. Serialized output below is the
    # canonical 03 -> 04 source-fact contract.
    @property
    def player_identifier(self) -> str | None:
        return self.player_id

    @property
    def team_identifier(self) -> str | None:
        return self.team_id

    @property
    def before(self) -> Mapping[str, object]:
        return self.before_state

    @property
    def after(self) -> Mapping[str, object]:
        return self.after_state

    @property
    def authoritative_state_delta(self) -> Mapping[str, object]:
        return self.state_delta

    @property
    def existing_identity(self) -> str | None:
        return self.existing_dedupe_key

    def as_dict(self) -> dict[str, object]:
        return {
            "fact_type": self.fact_type,
            "season": self.season,
            "game_number": self.game_number,
            "simulated_date": self.simulated_date.isoformat() if self.simulated_date else None,
            "phase": self.phase,
            "local_ordinal": self.local_ordinal,
            "player_id": self.player_id,
            "team_id": self.team_id,
            "before_state": dict(self.before_state),
            "after_state": dict(self.after_state),
            "state_delta": dict(self.state_delta),
            "existing_history_kind": self.existing_history_kind,
            "existing_dedupe_key": self.existing_dedupe_key,
            "persistence_hint": self.persistence_hint,
        }
