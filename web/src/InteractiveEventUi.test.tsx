import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'
import { App } from './App'
import { MockGameDataProvider } from './mock/mockGameDataProvider'
import { BackendTransportError } from './services/HttpBackendPresentationGateway'
import type { AdvancePresentationResult, ResolveEventPresentationResult } from './services/GameDataProvider'
import type { BackendAdvanceResultDto, BackendCanonicalEventDto, BackendInteractiveEventDto } from './types/backendPresentation'

const event = (id:string,title:string,importance='normal'):BackendInteractiveEventDto => ({
  event_id:id,event_type:'batting_training_intensity',category:'training',title,description:`${title} 설명`,occurred_at:'2026-04-12',generated_at:'2026-04-12',season:2026,game_number:12,importance,
  trigger_context:{form:'normal',roster_level:'FIRST'},
  choices:[
    {choice_id:'push',label:'강도를 높인다',description:'성장 기회를 늘리되 피로 부담을 감수합니다.',preview_effects:[{effect_type:'training_focus',target:'hitting',magnitude:'high',duration:14,metadata:{}},{effect_type:'fatigue_modifier',target:'player',magnitude:'cost_medium',duration:7,metadata:{}}],risk_level:'medium',requirements:{roster_level:'FIRST'}},
    {choice_id:'balanced',label:'균형을 유지한다',description:'성장과 회복을 균형 있게 가져갑니다.',preview_effects:[{effect_type:'training_focus',target:'hitting',magnitude:'balanced',duration:14,metadata:{}}],risk_level:'low',requirements:null},
  ],
  status:'pending',expires_at:null,source:'04-interactive-event-p1',dedupe_key:`dedupe-${id}`,blocking:false,selected_choice_id:null,resolved_at:null,resolution_summary:null,
})

const careerEvent = ():BackendCanonicalEventDto => ({
  event_id:'career-1',event_type:'roster_promotion',category:'roster',occurred_at:'2026-04-12',season:2026,game_number:12,sequence:0,title:'1군 등록',summary:'선수의 로스터 상태가 1군으로 변경되었습니다.',importance:'major',player_id:'player-1',team_id:'team-1',related_entity_ids:[],state_effects:null,rating_changes:null,injury_effect:null,trait_changes:[],source_command:'next_game',presentation_priority:90,persistence:'career_history',dedupe_key:'career-dedupe-1',
})

class EventProvider extends MockGameDataProvider {
  events:BackendInteractiveEventDto[]
  resolveCalls=0
  resolveError:string|null=null
  removeOnError=false
  nextAdvanceEvents:BackendInteractiveEventDto[]|null=null
  constructor(events:BackendInteractiveEventDto[]=[]){super({hasCareer:true});this.events=structuredClone(events)}
  async getPendingEvents(){return structuredClone(this.events)}
  private advanceResult(command:'next_game'|'week'|'month',games:number):BackendAdvanceResultDto{return {period_label:command,date_range:'2026-04-12~2026-04-13',games_played:games,hitter_period_line:{},pitcher_period_line:{},team_record_delta:null,season_total_line:{},notable_events:[careerEvent()],rating_changes:{},pending_events:structuredClone(this.events)}}
  private async withAdvance(command:'next_game'|'week'|'month',base:Promise<AdvancePresentationResult>,games:number){const dashboard=await base;if(this.nextAdvanceEvents)this.events=structuredClone(this.nextAdvanceEvents);return Object.assign(dashboard,{advanceResult:this.advanceResult(command,games),pendingEvents:structuredClone(this.events)})}
  async advanceNextGame(){return this.withAdvance('next_game',super.advanceNextGame(),1)}
  async advanceWeek(){return this.withAdvance('week',super.advanceWeek(),6)}
  async advanceMonth(){return this.withAdvance('month',super.advanceMonth(),24)}
  async resolveEvent(eventId:string,choiceId:string):Promise<ResolveEventPresentationResult>{
    this.resolveCalls+=1
    const current=this.events.find(item=>item.event_id===eventId)
    if(this.resolveError){if(this.removeOnError)this.events=this.events.filter(item=>item.event_id!==eventId);const status=this.resolveError==='UNSUPPORTED_EVENT_EFFECT'?422:this.resolveError==='NETWORK_ERROR'?0:409;throw new BackendTransportError(status,this.resolveError,'domain error',this.resolveError==='NETWORK_ERROR',49)}
    if(!current)throw new BackendTransportError(404,'EVENT_NOT_FOUND','missing',false,49)
    const choice=current.choices.find(item=>item.choice_id===choiceId)
    if(!choice)throw new BackendTransportError(400,'INVALID_EVENT_CHOICE','invalid',false,49)
    const resolvedEvent={...current,status:'resolved',selected_choice_id:choiceId,resolved_at:'2026-04-12',resolution_summary:`${current.title}: ${choice.label} 선택`}
    this.events=this.events.filter(item=>item.event_id!==eventId)
    return {dashboard:await super.getDashboard(),season:await super.getSeason(),pendingEvents:structuredClone(this.events),result:{resolved_event:resolvedEvent,applied_effects:[{effect_type:'training_focus',target:'hitting',magnitude:'high',games_remaining:14,source_event_id:eventId,parameters:{}}],resolution:{event_id:eventId,selected_choice_id:choiceId,effects:choice.preview_effects,resolved_at:'2026-04-12',resolution_summary:resolvedEvent.resolution_summary},pending_events:structuredClone(this.events)}}
  }
}

class SlowResolveProvider extends EventProvider {
  private releaseResolve:(()=>void)|null=null
  async resolveEvent(eventId:string,choiceId:string){this.resolveCalls+=1;await new Promise<void>(resolve=>{this.releaseResolve=resolve});this.resolveCalls-=1;return super.resolveEvent(eventId,choiceId)}
  release(){this.releaseResolve?.()}
}

afterEach(()=>{window.location.hash=''})
async function openSeason(provider:EventProvider){render(<App provider={provider}/>);await screen.findByRole('heading',{name:/김건우/});fireEvent.click(screen.getByRole('button',{name:/시즌/}));return await screen.findByLabelText('선택형 이벤트')}

describe('Interactive EVENT UI',()=>{
  it('supports no pending EVENT without mixing in Season data',async()=>{
    const panel=await openSeason(new EventProvider())
    expect(within(panel).getByText('현재 처리할 EVENT가 없습니다.')).toBeInTheDocument()
    expect(within(panel).getByText('0')).toBeInTheDocument()
  })

  it('renders one EVENT choice with preview, risk, requirements, and backend context',async()=>{
    const panel=await openSeason(new EventProvider([event('evt-1','타격 훈련 강도 조정')]))
    expect(within(panel).getByText('결정 1 / 1')).toBeInTheDocument()
    expect(within(panel).getByRole('heading',{name:'타격 훈련 강도 조정'})).toBeInTheDocument()
    expect(within(panel).getByText('리스크 중간')).toBeInTheDocument()
    expect(within(panel).getByText('훈련 집중 · 타격 · 높음 · 14경기')).toBeInTheDocument()
    expect(within(panel).getByText('피로 영향 · 선수 · 부담 중간 · 7경기')).toBeInTheDocument()
    expect(within(panel).getAllByText(/roster_level/).length).toBeGreaterThan(0)
  })

  it('preserves backend queue order and displays the next EVENT after resolution',async()=>{
    const provider=new EventProvider([event('evt-a','첫 번째 결정'),event('evt-b','두 번째 결정'),event('evt-c','세 번째 결정')])
    await openSeason(provider)
    expect(screen.getByText('결정 1 / 3')).toBeInTheDocument()
    expect(screen.getByRole('heading',{name:'첫 번째 결정'})).toBeInTheDocument()
    fireEvent.click(screen.getAllByRole('button',{name:'이 선택 적용'})[0])
    expect(await screen.findByRole('heading',{name:'두 번째 결정'})).toBeInTheDocument()
    expect(screen.getByText('결정 1 / 2')).toBeInTheDocument()
    expect(screen.queryByRole('heading',{name:'세 번째 결정'})).not.toBeInTheDocument()
  })

  it('shows only backend resolution summary, applied duration, and remaining count',async()=>{
    await openSeason(new EventProvider([event('evt-a','첫 번째 결정'),event('evt-b','두 번째 결정')]))
    fireEvent.click(screen.getAllByRole('button',{name:'이 선택 적용'})[0])
    const result=await screen.findByLabelText('이벤트 처리 결과')
    expect(result).toHaveTextContent('첫 번째 결정: 강도를 높인다 선택')
    expect(result).toHaveTextContent('훈련 집중 · 타격 · 높음 · 14경기 남음')
    expect(result).toHaveTextContent('남은 결정 1')
  })

  it('prevents duplicate choice dispatch during resolve',async()=>{
    const provider=new SlowResolveProvider([event('evt-slow','느린 결정')])
    await openSeason(provider)
    const button=screen.getAllByRole('button',{name:'이 선택 적용'})[0]
    fireEvent.click(button);fireEvent.click(button)
    await waitFor(()=>expect(provider.resolveCalls).toBe(1))
    expect(screen.getByRole('button',{name:'처리 중…'})).toBeDisabled()
    provider.release()
    await waitFor(()=>expect(screen.getByText('현재 처리할 EVENT가 없습니다.')).toBeInTheDocument())
    expect(provider.resolveCalls).toBe(1)
  })

  it('reloads authoritative state on stale revision',async()=>{
    const provider=new EventProvider([event('evt-old','오래된 결정')]);provider.resolveError='REVISION_CONFLICT';provider.removeOnError=true
    await openSeason(provider);fireEvent.click(screen.getAllByRole('button',{name:'이 선택 적용'})[0])
    expect(await screen.findByRole('alert')).toHaveTextContent('최신 EVENT 상태로 다시 불러왔습니다')
    expect(screen.getByText('현재 처리할 EVENT가 없습니다.')).toBeInTheDocument()
  })

  it('keeps unsupported EVENT pending and exposes the domain error',async()=>{
    const provider=new EventProvider([event('evt-unsupported','지원 대기 선택')]);provider.resolveError='UNSUPPORTED_EVENT_EFFECT'
    await openSeason(provider);fireEvent.click(screen.getAllByRole('button',{name:'이 선택 적용'})[0])
    expect(await screen.findByRole('alert')).toHaveTextContent('현재 이 선택은 아직 지원되지 않습니다')
    expect(screen.getByRole('heading',{name:'지원 대기 선택'})).toBeInTheDocument()
  })

  it('removes already-resolved EVENT only after authoritative refresh',async()=>{
    const provider=new EventProvider([event('evt-resolved','이미 처리된 결정')]);provider.resolveError='EVENT_ALREADY_RESOLVED';provider.removeOnError=true
    await openSeason(provider);fireEvent.click(screen.getAllByRole('button',{name:'이 선택 적용'})[0])
    expect(await screen.findByRole('alert')).toHaveTextContent('이미 처리된 이벤트입니다')
    expect(screen.getByText('현재 처리할 EVENT가 없습니다.')).toBeInTheDocument()
  })

  it('surfaces network failure without deleting EVENT or crashing Season Hub',async()=>{
    const provider=new EventProvider([event('evt-network','네트워크 결정')]);provider.resolveError='NETWORK_ERROR'
    await openSeason(provider);fireEvent.click(screen.getAllByRole('button',{name:'이 선택 적용'})[0])
    expect(await screen.findByRole('alert')).toHaveTextContent('네트워크 연결을 확인해 주세요')
    expect(screen.getByRole('heading',{name:'네트워크 결정'})).toBeInTheDocument()
  })

  it('keeps pending EVENT and automatic CAREER timeline in separate panels',async()=>{
    const provider=new EventProvider();provider.nextAdvanceEvents=[event('evt-after','진행 후 결정')]
    render(<App provider={provider}/>);await screen.findByRole('heading',{name:/김건우/});fireEvent.click(screen.getByRole('button',{name:'1주 진행'}))
    const eventPanel=await screen.findByLabelText('선택형 이벤트')
    expect(within(eventPanel).getByRole('heading',{name:'진행 후 결정'})).toBeInTheDocument()
    expect(within(eventPanel).queryByText('1군 등록')).not.toBeInTheDocument()
    expect(within(screen.getByLabelText('최근 커리어 기록')).getByText('1군 등록')).toBeInTheDocument()
    expect(screen.getByRole('button',{name:/시즌, 결정 필요 1/})).toBeInTheDocument()
  })

  it('exposes merged next-game/week/month commands but no automatic season advance',async()=>{
    const provider=new EventProvider();render(<App provider={provider}/>);await screen.findByRole('heading',{name:/김건우/})
    expect(screen.getByRole('button',{name:'▶ 다음 경기'})).toBeInTheDocument()
    expect(screen.getByRole('button',{name:'1주 진행'})).toBeInTheDocument()
    expect(screen.getByRole('button',{name:'1개월 진행'})).toBeInTheDocument()
    expect(screen.queryByRole('button',{name:/시즌 끝까지/})).not.toBeInTheDocument()
  })

  it('keeps choice actions available in narrow-screen smoke',async()=>{
    Object.defineProperty(window,'innerWidth',{configurable:true,value:480})
    await openSeason(new EventProvider([event('evt-mobile','좁은 화면 결정','major')]))
    expect(screen.getAllByRole('button',{name:'이 선택 적용'})).toHaveLength(2)
    expect(screen.getByRole('heading',{name:'좁은 화면 결정'})).toBeInTheDocument()
  })
})
