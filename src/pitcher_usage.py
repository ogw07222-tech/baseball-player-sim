"""Dynamic pitcher role, rotation, bullpen usage and recovery-debt foundation.

This module owns orchestration only. It never changes pitch outcome probabilities
or raw pitcher ratings. Exact pitch counts are used when available; the current
PR #28 provider otherwise falls back to four pitches per batter faced.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Iterable, Mapping, Sequence

class PitcherRole(str, Enum):
    STARTER="starter"; LONG_RELIEF="long_relief"; MIDDLE_RELIEF="middle_relief"; SETUP="setup"; CLOSER="closer"; SWINGMAN="swingman"
RELIEF_ROLES={r.value for r in (PitcherRole.LONG_RELIEF,PitcherRole.MIDDLE_RELIEF,PitcherRole.SETUP,PitcherRole.CLOSER,PitcherRole.SWINGMAN)}
class PitcherAvailability(str, Enum):
    AVAILABLE="AVAILABLE"; LIMITED="LIMITED"; TIRED="TIRED"; UNAVAILABLE="UNAVAILABLE"

CONSECUTIVE_LOAD_MULTIPLIERS={1:1.00,2:1.30,3:1.75,4:2.40}
ROLE_HOLD_DAYS=18; ROLE_HOLD_APPEARANCES=4; ROLE_EVALUATION_INTERVAL_DAYS=10; STARTER_REST_DAYS=4
PITCHES_PER_BF_FALLBACK=4.0; FATIGUE_RECOVERY_PER_DAY=18.0; DEBT_RECOVERY_PER_DAY=9.0
HEAVY_RELIEF_PITCHES=30.0; HEAVY_BACK_TO_BACK_DEBT=55.0
SECOND_DAY_BASE_DEBT=8.0; THIRD_DAY_BASE_DEBT=24.0; FOURTH_DAY_BASE_DEBT=48.0
RECENT_5_DAY_LIMITED=60.0; RECENT_5_DAY_UNAVAILABLE=100.0
STRESS_LIMITED=34.0; STRESS_TIRED=58.0; STRESS_UNAVAILABLE=82.0
STARTER_TARGET_PITCHES=95.0; STARTER_HARD_PITCHES=118.0
RELIEF_TARGET_BF={PitcherRole.LONG_RELIEF.value:10,PitcherRole.MIDDLE_RELIEF.value:6,PitcherRole.SETUP.value:5,PitcherRole.CLOSER.value:5,PitcherRole.SWINGMAN.value:9}

def _clamp(x:float,lo:float,hi:float)->float:return max(lo,min(hi,x))

@dataclass(frozen=True)
class PitcherUsageMember:
    pitcher_id:str; stamina:float=100.0; resilience:float=100.0

@dataclass(frozen=True)
class PitcherOuting:
    game_date:date; role:str; started:bool; BF:int; outs:int; H:int; R:int; HR:int; BB:int; HBP:int; SO:int; workload_pitches:float; emergency_reason:str|None=None
    def as_dict(self)->dict[str,object]:
        return {"date":self.game_date.isoformat(),"role":self.role,"started":self.started,"BF":self.BF,"outs":self.outs,"H":self.H,"R":self.R,"HR":self.HR,"BB":self.BB,"HBP":self.HBP,"SO":self.SO,"workload_pitches":self.workload_pitches,"emergency_reason":self.emergency_reason}
    @classmethod
    def from_dict(cls,d:Mapping[str,object])->"PitcherOuting":
        return cls(date.fromisoformat(str(d["date"])),str(d.get("role",PitcherRole.MIDDLE_RELIEF.value)),bool(d.get("started",False)),int(d.get("BF",0)),int(d.get("outs",0)),int(d.get("H",0)),int(d.get("R",0)),int(d.get("HR",0)),int(d.get("BB",0)),int(d.get("HBP",0)),int(d.get("SO",0)),float(d.get("workload_pitches",0.0)),str(d["emergency_reason"]) if d.get("emergency_reason") else None)

@dataclass
class PitcherSeasonUsageState:
    pitcher_id:str; current_role:str; previous_role:str|None=None; role_changed_at:date|None=None; role_change_appearances:int=0
    starter_appearances:int=0; relief_appearances:int=0; role_change_count:int=0; consecutive_days_used:int=0; days_since_last_appearance:int=999
    last_appearance_date:date|None=None; last_start_date:date|None=None; fatigue_load:float=0.0; recovery_debt:float=0.0; last_recovery_date:date|None=None
    recent_outings:list[PitcherOuting]=field(default_factory=list)
    def as_dict(self)->dict[str,object]:
        return {"pitcher_id":self.pitcher_id,"current_role":self.current_role,"previous_role":self.previous_role,"role_changed_at":self.role_changed_at.isoformat() if self.role_changed_at else None,"role_change_appearances":self.role_change_appearances,"starter_appearances":self.starter_appearances,"relief_appearances":self.relief_appearances,"role_change_count":self.role_change_count,"consecutive_days_used":self.consecutive_days_used,"days_since_last_appearance":self.days_since_last_appearance,"last_appearance_date":self.last_appearance_date.isoformat() if self.last_appearance_date else None,"last_start_date":self.last_start_date.isoformat() if self.last_start_date else None,"fatigue_load":self.fatigue_load,"recovery_debt":self.recovery_debt,"last_recovery_date":self.last_recovery_date.isoformat() if self.last_recovery_date else None,"recent_outings":[o.as_dict() for o in self.recent_outings]}
    @classmethod
    def from_dict(cls,d:Mapping[str,object])->"PitcherSeasonUsageState":
        def D(k):
            v=d.get(k); return date.fromisoformat(str(v)) if v else None
        raw=d.get("recent_outings",())
        outings=[PitcherOuting.from_dict(x) for x in raw if isinstance(x,Mapping)] if isinstance(raw,Sequence) and not isinstance(raw,(str,bytes)) else []
        return cls(str(d["pitcher_id"]),str(d.get("current_role",PitcherRole.MIDDLE_RELIEF.value)),str(d["previous_role"]) if d.get("previous_role") else None,D("role_changed_at"),int(d.get("role_change_appearances",0)),int(d.get("starter_appearances",0)),int(d.get("relief_appearances",0)),int(d.get("role_change_count",0)),int(d.get("consecutive_days_used",0)),int(d.get("days_since_last_appearance",999)),D("last_appearance_date"),D("last_start_date"),float(d.get("fatigue_load",0)),float(d.get("recovery_debt",0)),D("last_recovery_date"),outings[-8:])
    def can_change_role(self,on_date:date)->bool:
        return self.role_changed_at is None or ((on_date-self.role_changed_at).days>=ROLE_HOLD_DAYS and self.role_change_appearances>=ROLE_HOLD_APPEARANCES)

@dataclass
class TeamPitcherUsageState:
    team:str; pitchers:dict[str,PitcherSeasonUsageState]=field(default_factory=dict); rotation:list[str]=field(default_factory=list); rotation_index:int=0; last_role_evaluation_date:date|None=None
    role_switches:int=0; two_day_streaks:int=0; three_day_streaks:int=0; four_day_streaks:int=0; unavailable_usage_violations:int=0; bullpen_exhaustion_events:int=0
    def as_dict(self)->dict[str,object]:
        return {"team":self.team,"pitchers":{k:v.as_dict() for k,v in self.pitchers.items()},"rotation":list(self.rotation),"rotation_index":self.rotation_index,"last_role_evaluation_date":self.last_role_evaluation_date.isoformat() if self.last_role_evaluation_date else None,"role_switches":self.role_switches,"two_day_streaks":self.two_day_streaks,"three_day_streaks":self.three_day_streaks,"four_day_streaks":self.four_day_streaks,"unavailable_usage_violations":self.unavailable_usage_violations,"bullpen_exhaustion_events":self.bullpen_exhaustion_events}
    @classmethod
    def from_dict(cls,d:Mapping[str,object])->"TeamPitcherUsageState":
        rp=d.get("pitchers",{}); pitchers={str(k):PitcherSeasonUsageState.from_dict(v) for k,v in rp.items() if isinstance(v,Mapping)} if isinstance(rp,Mapping) else {}
        ev=d.get("last_role_evaluation_date")
        return cls(str(d.get("team","")),pitchers,[str(x) for x in d.get("rotation",())],int(d.get("rotation_index",0)),date.fromisoformat(str(ev)) if ev else None,int(d.get("role_switches",0)),int(d.get("two_day_streaks",0)),int(d.get("three_day_streaks",0)),int(d.get("four_day_streaks",0)),int(d.get("unavailable_usage_violations",0)),int(d.get("bullpen_exhaustion_events",0)))

@dataclass
class PitcherUsageLeagueState:
    teams:dict[str,TeamPitcherUsageState]=field(default_factory=dict)
    def team(self,name:str)->TeamPitcherUsageState:
        if name not in self.teams:self.teams[name]=TeamPitcherUsageState(name)
        return self.teams[name]
    def as_dict(self)->dict[str,object]:return {"teams":{k:v.as_dict() for k,v in self.teams.items()}}
    @classmethod
    def from_dict(cls,d:Mapping[str,object])->"PitcherUsageLeagueState":
        raw=d.get("teams",{}); return cls({str(k):TeamPitcherUsageState.from_dict(v) for k,v in raw.items() if isinstance(v,Mapping)} if isinstance(raw,Mapping) else {})

def initial_roles(members:Sequence[PitcherUsageMember])->dict[str,str]:
    if len(members)<7:raise ValueError("dynamic pitcher usage needs at least seven pitchers")
    roles={}
    for i,m in enumerate(members):
        role=PitcherRole.STARTER.value if i<5 else PitcherRole.LONG_RELIEF.value if i==5 else PitcherRole.MIDDLE_RELIEF.value if i in {6,7} else PitcherRole.SETUP.value if i==8 else PitcherRole.CLOSER.value if i==9 else PitcherRole.SWINGMAN.value if i==10 else PitcherRole.MIDDLE_RELIEF.value
        roles[m.pitcher_id]=role
    return roles

class PitcherUsageManager:
    def __init__(self,state:PitcherUsageLeagueState|None=None)->None:self.state=state or PitcherUsageLeagueState()
    def ensure_team(self,team:str,members:Sequence[PitcherUsageMember])->TeamPitcherUsageState:
        ts=self.state.team(team)
        if not ts.pitchers:
            roles=initial_roles(members); ts.pitchers={m.pitcher_id:PitcherSeasonUsageState(m.pitcher_id,roles[m.pitcher_id]) for m in members}; ts.rotation=[m.pitcher_id for m in members if roles[m.pitcher_id]==PitcherRole.STARTER.value]
        else:
            for m in members:
                if m.pitcher_id not in ts.pitchers:ts.pitchers[m.pitcher_id]=PitcherSeasonUsageState(m.pitcher_id,PitcherRole.MIDDLE_RELIEF.value)
            self._sync_rotation(ts)
        return ts
    def _sync_rotation(self,ts:TeamPitcherUsageState)->None:
        starters=[pid for pid,s in ts.pitchers.items() if s.current_role==PitcherRole.STARTER.value]; kept=[pid for pid in ts.rotation if pid in starters]; ts.rotation=kept+sorted(pid for pid in starters if pid not in kept); ts.rotation_index=(ts.rotation_index%len(ts.rotation)) if ts.rotation else 0
    def refresh_to(self,s:PitcherSeasonUsageState,on_date:date,resilience:float=100)->None:
        if s.last_recovery_date is None:s.last_recovery_date=on_date
        days=max(0,(on_date-s.last_recovery_date).days)
        if days:
            f=.80+max(0.,resilience)/500.; s.fatigue_load=max(0.,s.fatigue_load-days*FATIGUE_RECOVERY_PER_DAY*f); s.recovery_debt=max(0.,s.recovery_debt-days*DEBT_RECOVERY_PER_DAY*f); s.last_recovery_date=on_date
        if s.last_appearance_date is None:s.days_since_last_appearance=999
        else:
            s.days_since_last_appearance=max(0,(on_date-s.last_appearance_date).days)
            if s.days_since_last_appearance>1:s.consecutive_days_used=0
    def recent_five_day_workload(self,s:PitcherSeasonUsageState,on_date:date)->float:return sum(o.workload_pitches for o in s.recent_outings if 0<=(on_date-o.game_date).days<=4)
    def availability(self,s:PitcherSeasonUsageState,on_date:date,resilience:float=100)->PitcherAvailability:
        self.refresh_to(s,on_date,resilience); recent=self.recent_five_day_workload(s,on_date); stress=s.fatigue_load+s.recovery_debt
        if s.consecutive_days_used>=3 and s.days_since_last_appearance<=1:return PitcherAvailability.UNAVAILABLE
        if stress>=STRESS_UNAVAILABLE or recent>=RECENT_5_DAY_UNAVAILABLE:return PitcherAvailability.UNAVAILABLE
        if s.consecutive_days_used>=2 or stress>=STRESS_TIRED:return PitcherAvailability.TIRED
        if s.consecutive_days_used>=1 or stress>=STRESS_LIMITED or recent>=RECENT_5_DAY_LIMITED:return PitcherAvailability.LIMITED
        return PitcherAvailability.AVAILABLE
    def starter_eligible(self,s:PitcherSeasonUsageState,m:PitcherUsageMember,on_date:date)->bool:
        if s.current_role!=PitcherRole.STARTER.value:return False
        if s.last_start_date and (on_date-s.last_start_date).days<STARTER_REST_DAYS+1:return False
        return self.availability(s,on_date,m.resilience)!=PitcherAvailability.UNAVAILABLE
    def select_starter(self,team:str,members:Sequence[PitcherUsageMember],on_date:date)->tuple[str,str|None]:
        ts=self.ensure_team(team,members); mm={m.pitcher_id:m for m in members}; self._sync_rotation(ts)
        if not ts.rotation:raise RuntimeError("no starter in rotation")
        for off in range(len(ts.rotation)):
            i=(ts.rotation_index+off)%len(ts.rotation); pid=ts.rotation[i]
            if self.starter_eligible(ts.pitchers[pid],mm[pid],on_date):ts.rotation_index=(i+1)%len(ts.rotation); return pid,None
        c=[pid for pid,s in ts.pitchers.items() if s.current_role in {PitcherRole.SWINGMAN.value,PitcherRole.LONG_RELIEF.value}]
        for pid in sorted(c,key=lambda x:(-ts.pitchers[x].days_since_last_appearance,x)):
            if self.availability(ts.pitchers[pid],on_date,mm[pid].resilience)!=PitcherAvailability.UNAVAILABLE:return pid,"SPOT_START"
        pid=max(ts.rotation,key=lambda x:(ts.pitchers[x].days_since_last_appearance,x)); return pid,"ROTATION_EXHAUSTED"
    def starter_should_exit(self,stats,inning:int,stamina:float=100)->bool:
        outs=int(getattr(stats,"outs_pitched",getattr(stats,"outs",0))); bf=int(getattr(stats,"BF",0)); runs=int(getattr(stats,"R",getattr(stats,"ER",0))); hits=int(getattr(stats,"H",0)); walks=int(getattr(stats,"BB",0)); pitches=bf*PITCHES_PER_BF_FALLBACK; target=STARTER_TARGET_PITCHES+.12*(stamina-100); hard=STARTER_HARD_PITCHES+.10*(stamina-100)
        if pitches>=hard:return True
        if outs<9:return runs>=6 and bf>=16
        traffic=(hits+walks)/max(1,bf); score=.55*(pitches/max(65.,target))+.25*(runs/5.)+.20*(traffic/.35)
        if outs<15:return score>=1.05
        if outs<18:return score>=.90
        if inning<=7:return score>=.80
        if inning==8:return score>=.68
        return True
    def reliever_should_exit(self,s:PitcherSeasonUsageState,stats)->bool:
        bf=int(getattr(stats,"BF",0)); outs=int(getattr(stats,"outs_pitched",getattr(stats,"outs",0))); target=RELIEF_TARGET_BF.get(s.current_role,6)
        return bf>=target or (s.current_role in {PitcherRole.SETUP.value,PitcherRole.CLOSER.value} and outs>=3)
    def _role_fit(self,role:str,inning:int,margin:int)->float:
        close=abs(margin)<=3
        if inning>=9 and close:order={"closer":4,"setup":3,"middle_relief":2,"swingman":1.5,"long_relief":1}
        elif inning>=7 and close:order={"setup":4,"closer":3.2,"middle_relief":2.4,"swingman":1.6,"long_relief":1.2}
        elif inning<=5:order={"long_relief":4,"swingman":3.6,"middle_relief":2.5,"setup":1,"closer":.5}
        else:order={"middle_relief":4,"long_relief":3,"swingman":2.8,"setup":2.5,"closer":1.5}
        return order.get(role,0.)
    def select_reliever(self,team:str,members:Sequence[PitcherUsageMember],on_date:date,inning:int,score_margin:int,used_ids:Iterable[str])->tuple[str|None,str|None]:
        ts=self.ensure_team(team,members); mm={m.pitcher_id:m for m in members}; used=set(used_ids); c=[]; emergency=[]
        for pid,s in ts.pitchers.items():
            if pid in used or s.current_role==PitcherRole.STARTER.value:continue
            av=self.availability(s,on_date,mm[pid].resilience); stress=s.fatigue_load+s.recovery_debt; fit=self._role_fit(s.current_role,inning,score_margin)
            if av==PitcherAvailability.UNAVAILABLE:emergency.append((stress-fit*2,pid));continue
            pen={PitcherAvailability.AVAILABLE:0.,PitcherAvailability.LIMITED:1.5,PitcherAvailability.TIRED:3.}[av]; c.append((fit-pen-stress/100,pid))
        if c:c.sort(key=lambda x:(-x[0],x[1]));return c[0][1],None
        if emergency:emergency.sort();return emergency[0][1],"BULLPEN_EXHAUSTED"
        ts.bullpen_exhaustion_events+=1; return None,"NO_UNUSED_RELIEVER"
    def record_outing(self,team:str,member:PitcherUsageMember,on_date:date,role:str,*,started:bool,BF:int,outs:int,H:int=0,R:int=0,HR:int=0,BB:int=0,HBP:int=0,SO:int=0,pitches:float|None=None,emergency_reason:str|None=None)->PitcherOuting:
        ts=self.state.team(team); s=ts.pitchers[member.pitcher_id]; self.refresh_to(s,on_date,member.resilience); streak=s.consecutive_days_used+1 if s.last_appearance_date and (on_date-s.last_appearance_date).days==1 else 1; workload=float(pitches) if pitches is not None and pitches>0 else BF*PITCHES_PER_BF_FALLBACK; mult=CONSECUTIVE_LOAD_MULTIPLIERS[min(streak,4)]; s.fatigue_load+=workload; s.recovery_debt+=workload*(mult-1)
        if streak==2:s.recovery_debt+=SECOND_DAY_BASE_DEBT;ts.two_day_streaks+=1
        elif streak==3:s.recovery_debt+=THIRD_DAY_BASE_DEBT;ts.three_day_streaks+=1
        elif streak>=4:s.recovery_debt+=FOURTH_DAY_BASE_DEBT;ts.four_day_streaks+=1
        prev=s.recent_outings[-1] if s.recent_outings else None
        if streak>=2 and prev and prev.workload_pitches>=HEAVY_RELIEF_PITCHES and workload>=20 and not started:s.recovery_debt+=HEAVY_BACK_TO_BACK_DEBT
        o=PitcherOuting(on_date,role,started,BF,outs,H,R,HR,BB,HBP,SO,workload,emergency_reason); s.recent_outings=(s.recent_outings+[o])[-8:]; s.last_appearance_date=on_date;s.last_recovery_date=on_date;s.days_since_last_appearance=0;s.consecutive_days_used=streak;s.role_change_appearances+=1
        if started:s.starter_appearances+=1;s.last_start_date=on_date
        else:s.relief_appearances+=1
        return o
    def _recent(self,s:PitcherSeasonUsageState)->list[PitcherOuting]:return s.recent_outings[-5:]
    def performance_signal(self,s:PitcherSeasonUsageState,starter:bool)->float:
        outs=[o for o in self._recent(s) if o.started==starter]
        if not outs:return 0.
        bf=sum(o.BF for o in outs); op=sum(o.outs for o in outs)
        if bf<=0 or op<=0:return 0.
        r=sum(o.R for o in outs);h=sum(o.H for o in outs);bb=sum(o.BB for o in outs);hr=sum(o.HR for o in outs);so=sum(o.SO for o in outs);ra9=r*27/op;whip=(h+bb)*3/op;k=so/bf;bp=bb/bf;hp=hr/bf
        score=.35*_clamp((4.5-ra9)/2.5,-1,1)+.22*_clamp((1.35-whip)/.4,-1,1)+.18*_clamp((k-.20)/.10,-1,1)+.15*_clamp((.09-bp)/.06,-1,1)+.10*_clamp((.025-hp)/.025,-1,1)
        if starter:score+=.12*_clamp((op/len(outs)-15)/6,-1,1)-.12*(sum(o.outs<15 for o in outs)/len(outs))
        return score
    def starter_candidate_score(self,s:PitcherSeasonUsageState,m:PitcherUsageMember)->float:
        perf=self.performance_signal(s,s.current_role==PitcherRole.STARTER.value); relief=[o for o in self._recent(s) if not o.started]; multi=_clamp((sum(o.outs for o in relief)/max(1,len(relief)))/6,0,1); stamina=_clamp((m.stamina-80)/40,0,1); stability=.08 if s.current_role==PitcherRole.STARTER.value else 0.; return .60*perf+.22*stamina+.10*multi+stability
    def evaluate_roles(self,team:str,members:Sequence[PitcherUsageMember],on_date:date,*,force:bool=False)->tuple[tuple[str,str,str],...]:
        ts=self.ensure_team(team,members)
        if not force and ts.last_role_evaluation_date and (on_date-ts.last_role_evaluation_date).days<ROLE_EVALUATION_INTERVAL_DAYS:return ()
        ts.last_role_evaluation_date=on_date;mm={m.pitcher_id:m for m in members};dem=[];pro=[]
        for s in ts.pitchers.values():
            if not s.can_change_role(on_date):continue
            if s.current_role==PitcherRole.STARTER.value:
                rs=[o for o in self._recent(s) if o.started]
                if len(rs)>=3 and (self.performance_signal(s,True)<=-.45 or sum(o.outs<15 for o in rs)/len(rs)>=.80):dem.append((self.starter_candidate_score(s,mm[s.pitcher_id]),s))
            else:
                rr=[o for o in self._recent(s) if not o.started];bf=sum(o.BF for o in rr)
                if (len(rr)>=4 or bf>=20) and mm[s.pitcher_id].stamina>=88 and self.performance_signal(s,False)>=.35:pro.append((self.starter_candidate_score(s,mm[s.pitcher_id]),s))
        if not dem or not pro:return ()
        dem.sort(key=lambda x:(x[0],x[1].pitcher_id));pro.sort(key=lambda x:(-x[0],x[1].pitcher_id));cur,down=dem[0];rep,up=pro[0]
        if rep<cur+.28:return ()
        old=up.current_role;down.previous_role=down.current_role;down.current_role=PitcherRole.LONG_RELIEF.value;down.role_changed_at=on_date;down.role_change_appearances=0;down.role_change_count+=1;up.previous_role=old;up.current_role=PitcherRole.STARTER.value;up.role_changed_at=on_date;up.role_change_appearances=0;up.role_change_count+=1;ts.role_switches+=2;self._sync_rotation(ts)
        return ((down.pitcher_id,PitcherRole.STARTER.value,PitcherRole.LONG_RELIEF.value),(up.pitcher_id,old,PitcherRole.STARTER.value))
