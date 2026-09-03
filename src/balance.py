"""Monte Carlo balance report for growth, draft, coaching, events and careers."""
from __future__ import annotations
import argparse, json, math, statistics
from collections import Counter
from dataclasses import asdict
from .career import CareerEngine
from .coaches import CoachingStaff, generate_batting_coach, generate_fielding_coach
from .events import EVENT_BY_ID, resolve_event
from .growth import GrowthExperience, apply_season_growth
from .player import Player
from .rng import RNG
from .stats import PlayerStats

def pct(values:list[float],q:float)->float:
    if not values:return 0.0
    s=sorted(values);i=(len(s)-1)*q;lo=int(math.floor(i));hi=int(math.ceil(i))
    if lo==hi:return s[lo]
    return s[lo]*(hi-i)+s[hi]*(i-lo)
def summary(values:list[float])->dict[str,float]:return {'mean':round(statistics.mean(values),3),'p10':round(pct(values,.1),3),'p50':round(pct(values,.5),3),'p90':round(pct(values,.9),3)} if values else {'mean':0.,'p10':0.,'p50':0.,'p90':0.}
def corr(xs:list[float],ys:list[float])->float:
    if len(xs)<2:return 0.
    mx,my=statistics.mean(xs),statistics.mean(ys);num=sum((x-mx)*(y-my) for x,y in zip(xs,ys));den=math.sqrt(sum((x-mx)**2 for x in xs)*sum((y-my)**2 for y in ys));return num/den if den else 0.
def bucket_peak(age:int)->str:
    if age<=21:return '<22'
    if age<=25:return '22-25'
    if age<=29:return '26-29'
    if age<=33:return '30-33'
    return '34+'

def run_balance(samples:int=1000,careers:int=250,coach_samples:int=100,event_samples:int=1000,seed:int=20260903)->dict[str,object]:
    abilities=[];talents=[];draft=Counter()
    for i in range(samples):
        r=RNG(seed+i);p=Player.random('MC',r);abilities.append(p.stats.current_ability());talents.append(p.stats.talent);d=CareerEngine(p,r).evaluate_draft()
        draft['undrafted' if d.round is None else '1R' if d.round==1 else '2-3R' if d.round<=3 else '4-7R' if d.round<=7 else '8-11R']+=1
    draft_pct={k:round(draft[k]*100/samples,2) for k in ('1R','2-3R','4-7R','8-11R','undrafted')}

    debut_ages=[];debut_fail=0;first_pa=[];farm_pa=[];peaks=[];peak_ages=[];explosions=[];talent_career=[];event_counts=[];risky_q=[];stable_q=[];inj_counts=[];inj_missed=[];severe_count=0;retire=[];career_g=[];career_pa=[];mvp=gg=0;season_counts=[]
    for i in range(careers):
        r=RNG(seed+100000+i);p=Player.random('Career',r);initial=p.stats.current_ability();e=CareerEngine(p,r);e.run_to_retirement();season_counts.append(len(p.seasons));career=p.first_team_career();farm=p.farm_career();first_pa.append(career.PA);farm_pa.append(farm.PA);career_g.append(career.G);career_pa.append(career.PA);retire.append(float(p.retirement_age or p.age));talent_career.append(float(p.initial_talent or p.stats.talent))
        if p.debut_year is None:debut_fail+=1
        else:debut_ages.append(float(18+p.debut_year-2026))
        hist=[(initial,18)]+[(float(h.get('ability_after',initial)),int(h.get('age_after',18))) for h in p.growth_history];pk,pa=max(hist,key=lambda x:x[0]);peaks.append(pk);peak_ages.append(pa);explosions.append(sum(1 for h in p.growth_history if h.get('explosion')))
        ev=[x for x in p.event_history if x.get('event_id')!='coach_change'];event_counts.append(len(ev))
        for x in ev:
            q=float(x.get('outcome_quality',0));risk=x.get('choice_risk')
            if risk=='risky':risky_q.append(q)
            if risk=='stable':stable_q.append(q)
        inj_counts.append(len(p.injury_history));inj_missed.append(sum(int(x.get('games',0)) for x in p.injury_history));severe_count+=any(x.get('severity')=='중상' for x in p.injury_history)
        mvp+=any(x.get('award')=='MVP' and x.get('level')=='KBO' for x in p.awards);gg+=any(x.get('award')=='골든글러브' and x.get('level')=='KBO' for x in p.awards)
    peak_dist=Counter(bucket_peak(a) for a in peak_ages)
    career_report={
        'average_debut_age':round(statistics.mean(debut_ages),3) if debut_ages else None,'debut_failure_pct':round(debut_fail*100/careers,2),
        'average_first_team_PA':round(statistics.mean(first_pa),2),'average_farm_PA':round(statistics.mean(farm_pa),2),
        'average_peak_ability':round(statistics.mean(peaks),3),'average_peak_age':round(statistics.mean(peak_ages),3),'peak_age_distribution_pct':{k:round(peak_dist[k]*100/careers,2) for k in ('<22','22-25','26-29','30-33','34+')},
        'average_growth_explosions':round(statistics.mean(explosions),3),'talent_peak_ability_correlation':round(corr(talent_career,peaks),3),
        'events_per_season':round(sum(event_counts)/max(1,sum(season_counts)),3),'risky_success_pct':round(100*sum(q>0 for q in risky_q)/len(risky_q),2) if risky_q else 0.,'risky_disaster_pct':round(100*sum(q<=-2 for q in risky_q)/len(risky_q),2) if risky_q else 0.,'stable_mean_quality':round(statistics.mean(stable_q),3) if stable_q else 0.,'risky_quality_stddev':round(statistics.pstdev(risky_q),3) if risky_q else 0.,
        'average_injuries_per_career':round(statistics.mean(inj_counts),3),'severe_injury_experience_pct':round(severe_count*100/careers,2),'average_missed_games_from_injuries':round(statistics.mean(inj_missed),2),
        'retirement_age':summary(retire),'average_career_games':round(statistics.mean(career_g),2),'average_career_PA':round(statistics.mean(career_pa),2),'MVP_experience_pct':round(mvp*100/careers,2),'golden_glove_experience_pct':round(gg*100/careers,2)
    }

    base=PlayerStats(78,78,78,78,78,78,78,78,78,120);coach_report={}
    for kind in ('power','precision','balanced'):
        deltas={'contact':[],'power':[],'discipline':[],'peak_ability':[]}
        for i in range(coach_samples):
            p=Player('CoachTest',20,PlayerStats(**base.as_dict()),development_profile='normal');r=RNG(seed+200000+i);staff=CoachingStaff(generate_batting_coach(r,kind),generate_fielding_coach(r,'balanced'));peak=p.stats.current_ability();before=p.stats.as_dict()
            for _ in range(5):
                g=apply_season_growth(p,r,staff,GrowthExperience(180,260));peak=max(peak,g.ability_after)
            for stat in ('contact','power','discipline'):deltas[stat].append(getattr(p.stats,stat)-before[stat])
            deltas['peak_ability'].append(peak)
        coach_report[kind]={f'{k}_mean':round(statistics.mean(v),3) for k,v in deltas.items()}
        coach_report[kind]['ability_stddev']=round(statistics.pstdev(deltas['peak_ability']),3)

    event=EVENT_BY_ID['hamstring_warning'];event_report={}
    for choice in event.choices:
        qualities=[];severe=0;disaster=0;durability=[];ability_changes=[];missed=[]
        for i in range(event_samples):
            p=Player('EventTest',24,PlayerStats(85,85,85,85,85,85,85,85,85,110),development_profile='normal');before=p.stats.current_ability();erng=RNG(seed+300000+i);res=resolve_event(event,choice,p,erng,2032);entry=p.event_history[-1];qualities.append(float(entry['outcome_quality']));severe+=p.injury is not None and p.injury.severity=='중상';disaster+=entry['result']=='disaster';durability.append(res.stat_changes.get('durability',0));staff=CoachingStaff(generate_batting_coach(erng,'balanced'),generate_fielding_coach(erng,'balanced'));growth=apply_season_growth(p,erng,staff,GrowthExperience(250,200),res.growth_modifiers);ability_changes.append(growth.ability_after-before);missed.append(p.injury.games_remaining if p.injury else 0)
        event_report[choice.id]={'mean_quality':round(statistics.mean(qualities),3),'quality_stddev':round(statistics.pstdev(qualities),3),'disaster_pct':round(disaster*100/event_samples,2),'severe_injury_pct':round(severe*100/event_samples,2),'mean_durability_change':round(statistics.mean(durability),3),'post_event_ability_change_mean':round(statistics.mean(ability_changes),3),'post_event_ability_change_stddev':round(statistics.pstdev(ability_changes),3),'post_event_ability_change_p10':round(pct(ability_changes,.10),3),'mean_missed_games':round(statistics.mean(missed),2)}
    return {'samples':samples,'full_careers':careers,'generation':{'initial_ability':summary(abilities),'talent':summary([float(x) for x in talents])},'draft_pct':draft_pct,'career':career_report,'coach_comparison':coach_report,'hamstring_event_comparison':event_report}

def print_report(r:dict[str,object])->None:
    print(json.dumps(r,ensure_ascii=False,indent=2))
def main()->None:
    ap=argparse.ArgumentParser();ap.add_argument('--samples',type=int,default=1000);ap.add_argument('--careers',type=int,default=250);ap.add_argument('--coach-samples',type=int,default=100);ap.add_argument('--event-samples',type=int,default=1000);ap.add_argument('--seed',type=int,default=20260903);ap.add_argument('--output',default='');a=ap.parse_args();r=run_balance(a.samples,a.careers,a.coach_samples,a.event_samples,a.seed);print_report(r)
    if a.output:
        from pathlib import Path;Path(a.output).write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
if __name__=='__main__':main()
