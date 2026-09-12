"""Canonical progression-event DTO projection owned by 04 Events & Story.

This module consumes presentation-free CareerSourceFact values emitted by 03.
It never infers career transitions from snapshots, mutates simulation state,
appends durable history, or consumes simulation RNG.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date
from typing import Iterable, Mapping, Sequence

from .career_source_facts import CareerSourceFact


PHASE_ORDER = {
    "pre_game": 0,
    "in_game": 1,
    "post_game": 2,
    "off_day": 3,
    "lifecycle": 4,
    "system": 5,
}

CATEGORY_BY_FACT = {
    "roster_promotion": "roster",
    "roster_demotion": "roster",
    "first_team_debut": "roster",
    "injury_created": "injury",
    "injury_recovery_completed": "injury",
    "injury_cleared": "injury",
    "injury_changed": "injury",
    "form_transition": "form",
    "trait_gained": "trait",
    "trait_lost": "trait",
    "event_rating_change": "development",
    "season_growth": "development",
    "season_finalized": "lifecycle",
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
    importance: str
    player_id: str | None
    team_id: str | None
    related_entity_ids: tuple[str, ...]
    state_effects: Mapping[str, object] | None
    rating_changes: Mapping[str, int] | None
    injury_effect: Mapping[str, object] | None
    trait_changes: tuple[str, ...]
    source_command: str
    presentation_priority: int
    persistence: str
    dedupe_key: str
    phase: str
    source_ordinal: int

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
        }


def _coord_identity(fact: CareerSourceFact) -> str:
    date_part = fact.simulated_date.isoformat() if fact.simulated_date else "none"
    game_part = "none" if fact.game_number is None else str(fact.game_number)
    return f"{fact.season}:{game_part}:{date_part}:{fact.phase}:{fact.local_ordinal}:{fact.fact_type}"


def _identity(fact: CareerSourceFact) -> tuple[str, str]:
    if fact.existing_history_kind and fact.existing_dedupe_key:
        # One durable history row may emit several distinct transition facts
        # (for example injury + rating change from one v0.4 event resolution).
        # Keep the durable key as the identity basis while preserving each fact.
        event_id = f"{fact.existing_history_kind}:{fact.existing_dedupe_key}:{fact.fact_type}"
        return event_id, fact.existing_dedupe_key
    identity = _coord_identity(fact)
    return identity, identity


def _persistence(fact: CareerSourceFact) -> str:
    # 03 owns all existing durable histories. 04 never creates a second store.
    # Ordinary recovery completion currently has no durable recovery row, so it
    # intentionally remains mutation-response-only until 03 defines one.
    return fact.existing_history_kind or "transient"


def _injury(value: object) -> Mapping[str, object] | None:
    return value if isinstance(value, Mapping) else None


def _injury_summary(value: Mapping[str, object] | None) -> str:
    if not value:
        return "부상 정보 없음"
    name = str(value.get("name", "부상"))
    severity = str(value.get("severity", ""))
    remaining = value.get("games_remaining")
    parts = [name]
    if severity:
        parts.append(severity)
    if remaining is not None:
        parts.append(f"잔여 {remaining}경기")
    return " / ".join(parts)


def _rating_changes(fact: CareerSourceFact) -> dict[str, int] | None:
    raw = fact.state_delta.get("rating_deltas")
    if not isinstance(raw, Mapping):
        return None
    return {str(key): int(value) for key, value in raw.items() if int(value) != 0}


def _trait_changes(fact: CareerSourceFact) -> tuple[str, ...]:
    raw = fact.state_delta.get("trait")
    if not isinstance(raw, Mapping):
        return ()
    action = str(raw.get("action", "changed"))
    trait = str(raw.get("trait", ""))
    return (f"{action}:{trait}",) if trait else ()


def _presentation(fact: CareerSourceFact) -> tuple[str, str, str, int]:
    before, after = fact.before_state, fact.after_state
    if fact.fact_type == "roster_promotion":
        return "1군 등록", "선수의 로스터 상태가 비1군/개발군에서 1군으로 변경되었습니다.", "major", 90
    if fact.fact_type == "roster_demotion":
        return "1군 말소", "선수의 로스터 상태가 1군에서 비1군/개발군으로 변경되었습니다.", "normal", 75
    if fact.fact_type == "first_team_debut":
        return "1군 데뷔", "선수의 첫 1군 경기 출전이 확정되었습니다.", "major", 100
    if fact.fact_type == "injury_created":
        injury = _injury(after.get("injury"))
        severity = str(injury.get("severity", "")) if injury else ""
        importance = "major" if severity == "중상" else "normal"
        return "부상 발생", _injury_summary(injury), importance, 95 if importance == "major" else 80
    if fact.fact_type == "injury_recovery_completed":
        return "회복 완료", f"{_injury_summary(_injury(before.get('injury')))}에서 회복했습니다.", "normal", 85
    if fact.fact_type == "injury_cleared":
        return "부상 상태 해제", f"{_injury_summary(_injury(before.get('injury')))} 상태가 해제되었습니다.", "normal", 85
    if fact.fact_type == "injury_changed":
        return "부상 상태 변경", f"{_injury_summary(_injury(before.get('injury')))} → {_injury_summary(_injury(after.get('injury')))}", "normal", 85
    if fact.fact_type == "form_transition":
        return "컨디션 변화", f"{before.get('form', 'unknown')} → {after.get('form', 'unknown')}", "normal", 55
    if fact.fact_type == "trait_gained":
        trait = str(after.get("trait_present") or "trait")
        return "특성 획득", f"{trait} 특성을 획득했습니다.", "normal", 65
    if fact.fact_type == "trait_lost":
        trait = str(before.get("trait_present") or "trait")
        return "특성 상실", f"{trait} 특성이 제거되었습니다.", "normal", 65
    if fact.fact_type == "event_rating_change":
        changes = _rating_changes(fact) or {}
        text = ", ".join(f"{key} {value:+d}" for key, value in sorted(changes.items())) or "변화 없음"
        return "능력치 변화", text, "normal", 70
    if fact.fact_type == "season_growth":
        changes = _rating_changes(fact) or {}
        text = ", ".join(f"{key} {value:+d}" for key, value in sorted(changes.items())) or "능력치 변화 없음"
        return "시즌 성장 결과", text, "major", 88
    if fact.fact_type == "season_finalized":
        completed = before.get("season", fact.season)
        return "시즌 종료", f"{completed} 시즌 진행 결과가 최종 확정되었습니다.", "major", 92
    raise ValueError(f"unsupported CareerSourceFact type: {fact.fact_type}")


def canonical_event_from_source_fact(
    fact: CareerSourceFact,
    *,
    source_command: str,
) -> CanonicalEventDTO:
    if fact.fact_type not in CATEGORY_BY_FACT:
        raise ValueError(f"unsupported CareerSourceFact type: {fact.fact_type}")
    event_id, dedupe_key = _identity(fact)
    title, summary, importance, priority = _presentation(fact)
    before_injury = _injury(fact.before_state.get("injury"))
    after_injury = _injury(fact.after_state.get("injury"))
    injury_effect = None
    if fact.fact_type.startswith("injury_"):
        injury_effect = {"before": dict(before_injury) if before_injury else None, "after": dict(after_injury) if after_injury else None}
    return CanonicalEventDTO(
        event_id=event_id,
        event_type=fact.fact_type,
        category=CATEGORY_BY_FACT[fact.fact_type],
        occurred_at=fact.simulated_date.isoformat() if fact.simulated_date else None,
        season=fact.season,
        game_number=fact.game_number,
        sequence=-1,
        title=title,
        summary=summary,
        importance=importance,
        player_id=fact.player_id,
        team_id=fact.team_id,
        related_entity_ids=(),
        state_effects={"before": dict(fact.before_state), "after": dict(fact.after_state), "delta": dict(fact.state_delta)},
        rating_changes=_rating_changes(fact),
        injury_effect=injury_effect,
        trait_changes=_trait_changes(fact),
        source_command=source_command,
        presentation_priority=priority,
        persistence=_persistence(fact),
        dedupe_key=dedupe_key,
        phase=fact.phase,
        source_ordinal=fact.local_ordinal,
    )


def gameplay_notable_event(
    *,
    occurred_at: date | None,
    season: int | None,
    ordinal: int,
    kind: str,
    message: str,
    source_command: str,
    game_number: int | None = None,
) -> CanonicalEventDTO:
    date_part = occurred_at.isoformat() if occurred_at else "none"
    game_part = "none" if game_number is None else str(game_number)
    event_id = f"gameplay:{season}:{game_part}:{date_part}:in_game:{ordinal}:{kind}"
    return CanonicalEventDTO(
        event_id=event_id,
        event_type="gameplay_notable",
        category="gameplay",
        occurred_at=occurred_at.isoformat() if occurred_at else None,
        season=season,
        game_number=game_number,
        sequence=-1,
        title="경기 주요 장면",
        summary=message,
        importance="normal",
        player_id=None,
        team_id=None,
        related_entity_ids=(),
        state_effects=None,
        rating_changes=None,
        injury_effect=None,
        trait_changes=(),
        source_command=source_command,
        presentation_priority=40,
        persistence="transient",
        dedupe_key=event_id,
        phase="in_game",
        source_ordinal=ordinal,
    )


def finalize_timeline(events: Iterable[CanonicalEventDTO]) -> tuple[CanonicalEventDTO, ...]:
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
    result: list[CanonicalEventDTO] = []
    for event in ordered:
        # Fact type participates in persistent dedupe because one durable
        # event_history row may authoritatively emit multiple fact types.
        key = f"{event.event_type}|{event.dedupe_key}"
        if key in seen:
            continue
        seen.add(key)
        result.append(event)
    return tuple(replace(event, sequence=index) for index, event in enumerate(result))


def canonical_timeline_from_source_facts(
    facts: Sequence[CareerSourceFact],
    *,
    source_command: str,
) -> tuple[CanonicalEventDTO, ...]:
    return finalize_timeline(
        canonical_event_from_source_fact(fact, source_command=source_command)
        for fact in facts
    )


def canonical_timeline_for_advance(
    *,
    source_facts: Sequence[CareerSourceFact],
    gameplay_events: Sequence[object],
    source_command: str,
    season: int | None,
) -> tuple[CanonicalEventDTO, ...]:
    # 03 may add new authoritative fact types before 04 has presentation rules
    # for them. Keep those facts losslessly in AdvanceSummary.source_facts while
    # projecting only currently supported types into the legacy DTO timeline.
    events = [
        canonical_event_from_source_fact(fact, source_command=source_command)
        for fact in source_facts
        if fact.fact_type in CATEGORY_BY_FACT
    ]
    facts_by_date: dict[str, list[CareerSourceFact]] = {}
    for fact in source_facts:
        if fact.simulated_date:
            facts_by_date.setdefault(fact.simulated_date.isoformat(), []).append(fact)
    for ordinal, raw in enumerate(gameplay_events):
        game_date = getattr(raw, "game_date", None)
        kind = str(getattr(raw, "kind", "game"))
        message = str(getattr(raw, "message", ""))
        game_number = None
        if isinstance(game_date, date):
            same_date = facts_by_date.get(game_date.isoformat(), [])
            game_numbers = [fact.game_number for fact in same_date if fact.game_number is not None]
            if game_numbers:
                game_number = min(game_numbers)
        events.append(
            gameplay_notable_event(
                occurred_at=game_date if isinstance(game_date, date) else None,
                season=season,
                ordinal=ordinal,
                kind=kind,
                message=message,
                source_command=source_command,
                game_number=game_number,
            )
        )
    return finalize_timeline(events)
