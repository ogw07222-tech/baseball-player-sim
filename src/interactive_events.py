"""04 Events & Story: interactive decision EVENT domain (P1).

Terminology is deliberate:
- InteractiveEvent = a player-facing decision EVENT with choices.
- CareerSourceFact / CanonicalEventDTO = automatic CAREER timeline truth.

This module never mutates Player/Career simulation state. It may inspect current
state for eligibility, creates deterministic pending events, and resolves a
choice into declarative EventChoiceEffect requests for 03 to apply later.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import date
import hashlib
from typing import Mapping, Sequence


EVENT_STATUS_PENDING = "pending"
EVENT_STATUS_RESOLVED = "resolved"
EVENT_STATUS_EXPIRED = "expired"
EVENT_STATUSES = (EVENT_STATUS_PENDING, EVENT_STATUS_RESOLVED, EVENT_STATUS_EXPIRED)

DEFAULT_SEASON_EVENT_CAP = 6
DEFAULT_MAX_PENDING_EVENTS = 3
DEFAULT_CATEGORY_COOLDOWN_GAMES = 18
DEFAULT_EVENT_COOLDOWN_GAMES = 32
DEFAULT_OPPORTUNITY_PER_GAME = 0.04


@dataclass(frozen=True)
class EventChoiceEffect:
    """Declarative effect request owned by 04; 03 owns real state mutation."""

    effect_type: str
    target: str
    magnitude: str
    duration: int | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def as_dict(self) -> dict[str, object]:
        return {
            "effect_type": self.effect_type,
            "target": self.target,
            "magnitude": self.magnitude,
            "duration": self.duration,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> "EventChoiceEffect":
        return cls(
            effect_type=str(data["effect_type"]),
            target=str(data["target"]),
            magnitude=str(data["magnitude"]),
            duration=int(data["duration"]) if data.get("duration") is not None else None,
            metadata=dict(data.get("metadata", {})),
        )


@dataclass(frozen=True)
class InteractiveEventChoice:
    choice_id: str
    label: str
    description: str
    preview_effects: tuple[EventChoiceEffect, ...]
    risk_level: str | None = None
    requirements: Mapping[str, object] | None = None

    def as_dict(self) -> dict[str, object]:
        return {
            "choice_id": self.choice_id,
            "label": self.label,
            "description": self.description,
            "preview_effects": [effect.as_dict() for effect in self.preview_effects],
            "risk_level": self.risk_level,
            "requirements": dict(self.requirements) if self.requirements is not None else None,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> "InteractiveEventChoice":
        return cls(
            choice_id=str(data["choice_id"]),
            label=str(data["label"]),
            description=str(data["description"]),
            preview_effects=tuple(EventChoiceEffect.from_dict(dict(v)) for v in data.get("preview_effects", [])),
            risk_level=str(data["risk_level"]) if data.get("risk_level") is not None else None,
            requirements=dict(data["requirements"]) if data.get("requirements") is not None else None,
        )


@dataclass(frozen=True)
class InteractiveEvent:
    event_id: str
    event_type: str
    category: str
    title: str
    description: str
    occurred_at: str | None
    generated_at: str | None
    season: int
    game_number: int
    importance: str
    trigger_context: Mapping[str, object]
    choices: tuple[InteractiveEventChoice, ...]
    status: str = EVENT_STATUS_PENDING
    expires_at: str | None = None
    source: str = "04-interactive-event-p1"
    dedupe_key: str = ""
    blocking: bool = False
    selected_choice_id: str | None = None
    resolved_at: str | None = None
    resolution_summary: str | None = None

    def as_dict(self) -> dict[str, object]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "category": self.category,
            "title": self.title,
            "description": self.description,
            "occurred_at": self.occurred_at,
            "generated_at": self.generated_at,
            "season": self.season,
            "game_number": self.game_number,
            "importance": self.importance,
            "trigger_context": dict(self.trigger_context),
            "choices": [choice.as_dict() for choice in self.choices],
            "status": self.status,
            "expires_at": self.expires_at,
            "source": self.source,
            "dedupe_key": self.dedupe_key,
            "blocking": self.blocking,
            "selected_choice_id": self.selected_choice_id,
            "resolved_at": self.resolved_at,
            "resolution_summary": self.resolution_summary,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> "InteractiveEvent":
        return cls(
            event_id=str(data["event_id"]),
            event_type=str(data["event_type"]),
            category=str(data["category"]),
            title=str(data["title"]),
            description=str(data["description"]),
            occurred_at=str(data["occurred_at"]) if data.get("occurred_at") is not None else None,
            generated_at=str(data["generated_at"]) if data.get("generated_at") is not None else None,
            season=int(data["season"]),
            game_number=int(data["game_number"]),
            importance=str(data.get("importance", "normal")),
            trigger_context=dict(data.get("trigger_context", {})),
            choices=tuple(InteractiveEventChoice.from_dict(dict(v)) for v in data.get("choices", [])),
            status=str(data.get("status", EVENT_STATUS_PENDING)),
            expires_at=str(data["expires_at"]) if data.get("expires_at") is not None else None,
            source=str(data.get("source", "04-interactive-event-p1")),
            dedupe_key=str(data.get("dedupe_key", data["event_id"])),
            blocking=bool(data.get("blocking", False)),
            selected_choice_id=str(data["selected_choice_id"]) if data.get("selected_choice_id") is not None else None,
            resolved_at=str(data["resolved_at"]) if data.get("resolved_at") is not None else None,
            resolution_summary=str(data["resolution_summary"]) if data.get("resolution_summary") is not None else None,
        )


@dataclass(frozen=True)
class InteractiveEventResolution:
    event_id: str
    selected_choice_id: str
    effects: tuple[EventChoiceEffect, ...]
    resolved_at: str | None
    resolution_summary: str

    def as_dict(self) -> dict[str, object]:
        return {
            "event_id": self.event_id,
            "selected_choice_id": self.selected_choice_id,
            "effects": [effect.as_dict() for effect in self.effects],
            "resolved_at": self.resolved_at,
            "resolution_summary": self.resolution_summary,
        }


@dataclass(frozen=True)
class InteractiveEventArchetype:
    event_type: str
    category: str
    title: str
    description: str
    choices: tuple[InteractiveEventChoice, ...]
    importance: str = "normal"
    weight: float = 1.0
    min_game: int = 1
    max_game: int = 144
    levels: tuple[str, ...] = ("FIRST", "FARM")
    required_forms: tuple[str, ...] = ()
    min_fatigue: float | None = None
    max_fatigue: float | None = None
    positions: tuple[str, ...] = ()
    once_per_season: bool = False
    once_per_career: bool = False
    cooldown_games: int = DEFAULT_EVENT_COOLDOWN_GAMES
    category_cooldown_games: int = DEFAULT_CATEGORY_COOLDOWN_GAMES
    season_cap: int = 2
    blocking: bool = False


@dataclass
class InteractiveEventState:
    events: list[InteractiveEvent] = field(default_factory=list)
    event_cooldown_until: dict[str, int] = field(default_factory=dict)
    category_cooldown_until: dict[str, int] = field(default_factory=dict)
    season_counts: dict[str, int] = field(default_factory=dict)

    @property
    def pending(self) -> tuple[InteractiveEvent, ...]:
        return tuple(event for event in self.events if event.status == EVENT_STATUS_PENDING)

    def as_dict(self) -> dict[str, object]:
        return {
            "events": [event.as_dict() for event in self.events],
            "event_cooldown_until": dict(self.event_cooldown_until),
            "category_cooldown_until": dict(self.category_cooldown_until),
            "season_counts": dict(self.season_counts),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> "InteractiveEventState":
        return cls(
            events=[InteractiveEvent.from_dict(dict(v)) for v in data.get("events", [])],
            event_cooldown_until={str(k): int(v) for k, v in dict(data.get("event_cooldown_until", {})).items()},
            category_cooldown_until={str(k): int(v) for k, v in dict(data.get("category_cooldown_until", {})).items()},
            season_counts={str(k): int(v) for k, v in dict(data.get("season_counts", {})).items()},
        )

    def resolve(self, event_id: str, choice_id: str, resolved_at: date | None) -> InteractiveEventResolution:
        index = next((i for i, event in enumerate(self.events) if event.event_id == event_id), None)
        if index is None:
            raise KeyError(f"unknown interactive event: {event_id}")
        event = self.events[index]
        if event.status != EVENT_STATUS_PENDING:
            raise RuntimeError(f"interactive event is not pending: {event_id}")
        choice = next((choice for choice in event.choices if choice.choice_id == choice_id), None)
        if choice is None:
            raise ValueError(f"invalid choice for {event_id}: {choice_id}")
        summary = f"{event.title}: {choice.label} 선택"
        resolved_text = resolved_at.isoformat() if resolved_at is not None else None
        self.events[index] = replace(
            event,
            status=EVENT_STATUS_RESOLVED,
            selected_choice_id=choice.choice_id,
            resolved_at=resolved_text,
            resolution_summary=summary,
        )
        return InteractiveEventResolution(event.event_id, choice.choice_id, choice.preview_effects, resolved_text, summary)


def E(effect_type: str, target: str, magnitude: str, duration: int | None = None, **metadata: object) -> EventChoiceEffect:
    return EventChoiceEffect(effect_type, target, magnitude, duration, metadata)


def C(choice_id: str, label: str, description: str, *effects: EventChoiceEffect, risk: str | None = None) -> InteractiveEventChoice:
    return InteractiveEventChoice(choice_id, label, description, tuple(effects), risk)


EVENT_CATALOG: tuple[InteractiveEventArchetype, ...] = (
    InteractiveEventArchetype(
        "batting_training_intensity", "training", "타격 훈련 강도 조정", "다음 훈련 블록의 강도를 선택합니다.",
        (
            C("push", "강도를 높인다", "성장 기회를 늘리되 피로 부담을 감수합니다.", E("training_focus", "hitting", "high", 14), E("fatigue_modifier", "player", "cost_medium", 7), risk="medium"),
            C("balanced", "균형을 유지한다", "성장과 회복을 균형 있게 가져갑니다.", E("training_focus", "hitting", "balanced", 14), risk="low"),
            C("ease", "강도를 낮춘다", "성장 기회를 일부 포기하고 회복에 집중합니다.", E("training_focus", "hitting", "low", 14), E("fatigue_modifier", "player", "recovery_small", 7), risk="low"),
        ),
        weight=1.15,
    ),
    InteractiveEventArchetype(
        "defense_training_focus", "training", "수비 훈련 집중", "수비 훈련 비중을 조정할 기회가 생겼습니다.",
        (
            C("range", "범위 훈련", "수비 범위 중심 훈련을 요청합니다.", E("training_focus", "defense_range", "high", 14), E("development_modifier", "hitting", "opportunity_cost_small", 14), risk="medium"),
            C("throwing", "송구 훈련", "송구와 정확성 중심 훈련을 요청합니다.", E("training_focus", "throwing", "high", 14), E("development_modifier", "hitting", "opportunity_cost_small", 14), risk="medium"),
            C("balanced", "균형 훈련", "기존 훈련 비율을 유지합니다.", E("training_focus", "defense", "balanced", 14), risk="low"),
        ),
        weight=.85,
    ),
    InteractiveEventArchetype(
        "weakness_focus", "training", "약점 보완 훈련", "현재 약점을 집중적으로 보완할지 선택합니다.",
        (
            C("target", "약점을 집중 보완", "한 영역에 훈련 자원을 집중합니다.", E("development_modifier", "weakest_rating", "upside_medium", 21), E("fatigue_modifier", "player", "cost_small", 7), risk="medium"),
            C("strength", "강점을 더 강화", "이미 좋은 영역의 강점을 극대화합니다.", E("development_modifier", "strongest_rating", "upside_medium", 21), E("development_modifier", "weakest_rating", "opportunity_cost_small", 21), risk="medium"),
            C("general", "전체 균형 유지", "특정 능력에 치우치지 않습니다.", E("development_modifier", "all", "small", 21), risk="low"),
        ),
        weight=.75,
    ),
    InteractiveEventArchetype(
        "slump_response", "form", "최근 부진 대응", "부진한 흐름에 대응할 방식을 선택합니다.",
        (
            C("simplify", "루틴을 단순화", "변화를 줄이고 안정성을 우선합니다.", E("form_modifier", "player", "stability_up", 10), E("development_modifier", "player", "opportunity_cost_small", 10), risk="low"),
            C("adjust", "기술 조정을 시도", "회복 가능성과 추가 흔들림을 함께 감수합니다.", E("form_modifier", "player", "variance_medium", 10), E("development_modifier", "hitting", "upside_medium", 10), risk="medium"),
            C("push", "그대로 밀어붙인다", "출전 감각을 유지하지만 피로 부담이 커질 수 있습니다.", E("form_modifier", "player", "breakthrough_chance", 7), E("fatigue_modifier", "player", "cost_medium", 7), risk="high"),
        ),
        required_forms=("slump",), weight=1.6, category_cooldown_games=12, cooldown_games=28,
    ),
    InteractiveEventArchetype(
        "hot_streak_routine", "form", "좋은 흐름 유지", "좋은 컨디션을 어떻게 관리할지 선택합니다.",
        (
            C("protect", "현재 루틴 유지", "변화를 최소화해 안정성을 높입니다.", E("form_modifier", "player", "stability_up", 10), risk="low"),
            C("capitalize", "훈련 강도를 높인다", "상승세를 성장 기회로 연결하되 피로를 감수합니다.", E("development_modifier", "player", "upside_medium", 10), E("fatigue_modifier", "player", "cost_medium", 7), risk="medium"),
            C("recover", "회복 시간을 확보", "현재 흐름보다 장기 컨디션을 우선합니다.", E("fatigue_modifier", "player", "recovery_medium", 7), E("form_modifier", "player", "momentum_decay_small", 7), risk="low"),
        ),
        required_forms=("hot",), weight=1.25, category_cooldown_games=12,
    ),
    InteractiveEventArchetype(
        "coach_method_trial", "coach", "코치의 새 훈련 방식", "코치가 새로운 훈련 방식을 시험해 보자고 제안했습니다.",
        (
            C("accept", "제안을 따른다", "코치 방식에 맞춘 단기 훈련을 요청합니다.", E("training_focus", "coach_recommendation", "high", 14), E("development_modifier", "player", "variance_medium", 14), risk="medium"),
            C("partial", "일부만 적용", "현재 루틴과 코치 제안을 절충합니다.", E("training_focus", "coach_recommendation", "partial", 14), risk="low"),
            C("decline", "현재 방식을 유지", "변화를 최소화합니다.", E("training_focus", "player_routine", "maintain", 14), risk="low"),
        ),
        weight=.85, season_cap=1, once_per_season=True,
    ),
    InteractiveEventArchetype(
        "role_competition", "team_role", "주전 경쟁 대응", "팀 내 역할 경쟁이 이어지는 상황에서 대응 방식을 선택합니다.",
        (
            C("compete", "훈련과 출전 준비 강화", "주전 경쟁에 더 많은 자원을 투입합니다.", E("development_modifier", "role_readiness", "upside_medium", 14), E("fatigue_modifier", "player", "cost_small", 7), risk="medium"),
            C("steady", "현재 역할에 집중", "현재 역할 수행의 안정성을 우선합니다.", E("form_modifier", "role_execution", "stability_up", 14), risk="low"),
            C("versatile", "다양한 역할을 준비", "여러 역할 적응을 요청하지만 전문화 기회는 줄어듭니다.", E("training_focus", "versatility", "medium", 21), E("development_modifier", "primary_role", "opportunity_cost_small", 21), risk="medium"),
        ),
        weight=.8,
    ),
    InteractiveEventArchetype(
        "position_practice", "team_role", "새 포지션 연습 제안", "팀에서 보조 포지션 훈련을 제안했습니다.",
        (
            C("accept", "보조 포지션을 연습", "활용 폭을 넓히는 훈련을 요청합니다.", E("training_focus", "secondary_position", "medium", 28), E("development_modifier", "primary_position", "opportunity_cost_small", 28), risk="medium"),
            C("limited", "기초 훈련만 진행", "적응 가능성만 열어 두고 주 포지션을 유지합니다.", E("training_focus", "secondary_position", "low", 28), risk="low"),
            C("decline", "주 포지션에 집중", "현재 포지션 전문화를 유지합니다.", E("training_focus", "primary_position", "high", 28), risk="low"),
        ),
        weight=.55, season_cap=1, once_per_season=True,
    ),
    InteractiveEventArchetype(
        "media_interview", "media", "경기 후 인터뷰", "최근 팀 내 관심이 높아져 인터뷰 요청이 들어왔습니다.",
        (
            C("team", "팀을 강조한다", "개인보다 팀과 과정에 초점을 둡니다.", E("temporary_trait_request", "public_stance", "team_first", 14), risk="low"),
            C("confident", "자신감을 보인다", "높아진 기대를 받아들이는 태도를 보입니다.", E("temporary_trait_request", "public_stance", "confident", 14), E("form_modifier", "pressure", "variance_small", 7), risk="medium"),
            C("brief", "짧게 답한다", "추가 노출을 최소화합니다.", E("temporary_trait_request", "public_stance", "reserved", 14), risk="low"),
        ),
        weight=.55, season_cap=1,
    ),
    InteractiveEventArchetype(
        "fatigue_management", "recovery", "훈련 강도 조정", "누적 피로를 고려해 다음 훈련 주기를 조정할 수 있습니다.",
        (
            C("rest", "회복 우선", "훈련 기회를 줄이고 회복을 요청합니다.", E("fatigue_modifier", "player", "recovery_large", 5), E("development_modifier", "player", "opportunity_cost_medium", 7), risk="low"),
            C("normal", "정상 훈련", "기본 훈련과 회복 균형을 유지합니다.", E("training_focus", "player", "balanced", 7), risk="low"),
            C("push", "훈련을 이어간다", "성장 기회를 유지하지만 피로 부담을 감수합니다.", E("development_modifier", "player", "upside_small", 7), E("fatigue_modifier", "player", "cost_medium", 7), risk="medium"),
        ),
        min_fatigue=45.0, weight=1.35, category_cooldown_games=10, cooldown_games=20,
    ),
)
EVENT_BY_TYPE = {event.event_type: event for event in EVENT_CATALOG}


def _digest_int(*parts: object) -> int:
    raw = "|".join(str(part) for part in parts).encode("utf-8")
    return int.from_bytes(hashlib.sha256(raw).digest()[:8], "big", signed=False)


def deterministic_roll(seed: object, season: int, game_number: int, namespace: str) -> float:
    return _digest_int(seed, season, game_number, namespace) / float(2**64)


def event_state_for_engine(engine: object) -> InteractiveEventState:
    state = getattr(engine, "interactive_event_state", None)
    if isinstance(state, InteractiveEventState):
        return state
    state = InteractiveEventState()
    setattr(engine, "interactive_event_state", state)
    return state


def _career_has_event(state: InteractiveEventState, event_type: str) -> bool:
    return any(event.event_type == event_type for event in state.events)


def _eligible(archetype: InteractiveEventArchetype, *, player: object, state: InteractiveEventState, season: int, game_number: int, level: str) -> bool:
    if not archetype.min_game <= game_number <= archetype.max_game:
        return False
    if level not in archetype.levels:
        return False
    if game_number < state.event_cooldown_until.get(archetype.event_type, 0):
        return False
    if game_number < state.category_cooldown_until.get(archetype.category, 0):
        return False
    if state.season_counts.get(archetype.event_type, 0) >= archetype.season_cap:
        return False
    if archetype.once_per_season and state.season_counts.get(archetype.event_type, 0) > 0:
        return False
    if archetype.once_per_career and _career_has_event(state, archetype.event_type):
        return False
    form = str(getattr(player, "form", "normal"))
    if archetype.required_forms and form not in archetype.required_forms:
        return False
    fatigue = float(getattr(player, "fatigue", 0.0))
    if archetype.min_fatigue is not None and fatigue < archetype.min_fatigue:
        return False
    if archetype.max_fatigue is not None and fatigue > archetype.max_fatigue:
        return False
    position = str(getattr(player, "position", ""))
    if archetype.positions and position not in archetype.positions:
        return False
    dedupe_key = f"interactive:{season}:{game_number}:{archetype.event_type}"
    if any(event.dedupe_key == dedupe_key for event in state.events):
        return False
    return True


def eligible_event_types(*, player: object, state: InteractiveEventState, season: int, game_number: int, level: str) -> tuple[str, ...]:
    return tuple(
        archetype.event_type
        for archetype in EVENT_CATALOG
        if _eligible(archetype, player=player, state=state, season=season, game_number=game_number, level=level)
    )


def maybe_generate_interactive_event(
    *,
    player: object,
    state: InteractiveEventState,
    seed: object,
    season: int,
    game_number: int,
    simulated_date: date | None,
    level: str,
    opportunity_per_game: float = DEFAULT_OPPORTUNITY_PER_GAME,
    season_event_cap: int = DEFAULT_SEASON_EVENT_CAP,
    max_pending_events: int = DEFAULT_MAX_PENDING_EVENTS,
) -> InteractiveEvent | None:
    """Generate at most one non-blocking event at this exact game coordinate.

    The deterministic child stream is hash-derived and never advances the
    canonical simulation RNG. week/month callers should invoke this after each
    constituent game, preserving the real occurrence coordinate.
    """
    if len(state.pending) >= max_pending_events:
        return None
    current_season_total = sum(1 for event in state.events if event.season == season)
    if current_season_total >= season_event_cap:
        return None
    if deterministic_roll(seed, season, game_number, "interactive-event-opportunity") >= opportunity_per_game:
        return None
    candidates = [
        archetype for archetype in EVENT_CATALOG
        if _eligible(archetype, player=player, state=state, season=season, game_number=game_number, level=level)
    ]
    if not candidates:
        return None
    weighted: list[tuple[float, InteractiveEventArchetype]] = []
    for archetype in candidates:
        roll = max(1e-12, deterministic_roll(seed, season, game_number, f"interactive-event-select:{archetype.event_type}"))
        weighted.append((roll ** (1.0 / max(.05, archetype.weight)), archetype))
    archetype = min(weighted, key=lambda item: (item[0], item[1].event_type))[1]
    date_text = simulated_date.isoformat() if simulated_date is not None else None
    event_id = f"interactive:{season}:{game_number}:{archetype.event_type}"
    trigger_context = {
        "level": level,
        "form": str(getattr(player, "form", "normal")),
        "fatigue_band": "high" if float(getattr(player, "fatigue", 0.0)) >= 65 else "elevated" if float(getattr(player, "fatigue", 0.0)) >= 45 else "normal",
    }
    event = InteractiveEvent(
        event_id=event_id,
        event_type=archetype.event_type,
        category=archetype.category,
        title=archetype.title,
        description=archetype.description,
        occurred_at=date_text,
        generated_at=date_text,
        season=season,
        game_number=game_number,
        importance=archetype.importance,
        trigger_context=trigger_context,
        choices=archetype.choices,
        source="04-interactive-event-p1",
        dedupe_key=event_id,
        blocking=archetype.blocking,
    )
    state.events.append(event)
    state.event_cooldown_until[archetype.event_type] = game_number + archetype.cooldown_games
    state.category_cooldown_until[archetype.category] = game_number + archetype.category_cooldown_games
    state.season_counts[archetype.event_type] = state.season_counts.get(archetype.event_type, 0) + 1
    return event


def resolve_interactive_event(
    *, state: InteractiveEventState, event_id: str, choice_id: str, resolved_at: date | None
) -> InteractiveEventResolution:
    """Resolve EVENT record only; returns declarative requests and mutates no Player state."""
    return state.resolve(event_id, choice_id, resolved_at)
