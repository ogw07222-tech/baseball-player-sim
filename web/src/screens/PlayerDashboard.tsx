import { useState } from 'react'
import type { DashboardViewModel } from '../types/viewModels'
import { AbilityBar, Leaderboard, Panel, ProgressRing, Tabs } from '../components/ui'
import type { AdvanceCommand } from '../services/GameDataProvider'

const fmt3 = (v:number) => v.toFixed(3).replace(/^0/, '')
const fmtWar = (v:number|null) => v === null ? '—' : v.toFixed(1)
const fmtOptional = (v:string|number|null|undefined) => v === null || v === undefined || v === '' ? '—' : String(v)

export function PlayerDashboard({ data, onAdvance, mutationLoading, mutationCommand }: { data:DashboardViewModel; onAdvance:(command:AdvanceCommand)=>Promise<void>; mutationLoading:boolean; mutationCommand:AdvanceCommand|null }) {
  const [titleMetric,setTitleMetric] = useState('HR')
  const stats = data.seasonStats
  const recent = data.recentGames
  const chartMax = recent.points.length ? Math.max(.6, ...recent.points.map(point=>point.value)) : 1
  const titleMetrics = Object.keys(data.titleRace)
  const activeTitleMetric = titleMetrics.includes(titleMetric) ? titleMetric : titleMetrics[0]
  const conditionKnown = data.status.condition.trim().toLowerCase() !== 'unknown' && data.status.condition.trim() !== ''
  const busyLabel = mutationCommand==='week'?'1주 진행 중…':mutationCommand==='month'?'1개월 진행 중…':'경기 진행 중…'

  return <div className="dashboard-screen">
    <section className="player-hero panel">
      <div className="hero-art"><div className="avatar-placeholder" aria-label="선수 이미지 자리">{data.player.number ?? '—'}</div><span className="hero-caption">더 큰 선수가 되기 위해</span></div>
      <div className="hero-copy">
        <div className="hero-title"><h1>{data.player.name}{data.player.number !== null && <span>#{data.player.number}</span>}</h1><span className="team-mark">{data.league.code}</span></div>
        <p>{data.player.age}세 · {data.player.position} · {data.player.batsThrows} · {data.player.team ?? '소속 미정'}</p>
        <div className="badge-row"><span className="badge accent">{data.player.rosterLevel}</span>{data.player.careerYear !== null && <span className="badge">{data.player.careerYear}년차</span>}<span className="badge hot">● {data.player.form}</span></div>
        <div className="season-stat-strip" aria-label="시즌 성적">
          {[['AVG',fmt3(stats.avg)],['OBP',fmt3(stats.obp)],['SLG',fmt3(stats.slg)],['OPS',fmt3(stats.ops)],['HR',stats.hr],['RBI',stats.rbi],['SB',stats.sb],['WAR',fmtWar(stats.war)]].map(([label,value])=><div key={String(label)}><small>{label}</small><strong>{value}</strong></div>)}
        </div>
        <small className="secondary-stat">{stats.g} G · {stats.pa} PA · 시즌 결과 지표</small>
      </div>
    </section>

    <div className="dashboard-grid">
      <Panel title="선수 능력치" action={<small>Raw rating · 100 = 1군 평균 기준</small>} className="abilities-panel">
        <div className="abilities-list">{data.abilities.length ? data.abilities.map(stat=><AbilityBar stat={stat} key={stat.key}/>) : <div className="empty-tab">현재 제공되는 능력치가 없습니다.</div>}</div>
        <div className="ability-scale">0 <span>100 기준선 · 상한 없음</span> 200+</div>
      </Panel>

      <div className="center-stack">
        <Panel title="최근 경기" action={recent.metric ? <small>{recent.metric}</small> : undefined}>
          {recent.points.length ? <>
            <div className="recent-summary"><strong>{recent.avg === null ? '—' : fmt3(recent.avg)}</strong><span>{recent.hr === null ? '— HR' : `${recent.hr} HR`}</span><span>OPS {recent.ops === null ? '—' : recent.ops.toFixed(3)}</span></div>
            <div className="mini-chart" aria-label={`${recent.metric ?? '최근 경기'} 그래프`}>
              {recent.points.map(point=><div className="chart-col" key={point.label}><span className="chart-dot" style={{bottom:`${Math.max(6,(point.value/chartMax)*82)}%`}}/><span className="outcome-chip">{point.outcome}</span></div>)}
            </div>
          </> : <div className="empty-tab">아직 표시할 최근 경기 데이터가 없습니다.</div>}
        </Panel>
        <Panel title="선수 상태">
          <div className="status-grid">
            <div>{conditionKnown ? <div className="status-icon">●</div> : <div className="status-icon">?</div>}<span>컨디션 <b>{conditionKnown ? data.status.condition : '확인 불가'}</b></span></div>
            <div><ProgressRing value={data.status.fatigue} label="피로도"/><span>피로도 <b>{Math.round(data.status.fatigue)}%</b></span></div>
            <div className="status-icon">✚<span>부상 <b>{data.status.injury ?? '없음'}</b></span></div>
            <div className="status-icon flame">●<span>최근 폼 <b>{data.status.form}</b></span></div>
          </div>
        </Panel>
        <Panel title="특성 (Trait)">{data.traits.length ? <div className="trait-list">{data.traits.map(trait=><span key={trait.name} className={`trait ${trait.tone}`}>{trait.name}</span>)}</div> : <div className="empty-tab">현재 적용 중인 특성이 없습니다.</div>}</Panel>
      </div>

      <div className="right-stack">
        <Panel title="다음 경기" action={data.season.game !== null ? <small>정규시즌 {data.season.game+1}차전</small> : undefined}>
          {data.nextGame ? <>
            <div className="matchup"><div><strong>{data.nextGame.awayTeam}</strong><small>{fmtOptional(data.nextGame.awayRank)}위 · {fmtOptional(data.nextGame.awayRecord)}</small></div><b>VS</b><div><strong>{data.nextGame.homeTeam}</strong><small>{fmtOptional(data.nextGame.homeRank)}위 · {fmtOptional(data.nextGame.homeRecord)}</small></div></div>
            <p className="game-meta">{data.nextGame.date}{data.nextGame.time ? ` ${data.nextGame.time}` : ''}<br/>{data.nextGame.stadium ?? '경기장 미정'}</p>
            <div className="starter-card"><span>예상 선발</span><strong>{data.nextGame.opposingStarter ?? '미정'} · {data.nextGame.throwingHand ?? '—'}</strong><small>ERA {data.nextGame.era === null ? '—' : data.nextGame.era.toFixed(2)}{data.nextGame.expectedLineupSpot?` · 예상 ${data.nextGame.expectedLineupSpot}번 타순`:''}</small></div>
          </> : <div className="empty-tab">현재 backend가 다음 경기 세부 정보를 제공하지 않습니다.</div>}
        </Panel>
        <Panel title="시즌 스토리">{data.seasonStory.length ? <div className="timeline">{data.seasonStory.map(event=><div className="timeline-row" key={`${event.date}-${event.title}`}><time>{event.date}</time><span className={`timeline-dot ${event.category.toLowerCase()}`}/><div><strong>{event.title}</strong><small>{event.detail}</small></div></div>)}</div> : <div className="empty-tab">현재 시즌에 기록된 스토리가 없습니다.</div>}</Panel>
        <Panel title="타이틀 경쟁" action={titleMetrics.length && activeTitleMetric ? <Tabs items={titleMetrics} value={activeTitleMetric} onChange={setTitleMetric} ariaLabel="타이틀 경쟁 지표"/> : undefined}><Leaderboard rows={activeTitleMetric ? data.titleRace[activeTitleMetric] ?? [] : []}/></Panel>
      </div>
    </div>

    <nav className="advance-controls" aria-label="시간 진행">
      <button className="primary" disabled={mutationLoading} aria-busy={mutationLoading && mutationCommand==='nextGame'} onClick={()=>void onAdvance('nextGame')}>{mutationLoading && mutationCommand==='nextGame'?busyLabel:'▶ 다음 경기'}</button>
      <button disabled={mutationLoading} aria-busy={mutationLoading && mutationCommand==='week'} onClick={()=>void onAdvance('week')}>{mutationLoading && mutationCommand==='week'?busyLabel:'1주 진행'}</button>
      <button disabled={mutationLoading} aria-busy={mutationLoading && mutationCommand==='month'} onClick={()=>void onAdvance('month')}>{mutationLoading && mutationCommand==='month'?busyLabel:'1개월 진행'}</button>
    </nav>
  </div>
}
