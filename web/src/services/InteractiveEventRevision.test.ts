import { afterEach, describe, expect, it, vi } from 'vitest'
import { HttpBackendPresentationGateway } from './HttpBackendPresentationGateway'
import type { BackendInteractiveEventDto, BackendSnapshotDto } from '../types/backendPresentation'

const pending: BackendInteractiveEventDto = {
  event_id:'evt-1',event_type:'batting_training_intensity',category:'training',title:'훈련 결정',description:'선택',occurred_at:'2026-04-01',generated_at:'2026-04-01',season:2026,game_number:1,importance:'normal',trigger_context:{},
  choices:[{choice_id:'balanced',label:'균형',description:'균형 유지',preview_effects:[{effect_type:'training_focus',target:'hitting',magnitude:'balanced',duration:14,metadata:{}}],risk_level:'low',requirements:null}],
  status:'pending',expires_at:null,source:'04-interactive-event-p1',dedupe_key:'evt-1',blocking:false,selected_choice_id:null,resolved_at:null,resolution_summary:null,
}

const snapshot=(revision:number,pendingEvents:BackendInteractiveEventDto[]=[]):BackendSnapshotDto=>({
  data:{
    dashboard:{player:{name:'P',age:19,position:'SS',bats_throws:'R/R',team:null,roster_level:'FARM',form:'normal',number:null,career_year:1,avatar_url:null},abilities:[],season_stats:{G:0,PA:0,AVG:0,OBP:0,SLG:0,OPS:0,HR:0,RBI:0,SB:0,WAR:null},condition:'unknown',fatigue:0,injury:null,form:'normal',traits:[],league_code:'KBO',league_name:'KBO',recent_games:[],next_game:null,season_story:[],title_race:{},progress:{year:2026,game:1,total_games:144}},
    season:{year:2026,league_code:'KBO',league_name:'KBO',standings:[],hitting_leaderboards:{},pitching_leaderboards:{},recent_results:[],team_name:null,team_batting:[],team_metrics:[],progress:{year:2026,game:1,total_games:144}},
    pending_events:pendingEvents,
  },
  meta:{revision},
})

const resolvedSnapshot=()=>{
  const value=snapshot(9,[])
  value.mutation={kind:'resolve_event',event_id:'evt-1',choice_id:'balanced',result:{resolved_event:{...pending,status:'resolved',selected_choice_id:'balanced',resolved_at:'2026-04-01',resolution_summary:'훈련 결정: 균형 선택'},applied_effects:[],resolution:{event_id:'evt-1',selected_choice_id:'balanced',effects:pending.choices[0].preview_effects,resolved_at:'2026-04-01',resolution_summary:'훈련 결정: 균형 선택'},pending_events:[]}}
  return value
}

const advancedSnapshot=()=>{
  const value=snapshot(10,[])
  value.mutation={kind:'advance',command:'week',result:{period_label:'WEEK',date_range:'2026-04-01~2026-04-08',games_played:6,hitter_period_line:{},pitcher_period_line:{},team_record_delta:null,season_total_line:{},notable_events:[],rating_changes:{},pending_events:[]}}
  return value
}

const response=(body:unknown)=>Promise.resolve(new Response(JSON.stringify(body),{status:200,headers:{'Content-Type':'application/json'}}))
afterEach(()=>vi.unstubAllGlobals())

describe('Interactive EVENT revision lifecycle',()=>{
  it('uses the resolve response revision for the next mutation',async()=>{
    const keys=['resolve-key','week-key']
    const fetchMock=vi.fn()
      .mockImplementationOnce(()=>response({has_career:true,revision:8}))
      .mockImplementationOnce(()=>response(resolvedSnapshot()))
      .mockImplementationOnce(()=>response(advancedSnapshot()))
    vi.stubGlobal('fetch',fetchMock)
    const gateway=new HttpBackendPresentationGateway('/api/v1',()=>keys.shift() ?? 'fallback')
    await gateway.hasCareer()
    await gateway.resolveEvent('evt-1','balanced')
    await gateway.advanceWeek()
    const resolveBody=JSON.parse(String((fetchMock.mock.calls[1][1] as RequestInit).body)) as Record<string,unknown>
    const weekBody=JSON.parse(String((fetchMock.mock.calls[2][1] as RequestInit).body)) as Record<string,unknown>
    expect(resolveBody.expected_revision).toBe(8)
    expect(weekBody.expected_revision).toBe(9)
    expect(weekBody.idempotency_key).toBe('week-key')
  })

  it('does not reuse a resolved mutation snapshot for authoritative refresh',async()=>{
    const fetchMock=vi.fn()
      .mockImplementationOnce(()=>response({has_career:true,revision:8}))
      .mockImplementationOnce(()=>response(resolvedSnapshot()))
      .mockImplementationOnce(()=>response(snapshot(9,[])))
    vi.stubGlobal('fetch',fetchMock)
    const gateway=new HttpBackendPresentationGateway('/api/v1',()=> 'resolve-key')
    await gateway.hasCareer()
    await gateway.resolveEvent('evt-1','balanced')
    const [dashboard,events,season]=await Promise.all([gateway.getDashboard(),gateway.getPendingEvents(),gateway.getSeason()])
    expect(dashboard.player.name).toBe('P')
    expect(events).toEqual([])
    expect(season.year).toBe(2026)
    expect(fetchMock.mock.calls[2][0]).toBe('/api/v1/state')
  })
})
