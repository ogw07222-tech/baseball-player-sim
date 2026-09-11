import { afterEach, describe, expect, it, vi } from 'vitest'
import { BackendTransportError, HttpBackendPresentationGateway } from './HttpBackendPresentationGateway'
import type { BackendDashboardDto, BackendSeasonDto, BackendSnapshotDto } from '../types/backendPresentation'

const progress = { year:2026, game:0, games_completed:0, total_games:144, current_date:'2026-03-31', progress:0 }
const dashboard: BackendDashboardDto = {
  player: { name:'API', age:19, position:'SS', bats_throws:'R/R', team:'키움 히어로즈', roster_level:'FARM', form:'normal', number:null, career_year:1, avatar_url:null },
  abilities: [],
  season_stats: { G:0, PA:0, AVG:0, OBP:0, SLG:0, OPS:0, HR:0, RBI:0, SB:0, WAR:null },
  condition:'unknown', fatigue:0, injury:null, form:'normal', traits:[], league_code:'KBO', league_name:'KBO League', recent_games:[], next_game:null, season_story:[], title_race:{}, progress,
}
const season: BackendSeasonDto = {
  year:2026, league_code:'KBO', league_name:'KBO League', standings:[], hitting_leaderboards:{}, pitching_leaderboards:{}, recent_results:[], team_name:'키움 히어로즈', team_batting:[], team_metrics:[], progress,
}
const response = (body: unknown, status = 200) => Promise.resolve(new Response(JSON.stringify(body), { status, headers:{'Content-Type':'application/json'} }))

const snapshot = (revision:number): BackendSnapshotDto => ({ data:{dashboard,season}, meta:{revision} })

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
    advanced.data.dashboard.progress = { ...progress, game:1, games_completed:1, current_date:'2026-04-01', progress:1 }
    advanced.data.season.progress = { ...progress, game:1, games_completed:1, current_date:'2026-04-01', progress:1 }
    advanced.mutation = {
      kind:'advance', command:'next_game',
      result:{ period_label:'GAME', date_range:'2026-03-31~2026-04-01', games_played:1, hitter_period_line:{}, pitcher_period_line:{}, team_record_delta:{wins:1,losses:0,ties:0}, season_total_line:{}, notable_events:[], rating_changes:{} },
    }
    const fetchMock = vi.fn()
      .mockImplementationOnce(()=>response({has_career:true,revision:7}))
      .mockImplementationOnce(()=>response(advanced))
    vi.stubGlobal('fetch', fetchMock)
    const gateway = new HttpBackendPresentationGateway('/api/v1', ()=>'advance-key')
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
    expect(body.idempotency_key).toBe('advance-key')
  })

  it('retries one retryable transport failure with the same idempotency key', async()=>{
    const advanced = snapshot(8)
    const fetchMock = vi.fn()
      .mockImplementationOnce(()=>response({has_career:true,revision:7}))
      .mockRejectedValueOnce(new TypeError('network response lost'))
      .mockImplementationOnce(()=>response(advanced))
    vi.stubGlobal('fetch', fetchMock)
    const gateway = new HttpBackendPresentationGateway('/api/v1', ()=>'stable-retry-key')
    await gateway.hasCareer()
    await gateway.advanceNextGame()

    expect(fetchMock).toHaveBeenCalledTimes(3)
    const firstAttempt = fetchMock.mock.calls[1][1] as RequestInit
    const retryAttempt = fetchMock.mock.calls[2][1] as RequestInit
    expect(firstAttempt.body).toBe(retryAttempt.body)
    const body = JSON.parse(String(firstAttempt.body)) as Record<string, unknown>
    expect(body.idempotency_key).toBe('stable-retry-key')
    expect(body.expected_revision).toBe(7)
  })

  it('maps a non-mutation network failure to a typed retryable error', async()=>{
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('offline')))
    const gateway = new HttpBackendPresentationGateway()
    await expect(gateway.hasCareer()).rejects.toMatchObject<Partial<BackendTransportError>>({
      status:0,
      code:'NETWORK_ERROR',
      retryable:true,
      revision:null,
    })
  })

  it('preserves backend error details and authoritative revision', async()=>{
    const fetchMock = vi.fn().mockImplementationOnce(()=>response({
      error:{code:'REVISION_CONFLICT',message:'expected_revision is stale',retryable:false,details:{source:'cas'}},
      meta:{revision:9},
    },409))
    vi.stubGlobal('fetch', fetchMock)
    const gateway = new HttpBackendPresentationGateway()
    await expect(gateway.advanceNextGame()).rejects.toMatchObject<Partial<BackendTransportError>>({
      status:409,
      code:'REVISION_CONFLICT',
      retryable:false,
      revision:9,
      details:{source:'cas'},
    })
  })
})
