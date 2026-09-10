"""Deterministic observational career-history contracts.

This module mirrors authoritative career state owned by the career/growth layer.
It never mutates ratings, gameplay probabilities, growth, fatigue, injury, form,
or Traits, and it never consumes simulation RNG.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Mapping

if TYPE_CHECKING:
    from .player import Player


CAREER_HISTORY_SCHEMA_VERSION = 1
CAREER_ONCE = "career_once"
TRANSITION_REPEAT = "transition_repeat"


@dataclass(frozen=True)
class CareerNews:
    template_key: str
    headline: str
    body: str

    def as_dict(self) -> dict[str, str]:
        return {
            "template_key": self.template_key,
            "headline": self.headline,
            "body": self.body,
        }


@dataclass(frozen=True)
class CareerHistoryEntry:
    event_id: str
    year: int
    age: int
    career_stage: str
    kind: str
    importance: str
    dedupe_key: str
    trigger: str
    eligibility: str
    repeat_contract: str
    team: str | None = None
    game_number: int | None = None
    facts: Mapping[str, object] = field(default_factory=dict)
    news: CareerNews | None = None

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": CAREER_HISTORY_SCHEMA_VERSION,
            "event_id": self.event_id,
            "event_type": "system_mirror",
            "year": self.year,
            "age": self.age,
            "career_stage": self.career_stage,
            "kind": self.kind,
            "importance": self.importance,
            "dedupe_key": self.dedupe_key,
            "trigger": self.trigger,
            "eligibility": self.eligibility,
            "repeat_contract": self.repeat_contract,
            "team": self.team,
            "game_number": self.game_number,
            "facts": dict(self.facts),
            "news": self.news.as_dict() if self.news else None,
            "effects": [],
            "source_owner": "03-growth-career",
            "observer_owner": "04-events-story",
        }


def render_career_news(
    event_id: str,
    player_name: str,
    facts: Mapping[str, object],
) -> CareerNews:
    """Render factual template news without randomness or simulation mutation."""
    team = str(facts.get("team", "소속팀"))
    if event_id == "draft_selected":
        round_no = facts.get("round")
        pick = facts.get("pick")
        pick_text = f", 전체 {pick}순위" if pick is not None else ""
        return CareerNews(
            "career.draft_selected.v1",
            f"{player_name}, {team} {round_no}라운드 지명",
            f"{team}이 드래프트 {round_no}라운드{pick_text}로 {player_name}을 지명했다.",
        )
    if event_id == "draft_undrafted_entry":
        return CareerNews(
            "career.draft_undrafted_entry.v1",
            f"{player_name}, {team} 육성선수로 프로 도전",
            f"{player_name}이 미지명 후 {team} 육성선수로 프로 커리어를 시작한다.",
        )
    if event_id == "pro_entry":
        return CareerNews(
            "career.pro_entry.v1",
            f"{player_name}, {team} 입단",
            f"{player_name}이 {team}에 합류해 프로 생활을 시작했다.",
        )
    if event_id == "first_team_callup":
        return CareerNews(
            "career.first_team_callup.v1",
            f"{player_name}, 1군 콜업",
            f"{team}이 {player_name}을 1군 엔트리로 불러올렸다.",
        )
    if event_id == "first_team_debut":
        return CareerNews(
            "career.first_team_debut.v1",
            f"{player_name}, KBO 1군 데뷔",
            f"{player_name}이 {team} 소속으로 KBO 1군 첫 경기에 출전했다.",
        )
    if event_id == "farm_demotion":
        return CareerNews(
            "career.farm_demotion.v1",
            f"{player_name}, 2군 이동",
            f"{team}이 {player_name}을 2군으로 이동시켰다.",
        )
    raise ValueError(f"unsupported observational career event: {event_id}")


def record_observational_event(
    player: "Player",
    *,
    event_id: str,
    year: int,
    career_stage: str,
    kind: str,
    importance: str,
    dedupe_key: str,
    trigger: str,
    eligibility: str,
    repeat_contract: str,
    game_number: int | None = None,
    facts: Mapping[str, object] | None = None,
) -> dict[str, object] | None:
    """Append an observational event once according to its deterministic contract."""
    if repeat_contract not in {CAREER_ONCE, TRANSITION_REPEAT}:
        raise ValueError(f"unknown repeat contract: {repeat_contract}")
    if repeat_contract == CAREER_ONCE and any(
        entry.get("event_id") == event_id for entry in player.career_history
    ):
        return None
    if any(entry.get("dedupe_key") == dedupe_key for entry in player.career_history):
        return None

    payload = dict(facts or {})
    if player.team and "team" not in payload:
        payload["team"] = player.team
    news = render_career_news(event_id, player.name, payload)
    entry = CareerHistoryEntry(
        event_id=event_id,
        year=year,
        age=player.age,
        career_stage=career_stage,
        kind=kind,
        importance=importance,
        dedupe_key=dedupe_key,
        trigger=trigger,
        eligibility=eligibility,
        repeat_contract=repeat_contract,
        team=player.team,
        game_number=game_number,
        facts=payload,
        news=news,
    ).as_dict()
    player.career_history.append(entry)
    return entry
