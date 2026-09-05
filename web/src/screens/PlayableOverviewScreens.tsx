import type { DashboardViewModel, SeasonViewModel } from '../types/viewModels'
import { Leaderboard, Panel } from '../components/ui'

const fmt3 = (value:number) => value.toFixed(3).replace(/^0/, '')

export function CareerScreen({ data }: { data:DashboardViewModel }) {
  const s = data.seasonStats
  return <div className="overview-screen">
    <div className="page-title-row"><div><h1>커리어</h1><p>{data.player.name}의 현재 커리어 진행 상황입니다.</p></div></div>
    <div className="overview-grid overview-grid-3">
      <Panel title="커리어 프로필"><div className="overview-kv">
        <div><span>소속</span><strong>{data.player.team}</strong></div><div><span>포지션</span><strong>{data.player.position}</strong></div>
        <div><span>나이</span><strong>{data.player.age}</strong></div><div><span>커리어</span><strong>{data.player.careerYear}년차</strong></div>
        <div><span>레벨</span><strong>{data.player.rosterLevel}</strong></div><div><span>타/투</span><strong>{data.player.batsThrows}</strong></div>
      </div></Panel>
      <Panel title={`${data.season.year} 시즌`}><div className="overview-stat-line">
        <div><span>AVG</span><strong>{fmt3(s.avg)}</strong></div><div><span>OPS</span><strong>{fmt3(s.ops)}</strong></div><div><span>HR</span><strong>{s.hr}</strong></div><div><span>RBI</span><strong>{s.rbi}</strong></div><div><span>SB</span><strong>{s.sb}</strong></div><div><span>WAR</span><strong>{s.war.toFixed(1)}</strong></div>
      </div></Panel>
      <Panel title="현재 상태"><div className="overview-kv">
        <div><span>컨디션</span><strong>{data.status.condition}</strong></div><div><span>피로도</span><strong>{data.status.fatigue}%</strong></div>
        <div><span>부상</span><strong>{data.status.injury}</strong></div><div><span>폼</span><strong>{data.status.form}</strong></div>
      </div></Panel>
    </div>
    <Panel title="커리어 타임라인"><div className="overview-timeline">{data.seasonStory.map((event,index)=><div key={`${event.date}-${index}`}><time>{event.date}</time><span className={`story-dot ${event.category.toLowerCase()}`}/><div><strong>{event.title}</strong><p>{event.detail}</p></div></div>)}</div></Panel>
  </div>
}

export function TeamScreen({ data }: { data:SeasonViewModel }) {
  return <div className="overview-screen">
    <div className="page-title-row"><div><h1>팀</h1><p>{data.teamName}의 현재 시즌 전력과 타격 기록입니다.</p></div></div>
    <div className="overview-grid overview-grid-2">
      <Panel title="팀 주요 지표"><div className="metrics-list">{data.teamMetrics.map(metric=><div key={metric.label}><span>{metric.label}</span><strong>{metric.value}</strong><small>{metric.rank}위</small></div>)}</div></Panel>
      <Panel title="최근 경기"><div className="recent-results">{data.recentResults.map(game=><div key={`${game.date}-${game.awayTeam}`}><time>{game.date}</time><span>{game.awayTeam}</span><strong>{game.awayScore} : {game.homeScore}</strong><span>{game.homeTeam}</span><b className={game.result==='W'?'win':'loss'}>{game.result==='W'?'승':'패'}</b><small>{game.stadium}</small></div>)}</div></Panel>
    </div>
    <Panel title="팀 타격 기록"><div className="table-scroll team-table"><table><thead><tr>{['선수','G','PA','H','HR','RBI','SB','BB','SO','AVG','OBP','SLG','OPS','WAR'].map(h=><th key={h}>{h}</th>)}</tr></thead><tbody>{data.teamBatting.map(row=><tr key={row.player} className={row.isUser?'user-row':''}><td>{row.player}</td><td>{row.g}</td><td>{row.pa}</td><td>{row.h}</td><td>{row.hr}</td><td>{row.rbi}</td><td>{row.sb}</td><td>{row.bb}</td><td>{row.so}</td><td>{fmt3(row.avg)}</td><td>{fmt3(row.obp)}</td><td>{fmt3(row.slg)}</td><td>{fmt3(row.ops)}</td><td>{row.war.toFixed(1)}</td></tr>)}</tbody></table></div></Panel>
  </div>
}

export function LeagueScreen({ data }: { data:SeasonViewModel }) {
  return <div className="overview-screen">
    <div className="page-title-row"><div><h1>리그</h1><p>{data.league.name} 전체 순위와 주요 타이틀 경쟁입니다.</p></div></div>
    <div className="overview-grid overview-grid-2">
      <Panel title="팀 순위"><div className="standings-table table-scroll"><table><thead><tr><th>순위</th><th>팀</th><th>승</th><th>패</th><th>무</th><th>승률</th><th>게임차</th></tr></thead><tbody>{data.standings.map(row=><tr key={row.team} className={row.isUserTeam?'user-row':''}><td>{row.rank}</td><td>{row.team}</td><td>{row.w}</td><td>{row.l}</td><td>{row.d}</td><td>{fmt3(row.pct)}</td><td>{row.gb}</td></tr>)}</tbody></table></div></Panel>
      <div className="overview-stack"><Panel title="타격 AVG"><Leaderboard rows={data.hittingLeaderboards.AVG ?? []}/></Panel><Panel title="투수 ERA"><Leaderboard rows={data.pitchingLeaderboards.ERA ?? []}/></Panel></div>
    </div>
  </div>
}

export function RecordsScreen({ dashboard, season }: { dashboard:DashboardViewModel; season:SeasonViewModel }) {
  const s = dashboard.seasonStats
  return <div className="overview-screen">
    <div className="page-title-row"><div><h1>기록</h1><p>현재 production에서 제공되는 시즌 기록을 한곳에 모았습니다.</p></div></div>
    <Panel title={`${dashboard.player.name} — ${dashboard.season.year} 시즌`}><div className="record-hero-grid">
      {[['G',s.g],['PA',s.pa],['AVG',fmt3(s.avg)],['OBP',fmt3(s.obp)],['SLG',fmt3(s.slg)],['OPS',fmt3(s.ops)],['HR',s.hr],['RBI',s.rbi],['SB',s.sb],['WAR',s.war.toFixed(1)]].map(([label,value])=><div key={String(label)}><span>{label}</span><strong>{value}</strong></div>)}
    </div></Panel>
    <div className="overview-grid overview-grid-2">
      <Panel title="타이틀 레이스"><Leaderboard rows={dashboard.titleRace.OPS ?? dashboard.titleRace.AVG ?? []}/></Panel>
      <Panel title="리그 홈런"><Leaderboard rows={season.hittingLeaderboards.HR ?? []}/></Panel>
    </div>
    <div className="overview-note">통산 시즌별 기록은 backend의 career-history 계약이 UI provider에 노출되는 즉시 이 화면에 확장합니다. 현재 없는 데이터를 임의 생성하지 않습니다.</div>
  </div>
}

export function NewsScreen({ data }: { data:DashboardViewModel }) {
  return <div className="overview-screen">
    <div className="page-title-row"><div><h1>뉴스</h1><p>현재 커리어에서 실제 생성된 이벤트와 변화를 확인합니다.</p></div></div>
    <div className="news-feed">{data.seasonStory.map((event,index)=><article className="panel news-card" key={`${event.date}-${index}`}><div><time>{event.date}</time><span>{event.category}</span></div><h2>{event.title}</h2><p>{event.detail}</p></article>)}</div>
  </div>
}
