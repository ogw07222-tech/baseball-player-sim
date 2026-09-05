from src.pitching.model import PitcherStats
from src.pitching.physical_velocity import *
from tools.pitcher_joint_v2.adapter import JointWeights,PitcherJointAdapter

def stats(**kw):
 d=dict(velocity=97,stuff=100,control=100,breaking=100,stamina=100,resilience=100,talent=100);d.update(kw);return PitcherStats(**d)

def test_velocity_soft_cap_monotonic():
 xs=(30,50,70,100,130,150,160,180,200,250);ys=[base_avg_kmh(x) for x in xs];assert all(a<b for a,b in zip(ys,ys[1:]))
def test_velocity_hard_safety_cap():
 assert base_avg_kmh(10000)<=BASE_HARD_CAP and effective_avg_kmh(10000,100)<=EFFECTIVE_HARD_CAP
def test_raw_velocity_not_mutated():
 s=stats(velocity=250);before=s.velocity;snapshot(s.velocity,8,0);assert s.velocity==before
def test_no_200_kmh_average_velocity(): assert effective_avg_kmh(100000,100)<180
def test_no_cap_mass_pileup_pathology():
 vals=[base_avg_kmh(x) for x in range(140,251)];assert len(set(round(x,4) for x in vals))>100 and sum(abs(x-BASE_HARD_CAP)<1e-12 for x in vals)==0
def test_effort_respects_physical_cap(): assert effective_avg_kmh(150,4)>effective_avg_kmh(150,0) and effective_avg_kmh(250,20)<=EFFECTIVE_HARD_CAP
def test_fatigue_respects_physical_cap(): assert effective_avg_kmh(150,4,3)<effective_avg_kmh(150,4,0)
def test_max_velocity_separate_from_average(): assert max_pitch_kmh(160,7)==167 and max_pitch_kmh(166,10)==MAX_PITCH_HARD_CAP

def test_velocity_physical_path_frozen():
 assert abs(raw_to_uncapped_avg_kmh(97)-146)<1e-9 and abs(gameplay_velocity(146)-100)<1e-9 and abs(GAMEPLAY_POINTS_PER_KMH-1.5)<1e-9
def test_control_reduces_walks():
 w=JointWeights();a=PitcherJointAdapter(stats(control=120),w);assert a.pitcher_snapshot().control>100
def test_stuff_reduces_hard_contact():
 w=JointWeights();assert PitcherJointAdapter(stats(stuff=120),w).modifier(None,0)[1]<0
def test_breaking_increases_whiff():
 w=JointWeights();assert PitcherJointAdapter(stats(breaking=120),w).modifier(None,0)[0]<0
def test_breaking_reduces_contact_quality():
 w=JointWeights();assert PitcherJointAdapter(stats(breaking=120),w).modifier(None,0)[1]<0
def test_stuff_not_universal():
 w=JointWeights();a=PitcherJointAdapter(stats(stuff=120),w);assert a.pitcher_snapshot().control==100
def test_control_not_universal():
 w=JointWeights();a=PitcherJointAdapter(stats(control=120),w);assert a.modifier(None,0)==(0.0,-0.0)
def test_breaking_and_stuff_have_distinct_semantics():
 w=JointWeights();sb=PitcherJointAdapter(stats(stuff=120),w).modifier(None,0);br=PitcherJointAdapter(stats(breaking=120),w).modifier(None,0);assert sb!=br
def test_talent_zero_direct_gameplay():
 w=JointWeights();assert PitcherJointAdapter(stats(talent=250),w).modifier(None,0)==PitcherJointAdapter(stats(talent=30),w).modifier(None,0)
def test_stamina_zero_neutral_pa():
 w=JointWeights();assert PitcherJointAdapter(stats(stamina=250),w).modifier(None,0)==PitcherJointAdapter(stats(stamina=30),w).modifier(None,0)
def test_resilience_zero_neutral_pa():
 w=JointWeights();assert PitcherJointAdapter(stats(resilience=250),w).modifier(None,0)==PitcherJointAdapter(stats(resilience=30),w).modifier(None,0)
def test_extreme_pitcher_rating_safety():
 w=JointWeights()
 for q in (30,50,70,100,130,160,200,250):
  a=PitcherJointAdapter(stats(velocity=q,stuff=q,control=q,breaking=q),w);x=a.modifier(None,0);assert all(abs(v)<1000 for v in x);assert 0<a.pitcher_snapshot().control<1000
