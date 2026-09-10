"""Exact counting-stat containers and aggregation adapters.

This module owns no gameplay probabilities. It consumes counting events emitted
by gameplay systems and recomputes every derived rate from cumulative totals.
"""
from __future__ import annotations

from dataclasses import dataclass, field, fields
from datetime import date
from typing import Iterable, Mapping, Sequence


def _non_negative_int(value: object, name: str) -> int:
    if isinstance(value, bool):
        raise TypeError(f"{name} must be int")
    out = int(value)
    if out < 0:
        raise ValueError(f"{name} must be non-negative")
    return out


@dataclass
class HitterCountingStats:
    G: int = 0
    PA: int = 0
    AB: int = 0
    R: int = 0
    H: int = 0
    singles: int = 0
    doubles: int = 0
    triples: int = 0
    HR: int = 0
    RBI: int = 0
    BB: int = 0
    HBP: int = 0
    SO: int = 0
    SB: int = 0
    CS: int = 0
    GDP: int = 0
    SF: int = 0

    def __post_init__(self) -> None:
        for f in fields(self):
            setattr(self, f.name, _non_negative_int(getattr(self, f.name), f.name))
        self.validate()

    def validate(self) -> None:
        if self.H != self.singles + self.doubles + self.triples + self.HR:
            raise ValueError("H must equal 1B + 2B + 3B + HR")
        if self.AB < self.H:
            raise ValueError("AB must be >= H")
        if self.PA < self.AB:
            raise ValueError("PA must be >= AB")

    def add(self, other: "HitterCountingStats") -> None:
        for f in fields(self):
            setattr(self, f.name, getattr(self, f.name) + getattr(other, f.name))
        self.validate()

    def copy(self) -> "HitterCountingStats":
        return HitterCountingStats.from_dict(self.as_dict())

    @property
    def AVG(self) -> float:
        return self.H / self.AB if self.AB else 0.0

    @property
    def OBP(self) -> float:
        denominator = self.AB + self.BB + self.HBP + self.SF
        return (self.H + self.BB + self.HBP) / denominator if denominator else 0.0

    @property
    def SLG(self) -> float:
        tb = self.singles + 2 * self.doubles + 3 * self.triples + 4 * self.HR
        return tb / self.AB if self.AB else 0.0

    @property
    def OPS(self) -> float:
        return self.OBP + self.SLG

    @property
    def ISO(self) -> float:
        return self.SLG - self.AVG

    @property
    def BABIP(self) -> float:
        denominator = self.AB - self.SO - self.HR + self.SF
        return (self.H - self.HR) / denominator if denominator > 0 else 0.0

    @property
    def BB_pct(self) -> float:
        return self.BB / self.PA if self.PA else 0.0

    @property
    def K_pct(self) -> float:
        return self.SO / self.PA if self.PA else 0.0

    @property
    def HR_pct(self) -> float:
        return self.HR / self.PA if self.PA else 0.0

    def as_dict(self, include_derived: bool = False) -> dict[str, int | float]:
        payload: dict[str, int | float] = {
            "G": self.G, "PA": self.PA, "AB": self.AB, "R": self.R,
            "H": self.H, "1B": self.singles, "2B": self.doubles,
            "3B": self.triples, "HR": self.HR, "RBI": self.RBI,
            "BB": self.BB, "HBP": self.HBP, "SO": self.SO,
            "SB": self.SB, "CS": self.CS, "GDP": self.GDP, "SF": self.SF,
        }
        if include_derived:
            payload.update(
                AVG=self.AVG, OBP=self.OBP, SLG=self.SLG, OPS=self.OPS,
                ISO=self.ISO, BABIP=self.BABIP, BB_pct=self.BB_pct,
                K_pct=self.K_pct, HR_pct=self.HR_pct,
            )
        return payload

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> "HitterCountingStats":
        h = int(data.get("H", 0)); doubles = int(data.get("2B", data.get("doubles", 0)))
        triples = int(data.get("3B", data.get("triples", 0))); hr = int(data.get("HR", 0))
        singles = int(data.get("1B", data.get("singles", max(0, h - doubles - triples - hr))))
        return cls(
            G=int(data.get("G", 0)), PA=int(data.get("PA", 0)), AB=int(data.get("AB", 0)),
            R=int(data.get("R", 0)), H=h, singles=singles, doubles=doubles, triples=triples,
            HR=hr, RBI=int(data.get("RBI", 0)), BB=int(data.get("BB", 0)),
            HBP=int(data.get("HBP", 0)), SO=int(data.get("SO", 0)), SB=int(data.get("SB", 0)),
            CS=int(data.get("CS", 0)), GDP=int(data.get("GDP", 0)), SF=int(data.get("SF", 0)),
        )


_PITCHER_SUPPORT_FIELDS = {
    "ER": "er_supported",
    "W": "w_supported",
    "L": "l_supported",
    "SV": "sv_supported",
    "HLD": "hld_supported",
}


@dataclass
class PitcherCountingStats:
    G: int = 0
    GS: int = 0
    BF: int = 0
    outs_pitched: int = 0
    H: int = 0
    R: int = 0
    ER: int = 0
    HR: int = 0
    BB: int = 0
    HBP: int = 0
    SO: int = 0
    W: int = 0
    L: int = 0
    SV: int = 0
    HLD: int = 0
    er_supported: bool = True
    w_supported: bool = True
    l_supported: bool = True
    sv_supported: bool = True
    hld_supported: bool = True

    def __post_init__(self) -> None:
        for f in fields(self):
            value = getattr(self, f.name)
            if f.name.endswith("_supported"):
                if not isinstance(value, bool):
                    raise TypeError(f"{f.name} must be bool")
                continue
            setattr(self, f.name, _non_negative_int(value, f.name))
        self.validate()

    def validate(self) -> None:
        if self.GS > self.G:
            raise ValueError("GS must be <= G")
        if self.HR > self.H:
            raise ValueError("HR must be <= H")

    def add(self, other: "PitcherCountingStats") -> None:
        for f in fields(self):
            if f.name.endswith("_supported"):
                setattr(self, f.name, bool(getattr(self, f.name) and getattr(other, f.name)))
            else:
                setattr(self, f.name, getattr(self, f.name) + getattr(other, f.name))
        self.validate()

    def copy(self) -> "PitcherCountingStats":
        return PitcherCountingStats.from_dict(self.as_dict())

    def with_unsupported(self, labels: Iterable[str]) -> "PitcherCountingStats":
        out = self.copy()
        for label in labels:
            support_name = _PITCHER_SUPPORT_FIELDS.get(str(label).upper())
            if support_name is not None:
                setattr(out, support_name, False)
        return out

    @property
    def IP(self) -> float:
        return self.outs_pitched / 3.0

    @property
    def IP_display(self) -> str:
        return f"{self.outs_pitched // 3}.{self.outs_pitched % 3}"

    @property
    def ERA(self) -> float | None:
        if not self.er_supported:
            return None
        return self.ER * 27.0 / self.outs_pitched if self.outs_pitched else 0.0

    @property
    def era_supported(self) -> bool:
        return self.er_supported

    @property
    def WHIP(self) -> float:
        return (self.H + self.BB) * 3.0 / self.outs_pitched if self.outs_pitched else 0.0

    @property
    def K_pct(self) -> float:
        return self.SO / self.BF if self.BF else 0.0

    @property
    def BB_pct(self) -> float:
        return self.BB / self.BF if self.BF else 0.0

    @property
    def HR_pct(self) -> float:
        return self.HR / self.BF if self.BF else 0.0

    @property
    def K_per_9(self) -> float:
        return self.SO * 27.0 / self.outs_pitched if self.outs_pitched else 0.0

    @property
    def BB_per_9(self) -> float:
        return self.BB * 27.0 / self.outs_pitched if self.outs_pitched else 0.0

    @property
    def HR_per_9(self) -> float:
        return self.HR * 27.0 / self.outs_pitched if self.outs_pitched else 0.0

    def as_dict(self, include_derived: bool = False) -> dict[str, object]:
        payload: dict[str, object] = {
            "G": self.G, "GS": self.GS, "BF": self.BF, "OUTS_PITCHED": self.outs_pitched,
            "H": self.H, "R": self.R, "ER": self.ER if self.er_supported else None,
            "HR": self.HR, "BB": self.BB, "HBP": self.HBP, "SO": self.SO,
            "W": self.W if self.w_supported else None,
            "L": self.L if self.l_supported else None,
            "SV": self.SV if self.sv_supported else None,
            "HLD": self.HLD if self.hld_supported else None,
            "ER_SUPPORTED": self.er_supported,
            "ERA_SUPPORTED": self.er_supported,
            "W_SUPPORTED": self.w_supported,
            "L_SUPPORTED": self.l_supported,
            "SV_SUPPORTED": self.sv_supported,
            "HLD_SUPPORTED": self.hld_supported,
        }
        if include_derived:
            payload.update(
                IP=self.IP, IP_display=self.IP_display, ERA=self.ERA, WHIP=self.WHIP,
                K_pct=self.K_pct, BB_pct=self.BB_pct, HR_pct=self.HR_pct,
                K_per_9=self.K_per_9, BB_per_9=self.BB_per_9, HR_per_9=self.HR_per_9,
            )
        return payload

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> "PitcherCountingStats":
        def count(key: str, *fallbacks: str) -> int:
            value: object | None = data.get(key)
            for fallback in fallbacks:
                if value is None:
                    value = data.get(fallback)
            return 0 if value is None else int(value)

        def support(key: str) -> bool:
            value = data.get(f"{key}_SUPPORTED")
            if value is None and key == "ER":
                value = data.get("ERA_SUPPORTED")
            # Legacy payloads had no provenance metadata. Conservatively keep
            # the count internally but do not claim exact official support.
            return bool(value) if value is not None else False

        return cls(
            G=count("G"), GS=count("GS"), BF=count("BF"),
            outs_pitched=count("OUTS_PITCHED", "outs_pitched", "outs"),
            H=count("H"), R=count("R"), ER=count("ER"), HR=count("HR"),
            BB=count("BB"), HBP=count("HBP"), SO=count("SO"), W=count("W"),
            L=count("L"), SV=count("SV"), HLD=count("HLD"),
            er_supported=support("ER"), w_supported=support("W"),
            l_supported=support("L"), sv_supported=support("SV"),
            hld_supported=support("HLD"),
        )


@dataclass
class GameStatLine:
    hitter: HitterCountingStats = field(default_factory=HitterCountingStats)
    pitcher: PitcherCountingStats = field(default_factory=PitcherCountingStats)

    def add(self, other: "GameStatLine") -> None:
        self.hitter.add(other.hitter); self.pitcher.add(other.pitcher)

    def copy(self) -> "GameStatLine":
        return GameStatLine(self.hitter.copy(), self.pitcher.copy())

    def as_dict(self, include_derived: bool = False) -> dict[str, object]:
        return {"hitter": self.hitter.as_dict(include_derived), "pitcher": self.pitcher.as_dict(include_derived)}

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> "GameStatLine":
        return cls(HitterCountingStats.from_dict(_mapping(data.get("hitter"))), PitcherCountingStats.from_dict(_mapping(data.get("pitcher"))))


@dataclass
class _SplitStatLine:
    first_team: GameStatLine = field(default_factory=GameStatLine)
    farm: GameStatLine = field(default_factory=GameStatLine)

    def add_game(self, level: str, line: GameStatLine) -> None:
        target = self.first_team if normalize_level(level) == "FIRST" else self.farm
        target.add(line)

    def add_split(self, other: "_SplitStatLine") -> None:
        self.first_team.add(other.first_team); self.farm.add(other.farm)

    @property
    def overall(self) -> GameStatLine:
        out = self.first_team.copy(); out.add(self.farm); return out

    def copy(self):
        return type(self).from_dict(self.as_dict())

    def as_dict(self, include_derived: bool = False) -> dict[str, object]:
        return {
            "first_team": self.first_team.as_dict(include_derived),
            "farm": self.farm.as_dict(include_derived),
            "overall": self.overall.as_dict(include_derived),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]):
        return cls(GameStatLine.from_dict(_mapping(data.get("first_team"))), GameStatLine.from_dict(_mapping(data.get("farm"))))


@dataclass
class PeriodStatLine(_SplitStatLine):
    pass


@dataclass
class SeasonStatLine(_SplitStatLine):
    year: int | None = None

    def as_dict(self, include_derived: bool = False) -> dict[str, object]:
        payload = super().as_dict(include_derived); payload["year"] = self.year; return payload

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> "SeasonStatLine":
        return cls(
            GameStatLine.from_dict(_mapping(data.get("first_team"))),
            GameStatLine.from_dict(_mapping(data.get("farm"))),
            int(data["year"]) if data.get("year") is not None else None,
        )


@dataclass
class CareerStatLine(_SplitStatLine):
    seasons: int = 0

    def as_dict(self, include_derived: bool = False) -> dict[str, object]:
        payload = super().as_dict(include_derived); payload["seasons"] = self.seasons; return payload

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> "CareerStatLine":
        return cls(
            GameStatLine.from_dict(_mapping(data.get("first_team"))),
            GameStatLine.from_dict(_mapping(data.get("farm"))), int(data.get("seasons", 0)),
        )


@dataclass(frozen=True)
class GamePerformance:
    game_date: date
    level: str
    started: bool = True
    opponent: str | None = None
    hitter_stats: HitterCountingStats = field(default_factory=HitterCountingStats)
    pitcher_stats: PitcherCountingStats = field(default_factory=PitcherCountingStats)
    team_result: str | None = None
    score: tuple[int, int] | None = None
    notable_events: tuple[str, ...] = ()
    unsupported_stats: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "level", normalize_level(self.level))
        if self.team_result not in {None, "W", "L", "T"}:
            raise ValueError("team_result must be W/L/T/None")
        if self.score is not None and (len(self.score) != 2 or min(self.score) < 0):
            raise ValueError("score must be a non-negative (for, against) pair")
        if self.unsupported_stats:
            object.__setattr__(self, "pitcher_stats", self.pitcher_stats.with_unsupported(self.unsupported_stats))

    @property
    def stat_line(self) -> GameStatLine:
        return GameStatLine(self.hitter_stats.copy(), self.pitcher_stats.copy())

    def as_dict(self, include_derived: bool = False) -> dict[str, object]:
        return {
            "date": self.game_date.isoformat(), "level": self.level, "started": self.started,
            "opponent": self.opponent, "hitter_stats": self.hitter_stats.as_dict(include_derived),
            "pitcher_stats": self.pitcher_stats.as_dict(include_derived), "team_result": self.team_result,
            "score": list(self.score) if self.score is not None else None,
            "notable_events": list(self.notable_events), "unsupported_stats": list(self.unsupported_stats),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> "GamePerformance":
        raw = data.get("score"); score = None
        if isinstance(raw, Sequence) and not isinstance(raw, (str, bytes)) and len(raw) == 2:
            score = (int(raw[0]), int(raw[1]))
        return cls(
            date.fromisoformat(str(data["date"])), str(data.get("level", "FARM")),
            bool(data.get("started", True)), str(data["opponent"]) if data.get("opponent") is not None else None,
            HitterCountingStats.from_dict(_mapping(data.get("hitter_stats"))),
            PitcherCountingStats.from_dict(_mapping(data.get("pitcher_stats"))),
            str(data["team_result"]) if data.get("team_result") is not None else None, score,
            tuple(str(v) for v in _sequence(data.get("notable_events"))),
            tuple(str(v) for v in _sequence(data.get("unsupported_stats"))),
        )


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _sequence(value: object) -> Sequence[object]:
    return value if isinstance(value, Sequence) and not isinstance(value, (str, bytes)) else ()


def normalize_level(level: str) -> str:
    value = level.upper().strip()
    if value in {"FIRST", "FIRST_TEAM", "KBO"}: return "FIRST"
    if value in {"FARM", "SECOND", "SECOND_TEAM"}: return "FARM"
    raise ValueError(f"unsupported level: {level}")


def hitter_stats_from_result(source: object) -> HitterCountingStats:
    h = int(getattr(source, "H", 0)); doubles = int(getattr(source, "doubles", 0))
    triples = int(getattr(source, "triples", 0)); hr = int(getattr(source, "HR", 0))
    singles = int(getattr(source, "singles", max(0, h - doubles - triples - hr)))
    return HitterCountingStats(
        G=int(getattr(source, "G", 0)), PA=int(getattr(source, "PA", 0)), AB=int(getattr(source, "AB", 0)),
        R=int(getattr(source, "R", 0)), H=h, singles=singles, doubles=doubles, triples=triples, HR=hr,
        RBI=int(getattr(source, "RBI", 0)), BB=int(getattr(source, "BB", 0)), HBP=int(getattr(source, "HBP", 0)),
        SO=int(getattr(source, "SO", 0)), SB=int(getattr(source, "SB", 0)), CS=int(getattr(source, "CS", 0)),
        GDP=int(getattr(source, "GDP", 0)), SF=int(getattr(source, "SF", 0)),
    )


def pitcher_stats_from_result(source: object, *, started: bool | None = None, decisions: Mapping[str, int] | None = None) -> PitcherCountingStats:
    decisions = decisions or {}; g = int(getattr(source, "G", 0))
    return PitcherCountingStats(
        G=g, GS=1 if started and g else 0, BF=int(getattr(source, "BF", 0)),
        outs_pitched=int(getattr(source, "outs", getattr(source, "outs_pitched", 0))),
        H=int(getattr(source, "H", 0)), R=int(getattr(source, "R", 0)), ER=int(getattr(source, "ER", 0)),
        HR=int(getattr(source, "HR", 0)), BB=int(getattr(source, "BB", 0)), HBP=int(getattr(source, "HBP", 0)),
        SO=int(getattr(source, "SO", 0)), W=int(decisions.get("W", 0)), L=int(decisions.get("L", 0)),
        SV=int(decisions.get("SV", 0)), HLD=int(decisions.get("HLD", 0)),
        er_supported=hasattr(source, "ER"), w_supported="W" in decisions,
        l_supported="L" in decisions, sv_supported="SV" in decisions,
        hld_supported="HLD" in decisions,
    )


def unsupported_pitcher_fields(source: object, *, started: bool | None = None) -> tuple[str, ...]:
    out = [] if started is not None else ["GS"]
    for label in ("R", "ER", "HBP", "W", "L", "SV", "HLD"):
        if label in {"W", "L", "SV", "HLD"} or not hasattr(source, label):
            out.append(label)
    return tuple(out)


def game_performance_from_results(*, game_date: date, level: str, hitter_result: object | None = None,
                                  pitcher_result: object | None = None, started: bool = True,
                                  opponent: str | None = None, team_result: str | None = None,
                                  score: tuple[int, int] | None = None,
                                  notable_events: Iterable[str] = ()) -> GamePerformance:
    hitter = hitter_stats_from_result(hitter_result) if hitter_result is not None else HitterCountingStats()
    pitcher = pitcher_stats_from_result(pitcher_result, started=started) if pitcher_result is not None else PitcherCountingStats()
    unsupported: list[str] = []
    if hitter_result is not None and not hasattr(hitter_result, "SF"): unsupported.append("SF")
    if pitcher_result is not None: unsupported.extend(unsupported_pitcher_fields(pitcher_result, started=started))
    return GamePerformance(game_date, level, started, opponent, hitter, pitcher, team_result, score,
                           tuple(notable_events), tuple(sorted(set(unsupported))))


def aggregate_game_performances(games: Iterable[GamePerformance]) -> PeriodStatLine:
    out = PeriodStatLine()
    for game in games: out.add_game(game.level, game.stat_line)
    return out


def season_from_games(games: Iterable[GamePerformance], year: int | None = None) -> SeasonStatLine:
    items = list(games)
    if year is None and items: year = items[0].game_date.year
    out = SeasonStatLine(year=year)
    for game in items: out.add_game(game.level, game.stat_line)
    return out


def career_from_seasons(seasons: Iterable[SeasonStatLine]) -> CareerStatLine:
    out = CareerStatLine()
    for season in seasons: out.add_split(season); out.seasons += 1
    return out


def season_stats_from_record(record: object) -> SeasonStatLine:
    out = SeasonStatLine(year=int(getattr(record, "year", 0)) or None)
    if getattr(record, "first_team", None) is not None: out.first_team.hitter = hitter_stats_from_result(record.first_team)
    if getattr(record, "farm", None) is not None: out.farm.hitter = hitter_stats_from_result(record.farm)
    return out


def career_stats_from_records(records: Iterable[object]) -> CareerStatLine:
    return career_from_seasons(season_stats_from_record(record) for record in records)
