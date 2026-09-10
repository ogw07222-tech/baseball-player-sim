import json
import tempfile
import unittest
from pathlib import Path

from src import config
from src.career import CareerEngine
from src.persistence import load_game, save_game
from src.player import Player
from src.production_advance import ProductionAdvanceService
from src.rng import RNG
from src.stats import PlayerStats


def make_engine(seed: int = 7001) -> CareerEngine:
    team = str(config.KBO_TEAMS[0]["name"])
    player = Player(
        "Lifecycle User",
        24,
        PlayerStats(100, 100, 100, 100, 100, 100, 100, 100, 100, 100),
        position="SS",
        team=team,
        roster_level="FIRST",
    )
    player.draft_info = {
        "team": team,
        "round": 1,
        "pick": 1,
        "status": "지명",
        "scouting_score": 110.0,
        "scouted_talent": 100,
    }
    engine = CareerEngine(player, RNG(seed))
    engine.phase = "PRO"
    return engine


def completed_engine(seed: int = 7001) -> CareerEngine:
    engine = make_engine(seed)
    session = engine.start_pro_season()
    session.games_completed = config.KBO_FIRST_TEAM_GAMES
    session.record.first_team.PA = 250
    session.record.first_team.G = 80
    return engine


class SeasonLifecycleDomainTests(unittest.TestCase):
    def test_finalize_before_completion_rejected_without_rng_consumption(self):
        engine = make_engine()
        engine.start_pro_season().games_completed = 143
        before = engine.rng.get_state()
        with self.assertRaisesRegex(RuntimeError, "not complete"):
            engine.finalize_completed_pro_season()
        self.assertEqual(before, engine.rng.get_state())
        self.assertEqual(len(engine.player.seasons), 0)

    def test_completed_season_finalizes_exactly_once(self):
        engine = completed_engine()
        age_before = engine.player.age
        year_before = engine.year
        result = engine.finalize_completed_pro_season()
        self.assertEqual(result.completed_year, year_before)
        self.assertEqual(result.next_year, year_before + 1)
        self.assertEqual(result.age_before, age_before)
        self.assertEqual(result.age_after, age_before + 1)
        self.assertEqual(engine.player.age, age_before + 1)
        self.assertEqual(engine.year, year_before + 1)
        self.assertEqual(len(engine.player.seasons), 1)
        self.assertIsNone(engine.current_session)
        after_first = engine.rng.get_state()
        with self.assertRaisesRegex(RuntimeError, "no active professional season"):
            engine.finalize_completed_pro_season()
        self.assertEqual(after_first, engine.rng.get_state())
        self.assertEqual(len(engine.player.seasons), 1)
        self.assertEqual(len(engine.player.growth_history), 1)

    def test_pending_event_blocks_finalization_without_rng_consumption(self):
        engine = completed_engine()
        engine.current_session.pending_event_id = "pending-test"
        before = engine.rng.get_state()
        with self.assertRaisesRegex(RuntimeError, "pending event"):
            engine.finalize_completed_pro_season()
        self.assertEqual(before, engine.rng.get_state())
        self.assertEqual(len(engine.player.seasons), 0)

    def test_finish_pro_season_delegates_to_same_finalization_semantics(self):
        direct = completed_engine(7111)
        facade = completed_engine(7111)
        direct_result = direct.finalize_completed_pro_season()
        record, growth = facade.finish_pro_season()
        self.assertEqual(direct_result.record.as_dict(), record.as_dict())
        self.assertEqual(direct_result.growth, growth)
        self.assertEqual(direct.player.as_dict(), facade.player.as_dict())
        self.assertEqual(direct.as_dict(), facade.as_dict())
        self.assertEqual(direct.rng.get_state(), facade.rng.get_state())


class ProductionSeasonLifecycleTests(unittest.TestCase):
    def test_service_constructor_does_not_finalize_completed_season(self):
        engine = completed_engine(7201)
        before = engine.rng.get_state()
        service = ProductionAdvanceService(engine)
        self.assertTrue(service.season_complete)
        self.assertEqual(len(engine.player.seasons), 0)
        self.assertEqual(engine.year, config.START_YEAR)
        self.assertEqual(before, engine.rng.get_state())

    def test_game_144_save_load_then_finalize_exactly_once(self):
        engine = completed_engine(7301)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "at-144.json"
            save_game(path, engine)
            loaded = load_game(path)
            service = ProductionAdvanceService(loaded)
            self.assertTrue(service.season_complete)
            result = service.finalize_season()
            self.assertEqual(result.completed_year, config.START_YEAR)
            self.assertEqual(len(loaded.player.seasons), 1)
            self.assertFalse(hasattr(loaded, "advance_state"))
            after = loaded.rng.get_state()
            with self.assertRaises(RuntimeError):
                service.finalize_season()
            self.assertEqual(after, loaded.rng.get_state())

    def test_143_save_load_game_144_finalize_and_next_season(self):
        engine = make_engine(7401)
        session = engine.start_pro_season()
        session.games_completed = config.KBO_FIRST_TEAM_GAMES - 1
        service = ProductionAdvanceService(engine)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "at-143.json"
            save_game(path, engine)
            loaded = load_game(path)
            resumed = ProductionAdvanceService(loaded)
            resumed.advance_one_game()
            self.assertTrue(resumed.season_complete)
            old_year = loaded.year
            old_age = loaded.player.age
            resumed.finalize_season()
            self.assertEqual(loaded.year, old_year + 1)
            self.assertEqual(loaded.player.age, old_age + 1)
            self.assertEqual(len(loaded.player.seasons), 1)
            resumed.start_next_season()
            self.assertIsNotNone(loaded.current_session)
            self.assertEqual(loaded.current_session.year, old_year + 1)
            self.assertEqual(resumed.schedule.dates[0].year, old_year + 1)
            self.assertEqual(resumed.state.season.year, old_year + 1)

    def test_finalize_save_load_starts_fresh_next_season_without_replaying_growth(self):
        engine = completed_engine(7501)
        service = ProductionAdvanceService(engine)
        result = service.finalize_season()
        growth_history = list(engine.player.growth_history)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "finalized.json"
            save_game(path, engine)
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertNotIn("advance_state", payload)
            loaded = load_game(path)
            self.assertEqual(loaded.player.growth_history, growth_history)
            self.assertEqual(len(loaded.player.seasons), 1)
            self.assertEqual(loaded.year, result.next_year)
            next_service = ProductionAdvanceService(loaded)
            self.assertIsNone(loaded.current_session)
            self.assertEqual(loaded.player.growth_history, growth_history)
            next_service.start_next_season()
            self.assertEqual(len(loaded.player.growth_history), 1)
            self.assertEqual(loaded.current_session.year, result.next_year)

    def test_old_save_without_advance_state_remains_loadable(self):
        engine = make_engine(7601)
        engine.start_pro_season()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "save.json"
            save_game(path, engine)
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload.pop("advance_state", None)
            old_path = Path(tmp) / "old.json"
            old_path.write_text(json.dumps(payload), encoding="utf-8")
            loaded = load_game(old_path)
            service = ProductionAdvanceService(loaded)
            self.assertIsNotNone(service.state)
            self.assertEqual(loaded.current_session.games_completed, 0)


if __name__ == "__main__":
    unittest.main()
