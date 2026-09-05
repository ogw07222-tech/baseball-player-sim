import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'
import { App } from './App'
import { MockGameDataProvider } from './mock/mockGameDataProvider'
import type { GameDataProvider } from './services/GameDataProvider'

class FailingProvider extends MockGameDataProvider {
  constructor(){ super({hasCareer:true}) }
  async getDashboard(): ReturnType<GameDataProvider['getDashboard']> { throw new Error('boom') }
}

class SlowProvider extends MockGameDataProvider {
  constructor(){ super({hasCareer:true}) }
  async getDashboard() { await new Promise(resolve=>setTimeout(resolve,20)); return super.getDashboard() }
  async getSeason() { await new Promise(resolve=>setTimeout(resolve,20)); return super.getSeason() }
}

const existingCareerProvider = () => new MockGameDataProvider({hasCareer:true})
afterEach(()=>{ window.location.hash='' })

describe('web UI',()=>{
  it('renders the single-screen new career UI without catcher, wizard steps, or back button', async()=>{
    render(<App />)
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
    expect(screen.getByText('키움 히어로즈')).toBeInTheDocument()
    expect(screen.getByText('OVERALL PICK')).toBeInTheDocument()
    expect(screen.getByRole('heading',{name:'PRE-DRAFT PROJECTION'})).toBeInTheDocument()
    expect(screen.getByRole('heading',{name:'TEAM FIT'})).toBeInTheDocument()
    expect(screen.getByRole('heading',{name:'DRAFT RESULT'})).toBeInTheDocument()
    expect(screen.getAllByText('TEAM INTEREST')).toHaveLength(0)
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

  it('switches title race metric', async()=>{
    render(<App provider={existingCareerProvider()}/>)
    await screen.findByRole('heading',{name:/김건우/})
    fireEvent.click(screen.getByRole('tab',{name:'WAR'}))
    expect(screen.getAllByText('5.7').length).toBeGreaterThan(0)
  })

  it('accepts a replaceable provider', async()=>{
    render(<App provider={existingCareerProvider()}/>)
    expect(await screen.findByRole('heading',{name:/김건우/})).toBeInTheDocument()
  })

  it('shows loading state', async()=>{
    render(<App provider={new SlowProvider()}/>)
    expect(screen.getByRole('status')).toHaveTextContent('데이터를 불러오는 중입니다.')
    await screen.findByRole('heading',{name:/김건우/})
  })

  it('shows error state instead of crashing', async()=>{
    render(<App provider={new FailingProvider()}/>)
    await waitFor(()=>expect(screen.getByRole('alert')).toBeInTheDocument())
    expect(screen.getByText('시즌 정보를 불러올 수 없습니다.')).toBeInTheDocument()
  })
})
