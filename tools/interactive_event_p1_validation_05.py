from __future__ import annotations

import copy
import hashlib
import json
import math
import statistics
import time
from collections import Counter, defaultdict
from contextlib import nullcontext
from dataclasses import dataclass
from datetime import date
from unittest.mock import patch

from src.career import CareerEngine
from src.interactive_event_effects import (
    UnsupportedInteractiveEffect,
    apply_interactive_pre_form_effects,
    advance_interactive_effects_one_game,
    effect_state_for_engine,
    resolve_interactive_event_authoritatively,
)
from src.interactive_events import (
    DEFAULT_MAX_PENDING_EVENTS,
    DEFAULT_SEASON_EVENT_CAP,
    EVENT_BY_TYPE,
    EVENT_CATALOG,
    EVENT_STATUS_PENDING,
    InteractiveEvent,
    event_state_for_engine,
)
from src.persistence import deserialize_game, serialize_game
from src.player import Player
from src.production_advance import ProductionAdvanceService
from src.rng import RNG

SEASONS = 500
LONG_TERM_SEEDS = 80
RNG_PURITY_SEEDS = 40
PERF_SEASONS = 120
BASE_SEED = 20260912


def q(values, p):
    if not values:
        return None
    xs = sorted(values)
    if len(xs) == 1:
        return xs[0]
    pos = (len(xs) - 1) * p
    lo = int(math.floor(pos)); hi = int(math.ceil(pos))
    if lo == hi:
        return xs[lo]
    return xs[lo] + (xs[hi] - xs[lo]) * (pos - lo)


def summary(values):
    return {
        "n": len(values), "mean": statistics.fmean(values) if values else None,
        "median": q(values, .5), "p10": q(values, .1), "p25": q(values, .25),
        "p75": q(values, .75), "p90": q(values, .9), "min": min(values) if values else None,
        "max": max(values) if values else None,
    }


def sha(obj):
    raw = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str).encode()
    return hashlib.sha256(raw).hexdigest()


@dataclass
class DummyResult:
    user_player_id: str | None = None
    notable_events: tuple = ()
    def score_for(self, team): return (0, 0)
    def team_result_for(self, team): return "T"
    def player_line(self, player_id): return None


class DummyProvider:
    def run_game(self, fixture, rng, **kwargs):
        return DummyResult()


def make_engine(seed: int) -> CareerEngine:
    rng = RNG(seed)
    player = Player.random(f"V-{seed}", rng)
    player.team = "키움 히어로즈"
    player.roster_level = "FARM"
    engine = CareerEngine(player, rng, phase="PRO")
    engine.start_pro_season()
    engine.drain_source_facts()
    return engine


def attach_catalog_event(engine: CareerEngine, event_type: str, suffix: str = "x") -> InteractiveEvent:
    a = EVENT_BY_TYPE[event_type]
    s = event_state_for_engine(engine)
    e = InteractiveEvent(
        event_id=f"validation:{engine.year}:{event_type}:{suffix}", event_type=a.event_type,
        category=a.category, title=a.title, description=a.description,
        occurred_at=date(engine.year, 4, 1).isoformat(), generated_at=date(engine.year, 4, 1).isoformat(),
        season=engine.year, game_number=1, importance=a.importance, trigger_context={}, choices=a.choices,
        status=EVENT_STATUS_PENDING, dedupe_key=f"validation:{engine.year}:{event_type}:{suffix}", blocking=a.blocking,
    )
    s.events.append(e)
    return e


def support_matrix():
    rows = []
    supported_by_event = {}
    effect_plans = []
    for ai, a in enumerate(EVENT_CATALOG):
        supported = []
        for ci, c in enumerate(a.choices):
            e = make_engine(900000 + ai * 100 + ci)
            ev = attach_catalog_event(e, a.event_type, str(ci))
            before = serialize_game(e)
            try:
                resolve_interactive_event_authoritatively(engine=e, event_id=ev.event_id, choice_id=c.choice_id, resolved_at=date(e.year,4,2))
                cls = "SUPPORTED"; supported.append(c.choice_id)
                plans = [x.as_dict() for x in effect_state_for_engine(e).active_effects]
                effect_plans.extend(plans)
                detail = plans
            except UnsupportedInteractiveEffect as ex:
                cls = "UNSUPPORTED_BY_03"; detail = str(ex)
                assert serialize_game(e) == before, (a.event_type, c.choice_id, "unsupported mutated state")
            except Exception as ex:
                cls = "ERROR"; detail = f"{type(ex).__name__}: {ex}"
            rows.append({"event_type":a.event_type,"category":a.category,"choice_id":c.choice_id,"classification":cls,"detail":detail})
        supported_by_event[a.event_type] = tuple(supported)
    return rows, supported_by_event, effect_plans


def season_invariants(events):
    errors=[]
    ids=[e.event_id for e in events]; keys=[e.dedupe_key for e in events]
    if len(ids)!=len(set(ids)): errors.append("duplicate_event_id")
    if len(keys)!=len(set(keys)): errors.append("duplicate_dedupe_key")
    if len(events)>DEFAULT_SEASON_EVENT_CAP: errors.append("season_cap_bypass")
    by_type=defaultdict(list); by_cat=defaultdict(list)
    for e in events:
        by_type[e.event_type].append(e.game_number); by_cat[e.category].append(e.game_number)
    for typ,games in by_type.items():
        a=EVENT_BY_TYPE[typ]
        if len(games)>a.season_cap: errors.append(f"archetype_cap:{typ}")
        if a.once_per_season and len(games)>1: errors.append(f"once_per_season:{typ}")
        for x,y in zip(games,games[1:]):
            if y-x < a.cooldown_games: errors.append(f"event_cooldown:{typ}:{x}->{y}")
    for cat,games in by_cat.items():
        # category cooldown used is archetype-specific; validate each later event against previous emitted archetype's setting.
        cat_events=[e for e in events if e.category==cat]
        for prev,cur in zip(cat_events,cat_events[1:]):
            gap=cur.game_number-prev.game_number
            required=EVENT_BY_TYPE[prev.event_type].category_cooldown_games
            if gap < required: errors.append(f"category_cooldown:{cat}:{gap}<{required}")
    return errors


def run_season(seed: int, mode: str, supported_by_event):
    engine = make_engine(seed)
    service = ProductionAdvanceService(engine, game_provider=DummyProvider())
    generated=[]; pending_track=[]; failed_all=set(); supported_resolutions=0
    for _ in range(144):
        service.advance_one_game()
        generated.extend(service.drain_generated_interactive_events())
        state=event_state_for_engine(engine)
        if mode=="record_only":
            for ev in list(state.pending):
                state.resolve(ev.event_id, ev.choices[0].choice_id, None)
        elif mode=="authoritative":
            for ev in list(state.pending):
                choices=supported_by_event.get(ev.event_type, ())
                if not choices:
                    failed_all.add(ev.event_id); continue
                try:
                    service.resolve_interactive_event(ev.event_id, choices[0]); supported_resolutions += 1
                except UnsupportedInteractiveEffect:
                    failed_all.add(ev.event_id)
        elif mode=="unattended":
            pass
        else: raise ValueError(mode)
        pending_track.append(len(state.pending))
    return {
        "events": generated,
        "pending_track": pending_track,
        "final_pending": len(event_state_for_engine(engine).pending),
        "failed_all": len(failed_all),
        "supported_resolutions": supported_resolutions,
        "engine": engine,
        "service": service,
    }


def frequency_distribution(supported_by_event):
    seasons=[]; cat=Counter(); arch=Counter(); diversity=[]; invariant_errors=[]
    unsupported_event_count=all_unsupported_event_count=0; total_event_count=0
    per_arch_absent=Counter({a.event_type:0 for a in EVENT_CATALOG})
    cap_hits=zero=0
    for i in range(SEASONS):
        r=run_season(BASE_SEED+i,"record_only",supported_by_event); events=r["events"]
        n=len(events); seasons.append(n); zero += n==0; cap_hits += n>=DEFAULT_SEASON_EVENT_CAP
        cats={e.category for e in events}; diversity.append(len(cats))
        seen={e.event_type for e in events}
        for a in EVENT_CATALOG:
            if a.event_type not in seen: per_arch_absent[a.event_type]+=1
        for e in events:
            cat[e.category]+=1; arch[e.event_type]+=1; total_event_count+=1
            supports=supported_by_event[e.event_type]
            if len(supports)<len(e.choices): unsupported_event_count+=1
            if len(supports)==0: all_unsupported_event_count+=1
        invariant_errors.extend(season_invariants(events))
    total=sum(cat.values())
    return {
        "season_event_count": summary(seasons), "zero_event_season_rate":zero/SEASONS,
        "season_cap_hit_rate":cap_hits/SEASONS,"category_counts":dict(cat),
        "category_share":{k:v/total for k,v in cat.items()},"category_diversity":summary(diversity),
        "archetype_counts":dict(arch),"archetype_share":{k:v/total for k,v in arch.items()},
        "archetype_absent_season_rate":{k:v/SEASONS for k,v in per_arch_absent.items()},
        "total_events":total_event_count,
        "events_with_any_unsupported_choice_rate":unsupported_event_count/max(1,total_event_count),
        "all_choices_unsupported_event_rate":all_unsupported_event_count/max(1,total_event_count),
        "invariant_errors":Counter(invariant_errors),
    }


def pending_queue(supported_by_event):
    out={}
    for mode in ("unattended","authoritative"):
        finals=[]; maxed_seasons=0; maxed_game_states=0; total_states=0; generated=[]; failed=[]
        for i in range(SEASONS):
            r=run_season(BASE_SEED+10000+i,mode,supported_by_event)
            finals.append(r["final_pending"]); generated.append(len(r["events"])); failed.append(r["failed_all"])
            if any(v>=DEFAULT_MAX_PENDING_EVENTS for v in r["pending_track"]): maxed_seasons+=1
            maxed_game_states+=sum(v>=DEFAULT_MAX_PENDING_EVENTS for v in r["pending_track"]); total_states+=len(r["pending_track"])
        out[mode]={"final_pending":summary(finals),"generated_events":summary(generated),
                   "seasons_ever_max_pending_rate":maxed_seasons/SEASONS,
                   "game_states_at_max_pending_rate":maxed_game_states/total_states,
                   "all_unsupported_left_pending":summary(failed)}
    return out


def effect_magnitude(effect_plans):
    growth_totals=[]; fatigue_totals=[]; durations=[]; noops=[]
    for p in effect_plans:
        durations.append(p["games_remaining"]); params=p["parameters"]
        if "mean_per_game" in params: growth_totals.append(params["mean_per_game"]*p["games_remaining"])
        if "fatigue_delta_per_game" in params: fatigue_totals.append(params["fatigue_delta_per_game"]*p["games_remaining"])
        if p["effect_type"]=="form_modifier" and not params.get("duration_delta"): noops.append(p)
    # Explicit expiration/clamp check.
    e=make_engine(880001); e.player.fatigue=99.0; ev=attach_catalog_event(e,"fatigue_management","mag")
    resolve_interactive_event_authoritatively(engine=e,event_id=ev.event_id,choice_id="push",resolved_at=None)
    apply_interactive_pre_form_effects(e); fatigue_after_cost=e.player.fatigue
    for _ in range(7): advance_interactive_effects_one_game(e)
    expired=(len(effect_state_for_engine(e).active_effects)==0)
    return {"growth_configured_total_delta":summary(growth_totals),"fatigue_configured_total_delta":summary(fatigue_totals),
            "duration_games":summary(durations),"fatigue_upper_clamp_probe":fatigue_after_cost,
            "expiration_exact_probe":expired,"empty_form_parameter_plans":len(noops)}


def run_full_season_pair(seed, supported_by_event):
    initial=make_engine(seed); payload=serialize_game(initial)
    enabled=deserialize_game(copy.deepcopy(payload)); control=deserialize_game(copy.deepcopy(payload))
    es=ProductionAdvanceService(enabled,game_provider=DummyProvider()); cs=ProductionAdvanceService(control,game_provider=DummyProvider())
    # Enabled: production generator + first authoritative supported choice; all-unsupported remain pending.
    for _ in range(144):
        es.advance_one_game(); es.drain_generated_interactive_events()
        for ev in list(es.pending_interactive_events):
            choices=supported_by_event.get(ev.event_type,())
            if choices:
                try: es.resolve_interactive_event(ev.event_id,choices[0])
                except UnsupportedInteractiveEffect: pass
    # Control: no EVENT generation at all.
    with patch("src.production_advance.maybe_generate_interactive_event", return_value=None):
        for _ in range(144): cs.advance_one_game(); cs.drain_generated_interactive_events()
    pre_enabled={"stats":enabled.player.stats.as_dict(),"fatigue":enabled.player.fatigue,"form":enabled.player.form,
                 "mods":dict(enabled.current_session.growth_modifiers.mean_by_stat),"pending":len(event_state_for_engine(enabled).pending)}
    pre_control={"stats":control.player.stats.as_dict(),"fatigue":control.player.fatigue,"form":control.player.form,
                 "mods":dict(control.current_session.growth_modifiers.mean_by_stat)}
    # finalize even with interactive pending: they are distinct from legacy CareerSession pending event.
    eg=es.finalize_season(); cg=cs.finalize_season()
    return enabled,control,pre_enabled,pre_control,eg,cg


def long_term(supported_by_event):
    ability=[]; rating_abs=[]; fatigue=[]; growth_ability=[]; pending=[]; form_diff=0
    per_stat=defaultdict(list)
    for i in range(LONG_TERM_SEEDS):
        en,co,pe,pc,eg,cg=run_full_season_pair(BASE_SEED+20000+i,supported_by_event)
        a=en.player.stats.current_ability()-co.player.stats.current_ability(); ability.append(a)
        deltas={k:en.player.stats.as_dict()[k]-co.player.stats.as_dict()[k] for k in en.player.stats.as_dict() if isinstance(en.player.stats.as_dict()[k],(int,float))}
        rating_abs.append(statistics.fmean(abs(v) for v in deltas.values()))
        for k,v in deltas.items(): per_stat[k].append(v)
        fatigue.append(pe["fatigue"]-pc["fatigue"]); pending.append(pe["pending"]); form_diff += pe["form"]!=pc["form"]
        growth_ability.append(eg.growth.ability_after-cg.growth.ability_after)
    return {"season_end_current_ability_delta":summary(ability),"growth_ability_after_delta":summary(growth_ability),
            "mean_abs_rating_delta":summary(rating_abs),"pre_finalize_fatigue_delta":summary(fatigue),
            "form_state_difference_rate":form_diff/LONG_TERM_SEEDS,"final_pending":summary(pending),
            "per_stat_delta_mean":{k:statistics.fmean(v) for k,v in per_stat.items()}}


def rng_purity():
    failures=[]
    for i in range(RNG_PURITY_SEEDS):
        initial=make_engine(BASE_SEED+30000+i); payload=serialize_game(initial)
        eventful=deserialize_game(copy.deepcopy(payload)); control=deserialize_game(copy.deepcopy(payload))
        es=ProductionAdvanceService(eventful,game_provider=DummyProvider()); cs=ProductionAdvanceService(control,game_provider=DummyProvider())
        for _ in range(144):
            es.advance_one_game(); es.drain_generated_interactive_events()
            # observational only: resolve record locally so queue cannot suppress future generation; no authoritative effect.
            st=event_state_for_engine(eventful)
            for ev in list(st.pending): st.resolve(ev.event_id,ev.choices[0].choice_id,None)
        with patch("src.production_advance.maybe_generate_interactive_event", return_value=None):
            for _ in range(144): cs.advance_one_game(); cs.drain_generated_interactive_events()
        if eventful.rng.get_state()!=control.rng.get_state() or eventful.player.as_dict()!=control.player.as_dict() or eventful.current_session.as_dict()!=control.current_session.as_dict():
            failures.append(i)
    return {"seeds":RNG_PURITY_SEEDS,"exact_core_state_failures":failures,"pass":not failures}


def determinism(supported_by_event):
    seed=BASE_SEED+40000
    def once():
        r=run_season(seed,"authoritative",supported_by_event)
        e=r["engine"]
        return {"events":[x.as_dict() for x in event_state_for_engine(e).events],"effects":effect_state_for_engine(e).as_dict(),
                "player":e.player.as_dict(),"session":e.current_session.as_dict(),"rng":e.rng.get_state()}
    a=once(); b=once()
    return {"canonical_hash_left":sha(a),"canonical_hash_right":sha(b),"exact_equal":a==b}


def save_load(supported_by_event):
    e=make_engine(BASE_SEED+50000); s=ProductionAdvanceService(e,game_provider=DummyProvider())
    generated=[]
    for _ in range(80):
        s.advance_one_game(); generated.extend(s.drain_generated_interactive_events())
        # resolve supported events but preserve one pending when available
        for ev in list(s.pending_interactive_events):
            choices=supported_by_event.get(ev.event_type,())
            if choices and len(s.pending_interactive_events)>1:
                try:s.resolve_interactive_event(ev.event_id,choices[0])
                except UnsupportedInteractiveEffect: pass
    before=serialize_game(e); restored=deserialize_game(copy.deepcopy(before)); after=serialize_game(restored)
    exact=before==after
    st=event_state_for_engine(restored); ef=effect_state_for_engine(restored)
    # same next action equivalence
    left=deserialize_game(copy.deepcopy(before)); right=deserialize_game(copy.deepcopy(before))
    ls=ProductionAdvanceService(left,game_provider=DummyProvider()); rs=ProductionAdvanceService(right,game_provider=DummyProvider())
    ls.advance_one_game(); rs.advance_one_game()
    next_equal=serialize_game(left)==serialize_game(right) and left.rng.get_state()==right.rng.get_state()
    return {"roundtrip_exact":exact,"pending":len(st.pending),"resolved":sum(x.status=="resolved" for x in st.events),
            "active_effects":len(ef.active_effects),"cooldown_entries":len(st.event_cooldown_until),
            "season_count_entries":len(st.season_counts),"same_next_action":next_equal}


def advance_composition():
    out={}
    for command in ("next_game","week","month"):
        found=False
        for seed in range(60,260):
            e=make_engine(seed); s=ProductionAdvanceService(e,game_provider=DummyProvider())
            summary = s.advance_one_game() if command=="next_game" else s.advance_one_week() if command=="week" else s.advance_one_month()
            gen=s.drain_generated_interactive_events()
            if gen:
                ev=gen[0]; expected=s.schedule.dates[ev.game_number-1].isoformat()
                out[command]={"games_played":summary.games_played,"event_game_number":ev.game_number,"occurred_at":ev.occurred_at,
                              "expected_date":expected,"coordinate_exact":ev.occurred_at==expected}
                found=True;break
        if not found: out[command]={"found":False}
    return out


def performance():
    seeds=[BASE_SEED+60000+i for i in range(PERF_SEASONS)]
    def bench(enabled):
        t=time.perf_counter(); games=0
        ctx=nullcontext() if enabled else patch("src.production_advance.maybe_generate_interactive_event", return_value=None)
        with ctx:
            for seed in seeds:
                e=make_engine(seed); s=ProductionAdvanceService(e,game_provider=DummyProvider())
                for _ in range(144):
                    s.advance_one_game(); s.drain_generated_interactive_events(); games+=1
                    if enabled:
                        st=event_state_for_engine(e)
                        for ev in list(st.pending): st.resolve(ev.event_id,ev.choices[0].choice_id,None)
        return time.perf_counter()-t,games
    # interleave two pairs to reduce order bias
    c1,g=bench(False); e1,_=bench(True); e2,_=bench(True); c2,_=bench(False)
    c=(c1+c2)/2; e=(e1+e2)/2
    return {"seasons":PERF_SEASONS,"games":g,"control_seconds":c,"event_seconds":e,
            "control_us_per_game":c/g*1e6,"event_us_per_game":e/g*1e6,"increment_pct":(e/c-1)*100}


def main():
    rows,support,effect_plans=support_matrix()
    freq=frequency_distribution(support)
    pending=pending_queue(support)
    result={
        "meta":{"main_head":"47ada4fe9f1d95da2760d7a8d56a8900aab6fdc3","season_samples":SEASONS,
                "long_term_pairs":LONG_TERM_SEEDS,"rng_purity_pairs":RNG_PURITY_SEEDS},
        "catalog":{"archetypes":len(EVENT_CATALOG),"categories":sorted({a.category for a in EVENT_CATALOG}),
                   "once_per_season":[a.event_type for a in EVENT_CATALOG if a.once_per_season],
                   "once_per_career":[a.event_type for a in EVENT_CATALOG if a.once_per_career]},
        "choice_support_matrix":rows,
        "choice_support_summary":Counter(r["classification"] for r in rows),
        "frequency":freq,"pending_queue":pending,"effect_magnitude":effect_magnitude(effect_plans),
        "long_term":long_term(support),"determinism":determinism(support),"rng_purity":rng_purity(),
        "save_load":save_load(support),"advance_composition":advance_composition(),"performance":performance(),
    }
    print(json.dumps(result,ensure_ascii=False,indent=2,default=str))
    with open("interactive-event-p1-validation.json","w",encoding="utf-8") as f:
        json.dump(result,f,ensure_ascii=False,indent=2,default=str)

if __name__=="__main__": main()
