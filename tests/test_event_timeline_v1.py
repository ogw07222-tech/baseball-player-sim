from __future__ import annotations

import json
import unittest
from datetime import date

from src import config
from src.career import CareerEngine
from src.career_core import ProSeasonSession
from src.event_timeline import (
    CanonicalEventDTO,
    career_history_events,
    finalize_timeline,
    gameplay_notable_event,
)
from src.persistence import deserialize_game, serialize_game
from src.player import InjuryStatus, Player
from src.production_advance import ProductionAdvanceService
from src.records import SeasonRecord
from src.rng import RNG
from src.stats import PlayerStats
from src.time_advance import AdvanceResultViewModel


def make_player(name: str = "Timeline User") -> Player:
    team = str(config.KBO_TEAMS[0]["name"])
    return Player(
        name=name,
        age=24,
        stats=PlayerStats(
            contact=100,
            power=100,
            discipline=100,
            speed=100,
            defense=100,
            throwing=100,
            stamina=100,
            durability=100,
            mentality=100,
            talent=100,
        ),
        position="SS",
        team=team,
        roster_level="FARM",
    )


def make_career(seed: int = 20260911) -> CareerEngine:
    player = make_player()
    player.draft_info = {
        "team": player.team,
        "round": 1,
        "pick": 1,
        "status": "지명",
        "scouting_score": 110.0,
        "scouted_talent": 100,
    }
    engine = CareerEngine(player, RNG(seed))
    engine.phase = "PRO"
    return engine


class CanonicalEventContractTests(unittest.TestCase):
    def test_no_event_period_is_empty(self):
        self.assertEqual(finalize_timeline([], source_command="week"), ())

    def test_same_day_events_sort_dedupe_and_sequence(self):
        common = dict(
            occurred_at="2026-04-10",
            season=2026,
            game_number=7,
            sequence=-1,
            importance="normal",
            player_id=None,
            team_id="T",
            related_entity_ids=(),
            state_effects=None,
            rating_changes=None,
            injury_effect=None,
            trait_changes=(),
            source_command=None,
            presentation_priority=50,
            persistence="transient",
        )
        events = [
            CanonicalEventDTO(event_id="post", event_type="form_changed", category="form", title="post", summary="post", dedupe_key="post", phase="post_game", source_ordinal=0, **common),
            CanonicalEventDTO(event_id="pre", event_type="first_team_callup", category="roster", title="pre", summary="pre", dedupe_key="pre", phase="pre_game", source_ordinal=0, persistence="career_history", **{k:v for k,v in common.items() if k != "persistence"}),
            CanonicalEventDTO(event_id="game", event_type="gameplay_notable", category="gameplay", title="game", summary="game", dedupe_key="game", phase="in_game", source_ordinal=0, **common),
            CanonicalEventDTO(event_id="post-duplicate", event_type="form_changed", category="form", title="duplicate", summary="duplicate", dedupe_key="post", phase="post_game", source_ordinal=1, **common),
        ]
        timeline = finalize_timeline(events, source_command="week")
        self.assertEqual([event.event_id for event in timeline], ["pre", "game", "post"])
        self.assertEqual([event.sequence for event in timeline], [0, 1, 2])
        self.assertTrue(all(event.source_command == "week" for event in timeline))

    def test_farm_first_farm_round_trip_is_preserved(self):
        entries = [
            {
                "event_id": "first_team_callup",
                "year": 2026,
                "game_number": 41,
                "kind": "roster",
                "importance": "major",
                "dedupe_key": "roster:2026:41:FARM>FIRST",
                "team": "T",
                "facts": {"from_level": "FARM", "to_level": "FIRST"},
                "news": {"headline": "콜업", "body": "FARM→FIRST"},
            },
            {
                "event_id": "farm_demotion",
                "year": 2026,
                "game_number": 42,
                "kind": "roster",
                "importance": "normal",
                "dedupe_key": "roster:2026:42:FIRST>FARM",
                "team": "T",
                "facts": {"from_level": "FIRST", "to_level": "FARM"},
                "news": {"headline": "강등", "body": "FIRST→FARM"},
            },
        ]
        events = career_history_events(entries, occurred_at=date(2026, 5, 1), current_game_number=42)
        timeline = finalize_timeline(events, source_command="week")
        self.assertEqual([e.event_type for e in timeline], ["first_team_callup", "farm_demotion"])
        self.assertEqual(len({e.dedupe_key for e in timeline}), 2)

    def test_gameplay_marker_is_transient_and_deterministic(self):
        first = gameplay_notable_event(message="WALKOFF", occurred_at=date(2026, 4, 1), season=2026, game_number=1, ordinal=0, team_id="T")
        second = gameplay_notable_event(message="WALKOFF", occurred_at=date(2026, 4, 1), season=2026, game_number=1, ordinal=0, team_id="T")
        self.assertEqual(first.as_dict(), second.as_dict())
        self.assertEqual(first.persistence, "transient")
        self.assertEqual(first.event_id, "game:2026:1:in_game:0:walkoff")


class ProductionTimelineIntegrationTests(unittest.TestCase):
    def test_recovery_persists_exactly_once_and_survives_save_load(self):
        engine = make_career(7001)
        engine.player.injury = InjuryStatus("햄스트링 부상", "보통", 1)
        engine.current_session = ProSeasonSession(
            engine.year,
            SeasonRecord(engine.year, engine.player.age, engine.player.team or ""),
            0,
            "FARM",
        )
        service = ProductionAdvanceService(engine)
        summary = service.advance_one_game()
        recovery = [event for event in summary.major_events if getattr(event, "event_type", None) == "injury_recovered"]
        self.assertEqual(len(recovery), 1)
        self.assertEqual(recovery[0].persistence, "career_history")
        self.assertEqual(sum(entry.get("event_id") == "injury_recovered" for entry in engine.player.career_history), 1)

        restored = deserialize_game(serialize_game(engine))
        self.assertEqual(restored.player.career_history, engine.player.career_history)
        ProductionAdvanceService(restored).advance_one_game()
        self.assertEqual(sum(entry.get("event_id") == "injury_recovered" for entry in restored.player.career_history), 1)

    def test_same_seed_same_actions_produce_byte_stable_timeline_facts(self):
        a = make_career(8002)
        b = make_career(8002)
        sa = ProductionAdvanceService(a).advance_one_week()
        sb = ProductionAdvanceService(b).advance_one_week()
        pa = AdvanceResultViewModel.from_summary(sa).as_dict()["notable_events"]
        pb = AdvanceResultViewModel.from_summary(sb).as_dict()["notable_events"]
        self.assertEqual(
            json.dumps(pa, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
            json.dumps(pb, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
        )

    def test_week_and_month_sequences_are_dense_and_ordered(self):
        engine = make_career(9003)
        service = ProductionAdvanceService(engine)
        week = service.advance_one_week()
        self.assertEqual([event.sequence for event in week.major_events], list(range(len(week.major_events))))
        month = service.advance_one_month()
        self.assertEqual([event.sequence for event in month.major_events], list(range(len(month.major_events))))
        self.assertTrue(all(event.source_command == "week" for event in week.major_events))
        self.assertTrue(all(event.source_command == "month" for event in month.major_events))

    def test_partial_period_near_season_end_stops_at_last_game(self):
        engine = make_career(10004)
        session = ProSeasonSession(
            engine.year,
            SeasonRecord(engine.year, engine.player.age, engine.player.team or ""),
            config.KBO_FIRST_TEAM_GAMES - 1,
            "FARM",
        )
        engine.current_session = session
        service = ProductionAdvanceService(engine)
        summary = service.advance_one_week()
        self.assertEqual(summary.games_played, 1)
        self.assertEqual(engine.current_session.games_completed, config.KBO_FIRST_TEAM_GAMES)
        self.assertEqual([event.sequence for event in summary.major_events], list(range(len(summary.major_events))))


if __name__ == "__main__":
    unittest.main()
