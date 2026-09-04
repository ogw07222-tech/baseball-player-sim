import unittest

from src.application.dashboard_service import DashboardService
from src.application.season_service import SeasonService
from src.player import Player
from src.records import BattingLine, SeasonRecord
from src.stats import PlayerStats
from src.traits import trait_from_key


class PresentationAdapterTests(unittest.TestCase):
    def make_player(self) -> Player:
        stats = PlayerStats(contact=112, power=137, discipline=98, speed=89, defense=121, throwing=118, stamina=115, durability=82, mentality=110, talent=125)
        line = BattingLine(G=47, PA=198, AB=176, H=55, doubles=12, triples=1, HR=19, BB=18, SO=32, SB=14, R=28, RBI=61)
        return Player(
            name="김건우",
            age=22,
            stats=stats,
            traits=[trait_from_key("clutch"), trait_from_key("breaking_ball_weakness")],
            team="키움 히어로즈",
            roster_level="FIRST",
            seasons=[SeasonRecord(year=2029, age=22, team="키움 히어로즈", first_team=line)],
            fatigue=34.0,
            form="hot",
        )

    def test_dashboard_view_model_serialization(self):
        player = self.make_player()
        before = player.as_dict()
        vm = DashboardService().build(player, year=2029, progress={"game": 47, "total_games": 144})
        payload = vm.as_dict()
        self.assertEqual(payload["player"]["name"], "김건우")
        self.assertEqual(len(payload["abilities"]), 10)
        self.assertEqual(payload["abilities"][1]["rating"], 137)
        self.assertGreater(payload["season_stats"]["OPS"], 0)
        self.assertEqual(player.as_dict(), before)

    def test_season_view_model_serialization(self):
        player = self.make_player()
        before = player.as_dict()
        vm = SeasonService().build(player, year=2029)
        payload = vm.as_dict()
        self.assertEqual(payload["year"], 2029)
        self.assertEqual(payload["team_name"], "키움 히어로즈")
        self.assertEqual(payload["team_batting"][0]["player"], "김건우")
        self.assertEqual(player.as_dict(), before)


if __name__ == "__main__":
    unittest.main()
