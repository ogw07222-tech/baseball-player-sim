import unittest

from src.career import CareerEngine
from src.player import Player
from src.rng import RNG


class SeasonSessionRegressionTests(unittest.TestCase):
    def test_finished_manual_session_is_preserved_until_finalization(self):
        rng = RNG(321)
        player = Player.random("A", rng, "SS", "R/R", 1)
        engine = CareerEngine(player, rng)
        engine.evaluate_draft()

        session = engine.advance_pro_games(144)
        before = session.record.as_dict()
        self.assertTrue(session.finished)

        record, _ = engine.finish_pro_season()
        self.assertEqual(before, record.as_dict())
        self.assertEqual(1, len(player.seasons))


if __name__ == "__main__":
    unittest.main()
