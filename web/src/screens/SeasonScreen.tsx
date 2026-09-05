import { useState } from 'react'
import type { DashboardViewModel, SeasonViewModel } from '../types/viewModels'
import { Leaderboard, Panel, Tabs } from '../components/ui'

const fmt3 = (v:number) => v.toFixed(3).replace(/^0/, '')

export function SeasonScreen({ data, dashboard, onSave }: { data:SeasonViewModel; dashboard?:DashboardViewModel; onSave:()=>void }) {
  const [seasonTab,setSeasonTab] = useState('리그 현황')
  const [hitMetric,setHitMetric] = useState('AVG')
  const [pitchMetric,setPitchMetric] = useState('ERA')
  const [teamTab,setTeamTab] = useState('타격 기록')
  const nav = ['리그 현황','팀 기록','선수 기록','경기 일정/결과','월간 리포트','시즌 스토리']
  const teamTable = <div className="table-scroll team-table"><table><thead><tr>{['선수','G','PA','AB','R','H','2B','3B','HR','RBI','SB','BB','SO','AVG','OBP','SLG','OPS','WAR'].map(h=><th scope="col" key={h}>{h}</th>)}</tr></thead><tbody>{data.teamBatting.map(row=><tr key={row.player} className={row.isUser?'user-row':''}><td>{row.player}</td><td>{row.g}</td><td>{row.pa}</td><td>{row.ab}</td><td>{row.r}</td><td>{row.h}</td><td>{row.doubles}</td><td>{row.triples}</td><td>{row.hr}</td><td>{row.rbi}</td><td>{row.sb}</td><td>{row.bb}</td><td>{row.so}</td><td>{fmt3(row.avg)}</td><td>{fmt3(row.obp)}</td><td>{fmt3(row.slg)}</td><td>{fmt3(row.ops)}</td><td>{row.war.toFixed(1)}</td></tr>)}</tbody></table></div>
  return <div className="season-screen">
    <div className="page-title-row"><div><h1>시즌</h1><p>리그 전체의 흐름과 기록을 확인할 수 있습니다.</p></div><button className="save-button" onClick={onSave}>저장</button></div>
    <Tabs items={nav} value={seasonTab} onChange={setSeasonTab} ariaLabel="시즌 화면"/>
    {seasonTab==='리그 현황' && <>
      <div className="season-top-grid">
        <Panel title="팀 순위" className="standings-panel">
          <div className="subtabs"><button className="active">정규시즌</button><button title="추후 구현">최근 10경기</button><button title="추후 구현">홈 / 원정</button></div>
          <div className="standings-table table-scroll"><table><thead><tr><th scope="col">순위</th><th scope="col">팀</th><th scope="col">승</th><th scope="col">패</th><th scope="col">무</th><th scope="col">승률</th><th scope="col">게임차</th><th scope="col">연속</th></tr></thead><tbody>{data.standings.map(row=><tr key={row.team} className={row.isUserTeam?'user-row':''}><td>{row.rank}</td><td>{row.team}</td><td>{row.w}</td><td>{row.l}</td><td>{row.d}</td><td>{fmt3(row.pct)}</td><td>{row.gb}</td><td>{row.streak}</td></tr>)}</tbody></table></div>
        </Panel>
        <Panel title="주요 타격 지표 리더보드"><Tabs items={Object.keys(data.hittingLeaderboards)} value={hitMetric} onChange={setHitMetric} ariaLabel="타격 지표"/><Leaderboard rows={data.hittingLeaderboards[hitMetric] ?? []}/></Panel>
        <Panel title="주요 투수 지표 리더보드"><Tabs items={Object.keys(data.pitchingLeaderboards)} value={pitchMetric} onChange={setPitchMetric} ariaLabel="투수 지표"/><Leaderboard rows={data.pitchingLeaderboards[pitchMetric] ?? []}/></Panel>
        <Panel title="최근 경기 결과"><div className="recent-results">{data.recentResults.map(game=><div key={`${game.date}-${game.awayTeam}`}><time>{game.date}</time><span>{game.awayTeam}</span><strong>{game.awayScore} : {game.homeScore}</strong><span>{game.homeTeam}</span><b className={game.result==='W'?'win':'loss'}>{game.result==='W'?'승':'패'}</b><small>{game.stadium}</small></div>)}</div></Panel>
      </div>
      <div className="season-bottom-grid">
        <Panel title={`${data.teamName} 팀 기록`} action={<Tabs items={['타격 기록','투수 기록','수비 기록']} value={teamTab} onChange={setTeamTab} ariaLabel="팀 기록 구분"/>}>
          {teamTab==='타격 기록'?teamTable:<div className="empty-tab">{teamTab} 데이터는 현재 provider에 없으므로 생성하지 않습니다.</div>}
        </Panel>
        <Panel title="팀 주요 지표"><div className="metrics-list">{data.teamMetrics.map(metric=><div key={metric.label}><span>{metric.label}</span><strong>{metric.value}</strong><small>{metric.rank}위</small></div>)}</div></Panel>
      </div>
    </>}
    {seasonTab==='팀 기록' && <div className="season-bottom-grid"><Panel title={`${data.teamName} 팀 타격 기록`}>{data.teamBatting.length?teamTable:<div className="empty-tab">현재 팀 타격 기록이 없습니다.</div>}</Panel><Panel title="팀 주요 지표"><div className="metrics-list">{data.teamMetrics.map(metric=><div key={metric.label}><span>{metric.label}</span><strong>{metric.value}</strong><small>{metric.rank}위</small></div>)}</div></Panel></div>}
    {seasonTab==='선수 기록' && <>{dashboard?<><Panel title={`${dashboard.player.name} 시즌 기록`}><div className="record-hero-grid">{[['G',dashboard.seasonStats.g],['PA',dashboard.seasonStats.pa],['AVG',fmt3(dashboard.seasonStats.avg)],['OPS',fmt3(dashboard.seasonStats.ops)],['HR',dashboard.seasonStats.hr],['RBI',dashboard.seasonStats.rbi],['SB',dashboard.seasonStats.sb],['WAR',dashboard.seasonStats.war.toFixed(1)]].map(([label,value])=><div key={String(label)}><span>{label}</span><strong>{value}</strong></div>)}</div></Panel><Panel title="타이틀 레이스"><Leaderboard rows={dashboard.titleRace.OPS ?? dashboard.titleRace.AVG ?? []}/></Panel></>:<div className="empty-tab panel">선수 기록 provider 데이터가 없습니다.</div>}</>}
    {seasonTab==='경기 일정/결과' && <Panel title="최근 경기 결과"><div className="recent-results">{data.recentResults.length?data.recentResults.map(game=><div key={`${game.date}-${game.awayTeam}`}><time>{game.date}</time><span>{game.awayTeam}</span><strong>{game.awayScore} : {game.homeScore}</strong><span>{game.homeTeam}</span><b className={game.result==='W'?'win':'loss'}>{game.result==='W'?'승':'패'}</b><small>{game.stadium}</small></div>):<div className="empty-tab">현재 제공되는 경기 결과가 없습니다.</div>}</div></Panel>}
    {seasonTab==='시즌 스토리' && <Panel title="시즌 스토리">{dashboard?.seasonStory.length?<div className="overview-timeline">{dashboard.seasonStory.map((event,index)=><div key={`${event.date}-${index}`}><time>{event.date}</time><span className={`story-dot ${event.category.toLowerCase()}`}/><div><strong>{event.title}</strong><p>{event.detail}</p></div></div>)}</div>:<div className="empty-tab">현재 시즌에 기록된 스토리가 없습니다.</div>}</Panel>}
    {seasonTab==='월간 리포트' && <div className="coming-soon panel"><strong>월간 리포트</strong><p>현재 provider에 월간 집계 계약이 없어 향후 구현합니다. 없는 월간 데이터를 생성하지 않습니다.</p></div>}
  </div>
}
