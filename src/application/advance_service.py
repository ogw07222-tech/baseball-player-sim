"""Command boundary for time advancement.

The service does not implement simulation. Callers inject the existing domain/career
commands, so web clients cannot reach probability functions directly.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")


class AdvanceService:
    def __init__(
        self,
        *,
        next_game: Callable[[], T],
        week: Callable[[], T],
        month: Callable[[], T],
        season: Callable[[], T],
    ) -> None:
        self._commands = {
            "next_game": next_game,
            "week": week,
            "month": month,
            "season": season,
        }

    def advance(self, command: str) -> T:
        try:
            callback = self._commands[command]
        except KeyError as exc:
            raise ValueError(f"unsupported advance command: {command}") from exc
        return callback()
