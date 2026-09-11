import unittest
from datetime import timedelta

from src import config
from src.career import CareerEngine
from src.persistence import deserialize_game, serialize_game
from src.player import Player
from src.production_advance import ProductionAdvanceService, SeasonCompleteError
from src.rng import RNG
from src.stats import PlayerStats


def make_engine(seed: int) -> CareerEngine:
    team = str(config.KBO_TEAMS[0]["name"])
    player = Player(
        name="P1 Advance User",
        age=24,
        stats=PlayerStats(100, 100, 100, 100, 100, 100, 100, 100, 100, 100),
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


def clone_engine(engine: CareerEngine) -> CareerEngine:
    return deserialize_game(serialize_game(engine))


def move_to_game(engine: CareerEngine, completed_games: int) -> ProductionAdvanceService:
    service = ProductionAdvanceService(engine)
    session = engine.start_pro_season()
    session.games_completed = completed_games
    if completed_games:
        service.state.current_date = service.schedule.dates[completed_games - 1]
    return service


class P1CareerAdvanceBreadthTests(unittest.TestCase):
    def assert_engine_equivalent(self, left: CareerEngine, right: CareerEngine) -> None:
        self.assertEqual(serialize_game(left), serialize_game(right))
        self.assertEqual(left.rng.get_state(), right.rng.get_state())

    def test_next_week_is_exact_next_game_composition(self):
        bulk = make_engine(8101)
        repeated = clone_engine(bulk)
        bulk_service = ProductionAdvanceService(bulk)
        repeated_service = ProductionAdvanceService(repeated)

        start = bulk_service.state.current_date
        dates = bulk_service.schedule.game_dates(start, start + timedelta(days=7))
        summary = bulk_service.advance_one_week()
        for _ in dates:
            repeated_service.advance_one_game()

        self.assertEqual(summary.period_type, "WEEK")
        self.assertEqual(summary.games_played, len(dates))
        self.assert_engine_equivalent(bulk, repeated)

    def test_next_month_is_exact_next_game_composition(self):
        bulk = make_engine(8102)
        repeated = clone_engine(bulk)
        bulk_service = ProductionAdvanceService(bulk)
        repeated_service = ProductionAdvanceService(repeated)

        start = bulk_service.state.current_date
        end = start.replace(month=4, day=30)
        dates = bulk_service.schedule.game_dates(start, end)
        summary = bulk_service.advance_one_month()
        for _ in dates:
            repeated_service.advance_one_game()

        self.assertEqual(summary.period_type, "MONTH")
        self.assertEqual(summary.games_played, len(dates))
        self.assert_engine_equivalent(bulk, repeated)

    def test_week_save_load_equivalence(self):
        direct = make_engine(8103)
        resumed = clone_engine(direct)
        direct_summary = ProductionAdvanceService(direct).advance_one_week()
        resumed_summary = ProductionAdvanceService(resumed).advance_one_week()

        self.assertEqual(direct_summary.as_dict(), resumed_summary.as_dict())
        self.assert_engine_equivalent(direct, resumed)

    def test_month_save_load_equivalence(self):
        direct = make_engine(8104)
        resumed = clone_engine(direct)
        direct_summary = ProductionAdvanceService(direct).advance_one_month()
        resumed_summary = ProductionAdvanceService(resumed).advance_one_month()

        self.assertEqual(direct_summary.as_dict(), resumed_summary.as_dict())
        self.assert_engine_equivalent(direct, resumed)

    def test_week_stops_exactly_at_game_144(self):
        engine = make_engine(8105)
        service = move_to_game(engine, config.KBO_FIRST_TEAM_GAMES - 1)
        before_seasons = len(engine.player.seasons)
        before_growth = len(engine.player.growth_history)

        summary = service.advance_one_week()

        self.assertEqual(summary.games_played, 1)
        self.assertEqual(engine.current_session.games_completed, config.KBO_FIRST_TEAM_GAMES)
        self.assertTrue(service.season_complete)
        self.assertEqual(len(engine.player.seasons), before_seasons)
        self.assertEqual(len(engine.player.growth_history), before_growth)

    def test_month_stops_exactly_at_game_144(self):
        engine = make_engine(8106)
        service = move_to_game(engine, config.KBO_FIRST_TEAM_GAMES - 2)

        summary = service.advance_one_month()

        self.assertEqual(summary.games_played, 2)
        self.assertEqual(engine.current_session.games_completed, config.KBO_FIRST_TEAM_GAMES)
        self.assertTrue(service.season_complete)

    def test_completed_season_rejects_all_game_advances_without_rng_or_state_change(self):
        engine = make_engine(8107)
        service = move_to_game(engine, config.KBO_FIRST_TEAM_GAMES)
        before_payload = serialize_game(engine)
        before_rng = engine.rng.get_state()

        for command in (
            service.advance_one_game,
            service.advance_one_week,
            service.advance_one_month,
        ):
            with self.assertRaises(SeasonCompleteError):
                command()
            self.assertEqual(before_payload, serialize_game(engine))
            self.assertEqual(before_rng, engine.rng.get_state())

    def test_completed_period_advance_does_not_finalize_or_start_next_season(self):
        engine = make_engine(8108)
        service = move_to_game(engine, config.KBO_FIRST_TEAM_GAMES)
        age = engine.player.age
        year = engine.year

        with self.assertRaises(SeasonCompleteError):
            service.advance_one_week()

        self.assertEqual(engine.player.age, age)
        self.assertEqual(engine.year, year)
        self.assertEqual(len(engine.player.seasons), 0)
        self.assertEqual(len(engine.player.growth_history), 0)
        self.assertIsNotNone(engine.current_session)
        self.assertTrue(engine.current_session.finished)


if __name__ == "__main__":
    unittest.main()
