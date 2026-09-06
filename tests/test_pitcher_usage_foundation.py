import json
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from src import config
from src.career import CareerEngine
from src.persistence import load_game, save_game
from src.pitcher_usage import (
    PitcherAvailability,
    PitcherRole,
    PitcherUsageManager,
    PitcherUsageMember,
)
from src.pitcher_usage_advance import PitcherUsageProductionAdvanceService
from src.pitcher_usage_game_provider import (
    _charged_pitcher_ids,
    _scored_runner_ids,
)
from src.player import Player
from src.rng import RNG
from src.stat_aggregation import PitcherCountingStats
from src.stats import PlayerStats


def members():
    return [
        PitcherUsageMember(f"p{i}", 100 if i != 6 else 120, 100)
        for i in range(12)
    ]


def setup_switch_state():
    mgr = PitcherUsageManager()
    ms = members()
    team = mgr.ensure_team("T", ms)
    start = date(2026, 4, 1)
    for index in range(5):
        day = start + timedelta(days=index * 5)
        mgr.record_outing(
            "T",
            ms[0],
            day,
            PitcherRole.STARTER.value,
            started=True,
            BF=30,
            outs=12,
            H=12,
            R=8,
            HR=2,
            BB=5,
            SO=2,
        )
        mgr.record_outing(
            "T",
            ms[6],
            day,
            PitcherRole.MIDDLE_RELIEF.value,
            started=False,
            BF=8,
            outs=6,
            H=1,
            R=0,
            HR=0,
            BB=0,
            SO=4,
        )
    changes = mgr.evaluate_roles(
        "T", ms, start + timedelta(days=24), force=True
    )
    return mgr, ms, team, changes


def make_career(seed=1):
    team = str(config.KBO_TEAMS[0]["name"])
    player = Player(
        name="Usage User",
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


class PitcherUsageFoundationTests(unittest.TestCase):
    def test_starter_can_be_demoted_to_bullpen(self):
        _, _, team, changes = setup_switch_state()
        self.assertTrue(
            any(
                pid == "p0" and old == "starter" and new == "long_relief"
                for pid, old, new in changes
            )
        )
        self.assertEqual(team.pitchers["p0"].current_role, "long_relief")

    def test_reliever_can_be_promoted_to_rotation(self):
        _, _, team, changes = setup_switch_state()
        self.assertTrue(any(pid == "p6" and new == "starter" for pid, _, new in changes))
        self.assertIn("p6", team.rotation)

    def test_role_switch_hysteresis(self):
        mgr, ms, team, _ = setup_switch_state()
        self.assertEqual(
            mgr.evaluate_roles("T", ms, date(2026, 4, 26), force=True), ()
        )
        self.assertFalse(team.pitchers["p0"].can_change_role(date(2026, 4, 26)))

    def test_rotation_respects_rest(self):
        mgr = PitcherUsageManager()
        ms = members()
        team = mgr.ensure_team("T", ms)
        day = date(2026, 4, 1)
        state = team.pitchers["p0"]
        mgr.record_outing(
            "T", ms[0], day, "starter", started=True, BF=25, outs=18
        )
        self.assertFalse(
            mgr.starter_eligible(state, ms[0], day + timedelta(days=4))
        )
        self.assertTrue(
            mgr.starter_eligible(state, ms[0], day + timedelta(days=5))
        )

    def test_reliever_back_to_back_extra_fatigue(self):
        mgr = PitcherUsageManager()
        ms = members()
        team = mgr.ensure_team("T", ms)
        state = team.pitchers["p6"]
        d = date(2026, 4, 1)
        mgr.record_outing(
            "T", ms[6], d, "middle_relief", started=False, BF=4, outs=3, pitches=15
        )
        first = state.fatigue_load + state.recovery_debt
        mgr.record_outing(
            "T",
            ms[6],
            d + timedelta(days=1),
            "middle_relief",
            started=False,
            BF=4,
            outs=3,
            pitches=15,
        )
        self.assertGreater(state.fatigue_load + state.recovery_debt, first)
        self.assertGreater(state.recovery_debt, 0)

    def test_reliever_three_straight_days_heavier_penalty(self):
        mgr = PitcherUsageManager()
        ms = members()
        team = mgr.ensure_team("T", ms)
        state = team.pitchers["p6"]
        d = date(2026, 4, 1)
        debts = []
        for offset in range(3):
            before = state.recovery_debt
            mgr.record_outing(
                "T",
                ms[6],
                d + timedelta(days=offset),
                "middle_relief",
                started=False,
                BF=4,
                outs=3,
                pitches=14,
            )
            debts.append(state.recovery_debt - before)
        self.assertGreater(debts[2], debts[1])

    def test_four_straight_days_normally_unavailable(self):
        mgr = PitcherUsageManager()
        ms = members()
        team = mgr.ensure_team("T", ms)
        state = team.pitchers["p6"]
        d = date(2026, 4, 1)
        for offset in range(3):
            mgr.record_outing(
                "T",
                ms[6],
                d + timedelta(days=offset),
                "middle_relief",
                started=False,
                BF=3,
                outs=3,
                pitches=12,
            )
        self.assertEqual(
            mgr.availability(state, d + timedelta(days=3), ms[6].resilience),
            PitcherAvailability.UNAVAILABLE,
        )

    def test_heavy_back_to_back_usage(self):
        mgr = PitcherUsageManager()
        ms = members()
        team = mgr.ensure_team("T", ms)
        state = team.pitchers["p6"]
        d = date(2026, 4, 1)
        mgr.record_outing(
            "T", ms[6], d, "middle_relief", started=False, BF=9, outs=6, pitches=35
        )
        mgr.record_outing(
            "T",
            ms[6],
            d + timedelta(days=1),
            "middle_relief",
            started=False,
            BF=7,
            outs=5,
            pitches=25,
        )
        self.assertEqual(
            mgr.availability(state, d + timedelta(days=2), ms[6].resilience),
            PitcherAvailability.UNAVAILABLE,
        )

    def test_starter_can_exit_before_sixth(self):
        line = PitcherCountingStats(
            G=1, GS=1, BF=24, outs_pitched=9, H=10, R=6, BB=4
        )
        self.assertTrue(PitcherUsageManager().starter_should_exit(line, 4, 100))

    def test_starter_can_pitch_beyond_sixth(self):
        line = PitcherCountingStats(
            G=1, GS=1, BF=20, outs_pitched=18, H=3, R=0, BB=1
        )
        self.assertFalse(PitcherUsageManager().starter_should_exit(line, 7, 100))

    def test_bullpen_selector_respects_availability(self):
        mgr = PitcherUsageManager()
        ms = members()
        team = mgr.ensure_team("T", ms)
        d = date(2026, 4, 1)
        closer = next(
            pid
            for pid, state in team.pitchers.items()
            if state.current_role == "closer"
        )
        closer_member = next(m for m in ms if m.pitcher_id == closer)
        for offset in range(3):
            mgr.record_outing(
                "T",
                closer_member,
                d + timedelta(days=offset),
                "closer",
                started=False,
                BF=4,
                outs=3,
                pitches=12,
            )
        pick, reason = mgr.select_reliever(
            "T", ms, d + timedelta(days=3), 9, 1, set()
        )
        self.assertNotEqual(pick, closer)
        self.assertIsNone(reason)

    def test_scored_runner_identity_uses_run_delta(self):
        before = {"away:0:A": 0, "away:1:B": 1}
        after = {"away:0:A": 1, "away:1:B": 1}
        self.assertEqual(_scored_runner_ids(before, after), ("away:0:A",))

    def test_inherited_runner_charged_to_original_pitcher(self):
        responsibility = {"away:0:A": "starter"}
        charged = _charged_pitcher_ids(
            ("away:0:A", "away:1:B"),
            responsibility,
            "reliever",
        )
        self.assertEqual(charged, ("starter", "reliever"))
        self.assertEqual(responsibility, {})

    def test_advance_compositional_equivalence_with_pitcher_usage(self):
        bulk_engine = make_career(20260906)
        repeated_engine = make_career(20260906)
        bulk = PitcherUsageProductionAdvanceService(bulk_engine)
        repeated = PitcherUsageProductionAdvanceService(repeated_engine)
        dates = bulk.schedule.game_dates(
            bulk.state.current_date,
            bulk.state.current_date + timedelta(days=7),
        )
        bulk.advance_one_week()
        for _ in dates:
            repeated.advance_one_game()
        self.assertEqual(
            bulk_engine.pitcher_usage_state.as_dict(),
            repeated_engine.pitcher_usage_state.as_dict(),
        )
        self.assertEqual(
            bulk.state.season.as_dict(),
            repeated.state.season.as_dict(),
        )

    def test_save_roundtrip_pitcher_usage_state(self):
        engine = make_career(77)
        service = PitcherUsageProductionAdvanceService(engine)
        service.advance_one_game()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "save.json"
            save_game(path, engine)
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertIn("pitcher_usage_state", payload)
            loaded = load_game(path)
            self.assertEqual(
                engine.pitcher_usage_state.as_dict(),
                loaded.pitcher_usage_state.as_dict(),
            )
            payload.pop("pitcher_usage_state", None)
            old_path = Path(tmp) / "old.json"
            old_path.write_text(json.dumps(payload), encoding="utf-8")
            old = load_game(old_path)
            self.assertFalse(hasattr(old, "pitcher_usage_state"))


if __name__ == "__main__":
    unittest.main()
