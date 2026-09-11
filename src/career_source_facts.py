"""Authoritative, presentation-free career transition facts owned by 03.

Facts are emitted at the mutation point where career state changes. They contain
no narrative text, importance, UI ordering policy, or transport DTO semantics;
04 may normalize them into presentation events later.
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
    player_id: str | None
    team_id: str | None
    before_state: Mapping[str, object] = field(default_factory=dict)
    after_state: Mapping[str, object] = field(default_factory=dict)
    state_delta: Mapping[str, object] = field(default_factory=dict)
    existing_history_kind: str | None = None
    existing_dedupe_key: str | None = None
    persistence_hint: str | None = None

    # Internal compatibility aliases while downstream 04/07 migrate to the
    # canonical source-fact field names above.
    @property
    def occurred_at(self) -> date | None:
        return self.simulated_date

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
