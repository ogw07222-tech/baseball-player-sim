import type {
  BackendActiveCareerEffectDto,
  BackendEventChoiceEffectDto,
  BackendInteractiveEventDto,
  BackendResolveEventResultDto,
} from '../types/backendPresentation'

const effectTypeLabel: Record<string,string> = {
  training_focus: '훈련 집중',
  development_modifier: '성장 영향',
  fatigue_modifier: '피로 영향',
  form_modifier: '폼 영향',
  temporary_trait_request: '임시 Trait 요청',
}

const targetLabel: Record<string,string> = {
  player: '선수',
  hitting: '타격',
  defense: '수비',
  defense_range: '수비 범위',
  throwing: '송구',
  weakest_rating: '약점 능력',
  strongest_rating: '강점 능력',
  all: '전체 능력',
  pressure: '압박 대응',
  role_execution: '역할 수행',
}

const magnitudeLabel: Record<string,string> = {
  high: '높음',
  medium: '중간',
  balanced: '균형',
  low: '낮음',
  partial: '부분',
  maintain: '유지',
  upside_medium: '성장 가능성 중간',
  upside_small: '성장 가능성 소폭',
  small: '소폭',
  opportunity_cost_small: '기회비용 소폭',
  opportunity_cost_medium: '기회비용 중간',
  variance_small: '변동성 소폭',
  variance_medium: '변동성 중간',
  cost_small: '부담 소폭',
  cost_medium: '부담 중간',
  recovery_small: '회복 소폭',
  recovery_medium: '회복 중간',
  recovery_large: '회복 큼',
  stability_up: '안정성 상승',
  breakthrough_chance: '돌파 가능성',
  momentum_decay_small: '모멘텀 감소 소폭',
}

const riskLabel: Record<string,string> = { low:'낮음', medium:'중간', high:'높음' }

function simpleValue(value: unknown) {
  if (value === null || value === undefined) return '—'
  if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') return String(value)
  return JSON.stringify(value)
}

function previewText(effect: BackendEventChoiceEffectDto) {
  const type = effectTypeLabel[effect.effect_type] ?? effect.effect_type
  const target = targetLabel[effect.target] ?? effect.target
  const magnitude = magnitudeLabel[effect.magnitude] ?? effect.magnitude
  const duration = effect.duration === null ? '' : ` · ${effect.duration}경기`
  return `${type} · ${target} · ${magnitude}${duration}`
}

function appliedText(effect: BackendActiveCareerEffectDto) {
  const type = effectTypeLabel[effect.effect_type] ?? effect.effect_type
  const target = targetLabel[effect.target] ?? effect.target
  const magnitude = magnitudeLabel[effect.magnitude] ?? effect.magnitude
  return `${type} · ${target} · ${magnitude} · ${effect.games_remaining}경기 남음`
}

function ContextList({ values, emptyLabel }: { values:Record<string,unknown>|null; emptyLabel:string }) {
  const entries = values ? Object.entries(values) : []
  if (!entries.length) return <span className="event-muted">{emptyLabel}</span>
  return <div className="event-context-list">{entries.map(([key,value])=><span key={key}><b>{key}</b> {simpleValue(value)}</span>)}</div>
}

function ResolutionSummary({ result }: { result:BackendResolveEventResultDto }) {
  const selected = result.resolved_event.choices.find(choice=>choice.choice_id===result.resolved_event.selected_choice_id)
  return <section className="event-resolution" aria-label="이벤트 처리 결과">
    <div className="event-section-heading"><strong>처리 결과</strong><span>남은 결정 {result.pending_events.length}</span></div>
    <p><b>{selected?.label ?? result.resolution.selected_choice_id}</b> · {result.resolution.resolution_summary}</p>
    {result.applied_effects.length
      ? <div className="event-effect-list">{result.applied_effects.map((effect,index)=><span key={`${effect.source_event_id}-${effect.effect_type}-${index}`}>{appliedText(effect)}</span>)}</div>
      : <p className="event-muted">현재 적용 중인 효과 요약이 없습니다.</p>}
  </section>
}

export function InteractiveEventPanel({
  events,
  resolving,
  resolvingChoiceId,
  onResolve,
  resolution,
  error,
}: {
  events: BackendInteractiveEventDto[]
  resolving:boolean
  resolvingChoiceId:string|null
  onResolve:(eventId:string,choiceId:string)=>Promise<void>
  resolution:BackendResolveEventResultDto|null
  error:string|null
}) {
  const current = events[0]

  return <section className={`panel interactive-event-panel ${current?.importance ? `importance-${current.importance}` : ''}`} aria-label="선택형 이벤트">
    <header className="panel-header event-panel-header">
      <h2>결정 필요</h2>
      <span className={`event-count ${events.length ? 'active' : ''}`}>{events.length}</span>
    </header>

    {resolution && <ResolutionSummary result={resolution}/>} 
    {error && <div className="event-error" role="alert">{error}</div>}

    {!current ? <div className="event-empty"><strong>현재 처리할 EVENT가 없습니다.</strong><span>시뮬레이션을 진행하면 새로운 결정이 생성될 수 있습니다.</span></div> : <>
      <div className="event-queue-meta"><span>결정 1 / {events.length}</span><span>{current.blocking ? '진행 전 결정 필요' : '선택 가능'}</span></div>
      <div className="event-copy">
        <div className="event-label-row"><span>{current.category}</span><span>{current.importance}</span></div>
        <h3>{current.title}</h3>
        <p>{current.description}</p>
        <div className="event-time"><span>시즌 {current.season}</span><span>GAME {current.game_number}</span>{current.occurred_at && <time>{current.occurred_at}</time>}</div>
      </div>

      <div className="event-context">
        <strong>Context</strong>
        <ContextList values={current.trigger_context} emptyLabel="추가 context 없음"/>
      </div>

      <div className="event-choices" aria-label="이벤트 선택지">
        {current.choices.map(choice=><article className="event-choice" key={choice.choice_id}>
          <div className="event-choice-head"><strong>{choice.label}</strong>{choice.risk_level && <span>리스크 {riskLabel[choice.risk_level] ?? choice.risk_level}</span>}</div>
          <p>{choice.description}</p>
          <div className="event-effect-list">
            {choice.preview_effects.length
              ? choice.preview_effects.map((effect,index)=><span key={`${choice.choice_id}-${index}`}>{previewText(effect)}</span>)
              : <span>backend preview effect 없음</span>}
          </div>
          {choice.requirements && <div className="event-requirements"><b>요구 조건</b><ContextList values={choice.requirements} emptyLabel="없음"/></div>}
          <button
            type="button"
            disabled={resolving}
            aria-busy={resolving && resolvingChoiceId===choice.choice_id}
            onClick={()=>void onResolve(current.event_id,choice.choice_id)}
          >{resolving && resolvingChoiceId===choice.choice_id ? '처리 중…' : '이 선택 적용'}</button>
        </article>)}
      </div>
    </>}
  </section>
}
