#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, math, statistics
from collections import Counter, defaultdict
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from src.hitting.model import HitterSnapshot, HittingEngine, PitcherSnapshot
from src.hitting.retrieval import (
    RetrievalState, build_retrieval_state, owner_for_location,
    resolve_physical_hit_shadow, runner_arrival_times, throw_timing_to_base,
)
from src.hitting import retrieval_parameters as P
from src.hitting.ground_travel import GroundTravelState
from src.hitting import ground_travel_parameters as GP
from src.hitting.physical_defense import DefensiveOpportunity, DefensiveResolution
from src.rng import RNG

TRAJ_CLASSES=("ground_like","line_drive","fly_ball","popup")
OWNERS=("C","P","1B","2B","SS","3B","LF","CF","RF")
RESULTS=("OUT","1B","2B","3B")
DEF_BUCKETS=(60.0,80.0,100.0,120.0,140.0)
SPD_BUCKETS=(60.0,80.0,100.0,120.0,140.0)

def q(xs,p):
    if not xs:return None
    ys=sorted(xs); return float(ys[min(len(ys)-1,max(0,round((len(ys)-1)*p)))])

def dist(xs):
    if not xs:return {"n":0}
    return {"n":len(xs),"mean":statistics.fmean(xs),"median":q(xs,.5),"p10":q(xs,.10),"p25":q(xs,.25),"p75":q(xs,.75),"p90":q(xs,.90),"p95":q(xs,.95),"p99":q(xs,.99),"min":min(xs),"max":max(xs)}

def shares(counter):
    n=sum(counter.values()); return {str(k):{"count":v,"share":v/n if n else 0.0} for k,v in sorted(counter.items(),key=lambda kv:str(kv[0]))}

def coord(r,a):
    t=math.radians(a); return r*math.sin(t),r*math.cos(t)

def ground_at(x,y,valid=True,wall=False):
    r=math.hypot(x,y)
    return GroundTravelState(valid=valid,surface_class=GP.SURFACE_CLASS_NEUTRAL,
        impact_horizontal_speed_fps=70.0 if valid else 0.0,post_impact_horizontal_speed_fps=35.0 if valid else 0.0,
        bounce_distance_ft=8.0 if valid else 0.0,rollout_start_speed_fps=24.0 if valid else 0.0,
        rollout_distance_ft=12.0 if valid else 0.0,ground_travel_distance_ft=20.0 if valid else 0.0,
        first_impact_x_ft=x,first_impact_y_ft=y,final_x_ft=x,final_y_ft=y,final_radial_distance_ft=r,
        wall_ground_contact=wall,ground_model_version=GP.GROUND_MODEL_VERSION,invalid_reason=None if valid else "test_invalid")

def caught_resolution():
    o=DefensiveOpportunity(valid=True,defender_position="CF",opportunity_type="airborne",catch_x_ft=0.0,catch_y_ft=300.0,
        nominal_start_x_ft=0.0,nominal_start_y_ft=315.0,required_distance_ft=15.0,opportunity_time_s=4.0,
        direction_class="in",near_wall=False,baseline_catch_probability=.9,defender_rating=100.0,adjusted_catch_probability=.9)
    return DefensiveResolution(valid=True,opportunity=o,catch_probability=.9,roll=.1,physical_out_shadow=True)

def rbucket(r):
    if r<35:return "<35"
    if r<90:return "35-90"
    if r<185:return "90-185"
    if r<250:return "185-250"
    if r<330:return "250-330"
    return "330+"

def sbucket(a):
    if a<-30:return "<-30"
    if a<-15:return "-30:-15"
    if a<15:return "-15:15"
    if a<30:return "15:30"
    return "30+"

def evbucket(x):
    if x<75:return "<75"
    if x<85:return "75-85"
    if x<95:return "85-95"
    return "95+"

def labucket(x):
    if x<0:return "<0"
    if x<10:return "0-10"
    if x<25:return "10-25"
    if x<50:return "25-50"
    return "50+"

def count_results(rows,keyfn):
    out=defaultdict(Counter)
    for row in rows:
        out[str(keyfn(row))][row["result"]]+=1
    return {k:shares(v) for k,v in sorted(out.items())}

def mono(xs,nondecreasing=True):
    return all((b>=a-1e-12) if nondecreasing else (b<=a+1e-12) for a,b in zip(xs,xs[1:]))

def hobj(x):return hashlib.sha256(repr(x).encode()).hexdigest()

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--pa",type=int,default=200000); ap.add_argument("--seed",type=int,default=20260913); ap.add_argument("--output",type=Path,required=True); a=ap.parse_args()
    rng=RNG(a.seed); pitcher=PitcherSnapshot(100.0,100.0,100.0)
    owners=Counter(); ownership_by_rad=defaultdict(Counter); ownership_by_spray=defaultdict(Counter); ownership_by_class=defaultdict(Counter)
    retrieval_values=defaultdict(list); by_owner=defaultdict(lambda:defaultdict(list)); by_def=defaultdict(lambda:defaultdict(list)); by_rad=defaultdict(lambda:defaultdict(list))
    throw_by_owner=defaultdict(lambda:defaultdict(lambda:defaultdict(list)))
    phys=Counter(); invalid_reasons=Counter(); physical_rows=[]; margins={"1B":[],"2B":[],"3B":[]}; caught=0; retrieval_out=0; contradictions=0; wall_results=Counter()
    upstream_hash=hashlib.sha256(); legacy=Counter(); parent_before=rng.get_state()
    for i in range(a.pa):
        d=DEF_BUCKETS[i%len(DEF_BUCKETS)]; sp=SPD_BUCKETS[(i//len(DEF_BUCKETS))%len(SPD_BUCKETS)]
        out=HittingEngine(HitterSnapshot(100.0,100.0,100.0,sp),pitcher,d,rng).simulate_plate_appearance(); legacy[out.result]+=1
        if out.batted_ball is None or out.batted_ball.physical_state is None: continue
        s=out.batted_ball.physical_state; ph=s.physical_hit_resolution
        upstream_hash.update(repr((s.exit_velocity,s.launch_angle,s.timing,s.spray_angle,s.is_fair,s.contact_quality,s.trajectory,s.wall_interaction,s.defensive_opportunity,s.defensive_resolution,s.ground_travel)).encode())
        if ph is None:
            invalid_reasons["missing_physical_hit_resolution"]+=1; continue
        if not ph.valid:
            invalid_reasons[ph.invalid_reason or "unknown"]+=1; continue
        phys[ph.physical_result_shadow]+=1
        if ph.physical_result_shadow=="HR": raise AssertionError("Phase2E-B produced HR")
        tc=s.trajectory.trajectory_class if s.trajectory else "none"
        radial=s.ground_travel.final_radial_distance_ft if s.ground_travel and s.ground_travel.valid else None
        if s.defensive_resolution and s.defensive_resolution.valid and s.defensive_resolution.physical_out_shadow:
            caught+=1
            if ph.physical_result_shadow!="OUT" or ph.retrieval.valid or ph.defense_1b is not None: contradictions+=1
            physical_rows.append({"result":"OUT","class":tc,"radial":radial,"ev":s.exit_velocity,"la":s.launch_angle,"defense":d,"speed":sp,"owner":"air_caught"})
            continue
        r=ph.retrieval
        if not r.valid or r.defender_position is None:
            invalid_reasons[r.invalid_reason or "invalid_retrieval"]+=1; continue
        if ph.physical_result_shadow=="OUT":retrieval_out+=1
        owner=r.defender_position; owners[owner]+=1
        rad_label=rbucket(math.hypot(r.ball_x_ft,r.ball_y_ft)); spray_label=sbucket(s.spray_angle)
        ownership_by_rad[rad_label][owner]+=1; ownership_by_spray[spray_label][owner]+=1; ownership_by_class[tc][owner]+=1
        vals={"retrieval_distance_ft":r.retrieval_distance_ft,"reaction_time_s":r.reaction_time_s,"effective_fielder_speed_fps":r.effective_fielder_speed_fps,"movement_time_s":r.movement_time_s,"pickup_transfer_time_s":r.pickup_transfer_time_s,"total_retrieval_time_s":r.total_retrieval_time_s}
        for k,v in vals.items(): retrieval_values[k].append(v); by_owner[owner][k].append(v); by_def[str(int(d))][k].append(v); by_rad[rad_label][k].append(v)
        for base,t in (("1B",ph.defense_1b),("2B",ph.defense_2b),("3B",ph.defense_3b)):
            if t is None:raise AssertionError("valid retrieval missing base timing")
            for k,v in {"throw_distance_ft":t.throw_distance_ft,"effective_throw_speed_fps":t.effective_throw_speed_fps,"transfer_release_time_s":t.transfer_release_time_s,"relay_penalty_s":t.relay_penalty_s,"total_throw_time_s":t.total_throw_time_s,"defense_arrival_time_s":t.defense_arrival_time_s}.items():throw_by_owner[owner][base][k].append(v)
        margins["1B"].append(ph.margin_1b_s);margins["2B"].append(ph.margin_2b_s);margins["3B"].append(ph.margin_3b_s)
        if s.ground_travel and s.ground_travel.wall_ground_contact:wall_results[ph.physical_result_shadow]+=1
        physical_rows.append({"result":ph.physical_result_shadow,"class":tc,"radial":radial,"ev":s.exit_velocity,"la":s.launch_angle,"defense":d,"speed":sp,"owner":owner})
    parent_after=rng.get_state()

    retrieval_report={"overall":{k:dist(v) for k,v in retrieval_values.items()},"by_owner":{o:{k:dist(v) for k,v in vals.items()} for o,vals in sorted(by_owner.items())},"by_defense":{b:{k:dist(v) for k,v in vals.items()} for b,vals in sorted(by_def.items())},"by_radial":{b:{k:dist(v) for k,v in vals.items()} for b,vals in sorted(by_rad.items())}}
    reaction_bounds={"min":P.REACTION_MIN_S,"max":P.REACTION_MAX_S,"at_min":sum(abs(x-P.REACTION_MIN_S)<1e-12 for x in retrieval_values["reaction_time_s"]),"at_max":sum(abs(x-P.REACTION_MAX_S)<1e-12 for x in retrieval_values["reaction_time_s"])}
    speed_bounds={"min":P.FIELDER_SPEED_MIN_FPS,"max":P.FIELDER_SPEED_MAX_FPS,"at_min":sum(abs(x-P.FIELDER_SPEED_MIN_FPS)<1e-12 for x in retrieval_values["effective_fielder_speed_fps"]),"at_max":sum(abs(x-P.FIELDER_SPEED_MAX_FPS)<1e-12 for x in retrieval_values["effective_fielder_speed_fps"])}

    # Controlled defense monotonicity at representative IF/OF locations.
    defense_sweeps={}
    for name,g in {"IF":ground_at(*coord(145,-12)),"OF":ground_at(*coord(350,0))}.items():
        seq=[]
        for rating in (-1e6,60,80,100,120,140,1e6):
            r=build_retrieval_state(ground_travel=g,defender_rating=float(rating)); seq.append({"rating":rating,"valid":r.valid,"reaction":r.reaction_time_s,"speed":r.effective_fielder_speed_fps,"total":r.total_retrieval_time_s})
        defense_sweeps[name]={"rows":seq,"reaction_nonincreasing":mono([x["reaction"] for x in seq],False),"speed_nondecreasing":mono([x["speed"] for x in seq],True),"total_nonincreasing":mono([x["total"] for x in seq],False),"finite_positive":all(x["valid"] and math.isfinite(x["total"]) and x["speed"]>0 and x["total"]>=0 for x in seq)}

    # Throw threshold and monotonic distance checks from same retrieval role.
    base_r=build_retrieval_state(ground_travel=ground_at(0,300),defender_rating=100)
    target=(P.FIRST_BASE_X_FT,P.FIRST_BASE_Y_FT)
    def at_distance(d):
        rr=replace(base_r,ball_x_ft=target[0],ball_y_ft=target[1]+d)
        return throw_timing_to_base(rr,"1B")
    dists=[0,50,100,150,200,219.99,220.0,220.01,250,320]
    tseq=[at_distance(x) for x in dists]
    threshold_jump=at_distance(220.01).total_throw_time_s-at_distance(219.99).total_throw_time_s
    throw_control={"rows":[{"distance_input":d,"actual_distance":t.throw_distance_ft,"throw_time":t.total_throw_time_s,"relay":t.relay_penalty_s} for d,t in zip(dists,tseq)],"distance_monotonic":mono([t.throw_distance_ft for t in tseq]),"time_monotonic":mono([t.total_throw_time_s for t in tseq]),"below_penalty_zero":at_distance(219.99).relay_penalty_s==0.0,"at_threshold_penalty_zero":at_distance(220.0).relay_penalty_s==0.0,"above_penalty_fixed":abs(at_distance(220.01).relay_penalty_s-P.RELAY_PENALTY_S)<1e-12,"threshold_jump_s":threshold_jump}
    throw_report={o:{b:{k:dist(v) for k,v in vals.items()} for b,vals in bases.items()} for o,bases in sorted(throw_by_owner.items())}

    # Runner speed sweeps and multiplier clamp exposure.
    runner_rows=[]
    for speed in (-1e6,40,60,64,80,100,120,136,140,160,1e6):
        ts=runner_arrival_times(float(speed)); mult=max(P.RUNNER_TIME_MULTIPLIER_MIN,min(P.RUNNER_TIME_MULTIPLIER_MAX,1-(speed-P.RUNNER_SPEED_REFERENCE)*P.RUNNER_TIME_PER_RATING_POINT))
        runner_rows.append({"speed":speed,"multiplier":mult,"1B":ts[0],"2B":ts[1],"3B":ts[2]})
    runner_report={"rows":runner_rows,"one_b_nonincreasing":mono([x["1B"] for x in runner_rows],False),"two_b_nonincreasing":mono([x["2B"] for x in runner_rows],False),"three_b_nonincreasing":mono([x["3B"] for x in runner_rows],False),"clamp_low_at_or_above_rating":136.0,"clamp_high_at_or_below_rating":64.0}

    # Controlled result cases.
    controlled={}
    cases={"routine_grounder":ground_at(*coord(105,32)),"remote_single":ground_at(0,210),"deep_double":ground_at(200,350,wall=True),"deep_triple":ground_at(-280,280,wall=True)}
    for name,g in cases.items():
        ph=resolve_physical_hit_shadow(ground_travel=g,defensive_resolution=None,defender_rating=100,runner_speed_rating=100)
        controlled[name]={"valid":ph.valid,"result":ph.physical_result_shadow,"margins":[ph.margin_1b_s,ph.margin_2b_s,ph.margin_3b_s]}
    controlled["phase2d_caught"]={"result":resolve_physical_hit_shadow(ground_travel=ground_at(0,300),defensive_resolution=caught_resolution(),defender_rating=100,runner_speed_rating=100).physical_result_shadow}
    controlled_pass=controlled["routine_grounder"]["result"]=="OUT" and controlled["remote_single"]["result"]=="1B" and controlled["deep_double"]["result"]=="2B" and controlled["deep_triple"]["result"]=="3B" and controlled["phase2d_caught"]["result"]=="OUT"

    margin_report={b:{"distribution":dist(v),"abs_lt_0.05":sum(abs(x)<.05 for x in v)/len(v) if v else 0,"abs_lt_0.10":sum(abs(x)<.10 for x in v)/len(v) if v else 0,"abs_lt_0.25":sum(abs(x)<.25 for x in v)/len(v) if v else 0} for b,v in margins.items()}

    # Invalid/fail-safe probes.
    invalid={}
    def record(name,fn):
        try:
            ph=fn(); invalid[name]={"exception":None,"valid":ph.valid,"result":ph.physical_result_shadow,"reason":ph.invalid_reason,"finite":all(math.isfinite(x) for x in (ph.runner_time_1b_s,ph.runner_time_2b_s,ph.runner_time_3b_s,ph.margin_1b_s,ph.margin_2b_s,ph.margin_3b_s))}
        except Exception as e:invalid[name]={"exception":repr(e)}
    record("missing_ground",lambda:resolve_physical_hit_shadow(ground_travel=None,defensive_resolution=None,defender_rating=100,runner_speed_rating=100))
    record("invalid_ground",lambda:resolve_physical_hit_shadow(ground_travel=ground_at(0,0,False),defensive_resolution=None,defender_rating=100,runner_speed_rating=100))
    class FakeGround:
        valid=True; final_x_ft=float('nan'); final_y_ft=0.0
    record("nonfinite_location",lambda:resolve_physical_hit_shadow(ground_travel=FakeGround(),defensive_resolution=None,defender_rating=100,runner_speed_rating=100))
    record("invalid_defender_rating",lambda:resolve_physical_hit_shadow(ground_travel=ground_at(0,200),defensive_resolution=None,defender_rating=float('nan'),runner_speed_rating=100))
    record("invalid_runner_rating",lambda:resolve_physical_hit_shadow(ground_travel=ground_at(0,200),defensive_resolution=None,defender_rating=100,runner_speed_rating=float('nan')))
    def bad_fielder():
        with patch.object(P,"FIELDER_SPEED_MIN_FPS",0.0),patch.dict(P.EFFECTIVE_FIELDER_SPEED_FPS,{"PC":0.0,"IF":0.0,"OF":0.0}):
            return resolve_physical_hit_shadow(ground_travel=ground_at(0,200),defensive_resolution=None,defender_rating=100,runner_speed_rating=100)
    record("nonpositive_fielder_speed",bad_fielder)
    def bad_throw():
        with patch.dict(P.EFFECTIVE_THROW_SPEED_MPH,{"PC":0.0,"IF":0.0,"OF":0.0}):
            return resolve_physical_hit_shadow(ground_travel=ground_at(0,200),defensive_resolution=None,defender_rating=100,runner_speed_rating=100)
    record("invalid_throw_speed",bad_throw)
    invalid_pass=all(v.get("exception") is None and not v["valid"] and v["result"] is None and v["reason"] and v["finite"] for v in invalid.values())

    # Mirror retrieval and mapped-base throw symmetry.
    mirror=[]
    for radius in (200,260,300,360):
        for ang in (16,27,40):
            x,y=coord(radius,ang); l=build_retrieval_state(ground_travel=ground_at(-x,y),defender_rating=100); r=build_retrieval_state(ground_travel=ground_at(x,y),defender_rating=100)
            lt=throw_timing_to_base(l,"3B") if l.valid else None; rt=throw_timing_to_base(r,"1B") if r.valid else None
            mirror.append({"radius":radius,"angle":ang,"owners":[l.defender_position,r.defender_position],"distance_diff":abs(l.retrieval_distance_ft-r.retrieval_distance_ft),"reaction_diff":abs(l.reaction_time_s-r.reaction_time_s),"movement_diff":abs(l.movement_time_s-r.movement_time_s),"pickup_diff":abs(l.pickup_transfer_time_s-r.pickup_transfer_time_s),"total_diff":abs(l.total_retrieval_time_s-r.total_retrieval_time_s),"mapped_throw_distance_diff":abs(lt.throw_distance_ft-rt.throw_distance_ft),"mapped_throw_time_diff":abs(lt.total_throw_time_s-rt.total_throw_time_s)})
    mirror_pass=all(x["owners"]==["LF","RF"] and max(x["distance_diff"],x["reaction_diff"],x["movement_diff"],x["pickup_diff"],x["total_diff"],x["mapped_throw_distance_diff"],x["mapped_throw_time_diff"])<1e-9 for x in mirror)

    # Exact replay and enabled/disabled RNG/upstream invariance on 20k PA.
    def replay(disabled,n=20000):
        rr=RNG(a.seed+991); res=Counter(); up=hashlib.sha256(); phh=hashlib.sha256()
        ctx=None
        if disabled:
            from src.hitting.retrieval import _invalid_resolution
            ctx=patch("src.hitting.retrieval.resolve_physical_hit_shadow",side_effect=lambda **kw:_invalid_resolution("disabled_for_05"))
            ctx.start()
        try:
            for i in range(n):
                d=DEF_BUCKETS[i%5]; sp=SPD_BUCKETS[(i//5)%5]
                o=HittingEngine(HitterSnapshot(100,100,100,sp),pitcher,d,rr).simulate_plate_appearance();res[o.result]+=1
                if o.batted_ball and o.batted_ball.physical_state:
                    s=o.batted_ball.physical_state;up.update(repr((s.exit_velocity,s.launch_angle,s.timing,s.spray_angle,s.is_fair,s.contact_quality,s.trajectory,s.wall_interaction,s.defensive_opportunity,s.defensive_resolution,s.ground_travel)).encode());phh.update(repr(s.physical_hit_resolution).encode())
        finally:
            if ctx:ctx.stop()
        return {"results":dict(res),"rng":hobj(rr.get_state()),"upstream":up.hexdigest(),"physical":phh.hexdigest()}
    re1=replay(False);re2=replay(False);red=replay(True)
    determinism=re1==re2; rng_purity=re1["rng"]==red["rng"]; upstream_equal=re1["upstream"]==red["upstream"]; legacy_equal=re1["results"]==red["results"]

    nphys=sum(phys.values())
    result_report={"overall":shares(phys),"phase2d_caught_out_share":caught/nphys if nphys else 0,"retrieval_derived_out_share":retrieval_out/nphys if nphys else 0,"invalid_or_none":sum(invalid_reasons.values()),"by_trajectory":count_results(physical_rows,lambda r:r["class"]),"by_final_distance":count_results([r for r in physical_rows if r["radial"] is not None],lambda r:rbucket(r["radial"])),"by_ev":count_results(physical_rows,lambda r:evbucket(r["ev"])),"by_la":count_results(physical_rows,lambda r:labucket(r["la"])),"by_defense":count_results(physical_rows,lambda r:int(r["defense"])),"by_runner_speed":count_results(physical_rows,lambda r:int(r["speed"])),"by_owner":count_results([r for r in physical_rows if r["owner"]!="air_caught"],lambda r:r["owner"]),"wall_ground_contact_results":shares(wall_results)}

    out={
      "seed":a.seed,"pa":a.pa,"legacy_outcomes":dict(legacy),"population":{"physical_valid":nphys,"invalid_reasons":dict(invalid_reasons),"phase2d_caught":caught,"retrieval_applicable":sum(owners.values())},
      "ownership":{"overall":shares(owners),"by_radial":{k:shares(v) for k,v in sorted(ownership_by_rad.items())},"by_spray":{k:shares(v) for k,v in sorted(ownership_by_spray.items())},"by_trajectory":{k:shares(v) for k,v in sorted(ownership_by_class.items())}},
      "retrieval":retrieval_report,"reaction_bound_pileup":reaction_bounds,"fielder_speed_bound_pileup":speed_bounds,"defense_monotonicity":defense_sweeps,
      "throw":{"by_owner":throw_report,"controlled":throw_control},"runner":runner_report,"result_distribution":result_report,"controlled_results":controlled,"controlled_results_pass":controlled_pass,
      "timing_margins":margin_report,"phase2d_interface":{"caught":caught,"contradictions":contradictions,"pass":contradictions==0},"invalid_state":{"cases":invalid,"pass":invalid_pass},"mirror":{"cases":mirror,"pass":mirror_pass},
      "determinism":{"pass":determinism,"replay_hash":re1["physical"]},"rng_purity":{"pass":rng_purity,"enabled_rng":re1["rng"],"disabled_rng":red["rng"]},"upstream_regression":{"pass":upstream_equal,"enabled":re1["upstream"],"disabled":red["upstream"]},"legacy_pa_regression":{"pass":legacy_equal,"enabled":re1["results"],"disabled":red["results"]},
      "parent_rng_after_200k_hash":hobj(parent_after),"upstream_200k_hash":upstream_hash.hexdigest()
    }
    a.output.write_text(json.dumps(out,indent=2,sort_keys=True),encoding="utf-8")
    print(json.dumps({"physical_valid":nphys,"owners":shares(owners),"results":shares(phys),"invalid":dict(invalid_reasons),"controlled_pass":controlled_pass,"invalid_pass":invalid_pass,"mirror_pass":mirror_pass,"determinism":determinism,"rng_purity":rng_purity,"upstream_equal":upstream_equal,"legacy_equal":legacy_equal,"threshold_jump_s":threshold_jump},indent=2,sort_keys=True))

if __name__=="__main__":main()
