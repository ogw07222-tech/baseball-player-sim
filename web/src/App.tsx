import { useCallback, useEffect, useMemo, useState } from 'react'
import { PlayerDashboard } from './screens/PlayerDashboard'
import { SeasonScreen } from './screens/SeasonScreen'
import type { DashboardViewModel, SeasonViewModel } from './types/viewModels'
import type { AdvanceCommand, GameDataProvider } from './services/GameDataProvider'
import { MockGameDataProvider } from './mock/mockGameDataProvider'
import { ErrorState, LoadingState } from './components/ui'

type Screen = 'player' | 'season' | 'career' | 'team' | 'league' | 'records' | 'news'

const navItems: { key:Screen; label:string; icon:string }[] = [
  {key:'player',label:'선수',icon:'⌂'},{key:'season',label:'시즌',icon:'▣'},{key:'career',label:'커리어',icon:'♜'},{key:'team',label:'팀',icon:'◉'},{key:'league',label:'리그',icon:'◇'},{key:'records',label:'기록',icon:'⌁'},{key:'news',label:'뉴스',icon:'▤'},
]

export function App({ provider: injectedProvider }: { provider?:GameDataProvider }) {
  const provider = useMemo(()=>injectedProvider ?? new MockGameDataProvider(),[injectedProvider])
  const [screen,setScreen] = useState<Screen>('player')
  const [dashboard,setDashboard] = useState<DashboardViewModel|null>(null)
  const [season,setSeason] = useState<SeasonViewModel|null>(null)
  const [loading,setLoading] = useState(true)
  const [error,setError] = useState(false)

  const load = useCallback(async()=>{
    setLoading(true); setError(false)
    try {
      const [dashboardData,seasonData] = await Promise.all([provider.getDashboard(),provider.getSeason()])
      setDashboard(dashboardData); setSeason(seasonData)
    } catch { setError(true) } finally { setLoading(false) }
  },[provider])

  useEffect(()=>{ void load() },[load])

  const advance = async(command:AdvanceCommand) => {
    const actions = { nextGame:provider.advanceNextGame, week:provider.advanceWeek, month:provider.advanceMonth, season:provider.advanceSeason }
    try { setDashboard(await actions[command].call(provider)) } catch { setError(true) }
  }

  const seasonMeta = dashboard?.season ?? season?.season
  return <div className="app-shell">
    <aside className="sidebar">
      <div className="brand"><strong>KBO CAREER</strong><small>BASEBALL PLAYER SIMULATOR</small></div>
      <nav aria-label="메인 메뉴">{navItems.map(item=><button key={item.key} aria-label={item.label} className={screen===item.key?'active':''} aria-current={screen===item.key?'page':undefined} onClick={()=>setScreen(item.key)}><span aria-hidden="true">{item.icon}</span>{item.label}</button>)}</nav>
      <div className="sidebar-quote">“좋은 선수는 기록을 남기지만,<br/>위대한 선수는 이야기를 남긴다.”</div>
      <div className="sidebar-foot"><b>BASEBALL CAREER</b><span>ONE PLAYER<br/>A BIGGER STORY</span></div>
    </aside>
    <div className="app-content">
      <header className="top-header">
        <div><strong>{seasonMeta?.year ?? '—'} SEASON</strong><div className="season-progress"><span style={{width:`${seasonMeta?.progress ?? 0}%`}}/></div></div>
        <div className="game-count">GAME {seasonMeta?.game ?? '—'} / {seasonMeta?.totalGames ?? '—'} <small>{seasonMeta?.progress ?? 0}%</small></div>
        <div className="header-spacer"/>
        <div className="current-date">{seasonMeta?.date ?? '시즌 데이터 로딩 중'}<small>다음 경기를 진행하세요.</small></div>
        <button className="icon-button" aria-label="검색">⌕</button><button className="icon-button" aria-label="설정">⚙</button>
      </header>
      <main>
        {loading?<LoadingState/>:error?<ErrorState onRetry={()=>void load()}/>:screen==='player'&&dashboard?<PlayerDashboard data={dashboard} onAdvance={advance}/>:screen==='season'&&season?<SeasonScreen data={season} onSave={()=>void provider.saveGame()}/>:<div className="coming-soon panel"><h1>{navItems.find(n=>n.key===screen)?.label}</h1><p>이 화면은 v0.1 범위 밖이며 App Shell navigation만 연결되어 있습니다.</p></div>}
      </main>
    </div>
  </div>
}
