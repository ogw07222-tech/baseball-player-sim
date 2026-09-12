from __future__ import annotations

import json
import unittest
from datetime import date

from src.career_source_facts import CareerSourceFact
from src.event_timeline import (
    CAREER_STORY_FILTER_CATEGORIES,
    FUTURE_EVENT_NAMESPACE,
    IMPORTANCE_LEVELS,
    canonical_event_from_source_fact,
    canonical_timeline_for_advance,
    canonical_timeline_from_source_facts,
    gameplay_notable_event,
    presentation_for_source_fact,
)
from src.rng import RNG
from src.time_advance import CareerEventSummary


def fact(
    fact_type: str,
    *,
    game_number: int | None = 10,
    simulated_date: date | None = date(2026, 4, 11),
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


class EventPresentationV2Tests(unittest.TestCase):
    def test_same_input_is_byte_stable(self):
        source = fact(
            "roster_promotion",
            before={"roster_level": "FARM"},
            after={"roster_level": "FIRST"},
            history="career_history",
            dedupe="roster:2026:10:FARM>FIRST",
        )
        left = canonical_event_from_source_fact(source, source_command="week").as_dict()
        right = canonical_event_from_source_fact(source, source_command="week").as_dict()
        self.assertEqual(
            json.dumps(left, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
            json.dumps(right, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
        )

    def test_presentation_consumes_no_simulation_rng(self):
        rng = RNG(9911)
        before = rng.get_state()
        canonical_event_from_source_fact(
            fact("form_transition", before={"form": "normal"}, after={"form": "slump"}),
            source_command="next_game",
        )
        presentation_for_source_fact(
            fact("trait_gained", after={"trait_present": "clutch"})
        )
        self.assertEqual(before, rng.get_state())

    def test_importance_policy_is_consistent(self):
        self.assertEqual(IMPORTANCE_LEVELS, ("minor", "normal", "major", "career-defining"))
        promotion = canonical_event_from_source_fact(fact("roster_promotion"), source_command="next_game")
        form = canonical_event_from_source_fact(
            fact("form_transition", before={"form": "normal"}, after={"form": "hot"}),
            source_command="next_game",
        )
        debut = canonical_event_from_source_fact(fact("first_team_debut"), source_command="next_game")
        minor_injury = canonical_event_from_source_fact(
            fact("injury_created", after={"injury": {"name": "타박상", "severity": "경미", "games_remaining": 2}}),
            source_command="next_game",
        )
        major_injury = canonical_event_from_source_fact(
            fact("injury_created", local_ordinal=1, after={"injury": {"name": "무릎 인대 부상", "severity": "중상", "games_remaining": 90}}),
            source_command="next_game",
        )
        self.assertEqual(promotion.importance, "normal")
        self.assertEqual(form.importance, "minor")
        self.assertEqual(debut.importance, "major")
        self.assertEqual(minor_injury.importance, "minor")
        self.assertEqual(major_injury.importance, "major")
        self.assertNotIn("career-defining", {promotion.importance, form.importance, debut.importance, minor_injury.importance, major_injury.importance})

    def test_deterministic_template_uses_only_authoritative_metadata(self):
        injury = {"name": "햄스트링 부상", "severity": "보통", "games_remaining": 20}
        event = canonical_event_from_source_fact(
            fact("injury_created", after={"injury": injury}),
            source_command="week",
        )
        self.assertEqual(event.title, "부상 발생")
        self.assertEqual(event.summary, "햄스트링 부상 / 보통 / 잔여 20경기")

    def test_multiple_same_category_events_are_preserved(self):
        timeline = canonical_timeline_from_source_facts(
            (
                fact("roster_promotion", game_number=10, local_ordinal=0, history="career_history", dedupe="roster:p"),
                fact("roster_demotion", game_number=12, simulated_date=date(2026, 4, 13), local_ordinal=0, history="career_history", dedupe="roster:d"),
            ),
            source_command="week",
        )
        self.assertEqual([event.event_type for event in timeline], ["roster_promotion", "roster_demotion"])
        self.assertEqual([event.sequence for event in timeline], [0, 1])

    def test_multi_event_same_game_keeps_each_dto(self):
        source_facts = (
            fact("first_team_debut", local_ordinal=0, history="career_history", dedupe="career:first_team_debut"),
            fact("injury_created", local_ordinal=1, after={"injury": {"name": "타박상", "severity": "경미", "games_remaining": 2}}, history="injury_history", dedupe="injury:1"),
            fact("trait_gained", local_ordinal=2, after={"trait_present": "clutch"}, delta={"trait": {"action": "gained", "trait": "clutch"}}, history="event_history", dedupe="event:1"),
        )
        gameplay = (CareerEventSummary(date(2026, 4, 11), "game", "FIRST_HIT"),)
        timeline = canonical_timeline_for_advance(
            source_facts=source_facts,
            gameplay_events=gameplay,
            source_command="next_game",
            season=2026,
        )
        self.assertEqual(len(timeline), 4)
        self.assertEqual(len({event.event_id for event in timeline}), 4)
        self.assertEqual([event.sequence for event in timeline], list(range(4)))
        self.assertEqual({event.category for event in timeline}, {"gameplay", "roster", "injury", "trait"})

    def test_duplicate_suppression_does_not_collapse_distinct_fact_types(self):
        duplicate = fact("roster_promotion", history="career_history", dedupe="roster:1")
        same_history_other_fact = fact(
            "first_team_debut",
            local_ordinal=1,
            history="career_history",
            dedupe="roster:1",
        )
        timeline = canonical_timeline_from_source_facts(
            (duplicate, duplicate, same_history_other_fact),
            source_command="next_game",
        )
        self.assertEqual([event.event_type for event in timeline], ["roster_promotion", "first_team_debut"])

    def test_durable_and_transient_semantics_remain_separate(self):
        durable = canonical_event_from_source_fact(
            fact("roster_promotion", history="career_history", dedupe="roster:1"),
            source_command="week",
        )
        transient = canonical_event_from_source_fact(
            fact("injury_recovery_completed", before={"injury": {"name": "test", "severity": "경미", "games_remaining": 1}}, after={"injury": None}),
            source_command="week",
        )
        gameplay = gameplay_notable_event(
            occurred_at=date(2026, 4, 11),
            season=2026,
            ordinal=0,
            kind="game",
            message="WALKOFF",
            source_command="week",
            game_number=10,
        )
        self.assertEqual(durable.persistence, "career_history")
        self.assertEqual(transient.persistence, "transient")
        self.assertEqual(gameplay.persistence, "transient")

    def test_empty_events_remain_empty(self):
        self.assertEqual(canonical_timeline_from_source_facts((), source_command="month"), ())
        self.assertEqual(
            canonical_timeline_for_advance(source_facts=(), gameplay_events=(), source_command="month", season=2026),
            (),
        )

    def test_future_namespace_is_reserved_but_not_fabricated(self):
        self.assertEqual(FUTURE_EVENT_NAMESPACE["award"], "award")
        self.assertEqual(FUTURE_EVENT_NAMESPACE["record"], "record")
        self.assertEqual(FUTURE_EVENT_NAMESPACE["trade"], "transaction")
        self.assertEqual(FUTURE_EVENT_NAMESPACE["retirement"], "career")
        with self.assertRaises(ValueError):
            canonical_event_from_source_fact(fact("award_won"), source_command="lifecycle")
        with self.assertRaises(ValueError):
            canonical_event_from_source_fact(fact("career_milestone"), source_command="lifecycle")

    def test_career_story_filter_readiness_does_not_change_dto(self):
        self.assertEqual(CAREER_STORY_FILTER_CATEGORIES["Games"], ("gameplay",))
        self.assertEqual(CAREER_STORY_FILTER_CATEGORIES["Development"], ("development", "form", "trait"))
        self.assertEqual(CAREER_STORY_FILTER_CATEGORIES["Injuries"], ("injury",))
        self.assertEqual(CAREER_STORY_FILTER_CATEGORIES["Roster"], ("roster",))
        self.assertEqual(CAREER_STORY_FILTER_CATEGORIES["Awards"], ("award",))
        self.assertEqual(CAREER_STORY_FILTER_CATEGORIES["Records"], ("record",))
        self.assertEqual(CAREER_STORY_FILTER_CATEGORIES["Transactions"], ("transaction",))
        self.assertEqual(CAREER_STORY_FILTER_CATEGORIES["Career"], ("lifecycle", "career"))


if __name__ == "__main__":
    unittest.main()
