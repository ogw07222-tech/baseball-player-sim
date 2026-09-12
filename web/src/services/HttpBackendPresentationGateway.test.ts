import { afterEach, describe, expect, it, vi } from 'vitest'
import { BackendTransportError, HttpBackendPresentationGateway } from './HttpBackendPresentationGateway'
import type {
  BackendCanonicalEventDto,
  BackendDashboardDto,
  BackendInteractiveEventDto,
  BackendSeasonDto,
  BackendSnapshotDto,
} from '../types/backendPresentation'

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

const interactiveEvent = (eventId:string, title=`EVENT ${eventId}`): BackendInteractiveEventDto => ({
  event_id:eventId,
  event_type:'batting_training_intensity',
  category:'training',
  title,
  description:'훈련 강도를 선택합니다.',
  occurred_at:'2026-04-01',
  generated_at:'2026-04-01',
  season:2026,
  game_number:1,
  importance:'normal',
  trigger_context:{form:'normal'},
  choices:[{
    choice_id:'balanced',
    label:'균형을 유지한다',
    description:'성장과 회복을 균형 있게 가져갑니다.',
    preview_effects:[{effect_type:'training_focus',target:'hitting',magnitude:'balanced',duration:14,metadata:{}}],
    risk_level:'low',
    requirements:null,
  }],
  status:'pending',
  expires_at:null,
  source:'04-interactive-event-p1',
  dedupe_key:`dedupe-${eventId}`,
  blocking:false,
  selected_choice_id:null,
  resolved_at:null,
  resolution_summary:null,
})

const canonicalEvent = (sequence:number, eventType='roster_promotion'): BackendCanonicalEventDto => ({
  event_id:`career_history:roster:${sequence}:${eventType}`,
  event_type:eventType,
  category:eventType.startsWith('roster_') ? 'roster' : 'gameplay',
  occurred_at:'2026-04-01',
  season:2026,
  game_number:1,
  sequence,
  title:eventType === 'roster_promotion' ? '1군 등록' : '경기 주요 장면',
  summary:eventType === 'roster_promotion' ? '선수의 로스터 상태가 비1군/개발군에서 1군으로 변경되었습니다.' : 'WALKOFF',
  importance:'normal',
  player_id:'player-1',
  team_id:'team-1',
  related_entity_ids:[],
  state_effects:null,
  rating_changes:null,
  injury_effect:null,
  trait_changes:[],
  source_command:'next_game',
  presentation_priority:eventType === 'roster_promotion' ? 90 : 40,
  persistence:eventType === 'roster_promotion' ? 'career_history' : 'transient',
  dedupe_key:`career-${sequence}`,
})

const snapshot = (revision:number, pendingEvents:BackendInteractiveEventDto[]=[]): BackendSnapshotDto => ({
  data:{dashboard,season,pending_events:pendingEvents},
  meta:{revision},
})

const advancedSnapshot = (revision=8, pendingEvents=[interactiveEvent('evt-1')]): BackendSnapshotDto => {
  const advanced = snapshot(revision,pendingEvents)
  advanced.data.dashboard.progress = { ...progress, game:1, games_completed:1, current_date:'2026-04-01', progress:1 }
  advanced.data.season.progress = { ...progress, game:1, games_completed:1, current_date:'2026-04-01', progress:1 }
  advanced.mutation = {
    kind:'advance', command:'next_game',
    result:{
      period_label:'GAME',
      date_range:'2026-03-31~2026-04-01',
      games_played:1,
      hitter_period_line:{},
      pitcher_period_line:{},
      team_record_delta:{wins:1,losses:0,ties:0},
      season_total_line:{},
      notable_events:[canonicalEvent(0), canonicalEvent(1,'gameplay_notable')],
      rating_changes:{},
      pending_events:pendingEvents,
    },
  }
  return advanced
}

const resolvedSnapshot = (revision=9, remaining=[interactiveEvent('evt-2')]): BackendSnapshotDto => {
  const resolvedEvent = {...interactiveEvent('evt-1'),status:'resolved',selected_choice_id:'balanced',resolved_at:'2026-04-01',resolution_summary:'훈련 강도 조정: 균형을 유지한다 선택'}
  const value = snapshot(revision,remaining)
  value.mutation = {
    kind:'resolve_event',
    event_id:'evt-1',
    choice_id:'balanced',
    result:{
      resolved_event:resolvedEvent,
      applied_effects:[{effect_type:'training_focus',target:'hitting',magnitude:'balanced',games_remaining:14,source_event_id:'evt-1',parameters:{}}],
      resolution:{event_id:'evt-1',selected_choice_id:'balanced',effects:resolvedEvent.choices[0].preview_effects,resolved_at:'2026-04-01',resolution_summary:resolvedEvent.resolution_summary ?? ''},
      pending_events:remaining,
    },
  }
  return value
}

afterEach(()=>vi.unstubAllGlobals())

describe('HttpBackendPresentationGateway',()=>{
  it('shares an atomic state read for dashboard, season, and pending EVENTs', async()=>{
    const pending = [interactiveEvent('evt-a'),interactiveEvent('evt-b')]
    const fetchMock = vi.fn()
      .mockImplementationOnce(()=>response({has_career:true,revision:7}))
      .mockImplementationOnce(()=>response(snapshot(7,pending)))
    vi.stubGlobal('fetch', fetchMock)
    const gateway = new HttpBackendPresentationGateway()
    expect(await gateway.hasCareer()).toBe(true)
    const [loadedDashboard, loadedEvents, loadedSeason] = await Promise.all([
      gateway.getDashboard(),gateway.getPendingEvents(),gateway.getSeason(),
    ])
    expect(loadedDashboard.player.name).toBe('API')
    expect(loadedSeason.year).toBe(2026)
    expect(loadedEvents.map(event=>event.event_id)).toEqual(['evt-a','evt-b'])
    expect(fetchMock).toHaveBeenCalledTimes(2)
    expect(fetchMock.mock.calls[1][0]).toBe('/api/v1/state')
  })

  it('preserves canonical CAREER events separately from pending EVENT order', async()=>{
    const advanced = advancedSnapshot()
    const fetchMock = vi.fn()
      .mockImplementationOnce(()=>response({has_career:true,revision:7}))
      .mockImplementationOnce(()=>response(advanced))
    vi.stubGlobal('fetch', fetchMock)
    const gateway = new HttpBackendPresentationGateway('/api/v1', ()=>'advance-key')
    await gateway.hasCareer()
    const result = await gateway.advanceNextGame()
    expect(result.dashboard.progress.game).toBe(1)
    expect(result.result.notable_events.map(event=>event.sequence)).toEqual([0,1])
    expect(result.result.notable_events.map(event=>event.event_type)).toEqual(['roster_promotion','gameplay_notable'])
    expect(result.pendingEvents.map(event=>event.event_id)).toEqual(['evt-1'])
    const init = fetchMock.mock.calls[1][1] as RequestInit
    const body = JSON.parse(String(init.body)) as Record<string, unknown>
    expect(body.command).toBe('next_game')
    expect(body.expected_revision).toBe(7)
    expect(body.idempotency_key).toBe('advance-key')
  })

  it('retries an advance network failure with the same idempotency key', async()=>{
    const advanced = advancedSnapshot()
    const fetchMock = vi.fn()
      .mockImplementationOnce(()=>response({has_career:true,revision:7}))
      .mockRejectedValueOnce(new TypeError('network response lost'))
      .mockImplementationOnce(()=>response(advanced))
    vi.stubGlobal('fetch', fetchMock)
    const gateway = new HttpBackendPresentationGateway('/api/v1', ()=>'stable-retry-key')
    await gateway.hasCareer()
    await gateway.advanceNextGame()
    const firstAttempt = fetchMock.mock.calls[1][1] as RequestInit
    const retryAttempt = fetchMock.mock.calls[2][1] as RequestInit
    expect(firstAttempt.body).toBe(retryAttempt.body)
    expect(JSON.parse(String(firstAttempt.body)).idempotency_key).toBe('stable-retry-key')
  })

  it('resolves an EVENT with current revision and preserves remaining backend order', async()=>{
    const resolved = resolvedSnapshot()
    const fetchMock = vi.fn()
      .mockImplementationOnce(()=>response({has_career:true,revision:8}))
      .mockImplementationOnce(()=>response(resolved))
    vi.stubGlobal('fetch', fetchMock)
    const gateway = new HttpBackendPresentationGateway('/api/v1', ()=>'resolve-key')
    await gateway.hasCareer()
    const result = await gateway.resolveEvent('evt-1','balanced')
    expect(result.result.resolved_event.status).toBe('resolved')
    expect(result.result.applied_effects[0].games_remaining).toBe(14)
    expect(result.pendingEvents.map(event=>event.event_id)).toEqual(['evt-2'])
    const [url,init] = fetchMock.mock.calls[1] as [string,RequestInit]
    expect(url).toBe('/api/v1/events/evt-1/resolve')
    const body = JSON.parse(String(init.body)) as Record<string,unknown>
    expect(body.choice_id).toBe('balanced')
    expect(body.expected_revision).toBe(8)
    expect(body.idempotency_key).toBe('resolve-key')
  })

  it('retries EVENT resolution with the exact same request body', async()=>{
    const resolved = resolvedSnapshot()
    const fetchMock = vi.fn()
      .mockImplementationOnce(()=>response({has_career:true,revision:8}))
      .mockRejectedValueOnce(new TypeError('lost response'))
      .mockImplementationOnce(()=>response(resolved))
    vi.stubGlobal('fetch', fetchMock)
    const gateway = new HttpBackendPresentationGateway('/api/v1', ()=>'resolve-retry-key')
    await gateway.hasCareer()
    await gateway.resolveEvent('evt-1','balanced')
    expect((fetchMock.mock.calls[1][1] as RequestInit).body).toBe((fetchMock.mock.calls[2][1] as RequestInit).body)
  })

  it('rejects a malformed successful advance response with no mutation payload', async()=>{
    const fetchMock = vi.fn()
      .mockImplementationOnce(()=>response({has_career:true,revision:7}))
      .mockImplementationOnce(()=>response(snapshot(8)))
    vi.stubGlobal('fetch', fetchMock)
    const gateway = new HttpBackendPresentationGateway()
    await gateway.hasCareer()
    await expect(gateway.advanceNextGame()).rejects.toMatchObject<Partial<BackendTransportError>>({status:502,code:'INVALID_RESPONSE',revision:8})
  })

  it('maps a network failure to a typed retryable error', async()=>{
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('offline')))
    const gateway = new HttpBackendPresentationGateway()
    await expect(gateway.hasCareer()).rejects.toMatchObject<Partial<BackendTransportError>>({status:0,code:'NETWORK_ERROR',retryable:true,revision:null})
  })

  it('preserves backend domain errors and authoritative revision', async()=>{
    const fetchMock = vi.fn().mockImplementationOnce(()=>response({
      error:{code:'UNSUPPORTED_EVENT_EFFECT',message:'temporary Trait semantics are not implemented in production',retryable:false,details:null},
      meta:{revision:9},
    },422))
    vi.stubGlobal('fetch', fetchMock)
    const gateway = new HttpBackendPresentationGateway()
    await expect(gateway.resolveEvent('evt-1','trait')).rejects.toMatchObject<Partial<BackendTransportError>>({status:422,code:'UNSUPPORTED_EVENT_EFFECT',retryable:false,revision:9})
  })
})
