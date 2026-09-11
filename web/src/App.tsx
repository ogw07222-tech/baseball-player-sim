import { useCallback, useEffect, useRef, useState } from 'react'
import { PlayerDashboard } from './screens/PlayerDashboard'
import { SeasonScreen } from './screens/SeasonScreen'
import { NewCareerPage } from './screens/NewCareerPage'
import { DraftDayPage } from './screens/DraftDayPage'
import { CareerScreen, LeagueScreen, NewsScreen, RecordsScreen, TeamScreen } from './screens/PlayableOverviewScreens'
import type { DashboardViewModel, SeasonProgressViewModel, SeasonViewModel } from './types/viewModels'
import type { NewCareerRequest } from './types/newCareer'
import type { GameDataProvider } from './services/GameDataProvider'
import { BackendTransportError } from './services/HttpBackendPresentationGateway'
import { draftDayForPlayer, draftDayMock } from './mocks/draftDay'
import { ErrorState, LoadingState } from './components/ui'

type Screen = 'player' | 'season' | 'career' | 'team' | 'league' | 'records' | 'news'

const navItems: { key:Screen; label:string; icon:string }[] = [
  {key:'player',label:'선수',icon:'⌂'},{key:'season',label:'시즌',icon:'▣'},{key:'career',label:'커리어',icon:'♜'},{key:'team',label:'팀',icon:'◉'},{key:'league',label:'리그',icon:'◇'},{key:'records',label:'기록',icon:'⌁'},{key:'news',label:'뉴스',icon:'▤'},
]

function mergeSeasonMeta(dashboard:DashboardViewModel|null, season:SeasonViewModel|null):SeasonProgressViewModel|null {
  if(!dashboard && !season) return null
  const dashboardSeason = dashboard?.season
  const seasonView = season?.season
  return {
    year: dashboardSeason?.year ?? seasonView?.year ?? null,
    game: dashboardSeason?.game ?? seasonView?.game ?? null,
    totalGames: dashboardSeason?.totalGames ?? seasonView?.totalGames ?? null,
    date: dashboardSeason?.date ?? seasonView?.date ?? null,
    progress: dashboardSeason?.progress ?? seasonView?.progress ?? null,
  }
}

function transportMessage(error: unknown): string {
  if (error instanceof BackendTransportError) {
    if (error.code === 'NO_CAREER') return '저장된 커리어를 찾을 수 없습니다. 새 커리어를 시작해 주세요.'
    if (error.code === 'SAVE_FAILED') return '서버에 커리어 상태를 저장할 수 없습니다. 잠시 후 다시 시도해 주세요.'
    if (error.code === 'NETWORK_ERROR') return '서버에 연결할 수 없습니다. 네트워크 연결을 확인해 주세요.'
    if (error.code === 'SIMULATION_CONFLICT') return '진행 요청이 이미 처리되었거나 다른 요청과 충돌했습니다. 최신 상태를 다시 확인해 주세요.'
    return error.message
  }
  return '서버와 통신하는 중 문제가 발생했습니다.'
}

export function App({ provider }: { provider:GameDataProvider }) {
  const [screen,setScreen] = useState<Screen>('player')
  const [eventRoute,setEventRoute] = useState(()=>window.location.hash)
  const [careerReady,setCareerReady] = useState<boolean|null>(null)
  const [dashboard,setDashboard] = useState<DashboardViewModel|null>(null)
  const [season,setSeason] = useState<SeasonViewModel|null>(null)
  const [loading,setLoading] = useState(true)
  const [mutationLoading,setMutationLoading] = useState(false)
  const [error,setError] = useState<string|null>(null)
  const mutationLock = useRef(false)

  const load = useCallback(async(showPageLoading=true)=>{
    if(showPageLoading) setLoading(true)
    setError(null)
    try {
      const exists = await provider.hasCareer()
      setCareerReady(exists)
      if(exists) {
        const [dashboardData,seasonData] = await Promise.all([provider.getDashboard(),provider.getSeason()])
        setDashboard(dashboardData); setSeason(seasonData)
      } else {
        setDashboard(null); setSeason(null)
      }
    } catch (caught) {
      setError(transportMessage(caught))
    } finally {
      if(showPageLoading) setLoading(false)
    }
  },[provider])

  const restoreAuthoritativeState = useCallback(async()=>{
    const [dashboardData,seasonData] = await Promise.all([provider.getDashboard(),provider.getSeason()])
    setDashboard(dashboardData)
    setSeason(seasonData)
    setCareerReady(true)
  },[provider])

  useEffect(()=>{ void load() },[load])
  useEffect(()=>{ const sync=()=>setEventRoute(window.location.hash); window.addEventListener('hashchange',sync); return()=>window.removeEventListener('hashchange',sync) },[])

  const startCareer = async(request:NewCareerRequest) => {
    setError(null)
    const created = await provider.createCareer(request)
    const seasonData = await provider.getSeason()
    setDashboard(created); setSeason(seasonData); setCareerReady(true); setScreen('player')
  }

  const advanceNextGame = async() => {
    if(mutationLock.current) return
    mutationLock.current = true
    setMutationLoading(true)
    setError(null)
    try {
      const updatedDashboard = await provider.advanceNextGame()
      setDashboard(updatedDashboard)
      setSeason(await provider.getSeason())
    } catch (caught) {
      if(caught instanceof BackendTransportError && caught.code === 'REVISION_CONFLICT') {
        try {
          await restoreAuthoritativeState()
          setError('다른 요청에서 커리어 상태가 변경되어 최신 서버 상태로 다시 불러왔습니다.')
        } catch (reloadError) {
          setError(transportMessage(reloadError))
        }
      } else if(caught instanceof BackendTransportError && caught.code === 'NO_CAREER') {
        await load(false)
      } else {
        setError(transportMessage(caught))
      }
    } finally {
      mutationLock.current = false
      setMutationLoading(false)
    }
  }

  if(loading) return <LoadingState message="저장된 커리어를 확인하는 중입니다."/>
  if(error && careerReady===null) return <ErrorState message={error} onRetry={()=>void load()}/>
  if(careerReady===false) return <NewCareerPage onStart={startCareer}/>

  if(eventRoute==='#draft') {
    const draftData = dashboard?.player.rosterLevel==='고교'
      ? draftDayForPlayer({name:dashboard.player.name,position:dashboard.player.position,batsThrows:dashboard.player.batsThrows.replace('/',' / '),age:dashboard.player.age})
      : draftDayMock
    return <DraftDayPage data={draftData} onStartProCareer={()=>{window.location.hash=''; setEventRoute(''); setScreen('player')}}/>
  }

  const seasonMeta = mergeSeasonMeta(dashboard,season)
  const progress = seasonMeta?.progress ?? 0
  const content = !dashboard || !season ? <LoadingState message="커리어 데이터를 불러오는 중입니다."/> : screen==='player'
    ? <PlayerDashboard data={dashboard} onAdvanceNextGame={advanceNextGame} mutationLoading={mutationLoading}/>
    : screen==='season'
      ? <SeasonScreen data={season} dashboard={dashboard} onSave={()=>void provider.saveGame()}/>
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
        <div><strong>{seasonMeta?.year ?? '—'} SEASON</strong><div className="season-progress" aria-label={`시즌 진행률 ${progress}%`}><span style={{width:`${Math.max(0,Math.min(100,progress))}%`}}/></div></div>
        <div className="game-count">GAME {seasonMeta?.game ?? '—'} / {seasonMeta?.totalGames ?? '—'} <small>{seasonMeta?.progress === null || seasonMeta?.progress === undefined ? '—' : `${seasonMeta.progress}%`}</small></div>
        <div className="header-spacer"/>
        <div className="current-date">{seasonMeta?.date ?? '시즌 날짜 정보 없음'}<small>{mutationLoading?'다음 경기를 진행하는 중입니다…':'다음 경기를 진행하세요.'}</small></div>
        <button className="icon-button" aria-label="검색">⌕</button><button className="icon-button" aria-label="설정">⚙</button>
      </header>
      <main>
        {error && <ErrorState message={error} onRetry={()=>void load(false)}/>}
        {content}
      </main>
    </div>
  </div>
}
