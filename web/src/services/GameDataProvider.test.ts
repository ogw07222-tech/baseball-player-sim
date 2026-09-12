import { describe, expect, it, vi } from 'vitest'
import { ProductionPresentationProvider, type BackendPresentationGateway } from './GameDataProvider'
import type {
  BackendAdvanceResultDto,
  BackendDashboardDto,
  BackendInteractiveEventDto,
  BackendResolveEventResultDto,
  BackendSeasonDto,
} from '../types/backendPresentation'

const dashboard: BackendDashboardDto = {
  player: { name:'Production Player', age:19, position:'SS', bats_throws:'R/R', team:null, roster_level:'FARM', form:'normal', number:null, career_year:1, avatar_url:null },
  abilities: [],
  season_stats: { G:1, PA:4, AVG:.25, OBP:.25, SLG:.25, OPS:.5, HR:0, RBI:0, SB:0, WAR:null },
  condition:'unknown', fatigue:3, injury:null, form:'normal', traits:[], league_code:'KBO', league_name:'KBO League', recent_games:[], next_game:null, season_story:[], title_race:{}, progress:{year:2026,game:1,total_games:144},
}

const season: BackendSeasonDto = {
  year:2026, league_code:'KBO', league_name:'KBO League', standings:[], hitting_leaderboards:{}, pitching_leaderboards:{}, recent_results:[], team_name:null, team_batting:[], team_metrics:[], progress:{year:2026,game:1,total_games:144},
}

const pendingEvent: BackendInteractiveEventDto = {
  event_id:'evt-1', event_type:'batting_training_intensity', category:'training', title:'타격 훈련 강도 조정', description:'훈련 강도를 선택합니다.',
  occurred_at:'2026-04-01', generated_at:'2026-04-01', season:2026, game_number:1, importance:'normal', trigger_context:{},
  choices:[{choice_id:'balanced',label:'균형을 유지한다',description:'성장과 회복을 균형 있게 가져갑니다.',preview_effects:[{effect_type:'training_focus',target:'hitting',magnitude:'balanced',duration:14,metadata:{}}],risk_level:'low',requirements:null}],
  status:'pending', expires_at:null, source:'04-interactive-event-p1', dedupe_key:'evt-1', blocking:false, selected_choice_id:null, resolved_at:null, resolution_summary:null,
}

const advanceResult: BackendAdvanceResultDto = {
  period_label:'GAME',
  date_range:'2026-03-31~2026-04-01',
  games_played:1,
  hitter_period_line:{},
  pitcher_period_line:{},
  team_record_delta:null,
  season_total_line:{},
  notable_events:[{
    event_id:'career_history:roster:1:roster_promotion', event_type:'roster_promotion', category:'roster', occurred_at:'2026-04-01', season:2026, game_number:1, sequence:0,
    title:'1군 등록', summary:'선수의 로스터 상태가 비1군/개발군에서 1군으로 변경되었습니다.', importance:'major', player_id:'player-1', team_id:'team-1', related_entity_ids:[],
    state_effects:null, rating_changes:null, injury_effect:null, trait_changes:[], source_command:'next_game', presentation_priority:90, persistence:'career_history', dedupe_key:'roster:1',
  }],
  rating_changes:{},
  pending_events:[pendingEvent],
}

const resolveResult: BackendResolveEventResultDto = {
  resolved_event:{...pendingEvent,status:'resolved',selected_choice_id:'balanced',resolved_at:'2026-04-01',resolution_summary:'타격 훈련 강도 조정: 균형을 유지한다 선택'},
  applied_effects:[{effect_type:'training_focus',target:'hitting',magnitude:'balanced',games_remaining:14,source_event_id:'evt-1',parameters:{}}],
  resolution:{event_id:'evt-1',selected_choice_id:'balanced',effects:pendingEvent.choices[0].preview_effects,resolved_at:'2026-04-01',resolution_summary:'타격 훈련 강도 조정: 균형을 유지한다 선택'},
  pending_events:[],
}

const gateway = (): BackendPresentationGateway => ({
  hasCareer: vi.fn(async()=>true),
  createCareer: vi.fn(async()=>dashboard),
  getDashboard: vi.fn(async()=>dashboard),
  getSeason: vi.fn(async()=>season),
  getPendingEvents: vi.fn(async()=>[pendingEvent]),
  advanceNextGame: vi.fn(async()=>({dashboard,result:advanceResult,pendingEvents:[pendingEvent]})),
  advanceWeek: vi.fn(async()=>({dashboard,result:{...advanceResult,period_label:'WEEK'},pendingEvents:[pendingEvent]})),
  advanceMonth: vi.fn(async()=>({dashboard,result:{...advanceResult,period_label:'MONTH'},pendingEvents:[pendingEvent]})),
  advanceSeason: vi.fn(async()=>({dashboard,result:{...advanceResult,period_label:'SEASON'},pendingEvents:[pendingEvent]})),
  resolveEvent: vi.fn(async()=>({dashboard,season,pendingEvents:[],result:resolveResult})),
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

  it('delegates advances while keeping CAREER and pending EVENT domains separate', async()=>{
    const backend = gateway()
    const provider = new ProductionPresentationProvider(backend)
    const result = await provider.advanceNextGame()
    expect(backend.advanceNextGame).toHaveBeenCalledTimes(1)
    expect(result.advanceResult?.notable_events[0].persistence).toBe('career_history')
    expect(result.pendingEvents?.[0].event_id).toBe('evt-1')
    expect(result.pendingEvents?.[0].title).toBe('타격 훈련 강도 조정')
  })

  it('delegates EVENT resolution and returns authoritative remaining state', async()=>{
    const backend = gateway()
    const provider = new ProductionPresentationProvider(backend)
    const result = await provider.resolveEvent('evt-1','balanced')
    expect(backend.resolveEvent).toHaveBeenCalledWith('evt-1','balanced')
    expect(result.result.resolved_event.status).toBe('resolved')
    expect(result.result.applied_effects[0].games_remaining).toBe(14)
    expect(result.pendingEvents).toEqual([])
    expect(result.dashboard.player.name).toBe('Production Player')
  })
})
