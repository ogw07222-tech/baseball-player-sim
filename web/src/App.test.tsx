import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'
import { App } from './App'
import { MockGameDataProvider } from './mock/mockGameDataProvider'
import type { GameDataProvider } from './services/GameDataProvider'
import { BackendTransportError } from './services/HttpBackendPresentationGateway'

class FailingProvider extends MockGameDataProvider {
  constructor(){ super({hasCareer:true}) }
  async getDashboard(): ReturnType<GameDataProvider['getDashboard']> { throw new Error('boom') }
}

class SlowProvider extends MockGameDataProvider {
  constructor(){ super({hasCareer:true}) }
  async getDashboard() { await new Promise(resolve=>setTimeout(resolve,20)); return super.getDashboard() }
  async getSeason() { await new Promise(resolve=>setTimeout(resolve,20)); return super.getSeason() }
}

class SlowAdvanceProvider extends MockGameDataProvider {
  advanceCalls = 0
  private releaseAdvance: (()=>void) | null = null
  constructor(){ super({hasCareer:true}) }
  async advanceNextGame() {
    this.advanceCalls += 1
    await new Promise<void>(resolve=>{ this.releaseAdvance = resolve })
    return super.advanceNextGame()
  }
  release(){ this.releaseAdvance?.() }
}

class ConflictProvider extends MockGameDataProvider {
  dashboardReads = 0
  private conflict = true
  constructor(){ super({hasCareer:true}) }
  async getDashboard() {
    this.dashboardReads += 1
    return super.getDashboard()
  }
  async advanceNextGame() {
    if(this.conflict) {
      this.conflict = false
      throw new BackendTransportError(409,'REVISION_CONFLICT','expected_revision is stale',false,48)
    }
    return super.advanceNextGame()
  }
}

class EmptyOptionalDataProvider extends MockGameDataProvider {
  constructor(){ super({hasCareer:true}) }
  async getDashboard() {
    const data = await super.getDashboard()
    data.seasonStory = []
    data.traits = []
    data.titleRace = {}
    return data
  }
  async getSeason() {
    const data = await super.getSeason()
    data.teamBatting = []
    data.teamMetrics = []
    data.recentResults = []
    data.standings = []
    data.hittingLeaderboards = {}
    data.pitchingLeaderboards = {}
    return data
  }
}

const existingCareerProvider = () => new MockGameDataProvider({hasCareer:true})
afterEach(()=>{ window.location.hash='' })

describe('web UI',()=>{
  it('renders the single-screen new career UI without catcher, wizard steps, or back button', async()=>{
    render(<App provider={new MockGameDataProvider()}/>)
    expect(await screen.findByRole('heading',{name:'NEW CAREER'})).toBeInTheDocument()
    expect(screen.getByLabelText('PLAYER NAME')).toBeInTheDocument()
    expect(screen.getAllByRole('button').filter(button=>['1B','2B','3B','SS','LF','CF','RF'].includes(button.textContent?.trim() ?? ''))).toHaveLength(7)
    expect(screen.queryByRole('button',{name:'C'})).not.toBeInTheDocument()
    expect(screen.queryByRole('button',{name:'뒤로'})).not.toBeInTheDocument()
    expect(screen.queryByText('선수 설정')).not.toBeInTheDocument()
    expect(screen.getByRole('button',{name:/커리어 시작/})).toBeDisabled()
  })

  it('updates preview and creates a player before navigating to the dashboard', async()=>{
    const provider = new MockGameDataProvider()
    render(<App provider={provider}/>)
    await screen.findByRole('heading',{name:'NEW CAREER'})
    fireEvent.change(screen.getByLabelText('PLAYER NAME'),{target:{value:'테스트선수'}})
    fireEvent.click(screen.getByRole('button',{name:'1B'}))
    fireEvent.click(within(screen.getByRole('group',{name:/BATS/})).getByRole('button',{name:/LEFT/}))
    fireEvent.click(within(screen.getByRole('group',{name:/THROWS/})).getByRole('button',{name:/RIGHT/}))
    fireEvent.click(within(screen.getByRole('group',{name:/STARTING TRAITS/})).getByRole('button',{name:'3'}))
    expect(screen.getByRole('heading',{name:'테스트선수'})).toBeInTheDocument()
    expect(screen.getByText(/1B\s*\|\s*L \/ R/)).toBeInTheDocument()
    expect(screen.getByText('3개 (랜덤)')).toBeInTheDocument()
    const startButton = screen.getByRole('button',{name:/커리어 시작/})
    expect(startButton).toBeEnabled()
    fireEvent.click(startButton)
    await waitFor(async()=>expect(await provider.hasCareer()).toBe(true))
    expect(await screen.findByTestId('ability-contact')).toBeInTheDocument()
    expect(screen.getByRole('heading',{name:/테스트선수/})).toBeInTheDocument()
    expect(screen.getAllByTestId(/ability-/)).toHaveLength(10)
    const created = await provider.getDashboard()
    expect(created.player.position).toBe('1B')
    expect(created.player.batsThrows).toBe('L/R')
    expect(created.traits).toHaveLength(3)
    expect(created.season.game).toBe(0)
  })

  it('renders the focused selected-state Draft Day screen with the requested hierarchy', async()=>{
    window.location.hash='#draft'
    render(<App provider={existingCareerProvider()}/>)
    expect(await screen.findByRole('heading',{name:'KBO DRAFT'})).toBeInTheDocument()
    expect(screen.getByRole('heading',{name:'SELECTED'})).toBeInTheDocument()
    expect(screen.getAllByText('키움 히어로즈').length).toBeGreaterThanOrEqual(2)
    expect(screen.getByText('OVERALL PICK')).toBeInTheDocument()
    expect(screen.getByRole('heading',{name:'PRE-DRAFT PROJECTION'})).toBeInTheDocument()
    expect(screen.getByRole('heading',{name:'TEAM FIT'})).toBeInTheDocument()
    expect(screen.getByRole('heading',{name:'DRAFT RESULT'})).toBeInTheDocument()
    expect(screen.queryAllByText('TEAM INTEREST')).toHaveLength(0)
    expect(screen.getByRole('heading',{name:'FINAL HS RESUME'})).toBeInTheDocument()
    expect(screen.getByRole('heading',{name:'DRAFT FEED'})).toBeInTheDocument()
    expect(screen.getByRole('heading',{name:'ROUND PROGRESS'})).toBeInTheDocument()
    expect(document.querySelector('[data-selected="true"]')).not.toBeNull()
  })

  it('opens and closes the full Draft Board modal with button and ESC', async()=>{
    window.location.hash='#draft'
    render(<App provider={existingCareerProvider()}/>)
    await screen.findByRole('heading',{name:'KBO DRAFT'})
    fireEvent.click(screen.getByRole('button',{name:/전체 드래프트 보기/}))
    expect(await screen.findByRole('dialog')).toBeInTheDocument()
    expect(screen.getByRole('heading',{name:'FULL DRAFT BOARD'})).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button',{name:'전체 드래프트 닫기'}))
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    fireEvent.click(screen.getByRole('button',{name:/전체 드래프트 보기/}))
    expect(await screen.findByRole('dialog')).toBeInTheDocument()
    fireEvent.keyDown(window,{key:'Escape'})
    await waitFor(()=>expect(screen.queryByRole('dialog')).not.toBeInTheDocument())
  })

  it('uses the Pro Career CTA as a safe transition back to the existing KBO career hub', async()=>{
    window.location.hash='#draft'
    render(<App provider={existingCareerProvider()}/>)
    await screen.findByRole('heading',{name:'KBO DRAFT'})
    fireEvent.click(screen.getByRole('button',{name:/프로 커리어 시작/}))
    expect(await screen.findByRole('heading',{name:/김건우/})).toBeInTheDocument()
    expect(window.location.hash).toBe('')
  })

  it('renders player dashboard and all ten abilities including uncapped values for an existing career', async()=>{
    render(<App provider={existingCareerProvider()}/>)
    expect(await screen.findByRole('heading',{name:/김건우/})).toBeInTheDocument()
    expect(screen.getAllByTestId(/ability-/)).toHaveLength(10)
    expect(screen.getByTestId('ability-power')).toHaveTextContent('137')
    expect(screen.getByText(/100 기준선 · 상한 없음/)).toBeInTheDocument()
  })

  it('navigates to season screen and switches leaderboards', async()=>{
    render(<App provider={existingCareerProvider()}/>)
    await screen.findByRole('heading',{name:/김건우/})
    fireEvent.click(screen.getByRole('button',{name:'시즌'}))
    expect(await screen.findByRole('heading',{name:'팀 순위'})).toBeInTheDocument()
    fireEvent.click(screen.getByRole('tab',{name:'HR'}))
    expect(screen.getAllByText('38').length).toBeGreaterThan(0)
  })

  it('connects every app-shell destination to usable provider-backed content', async()=>{
    render(<App provider={existingCareerProvider()}/>)
    await screen.findByRole('heading',{name:/김건우/})
    const checks:[string,string][] = [['커리어','현재 능력치'],['팀','팀 타격 기록'],['리그','팀 순위'],['기록','타이틀 레이스'],['뉴스','3경기 연속 홈런']]
    for(const [nav,label] of checks){
      fireEvent.click(screen.getByRole('button',{name:nav}))
      expect(await screen.findByText(label)).toBeInTheDocument()
      expect(screen.getByRole('button',{name:nav})).toHaveAttribute('aria-current','page')
    }
  })

  it('connects season tabs that already have provider data and leaves monthly report explicit', async()=>{
    render(<App provider={existingCareerProvider()}/>)
    await screen.findByRole('heading',{name:/김건우/})
    fireEvent.click(screen.getByRole('button',{name:'시즌'}))
    fireEvent.click(screen.getByRole('tab',{name:'팀 기록'}))
    expect(await screen.findByText('키움 히어로즈 팀 타격 기록')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('tab',{name:'선수 기록'}))
    expect(await screen.findByText('김건우 시즌 기록')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('tab',{name:'경기 일정/결과'}))
    expect(await screen.findByText('최근 경기 결과')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('tab',{name:'시즌 스토리'}))
    expect(await screen.findByText('3경기 연속 홈런')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('tab',{name:'월간 리포트'}))
    expect(await screen.findByText(/현재 provider에 월간 집계 계약이 없어/)).toBeInTheDocument()
  })

  it('refreshes dashboard and season metadata after a production-supported next-game action', async()=>{
    const provider = existingCareerProvider()
    render(<App provider={provider}/>)
    await screen.findByRole('heading',{name:/김건우/})
    expect(screen.getByText(/GAME 47 \/ 144/)).toBeInTheDocument()
    expect(screen.queryByRole('button',{name:/1주 진행/})).not.toBeInTheDocument()
    expect(screen.queryByRole('button',{name:/1개월 진행/})).not.toBeInTheDocument()
    expect(screen.queryByRole('button',{name:/시즌 끝까지/})).not.toBeInTheDocument()
    fireEvent.click(screen.getByRole('button',{name:/다음 경기/}))
    await waitFor(()=>expect(screen.getByText(/GAME 48 \/ 144/)).toBeInTheDocument())
    expect((await provider.getSeason()).season.game).toBe(48)
  })

  it('disables the next-game mutation and prevents duplicate clicks while a request is in flight', async()=>{
    const provider = new SlowAdvanceProvider()
    render(<App provider={provider}/>)
    await screen.findByRole('heading',{name:/김건우/})
    const advanceButton = screen.getByRole('button',{name:/다음 경기/})
    fireEvent.click(advanceButton)
    fireEvent.click(advanceButton)
    await waitFor(()=>expect(provider.advanceCalls).toBe(1))
    expect(screen.getByRole('button',{name:/경기 진행 중/})).toBeDisabled()
    provider.release()
    await waitFor(()=>expect(screen.getByText(/GAME 48 \/ 144/)).toBeInTheDocument())
  })

  it('reloads authoritative state after a revision conflict instead of applying optimistic state', async()=>{
    const provider = new ConflictProvider()
    render(<App provider={provider}/>)
    await screen.findByRole('heading',{name:/김건우/})
    expect(screen.getByText(/GAME 47 \/ 144/)).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button',{name:/다음 경기/}))
    await waitFor(()=>expect(provider.dashboardReads).toBeGreaterThanOrEqual(2))
    expect(screen.getByRole('alert')).toHaveTextContent('최신 서버 상태로 다시 불러왔습니다')
    expect(screen.getByText(/GAME 47 \/ 144/)).toBeInTheDocument()
  })

  it('renders graceful empty states when optional collections are empty', async()=>{
    render(<App provider={new EmptyOptionalDataProvider()}/>)
    await screen.findByRole('heading',{name:/김건우/})
    fireEvent.click(screen.getByRole('button',{name:'커리어'}))
    expect(await screen.findByText('현재 적용 중인 특성이 없습니다.')).toBeInTheDocument()
    expect(screen.getByText('현재 시즌에 기록된 스토리가 없습니다.')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button',{name:'팀'}))
    expect(await screen.findByText('현재 제공되는 팀 타격 기록이 없습니다.')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button',{name:'리그'}))
    expect(await screen.findByText('현재 리그 순위 데이터가 없습니다.')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button',{name:'뉴스'}))
    expect(await screen.findByText('현재 시즌에 생성된 뉴스 이벤트가 없습니다.')).toBeInTheDocument()
  })

  it('switches title race metric', async()=>{
    render(<App provider={existingCareerProvider()}/>)
    await screen.findByRole('heading',{name:/김건우/})
    fireEvent.click(screen.getByRole('tab',{name:'WAR'}))
    expect(screen.getAllByText('5.7').length).toBeGreaterThan(0)
  })

  it('accepts an explicitly injected provider', async()=>{
    render(<App provider={existingCareerProvider()}/>)
    expect(await screen.findByRole('heading',{name:/김건우/})).toBeInTheDocument()
  })

  it('shows session loading state', async()=>{
    render(<App provider={new SlowProvider()}/>)
    expect(screen.getByRole('status')).toHaveTextContent('저장된 커리어를 확인하는 중입니다.')
    await screen.findByRole('heading',{name:/김건우/})
  })

  it('shows API error state instead of crashing', async()=>{
    render(<App provider={new FailingProvider()}/>)
    await waitFor(()=>expect(screen.getByRole('alert')).toBeInTheDocument())
    expect(screen.getByText('서버와 통신하는 중 문제가 발생했습니다.')).toBeInTheDocument()
  })
})
