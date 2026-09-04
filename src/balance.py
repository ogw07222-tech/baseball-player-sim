"""Monte Carlo balance report for v0.4.

The report intentionally separates generation/draft samples from full careers so
large-scale iteration remains practical while every career sample still runs
from high school through retirement.
"""
from __future__ import annotations
import argparse,json,math,statistics
from collections import Counter
from .career import CareerEngine
from .coaches import CoachingStaff,generate_batting_coach,generate_fielding_coach
from .events import EVENT_BY_ID,EventContext,resolve_event
from .growth import GrowthExperience,apply_season_growth
from .player import Player
from .rng import RNG
from .stats import PlayerStats

def pct(values:list[float],q:float)->float:
    if not values:return 0.0
    s=sorted(values);i=(len(s)-1)*q;lo=int(math.floor(i));hi=int(math.ceil(i))
    if lo==hi:return s[lo]
    return s[lo]*(hi-i)+s[hi]*(i-lo)
def desc(values:list[float],qs=(.1,.5,.9))->dict[str,float]:
    out={'mean':round(statistics.mean(values),3)} if values else {'mean':0.0}
    for q in qs:out[f'p{int(q*100)}']=round(pct(values,q),3) if values else 0.0
    return out
def corr(xs:list[float],ys:list[float])->float:
    if len(xs)<2:return 0.0
    mx,my=statistics.mean(xs),statistics.mean(ys);num=sum((x-mx)*(y-my) for x,y in zip(xs,ys));den=math.sqrt(sum((x-mx)**2 for x in xs)*sum((y-my)**2 for y in ys));return num/den if den else 0.0

def run_balance(samples:int=1000,careers:int=300,event_samples:int=3000,coach_samples:int=100,seed:int=20260904)->dict[str,object]:
    abilities=[];talents=[];draft=Counter()
    for i in range(samples):
        r=RNG(seed+i);p=Player.random('MC',r);abilities.append(p.stats.current_ability());talents.append(float(p.stats.talent));d=CareerEngine(p,r).evaluate_draft();draft['undrafted' if d.round is None else '1R' if d.round==1 else '2-3R' if d.round<=3 else '4-7R' if d.round<=7 else '8-11R']+=1
    generation={'initial_ability':desc(abilities),'ability_80_plus_pct':round(100*sum(v>=80 for v in abilities)/samples,2),'ability_90_plus_pct':round(100*sum(v>=90 for v in abilities)/samples,2),'talent':desc(talents)}
    draft_pct={k:round(100*draft[k]/samples,2) for k in ('1R','2-3R','4-7R','8-11R','undrafted')}

    debut=[];debut_fail=0;first_pa=[];farm_pa=[];farm_heavy_5y=0;peaks=[];peak_ages=[];talent_peak=[];inj_count=[];inj_missed=[];severe=0;retire=[];career_g=[];career_pa=[];mvp=gg=0;season_total=0
    category=Counter();tier=Counter();major_per=[];legend_per=[];breakthrough_deltas=[];major_deltas=[];legend_deltas=[]
    for i in range(careers):
        r=RNG(seed+100000+i);p=Player.random('Career',r);initial=p.stats.current_ability();e=CareerEngine(p,r);e.run_to_retirement();season_total+=len(p.seasons)
        first=p.first_team_career();farm=p.farm_career();first_pa.append(float(first.PA));farm_pa.append(float(farm.PA));career_g.append(float(first.G));career_pa.append(float(first.PA));retire.append(float(p.retirement_age or p.age));talent_peak.append(float(p.initial_talent or p.stats.talent))
        if p.debut_year is None:debut_fail+=1
        else:debut.append(float(18+p.debut_year-2026))
        farm_seasons=sum(1 for s in p.seasons if s.farm.PA>=200 and s.farm.PA>s.first_team.PA)
        farm_heavy_5y+=farm_seasons>=5
        points=[(initial,18)]
        for x in p.event_history:
            if x.get('ability_after') is not None:points.append((float(x['ability_after']),int(x.get('age',18))))
        for h in p.growth_history:points.append((float(h.get('ability_after',initial)),int(h.get('age_after',18))))
        pk,pa=max(points,key=lambda z:z[0]);peaks.append(pk);peak_ages.append(float(pa))
        ev=[x for x in p.event_history if x.get('event_id')!='coach_change'];m=l=0
        for x in ev:
            cat=str(x.get('category','other'));category[cat]+=1;bt=x.get('breakthrough_tier')
            if bt:
                tier[str(bt)]+=1;delta=float(x.get('ability_after',0))-float(x.get('ability_before',0));breakthrough_deltas.append(delta)
                if bt=='major_breakthrough':m+=1;major_deltas.append(delta)
                elif bt=='legendary_breakthrough':l+=1;legend_deltas.append(delta)
        major_per.append(m);legend_per.append(l)
        inj_count.append(float(len(p.injury_history)));inj_missed.append(float(sum(int(x.get('games',0)) for x in p.injury_history)));severe+=any(x.get('severity')=='중상' for x in p.injury_history)
        mvp+=any(x.get('award')=='MVP' and x.get('level')=='KBO' for x in p.awards);gg+=any(x.get('award')=='골든글러브' and x.get('level')=='KBO' for x in p.awards)

    # Event choice trade-off samples.
    ham=EVENT_BY_ID['hamstring_warning'];ham_report={}
    for choice in ham.choices:
        qualities=[];ability_delta=[];severe_n=0;missed=[]
        for i in range(event_samples):
            p=Player('Event',24,PlayerStats(90,90,90,90,90,90,90,90,90,110),development_profile='normal');before=p.stats.current_ability();r=RNG(seed+300000+i);res=resolve_event(ham,choice,p,r,2032,EventContext(2032,70,'mid','FIRST'));qualities.append(float(res.quality));ability_delta.append(p.stats.current_ability()-before);severe_n+=p.injury is not None and p.injury.severity=='중상';missed.append(float(p.injury.games_remaining if p.injury else 0))
        ham_report[choice.id]={'mean_quality':round(statistics.mean(qualities),3),'quality_stddev':round(statistics.pstdev(qualities),3),'direct_ability_change_mean':round(statistics.mean(ability_delta),3),'direct_ability_change_stddev':round(statistics.pstdev(ability_delta),3),'severe_injury_pct':round(100*severe_n/event_samples,2),'mean_missed_games':round(statistics.mean(missed),2)}
    mech=EVENT_BY_ID['batting_mechanics_complete'];major_choice={}
    for choice in mech.choices:
        ds=[]
        for i in range(event_samples):
            p=Player('Break',26,PlayerStats(92,92,92,92,92,92,92,92,92,120),development_profile='normal');before=p.stats.current_ability();r=RNG(seed+400000+i);resolve_event(mech,choice,p,r,2034,EventContext(2034,80,'mid','FIRST'));ds.append(p.stats.current_ability()-before)
        major_choice[choice.id]={'mean_ability_change':round(statistics.mean(ds),3),'stddev':round(statistics.pstdev(ds),3),'p10':round(pct(ds,.1),3),'p90':round(pct(ds,.9),3)}

    base=PlayerStats(82,82,82,82,82,82,82,82,82,120);coach_report={}
    for kind in ('power','precision','balanced'):
        c={'contact':[],'power':[],'discipline':[],'peak':[]}
        for i in range(coach_samples):
            p=Player('Coach',20,PlayerStats(**base.as_dict()),development_profile='normal');r=RNG(seed+500000+i);staff=CoachingStaff(generate_batting_coach(r,kind),generate_fielding_coach(r,'balanced'));before=p.stats.as_dict();peak=p.stats.current_ability()
            for _ in range(5):peak=max(peak,apply_season_growth(p,r,staff,GrowthExperience(180,260)).ability_after)
            for stat in ('contact','power','discipline'):c[stat].append(float(getattr(p.stats,stat)-before[stat]))
            c['peak'].append(peak)
        coach_report[kind]={'contact_change_mean':round(statistics.mean(c['contact']),3),'power_change_mean':round(statistics.mean(c['power']),3),'discipline_change_mean':round(statistics.mean(c['discipline']),3),'peak_ability_mean':round(statistics.mean(c['peak']),3),'peak_stddev':round(statistics.pstdev(c['peak']),3)}

    total_events=sum(category.values())
    career={
        'debut_age':desc(debut),'debut_19_or_younger_pct':round(100*sum(a<=19 for a in debut)/careers,2),'debut_21_or_younger_pct':round(100*sum(a<=21 for a in debut)/careers,2),'debut_failure_pct':round(100*debut_fail/careers,2),
        'first_team_PA':desc(first_pa),'farm_PA':desc(farm_pa),'farm_heavy_5plus_year_pct':round(100*farm_heavy_5y/careers,2),
        'peak_ability':desc(peaks,(.5,.9,.95,.99)),'peak_age':desc(peak_ages),'talent_peak_correlation':round(corr(talent_peak,peaks),3),
        'events_per_season':round(total_events/max(1,season_total),3),'event_category_pct':{k:round(100*category[k]/max(1,total_events),2) for k in ('training','performance','injury','breakthrough')},'major_breakthrough_per_season':round(tier['major_breakthrough']/max(1,season_total),3),'legendary_breakthrough_per_season':round(tier['legendary_breakthrough']/max(1,season_total),3),
        'major_per_career':{'mean':round(statistics.mean(major_per),3),'zero_pct':round(100*sum(x==0 for x in major_per)/careers,2),'one_pct':round(100*sum(x==1 for x in major_per)/careers,2),'two_plus_pct':round(100*sum(x>=2 for x in major_per)/careers,2)},
        'legendary_per_career':{'mean':round(statistics.mean(legend_per),3),'zero_pct':round(100*sum(x==0 for x in legend_per)/careers,2),'one_pct':round(100*sum(x==1 for x in legend_per)/careers,2),'two_plus_pct':round(100*sum(x>=2 for x in legend_per)/careers,2)},
        'breakthrough_direct_ability_change_mean':round(statistics.mean(breakthrough_deltas),3) if breakthrough_deltas else 0.,'major_direct_ability_change_mean':round(statistics.mean(major_deltas),3) if major_deltas else 0.,'legendary_direct_ability_change_mean':round(statistics.mean(legend_deltas),3) if legend_deltas else 0.,
        'injuries_per_career':round(statistics.mean(inj_count),3),'severe_injury_experience_pct':round(100*severe/careers,2),'missed_games_from_injuries_mean':round(statistics.mean(inj_missed),2),
        'retirement_age':desc(retire),'career_games_mean':round(statistics.mean(career_g),2),'career_PA_mean':round(statistics.mean(career_pa),2),'MVP_experience_pct':round(100*mvp/careers,2),'golden_glove_experience_pct':round(100*gg/careers,2),
    }
    return {'seed':seed,'samples':samples,'full_careers':careers,'event_samples_per_choice':event_samples,'generation':generation,'draft_pct':draft_pct,'career':career,'hamstring_choice_comparison':ham_report,'major_choice_comparison':major_choice,'coach_comparison':coach_report}

def main()->None:
    ap=argparse.ArgumentParser();ap.add_argument('--samples',type=int,default=1000);ap.add_argument('--careers',type=int,default=300);ap.add_argument('--event-samples',type=int,default=3000);ap.add_argument('--coach-samples',type=int,default=100);ap.add_argument('--seed',type=int,default=20260904);ap.add_argument('--output',default='');a=ap.parse_args();r=run_balance(a.samples,a.careers,a.event_samples,a.coach_samples,a.seed);text=json.dumps(r,ensure_ascii=False,indent=2);print(text)
    if a.output:
        from pathlib import Path;Path(a.output).write_text(text,encoding='utf-8')
if __name__=='__main__':main()
