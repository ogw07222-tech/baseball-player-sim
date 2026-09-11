import types
import unittest

from src import config
from src.career import CareerEngine
from src.persistence import deserialize_game, serialize_game
from src.player import InjuryStatus, Player
from src.production_advance import ProductionAdvanceService, SeasonCompleteError
from src.rng import RNG
from src.stats import PlayerStats


def make_engine(seed: int = 9101) -> CareerEngine:
    team = str(config.KBO_TEAMS[0]["name"])
    player = Player(
        name="Source Fact User",
        age=24,
        stats=PlayerStats(100, 100, 100, 100, 100, 100, 100, 100, 100, 100),
        position="SS",
        team=team,
        roster_level="FARM",
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


def start_clean(engine: CareerEngine):
    session = engine.start_pro_season()
    engine.drain_source_facts()
    return session


def fact_dicts(summary):
    return [fact.as_dict() for fact in summary.source_facts]


def force_roster_roundtrip(engine: CareerEngine) -> None:
    def reconsider(self, session):
        if session.games_completed == 10 and session.current_level == "FARM":
            before = session.current_level
            session.current_level = "FIRST"
            self.player.roster_level = "FIRST"
            self._record_roster_transition(session, before, session.current_level)
        elif session.games_completed == 20 and session.current_level == "FIRST":
            before = session.current_level
            session.current_level = "FARM"
            self.player.roster_level = "FARM"
            self._record_roster_transition(session, before, session.current_level)
    engine._reconsider_roster = types.MethodType(reconsider, engine)


class CareerSourceFactTests(unittest.TestCase):
    def test_one_roster_transition_is_authoritative_fact(self):
        engine = make_engine()
        session = start_clean(engine)
        session.current_level = "FARM"
        engine.player.roster_level = "FARM"
        session.games_completed = 9
        service = ProductionAdvanceService(engine)
        service.state.current_date = service.schedule.dates[8]
        force_roster_roundtrip(engine)
        summary = service.advance_one_game()
        promotions = [f for f in fact_dicts(summary) if f["fact_type"] == "roster_promotion"]
        self.assertEqual(len(promotions), 1)
        fact = promotions[0]
        self.assertEqual(fact["game_number"], 10)
        self.assertEqual(fact["before_state"], {"roster_level": "FARM"})
        self.assertEqual(fact["after_state"], {"roster_level": "FIRST"})
        self.assertEqual(fact["existing_history_kind"], "career_history")
        self.assertTrue(str(fact["existing_dedupe_key"]).startswith("roster:"))
        self.assertIn("player_id", fact)
        self.assertIn("team_id", fact)
        self.assertIn("state_delta", fact)
        self.assertNotIn("title", fact)
        self.assertNotIn("summary", fact)
        self.assertNotIn("importance", fact)

    def test_multiple_transition_facts_same_week_are_retained(self):
        engine = make_engine(9102)
        session = start_clean(engine)
        session.current_level = "FARM"
        engine.player.roster_level = "FARM"
        session.games_completed = 9
        engine.player.injury = InjuryStatus("test", "경미", 1)
        service = ProductionAdvanceService(engine)
        service.state.current_date = service.schedule.dates[8]
        force_roster_roundtrip(engine)
        summary = service.advance_one_week()
        types_seen = [f.fact_type for f in summary.source_facts]
        self.assertIn("injury_recovery_completed", types_seen)
        self.assertIn("roster_promotion", types_seen)

    def test_farm_first_farm_same_month_preserves_both_transitions(self):
        engine = make_engine(9103)
        session = start_clean(engine)
        session.current_level = "FARM"
        engine.player.roster_level = "FARM"
        session.games_completed = 9
        service = ProductionAdvanceService(engine)
        service.state.current_date = service.schedule.dates[8]
        force_roster_roundtrip(engine)
        summary = service.advance_one_month()
        roster = [f for f in summary.source_facts if f.fact_type.startswith("roster_")]
        self.assertGreaterEqual(len(roster), 2)
        self.assertEqual([roster[0].fact_type, roster[1].fact_type], ["roster_promotion", "roster_demotion"])
        self.assertEqual(roster[0].game_number, 10)
        self.assertEqual(roster[1].game_number, 20)
        self.assertEqual(engine.player.roster_level, "FARM")

    def test_injury_creation_fact(self):
        engine = make_engine(9104)
        start_clean(engine).current_level = "FIRST"
        engine.player.roster_level = "FIRST"
        engine._play_probability = types.MethodType(lambda self, level: 1.0, engine)
        engine._injury_chance = types.MethodType(lambda self: 1.0, engine)
        summary = ProductionAdvanceService(engine).advance_one_game()
        injuries = [f for f in summary.source_facts if f.fact_type == "injury_created"]
        self.assertEqual(len(injuries), 1)
        self.assertIsNone(injuries[0].before_state["injury"])
        self.assertIsNotNone(injuries[0].after_state["injury"])
        self.assertEqual(injuries[0].existing_history_kind, "injury_history")
        self.assertEqual(injuries[0].persistence_hint, "injury_history")

    def test_recovery_completion_fact(self):
        engine = make_engine(9105)
        start_clean(engine)
        engine.player.injury = InjuryStatus("test", "경미", 1)
        summary = ProductionAdvanceService(engine).advance_one_game()
        recovery = [f for f in summary.source_facts if f.fact_type == "injury_recovery_completed"]
        self.assertEqual(len(recovery), 1)
        self.assertIsNotNone(recovery[0].before_state["injury"])
        self.assertIsNone(recovery[0].after_state["injury"])
        self.assertIsNone(recovery[0].existing_history_kind)
        self.assertIsNone(engine.player.injury)

    def test_save_load_same_actions_produce_same_ordered_source_facts(self):
        direct = make_engine(9106)
        loaded = deserialize_game(serialize_game(direct))
        direct_summary = ProductionAdvanceService(direct).advance_one_week()
        loaded_summary = ProductionAdvanceService(loaded).advance_one_week()
        self.assertEqual(fact_dicts(direct_summary), fact_dicts(loaded_summary))
        self.assertEqual(serialize_game(direct), serialize_game(loaded))

    def test_repeated_same_seed_actions_are_equivalent(self):
        left = make_engine(9111)
        right = make_engine(9111)
        left_summary = ProductionAdvanceService(left).advance_one_month()
        right_summary = ProductionAdvanceService(right).advance_one_month()
        self.assertEqual(fact_dicts(left_summary), fact_dicts(right_summary))
        self.assertEqual(serialize_game(left), serialize_game(right))
        self.assertEqual(left.rng.get_state(), right.rng.get_state())

    def test_ordering_coordinates_are_deterministic(self):
        engine = make_engine(9107)
        start_clean(engine)
        engine.player.injury = InjuryStatus("test", "경미", 1)
        summary = ProductionAdvanceService(engine).advance_one_week()
        coords = [(f.simulated_date, f.game_number, f.local_ordinal, f.fact_type) for f in summary.source_facts]
        self.assertEqual(coords, sorted(coords, key=lambda x: ((x[0].isoformat() if x[0] else ""), -1 if x[1] is None else x[1], x[2], x[3])))
        for fact in summary.source_facts:
            self.assertIsNotNone(fact.simulated_date)
            self.assertGreaterEqual(fact.local_ordinal, 0)

    def test_failed_completed_season_advance_emits_no_fact_or_state_change(self):
        engine = make_engine(9108)
        session = start_clean(engine)
        session.games_completed = config.KBO_FIRST_TEAM_GAMES
        service = ProductionAdvanceService(engine)
        before = serialize_game(engine)
        before_rng = engine.rng.get_state()
        with self.assertRaises(SeasonCompleteError):
            service.advance_one_week()
        self.assertEqual(before, serialize_game(engine))
        self.assertEqual(before_rng, engine.rng.get_state())
        self.assertEqual(engine.drain_source_facts(), ())

    def test_partial_period_near_season_end_only_emits_committed_game_coordinates(self):
        engine = make_engine(9109)
        session = start_clean(engine)
        session.games_completed = config.KBO_FIRST_TEAM_GAMES - 1
        engine.player.injury = InjuryStatus("test", "경미", 1)
        service = ProductionAdvanceService(engine)
        service.state.current_date = service.schedule.dates[-2]
        summary = service.advance_one_week()
        self.assertEqual(summary.games_played, 1)
        self.assertTrue(service.season_complete)
        self.assertTrue(all(f.game_number == config.KBO_FIRST_TEAM_GAMES for f in summary.source_facts))
        self.assertTrue(all(f.simulated_date == service.schedule.dates[-1] for f in summary.source_facts))

    def test_lifecycle_finalization_exposes_growth_and_finalized_facts(self):
        engine = make_engine(9110)
        session = start_clean(engine)
        session.games_completed = config.KBO_FIRST_TEAM_GAMES
        session.record.first_team.PA = 250
        session.record.first_team.G = 80
        service = ProductionAdvanceService(engine)
        result = service.finalize_season()
        types_seen = [f.fact_type for f in result.source_facts]
        self.assertIn("season_growth", types_seen)
        self.assertIn("season_finalized", types_seen)
        self.assertEqual(types_seen.count("season_finalized"), 1)


if __name__ == "__main__":
    unittest.main()
