"""Usage-orchestration Monte Carlo sanity for dynamic pitcher roles/fatigue.

This synthesizes supported counting lines only; it does not recalibrate or
replace any gameplay probability formula.
"""
from __future__ import annotations
import argparse,json,random,statistics
from datetime import date,timedelta
from src.pitcher_usage import PitcherUsageManager,PitcherUsageMember

def season_dates(year=2026,games=144):
    cursor=date(year,4,1);out=[]
    while len(out)<games:
        if cursor.weekday()!=0:out.append(cursor)
        cursor+=timedelta(days=1)
    return out

def run_season(seed):
    rng=random.Random(seed);manager=PitcherUsageManager();members=[PitcherUsageMember(f"p{i}",100,100) for i in range(12)];team=manager.ensure_team("T",members);quality={m.pitcher_id:rng.gauss(0,.7) for m in members};starts={m.pitcher_id:0 for m in members};relief={m.pitcher_id:0 for m in members};starter_outs=[]
    for game_date in season_dates():
        pid,_=manager.select_starter("T",members,game_date);starts[pid]+=1;q=quality[pid]+rng.gauss(0,.7);outs=max(6,min(24,int(round(rng.gauss(17+2*q,3.2)))));bf=max(10,outs+int(round(rng.gauss(8-1.2*q,2.5))));runs=max(0,int(round(rng.gauss(3.1-q,1.8))));hits=max(0,int(round(rng.gauss(6.5-.7*q,2.0))));walks=max(0,int(round(rng.gauss(2.2-.3*q,1.0))));so=max(0,int(round(rng.gauss(4.5+1.1*q,1.6))));hr=max(0,min(hits,int(round(rng.gauss(.7-.15*q,.5)))));manager.record_outing("T",members[int(pid[1:])],game_date,"starter",started=True,BF=bf,outs=outs,H=hits,R=runs,HR=hr,BB=walks,SO=so);starter_outs.append(outs);remaining=max(0,27-outs);used={pid};inning=max(4,outs//3+1)
        while remaining>0:
            rid,emergency=manager.select_reliever("T",members,game_date,inning,0,used)
            if rid is None:break
            used.add(rid);relief[rid]+=1;rq=quality[rid]+rng.gauss(0,.8);role=team.pitchers[rid].current_role;ro=min(remaining,6 if role in {"long_relief","swingman"} and remaining>=6 and rng.random()<.35 else 3);rbf=max(3,ro+int(round(rng.gauss(2.0-.4*rq,.8))));rr=max(0,int(round(rng.gauss(.55-.25*rq,.7))));rh=max(0,int(round(rng.gauss(1.1-.2*rq,.8))));rbb=max(0,int(round(rng.gauss(.35-.08*rq,.45))));rso=max(0,int(round(rng.gauss(1.1+.25*rq,.7))));rhr=max(0,min(rh,int(round(rng.gauss(.12-.03*rq,.25)))));manager.record_outing("T",members[int(rid[1:])],game_date,role,started=False,BF=rbf,outs=ro,H=rh,R=rr,HR=rhr,BB=rbb,SO=rso,emergency_reason=emergency);remaining-=ro;inning+=max(1,ro//3)
        manager.evaluate_roles("T",members,game_date)
    return {"starts":starts,"relief":relief,"role_switches":team.role_switches,"role_change_counts":[s.role_change_count for s in team.pitchers.values()],"avg_ip_start":sum(starter_outs)/len(starter_outs)/3,"two":team.two_day_streaks,"three":team.three_day_streaks,"four":team.four_day_streaks,"viol":team.unavailable_usage_violations,"exhaust":team.bullpen_exhaustion_events}

def run(seasons=500,seed=20260906):
    rows=[run_season(seed+i) for i in range(seasons)];changes=[v for r in rows for v in r["role_change_counts"]]
    return {"seasons":seasons,"mean_role_switches_team_season":statistics.mean(r["role_switches"] for r in rows),"median_role_switches_team_season":statistics.median(r["role_switches"] for r in rows),"pitcher_role_change_0_pct":sum(v==0 for v in changes)/len(changes),"pitcher_role_change_1_pct":sum(v==1 for v in changes)/len(changes),"pitcher_role_change_2plus_pct":sum(v>=2 for v in changes)/len(changes),"avg_starter_ip_start":statistics.mean(r["avg_ip_start"] for r in rows),"mean_two_day_streaks":statistics.mean(r["two"] for r in rows),"mean_three_day_streaks":statistics.mean(r["three"] for r in rows),"mean_four_day_streaks":statistics.mean(r["four"] for r in rows),"unavailable_usage_violations":sum(r["viol"] for r in rows),"mean_bullpen_exhaustion_events":statistics.mean(r["exhaust"] for r in rows),"mean_starts_per_pitcher":statistics.mean(sum(r["starts"].values())/12 for r in rows),"mean_relief_apps_per_pitcher":statistics.mean(sum(r["relief"].values())/12 for r in rows)}

def main():
    parser=argparse.ArgumentParser();parser.add_argument("--seasons",type=int,default=500);parser.add_argument("--seed",type=int,default=20260906);args=parser.parse_args();print(json.dumps(run(args.seasons,args.seed),indent=2))
if __name__=="__main__":main()
