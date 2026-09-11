"""In-season roster and career-event time-axis flow."""
from __future__ import annotations
from . import config
from .career_core import ProSeasonSession, EventDecider
from .events import CareerEvent, EventChoice, EventContext, EventResolution, EVENT_CATALOG, EVENT_BY_ID, auto_choose, eligible, event_weight, resolve_event
from .simulation import logistic_range, simulate_player_game

class CareerSeasonMixin:
    def _reconsider_roster(self,s:ProSeasonSession)->None:
        if s.games_completed==0 or s.games_completed%10:return
        team=self._team_config();competition=float(team['depth'])+config.POSITION_COMPETITION.get(self.player.position,0)-config.CALLUP_COMPETITION_OFFSET;line=s.record.first_team if s.current_level=='FIRST' else s.record.farm;form_bonus=max(-12.,min(15.,(line.OPS-.75)*25.)) if line.PA>=20 else 0.;evaluation=self.player.stats.current_ability()+form_bonus+self.rng.gauss(0,5.5)
        if s.current_level=='FARM' and evaluation>=competition:
            callup_chance=logistic_range(self.player.stats.current_ability()-90.0,.025,.88,4.8)
            if self.player.draft_info and self.player.draft_info.get('round')==1:callup_chance=min(.94,callup_chance+.07)
            if form_bonus>=6:callup_chance=min(.94,callup_chance+.05)
            if self.rng.random()<callup_chance:s.current_level='FIRST';self.player.roster_level='FIRST';self.player.debut_year=self.player.debut_year or self.year
        elif s.current_level=='FIRST' and line.PA>=30:
            established=self.player.first_team_career().PA+s.record.first_team.PA>=config.ESTABLISHED_FIRST_TEAM_PA;margin=config.ESTABLISHED_DEMOTION_MARGIN if established else config.REGULAR_DEMOTION_MARGIN
            if evaluation<competition-margin:s.current_level='FARM';self.player.roster_level='FARM'
    @staticmethod
    def _season_phase(game_number:int)->str:
        if game_number<=0:return 'preseason'
        if game_number<=45:return 'early'
        if game_number<=100:return 'mid'
        return 'late'
    def _event_context(self,s:ProSeasonSession,phase:str|None=None,game_number:int|None=None)->EventContext:
        staff=self.current_coaching_staff();return EventContext(self.year,s.games_completed if game_number is None else game_number,phase or self._season_phase(s.games_completed),s.current_level,s.record.first_team.PA,s.record.farm.PA,staff.batting_coach.archetype)
    def _career_seen(self,event_id:str)->bool:return any(e.get('event_id')==event_id for e in self.player.event_history)
    def _event_candidates(self,s:ProSeasonSession,ctx:EventContext)->list[CareerEvent]:
        out=[]
        for event in EVENT_CATALOG:
            if event.once_per_season and event.id in s.occurred_event_ids:continue
            if event.career_once and self._career_seen(event.id):continue
            if ctx.game_number<s.cooldown_until.get(event.id,0):continue
            if ctx.season_phase!='preseason' and ctx.game_number-s.last_event_game<config.EVENT_MIN_GAP_GAMES:continue
            if eligible(event,self.player,ctx):out.append(event)
        return out
    def _queue_event(self,s:ProSeasonSession,event:CareerEvent,ctx:EventContext)->None:s.pending_event_id=event.id;s.pending_event_game=ctx.game_number;s.pending_event_phase=ctx.season_phase
    def pending_event(self)->CareerEvent|None:
        s=self.current_session;return EVENT_BY_ID[s.pending_event_id] if s and s.pending_event_id else None
    def resolve_pending_event(self,choice:EventChoice|None=None,event_decider:EventDecider|None=None)->EventResolution:
        s=self.start_pro_season()
        if not s.pending_event_id:raise RuntimeError('no pending event')
        event=EVENT_BY_ID[s.pending_event_id];ctx=self._event_context(s,s.pending_event_phase or self._season_phase(s.games_completed),s.pending_event_game if s.pending_event_game is not None else s.games_completed);picked=choice or (event_decider(event,self.player) if event_decider else auto_choose(event,self.player,self.rng))
        injury_before=self.player.injury.as_dict() if self.player.injury else None;form_before={'form':self.player.form,'games_remaining':self.player.form_games_remaining};traits_before={t.key for t in self.player.traits}
        resolution=resolve_event(event,picked,self.player,self.rng,self.year,ctx)
        event_identity=f'event_history:{self.year}:{len(self.player.event_history)-1}' if self.player.event_history else None;injury_after=self.player.injury.as_dict() if self.player.injury else None;form_after={'form':self.player.form,'games_remaining':self.player.form_games_remaining};traits_after={t.key for t in self.player.traits}
        if injury_before!=injury_after:
            if injury_before is None and injury_after is not None:fact_type='injury_created'
            elif injury_before is not None and injury_after is None:fact_type='injury_cleared'
            else:fact_type='injury_changed'
            self._emit_source_fact(fact_type,before={'injury':injury_before},after={'injury':injury_after},authoritative_state_delta={'injury':{'before':injury_before,'after':injury_after}},persistence_hint='event_history',existing_identity=event_identity,game_number=ctx.game_number)
        if form_before['form']!=form_after['form']:
            self._emit_source_fact('form_transition',before=form_before,after=form_after,authoritative_state_delta={'form':{'before':form_before['form'],'after':form_after['form']}},persistence_hint='event_history',existing_identity=event_identity,game_number=ctx.game_number)
        for key in sorted(traits_before-traits_after):self._emit_source_fact('trait_lost',before={'trait_present':key},after={'trait_present':None},authoritative_state_delta={'trait':{'action':'lost','trait':key}},persistence_hint='event_history',existing_identity=event_identity,game_number=ctx.game_number)
        for key in sorted(traits_after-traits_before):self._emit_source_fact('trait_gained',before={'trait_present':None},after={'trait_present':key},authoritative_state_delta={'trait':{'action':'gained','trait':key}},persistence_hint='event_history',existing_identity=event_identity,game_number=ctx.game_number)
        if resolution.stat_changes:
            self._emit_source_fact('event_rating_change',before={'ability':resolution.ability_before},after={'ability':resolution.ability_after},authoritative_state_delta={'rating_deltas':dict(resolution.stat_changes),'ability':{'before':resolution.ability_before,'after':resolution.ability_after}},persistence_hint='event_history',existing_identity=event_identity,game_number=ctx.game_number)
        s.growth_modifiers.merge(resolution.growth_modifiers);s.occurred_event_ids.append(event.id);s.cooldown_until[event.id]=ctx.game_number+event.cooldown_games;s.last_event_game=ctx.game_number;s.pending_event_id=None;s.pending_event_game=None;s.pending_event_phase=None;self.last_event_resolutions.append(resolution);return resolution
    def _maybe_event(self,s:ProSeasonSession,event_decider:EventDecider|None,stop_on_event:bool,preseason:bool=False)->bool:
        if s.has_pending_event:return True
        phase='preseason' if preseason else self._season_phase(s.games_completed);ctx=self._event_context(s,phase,0 if preseason else s.games_completed);chance=config.EVENT_PRESEASON_CHANCE if preseason else config.EVENT_BASE_CHANCE_PER_GAME
        if self.rng.random()>=chance:return False
        candidates=self._event_candidates(s,ctx)
        if not candidates:return False
        event=self.rng.weighted_choice([(e,event_weight(e,self.player,ctx)) for e in candidates]);self._queue_event(s,event,ctx)
        if stop_on_event and event_decider is None:return True
        self.resolve_pending_event(event_decider=event_decider);return False
    def _check_preseason(self,s:ProSeasonSession,event_decider:EventDecider|None,stop_on_event:bool)->bool:
        if s.preseason_checked:return s.has_pending_event
        s.preseason_checked=True;return self._maybe_event(s,event_decider,stop_on_event,preseason=True)
    def advance_pro_games(self,count:int,event_decider:EventDecider|None=None,stop_on_event:bool=False)->ProSeasonSession:
        if count<=0:raise ValueError('count must be positive')
        s=self.start_pro_season();team=self._team_config()
        if self._check_preseason(s,event_decider,stop_on_event):return s
        if s.has_pending_event:return s
        for _ in range(min(count,config.KBO_FIRST_TEAM_GAMES-s.games_completed)):
            s.games_completed+=1
            if self.player.injury:self._recover_day();self._update_form();self._reconsider_roster(s)
            elif self.rng.random()>=self._play_probability(s.current_level):self._recover_day();self._update_form();self._reconsider_roster(s)
            else:
                target=s.record.first_team if s.current_level=='FIRST' else s.record.farm;level=float(team['first_team_level'] if s.current_level=='FIRST' else team['farm_level']);simulate_player_game(self.player,level,self.rng,target)
                if s.current_level=='FIRST' and self.player.debut_year is None:self.player.debut_year=self.year
                self._fatigue_after_game();self._maybe_injure();self._update_form();self._reconsider_roster(s)
            if self._maybe_event(s,event_decider,stop_on_event):break
        return s
    def advance_to_season_end(self,event_decider:EventDecider|None=None,interactive:bool=False)->ProSeasonSession:
        s=self.start_pro_season()
        if s.has_pending_event:return s
        return self.advance_pro_games(max(1,config.KBO_FIRST_TEAM_GAMES-s.games_completed),event_decider,stop_on_event=interactive)
