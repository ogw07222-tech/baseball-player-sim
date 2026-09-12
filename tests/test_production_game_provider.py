import json
import subprocess
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from src import config
from src.career import CareerEngine
from src.game_provider import GameFixture, ProductionGameProvider
from src.persistence import load_game, save_game
from src.player import Player
from src.production_advance import ProductionAdvanceService
from src.rng import RNG
from src.stat_aggregation import aggregate_game_performances
from src.stats import PlayerStats
from src.time_advance import _add_one_calendar_month


def make_player(name: str, *, team: str | None = None, speed: int = 100) -> Player:
    return Player(
        name=name,
        age=24,
        stats=PlayerStats(
            contact=100, power=100, discipline=100, speed=speed, defense=100,
            throwing=100, stamina=100, durability=100, mentality=100, talent=100,
        ),
        position="SS",
        team=team,
        roster_level="FIRST",
    )


def make_career(seed: int = 1) -> CareerEngine:
    team = str(config.KBO_TEAMS[0]["name"])
    player = make_player("Career User", team=team)
    player.draft_info = {
        "team": team, "round": 1, "pick": 1, "status": "지명",
        "scouting_score": 110.0, "scouted_talent": 100,
    }
    engine = CareerEngine(player, RNG(seed))
    engine.phase = "PRO"
    return engine


class FullGameProviderTests(unittest.TestCase):
    def test_production_game_finishes_and_score_nonnegative(self):
        result = ProductionGameProvider().run_game(
            GameFixture(date(2026, 4, 1), "Away", "Home"), RNG(20260906)
        )
        self.assertGreaterEqual(result.innings_played, 9)
        self.assertGreaterEqual(result.away_score, 0)
        self.assertGreaterEqual(result.home_score, 0)
        self.assertIsNotNone(result.winner)
        self.assertFalse(result.safety_cap_hit)

    def test_same_seed_same_full_game(self):
        fixture = GameFixture(date(2026, 4, 1), "Away", "Home")
        a = ProductionGameProvider().run_game(fixture, RNG(77))
        b = ProductionGameProvider().run_game(fixture, RNG(77))
        self.assertEqual(
            (a.away_score, a.home_score, a.innings_played, a.event_count),
            (b.away_score, b.home_score, b.innings_played, b.event_count),
        )
        self.assertEqual(
            [line.batting_line.as_dict() for line in a.player_lines],
            [line.batting_line.as_dict() for line in b.player_lines],
        )
        self.assertEqual(
            [(p.pitcher_id, p.stats.as_dict()) for p in a.pitcher_lines],
            [(p.pitcher_id, p.stats.as_dict()) for p in b.pitcher_lines],
        )

    def test_real_nine_player_lineups_and_exact_user_line(self):
        user = make_player("User", team="Home", speed=120)
        result = ProductionGameProvider().run_game(
            GameFixture(date(2026, 4, 2), "Away", "Home"), RNG(123),
            user_player=user, user_team="Home", user_started=True,
            participation_reason="STARTED",
        )
        away = [line for line in result.player_lines if line.team == "Away"]
        home = [line for line in result.player_lines if line.team == "Home"]
        self.assertEqual(len(away), 9)
        self.assertEqual(len(home), 9)
        self.assertEqual(len({line.lineup_slot for line in home}), 9)
        self.assertIsNotNone(result.user_player_id)
        user_line = result.player_line(result.user_player_id)
        self.assertIsNotNone(user_line)
        self.assertEqual(user_line.player_name, "User")
        self.assertEqual(user_line.stats.PA, user_line.batting_line.PA)
        self.assertEqual(user_line.stats.H, user_line.batting_line.H)
        self.assertEqual(user_line.stats.SB, user_line.batting_line.SB)

    def test_pitcher_bf_hits_walks_strikeouts_and_runs_exact(self):
        result = ProductionGameProvider().run_game(
            GameFixture(date(2026, 4, 3), "Away", "Home"), RNG(303)
        )
        away_batters = [line.stats for line in result.player_lines if line.team == "Away"]
        home_batters = [line.stats for line in result.player_lines if line.team == "Home"]
        home_pitchers = [line.stats for line in result.pitcher_lines if line.team == "Home"]
        away_pitchers = [line.stats for line in result.pitcher_lines if line.team == "Away"]
        self.assertEqual(sum(p.BF for p in home_pitchers), sum(h.PA for h in away_batters))
        self.assertEqual(sum(p.H for p in home_pitchers), sum(h.H for h in away_batters))
        self.assertEqual(sum(p.BB for p in home_pitchers), sum(h.BB for h in away_batters))
        self.assertEqual(sum(p.SO for p in home_pitchers), sum(h.SO for h in away_batters))
        self.assertEqual(sum(p.R for p in home_pitchers), result.away_score)
        self.assertEqual(sum(p.BF for p in away_pitchers), sum(h.PA for h in home_batters))
        self.assertEqual(sum(p.R for p in away_pitchers), result.home_score)

    def test_starter_does_not_throw_every_inning(self):
        result = ProductionGameProvider().run_game(
            GameFixture(date(2026, 4, 4), "Away", "Home"), RNG(404)
        )
        for team in ("Away", "Home"):
            lines = [line for line in result.pitcher_lines if line.team == team]
            roles = {line.role for line in lines}
            self.assertIn("starter", roles)
            self.assertIn("bullpen_fallback", roles)
            starter = next(line for line in lines if line.role == "starter")
            self.assertEqual(starter.stats.outs_pitched, 18)
            self.assertIn("ER", starter.unsupported_stats)
            self.assertIn("W", starter.unsupported_stats)

        high_k = [event for event in result.notable_events if event.startswith("HIGH_K:")]
        pitcher_ids = {line.pitcher_id for line in result.pitcher_lines}
        for event in high_k:
            pitcher_id, strikeouts = event[len("HIGH_K:"):].rsplit(":", 1)
            self.assertIn(pitcher_id, pitcher_ids)
            self.assertGreaterEqual(int(strikeouts), 10)

    def test_team_result_comes_from_final_score(self):
        result = ProductionGameProvider().run_game(
            GameFixture(date(2026, 4, 5), "Away", "Home"), RNG(505)
        )
        self.assertEqual(
            {result.team_result_for("Away"), result.team_result_for("Home")},
            {"W", "L"},
        )


class ProductionAdvanceTests(unittest.TestCase):
    def test_advance_one_game_uses_full_game_provider_and_aggregates(self):
        engine = make_career(1001)
        service = ProductionAdvanceService(engine)
        summary = service.advance_one_game()
        self.assertEqual(summary.games_played, 1)
        self.assertTrue(summary.team_result_supported)
        self.assertIsNotNone(service.game_provider.last_result)
        perf = service.state.recent_games[-1]
        self.assertEqual(summary.player_period_stats.overall.hitter.PA, perf.hitter_stats.PA)
        session = engine.current_session
        self.assertIsNotNone(session)
        expected_pa = session.record.first_team.PA + session.record.farm.PA
        self.assertEqual(service.state.season.overall.hitter.PA, expected_pa)

    def test_week_equals_repeated_games(self):
        bulk_engine = make_career(2002)
        repeated_engine = make_career(2002)
        bulk = ProductionAdvanceService(bulk_engine)
        repeated = ProductionAdvanceService(repeated_engine)
        start = bulk.state.current_date
        end = start + timedelta(days=7)
        dates = bulk.schedule.game_dates(start, end)
        bulk.advance_one_week()
        for _ in dates:
            repeated.advance_one_game()
        self.assertEqual(bulk.state.season.as_dict(), repeated.state.season.as_dict())
        self.assertEqual(bulk.state.career.as_dict(), repeated.state.career.as_dict())
        self.assertEqual(
            [g.as_dict() for g in bulk.state.recent_games],
            [g.as_dict() for g in repeated.state.recent_games],
        )
        self.assertEqual(
            bulk_engine.current_session.record.as_dict(),
            repeated_engine.current_session.record.as_dict(),
        )

    def test_month_equals_repeated_games(self):
        bulk_engine = make_career(3003)
        repeated_engine = make_career(3003)
        bulk = ProductionAdvanceService(bulk_engine)
        repeated = ProductionAdvanceService(repeated_engine)
        start = bulk.state.current_date
        end = _add_one_calendar_month(start)
        dates = bulk.schedule.game_dates(start, end)
        bulk.advance_one_month()
        for _ in dates:
            repeated.advance_one_game()
        self.assertEqual(bulk.state.season.as_dict(), repeated.state.season.as_dict())
        self.assertEqual(bulk.state.career.as_dict(), repeated.state.career.as_dict())

    def test_month_window_uses_production_calendar_helper(self):
        self.assertEqual(_add_one_calendar_month(date(2026, 1, 31)), date(2026, 2, 28))
        self.assertEqual(_add_one_calendar_month(date(2026, 4, 30)), date(2026, 5, 30))
        self.assertEqual(_add_one_calendar_month(date(2026, 12, 31)), date(2027, 1, 31))

    def test_season_and_career_totals_equal_game_sum(self):
        engine = make_career(4004)
        service = ProductionAdvanceService(engine)
        service.advance_one_week()
        aggregate = aggregate_game_performances(list(service.state.recent_games))
        self.assertEqual(
            service.state.season.overall.hitter.as_dict(),
            aggregate.overall.hitter.as_dict(),
        )
        self.assertEqual(
            service.state.career.overall.hitter.as_dict(),
            service.state.season.overall.hitter.as_dict(),
        )

    def test_save_load_optional_advance_state_and_old_save_compatibility(self):
        engine = make_career(5005)
        service = ProductionAdvanceService(engine)
        service.advance_one_game()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "save.json"
            save_game(path, engine)
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertIn("advance_state", payload)
            loaded = load_game(path)
            self.assertTrue(hasattr(loaded, "advance_state"))
            self.assertEqual(engine.advance_state.as_dict(), loaded.advance_state.as_dict())
            payload.pop("advance_state", None)
            old_path = Path(tmp) / "old.json"
            old_path.write_text(json.dumps(payload), encoding="utf-8")
            old = load_game(old_path)
            self.assertFalse(hasattr(old, "advance_state"))


class ProtectedFormulaTests(unittest.TestCase):
    EXPECTED_BLOBS = {
        "src/simulation.py": "b441fbe2fd8bf2aac9239a4648636a2ec67ceb53",
        "src/hitting/model.py": "585d4cd0eb4c5464d02fe0805d359b0e9cafe39d",
        "src/hitting/parameters.py": "3876b4221f53b7d4b7cc6069d9425004fc9f311a",
        "src/hitting/baserunning.py": "2a383ce61fb6938ae30973be210159baa1d76726",
        "src/hitting/defense.py": "279f6282ef41c53e709839dbbe791e16836eaf53",
        "src/natural_events.py": "e13f093d646ac6eb0409c3d0b633ba17073cf877",
        "src/config.py": "ed6c07b3517f92f6ad2d1ceb35fe0e0a81862512",
        "src/pitching/__init__.py": "8593e1865da96fbfa0587199c8bddc56833f219d",
        "src/pitching/events.py": "55803e2d79b89b2065eb702b5306005c5d6b075f",
        "src/pitching/fatigue.py": "533516598f4143e6e4940fde102db517c279e2c8",
        "src/pitching/growth.py": "2607359b3f997013447ddd8b67187c59e851dfb1",
        "src/pitching/model.py": "c53739f5afe57398c860f8986051723a977b5056",
        "src/pitching/parameters.py": "6d982f38d966345e7b57e59462e5dce85773278b",
        "src/pitching/performance.py": "c1a43de1ba705ae6469ebc2113381f98194407ee",
        "src/pitching/roles.py": "31222d3ee62998ccd892407c225ef7fa501af566",
    }

    def _root(self):
        return Path(__file__).resolve().parents[1]

    def _hash(self, path):
        root = self._root()
        if not (root / ".git").exists():
            self.skipTest("git metadata unavailable")
        return subprocess.check_output(["git", "hash-object", path], cwd=root, text=True).strip()

    def test_formula_files_untouched(self):
        for path, expected in self.EXPECTED_BLOBS.items():
            self.assertEqual(self._hash(path), expected, path)

    def test_catcher_schema_does_not_change_current_ability(self):
        base = dict(
            contact=111, power=109, discipline=103, speed=97, defense=105,
            throwing=98, stamina=101, durability=96, mentality=107, talent=120,
        )
        low = PlayerStats(**base, game_calling=0)
        high = PlayerStats(**base, game_calling=180)
        self.assertEqual(low.current_ability(), high.current_ability())
        weights = {
            "contact": 1.2, "power": 1.1, "discipline": 1.0, "speed": 0.55,
            "defense": 0.75, "throwing": 0.35, "stamina": 0.30,
            "durability": 0.30, "mentality": 0.45,
        }
        expected = sum(base[name] * weight for name, weight in weights.items()) / sum(weights.values())
        self.assertAlmostEqual(low.current_ability(), expected)

    def test_normalization_files_untouched(self):
        root = self._root()
        self.assertFalse((root / "src/hitting/normalization.py").exists())


if __name__ == "__main__":
    unittest.main()