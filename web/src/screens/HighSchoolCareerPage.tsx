import { useEffect, useRef, useState } from 'react'
import type { BracketMatchVm, HighSchoolHubViewModel } from '../types/highSchool'
import '../highSchoolCareer.css'

const fmt3=(v:number)=>v.toFixed(3).replace(/^0/,'')

function SectionTitle({title,subtle}:{title:string;subtle?:string}){
  return <div className="hs-section-title"><h2>{title}</h2>{subtle&&<small>{subtle}</small>}</div>
}

function PlayerIdentityCard({data}:{data:HighSchoolHubViewModel['player']}){
  return <section className="hs-player-card hs-card">
    <div className="hs-player-art" aria-label="가상 고교 야구선수 실루엣"><div className="hs-cap"/><div className="hs-silhouette"/><span>HIGH SCHOOL PROSPECT</span></div>
    <div className="hs-player-copy"><h1>{data.name}</h1><p>{data.school}<br/><small>{data.schoolEnglish}</small></p><dl><div><dt>POSITION</dt><dd>{data.position}</dd></div><div><dt>BATS / THROWS</dt><dd>{data.batsThrows}</dd></div><div><dt>AGE</dt><dd>{data.age}</dd></div><div><dt>YEAR</dt><dd>{data.yearLabel}</dd></div></dl><blockquote>“한 경기씩, 내 이름을 남긴다.”</blockquote></div>
  </section>
}

function PlayerStatusCard({data}:{data:HighSchoolHubViewModel['player']}){
  return <section className="hs-card hs-status-card"><SectionTitle title="PLAYER STATUS"/><div className="hs-status-grid"><div><small>Scouted Grade</small><strong>{data.scoutedGrade}</strong></div><div><small>Condition</small><strong className="good">{data.condition}</strong></div><div><small>Season Growth</small><strong className="growth">+{data.seasonGrowth}</strong></div></div></section>
}

function BracketTeam({team}:{team:BracketMatchVm['top']}){
  return <div className={`hs-bracket-team ${team.state}`}><span>{team.name}</span>{team.score!==undefined&&<b>{team.score}</b>}</div>
}

function TournamentBracket({matches}:{matches:BracketMatchVm[]}){
  const rounds=['32강','16강','8강'] as const
  return <div className="hs-bracket" aria-label="현재 선수 대진 경로">
    {rounds.map(round=><div className={`hs-bracket-round round-${round}`} key={round}><h3>{round}</h3><div className="hs-bracket-round-body">{matches.filter(m=>m.round===round).map(match=><div className={`hs-bracket-match ${match.isCurrent?'current':''}`} key={match.id}><BracketTeam team={match.top}/><BracketTeam team={match.bottom}/></div>)}</div></div>)}
    <svg className="hs-bracket-lines" viewBox="0 0 1000 300" preserveAspectRatio="none" aria-hidden="true"><path d="M282 68 H340 V92 H388 M282 132 H340 V108 H388"/><path d="M282 200 H340 V224 H388 M282 264 H340 V240 H388"/><path d="M612 100 H672 V162 H724 M612 232 H672 V178 H724" className="muted"/><path d="M282 68 H340 V92 H388" className="player-path"/></svg>
  </div>
}

function CurrentTournamentCard({data,onOpenBracket,onAdvance}:{data:HighSchoolHubViewModel['currentTournament'];onOpenBracket:()=>void;onAdvance:()=>void}){
  return <section className="hs-card hs-tournament-card"><div className="hs-tournament-sky"/><div className="hs-tournament-content"><div className="hs-tournament-top"><SectionTitle title="CURRENT TOURNAMENT" subtle={data.stage}/><div className="hs-tournament-name"><strong>{data.name}</strong><small>{data.subtitle}</small></div></div><div className="hs-matchup"><div><span>{data.homeTeam}</span></div><b>VS</b><div><span>{data.awayTeam}</span></div></div><div className="hs-game-meta"><span>{data.date}</span><span>{data.time}</span><span>{data.stadium}</span></div><TournamentBracket matches={data.bracket}/><div className="hs-tournament-actions"><button className="hs-primary" onClick={onAdvance}>경기 진행</button><button onClick={onOpenBracket}>전체 대진표 보기</button></div></div></section>
}

function SeasonCard({items}:{items:HighSchoolHubViewModel['seasonTournaments']}){
  return <section className="hs-card hs-season-card"><SectionTitle title="HIGH SCHOOL SEASON" subtle="2026 시즌 주요 대회"/><div className="hs-season-tournaments">{items.map(item=><button type="button" key={item.name} className={item.state.toLowerCase()}><strong>{item.name}</strong><span>{item.status}</span>{item.note&&<small>({item.note})</small>}</button>)}</div></section>
}

function PerformanceCard({data}:{data:HighSchoolHubViewModel['performance']}){
  const stats=[['AVG',fmt3(data.avg)],['OBP',fmt3(data.obp)],['SLG',fmt3(data.slg)],['OPS',fmt3(data.ops)],['HR',data.hr],['BB',data.bb],['SO',data.so],['SB',data.sb]]
  return <section className="hs-card hs-performance-card"><SectionTitle title="HIGH SCHOOL PERFORMANCE" subtle="2026 HS TOTAL"/><div className="hs-stat-strip">{stats.map(([k,v])=><div key={String(k)} className={k==='OPS'?'featured':''}><small>{k}</small><strong>{v}</strong></div>)}</div></section>
}

function ProspectCard({data}:{data:HighSchoolHubViewModel['prospectEvaluation']}){
  return <section className="hs-card hs-prospect-card"><SectionTitle title="PROSPECT EVALUATION" subtle="scouting report"/><div className="hs-score-ring"><strong>{data.performanceScore}</strong><span>Performance Score</span><small>HS PERFORMANCE BASED</small></div><div className="hs-prospect-grid"><div><small>전국 순위</small><strong>#{data.nationalRank}</strong></div><div><small>포지션 순위</small><strong>SS #{data.positionRank}</strong></div><div><small>백분위</small><strong>{data.percentile}%</strong></div><div><small>예상 지명 범위</small><strong>{data.projectedRange}</strong><em>스카우트 컨센서스</em></div></div></section>
}

function DraftStockCard({data}:{data:HighSchoolHubViewModel['draftStock']}){
  const min=Math.min(...data.trend), max=Math.max(...data.trend), span=Math.max(1,max-min)
  const points=data.trend.map((v,i)=>`${(i/(data.trend.length-1))*100},${92-((v-min)/span)*72}`).join(' ')
  return <section className="hs-card hs-draft-card"><SectionTitle title="DRAFT STOCK"/><div className="hs-draft-head"><div><strong>{data.direction}</strong><span>▲ +{data.delta}</span><small>{data.span}</small></div><div><small>Current Projection</small><b>{data.projection}</b></div></div><svg className="hs-trend-chart" viewBox="0 0 100 100" preserveAspectRatio="none" aria-label="드래프트 평가 추세"><polyline points={points}/></svg></section>
}

function DevelopmentCard({data}:{data:HighSchoolHubViewModel['development']}){
  const total=data.reduce((s,x)=>s+(x.change??0),0)
  return <section className="hs-card hs-development-card"><SectionTitle title="PLAYER DEVELOPMENT" subtle={`시즌 성장 +${total.toFixed(1)}`}/><div className="hs-dev-list">{data.map(stat=><div key={stat.key}><div className="hs-dev-label"><span>{stat.label}</span><strong>{stat.rating}</strong></div><div className="hs-dev-track"><i style={{width:`${Math.min(stat.rating,100)}%`}}/></div></div>)}</div></section>
}

function RecentGamesCard({games}:{games:HighSchoolHubViewModel['recentGames']}){
  return <section className="hs-card hs-recent-card"><SectionTitle title="RECENT GAMES"/><div className="hs-recent-table"><div className="head"><span>날짜</span><span>대회</span><span>상대팀</span><span>결과</span><span>개인 기록</span></div>{games.map(g=><div className="row" key={`${g.date}-${g.opponent}`}><span>{g.date}</span><span>{g.tournament}</span><span>{g.opponent}</span><strong className={g.outcome==='W'?'win':'loss'}>{g.result}</strong><span>{g.line}</span></div>)}</div></section>
}

function CareerNewsCard({news}:{news:HighSchoolHubViewModel['careerNews']}){
  return <section className="hs-card hs-news-card"><SectionTitle title="CAREER NEWS"/><div className="hs-news-list">{news.map(item=><article key={`${item.date}-${item.headline}`}><time>{item.date}</time><p>{item.headline}</p></article>)}</div></section>
}

function FullBracketModal({data,onClose}:{data:HighSchoolHubViewModel['fullBracket'];onClose:()=>void}){
  const closeRef=useRef<HTMLButtonElement>(null)
  useEffect(()=>{const key=(e:KeyboardEvent)=>{if(e.key==='Escape')onClose()};window.addEventListener('keydown',key);closeRef.current?.focus();return()=>window.removeEventListener('keydown',key)},[onClose])
  return <div className="hs-modal-backdrop" role="presentation" onMouseDown={e=>{if(e.target===e.currentTarget)onClose()}}><section className="hs-full-bracket" role="dialog" aria-modal="true" aria-labelledby="full-bracket-title"><header><div><small>황금사자기 전국고교야구대회</small><h2 id="full-bracket-title">FULL TOURNAMENT BRACKET</h2></div><button ref={closeRef} aria-label="전체 대진표 닫기" onClick={onClose}>×</button></header><div className="hs-full-bracket-grid">{data.map(round=><div key={round.round}><h3>{round.round}</h3>{round.games.map((game,i)=><div className="hs-full-game" key={`${round.round}-${i}`}><span className={game.winner===game.a?'winner':''}>{game.a}<b>{game.aScore??''}</b></span><span className={game.winner===game.b?'winner':''}>{game.b}<b>{game.bScore??''}</b></span></div>)}</div>)}</div></section></div>
}

export function HighSchoolCareerPage({data,onAdvanceGame=()=>{}}:{data:HighSchoolHubViewModel;onAdvanceGame?:()=>void}){
  const [fullBracketOpen,setFullBracketOpen]=useState(false)
  const [notice,setNotice]=useState('')
  const advance=()=>{onAdvanceGame();setNotice('경기 진행은 현재 UI mock 상태입니다. 실제 시뮬레이션 연결 시 이 버튼이 application command를 호출합니다.')}
  return <div className="hs-career-screen"><header className="hs-header"><div><strong>BASEBALL PLAYER SIM</strong><small>ONE PLAYER, A BIGGER STORY</small></div><h1>HIGH SCHOOL CAREER</h1><div><span>{data.seasonLabel}</span><button aria-label="설정" disabled title="설정 기능 준비 중">⚙</button></div></header><main className="hs-layout"><aside className="hs-left"><PlayerIdentityCard data={data.player}/><PlayerStatusCard data={data.player}/></aside><section className="hs-center"><CurrentTournamentCard data={data.currentTournament} onOpenBracket={()=>setFullBracketOpen(true)} onAdvance={advance}/><SeasonCard items={data.seasonTournaments}/><PerformanceCard data={data.performance}/><RecentGamesCard games={data.recentGames}/></section><aside className="hs-right"><ProspectCard data={data.prospectEvaluation}/><DraftStockCard data={data.draftStock}/><DevelopmentCard data={data.development}/><CareerNewsCard news={data.careerNews}/></aside></main>{notice&&<div className="hs-toast" role="status">{notice}<button aria-label="알림 닫기" onClick={()=>setNotice('')}>×</button></div>}{fullBracketOpen&&<FullBracketModal data={data.fullBracket} onClose={()=>setFullBracketOpen(false)}/>}</div>
}
