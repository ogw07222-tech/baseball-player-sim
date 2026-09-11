import { afterEach, describe, expect, it, vi } from 'vitest'
import { BackendTransportError, HttpBackendPresentationGateway } from './HttpBackendPresentationGateway'
import type { BackendDashboardDto, BackendSeasonDto } from '../types/backendPresentation'

const dashboard: BackendDashboardDto = {
  player: { name:'API', age:19, position:'SS', bats_throws:'R/R', team:'키움 히어로즈', roster_level:'FARM', form:'normal', number:null, career_year:1, avatar_url:null },
  abilities: [],
  season_stats: { G:0, PA:0, AVG:0, OBP:0, SLG:0, OPS:0, HR:0, RBI:0, SB:0, WAR:null },
  condition:'unknown', fatigue:0, injury:null, form:'normal', traits:[], league_code:'KBO', league_name:'KBO League', recent_games:[], next_game:null, season_story:[], title_race:{}, progress:{year:2026,game:0,total_games:144},
}
const season: BackendSeasonDto = {
  year:2026, league_code:'KBO', league_name:'KBO League', standings:[], hitting_leaderboards:{}, pitching_leaderboards:{}, recent_results:[], team_name:'키움 히어로즈', team_batting:[], team_metrics:[], progress:{year:2026,game:0,total_games:144},
}
const response = (body: unknown, status = 200) => Promise.resolve(new Response(JSON.stringify(body), { status, headers:{'Content-Type':'application/json'} }))

const snapshot = (revision:number) => ({ data:{dashboard,season}, meta:{revision} })

afterEach(()=>vi.unstubAllGlobals())

describe('HttpBackendPresentationGateway',()=>{
  it('shares an atomic state read for concurrent dashboard and season loading', async()=>{
    const fetchMock = vi.fn()
      .mockImplementationOnce(()=>response({has_career:true,revision:7}))
      .mockImplementationOnce(()=>response(snapshot(7)))
    vi.stubGlobal('fetch', fetchMock)
    const gateway = new HttpBackendPresentationGateway()
    expect(await gateway.hasCareer()).toBe(true)
    const [loadedDashboard, loadedSeason] = await Promise.all([gateway.getDashboard(),gateway.getSeason()])
    expect(loadedDashboard.player.name).toBe('API')
    expect(loadedSeason.year).toBe(2026)
    expect(fetchMock).toHaveBeenCalledTimes(2)
    expect(fetchMock.mock.calls[1][0]).toBe('/api/v1/state')
  })

  it('sends expected revision and reuses the committed snapshot for season', async()=>{
    const advanced = snapshot(8)
    advanced.data.dashboard.progress = {year:2026,game:1,total_games:144}
    advanced.data.season.progress = {year:2026,game:1,total_games:144}
    const fetchMock = vi.fn()
      .mockImplementationOnce(()=>response({has_career:true,revision:7}))
      .mockImplementationOnce(()=>response(advanced))
    vi.stubGlobal('fetch', fetchMock)
    const gateway = new HttpBackendPresentationGateway()
    await gateway.hasCareer()
    const result = await gateway.advanceNextGame()
    expect(result.progress.game).toBe(1)
    const seasonResult = await gateway.getSeason()
    expect(seasonResult.progress.game).toBe(1)
    expect(fetchMock).toHaveBeenCalledTimes(2)
    const init = fetchMock.mock.calls[1][1] as RequestInit
    const body = JSON.parse(String(init.body)) as Record<string, unknown>
    expect(body.command).toBe('next_game')
    expect(body.expected_revision).toBe(7)
    expect(typeof body.idempotency_key).toBe('string')
    expect(String(body.idempotency_key).length).toBeGreaterThan(10)
  })

  it('maps backend conflict envelopes to a typed transport error with authoritative revision', async()=>{
    const fetchMock = vi.fn()
      .mockImplementationOnce(()=>response({has_career:true,revision:7}))
      .mockImplementationOnce(()=>response({error:{code:'REVISION_CONFLICT',message:'expected_revision is stale',retryable:false,details:null},meta:{revision:8}},409))
    vi.stubGlobal('fetch', fetchMock)
    const gateway = new HttpBackendPresentationGateway()
    await gateway.hasCareer()
    await expect(gateway.advanceNextGame()).rejects.toMatchObject({
      name:'BackendTransportError', status:409, code:'REVISION_CONFLICT', retryable:false, revision:8,
    })
  })

  it('maps fetch failures to retryable NETWORK_ERROR without fabricating backend state', async()=>{
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('offline')))
    const gateway = new HttpBackendPresentationGateway()
    let caught: unknown
    try { await gateway.hasCareer() } catch (error) { caught = error }
    expect(caught).toBeInstanceOf(BackendTransportError)
    expect(caught).toMatchObject({status:0,code:'NETWORK_ERROR',retryable:true,revision:null})
  })
})
