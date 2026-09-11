import ast
import json
import subprocess
import unittest
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

from src import config
from src.growth import GROWABLE_STATS
from src.stat_aggregation import (
    GamePerformance,
    HitterCountingStats,
    PitcherCountingStats,
    SeasonStatLine,
    aggregate_game_performances,
    career_from_seasons,
    pitcher_stats_from_result,
    season_from_games,
)
from src.stats import PlayerStats
from src.time_advance import (
    AdvanceOrchestrator,
    AdvancePipelineState,
    AdvanceResultViewModel,
    ListScheduleProvider,
)


def hitter_line(*, g=1, pa=4, ab=4, h=1, doubles=0, triples=0, hr=0, bb=0, hbp=0, so=1, sb=0, cs=0, r=0, rbi=0, gdp=0, sf=0):
    singles = h - doubles - triples - hr
    return HitterCountingStats(
        G=g, PA=pa, AB=ab, R=r, H=h, singles=singles,
        doubles=doubles, triples=triples, HR=hr, RBI=rbi,
        BB=bb, HBP=hbp, SO=so, SB=sb, CS=cs, GDP=gdp, SF=sf,
    )


def performance(game_date, marker, level="FIRST", team_result=None):
    h = 2 if marker % 2 == 0 else 1
    doubles = 1 if marker % 3 == 0 else 0
    hr = 1 if marker % 5 == 0 else 0
    h = max(h, doubles + hr)
    pa = 4 + (marker % 2)
    ab = pa - (1 if marker % 4 == 0 else 0)
    bb = pa - ab
    line = hitter_line(
        pa=pa, ab=ab, h=h, doubles=doubles, hr=hr, bb=bb,
        so=marker % 2, r=h, rbi=h + hr, sb=int(marker % 3 == 0),
    )
    return GamePerformance(
        game_date=game_date,
        level=level,
        hitter_stats=line,
        team_result=team_result,
        opponent=f"OPP{marker}",
    )


class MappingGameProvider:
    def __init__(self, mapping):
        self.mapping = dict(mapping)

    def advance_game(self, game_date):
        return self.mapping[game_date]


class StatAggregationTests(unittest.TestCase):
    def test_game_hitter_stats_aggregate(self):
        a = hitter_line(pa=5, ab=4, h=2, doubles=1, bb=1, r=1, rbi=2)
        b = hitter_line(pa=4, ab=4, h=1, hr=1, so=2, r=1, rbi=1)
        period = aggregate_game_performances([
            GamePerformance(date(2026, 4, 1), "FIRST", hitter_stats=a),
            GamePerformance(date(2026, 4, 2), "FIRST", hitter_stats=b),
        ])
        total = period.first_team.hitter
        self.assertEqual(total.PA, 9)
        self.assertEqual(total.H, 3)
        self.assertEqual(total.doubles, 1)
        self.assertEqual(total.HR, 1)
        self.assertEqual(total.RBI, 3)

    def test_hitter_hits_decompose(self):
        line = HitterCountingStats(PA=10, AB=9, H=5, singles=2, doubles=1, triples=1, HR=1, BB=1)
        self.assertEqual(line.H, line.singles + line.doubles + line.triples + line.HR)
        with self.assertRaises(ValueError):
            HitterCountingStats(PA=5, AB=5, H=2, singles=2, doubles=1)

    def test_hitter_derived_stats_from_totals(self):
        a = hitter_line(pa=5, ab=4, h=2, doubles=1, bb=1, so=1)
        b = hitter_line(pa=4, ab=3, h=0, bb=1, so=1, sf=0)
        total = a.copy(); total.add(b)
        self.assertAlmostEqual(total.AVG, 2 / 7)
        self.assertAlmostEqual(total.OBP, 4 / 9)
        self.assertAlmostEqual(total.SLG, 3 / 7)
        self.assertAlmostEqual(total.ISO, 1 / 7)
        self.assertNotAlmostEqual(total.AVG, (a.AVG + b.AVG) / 2)

    def test_pitcher_outs_to_ip(self):
        line = PitcherCountingStats(G=1, BF=16, outs_pitched=10, H=4, ER=1, BB=1, SO=5)
        self.assertEqual(line.IP_display, "3.1")
        self.assertAlmostEqual(line.IP, 10 / 3)

    def test_pitcher_era(self):
        line = PitcherCountingStats(G=1, BF=30, outs_pitched=21, H=5, ER=2, BB=2, SO=7)
        self.assertAlmostEqual(line.ERA, 18 / 7)

    def test_pitcher_whip(self):
        line = PitcherCountingStats(G=1, BF=30, outs_pitched=18, H=5, ER=2, BB=3, SO=7)
        self.assertAlmostEqual(line.WHIP, 8 / 6)

    def test_result_adapters_do_not_invent_unsupported_pitcher_stats(self):
        @dataclass
        class ExistingPitchingLine:
            G: int = 1; BF: int = 25; outs: int = 18; H: int = 4
            HR: int = 1; BB: int = 2; SO: int = 8; ER: int = 2
        adapted = pitcher_stats_from_result(ExistingPitchingLine(), started=True)
        self.assertEqual(adapted.GS, 1)
        self.assertEqual(adapted.R, 0)
        self.assertEqual(adapted.W, 0)
        self.assertEqual(adapted.SV, 0)

    def test_period_season_and_career_aggregation(self):
        games_2026 = [
            performance(date(2026, 4, 1), 1, "FIRST"),
            performance(date(2026, 4, 2), 2, "FARM"),
            performance(date(2026, 4, 3), 3, "FIRST"),
        ]
        games_2027 = [performance(date(2027, 4, 1), 4, "FIRST")]
        season_a = season_from_games(games_2026, 2026)
        season_b = season_from_games(games_2027, 2027)
        career = career_from_seasons([season_a, season_b])
        self.assertEqual(season_a.overall.hitter.PA, sum(g.hitter_stats.PA for g in games_2026))
        self.assertEqual(career.overall.hitter.PA, sum(g.hitter_stats.PA for g in games_2026 + games_2027))
        self.assertEqual(career.seasons, 2)

    def test_stat_serialization_round_trip(self):
        season = SeasonStatLine(year=2026)
        season.add_game("FIRST", performance(date(2026, 4, 1), 1).stat_line)
        restored = SeasonStatLine.from_dict(json.loads(json.dumps(season.as_dict())))
        self.assertEqual(season.as_dict(), restored.as_dict())


class AdvancePipelineTests(unittest.TestCase):
    def setUp(self):
        self.start = date(2026, 4, 1)
        self.dates = tuple(self.start + timedelta(days=n) for n in (1, 2, 4, 6, 8, 12, 20, 27))
        self.mapping = {
            game_date: performance(game_date, i + 1, "FIRST" if i % 2 == 0 else "FARM", "W" if i % 3 else "L")
            for i, game_date in enumerate(self.dates)
        }

    def _orchestrator(self):
        return AdvanceOrchestrator(
            AdvancePipelineState(self.start),
            ListScheduleProvider(self.dates),
            MappingGameProvider(self.mapping),
            rating_provider=lambda: {"contact": 100, "power": 95, "speed": 90},
            roster_provider=lambda: "FIRST",
        )

    def test_weekly_aggregation(self):
        orch = self._orchestrator(); summary = orch.advance_one_week()
        expected = [d for d in self.dates if self.start < d <= self.start + timedelta(days=7)]
        self.assertEqual(summary.games_played, len(expected))
        self.assertEqual(summary.player_period_stats.overall.hitter.PA, sum(self.mapping[d].hitter_stats.PA for d in expected))

    def test_monthly_aggregation(self):
        orch = self._orchestrator(); summary = orch.advance_one_month()
        self.assertEqual(summary.games_played, len(self.dates))
        monthly = orch.get_monthly_summary(2026, 4)
        self.assertEqual(monthly.overall.hitter.PA, summary.player_period_stats.overall.hitter.PA)

    def test_season_aggregation(self):
        orch = self._orchestrator(); summary = orch.advance_one_month()
        self.assertEqual(summary.season_after.overall.hitter.PA, summary.player_period_stats.overall.hitter.PA)

    def test_career_aggregation(self):
        orch = self._orchestrator(); orch.advance_one_month()
        self.assertEqual(orch.state.career.overall.hitter.PA, orch.state.season.overall.hitter.PA)

    def test_week_advance_equals_repeated_game_advance(self):
        bulk = self._orchestrator(); repeated = self._orchestrator()
        bulk.advance_one_week(); end = self.start + timedelta(days=7)
        scheduled = [d for d in self.dates if self.start < d <= end]
        for _ in scheduled: repeated.advance_one_game()
        self.assertEqual(bulk.state.season.overall.as_dict(), repeated.state.season.overall.as_dict())

    def test_month_advance_equals_repeated_game_advance(self):
        bulk = self._orchestrator(); repeated = self._orchestrator()
        bulk.advance_one_month()
        for _ in self.dates: repeated.advance_one_game()
        self.assertEqual(bulk.state.season.overall.as_dict(), repeated.state.season.overall.as_dict())
        self.assertEqual(bulk.state.career.overall.as_dict(), repeated.state.career.overall.as_dict())

    def test_stat_save_backward_compatible(self):
        state = self._orchestrator().state; state.add_game(self.mapping[self.dates[0]])
        payload = json.loads(json.dumps(state.as_dict())); restored = AdvancePipelineState.from_dict(payload)
        self.assertEqual(state.season.as_dict(), restored.season.as_dict())
        old_save = AdvancePipelineState.from_dict({}, default_date=self.start)
        self.assertEqual(old_save.current_date, self.start)
        self.assertEqual(old_save.season.overall.hitter.PA, 0)

    def test_raw_ratings_only_in_ui_view_model(self):
        orch = self._orchestrator(); vm = AdvanceResultViewModel.from_summary(orch.advance_one_week())
        encoded = json.dumps(vm.as_dict())
        self.assertNotIn("normalized", encoded); self.assertNotIn("gameplay_", encoded)
        bad = AdvanceOrchestrator(
            AdvancePipelineState(self.start), ListScheduleProvider(self.dates), MappingGameProvider(self.mapping),
            rating_provider=lambda: {"normalized_contact": 100},
        )
        with self.assertRaises(ValueError): bad.advance_one_game()


class ProtectedFileTests(unittest.TestCase):
    EXPECTED_BLOBS = {
        "src/simulation.py": "b441fbe2fd8bf2aac9239a4648636a2ec67ceb53",
        "src/hitting/model.py": "021399628e083f607e7503dca70154a96177b6f9",
        "src/hitting/parameters.py": "6bd5d35372297eab71d9fbf9ebcc63be615c8d1c",
        "src/hitting/baserunning.py": "2a383ce61fb6938ae30973be210159baa1d76726",
        "src/hitting/defense.py": "279f6282ef41c53e709839dbbe791e16836eaf53",
        "src/config.py": "ed6c07b3517f92f6ad2d1ceb35fe0e0a81862512",
        "src/pitching/__init__.py": "8593e1865da96fbfa0587199c8bddc56833f219d",
        "src/pitching/events.py": "55803e2d79b89b2065eb702b5306005c5d6b075f",
        "src/pitching/fatigue.py": "533516598f4143e6e4940fde102db517c279e2c8",
        "src/pitching/growth.py": "2607359b3f997013447ddd8b67187c59e851dfb1",
        "src/pitching/model.py": "c53739f5afe57398c860f8986051723a977b5056",
        "src/pitching/parameters.py": "6d982f38d966345e7b57e59462e5dce85773278b",
        "src/pitching/performance.py": "c1a43de1ba705ae6469ebc2113381f98194407ee",
        "src/pitching/roles.py": "31222d3ee62998ccd892407c225ef7fa501af566",
    }

    def _repo_root(self): return Path(__file__).resolve().parents[1]

    def _git_blob(self, path):
        root = self._repo_root()
        if not (root / ".git").exists(): self.skipTest("git metadata unavailable")
        return subprocess.check_output(["git", "hash-object", path], cwd=root, text=True).strip()

    def test_no_gameplay_formula_files_changed(self):
        for path in (
            "src/simulation.py", "src/hitting/model.py", "src/hitting/parameters.py",
            "src/hitting/baserunning.py", "src/hitting/defense.py", "src/config.py",
        ):
            self.assertEqual(self._git_blob(path), self.EXPECTED_BLOBS[path], path)
        self.assertFalse((self._repo_root() / "src/hitting/normalization.py").exists())

    def test_catcher_schema_preserves_current_ability_weights(self):
        base = dict(
            contact=111, power=109, discipline=103, speed=97, defense=105,
            throwing=98, stamina=101, durability=96, mentality=107, talent=120,
        )
        low = PlayerStats(**base, game_calling=0)
        high = PlayerStats(**base, game_calling=180)
        self.assertEqual(low.current_ability(), high.current_ability())
        weights = {
            "contact": 1.2, "power": 1.1, "discipline": 1.0, "speed": 0.55,
            "defense": 0.75, "throwing": 0.35, "stamina": 0.30,
            "durability": 0.30, "mentality": 0.45,
        }
        expected = sum(base[name] * weight for name, weight in weights.items()) / sum(weights.values())
        self.assertAlmostEqual(low.current_ability(), expected)

    def test_catcher_growth_addition_is_isolated_from_legacy_growth_logic(self):
        self.assertEqual(GROWABLE_STATS, config.HITTER_STAT_NAMES)
        source = (self._repo_root() / "src/growth.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        function = next(
            node for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "apply_season_growth"
        )
        catcher_blocks = [
            node for node in ast.walk(function)
            if isinstance(node, ast.If) and "game_calling" in ast.unparse(node).lower()
        ]
        self.assertEqual(len(catcher_blocks), 1)
        guard = ast.unparse(catcher_blocks[0].test).replace('"', "'")
        self.assertIn("player.position == 'C'", guard)
        for name in (
            "growth_distribution", "_age_bias", "_profile_bias",
            "_trait_growth_bias", "_experience_bias", "_explosion_chance",
        ):
            node = next(
                item for item in tree.body
                if isinstance(item, ast.FunctionDef) and item.name == name
            )
            self.assertNotIn("game_calling", ast.unparse(node).lower(), name)

    def test_no_pitcher_calibration_files_changed(self):
        for path, expected in self.EXPECTED_BLOBS.items():
            if path.startswith("src/pitching/"):
                self.assertEqual(self._git_blob(path), expected, path)


if __name__ == "__main__": unittest.main()