"""Career finalization facade; season/draft flow lives in career_core."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from . import config
from .career_core import CareerEngineBase, TournamentResult, DraftResult, ProSeasonSession, EventDecider
from .career_season import CareerSeasonMixin
from .coaches import CoachingStaff, generate_batting_coach, generate_fielding_coach
from .growth import GrowthExperience, GrowthResult, apply_season_growth
from .records import SeasonRecord
from .traits import TRAIT_CATALOG, has_trait, traits_conflict


@dataclass(frozen=True)
class SeasonFinalizationResult:
    completed_year:int
    next_year:int
    age_before:int
    age_after:int
    record:SeasonRecord
    growth:GrowthResult
    awards:tuple[str,...]

    def as_dict(self)->dict[str,object]:
        return {
            'completed_year':self.completed_year,
            'next_year':self.next_year,
            'age_before':self.age_before,
            'age_after':self.age_after,
            'record':self.record.as_dict(),
            'growth':{
                'age_before':self.growth.age_before,
                'age_after':self.growth.age_after,
                'deltas':dict(self.growth.deltas),
                'explosion':self.growth.explosion,
                'ability_before':self.growth.ability_before,
                'ability_after':self.growth.ability_after,
            },
            'awards':list(self.awards),
        }


class CareerEngine(CareerSeasonMixin, CareerEngineBase):
    def _determine_awards(self,record:SeasonRecord)->list[str]:
        line=record.first_team
        if line.PA<300:return []
        rivals=[]
        for _ in range(9):
            avg=max(.210,min(.360,self.rng.gauss(.275,.027)));hr=max(1.,self.rng.gauss(22,10));rbi=max(20.,self.rng.gauss(78,20));sb=max(0.,self.rng.gauss(14,11));ops=max(.600,min(1.080,self.rng.gauss(.790,.085)));defense=self.rng.gauss(100,13);rivals.append({'AVG':avg,'HR':hr,'RBI':rbi,'SB':sb,'DEF':defense,'MVP':ops*100+hr*.55+rbi*.10+sb*.05})
        a=[]
        if line.AVG>max(r['AVG'] for r in rivals):a.append('타격왕')
        if line.HR>max(r['HR'] for r in rivals):a.append('홈런왕')
        if line.RBI>max(r['RBI'] for r in rivals):a.append('타점왕')
        if line.SB>max(r['SB'] for r in rivals):a.append('도루왕')
        defense_score=self.player.stats.defense+(8 if has_trait(self.player.traits,'defense_sense') else 0)+self.rng.gauss(0,7)
        if line.G>=80 and defense_score>max(r['DEF'] for r in rivals):a.append('골든글러브')
        mvp=line.OPS*100+line.HR*.55+line.RBI*.10+line.SB*.05
        if mvp>max(r['MVP'] for r in rivals):a.append('MVP')
        return a
    def _maybe_change_trait(self)->None:
        if self.player.traits and self.rng.random()<.018:
            removed=self.rng.choice(self.player.traits);self.player.traits.remove(removed);self.player.trait_history.append({'year':self.year,'action':'lost','trait':removed.key})
        if len(self.player.traits)>=7 or self.rng.random()>=.045:return
        c=[t for t in TRAIT_CATALOG if t not in self.player.traits and not any(traits_conflict(t,e) for e in self.player.traits)]
        if c:
            gained=self.rng.choice(c);self.player.traits.append(gained);self.player.trait_history.append({'year':self.year,'action':'gained','trait':gained.key})
    def _maybe_replace_coaches(self)->None:
        self._ensure_coaches()
        for team,staff in list(self.team_coaches.items()):
            batting=staff.batting_coach;fielding=staff.fielding_coach;changes=[]
            if self.rng.random()<config.COACH_REPLACEMENT_CHANCE:batting=generate_batting_coach(self.rng);changes.append(f'batting:{batting.archetype}')
            if self.rng.random()<config.COACH_REPLACEMENT_CHANCE:fielding=generate_fielding_coach(self.rng);changes.append(f'fielding:{fielding.archetype}')
            if changes:
                self.team_coaches[team]=CoachingStaff(batting,fielding);entry={'year':self.year,'team':team,'changes':changes};self.coach_history.append(entry)
                if team==self.player.team:self.player.event_history.append({'year':self.year,'age':self.player.age,'game_number':144,'season_phase':'offseason','event_id':'coach_change','event_name':'코칭스태프 교체','rarity':'system','category':'coach','choice':'none','chosen_option':'none','choice_risk':'none','outcome':'change','result':','.join(changes),'outcome_quality':0,'stat_changes':{},'temporary_effects':{},'trait_changes':[],'injury_changes':'none'})
    def finalize_completed_pro_season(self)->SeasonFinalizationResult:
        if self.phase!='PRO':raise RuntimeError('career is not in professional phase')
        s=self.current_session
        if s is None:raise RuntimeError('no active professional season to finalize')
        if not s.finished:raise RuntimeError('professional season is not complete')
        if s.has_pending_event:raise RuntimeError('cannot finalize professional season with a pending event')
        completed_year=self.year;age_before=self.player.age
        awards=self._determine_awards(s.record);s.record.awards.extend(awards)
        for award in awards:self.player.awards.append({'year':self.year,'award':award,'level':'KBO'})
        self.player.seasons.append(s.record)
        exp=GrowthExperience(s.record.first_team.PA,s.record.farm.PA)
        growth=apply_season_growth(self.player,self.rng,self.current_coaching_staff(),exp,s.growth_modifiers)
        self._maybe_change_trait();self._maybe_replace_coaches();self.year+=1;self.current_session=None
        self.player.clear_season_modifiers();self.player.form='normal';self.player.form_games_remaining=0;self.player.fatigue=max(0.,self.player.fatigue*.25)
        return SeasonFinalizationResult(completed_year,self.year,age_before,self.player.age,s.record,growth,tuple(awards))
    def finish_pro_season(self,event_decider:EventDecider|None=None)->tuple[SeasonRecord,GrowthResult]:
        s=self.start_pro_season()
        if s.has_pending_event:self.resolve_pending_event(event_decider=event_decider)
        while not s.finished:
            self.advance_to_season_end(event_decider=event_decider,interactive=False)
            if s.has_pending_event:self.resolve_pending_event(event_decider=event_decider)
        if s.has_pending_event:self.resolve_pending_event(event_decider=event_decider)
        finalized=self.finalize_completed_pro_season();return finalized.record,finalized.growth
    def should_retire(self)->bool:
        if self.player.age>=config.RETIREMENT_HARD_AGE:return True
        recent=self.player.seasons[-2:];pa=sum(s.first_team.PA for s in recent);ability=self.player.stats.current_ability();chance=0.
        if self.player.age>=35:chance+=.05+(self.player.age-35)*.055
        if self.player.age>=30 and pa<80:chance+=.08
        if self.player.debut_year is None and self.player.age>=27:
            chance+=.18+(self.player.age-27)*.08
            if ability<90:chance+=.08
        if ability<72:chance+=.08
        if self.player.injury and self.player.injury.severity=='중상':chance+=.07
        if self.player.age<27:chance*=.05
        return self.rng.random()<min(.92,chance)
    def retire(self)->None:self.phase='RETIRED';self.player.roster_level='RETIRED';self.player.retirement_age=self.player.age
    def run_to_retirement(self,max_seasons:int=30)->Player:
        if self.phase=='HIGH_SCHOOL':self.evaluate_draft()
        seasons=0
        while self.phase=='PRO' and seasons<max_seasons:
            self.finish_pro_season();seasons+=1
            if self.should_retire():self.retire()
        if self.phase=='PRO':self.retire()
        return self.player
    def as_dict(self)->dict[str,object]:return {'year':self.year,'tournament_index':self.tournament_index,'phase':self.phase,'tournament_results':self.tournament_results,'current_session':self.current_session.as_dict() if self.current_session else None,'team_coaches':{k:v.as_dict() for k,v in self.team_coaches.items()},'coach_history':self.coach_history}
    def restore_state(self,d:dict[str,Any])->None:
        self.year=int(d.get('year',self.year));self.tournament_index=int(d.get('tournament_index',0));self.phase=str(d.get('phase','HIGH_SCHOOL'));self.tournament_results=[dict(v) for v in d.get('tournament_results',[])];self.current_session=ProSeasonSession.from_dict(dict(d['current_session'])) if d.get('current_session') else None;self.team_coaches={str(k):CoachingStaff.from_dict(dict(v)) for k,v in dict(d.get('team_coaches',{})).items()};self.coach_history=[dict(v) for v in d.get('coach_history',[])]
