import { useCallback, useEffect, useMemo, useState } from 'react'
import { PlayerDashboard } from './screens/PlayerDashboard'
import { SeasonScreen } from './screens/SeasonScreen'
import { NewCareerPage } from './screens/NewCareerPage'
import { DraftDayPage } from './screens/DraftDayPage'
import { CareerScreen, LeagueScreen, NewsScreen, RecordsScreen, TeamScreen } from './screens/PlayableOverviewScreens'
import type { DashboardViewModel, SeasonViewModel } from './types/viewModels'
import type { NewCareerRequest } from './types/newCareer'
import type { AdvanceCommand, GameDataProvider } from './services/GameDataProvider'
import { MockGameDataProvider } from './mock/mockGameDataProvider'
import { draftDayForPlayer, draftDayMock } from './mocks/draftDay'
import { ErrorState, LoadingState } from './components/ui'

type Screen = 'player' | 'season' | 'career' | 'team' | 'league' | 'records' | 'news'

const navItems: { key:Screen; label:string; icon:string }[] = [
  {key:'player',label:'선수',icon:'⌂'},{key:'season',label:'시즌',icon:'▣'},{key:'career',label:'커리어',icon:'♜'},{key:'team',label:'팀',icon:'◉'},{key:'league',label:'리그',icon:'◇'},{key:'records',label:'기록',icon:'⌁'},{key:'news',label:'뉴스',icon:'▤'},
]

export function App({ provider: injectedProvider }: { provider?:GameDataProvider }) {
  const provider = useMemo(()=>injectedProvider ?? new MockGameDataProvider(),[injectedProvider])
  const [screen,setScreen] = useState<Screen>('player')
  const [eventRoute,setEventRoute] = useState(()=>window.location.hash)
  const [careerReady,setCareerReady] = useState<boolean|null>(null)
  const [dashboard,setDashboard] = useState<DashboardViewModel|null>(null)
  const [season,setSeason] = useState<SeasonViewModel|null>(null)
  const [loading,setLoading] = useState(true)
  const [error,setError] = useState(false)

  const load = useCallback(async()=>{
    setLoading(true); setError(false)
    try {
      const exists = await provider.hasCareer()
      setCareerReady(exists)
      if(exists) {
        const [dashboardData,seasonData] = await Promise.all([provider.getDashboard(),provider.getSeason()])
        setDashboard(dashboardData); setSeason(seasonData)
      } else {
        setDashboard(null); setSeason(null)
      }
    } catch { setError(true) } finally { setLoading(false) }
  },[provider])

  useEffect(()=>{ void load() },[load])
  useEffect(()=>{ const sync=()=>setEventRoute(window.location.hash); window.addEventListener('hashchange',sync); return()=>window.removeEventListener('hashchange',sync) },[])

  const startCareer = async(request:NewCareerRequest) => {
    const created = await provider.createCareer(request)
    const seasonData = await provider.getSeason()
    setDashboard(created); setSeason(seasonData); setCareerReady(true); setScreen('player'); setError(false)
  }

  const advance = async(command:AdvanceCommand) => {
    const actions = { nextGame:provider.advanceNextGame, week:provider.advanceWeek, month:provider.advanceMonth, season:provider.advanceSeason }
    try {
      const updatedDashboard = await actions[command].call(provider)
      setDashboard(updatedDashboard)
      setSeason(await provider.getSeason())
    } catch { setError(true) }
  }

  if(loading) return <LoadingState/>
  if(error && careerReady===null) return <ErrorState onRetry={()=>void load()}/>
  if(careerReady===false) return <NewCareerPage onStart={startCareer}/>

  if(eventRoute==='#draft') {
    const draftData = dashboard?.player.rosterLevel==='고교'
      ? draftDayForPlayer({name:dashboard.player.name,position:dashboard.player.position,batsThrows:dashboard.player.batsThrows.replace('/',' / '),age:dashboard.player.age})
      : draftDayMock
    return <DraftDayPage data={draftData} onStartProCareer={()=>{window.location.hash=''; setEventRoute(''); setScreen('player')}}/>
  }

  const seasonMeta = dashboard?.season ?? season?.season
  const content = !dashboard || !season ? <LoadingState/> : screen==='player'
    ? <PlayerDashboard data={dashboard} onAdvance={advance}/>
    : screen==='season'
      ? <SeasonScreen data={season} onSave={()=>void provider.saveGame()}/>
      : screen==='career'
        ? <CareerScreen data={dashboard}/>
        : screen==='team'
          ? <TeamScreen data={season}/>
          : screen==='league'
            ? <LeagueScreen data={season}/>
            : screen==='records'
              ? <RecordsScreen dashboard={dashboard} season={season}/>
              : <NewsScreen data={dashboard}/>

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
      <main>{error?<ErrorState onRetry={()=>void load()}/>:content}</main>
    </div>
  </div>
}
