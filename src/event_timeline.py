"""Canonical, deterministic progression-event timeline DTOs.

This module is presentation/domain plumbing only. It normalizes authoritative
simulation facts for one advance response and does not own gameplay, growth,
injury, roster, or event probabilities.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date
from typing import Iterable, Mapping, Sequence


PHASE_ORDER = {
    "pre_game": 0,
    "in_game": 1,
    "post_game": 2,
    "off_day": 3,
    "lifecycle": 4,
}


@dataclass(frozen=True)
class CanonicalEventDTO:
    event_id: str
    event_type: str
    category: str
    occurred_at: str | None
    season: int | None
    game_number: int | None
    sequence: int
    title: str
    summary: str
    importance: str = "normal"
    player_id: str | None = None
    team_id: str | None = None
    related_entity_ids: tuple[str, ...] = ()
    state_effects: Mapping[str, object] | None = None
    rating_changes: Mapping[str, int] | None = None
    injury_effect: Mapping[str, object] | None = None
    trait_changes: tuple[str, ...] = ()
    source_command: str | None = None
    presentation_priority: int = 50
    persistence: str = "transient"
    dedupe_key: str = ""
    phase: str = "post_game"
    source_ordinal: int = 0

    def as_dict(self) -> dict[str, object]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "category": self.category,
            "occurred_at": self.occurred_at,
            "season": self.season,
            "game_number": self.game_number,
            "sequence": self.sequence,
            "title": self.title,
            "summary": self.summary,
            "importance": self.importance,
            "player_id": self.player_id,
            "team_id": self.team_id,
            "related_entity_ids": list(self.related_entity_ids),
            "state_effects": dict(self.state_effects) if self.state_effects is not None else None,
            "rating_changes": dict(self.rating_changes) if self.rating_changes is not None else None,
            "injury_effect": dict(self.injury_effect) if self.injury_effect is not None else None,
            "trait_changes": list(self.trait_changes),
            "source_command": self.source_command,
            "presentation_priority": self.presentation_priority,
            "persistence": self.persistence,
            "dedupe_key": self.dedupe_key,
            "phase": self.phase,
        }


def finalize_timeline(
    events: Iterable[CanonicalEventDTO],
    *,
    source_command: str,
) -> tuple[CanonicalEventDTO, ...]:
    """Deterministically sort, dedupe, and sequence one mutation timeline."""
    ordered = sorted(
        events,
        key=lambda event: (
            event.occurred_at or "",
            -1 if event.game_number is None else event.game_number,
            PHASE_ORDER.get(event.phase, 99),
            event.source_ordinal,
            event.event_id,
        ),
    )
    seen: set[str] = set()
    deduped: list[CanonicalEventDTO] = []
    for event in ordered:
        key = event.dedupe_key or event.event_id
        if key in seen:
            continue
        seen.add(key)
        deduped.append(event)
    return tuple(
        replace(event, sequence=index, source_command=source_command)
        for index, event in enumerate(deduped)
    )


def gameplay_notable_event(
    *,
    message: str,
    occurred_at: date,
    season: int,
    game_number: int,
    ordinal: int,
    team_id: str | None,
) -> CanonicalEventDTO:
    marker = message.split(":", 1)[0].strip().lower() or "game_event"
    identity = f"game:{season}:{game_number}:in_game:{ordinal}:{marker}"
    return CanonicalEventDTO(
        event_id=identity,
        event_type="gameplay_notable",
        category="gameplay",
        occurred_at=occurred_at.isoformat(),
        season=season,
        game_number=game_number,
        sequence=-1,
        title=marker.replace("_", " ").upper(),
        summary=message,
        importance="normal",
        team_id=team_id,
        presentation_priority=30,
        persistence="transient",
        dedupe_key=identity,
        phase="in_game",
        source_ordinal=ordinal,
    )


def career_history_events(
    entries: Sequence[Mapping[str, object]],
    *,
    occurred_at: date,
    current_game_number: int,
    start_ordinal: int = 0,
) -> list[CanonicalEventDTO]:
    out: list[CanonicalEventDTO] = []
    for offset, entry in enumerate(entries):
        logical_id = str(entry.get("event_id", "career_event"))
        dedupe = str(entry.get("dedupe_key") or f"career:{logical_id}:{entry.get('year')}:{entry.get('game_number')}")
        news = entry.get("news") if isinstance(entry.get("news"), Mapping) else {}
        facts = entry.get("facts") if isinstance(entry.get("facts"), Mapping) else {}
        raw_game = entry.get("game_number")
        game_number = int(raw_game) if raw_game is not None else None
        phase = "pre_game" if game_number is not None and game_number < current_game_number else "post_game"
        out.append(
            CanonicalEventDTO(
                event_id=f"career:{dedupe}",
                event_type=logical_id,
                category=str(entry.get("kind", "career")),
                occurred_at=occurred_at.isoformat(),
                season=int(entry.get("year")) if entry.get("year") is not None else None,
                game_number=game_number,
                sequence=-1,
                title=str(news.get("headline") or logical_id.replace("_", " ")),
                summary=str(news.get("body") or entry.get("trigger") or logical_id),
                importance=str(entry.get("importance", "normal")),
                team_id=str(entry.get("team")) if entry.get("team") is not None else None,
                state_effects=dict(facts),
                presentation_priority=90 if str(entry.get("importance")) == "major" else 70,
                persistence="career_history",
                dedupe_key=f"career:{dedupe}",
                phase=phase,
                source_ordinal=start_ordinal + offset,
            )
        )
    return out


def event_history_events(
    entries: Sequence[Mapping[str, object]],
    *,
    occurred_at: date,
    season: int,
    current_game_number: int,
    team_id: str | None,
    start_ordinal: int = 0,
) -> list[CanonicalEventDTO]:
    out: list[CanonicalEventDTO] = []
    for offset, entry in enumerate(entries):
        logical_id = str(entry.get("event_id", "career_event"))
        raw_game = entry.get("game_number")
        game_number = int(raw_game) if raw_game is not None else current_game_number
        identity = (
            f"event_history:{season}:{game_number}:{logical_id}:"
            f"{entry.get('choice', 'none')}:{entry.get('outcome', 'none')}"
        )
        stat_changes = entry.get("stat_changes") if isinstance(entry.get("stat_changes"), Mapping) else {}
        trait_changes = entry.get("trait_changes") if isinstance(entry.get("trait_changes"), Sequence) and not isinstance(entry.get("trait_changes"), (str, bytes)) else ()
        injury_change = str(entry.get("injury_changes", "none"))
        injury_effect = None if injury_change in {"", "none"} else {"change": injury_change}
        out.append(
            CanonicalEventDTO(
                event_id=identity,
                event_type=logical_id,
                category=str(entry.get("category", "career_event")),
                occurred_at=occurred_at.isoformat(),
                season=season,
                game_number=game_number,
                sequence=-1,
                title=str(entry.get("event_name", logical_id.replace("_", " "))),
                summary=str(entry.get("result") or entry.get("outcome") or logical_id),
                importance="major" if str(entry.get("rarity", "")) in {"major_breakthrough", "legendary_breakthrough"} else "normal",
                team_id=team_id,
                state_effects={"outcome": entry.get("outcome"), "choice": entry.get("choice")},
                rating_changes={str(k): int(v) for k, v in stat_changes.items()},
                injury_effect=injury_effect,
                trait_changes=tuple(str(value) for value in trait_changes),
                presentation_priority=80 if str(entry.get("rarity", "")) in {"major_breakthrough", "legendary_breakthrough"} else 55,
                persistence="event_history",
                dedupe_key=identity,
                phase="post_game",
                source_ordinal=start_ordinal + offset,
            )
        )
    return out


def injury_history_events(
    entries: Sequence[Mapping[str, object]],
    *,
    occurred_at: date,
    season: int,
    current_game_number: int,
    team_id: str | None,
    start_ordinal: int = 0,
) -> list[CanonicalEventDTO]:
    out: list[CanonicalEventDTO] = []
    for offset, entry in enumerate(entries):
        # Event-caused injuries are already represented by persistent event_history.
        if str(entry.get("source", "")) == "event":
            continue
        name = str(entry.get("name", "부상"))
        severity = str(entry.get("severity", "unknown"))
        games = int(entry.get("games", 0))
        identity = f"injury:{season}:{current_game_number}:{name}:{severity}:{games}"
        out.append(
            CanonicalEventDTO(
                event_id=identity,
                event_type="injury_started",
                category="injury",
                occurred_at=occurred_at.isoformat(),
                season=season,
                game_number=current_game_number,
                sequence=-1,
                title="부상 발생",
                summary=f"{name} ({severity}, 예상 결장 {games}경기)",
                importance="major" if severity == "중상" else "normal",
                team_id=team_id,
                injury_effect={"status": "started", "name": name, "severity": severity, "games": games},
                presentation_priority=95 if severity == "중상" else 75,
                persistence="injury_history",
                dedupe_key=identity,
                phase="post_game",
                source_ordinal=start_ordinal + offset,
            )
        )
    return out


def form_change_event(
    *,
    before: str,
    after: str,
    occurred_at: date,
    season: int,
    game_number: int,
    team_id: str | None,
    ordinal: int,
) -> CanonicalEventDTO | None:
    if before == after:
        return None
    identity = f"form:{season}:{game_number}:{before}>{after}"
    return CanonicalEventDTO(
        event_id=identity,
        event_type="form_changed",
        category="form",
        occurred_at=occurred_at.isoformat(),
        season=season,
        game_number=game_number,
        sequence=-1,
        title="컨디션 변화",
        summary=f"{before} → {after}",
        team_id=team_id,
        state_effects={"from": before, "to": after},
        presentation_priority=45,
        persistence="transient",
        dedupe_key=identity,
        phase="post_game",
        source_ordinal=ordinal,
    )
