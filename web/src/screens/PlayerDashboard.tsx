import { useState } from 'react'
import type { DashboardViewModel } from '../types/viewModels'
import { AbilityBar, Leaderboard, Panel, ProgressRing, Tabs } from '../components/ui'
import type { AdvanceCommand } from '../services/GameDataProvider'

const fmt3 = (v:number) => v.toFixed(3).replace(/^0/, '')

export function PlayerDashboard({ data, onAdvance }: { data:DashboardViewModel; onAdvance:(command:AdvanceCommand)=>void }) {
  const [titleMetric,setTitleMetric] = useState('HR')
  const stats = data.seasonStats
  const chartMax = Math.max(.6, ...data.recentGames.points.map(point=>point.value))
  return <div className="dashboard-screen">
    <section className="player-hero panel">
      <div className="hero-art"><div className="avatar-placeholder" aria-label="선수 이미지 자리">{data.player.number}</div><span className="hero-caption">더 큰 선수가 되기 위해</span></div>
      <div className="hero-copy">
        <div className="hero-title"><h1>{data.player.name} <span>#{data.player.number}</span></h1><span className="team-mark">{data.league.code}</span></div>
        <p>{data.player.age}세 · {data.player.position} · {data.player.batsThrows} · {data.player.team}</p>
        <div className="badge-row"><span className="badge accent">{data.player.rosterLevel}</span><span className="badge">{data.player.careerYear}년차</span><span className="badge hot">● {data.player.form}</span></div>
        <div className="season-stat-strip">
          {[['AVG',fmt3(stats.avg)],['OBP',fmt3(stats.obp)],['SLG',fmt3(stats.slg)],['OPS',fmt3(stats.ops)],['HR',stats.hr],['RBI',stats.rbi],['SB',stats.sb],['WAR',stats.war.toFixed(1)]].map(([label,value])=><div key={String(label)}><small>{label}</small><strong>{value}</strong></div>)}
        </div>
        <small className="secondary-stat">{stats.g} G · {stats.pa} PA</small>
      </div>
    </section>

    <div className="dashboard-grid">
      <Panel title="선수 능력치" action={<small>100 = 1군 평균 기준</small>} className="abilities-panel">
        <div className="abilities-list">{data.abilities.map(stat=><AbilityBar stat={stat} key={stat.key}/>)}</div>
        <div className="ability-scale">0 <span>100 기준선 · 상한 없음</span> 200+</div>
      </Panel>

      <div className="center-stack">
        <Panel title="최근 10경기" action={<small>{data.recentGames.metric}</small>}>
          <div className="recent-summary"><strong>{fmt3(data.recentGames.avg)}</strong><span>{data.recentGames.hr} HR</span><span>OPS {data.recentGames.ops.toFixed(3)}</span></div>
          <div className="mini-chart" aria-label={`${data.recentGames.metric} 최근 10경기 그래프`}>
            {data.recentGames.points.map(point=><div className="chart-col" key={point.label}><span className="chart-dot" style={{bottom:`${Math.max(6,(point.value/chartMax)*82)}%`}}/><span className="outcome-chip">{point.outcome}</span></div>)}
          </div>
        </Panel>
        <Panel title="선수 상태">
          <div className="status-grid"><div><ProgressRing value={82} label="컨디션"/><span>컨디션 <b>{data.status.condition}</b></span></div><div><ProgressRing value={data.status.fatigue} label="피로도"/><span>피로도 <b>{data.status.fatigue}%</b></span></div><div className="status-icon">✚<span>부상 <b>{data.status.injury}</b></span></div><div className="status-icon flame">●<span>최근 폼 <b>{data.status.form}</b></span></div></div>
        </Panel>
        <Panel title="특성 (Trait)"><div className="trait-list">{data.traits.map(trait=><span key={trait.name} className={`trait ${trait.tone}`}>{trait.name}</span>)}</div></Panel>
      </div>

      <div className="right-stack">
        <Panel title="다음 경기" action={<small>정규시즌 {data.season.game+1}차전</small>}>
          <div className="matchup"><div><strong>{data.nextGame.awayTeam}</strong><small>{data.nextGame.awayRank}위 · {data.nextGame.awayRecord}</small></div><b>VS</b><div><strong>{data.nextGame.homeTeam}</strong><small>{data.nextGame.homeRank}위 · {data.nextGame.homeRecord}</small></div></div>
          <p className="game-meta">{data.nextGame.date} {data.nextGame.time}<br/>{data.nextGame.stadium}</p>
          <div className="starter-card"><span>예상 선발</span><strong>{data.nextGame.opposingStarter} · {data.nextGame.throwingHand}</strong><small>ERA {data.nextGame.era.toFixed(2)}{data.nextGame.expectedLineupSpot?` · 예상 ${data.nextGame.expectedLineupSpot}번 타순`:''}</small></div>
        </Panel>
        <Panel title="시즌 스토리"><div className="timeline">{data.seasonStory.map(event=><div className="timeline-row" key={`${event.date}-${event.title}`}><time>{event.date}</time><span className={`timeline-dot ${event.category.toLowerCase()}`}/><div><strong>{event.title}</strong><small>{event.detail}</small></div></div>)}</div></Panel>
        <Panel title="타이틀 경쟁" action={<Tabs items={Object.keys(data.titleRace)} value={titleMetric} onChange={setTitleMetric} ariaLabel="타이틀 경쟁 지표"/>}><Leaderboard rows={data.titleRace[titleMetric] ?? []}/></Panel>
      </div>
    </div>

    <nav className="advance-controls" aria-label="시간 진행">
      <button className="primary" onClick={()=>onAdvance('nextGame')}>▶ 다음 경기</button>
      <button onClick={()=>onAdvance('week')}>1주 진행</button>
      <button onClick={()=>onAdvance('month')}>1개월 진행</button>
      <button onClick={()=>onAdvance('season')}>▶▶ 시즌 끝까지</button>
    </nav>
  </div>
}
