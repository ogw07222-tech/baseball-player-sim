"""Draft-performance architecture and calibration regressions."""
import statistics
import unittest

from src import config
from src.career import CareerEngine
from src.draft_scoring import (
    CATCHER_EVALUATION_PENDING,
    HITTER_POSITION_AWARE,
    evaluate_hitter_draft,
    score_hitter_performance,
    score_pitcher_performance,
)
from src.player import Player
from src.records import BattingLine
from src.rng import RNG
from src.stats import generate_high_school_npc_stats


class ZeroNoise:
    def gauss(self, _mean, _stddev):
        return 0.0


def line_for_ops_band(level: int) -> BattingLine:
    # Roughly OPS .65 / .82 / .97 / 1.13 with progressively better K outcomes.
    data = (
        (100, 92, 22, 4, 0, 2, 8, 25, 2, 1),
        (100, 90, 25, 5, 0, 4, 10, 20, 4, 1),
        (100, 88, 27, 6, 0, 6, 12, 16, 6, 1),
        (100, 86, 29, 7, 0, 8, 14, 12, 9, 1),
    )[level]
    pa, ab, hits, doubles, triples, hr, bb, so, sb, cs = data
    return BattingLine(PA=pa, AB=ab, H=hits, doubles=doubles, triples=triples, HR=hr, BB=bb, SO=so, SB=sb, CS=cs)


class DraftPerformanceTests(unittest.TestCase):
    def test_player_generation_target_and_npc_separation(self):
        player=[];npc=[]
        positions=config.POSITIONS
        for i in range(3000):
            pos=positions[i%len(positions)]
            player.append(Player.random('P',RNG(10000+i),position=pos).stats.current_ability())
            npc.append(generate_high_school_npc_stats(RNG(50000+i),pos).current_ability())
        pm,ps=statistics.mean(player),statistics.pstdev(player)
        nm,ns=statistics.mean(npc),statistics.pstdev(npc)
        self.assertGreaterEqual(pm,79);self.assertLessEqual(pm,81)
        self.assertGreaterEqual(ps,9);self.assertLessEqual(ps,12)
        self.assertGreaterEqual(nm,68);self.assertLessEqual(nm,72)
        self.assertGreaterEqual(ns,6);self.assertLessEqual(ns,8)
        self.assertGreater(pm,nm);self.assertGreater(ps,ns)

    def test_performance_score_rises_with_high_school_production(self):
        scores=[score_hitter_performance(line_for_ops_band(i),'SS').score for i in range(4)]
        self.assertEqual(scores,sorted(scores))
        self.assertEqual(len(set(round(x,6) for x in scores)),4)

    def test_direct_current_ability_weight_is_zero(self):
        self.assertEqual(config.DRAFT_WEIGHTS['current_ability'],0.0)
        self.assertGreaterEqual(config.DRAFT_WEIGHTS['performance'],.70)

    def test_elite_performance_can_beat_high_ability_poor_performance(self):
        # Ability is deliberately not an input to the draft scoring layer.
        poor=evaluate_hitter_draft(line_for_ops_band(0),'SS',100,100,[],ZeroNoise()).score
        elite=evaluate_hitter_draft(line_for_ops_band(3),'SS',100,100,[],ZeroNoise()).score
        self.assertGreater(elite,poor)

    def test_strong_performance_can_beat_high_projection_mediocre_performance(self):
        projected=evaluate_hitter_draft(line_for_ops_band(1),'SS',160,100,[],ZeroNoise()).score
        performed=evaluate_hitter_draft(line_for_ops_band(3),'SS',100,100,[],ZeroNoise()).score
        self.assertGreater(performed,projected)

    def test_position_aware_weights_are_real(self):
        line=line_for_ops_band(2)
        ss=score_hitter_performance(line,'SS')
        first=score_hitter_performance(line,'1B')
        self.assertEqual(ss.evaluation_mode,HITTER_POSITION_AWARE)
        self.assertEqual(first.evaluation_mode,HITTER_POSITION_AWARE)
        self.assertNotAlmostEqual(ss.score,first.score,places=6)

    def test_catcher_is_explicit_special_case(self):
        self.assertNotIn('C',config.POSITION_PERFORMANCE_WEIGHTS)
        score=score_hitter_performance(line_for_ops_band(2),'C')
        self.assertEqual(score.evaluation_mode,CATCHER_EVALUATION_PENDING)

    def test_pitcher_extension_is_explicitly_pending(self):
        with self.assertRaises(NotImplementedError):score_pitcher_performance(None)

    def test_sample_reliability_shrinks_small_samples(self):
        full=line_for_ops_band(3)
        tiny=BattingLine(PA=10,AB=8,H=4,doubles=1,HR=2,BB=2,SO=1,SB=1)
        full_score=score_hitter_performance(full,'SS')
        tiny_score=score_hitter_performance(tiny,'SS')
        self.assertGreater(full_score.reliability,tiny_score.reliability)
        self.assertLess(abs(tiny_score.score-100),abs(full_score.score-100))

    def test_catcher_career_draft_path_remains_operational(self):
        r=RNG(9876);p=Player.random('C',r,position='C');d=CareerEngine(p,r).evaluate_draft()
        self.assertIn(d.round,(None,1,2,3,4,5,6,7,8,9,10,11))

    def test_draft_seed_is_reproducible(self):
        def run():
            r=RNG(20260905);p=Player.random('D',r,position='SS');return CareerEngine(p,r).evaluate_draft().as_dict()
        self.assertEqual(run(),run())


if __name__=='__main__':unittest.main()
