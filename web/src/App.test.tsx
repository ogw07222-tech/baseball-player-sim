import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
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

async function createHighSchoolCareer(){
  const provider = new MockGameDataProvider()
  render(<App provider={provider}/>)
  await screen.findByRole('heading',{name:'NEW CAREER'})
  fireEvent.change(screen.getByLabelText('PLAYER NAME'),{target:{value:'테스트선수'}})
  fireEvent.click(screen.getByRole('button',{name:'1B'}))
  fireEvent.click(within(screen.getByRole('group',{name:/BATS/})).getByRole('button',{name:/LEFT/}))
  fireEvent.click(within(screen.getByRole('group',{name:/THROWS/})).getByRole('button',{name:/RIGHT/}))
  fireEvent.click(within(screen.getByRole('group',{name:/STARTING TRAITS/})).getByRole('button',{name:'3'}))
  fireEvent.click(screen.getByRole('button',{name:/커리어 시작/}))
  await waitFor(async()=>expect(await provider.hasCareer()).toBe(true))
  return provider
}

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

  it('creates a player and routes directly into the one-page high school career hub', async()=>{
    const provider = await createHighSchoolCareer()
    expect(await screen.findByRole('heading',{name:'HIGH SCHOOL CAREER'})).toBeInTheDocument()
    expect(screen.getByRole('heading',{name:'테스트선수'})).toBeInTheDocument()
    expect(screen.getByText('1B')).toBeInTheDocument()
    expect(screen.getByText('L / R')).toBeInTheDocument()
    expect(screen.getByRole('heading',{name:'CURRENT TOURNAMENT'})).toBeInTheDocument()
    expect(screen.getByRole('heading',{name:'PROSPECT EVALUATION'})).toBeInTheDocument()
    expect(screen.queryByRole('button',{name:'PLAYER'})).not.toBeInTheDocument()
    expect(screen.queryByRole('button',{name:'STATS'})).not.toBeInTheDocument()
    expect(screen.queryByRole('button',{name:'TOURNAMENTS'})).not.toBeInTheDocument()
    expect(screen.queryByRole('button',{name:'RANKINGS'})).not.toBeInTheDocument()
    const created = await provider.getDashboard()
    expect(created.player.position).toBe('1B')
    expect(created.player.batsThrows).toBe('L/R')
    expect(created.traits).toHaveLength(3)
  })

  it('shows the compact player status separately from performance score', async()=>{
    await createHighSchoolCareer()
    expect(await screen.findByText('Scouted Grade')).toBeInTheDocument()
    expect(screen.getByText('A-')).toBeInTheDocument()
    expect(screen.getByText('Performance Score')).toBeInTheDocument()
    expect(screen.getByText('132')).toBeInTheDocument()
    expect(screen.getByText('HS PERFORMANCE BASED')).toBeInTheDocument()
    expect(screen.getByText('예상 지명 범위')).toBeInTheDocument()
    expect(screen.getByText('2–3 ROUND')).toBeInTheDocument()
  })

  it('renders the player-path bracket and opens/closes the full bracket modal', async()=>{
    await createHighSchoolCareer()
    expect(await screen.findByLabelText('현재 선수 대진 경로')).toBeInTheDocument()
    expect(screen.getAllByText('서울 한빛고').length).toBeGreaterThan(0)
    fireEvent.click(screen.getByRole('button',{name:'전체 대진표 보기'}))
    expect(await screen.findByRole('dialog')).toBeInTheDocument()
    expect(screen.getByRole('heading',{name:'FULL TOURNAMENT BRACKET'})).toBeInTheDocument()
    fireEvent.keyDown(window,{key:'Escape'})
    await waitFor(()=>expect(screen.queryByRole('dialog')).not.toBeInTheDocument())
  })

  it('shows all four high school tournaments, development, recent games, news, and draft trend', async()=>{
    await createHighSchoolCareer()
    expect(await screen.findByText('청룡기')).toBeInTheDocument()
    expect(screen.getByText('황금사자기')).toBeInTheDocument()
    expect(screen.getByText('대통령배')).toBeInTheDocument()
    expect(screen.getByText('봉황대기')).toBeInTheDocument()
    expect(screen.getByRole('heading',{name:'HIGH SCHOOL PERFORMANCE'})).toBeInTheDocument()
    expect(screen.getByRole('heading',{name:'DRAFT STOCK'})).toBeInTheDocument()
    expect(screen.getByText('RISING')).toBeInTheDocument()
    expect(screen.getByRole('heading',{name:'PLAYER DEVELOPMENT'})).toBeInTheDocument()
    expect(screen.getByText('Resilience')).toBeInTheDocument()
    expect(screen.getByRole('heading',{name:'RECENT GAMES'})).toBeInTheDocument()
    expect(screen.getByRole('heading',{name:'CAREER NEWS'})).toBeInTheDocument()
  })

  it('keeps the existing KBO player dashboard and uncapped ability display working', async()=>{
    render(<App provider={existingCareerProvider()}/>)
    expect(await screen.findByRole('heading',{name:/김건우/})).toBeInTheDocument()
    expect(screen.getAllByTestId(/ability-/)).toHaveLength(10)
    expect(screen.getByTestId('ability-power')).toHaveTextContent('137')
    expect(screen.getByText(/100 기준선 · 상한 없음/)).toBeInTheDocument()
  })

  it('navigates to season screen and switches leaderboards for an existing KBO career', async()=>{
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
