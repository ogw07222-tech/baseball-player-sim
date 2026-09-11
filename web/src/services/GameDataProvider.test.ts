import { describe, expect, it, vi } from 'vitest'
import { ProductionPresentationProvider, type BackendPresentationGateway } from './GameDataProvider'
import type { BackendDashboardDto, BackendSeasonDto } from '../types/backendPresentation'

const dashboard: BackendDashboardDto = {
  player: { name:'Production Player', age:19, position:'SS', bats_throws:'R/R', team:null, roster_level:'FARM', form:'normal', number:null, career_year:1, avatar_url:null },
  abilities: [],
  season_stats: { G:1, PA:4, AVG:.25, OBP:.25, SLG:.25, OPS:.5, HR:0, RBI:0, SB:0, WAR:null },
  condition:'unknown', fatigue:3, injury:null, form:'normal', traits:[], league_code:'KBO', league_name:'KBO League', recent_games:[], next_game:null, season_story:[], title_race:{}, progress:{year:2026,game:1,total_games:144},
}

const season: BackendSeasonDto = {
  year:2026, league_code:'KBO', league_name:'KBO League', standings:[], hitting_leaderboards:{}, pitching_leaderboards:{}, recent_results:[], team_name:null, team_batting:[], team_metrics:[], progress:{year:2026,game:1,total_games:144},
}

const gateway = (): BackendPresentationGateway => ({
  hasCareer: vi.fn(async()=>true),
  createCareer: vi.fn(async()=>dashboard),
  getDashboard: vi.fn(async()=>dashboard),
  getSeason: vi.fn(async()=>season),
  advanceNextGame: vi.fn(async()=>dashboard),
  advanceWeek: vi.fn(async()=>dashboard),
  advanceMonth: vi.fn(async()=>dashboard),
  advanceSeason: vi.fn(async()=>dashboard),
  saveGame: vi.fn(async()=>undefined),
})

describe('ProductionPresentationProvider',()=>{
  it('adapts backend DTOs without inventing missing production values', async()=>{
    const provider = new ProductionPresentationProvider(gateway())
    const loaded = await provider.getDashboard()
    expect(loaded.player.name).toBe('Production Player')
    expect(loaded.player.team).toBeNull()
    expect(loaded.seasonStats.war).toBeNull()
    expect(loaded.nextGame).toBeNull()
    expect(loaded.season.game).toBe(1)
  })

  it('delegates next-game mutations to the backend gateway', async()=>{
    const backend = gateway()
    const provider = new ProductionPresentationProvider(backend)
    await provider.advanceNextGame()
    expect(backend.advanceNextGame).toHaveBeenCalledTimes(1)
  })
})
