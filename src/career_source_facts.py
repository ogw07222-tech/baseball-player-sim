"""Authoritative, presentation-free career transition facts owned by 03.

These facts are emitted at the mutation point where career state changes. They
contain no narrative text, importance, UI ordering policy, or transport DTO
semantics; 04 may normalize them into presentation events later.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Mapping


@dataclass(frozen=True)
class CareerSourceFact:
    fact_type: str
    season: int | None
    game_number: int | None
    simulated_date: date | None
    phase: str
    local_ordinal: int
    player_identifier: str | None
    team_identifier: str | None
    before: Mapping[str, object] = field(default_factory=dict)
    after: Mapping[str, object] = field(default_factory=dict)
    authoritative_state_delta: Mapping[str, object] = field(default_factory=dict)
    persistence_hint: str | None = None
    existing_identity: str | None = None

    def as_dict(self) -> dict[str, object]:
        return {
            "fact_type": self.fact_type,
            "season": self.season,
            "game_number": self.game_number,
            "simulated_date": self.simulated_date.isoformat() if self.simulated_date else None,
            "phase": self.phase,
            "local_ordinal": self.local_ordinal,
            "player_identifier": self.player_identifier,
            "team_identifier": self.team_identifier,
            "before": dict(self.before),
            "after": dict(self.after),
            "authoritative_state_delta": dict(self.authoritative_state_delta),
            "persistence_hint": self.persistence_hint,
            "existing_identity": self.existing_identity,
        }
