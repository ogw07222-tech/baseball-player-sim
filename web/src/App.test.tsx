import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { App } from './App'
import { MockGameDataProvider } from './mock/mockGameDataProvider'
import type { GameDataProvider } from './services/GameDataProvider'

class FailingProvider extends MockGameDataProvider {
  async getDashboard(): ReturnType<GameDataProvider['getDashboard']> { throw new Error('boom') }
}

class SlowProvider extends MockGameDataProvider {
  async getDashboard() { await new Promise(resolve=>setTimeout(resolve,20)); return super.getDashboard() }
  async getSeason() { await new Promise(resolve=>setTimeout(resolve,20)); return super.getSeason() }
}

describe('web UI v0.1',()=>{
  it('renders player dashboard and all ten abilities including uncapped values', async()=>{
    render(<App />)
    expect(await screen.findByRole('heading',{name:/김건우/})).toBeInTheDocument()
    expect(screen.getAllByTestId(/ability-/)).toHaveLength(10)
    expect(screen.getByTestId('ability-power')).toHaveTextContent('137')
    expect(screen.getByText(/100 기준선 · 상한 없음/)).toBeInTheDocument()
  })

  it('navigates to season screen and switches leaderboards', async()=>{
    render(<App />)
    await screen.findByRole('heading',{name:/김건우/})
    fireEvent.click(screen.getByRole('button',{name:'시즌'}))
    expect(await screen.findByRole('heading',{name:'팀 순위'})).toBeInTheDocument()
    fireEvent.click(screen.getByRole('tab',{name:'HR'}))
    expect(screen.getAllByText('38').length).toBeGreaterThan(0)
  })

  it('switches title race metric', async()=>{
    render(<App />)
    await screen.findByRole('heading',{name:/김건우/})
    fireEvent.click(screen.getByRole('tab',{name:'WAR'}))
    expect(screen.getAllByText('5.7').length).toBeGreaterThan(0)
  })

  it('accepts a replaceable provider', async()=>{
    const provider = new MockGameDataProvider()
    render(<App provider={provider}/>)
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
