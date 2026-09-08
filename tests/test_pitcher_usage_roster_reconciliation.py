import unittest
from datetime import date, timedelta

from src.pitcher_usage import PitcherUsageManager, PitcherUsageMember


def members():
    return [PitcherUsageMember(f"p{i}", 100.0, 100.0) for i in range(12)]


class PitcherUsageRosterReconciliationTests(unittest.TestCase):
    def test_stale_starter_is_pruned_from_active_rotation_and_not_selected(self):
        mgr = PitcherUsageManager()
        ms = members()
        team = mgr.ensure_team("T", ms)
        stale = team.rotation[0]
        team.rotation_index = 0

        active = [m for m in ms if m.pitcher_id != stale]
        picked, _ = mgr.select_starter("T", active, date(2026, 4, 1))

        self.assertNotEqual(picked, stale)
        self.assertNotIn(stale, team.rotation)
        self.assertIn(stale, team.pitchers)

    def test_stale_bullpen_pitcher_is_not_selected_for_relief(self):
        mgr = PitcherUsageManager()
        ms = members()
        team = mgr.ensure_team("T", ms)
        stale = next(
            pid for pid, state in team.pitchers.items()
            if state.current_role == "closer"
        )
        active = [m for m in ms if m.pitcher_id != stale]

        picked, _ = mgr.select_reliever(
            "T", active, date(2026, 4, 1), 9, 1, set()
        )

        self.assertNotEqual(picked, stale)
        self.assertIn(stale, team.pitchers)

    def test_returning_pitcher_preserves_usage_state(self):
        mgr = PitcherUsageManager()
        ms = members()
        team = mgr.ensure_team("T", ms)
        returning = ms[0]
        day = date(2026, 4, 1)
        mgr.record_outing(
            "T", returning, day, "starter", started=True,
            BF=25, outs=18, pitches=80,
        )
        before = team.pitchers[returning.pitcher_id].as_dict()

        active = [m for m in ms if m.pitcher_id != returning.pitcher_id]
        mgr.ensure_team("T", active)
        self.assertIn(returning.pitcher_id, team.pitchers)

        mgr.ensure_team("T", ms)
        after = team.pitchers[returning.pitcher_id].as_dict()
        self.assertEqual(after, before)
        self.assertIn(returning.pitcher_id, team.rotation)

    def test_rotation_index_remains_valid_after_active_roster_pruning(self):
        mgr = PitcherUsageManager()
        ms = members()
        team = mgr.ensure_team("T", ms)
        team.rotation_index = len(team.rotation) - 1
        removed = {team.rotation[0], team.rotation[1]}
        active = [m for m in ms if m.pitcher_id not in removed]

        mgr.ensure_team("T", active)

        self.assertTrue(team.rotation)
        self.assertGreaterEqual(team.rotation_index, 0)
        self.assertLess(team.rotation_index, len(team.rotation))
        self.assertTrue(set(team.rotation).isdisjoint(removed))

    def test_stale_swingman_is_not_used_as_spot_starter(self):
        mgr = PitcherUsageManager()
        ms = members()
        team = mgr.ensure_team("T", ms)
        stale = next(
            pid for pid, state in team.pitchers.items()
            if state.current_role == "swingman"
        )
        active = [m for m in ms if m.pitcher_id != stale]
        on_date = date(2026, 4, 2)

        for pid in list(team.rotation):
            member = next(m for m in ms if m.pitcher_id == pid)
            mgr.record_outing(
                "T", member, on_date - timedelta(days=1), "starter",
                started=True, BF=20, outs=15,
            )

        picked, reason = mgr.select_starter("T", active, on_date)
        self.assertNotEqual(picked, stale)
        if reason == "SPOT_START":
            self.assertIn(picked, {m.pitcher_id for m in active})


if __name__ == "__main__":
    unittest.main()
