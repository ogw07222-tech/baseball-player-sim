import type { DashboardViewModel, SeasonViewModel } from '../types/viewModels'
import { Leaderboard, Panel } from '../components/ui'

const fmt3 = (value:number) => value.toFixed(3).replace(/^0/, '')
const fmtWar = (value:number|null) => value === null ? '—' : value.toFixed(1)
const Empty = ({ children }: { children:string }) => <div className="empty-tab">{children}</div>

export function CareerScreen({ data }: { data:DashboardViewModel }) {
  const s = data.seasonStats
  const condition = data.status.condition.trim().toLowerCase() === 'unknown' || !data.status.condition.trim() ? '확인 불가' : data.status.condition
  return <div className="overview-screen">
    <div className="page-title-row"><div><h1>커리어</h1><p>{data.player.name}의 현재 커리어 진행 상황입니다.</p></div></div>
    <div className="overview-grid overview-grid-3">
      <Panel title="커리어 프로필"><div className="overview-kv">
        <div><span>소속</span><strong>{data.player.team ?? '소속 미정'}</strong></div><div><span>포지션</span><strong>{data.player.position}</strong></div>
        <div><span>나이</span><strong>{data.player.age}</strong></div><div><span>커리어</span><strong>{data.player.careerYear === null ? '—' : `${data.player.careerYear}년차`}</strong></div>
        <div><span>레벨</span><strong>{data.player.rosterLevel}</strong></div><div><span>타/투</span><strong>{data.player.batsThrows}</strong></div>
      </div></Panel>
      <Panel title={`${data.season.year ?? '현재'} 시즌`}><div className="overview-stat-line">
        <div><span>AVG</span><strong>{fmt3(s.avg)}</strong></div><div><span>OPS</span><strong>{fmt3(s.ops)}</strong></div><div><span>HR</span><strong>{s.hr}</strong></div><div><span>RBI</span><strong>{s.rbi}</strong></div><div><span>SB</span><strong>{s.sb}</strong></div><div><span>WAR</span><strong>{fmtWar(s.war)}</strong></div>
      </div></Panel>
      <Panel title="현재 상태"><div className="overview-kv">
        <div><span>컨디션</span><strong>{condition}</strong></div><div><span>피로도</span><strong>{Math.round(data.status.fatigue)}%</strong></div>
        <div><span>부상</span><strong>{data.status.injury ?? '없음'}</strong></div><div><span>폼</span><strong>{data.status.form}</strong></div>
      </div></Panel>
    </div>
    <div className="overview-grid overview-grid-2">
      <Panel title="현재 능력치" action={<small>Raw rating</small>}><div className="overview-kv">{data.abilities.map(ability=><div key={ability.key}><span>{ability.label}</span><strong>{ability.rating}</strong><small>{ability.delta===0?'변화 없음':`${ability.delta>0?'+':''}${ability.delta}`}</small></div>)}</div></Panel>
      <Panel title="특성"><div className="trait-list">{data.traits.length?data.traits.map(trait=><div className={`trait ${trait.tone}`} key={trait.name}><strong>{trait.name}</strong><span>{trait.category}</span></div>):<Empty>현재 적용 중인 특성이 없습니다.</Empty>}</div></Panel>
    </div>
    <Panel title="커리어 타임라인">{data.seasonStory.length?<div className="overview-timeline">{data.seasonStory.map((event,index)=><div key={`${event.date}-${index}`}><time>{event.date}</time><span className={`story-dot ${event.category.toLowerCase()}`}/><div><strong>{event.title}</strong><p>{event.detail}</p></div></div>)}</div>:<Empty>현재 시즌에 기록된 스토리가 없습니다.</Empty>}</Panel>
    <div className="overview-note">과거 시즌별 커리어 기록은 career-history backend 계약이 provider에 노출된 뒤 제공합니다. 현재 없는 과거 기록은 생성하지 않습니다.</div>
  </div>
}

export function TeamScreen({ data }: { data:SeasonViewModel }) {
  const teamName = data.teamName ?? '소속팀'
  return <div className="overview-screen">
    <div className="page-title-row"><div><h1>팀</h1><p>{teamName}의 현재 시즌 전력과 타격 기록입니다.</p></div></div>
    <div className="overview-grid overview-grid-2">
      <Panel title="팀 주요 지표">{data.teamMetrics.length?<div className="metrics-list">{data.teamMetrics.map(metric=><div key={metric.label}><span>{metric.label}</span><strong>{metric.value}</strong><small>{metric.rank}위</small></div>)}</div>:<Empty>현재 제공되는 팀 지표가 없습니다.</Empty>}</Panel>
      <Panel title="최근 경기">{data.recentResults.length?<div className="recent-results">{data.recentResults.map(game=><div key={`${game.date}-${game.awayTeam}`}><time>{game.date}</time><span>{game.awayTeam}</span><strong>{game.awayScore} : {game.homeScore}</strong><span>{game.homeTeam}</span><b className={game.result==='W'?'win':'loss'}>{game.result==='W'?'승':'패'}</b><small>{game.stadium}</small></div>)}</div>:<Empty>최근 경기 결과가 아직 없습니다.</Empty>}</Panel>
    </div>
    <Panel title="팀 타격 기록">{data.teamBatting.length?<div className="table-scroll team-table"><table><thead><tr>{['선수','G','PA','H','HR','RBI','SB','BB','SO','AVG','OBP','SLG','OPS','WAR'].map(h=><th scope="col" key={h}>{h}</th>)}</tr></thead><tbody>{data.teamBatting.map(row=><tr key={row.player} className={row.isUser?'user-row':''}><td>{row.player}</td><td>{row.g}</td><td>{row.pa}</td><td>{row.h}</td><td>{row.hr}</td><td>{row.rbi}</td><td>{row.sb}</td><td>{row.bb}</td><td>{row.so}</td><td>{fmt3(row.avg)}</td><td>{fmt3(row.obp)}</td><td>{fmt3(row.slg)}</td><td>{fmt3(row.ops)}</td><td>{fmtWar(row.war)}</td></tr>)}</tbody></table></div>:<Empty>현재 제공되는 팀 타격 기록이 없습니다.</Empty>}</Panel>
    <div className="overview-grid overview-grid-2"><Panel title="팀 투수 기록"><Empty>현재 provider에 팀 투수 로스터 기록이 없습니다.</Empty></Panel><Panel title="팀 수비 기록"><Empty>현재 provider에 팀 수비 로스터 기록이 없습니다.</Empty></Panel></div>
  </div>
}

export function LeagueScreen({ data }: { data:SeasonViewModel }) {
  return <div className="overview-screen">
    <div className="page-title-row"><div><h1>리그</h1><p>{data.league.name} 전체 순위와 주요 타이틀 경쟁입니다.</p></div></div>
    <Panel title="팀 순위">{data.standings.length?<div className="standings-table table-scroll"><table><thead><tr><th scope="col">순위</th><th scope="col">팀</th><th scope="col">승</th><th scope="col">패</th><th scope="col">무</th><th scope="col">승률</th><th scope="col">게임차</th></tr></thead><tbody>{data.standings.map(row=><tr key={row.team} className={row.isUserTeam?'user-row':''}><td>{row.rank}</td><td>{row.team}</td><td>{row.w}</td><td>{row.l}</td><td>{row.d}</td><td>{fmt3(row.pct)}</td><td>{row.gb}</td></tr>)}</tbody></table></div>:<Empty>현재 리그 순위 데이터가 없습니다.</Empty>}</Panel>
    <div className="overview-grid overview-grid-2">
      <Panel title="타격 리더보드">{Object.keys(data.hittingLeaderboards).length?<div className="overview-stack">{Object.entries(data.hittingLeaderboards).map(([metric,rows])=><section key={metric}><h3>{metric}</h3><Leaderboard rows={rows}/></section>)}</div>:<Empty>현재 타격 리더보드 데이터가 없습니다.</Empty>}</Panel>
      <Panel title="투수 리더보드">{Object.keys(data.pitchingLeaderboards).length?<div className="overview-stack">{Object.entries(data.pitchingLeaderboards).map(([metric,rows])=><section key={metric}><h3>{metric}</h3><Leaderboard rows={rows}/></section>)}</div>:<Empty>현재 투수 리더보드 데이터가 없습니다.</Empty>}</Panel>
    </div>
    <Panel title="최근 경기 결과">{data.recentResults.length?<div className="recent-results">{data.recentResults.map(game=><div key={`${game.date}-${game.awayTeam}`}><time>{game.date}</time><span>{game.awayTeam}</span><strong>{game.awayScore} : {game.homeScore}</strong><span>{game.homeTeam}</span><b className={game.result==='W'?'win':'loss'}>{game.result==='W'?'승':'패'}</b><small>{game.stadium}</small></div>)}</div>:<Empty>최근 리그 경기 결과가 아직 없습니다.</Empty>}</Panel>
  </div>
}

export function RecordsScreen({ dashboard, season }: { dashboard:DashboardViewModel; season:SeasonViewModel }) {
  const s = dashboard.seasonStats
  const titleRows = dashboard.titleRace.OPS ?? dashboard.titleRace.AVG ?? []
  return <div className="overview-screen">
    <div className="page-title-row"><div><h1>기록</h1><p>현재 provider에서 제공되는 시즌 결과 지표를 한곳에 모았습니다.</p></div></div>
    <Panel title={`${dashboard.player.name} — ${dashboard.season.year ?? '현재'} 시즌`}><div className="record-hero-grid">
      {[['G',s.g],['PA',s.pa],['AVG',fmt3(s.avg)],['OBP',fmt3(s.obp)],['SLG',fmt3(s.slg)],['OPS',fmt3(s.ops)],['HR',s.hr],['RBI',s.rbi],['SB',s.sb],['WAR',fmtWar(s.war)]].map(([label,value])=><div key={String(label)}><span>{label}</span><strong>{value}</strong></div>)}
    </div></Panel>
    <div className="overview-grid overview-grid-2">
      <Panel title="타이틀 레이스">{titleRows.length?<Leaderboard rows={titleRows}/>:<Empty>현재 타이틀 레이스 데이터가 없습니다.</Empty>}</Panel>
      <Panel title="리그 홈런">{(season.hittingLeaderboards.HR ?? []).length?<Leaderboard rows={season.hittingLeaderboards.HR}/>:<Empty>현재 홈런 순위 데이터가 없습니다.</Empty>}</Panel>
    </div>
    <div className="overview-note">통산 기록, 역대 마일스톤, 과거 시즌 표는 career-history backend 계약이 UI provider에 노출된 뒤 제공합니다. 현재 없는 데이터를 임의 생성하지 않습니다.</div>
  </div>
}

export function NewsScreen({ data }: { data:DashboardViewModel }) {
  return <div className="overview-screen">
    <div className="page-title-row"><div><h1>뉴스</h1><p>현재 커리어에서 실제 생성된 이벤트와 변화를 확인합니다.</p></div></div>
    {data.seasonStory.length?<div className="news-feed">{data.seasonStory.map((event,index)=><article className="panel news-card" key={`${event.date}-${index}`}><div><time>{event.date}</time><span className={`news-badge ${event.category.toLowerCase()}`}>{event.category}</span></div><h2>{event.title}</h2><p>{event.detail}</p></article>)}</div>:<Empty>현재 시즌에 생성된 뉴스 이벤트가 없습니다.</Empty>}
    <div className="overview-note">이벤트 중요도 수치는 현재 provider 계약에 없으므로 별도 값을 만들어 표시하지 않습니다.</div>
  </div>
}
