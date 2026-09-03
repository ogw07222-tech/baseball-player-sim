"""High-school, draft, KBO season, awards, events, and retirement loop."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from . import config
from .growth import GrowthResult, apply_season_growth
from .player import InjuryStatus, Player
from .records import BattingLine, SeasonRecord
from .rng import RNG
from .simulation import logistic_range, simulate_player_game
from .traits import TRAIT_CATALOG, Trait, has_trait, traits_conflict


@dataclass(frozen=True)
class TournamentResult:
    name: str
    games: int
    line: BattingLine
    champion: bool
    mvp: bool


@dataclass(frozen=True)
class DraftResult:
    team: str
    round: int | None
    pick: int | None
    status: str
    scouting_score: float
    scouted_talent: int

    def as_dict(self) -> dict[str, object]:
        return {
            "team": self.team, "round": self.round, "pick": self.pick, "status": self.status,
            "scouting_score": round(self.scouting_score, 3), "scouted_talent": self.scouted_talent,
        }


@dataclass
class ProSeasonSession:
    year: int
    record: SeasonRecord
    games_completed: int = 0
    current_level: str = "FARM"

    @property
    def finished(self) -> bool:
        return self.games_completed >= config.KBO_FIRST_TEAM_GAMES

    def as_dict(self) -> dict[str, object]:
        return {
            "year": self.year, "record": self.record.as_dict(), "games_completed": self.games_completed,
            "current_level": self.current_level,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "ProSeasonSession":
        return cls(
            year=int(data["year"]), record=SeasonRecord.from_dict(dict(data["record"])),
            games_completed=int(data.get("games_completed", 0)), current_level=str(data.get("current_level", "FARM")),
        )


@dataclass
class CareerEngine:
    player: Player
    rng: RNG
    year: int = config.START_YEAR
    tournament_index: int = 0
    phase: str = "HIGH_SCHOOL"
    tournament_results: list[dict[str, object]] = field(default_factory=list)
    current_session: ProSeasonSession | None = None

    def run_next_tournament(self) -> TournamentResult:
        if self.phase != "HIGH_SCHOOL":
            raise RuntimeError("not in high-school phase")
        if self.tournament_index >= len(config.HIGH_SCHOOL_TOURNAMENTS):
            raise RuntimeError("all tournaments already completed")
        name = config.HIGH_SCHOOL_TOURNAMENTS[self.tournament_index]
        line = BattingLine()
        games = 0
        alive = True
        while alive and games < 5:
            games += 1
            opponent = self.rng.uniform(*config.HIGH_SCHOOL_PITCHER_LEVEL)
            simulate_player_game(self.player, opponent, self.rng, line, pa_count=self.rng.randint(4, 5))
            ability_edge = (self.player.stats.current_ability() - opponent) / 150.0
            win_p = max(0.25, min(0.75, 0.50 + ability_edge + self.rng.gauss(0, 0.035)))
            alive = self.rng.random() < win_p
        champion = alive and games == 5
        mvp = games >= 3 and line.PA >= 12 and line.OPS >= 1.05 and self.rng.random() < min(0.85, 0.25 + (line.OPS - 1.0))
        self.player.high_school_stats.add(line)
        if mvp:
            self.player.awards.append({"year": self.year, "award": f"{name} MVP", "level": "HIGH_SCHOOL"})
        result = TournamentResult(name, games, line, champion, mvp)
        self.tournament_results.append({
            "name": name, "games": games, "line": line.as_dict(), "champion": champion, "mvp": mvp,
        })
        self.tournament_index += 1
        return result

    def finish_high_school(self) -> None:
        while self.tournament_index < len(config.HIGH_SCHOOL_TOURNAMENTS):
            self.run_next_tournament()

    def evaluate_draft(self) -> DraftResult:
        if self.phase != "HIGH_SCHOOL":
            if self.player.draft_info:
                info = self.player.draft_info
                return DraftResult(str(info["team"]), info.get("round") and int(info["round"]), info.get("pick") and int(info["pick"]), str(info["status"]), float(info["scouting_score"]), int(info["scouted_talent"]))
            raise RuntimeError("draft can only run after high school")
        self.finish_high_school()
        scouted_talent = max(0, int(round(self.rng.gauss(self.player.stats.talent, 24.0))))
        ability = self.player.stats.current_ability()
        perf = 72.0 + (self.player.high_school_stats.OPS - 0.75) * 55.0
        perf += min(12.0, self.player.high_school_stats.HR * 1.4)
        health = self.player.stats.durability
        position = 75.0 + config.POSITION_DRAFT_VALUE.get(self.player.position, 0)
        w = config.DRAFT_WEIGHTS
        score = (
            ability * w["current_ability"] + scouted_talent * w["scouted_talent"]
            + perf * w["performance"] + position * w["position"] + health * w["health"]
            + self.rng.gauss(0.0, 7.0)
        )
        if score >= 103:
            round_no = 1
        elif score >= 94:
            round_no = self.rng.randint(2, 3)
        elif score >= 84:
            round_no = self.rng.randint(4, 7)
        elif score >= 75:
            round_no = self.rng.randint(8, 11)
        else:
            round_no = None
        team_info = self.rng.choice(config.KBO_TEAMS)
        team = str(team_info["name"])
        if round_no is None:
            status = "미지명 육성선수 계약"
            pick = None
        else:
            status = "지명"
            pick = (round_no - 1) * 10 + self.rng.randint(1, 10)
        draft = DraftResult(team, round_no, pick, status, score, scouted_talent)
        self.player.draft_info = draft.as_dict()
        self.player.team = team
        self.player.roster_level = "FARM"
        self.player.team_history.append({"year": self.year, "team": team, "event": "KBO 입단"})
        self.phase = "PRO"
        return draft

    def _team_config(self) -> dict[str, object]:
        if not self.player.team:
            raise RuntimeError("player has no KBO team")
        return next(dict(team) for team in config.KBO_TEAMS if team["name"] == self.player.team)

    def start_pro_season(self) -> ProSeasonSession:
        if self.phase == "HIGH_SCHOOL":
            self.evaluate_draft()
        if self.phase != "PRO":
            raise RuntimeError("career is not in professional phase")
        if self.current_session:
            return self.current_session
        current_level = "FIRST" if self._initial_first_team_chance() else "FARM"
        self.player.roster_level = current_level
        record = SeasonRecord(self.year, self.player.age, self.player.team or "", BattingLine(), BattingLine())
        self.current_session = ProSeasonSession(self.year, record, 0, current_level)
        return self.current_session

    def _initial_first_team_chance(self) -> bool:
        team = self._team_config()
        competition = float(team["depth"]) + config.POSITION_COMPETITION.get(self.player.position, 0) - 10.0
        chance = logistic_range(self.player.stats.current_ability() - competition, 0.02, 0.72, 11.0)
        if self.player.draft_info and self.player.draft_info.get("round") == 1:
            chance += 0.08
        return self.rng.random() < min(0.82, chance)

    def _update_form(self) -> None:
        if self.player.form_games_remaining > 0:
            self.player.form_games_remaining -= 1
            if self.player.form_games_remaining <= 0:
                self.player.form = "normal"
            return
        mentality_factor = logistic_range(100 - self.player.stats.mentality, 0.65, 1.35, 35)
        slump_chance = config.SLUMP_BASE_CHANCE_PER_GAME * mentality_factor
        hot_chance = config.HOT_STREAK_BASE_CHANCE_PER_GAME / max(0.7, mentality_factor)
        if has_trait(self.player.traits, "volatile"):
            slump_chance *= 1.55
            hot_chance *= 1.35
        if has_trait(self.player.traits, "consistent"):
            slump_chance *= 0.62
            hot_chance *= 0.72
        roll = self.rng.random()
        if roll < slump_chance:
            self.player.form = "slump"
            self.player.form_games_remaining = self.rng.randint(config.FORM_MIN_GAMES, config.FORM_MAX_GAMES)
        elif roll < slump_chance + hot_chance:
            self.player.form = "hot"
            self.player.form_games_remaining = self.rng.randint(config.FORM_MIN_GAMES, config.FORM_MAX_GAMES)

    def _injury_chance(self) -> float:
        durability_factor = logistic_range(100 - self.player.stats.durability, 0.55, 1.65, 32.0)
        fatigue_factor = 1.0 + max(0.0, self.player.fatigue - 50.0) / 65.0
        age_factor = 1.0 + max(0, self.player.age - 30) * 0.045
        chance = config.INJURY_BASE_CHANCE_PER_GAME * durability_factor * fatigue_factor * age_factor
        if has_trait(self.player.traits, "injury_risk"):
            chance *= 1.65
        return min(0.08, chance)

    def _maybe_injure(self) -> None:
        if self.player.injury or self.rng.random() >= self._injury_chance():
            return
        severity = self.rng.weighted_choice((("경미", 0.72), ("보통", 0.24), ("중상", 0.04)))
        if severity == "경미":
            days = self.rng.randint(2, 10)
            name = self.rng.choice(("가벼운 근육통", "손목 염좌", "발목 통증"))
        elif severity == "보통":
            days = self.rng.randint(12, 45)
            name = self.rng.choice(("햄스트링 부상", "어깨 염좌", "손가락 골절"))
        else:
            days = self.rng.randint(60, 150)
            name = self.rng.choice(("무릎 인대 부상", "어깨 중상", "발목 골절"))
        self.player.injury = InjuryStatus(name, severity, days)
        self.player.injury_history.append({"year": self.year, "age": self.player.age, "name": name, "severity": severity, "games": days})

    def _recover_day(self) -> None:
        self.player.fatigue = max(0.0, self.player.fatigue - config.FATIGUE_REST_RECOVERY)
        if self.player.injury:
            recovery = 2 if has_trait(self.player.traits, "quick_recovery") and self.rng.random() < 0.25 else 1
            self.player.injury.games_remaining -= recovery
            if self.player.injury.games_remaining <= 0:
                self.player.injury = None

    def _play_probability(self, level: str) -> float:
        ability = self.player.stats.current_ability()
        if level == "FIRST":
            return logistic_range(ability - 92.0, 0.38, 0.90, 16.0)
        return logistic_range(ability - 68.0, 0.55, 0.94, 16.0)

    def _fatigue_after_game(self) -> None:
        stamina = max(1, self.player.stats.stamina)
        increment = config.FATIGUE_PER_GAME_BASE * (100.0 / (stamina + 45.0))
        self.player.fatigue = min(100.0, self.player.fatigue + increment)

    def _reconsider_roster(self, session: ProSeasonSession) -> None:
        if session.games_completed == 0 or session.games_completed % 10 != 0:
            return
        team = self._team_config()
        competition = float(team["depth"]) + config.POSITION_COMPETITION.get(self.player.position, 0) - 11.0
        line = session.record.first_team if session.current_level == "FIRST" else session.record.farm
        form_bonus = max(-12.0, min(15.0, (line.OPS - 0.75) * 25.0)) if line.PA >= 20 else 0.0
        evaluation = self.player.stats.current_ability() + form_bonus + self.rng.gauss(0, 5.5)
        if session.current_level == "FARM" and evaluation >= competition:
            session.current_level = "FIRST"
            self.player.roster_level = "FIRST"
            if self.player.debut_year is None:
                self.player.debut_year = self.year
        elif session.current_level == "FIRST" and evaluation < competition - 13.0 and line.PA >= 30:
            session.current_level = "FARM"
            self.player.roster_level = "FARM"

    def advance_pro_games(self, count: int) -> ProSeasonSession:
        if count <= 0:
            raise ValueError("count must be positive")
        session = self.start_pro_season()
        remaining = min(count, config.KBO_FIRST_TEAM_GAMES - session.games_completed)
        team = self._team_config()
        for _ in range(remaining):
            session.games_completed += 1
            if self.player.injury:
                self._recover_day()
                self._update_form()
                self._reconsider_roster(session)
                continue
            if self.rng.random() >= self._play_probability(session.current_level):
                self._recover_day()
                self._update_form()
                self._reconsider_roster(session)
                continue
            target = session.record.first_team if session.current_level == "FIRST" else session.record.farm
            opponent_level = float(team["first_team_level"] if session.current_level == "FIRST" else team["farm_level"])
            simulate_player_game(self.player, opponent_level, self.rng, target)
            if session.current_level == "FIRST" and self.player.debut_year is None:
                self.player.debut_year = self.year
            self._fatigue_after_game()
            self._maybe_injure()
            self._update_form()
            self._reconsider_roster(session)
        return session

    def _determine_awards(self, record: SeasonRecord) -> list[str]:
        line = record.first_team
        if line.PA < 300:
            return []
        rivals: list[dict[str, float]] = []
        for _ in range(9):
            avg = max(0.210, min(0.360, self.rng.gauss(0.275, 0.027)))
            hr = max(1.0, self.rng.gauss(22.0, 10.0))
            rbi = max(20.0, self.rng.gauss(78.0, 20.0))
            sb = max(0.0, self.rng.gauss(14.0, 11.0))
            ops = max(0.600, min(1.080, self.rng.gauss(0.790, 0.085)))
            defense = self.rng.gauss(100.0, 13.0)
            mvp = ops * 100 + hr * 0.55 + rbi * 0.10 + sb * 0.05
            rivals.append({"AVG": avg, "HR": hr, "RBI": rbi, "SB": sb, "OPS": ops, "DEF": defense, "MVP": mvp})
        awards: list[str] = []
        if line.AVG > max(r["AVG"] for r in rivals):
            awards.append("타격왕")
        if line.HR > max(r["HR"] for r in rivals):
            awards.append("홈런왕")
        if line.RBI > max(r["RBI"] for r in rivals):
            awards.append("타점왕")
        if line.SB > max(r["SB"] for r in rivals):
            awards.append("도루왕")
        defense_score = self.player.stats.defense + (8 if has_trait(self.player.traits, "defense_sense") else 0) + self.rng.gauss(0, 7)
        if line.G >= 80 and defense_score > max(r["DEF"] for r in rivals):
            awards.append("골든글러브")
        mvp_score = line.OPS * 100 + line.HR * 0.55 + line.RBI * 0.10 + line.SB * 0.05
        if mvp_score > max(r["MVP"] for r in rivals):
            awards.append("MVP")
        return awards

    def _maybe_change_trait(self) -> None:
        # Low-frequency acquisition/removal. This is intentionally not a fixed canon rule.
        if self.player.traits and self.rng.random() < 0.018:
            removed = self.rng.choice(self.player.traits)
            self.player.traits.remove(removed)
            self.player.trait_history.append({"year": self.year, "action": "lost", "trait": removed.key})
        if len(self.player.traits) >= 7 or self.rng.random() >= 0.045:
            return
        candidates: list[Trait] = [
            trait for trait in TRAIT_CATALOG
            if trait not in self.player.traits and not any(traits_conflict(trait, existing) for existing in self.player.traits)
        ]
        if candidates:
            gained = self.rng.choice(candidates)
            self.player.traits.append(gained)
            self.player.trait_history.append({"year": self.year, "action": "gained", "trait": gained.key})

    def finish_pro_season(self) -> tuple[SeasonRecord, GrowthResult]:
        session = self.start_pro_season()
        if not session.finished:
            self.advance_pro_games(config.KBO_FIRST_TEAM_GAMES - session.games_completed)
        awards = self._determine_awards(session.record)
        session.record.awards.extend(awards)
        for award in awards:
            self.player.awards.append({"year": self.year, "award": award, "level": "KBO"})
        self.player.seasons.append(session.record)
        growth = apply_season_growth(self.player, self.rng)
        self._maybe_change_trait()
        self.year += 1
        self.current_session = None
        self.player.form = "normal"
        self.player.form_games_remaining = 0
        self.player.fatigue = max(0.0, self.player.fatigue * 0.25)
        return session.record, growth

    def should_retire(self) -> bool:
        if self.player.age >= config.RETIREMENT_HARD_AGE:
            return True
        recent = self.player.seasons[-2:]
        recent_first_pa = sum(s.first_team.PA for s in recent)
        ability = self.player.stats.current_ability()
        chance = 0.0
        if self.player.age >= 35:
            chance += 0.05 + (self.player.age - 35) * 0.055
        if self.player.age >= 30 and recent_first_pa < 80:
            chance += 0.08
        if ability < 72:
            chance += 0.08
        if self.player.injury and self.player.injury.severity == "중상":
            chance += 0.07
        if self.player.age < 27:
            chance *= 0.05
        return self.rng.random() < min(0.92, chance)

    def retire(self) -> None:
        self.phase = "RETIRED"
        self.player.roster_level = "RETIRED"
        self.player.retirement_age = self.player.age

    def run_to_retirement(self, max_seasons: int = 30) -> Player:
        if self.phase == "HIGH_SCHOOL":
            self.evaluate_draft()
        seasons = 0
        while self.phase == "PRO" and seasons < max_seasons:
            self.finish_pro_season()
            seasons += 1
            if self.should_retire():
                self.retire()
        if self.phase == "PRO":
            self.retire()
        return self.player

    def as_dict(self) -> dict[str, object]:
        return {
            "year": self.year, "tournament_index": self.tournament_index, "phase": self.phase,
            "tournament_results": self.tournament_results,
            "current_session": self.current_session.as_dict() if self.current_session else None,
        }

    def restore_state(self, data: dict[str, Any]) -> None:
        self.year = int(data.get("year", self.year))
        self.tournament_index = int(data.get("tournament_index", 0))
        self.phase = str(data.get("phase", "HIGH_SCHOOL"))
        self.tournament_results = [dict(v) for v in data.get("tournament_results", [])]
        self.current_session = ProSeasonSession.from_dict(dict(data["current_session"])) if data.get("current_session") else None
