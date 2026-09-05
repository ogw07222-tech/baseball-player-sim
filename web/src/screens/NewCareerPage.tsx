import { useMemo, useState } from 'react'
import type { CareerPosition, Handedness, NewCareerRequest, TraitCount } from '../types/newCareer'
import heroArtwork from '../assets/new-career-hero.svg'
import '../newCareer.css'

const positions: Array<{value:CareerPosition; label:string}> = [
  {value:'1B',label:'1루수'}, {value:'2B',label:'2루수'}, {value:'3B',label:'3루수'},
  {value:'SS',label:'유격수'}, {value:'LF',label:'좌익수'}, {value:'CF',label:'중견수'}, {value:'RF',label:'우익수'},
]

const handCode = (hand:Handedness) => hand === 'LEFT' ? 'L' : 'R'

function ChoiceButton({pressed,onClick,children,className=''}:{pressed:boolean;onClick:()=>void;children:React.ReactNode;className?:string}) {
  return <button type="button" className={`career-choice ${pressed?'selected':''} ${className}`} aria-pressed={pressed} onClick={onClick}>{children}</button>
}

export function NewCareerPage({onStart}:{onStart:(request:NewCareerRequest)=>Promise<void>}) {
  const [name,setName] = useState('')
  const [position,setPosition] = useState<CareerPosition>('SS')
  const [bats,setBats] = useState<Handedness>('RIGHT')
  const [throws,setThrows] = useState<Handedness>('RIGHT')
  const [traitCount,setTraitCount] = useState<TraitCount>(2)
  const [submitting,setSubmitting] = useState(false)
  const [error,setError] = useState('')

  const cleanName = name.trim()
  const canStart = cleanName.length > 0 && !submitting
  const previewName = cleanName || '선수 이름'
  const previewLine = useMemo(()=>`${position}  |  ${handCode(bats)} / ${handCode(throws)}`,[position,bats,throws])

  const submit = async() => {
    if (!canStart) return
    setSubmitting(true); setError('')
    try { await onStart({name:cleanName,position,bats,throws,traitCount}) }
    catch { setError('선수를 생성할 수 없습니다. 다시 시도해 주세요.') }
    finally { setSubmitting(false) }
  }

  return <div className="new-career-screen">
    <section className="career-hero" aria-label="새 커리어 소개">
      <img src={heroArtwork} alt="야간 야구장의 가상 선수 실루엣" className="career-hero-art"/>
      <div className="career-hero-shade"/>
      <div className="career-brand"><strong>KBO CAREER</strong><small>BASEBALL PLAYER SIMULATOR</small></div>
      <div className="career-hero-copy">
        <p className="hero-script">BASEBALL<br/>LIVES ON</p>
        <h2>A GREATER<br/><em>PLAYER.</em><br/><span>A DEEPER STORY.</span></h2>
        <div className="hero-rule"/>
        <p className="hero-korean">지금부터,<br/>당신만의 야구 이야기가 시작됩니다.</p>
        <small>HIGH SCHOOL. PRO. AND BEYOND.<br/>ALL IN YOUR HANDS.</small>
      </div>
    </section>

    <main className="career-form-column">
      <header className="career-heading">
        <div><h1>NEW CAREER</h1><p>CREATE YOUR PLAYER <span/></p></div>
        <blockquote>평범한 시작도,<br/>위대한 커리어가 될 수 있다.<small>— KBO</small></blockquote>
      </header>

      <form className="career-form" onSubmit={e=>{e.preventDefault();void submit()}}>
        <div className="form-block name-block">
          <label htmlFor="player-name">PLAYER NAME</label>
          <div className={`career-input ${error?'invalid':''}`}>
            <span aria-hidden="true">●</span>
            <input id="player-name" value={name} maxLength={12} placeholder="선수 이름 입력" onChange={e=>{setName(e.target.value);setError('')}} autoComplete="off"/>
            {name && <button type="button" aria-label="이름 지우기" onClick={()=>setName('')}>×</button>}
          </div>
        </div>

        <fieldset className="form-block position-block">
          <legend>POSITION</legend>
          <div className="position-grid">
            {positions.map(item=><div className="position-option" key={item.value}>
              <ChoiceButton pressed={position===item.value} onClick={()=>setPosition(item.value)}>{item.value}</ChoiceButton>
              <small>{item.label}</small>
            </div>)}
          </div>
        </fieldset>

        <div className="handedness-grid">
          <fieldset className="form-block">
            <legend>BATS <span>(타석)</span></legend>
            <div className="hand-choice-grid">
              <ChoiceButton pressed={bats==='LEFT'} onClick={()=>setBats('LEFT')}><strong>LEFT</strong><small>좌타</small></ChoiceButton>
              <ChoiceButton pressed={bats==='RIGHT'} onClick={()=>setBats('RIGHT')}><strong>RIGHT</strong><small>우타</small></ChoiceButton>
            </div>
          </fieldset>
          <fieldset className="form-block">
            <legend>THROWS <span>(투구)</span></legend>
            <div className="hand-choice-grid">
              <ChoiceButton pressed={throws==='LEFT'} onClick={()=>setThrows('LEFT')}><strong>LEFT</strong><small>좌투</small></ChoiceButton>
              <ChoiceButton pressed={throws==='RIGHT'} onClick={()=>setThrows('RIGHT')}><strong>RIGHT</strong><small>우투</small></ChoiceButton>
            </div>
          </fieldset>
        </div>

        <fieldset className="form-block traits-block">
          <legend>STARTING TRAITS <span>(시작 특성 개수)</span></legend>
          <div className="trait-count-grid">
            {([0,1,2,3] as TraitCount[]).map(count=><ChoiceButton key={count} pressed={traitCount===count} onClick={()=>setTraitCount(count)}>{count}</ChoiceButton>)}
          </div>
          <p>특성은 랜덤으로 부여됩니다. 좋은 특성과 좋지 않은 특성 모두 가능성이 있습니다.</p>
        </fieldset>

        {error && <p className="career-validation" role="alert">{error}</p>}
        <div className="career-cta-row">
          <button className="start-career-button" type="submit" disabled={!canStart}>
            <span>{submitting?'선수 생성 중…':'커리어 시작'}</span><small>START CAREER</small><b aria-hidden="true">›</b>
          </button>
        </div>
      </form>
    </main>

    <aside className="career-preview-column">
      <div className="preview-card">
        <header>PLAYER PREVIEW</header>
        <div className="preview-visual">
          <img src={heroArtwork} alt="가상 선수 미리보기"/>
          <div className="preview-gradient"/>
          <span className="preview-note">A<br/>NEW<br/>JOURNEY</span>
          <div className="preview-identity"><h2>{previewName}</h2><strong>{previewLine}</strong><p>High School Prospect</p></div>
        </div>
        <div className="preview-facts">
          <div><span className="fact-icon">◈</span><p><small>Starting Traits</small><strong>{traitCount}개 (랜덤)</strong></p></div>
          <div><span className="fact-icon mystery">???</span><p><small>Abilities</small><strong>커리어 시작 시 랜덤으로 생성됩니다.</strong></p></div>
        </div>
      </div>

      <div className="generation-info">
        <header><span>i</span> RANDOM GENERATION INFO</header>
        <ul>
          <li>선수의 초기 능력치는 랜덤으로 생성됩니다.</li>
          <li>평균적으로 일반 고교 선수보다 높은 유망주 수준에서 시작합니다.</li>
          <li>Talent는 랜덤으로 결정됩니다.</li>
          <li>선택한 개수만큼 Trait이 랜덤으로 부여됩니다.</li>
          <li>모든 커리어는 서로 다른 이야기로 시작됩니다.</li>
        </ul>
      </div>
      <div className="preview-footer"><strong>KBO CAREER</strong><small>BASEBALL PLAYER SIMULATOR</small></div>
    </aside>
  </div>
}
