from __future__ import annotations

import unittest

from tools.kbo_rating_inference.broad_spectrum import (
    HITTER_BINS,PITCHER_BINS,bucket_for,hitter_usage_bucket,pitcher_role,
    pitcher_usage_bucket,qrank,shrink_rate,stratify_hitters,stratify_pitchers,
)
from tools.kbo_rating_inference.pitcher_first_team_usage import build as build_pitcher_usage


class BroadSpectrumTests(unittest.TestCase):
    def test_quantile_buckets_keep_bottom(self):
        self.assertEqual(bucket_for(.02,HITTER_BINS),'P00_10_low')
        self.assertEqual(bucket_for(.24,HITTER_BINS),'P10_25_below')
        self.assertEqual(bucket_for(.95,HITTER_BINS),'P90_100_star_elite')
        self.assertEqual(bucket_for(.05,PITCHER_BINS),'P00_20_low')

    def test_rank_spans_full_spectrum(self):
        r=qrank([1,2,3,4,5,6]);self.assertEqual(r[0],0.0);self.assertEqual(r[-1],1.0)

    def test_hitter_usage_buckets(self):
        self.assertEqual(hitter_usage_bucket(120),'role_100_299')
        self.assertEqual(hitter_usage_bucket(610),'everyday_550_plus')

    def test_shrinkage_stronger_for_small_sample(self):
        low=shrink_rate(.400,100,.300,250);high=shrink_rate(.400,600,.300,250)
        self.assertLess(abs(low-.300),abs(high-.300))
        self.assertLess(low,high)

    def test_hitter_stratification_retains_low_performers(self):
        rows=[]
        for i in range(60):
            pa=120+i*8;ab=pa-40;avg=.190+i*.0028;h=round(ab*avg);hr=i%20;bb=40;so=100-i
            rows.append({'player':f'H{i}','PA':str(pa),'AB':str(ab),'H':str(h),'2B':'10','3B':'1','HR':str(hr),'BB':str(bb),'SO':str(max(20,so)),'AVG':str(avg),'OBP':str(min(.450,avg+.070)),'SLG':str(min(.650,avg+.100+hr/200)),'BABIP':'.300','SB':'0','CS':'0'})
        out=stratify_hitters(rows);self.assertEqual(len(out),60);b={r['performance_bucket'] for r in out}
        self.assertTrue(all(x[2] in b for x in HITTER_BINS))
        self.assertTrue(any(r['performance_bucket']=='P00_10_low' for r in out))

    def test_pitcher_roles_separate(self):
        self.assertEqual(pitcher_role({'G':'28','GS':'28'}),'starter')
        self.assertEqual(pitcher_role({'G':'55','GS':'0'}),'reliever')
        self.assertEqual(pitcher_role({'G':'30','GS':'5'}),'swingman')
        self.assertEqual(pitcher_usage_bucket({'BF':'650','G':'28','GS':'28'},'starter'),'starter_workhorse')
        self.assertEqual(pitcher_usage_bucket({'BF':'250','G':'60','GS':'0','SV':'0'},'reliever'),'setup_middle_high_usage')

    def test_pitcher_stratification_role_quantiles(self):
        rows=[]
        for i in range(30):
            rows.append({'player':f'S{i}','BF':str(350+i*10),'G':'28','GS':'28','SO':str(70+i*3),'BB':str(60-i),'HR':str(20-i//3),'H':str(180-i),'OPP_SLG':str(.500-i*.006),'BABIP':'.300'})
        for i in range(30):
            rows.append({'player':f'R{i}','BF':str(120+i*7),'G':'55','GS':'0','SV':str(i//10*10),'SO':str(20+i*2),'BB':str(30-i//2),'HR':str(10-i//5),'H':str(70-i),'OPP_SLG':str(.480-i*.006),'BABIP':'.300'})
        out=stratify_pitchers(rows);starter={r['performance_bucket'] for r in out if r['role']=='starter'};reliever={r['performance_bucket'] for r in out if r['role']=='reliever'}
        self.assertTrue(all(x[2] in starter for x in PITCHER_BINS));self.assertTrue(all(x[2] in reliever for x in PITCHER_BINS))

    def test_pitcher_usage_provider_preserves_raw_and_has_roles(self):
        rows=build_pitcher_usage(30,88001,'data/kbo_2025_pitcher_stats_seed.csv')
        self.assertEqual(len(rows),30);self.assertTrue(all(r.BF>0 and r.usage_weight==r.BF for r in rows));self.assertGreater(len({r.role for r in rows}),1)


if __name__=='__main__':unittest.main()
