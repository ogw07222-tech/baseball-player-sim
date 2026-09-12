import types
import unittest
from datetime import date

from src import config
from src.career import CareerEngine
from src.persistence import deserialize_game, serialize_game
from src.player import Player
from src.production_advance import ProductionAdvanceService
from src.records import BattingLine
from src.rng import RNG
from src.stats import PlayerStats


def make_engine(seed: int = 12001) -> CareerEngine:
    team = str(config.KBO_TEAMS[0]["name"])
    player = Player(
        name="Nextgen Fact User",
        age=24,
        stats=PlayerStats(115, 115, 110, 100, 100, 100, 100, 100, 100, 100),
        position="SS",
        team=team,
        roster_level="FIRST",
    )
    player.draft_info = {
        "team": team,
        "round": 1,
        "pick": 1,
        "status": "지명",
        "scouting_score": 120.0,
        "scouted_talent": 110,
    }
    engine = CareerEngine(player, RNG(seed))
    engine.phase = "PRO"
    session = engine.start_pro_season()
    session.current_level = "FIRST"
    player.roster_level = "FIRST"
    engine.drain_source_facts()
    return engine


def milestones(facts):
    return [fact for fact in facts if fact.fact_type == "career_milestone_reached"]


class NextGenerationCareerSourceFactTests(unittest.TestCase):
    def test_first_milestones_emit_exact_once(self):
        engine = make_engine()
        session = engine.current_session
        self.assertIsNotNone(session)
        engine.begin_source_fact_capture(date(2026, 4, 1), "post_game")
        before = BattingLine()
        after = BattingLine(H=1, HR=1, RBI=1)
        session.games_completed = 1
        engine.emit_batting_milestone_facts(before, after, session)
        facts = milestones(engine.drain_source_facts())
        self.assertEqual(
            [f.state_delta["milestone_key"] for f in facts],
            ["career_first_hit", "career_first_home_run", "career_first_rbi"],
        )
        self.assertEqual([f.local_ordinal for f in facts], [0, 1, 2])
        engine.begin_source_fact_capture(date(2026, 4, 2), "post_game")
        engine.emit_batting_milestone_facts(after, BattingLine(H=2, HR=1, RBI=1), session)
        self.assertEqual(milestones(engine.drain_source_facts()), [])

    def test_threshold_crossing_exact_once_and_no_skipped_threshold(self):
        engine = make_engine(12002)
        session = engine.current_session
        self.assertIsNotNone(session)
        session.games_completed = 40
        engine.begin_source_fact_capture(date(2026, 5, 20), "post_game")
        before = BattingLine(H=99, HR=99)
        after = BattingLine(H=101, HR=100)
        engine.emit_batting_milestone_facts(before, after, session)
        facts = milestones(engine.drain_source_facts())
        self.assertEqual(
            [f.state_delta["milestone_key"] for f in facts],
            ["career_hits_100", "career_home_runs_100"],
        )
        self.assertEqual([f.state_delta["milestone_value"] for f in facts], [100, 100])
        engine.begin_source_fact_capture(date(2026, 5, 21), "post_game")
        engine.emit_batting_milestone_facts(after, BattingLine(H=103, HR=101), session)
        self.assertEqual(milestones(engine.drain_source_facts()), [])

    def test_month_aggregation_retains_milestone_in_order(self):
        engine = make_engine(12003)
        session = engine.current_session
        self.assertIsNotNone(session)
        session.record.first_team.H = 99
        session.record.first_team.AB = 300
        session.record.first_team.PA = 330
        engine._play_probability = types.MethodType(lambda self, level: 1.0, engine)
        summary = ProductionAdvanceService(engine).advance_one_month()
        facts = list(summary.source_facts)
        hit100 = [f for f in facts if f.fact_type == "career_milestone_reached" and f.state_delta.get("milestone_key") == "career_hits_100"]
        self.assertEqual(len(hit100), 1)
        coords = [(f.simulated_date, f.game_number, f.local_ordinal) for f in facts]
        self.assertEqual(coords, sorted(coords, key=lambda x: ((x[0].isoformat() if x[0] else ""), -1 if x[1] is None else x[1], x[2])))

    def test_save_load_and_same_seed_actions_have_same_milestones(self):
        left = make_engine(12004)
        left.current_session.record.first_team.H = 99
        left.current_session.record.first_team.AB = 300
        left.current_session.record.first_team.PA = 330
        left._play_probability = types.MethodType(lambda self, level: 1.0, left)
        loaded = deserialize_game(serialize_game(left))
        loaded._play_probability = types.MethodType(lambda self, level: 1.0, loaded)
        a = ProductionAdvanceService(left).advance_one_month()
        b = ProductionAdvanceService(loaded).advance_one_month()
        self.assertEqual([f.as_dict() for f in a.source_facts], [f.as_dict() for f in b.source_facts])
        self.assertEqual(serialize_game(left), serialize_game(loaded))
        self.assertEqual(left.rng.get_state(), loaded.rng.get_state())

    def test_awards_emit_at_authoritative_finalization_point(self):
        engine = make_engine(12005)
        session = engine.current_session
        session.games_completed = config.KBO_FIRST_TEAM_GAMES
        session.record.first_team.PA = 500
        session.record.first_team.AB = 450
        session.record.first_team.H = 160
        session.record.first_team.HR = 35
        session.record.first_team.RBI = 105
        session.record.first_team.G = 130
        engine._determine_awards = types.MethodType(lambda self, record: ["MVP", "골든글러브"], engine)
        result = ProductionAdvanceService(engine).finalize_season()
        awards = [f for f in result.source_facts if f.fact_type == "award_granted"]
        self.assertEqual([f.state_delta["award_key"] for f in awards], ["MVP", "골든글러브"])
        self.assertEqual(len({f.existing_dedupe_key for f in awards}), 2)
        self.assertEqual([row["award"] for row in engine.player.awards[-2:]], ["MVP", "골든글러브"])

    def test_retirement_fact_is_exact_once(self):
        engine = make_engine(12006)
        before_phase = engine.phase
        engine.retire("retirement_rule")
        facts = engine.drain_source_facts()
        retired = [f for f in facts if f.fact_type == "career_retired"]
        self.assertEqual(len(retired), 1)
        self.assertEqual(retired[0].before_state["phase"], before_phase)
        self.assertEqual(retired[0].after_state["phase"], "RETIRED")
        self.assertEqual(retired[0].state_delta["retirement_reason"], "retirement_rule")
        engine.retire("retirement_rule")
        self.assertEqual(engine.drain_source_facts(), ())

    def test_unsupported_team_movement_semantics_do_not_fabricate_facts(self):
        engine = make_engine(12007)
        engine.retire("explicit")
        fact_types = {f.fact_type for f in engine.drain_source_facts()}
        self.assertFalse(fact_types & {"trade", "release", "contract_signed", "free_agency", "team_transfer"})


if __name__ == "__main__":
    unittest.main()
