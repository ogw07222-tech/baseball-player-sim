"""Terminal CLI for the playable career prototype."""
from __future__ import annotations
import argparse
from pathlib import Path
from . import config
from .career import CareerEngine
from .events import CareerEvent,EventChoice
from .persistence import load_game,save_game
from .player import Player
from .rng import RNG
STAT_LABELS={'contact':'컨택','power':'파워','discipline':'선구안','speed':'주력','defense':'수비','throwing':'송구','stamina':'체력','durability':'내구성','mentality':'멘탈','talent':'재능'}
def _fmt_rate(v:float)->str:return f'{v:.3f}'.lstrip('0')
def print_player(p:Player)->None:
    print('\n=== 선수 ===');print(f'{p.name} | {p.age}세 | {p.position} | {p.bats_throws}');print(f"소속: {p.team or '고교'} | 상태: {p.roster_level} | 성장형: {p.development_profile}")
    for k,v in p.stats.as_dict().items():print(f'{STAT_LABELS[k]} {v}')
    if p.season_modifiers:print('시즌 임시 효과:',', '.join(f'{STAT_LABELS.get(k,k)} {v:+d}' for k,v in p.season_modifiers.items()))
    print('특성:',', '.join(t.name for t in p.traits) or '없음')
def print_line(title,line)->None:
    print(f'\n=== {title} ===');print(f'G {line.G} PA {line.PA} H {line.H} 2B {line.doubles} 3B {line.triples} HR {line.HR} BB {line.BB} SO {line.SO} HBP {line.HBP} SB {line.SB} RBI {line.RBI}');print(f'AVG {_fmt_rate(line.AVG)} OBP {_fmt_rate(line.OBP)} SLG {_fmt_rate(line.SLG)} OPS {_fmt_rate(line.OPS)}')
def print_career_summary(p:Player)->None:
    total=p.first_team_career();best=p.best_season();print('\n=== 커리어 종료 ===');print(f'{p.name} | {p.position}');print(f"1군 데뷔: {p.debut_year if p.debut_year is not None else '없음'} | 은퇴: {p.retirement_age}세");print_line('KBO 1군 통산',total)
    counts={}
    for e in p.awards:
        if e.get('level')=='KBO':n=str(e['award']);counts[n]=counts.get(n,0)+1
    print('수상:',', '.join(f'{n} {c}회' for n,c in counts.items()) or '없음')
    if best:print(f'최고 시즌: {best.year} | OPS {_fmt_rate(best.first_team.OPS)} HR {best.first_team.HR} AVG {_fmt_rate(best.first_team.AVG)}')
    if p.draft_info:
        i=p.draft_info;print(f"드래프트: {i['round']}라운드 전체 {i['pick']}순위 | {i['team']}" if i.get('round') else f"드래프트: 미지명 | {i['team']} 육성선수 계약")
    print(f'초기 재능: {p.initial_talent}');print('최종 특성:',', '.join(t.name for t in p.traits) or '없음')
    ev=[e for e in p.event_history if e.get('event_id')!='coach_change'];major=sum(e.get('breakthrough_tier')=='major_breakthrough' for e in ev);legend=sum(e.get('breakthrough_tier')=='legendary_breakthrough' for e in ev);print(f'커리어 이벤트: {len(ev)}회 | major {major}회 | legendary {legend}회')
def _choose(prompt:str,values:tuple[str,...])->str:
    while True:
        print(prompt)
        for i,v in enumerate(values,1):print(f'{i}. {v}')
        raw=input('> ').strip()
        if raw.isdigit() and 1<=int(raw)<=len(values):return values[int(raw)-1]
        if raw in values:return raw
        print('잘못된 입력입니다.')
def create_interactive_player(rng:RNG)->Player:
    name=input('이름: ').strip() or '김OO';position=_choose('포지션:',config.POSITIONS);bt=_choose('투타:',config.BATS_THROWS)
    while True:
        raw=input('초기 특성 개수 [0~3]: ').strip()
        if raw in {'0','1','2','3'}:return Player.random(name,rng,position,bt,int(raw))
        print('0~3 중 하나를 입력하세요.')
def choose_event(event:CareerEvent)->EventChoice:
    print('\n=== 커리어 이벤트 발생 ===');print(event.name);print(event.description)
    for i,c in enumerate(event.choices,1):print(f'{i}. {c.name} [{c.risk}]')
    while True:
        raw=input('선택: ').strip()
        if raw.isdigit() and 1<=int(raw)<=len(event.choices):return event.choices[int(raw)-1]
        print('잘못된 입력입니다.')
def show_resolution(r)->None:
    permanent=', '.join(f'{STAT_LABELS.get(k,k)} {v:+d}' for k,v in r.stat_changes.items()) or '영구 능력치 변화 없음';temporary=', '.join(f'{STAT_LABELS.get(k,k)} {v:+d}' for k,v in r.temporary_changes.items()) or '임시 효과 없음';print(f'결과: {r.outcome_name} | {permanent} | {temporary} | 부상 {r.injury_change}')
def handle_pending_event(engine:CareerEngine)->None:
    event=engine.pending_event()
    if not event:return
    choice=choose_event(event);show_resolution(engine.resolve_pending_event(choice))
def run_high_school_cli(engine:CareerEngine,save_path:Path)->None:
    while engine.phase=='HIGH_SCHOOL':
        print('\n1. 다음 전국대회 진행  2. 현재 기록  3. 능력치  4. 스카우트 평가/드래프트  5. 저장  6. 시즌 종료까지');choice=input('> ').strip()
        if choice=='1':
            if engine.tournament_index>=len(config.HIGH_SCHOOL_TOURNAMENTS):print('드래프트:',engine.evaluate_draft().as_dict());break
            r=engine.run_next_tournament();print(f'{r.name}: {r.games}경기 | OPS {_fmt_rate(r.line.OPS)} | 우승={r.champion} MVP={r.mvp}')
        elif choice=='2':print_line('고교 누적',engine.player.high_school_stats)
        elif choice=='3':print_player(engine.player)
        elif choice in {'4','6'}:print('드래프트:',engine.evaluate_draft().as_dict());break
        elif choice=='5':save_game(save_path,engine);print(f'저장 완료: {save_path}')
def advance_interactive(engine:CareerEngine,count:int|None=None)->None:
    if count is None:
        while True:
            s=engine.advance_to_season_end(interactive=True);print(f'시즌 진행: {s.games_completed}/{config.KBO_FIRST_TEAM_GAMES}')
            if s.has_pending_event:handle_pending_event(engine);continue
            break
    else:
        remaining=count
        while remaining>0:
            before=engine.start_pro_season().games_completed;s=engine.advance_pro_games(remaining,stop_on_event=True);advanced=s.games_completed-before;remaining-=advanced
            if s.has_pending_event:handle_pending_event(engine)
            if advanced==0 and not s.has_pending_event:break
def run_pro_cli(engine:CareerEngine,save_path:Path)->None:
    while engine.phase=='PRO':
        s=engine.start_pro_season();print(f'\n=== {engine.year} 시즌 | {s.games_completed}/{config.KBO_FIRST_TEAM_GAMES} | {s.current_level} ===');print('1. 다음 경기  2. 1주(7경기)  3. 1개월(25경기)  4. 시즌 종료까지  5. 시즌 기록  6. 커리어 기록  7. 능력치  8. 특성  9. 부상/컨디션  10. 저장');choice=input('> ').strip()
        if choice in {'1','2','3'}:advance_interactive(engine,{'1':1,'2':7,'3':25}[choice])
        elif choice=='4':
            advance_interactive(engine,None);record,growth=engine.finish_pro_season();print_line(f'{record.year} 1군',record.first_team);print('수상:',', '.join(record.awards) or '없음');print('성장 폭발:' if growth.explosion else '시즌 성장:',growth.deltas)
            if engine.should_retire():engine.retire();break
        elif choice=='5':print_line('1군',s.record.first_team);print_line('2군',s.record.farm)
        elif choice=='6':print_line('KBO 1군 통산',engine.player.first_team_career())
        elif choice=='7':print_player(engine.player)
        elif choice=='8':print('특성:',', '.join(t.name for t in engine.player.traits) or '없음')
        elif choice=='9':
            i=engine.player.injury;print(f"피로 {engine.player.fatigue:.1f} | 폼 {engine.player.form} | 부상 {i.name+' '+str(i.games_remaining)+'경기' if i else '없음'}")
        elif choice=='10':save_game(save_path,engine);print(f'저장 완료: {save_path}')
def run_auto(seed:int|None,name:str,position:str,bats_throws:str,trait_count:int)->Player:
    rng=RNG(seed);p=Player.random(name,rng,position,bats_throws,trait_count);e=CareerEngine(p,rng);e.run_to_retirement();print_player(p);print_career_summary(p);return p
def main()->None:
    parser=argparse.ArgumentParser(description='Baseball Player Career Simulator');parser.add_argument('--seed',type=int,default=None);parser.add_argument('--auto',action='store_true');parser.add_argument('--name',default='Prototype Player');parser.add_argument('--position',choices=config.POSITIONS,default='SS');parser.add_argument('--bats-throws',choices=config.BATS_THROWS,default='R/R');parser.add_argument('--traits',type=int,choices=range(4),default=2);parser.add_argument('--save',default='savegame.json');args=parser.parse_args()
    if args.auto:run_auto(args.seed,args.name,args.position,args.bats_throws,args.traits);return
    print('=== Baseball Player Career Simulator ===\n1. 새 게임\n2. 불러오기\n3. 종료');choice=input('> ').strip()
    if choice=='3':return
    save_path=Path(args.save)
    if choice=='2':engine=load_game(save_path)
    else:rng=RNG(args.seed);engine=CareerEngine(create_interactive_player(rng),rng);print_player(engine.player)
    if engine.phase=='HIGH_SCHOOL':run_high_school_cli(engine,save_path)
    if engine.phase=='PRO':run_pro_cli(engine,save_path)
    if engine.phase=='RETIRED':print_career_summary(engine.player)
if __name__=='__main__':main()
