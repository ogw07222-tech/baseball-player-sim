from __future__ import annotations

import json
import types
import unittest
from datetime import date

from src import config
from src.career import CareerEngine
from src.career_source_facts import CareerSourceFact
from src.event_timeline import (
    canonical_event_from_source_fact,
    canonical_timeline_for_advance,
    canonical_timeline_from_source_facts,
)
from src.persistence import deserialize_game, serialize_game
from src.player import InjuryStatus, Player
from src.production_advance import ProductionAdvanceService
from src.rng import RNG
from src.stats import PlayerStats
from src.time_advance import AdvanceResultViewModel, CareerEventSummary


def fact(
    fact_type: str,
    *,
    game_number: int | None = 1,
    simulated_date: date | None = date(2026, 4, 1),
    phase: str = "post_game",
    local_ordinal: int = 0,
    before: dict[str, object] | None = None,
    after: dict[str, object] | None = None,
    delta: dict[str, object] | None = None,
    history: str | None = None,
    dedupe: str | None = None,
) -> CareerSourceFact:
    return CareerSourceFact(
        fact_type=fact_type,
        season=2026,
        game_number=game_number,
        simulated_date=simulated_date,
        phase=phase,
        local_ordinal=local_ordinal,
        player_id="player-1",
        team_id="team-1",
        before_state=before or {},
        after_state=after or {},
        state_delta=delta or {},
        existing_history_kind=history,
        existing_dedupe_key=dedupe,
        persistence_hint=history,
    )


def make_engine(seed: int = 42001) -> CareerEngine:
    team = str(config.KBO_TEAMS[0]["name"])
    player = Player(
        name="Canonical User",
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


class CanonicalSourceFactNormalizationTests(unittest.TestCase):
    def test_no_source_facts_is_empty(self):
        self.assertEqual(canonical_timeline_from_source_facts((), source_command="week"), ())
        self.assertEqual(canonical_timeline_for_advance(source_facts=(), gameplay_events=(), source_command="week", season=2026), ())

    def test_single_roster_promotion(self):
        source = fact(
            "roster_promotion",
            before={"roster_level": "FARM"},
            after={"roster_level": "FIRST"},
            delta={"roster_level": {"before": "FARM", "after": "FIRST"}},
            history="career_history",
            dedupe="roster:2026:1:FARM>FIRST",
        )
        event = canonical_event_from_source_fact(source, source_command="next_game")
        self.assertEqual(event.category, "roster")
        self.assertEqual(event.title, "1군 등록")
        self.assertEqual(event.persistence, "career_history")
        self.assertEqual(event.dedupe_key, "roster:2026:1:FARM>FIRST")
        self.assertIn(event.dedupe_key, event.event_id)

    def test_farm_first_farm_same_week_preserves_both(self):
        facts = (
            fact("roster_promotion", game_number=10, local_ordinal=0, before={"roster_level": "FARM"}, after={"roster_level": "FIRST"}, history="career_history", dedupe="roster:2026:10:FARM>FIRST"),
            fact("roster_demotion", game_number=12, simulated_date=date(2026, 4, 3), local_ordinal=0, before={"roster_level": "FIRST"}, after={"roster_level": "FARM"}, history="career_history", dedupe="roster:2026:12:FIRST>FARM"),
        )
        timeline = canonical_timeline_from_source_facts(facts, source_command="week")
        self.assertEqual([event.event_type for event in timeline], ["roster_promotion", "roster_demotion"])
        self.assertEqual([event.sequence for event in timeline], [0, 1])

    def test_first_team_debut(self):
        event = canonical_event_from_source_fact(
            fact("first_team_debut", history="career_history", dedupe="career:first_team_debut"),
            source_command="next_game",
        )
        self.assertEqual(event.title, "1군 데뷔")
        self.assertEqual(event.importance, "major")
        self.assertEqual(event.persistence, "career_history")

    def test_injury_created(self):
        injury = {"name": "햄스트링 부상", "severity": "보통", "games_remaining": 20}
        event = canonical_event_from_source_fact(
            fact("injury_created", before={"injury": None}, after={"injury": injury}, delta={"injury": {"before": None, "after": injury}}, history="injury_history", dedupe="injury_history:2026:0"),
            source_command="next_game",
        )
        self.assertEqual(event.category, "injury")
        self.assertEqual(event.injury_effect["after"], injury)
        self.assertEqual(event.persistence, "injury_history")

    def test_recovery_completion_is_transient_only(self):
        injury = {"name": "test", "severity": "경미", "games_remaining": 1}
        event = canonical_event_from_source_fact(
            fact("injury_recovery_completed", before={"injury": injury}, after={"injury": None}, delta={"injury": {"before": injury, "after": None}}),
            source_command="week",
        )
        self.assertEqual(event.title, "회복 완료")
        self.assertEqual(event.persistence, "transient")
        self.assertIsNone(event.injury_effect["after"])

    def test_form_transition(self):
        event = canonical_event_from_source_fact(
            fact("form_transition", before={"form": "normal"}, after={"form": "slump"}, delta={"form": {"before": "normal", "after": "slump"}}),
            source_command="next_game",
        )
        self.assertEqual(event.category, "form")
        self.assertEqual(event.summary, "normal → slump")
        self.assertEqual(event.persistence, "transient")

    def test_trait_gain_and_loss(self):
        gained = canonical_event_from_source_fact(
            fact("trait_gained", after={"trait_present": "clutch"}, delta={"trait": {"action": "gained", "trait": "clutch"}}, history="trait_history", dedupe="trait_history:2026:0"),
            source_command="lifecycle",
        )
        lost = canonical_event_from_source_fact(
            fact("trait_lost", local_ordinal=1, before={"trait_present": "volatile"}, delta={"trait": {"action": "lost", "trait": "volatile"}}, history="trait_history", dedupe="trait_history:2026:1"),
            source_command="lifecycle",
        )
        self.assertEqual(gained.trait_changes, ("gained:clutch",))
        self.assertEqual(lost.trait_changes, ("lost:volatile",))
        self.assertEqual(gained.persistence, "trait_history")

    def test_event_rating_change(self):
        event = canonical_event_from_source_fact(
            fact("event_rating_change", delta={"rating_deltas": {"contact": 2, "power": -1}}, history="event_history", dedupe="event_history:2026:4"),
            source_command="next_game",
        )
        self.assertEqual(event.rating_changes, {"contact": 2, "power": -1})
        self.assertEqual(event.persistence, "event_history")

    def test_season_growth(self):
        event = canonical_event_from_source_fact(
            fact("season_growth", game_number=144, phase="lifecycle", before={"age": 24, "ability": 100.0}, after={"age": 25, "ability": 103.0}, delta={"rating_deltas": {"contact": 2, "power": 1}}, history="growth_history", dedupe="growth_history:2026:0"),
            source_command="lifecycle",
        )
        self.assertEqual(event.category, "development")
        self.assertEqual(event.rating_changes, {"contact": 2, "power": 1})
        self.assertEqual(event.persistence, "growth_history")

    def test_season_finalized(self):
        event = canonical_event_from_source_fact(
            fact("season_finalized", game_number=144, phase="lifecycle", before={"season": 2026, "age": 24}, after={"season": 2027, "age": 25}, delta={"year": {"before": 2026, "after": 2027}}),
            source_command="lifecycle",
        )
        self.assertEqual(event.category, "lifecycle")
        self.assertEqual(event.title, "시즌 종료")
        self.assertEqual(event.persistence, "transient")

    def test_same_date_game_uses_phase_ordinal_then_event_id(self):
        facts = (
            fact("form_transition", phase="post_game", local_ordinal=2, before={"form": "normal"}, after={"form": "hot"}),
            fact("roster_promotion", phase="post_game", local_ordinal=1, before={"roster_level": "FARM"}, after={"roster_level": "FIRST"}, history="career_history", dedupe="roster:1"),
            fact("first_team_debut", phase="post_game", local_ordinal=3, history="career_history", dedupe="debut"),
        )
        timeline = canonical_timeline_from_source_facts(facts, source_command="next_game")
        self.assertEqual([event.event_type for event in timeline], ["roster_promotion", "form_transition", "first_team_debut"])
        self.assertEqual([event.sequence for event in timeline], [0, 1, 2])

    def test_same_durable_row_can_emit_distinct_fact_types_without_collapse(self):
        shared = "event_history:2026:7"
        timeline = canonical_timeline_from_source_facts(
            (
                fact("injury_created", local_ordinal=0, after={"injury": {"name": "test", "severity": "경미", "games_remaining": 2}}, history="event_history", dedupe=shared),
                fact("event_rating_change", local_ordinal=1, delta={"rating_deltas": {"contact": 1}}, history="event_history", dedupe=shared),
            ),
            source_command="next_game",
        )
        self.assertEqual(len(timeline), 2)
        self.assertTrue(all(event.dedupe_key == shared for event in timeline))
        self.assertEqual(len({event.event_id for event in timeline}), 2)

    def test_transient_gameplay_adapter_is_deterministic_and_not_persistent(self):
        raw = (CareerEventSummary(date(2026, 4, 1), "game", "WALKOFF"),)
        first = canonical_timeline_for_advance(source_facts=(), gameplay_events=raw, source_command="next_game", season=2026)
        second = canonical_timeline_for_advance(source_facts=(), gameplay_events=raw, source_command="next_game", season=2026)
        self.assertEqual([event.as_dict() for event in first], [event.as_dict() for event in second])
        self.assertEqual(first[0].category, "gameplay")
        self.assertEqual(first[0].persistence, "transient")


class CanonicalSourceFactProductionTests(unittest.TestCase):
    def test_same_seed_actions_produce_byte_stable_canonical_list(self):
        left = make_engine(43001)
        right = make_engine(43001)
        left_summary = ProductionAdvanceService(left).advance_one_week()
        right_summary = ProductionAdvanceService(right).advance_one_week()
        left_events = AdvanceResultViewModel.from_summary(left_summary).as_dict()["notable_events"]
        right_events = AdvanceResultViewModel.from_summary(right_summary).as_dict()["notable_events"]
        self.assertEqual(
            json.dumps(left_events, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
            json.dumps(right_events, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
        )

    def test_projection_does_not_append_or_mutate_durable_history(self):
        engine = make_engine(43002)
        engine.player.injury = InjuryStatus("test", "경미", 1)
        summary = ProductionAdvanceService(engine).advance_one_game()
        before = serialize_game(engine)
        first = AdvanceResultViewModel.from_summary(summary).as_dict()["notable_events"]
        second = AdvanceResultViewModel.from_summary(summary).as_dict()["notable_events"]
        self.assertEqual(before, serialize_game(engine))
        self.assertEqual(first, second)
        self.assertFalse(any(entry.get("event_id") == "injury_recovered" for entry in engine.player.career_history))

    def test_save_load_keeps_durable_truth_stable(self):
        engine = make_engine(43003)
        service = ProductionAdvanceService(engine)
        summary = service.advance_one_game()
        AdvanceResultViewModel.from_summary(summary)
        payload = serialize_game(engine)
        restored = deserialize_game(payload)
        self.assertEqual(serialize_game(restored), payload)

    def test_partial_period_near_season_end_only_projects_actual_source_facts(self):
        engine = make_engine(43004)
        session = engine.start_pro_season()
        engine.drain_source_facts()
        session.games_completed = config.KBO_FIRST_TEAM_GAMES - 1
        engine.player.injury = InjuryStatus("test", "경미", 1)
        service = ProductionAdvanceService(engine)
        service.state.current_date = service.schedule.dates[-2]
        summary = service.advance_one_week()
        events = AdvanceResultViewModel.from_summary(summary).as_dict()["notable_events"]
        career_events = [event for event in events if event["category"] != "gameplay"]
        self.assertEqual(summary.games_played, 1)
        self.assertTrue(all(event["game_number"] == config.KBO_FIRST_TEAM_GAMES for event in career_events))

    def test_forced_roundtrip_source_facts_are_not_collapsed_by_viewmodel(self):
        engine = make_engine(43005)
        session = engine.start_pro_season()
        engine.drain_source_facts()
        session.current_level = "FARM"
        engine.player.roster_level = "FARM"
        session.games_completed = 9

        def reconsider(self, active):
            if active.games_completed == 10 and active.current_level == "FARM":
                before = active.current_level
                active.current_level = "FIRST"
                self.player.roster_level = "FIRST"
                self._record_roster_transition(active, before, active.current_level)
            elif active.games_completed == 20 and active.current_level == "FIRST":
                before = active.current_level
                active.current_level = "FARM"
                self.player.roster_level = "FARM"
                self._record_roster_transition(active, before, active.current_level)

        engine._reconsider_roster = types.MethodType(reconsider, engine)
        service = ProductionAdvanceService(engine)
        service.state.current_date = service.schedule.dates[8]
        summary = service.advance_one_month()
        events = AdvanceResultViewModel.from_summary(summary).as_dict()["notable_events"]
        roster = [event["event_type"] for event in events if event["category"] == "roster"]
        self.assertIn("roster_promotion", roster)
        self.assertIn("roster_demotion", roster)
        self.assertLess(roster.index("roster_promotion"), roster.index("roster_demotion"))


if __name__ == "__main__":
    unittest.main()
