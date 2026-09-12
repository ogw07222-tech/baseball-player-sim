#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, math, statistics
from collections import Counter, defaultdict
from dataclasses import asdict
from pathlib import Path
from unittest.mock import patch

from src.hitting.ground_travel import generate_ground_travel_state, impact_horizontal_speed_proxy, rollout_distance_ft
from src.hitting.model import HitterSnapshot, HittingEngine, PitcherSnapshot
from src.hitting.stadium import WallInteraction
from src.hitting.trajectory import BattedBallTrajectory
from src.rng import RNG


def q(xs,p):
    if not xs: return 0.0
    ys=sorted(xs); i=min(len(ys)-1,max(0,round((len(ys)-1)*p))); return float(ys[i])

def dist(xs, probs=(.01,.05,.10,.25,.50,.75,.90,.95,.99)):
    if not xs: return {"n":0}
    out={"n":len(xs),"mean":statistics.mean(xs),"median":q(xs,.5),"min":min(xs),"max":max(xs)}
    for p in probs: out[f"p{int(p*100)}"]=q(xs,p)
    return out

def corr(xs,ys):
    if len(xs)<2 or len(xs)!=len(ys): return 0.0
    mx,my=statistics.mean(xs),statistics.mean(ys)
    num=sum((x-mx)*(y-my) for x,y in zip(xs,ys)); dx=sum((x-mx)**2 for x in xs); dy=sum((y-my)**2 for y in ys)
    return num/math.sqrt(dx*dy) if dx>0 and dy>0 else 0.0

def traj(distance, spray=0.0, *, hang=2.0, cls="ground_like", valid=True):
    a=math.radians(spray)
    return BattedBallTrajectory(horizontal_distance_ft=distance,hang_time_s=hang,apex_height_ft=20.0,landing_x_ft=distance*math.sin(a),landing_y_ft=distance*math.cos(a),trajectory_class=cls,apex_distance_fraction=0.0 if cls=="ground_like" else 0.5,valid=valid)

def wall(radius=500.0, *, reaches=False):
    return WallInteraction(stadium_id="v05",wall_radius_ft=radius,wall_height_ft=10.0,reaches_wall=reaches,ball_height_at_wall_ft=5.0 if reaches else 0.0,clearance_ft=-5.0 if reaches else -10.0,clears_wall=False,wall_contact=False,physical_hr_shadow=False)

def mono(seq, nondecreasing=True):
    return all((b+1e-12>=a) if nondecreasing else (b<=a+1e-12) for a,b in zip(seq,seq[1:]))

def hobj(x): return hashlib.sha256(repr(x).encode()).hexdigest()

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--pa',type=int,default=200000); ap.add_argument('--seed',type=int,default=20260912); ap.add_argument('--output',type=Path,required=True); a=ap.parse_args()
    rng=RNG(a.seed); hitter=HitterSnapshot(100,100,100,100); pitcher=PitcherSnapshot(100,100,100)
    rows=[]; outcomes=Counter()
    for _ in range(a.pa):
        out=HittingEngine(hitter,pitcher,100.0,rng).simulate_plate_appearance(); outcomes[out.result]+=1
        if out.batted_ball and out.batted_ball.physical_state:
            s=out.batted_ball.physical_state; g=s.ground_travel
            rows.append((s,g,out.result))
    valid=[r for r in rows if r[1] is not None and r[1].valid]; invalid=[r for r in rows if r[1] is None or not r[1].valid]
    reasons=Counter(("missing_state" if g is None else g.invalid_reason) for _,g,_ in invalid)
    class_stats={}
    for cls in ("ground_like","line_drive","fly_ball","popup"):
        z=[r for r in rows if r[0].trajectory and r[0].trajectory.trajectory_class==cls]; zv=[r for r in z if r[1] and r[1].valid]
        class_stats[cls]={"n":len(z),"valid":len(zv),"valid_rate":len(zv)/len(z) if z else 0.0,"invalid":len(z)-len(zv)}

    impact=[g.impact_horizontal_speed_fps for _,g,_ in valid]; post=[g.post_impact_horizontal_speed_fps for _,g,_ in valid]; bounce=[g.bounce_distance_ft for _,g,_ in valid]; rollspd=[g.rollout_start_speed_fps for _,g,_ in valid]; rollout=[g.rollout_distance_ft for _,g,_ in valid]; ground=[g.ground_travel_distance_ft for _,g,_ in valid]
    first=[math.hypot(g.first_impact_x_ft,g.first_impact_y_ft) for _,g,_ in valid]; hang=[s.trajectory.hang_time_s for s,_,_ in valid]; ev=[s.exit_velocity for s,_,_ in valid]; la=[s.launch_angle for s,_,_ in valid]
    by_class={}
    for cls in ("ground_like","line_drive","fly_ball","popup"):
        z=[r for r in valid if r[0].trajectory.trajectory_class==cls]
        by_class[cls]={"n":len(z),"impact":dist([g.impact_horizontal_speed_fps for _,g,_ in z]),"post_impact":dist([g.post_impact_horizontal_speed_fps for _,g,_ in z]),"bounce":dist([g.bounce_distance_ft for _,g,_ in z]),"rollout_start":dist([g.rollout_start_speed_fps for _,g,_ in z]),"rollout":dist([g.rollout_distance_ft for _,g,_ in z]),"ground_travel":dist([g.ground_travel_distance_ft for _,g,_ in z])}

    def bucket_stats(field, chooser):
        out={}
        for label,pred in chooser:
            xs=[field(r) for r in valid if pred(r)]
            out[label]=dist(xs)
        return out
    rollout_buckets={
      "ev":bucket_stats(lambda r:r[1].rollout_distance_ft,[('<70',lambda r:r[0].exit_velocity<70),('70-80',lambda r:70<=r[0].exit_velocity<80),('80-90',lambda r:80<=r[0].exit_velocity<90),('90-100',lambda r:90<=r[0].exit_velocity<100),('100+',lambda r:r[0].exit_velocity>=100)]),
      "la":bucket_stats(lambda r:r[1].rollout_distance_ft,[('<0',lambda r:r[0].launch_angle<0),('0-10',lambda r:0<=r[0].launch_angle<10),('10-25',lambda r:10<=r[0].launch_angle<25),('25-50',lambda r:25<=r[0].launch_angle<50),('50+',lambda r:r[0].launch_angle>=50)]),
      "impact_distance":bucket_stats(lambda r:r[1].rollout_distance_ft,[('<50',lambda r:math.hypot(r[1].first_impact_x_ft,r[1].first_impact_y_ft)<50),('50-150',lambda r:50<=math.hypot(r[1].first_impact_x_ft,r[1].first_impact_y_ft)<150),('150-250',lambda r:150<=math.hypot(r[1].first_impact_x_ft,r[1].first_impact_y_ft)<250),('250-350',lambda r:250<=math.hypot(r[1].first_impact_x_ft,r[1].first_impact_y_ft)<350),('350+',lambda r:math.hypot(r[1].first_impact_x_ft,r[1].first_impact_y_ft)>=350)])
    }

    final_rad=[g.final_radial_distance_ft for _,g,_ in valid]; deltas=[g.final_radial_distance_ft-math.hypot(g.first_impact_x_ft,g.first_impact_y_ft) for _,g,_ in valid]
    finite_all=all(all(math.isfinite(v) for v in (g.final_x_ft,g.final_y_ft,g.final_radial_distance_ft,g.ground_travel_distance_ft)) for _,g,_ in valid)
    no_negative=all(g.ground_travel_distance_ft>=-1e-12 for _,g,_ in valid)
    radial_ok=all((g.wall_ground_contact or g.final_radial_distance_ft+1e-9>=math.hypot(g.first_impact_x_ft,g.first_impact_y_ft)) for _,g,_ in valid)
    ray_ok=max([abs(math.atan2(g.final_x_ft,g.final_y_ft)-math.radians(s.spray_angle)) for s,g,_ in valid] or [0.0])<1e-9
    wall_rate=sum(g.wall_ground_contact for _,g,_ in valid)/len(valid) if valid else 0.0

    mirrors=[]
    for cls in ("ground_like","line_drive","fly_ball","popup"):
      for d in (80,160,240,320):
        for ang in (10,25,40):
          l=generate_ground_travel_state(trajectory=traj(d,-ang,hang=max(.5,d/100),cls=cls),wall_interaction=wall(500),spray_angle_deg=-ang)
          r=generate_ground_travel_state(trajectory=traj(d,ang,hang=max(.5,d/100),cls=cls),wall_interaction=wall(500),spray_angle_deg=ang)
          mirrors.append((l,r))
    mirror_pass=all(l.valid==r.valid and abs(l.impact_horizontal_speed_fps-r.impact_horizontal_speed_fps)<1e-12 and abs(l.post_impact_horizontal_speed_fps-r.post_impact_horizontal_speed_fps)<1e-12 and abs(l.bounce_distance_ft-r.bounce_distance_ft)<1e-12 and abs(l.rollout_distance_ft-r.rollout_distance_ft)<1e-12 and abs(l.ground_travel_distance_ft-r.ground_travel_distance_ft)<1e-12 and abs(l.final_radial_distance_ft-r.final_radial_distance_ft)<1e-12 and abs(abs(l.final_x_ft)-abs(r.final_x_ft))<1e-12 and abs(l.final_y_ft-r.final_y_ft)<1e-12 and abs(l.final_x_ft+r.final_x_ft)<1e-12 for l,r in mirrors)

    dgrid=[impact_horizontal_speed_proxy(first_impact_distance_ft=d,hang_time_s=2.0,trajectory_class='ground_like') for d in range(0,451,5)]
    sgrid=[rollout_distance_ft(s,35.0) for s in range(0,121,5)]
    agrid=[rollout_distance_ft(60.0,decel) for decel in range(10,101,5)]
    retain=[]
    from src.hitting import ground_travel_parameters as GP
    for ret in (.2,.35,.5,.65,.8):
        with patch.dict(GP.POST_IMPACT_SPEED_RETENTION,{"ground_like":ret}):
            retain.append(generate_ground_travel_state(trajectory=traj(120,0,hang=1.2,cls='ground_like'),wall_interaction=wall(500),spray_angle_deg=0).ground_travel_distance_ft)
    monotonicity={"impact_distance_nondecreasing":mono(dgrid,True),"rollout_speed_nondecreasing":mono(sgrid,True),"deceleration_nonincreasing":mono(agrid,False),"retention_nondecreasing":mono(retain,True),"zero_rollout_exact":rollout_distance_ft(0.0,35.0)==0.0,"retention_values":retain}

    wall_cases={}
    c1=generate_ground_travel_state(trajectory=traj(80,0,hang=2),wall_interaction=wall(500),spray_angle_deg=0)
    c2=generate_ground_travel_state(trajectory=traj(300,0,hang=2),wall_interaction=wall(330),spray_angle_deg=0)
    c3=generate_ground_travel_state(trajectory=traj(380,0,hang=2),wall_interaction=wall(350,reaches=True),spray_angle_deg=0)
    ml=generate_ground_travel_state(trajectory=traj(300,-25,hang=2),wall_interaction=wall(330),spray_angle_deg=-25); mr=generate_ground_travel_state(trajectory=traj(300,25,hang=2),wall_interaction=wall(330),spray_angle_deg=25)
    wall_cases={"inside":{"valid":c1.valid,"contact":c1.wall_ground_contact,"final":c1.final_radial_distance_ft},"exceeds":{"valid":c2.valid,"contact":c2.wall_ground_contact,"final":c2.final_radial_distance_ft},"air_wall":{"valid":c3.valid,"reason":c3.invalid_reason},"mirror":{"valid":ml.valid and mr.valid,"same_radial":abs(ml.final_radial_distance_ft-mr.final_radial_distance_ft)<1e-12,"x_mirror":abs(ml.final_x_ft+mr.final_x_ft)<1e-12,"y_same":abs(ml.final_y_ft-mr.final_y_ft)<1e-12}}
    wall_pass=c1.valid and not c1.wall_ground_contact and c2.valid and c2.wall_ground_contact and abs(c2.final_radial_distance_ft-330)<1e-12 and (not c3.valid and c3.invalid_reason=='air_wall_precedes_ground') and all(wall_cases['mirror'].values())

    invalid={}
    def rec(name,**kw):
      try: st=generate_ground_travel_state(**kw); invalid[name]={"valid":st.valid,"reason":st.invalid_reason,"finite":all(math.isfinite(v) for v in (st.impact_horizontal_speed_fps,st.rollout_distance_ft,st.ground_travel_distance_ft,st.final_radial_distance_ft)),"travel":st.ground_travel_distance_ft}
      except Exception as e: invalid[name]={"exception":repr(e)}
    rec('none',trajectory=None,wall_interaction=wall(),spray_angle_deg=0)
    rec('invalid_traj',trajectory=traj(100,valid=False),wall_interaction=wall(),spray_angle_deg=0)
    rec('unsupported',trajectory=traj(100,cls='weird'),wall_interaction=wall(),spray_angle_deg=0)
    rec('zero_hang',trajectory=traj(100,hang=0.0),wall_interaction=wall(),spray_angle_deg=0)
    rec('missing_wall',trajectory=traj(100),wall_interaction=None,spray_angle_deg=0)
    rec('bad_wall',trajectory=traj(100),wall_interaction=wall(0.0),spray_angle_deg=0)
    rec('nonfinite',trajectory=traj(100),wall_interaction=wall(),spray_angle_deg=float('nan'))
    rec('bad_decel',trajectory=traj(100),wall_interaction=wall(),spray_angle_deg=0,effective_deceleration_ftps2=0.0)
    invalid_pass=all(('exception' not in v) and (not v['valid']) and v['finite'] and abs(v['travel'])<1e-12 for v in invalid.values())

    # deterministic replay and parent-RNG purity + A/B/C/D/legacy exact regression
    def replay(disabled,n=200000):
      rr=RNG(a.seed+99); counts=Counter(); upstream=hashlib.sha256(); groundh=hashlib.sha256()
      ctx=patch('src.hitting.ground_travel.generate_ground_travel_state',return_value=None) if disabled else None
      if ctx: ctx.start()
      try:
        for _ in range(n):
          out=HittingEngine(hitter,pitcher,100.0,rr).simulate_plate_appearance(); counts[out.result]+=1
          if out.batted_ball and out.batted_ball.physical_state:
            s=out.batted_ball.physical_state
            tup=(s.exit_velocity,s.launch_angle,s.timing,s.spray_angle,s.is_fair,s.contact_quality,s.trajectory,s.wall_interaction,s.defensive_opportunity,s.defensive_resolution)
            upstream.update(repr(tup).encode()); groundh.update(repr(s.ground_travel).encode())
      finally:
        if ctx: ctx.stop()
      return {"counts":dict(counts),"rng_hash":hobj(rr.get_state()),"upstream_hash":upstream.hexdigest(),"ground_hash":groundh.hexdigest()}
    enabled=replay(False); disabled=replay(True)
    replay2=replay(False,n=20000)
    replay3=replay(False,n=20000)
    determinism=(replay2==replay3)
    upstream_equal=enabled['upstream_hash']==disabled['upstream_hash']; legacy_equal=enabled['counts']==disabled['counts']; rng_equal=enabled['rng_hash']==disabled['rng_hash']

    result={"seed":a.seed,"pa":a.pa,"outcomes":dict(outcomes),"population":{"physical_bip":len(rows),"valid":len(valid),"valid_rate":len(valid)/len(rows) if rows else 0.0,"invalid":len(invalid),"invalid_rate":len(invalid)/len(rows) if rows else 0.0,"invalid_reasons":dict(reasons),"by_class":class_stats},"impact":{"overall":dist(impact),"by_class":{k:v['impact'] for k,v in by_class.items()},"clamp_220_count":sum(abs(x-220.0)<1e-12 for x in impact),"clamp_220_rate":sum(abs(x-220.0)<1e-12 for x in impact)/len(impact) if impact else 0.0,"correlations":{"first_impact_distance":corr(impact,first),"hang_time":corr(impact,hang),"exit_velocity":corr(impact,ev),"launch_angle":corr(impact,la)}},"bounce":{"post_impact":dist(post),"bounce":dist(bounce),"rollout_start":dist(rollspd),"by_class":by_class},"rollout":{"rollout":dist(rollout),"ground_travel":dist(ground),"buckets":rollout_buckets},"final_location":{"final_radial":dist(final_rad),"delta_final_minus_first":dist(deltas),"wall_ground_contact_rate":wall_rate,"finite":finite_all,"nonnegative_travel":no_negative,"radial_invariant":radial_ok,"spray_ray_preserved":ray_ok},"mirror":{"cases":len(mirrors),"pass":mirror_pass},"monotonicity":monotonicity,"wall_stop":{"pass":wall_pass,"cases":wall_cases},"invalid":{"pass":invalid_pass,"cases":invalid},"regression":{"enabled":enabled,"disabled":disabled,"phase2abcd_equal":upstream_equal,"legacy_counts_equal":legacy_equal,"parent_rng_equal":rng_equal,"determinism_20k":determinism},"calibration":{"engineering_only":True,"max_ground_travel_clamp_count":sum(abs(g.rollout_distance_ft+b - 450.0)<1e-9 for (_,g,_),b in zip(valid,bounce)) if valid else 0}}
    a.output.write_text(json.dumps(result,indent=2,sort_keys=True),encoding='utf-8')

if __name__=='__main__': main()
