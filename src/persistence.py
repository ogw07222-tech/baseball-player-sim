"""JSON save/load with backward-compatible versioning and RNG-state preservation."""
from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from . import config
from .career import CareerEngine
from .pitcher_usage import PitcherUsageLeagueState
from .player import Player
from .rng import RNG
from .time_advance import AdvancePipelineState


def _jsonable_state(value: object) -> object:
    if isinstance(value, tuple):
        return [_jsonable_state(v) for v in value]
    if isinstance(value, list):
        return [_jsonable_state(v) for v in value]
    return value


def _tuple_state(value: object) -> object:
    if isinstance(value, list):
        return tuple(_tuple_state(v) for v in value)
    return value


def serialize_game(engine: CareerEngine) -> dict[str, object]:
    """Return the canonical durable save payload without choosing a storage medium."""
    payload: dict[str, object] = {
        "save_version": config.SAVE_VERSION,
        "player": engine.player.as_dict(),
        "career": engine.as_dict(),
        "rng": {"seed": engine.rng.seed, "state": _jsonable_state(engine.rng.get_state())},
    }
    advance_state = getattr(engine, "advance_state", None)
    if isinstance(advance_state, AdvancePipelineState):
        payload["advance_state"] = advance_state.as_dict()
    pitcher_usage_state = getattr(engine, "pitcher_usage_state", None)
    if isinstance(pitcher_usage_state, PitcherUsageLeagueState):
        payload["pitcher_usage_state"] = pitcher_usage_state.as_dict()
    return payload


def deserialize_game(payload: Mapping[str, Any]) -> CareerEngine:
    """Restore a CareerEngine from the canonical save payload."""
    data = dict(payload)
    version = int(data.get("save_version", 1))
    if version not in config.SUPPORTED_SAVE_VERSIONS:
        raise ValueError(f"unsupported save version: {version}")
    player = Player.from_dict(dict(data["player"]))
    rng_data = dict(data["rng"])
    rng = RNG(rng_data.get("seed"))
    rng.set_state(_tuple_state(rng_data["state"]))  # type: ignore[arg-type]
    career_data = dict(data["career"])
    engine = CareerEngine(
        player=player,
        rng=rng,
        year=int(career_data.get("year", config.START_YEAR)),
    )
    engine.restore_state(career_data)
    if data.get("advance_state") is not None:
        # Import lazily to avoid making persistence a module-import dependency of
        # the production advance layer. Older payloads with no team_record are
        # upgraded with team_record_supported=False rather than fabricating W/L.
        from .production_advance import ProductionAdvancePipelineState

        engine.advance_state = ProductionAdvancePipelineState.from_dict(
            dict(data["advance_state"])
        )
    if data.get("pitcher_usage_state") is not None:
        engine.pitcher_usage_state = PitcherUsageLeagueState.from_dict(
            dict(data["pitcher_usage_state"])
        )
    return engine


def save_game(path: str | Path, engine: CareerEngine) -> Path:
    target = Path(path)
    target.write_text(
        json.dumps(serialize_game(engine), ensure_ascii=False, indent=2, allow_nan=False),
        encoding="utf-8",
    )
    return target


def load_game(path: str | Path) -> CareerEngine:
    data: dict[str, Any] = json.loads(Path(path).read_text(encoding="utf-8"))
    return deserialize_game(data)
