"""Batting and career record models."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class BattingLine:
    G: int = 0
    PA: int = 0
    AB: int = 0
    H: int = 0
    doubles: int = 0
    triples: int = 0
    HR: int = 0
    BB: int = 0
    SO: int = 0
    HBP: int = 0
    SB: int = 0
    CS: int = 0
    R: int = 0
    RBI: int = 0
    # H3.2.1 optional production diagnostics. Defaults preserve old saves.
    ROE: int = 0
    GDP: int = 0
    SB_attempts: int = 0
    DP_avoided: int = 0
    XBT: int = 0
    XBT_attempts: int = 0
    first_to_third: int = 0
    second_to_home: int = 0
    # Natural-event extension. Optional zero-default preserves old saves.
    SF: int = 0

    @property
    def singles(self) -> int:
        return max(0, self.H - self.doubles - self.triples - self.HR)

    @property
    def AVG(self) -> float:
        return self.H / self.AB if self.AB else 0.0

    @property
    def OBP(self) -> float:
        return (self.H + self.BB + self.HBP) / self.PA if self.PA else 0.0

    @property
    def SLG(self) -> float:
        total_bases = self.singles + 2 * self.doubles + 3 * self.triples + 4 * self.HR
        return total_bases / self.AB if self.AB else 0.0

    @property
    def OPS(self) -> float:
        return self.OBP + self.SLG

    def record_pa(self, result: str, runs: int = 0, rbi: int = 0) -> None:
        self.PA += 1
        self.R += max(0, runs)
        self.RBI += max(0, rbi)
        if result == "walk":
            self.BB += 1
            return
        if result == "hit_by_pitch":
            self.HBP += 1
            return
        if result == "sacrifice_fly":
            self.SF += 1
            return
        self.AB += 1
        if result == "strikeout":
            self.SO += 1
        elif result in {"out", "fielders_choice"}:
            return
        elif result == "reached_on_error":
            self.ROE += 1
        elif result == "single":
            self.H += 1
        elif result == "double":
            self.H += 1
            self.doubles += 1
        elif result == "triple":
            self.H += 1
            self.triples += 1
        elif result == "home_run":
            self.H += 1
            self.HR += 1
        else:
            raise ValueError(f"unsupported plate appearance result: {result}")

    def add(self, other: "BattingLine") -> None:
        for name in (
            "G", "PA", "AB", "H", "doubles", "triples", "HR", "BB", "SO",
            "HBP", "SB", "CS", "R", "RBI", "ROE", "GDP", "SB_attempts",
            "DP_avoided", "XBT", "XBT_attempts", "first_to_third",
            "second_to_home", "SF",
        ):
            setattr(self, name, getattr(self, name) + getattr(other, name))

    def as_dict(self) -> dict[str, int]:
        return {
            "G": self.G, "PA": self.PA, "AB": self.AB, "H": self.H,
            "2B": self.doubles, "3B": self.triples, "HR": self.HR,
            "BB": self.BB, "SO": self.SO, "HBP": self.HBP, "SB": self.SB,
            "CS": self.CS, "R": self.R, "RBI": self.RBI, "ROE": self.ROE,
            "GDP": self.GDP, "SB_attempts": self.SB_attempts,
            "DP_avoided": self.DP_avoided, "XBT": self.XBT,
            "XBT_attempts": self.XBT_attempts,
            "first_to_third": self.first_to_third,
            "second_to_home": self.second_to_home,
            "SF": self.SF,
        }

    @classmethod
    def from_dict(cls, data: dict[str, int]) -> "BattingLine":
        return cls(
            G=int(data.get("G", 0)), PA=int(data.get("PA", 0)),
            AB=int(data.get("AB", 0)), H=int(data.get("H", 0)),
            doubles=int(data.get("2B", data.get("doubles", 0))),
            triples=int(data.get("3B", data.get("triples", 0))),
            HR=int(data.get("HR", 0)), BB=int(data.get("BB", 0)),
            SO=int(data.get("SO", 0)), HBP=int(data.get("HBP", 0)),
            SB=int(data.get("SB", 0)), CS=int(data.get("CS", 0)),
            R=int(data.get("R", 0)), RBI=int(data.get("RBI", 0)),
            ROE=int(data.get("ROE", 0)), GDP=int(data.get("GDP", 0)),
            SB_attempts=int(data.get("SB_attempts", 0)),
            DP_avoided=int(data.get("DP_avoided", 0)),
            XBT=int(data.get("XBT", 0)),
            XBT_attempts=int(data.get("XBT_attempts", 0)),
            first_to_third=int(data.get("first_to_third", 0)),
            second_to_home=int(data.get("second_to_home", 0)),
            SF=int(data.get("SF", 0)),
        )


@dataclass
class SeasonRecord:
    year: int
    age: int
    team: str
    first_team: BattingLine = field(default_factory=BattingLine)
    farm: BattingLine = field(default_factory=BattingLine)
    awards: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, object]:
        return {
            "year": self.year, "age": self.age, "team": self.team,
            "first_team": self.first_team.as_dict(),
            "farm": self.farm.as_dict(),
            "awards": list(self.awards),
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "SeasonRecord":
        return cls(
            year=int(data["year"]), age=int(data["age"]), team=str(data["team"]),
            first_team=BattingLine.from_dict(dict(data.get("first_team", {}))),
            farm=BattingLine.from_dict(dict(data.get("farm", {}))),
            awards=[str(v) for v in data.get("awards", [])],
        )
