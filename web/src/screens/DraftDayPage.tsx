import { useEffect, useRef, useState } from 'react'
import type { DraftBoardRow, DraftDayViewModel } from '../types/draftDay'
import '../draftDay.css'

const fmt3=(value:number)=>value.toFixed(3).replace(/^0/,'')

function DraftTable({rows}:{rows:DraftBoardRow[]}){
  return <div className="dd-board-table" role="table" aria-label="드래프트 보드">
    <div className="dd-board-row head" role="row"><span>PICK</span><span>TEAM</span><span>PLAYER</span><span>POS</span><span>SCHOOL</span><span>GRADE</span></div>
    {rows.map(row=><div key={row.pick} className={`dd-board-row ${row.selected?'selected':''}`} role="row" data-selected={row.selected?'true':undefined}>
      <span>{row.pick}</span><span>{row.team}</span><strong>{row.player}</strong><span>{row.pos}</span><span>{row.school}</span><b>{row.grade}</b>
    </div>)}
  </div>
}

function FullDraftModal({data,onClose}:{data:DraftDayViewModel;onClose:()=>void}){
  const closeRef=useRef<HTMLButtonElement>(null)
  useEffect(()=>{ closeRef.current?.focus(); const onKey=(e:KeyboardEvent)=>{if(e.key==='Escape')onClose()}; window.addEventListener('keydown',onKey); return()=>window.removeEventListener('keydown',onKey)},[onClose])
  return <div className="dd-modal-backdrop" role="presentation" onMouseDown={e=>{if(e.currentTarget===e.target)onClose()}}>
    <section className="dd-modal" role="dialog" aria-modal="true" aria-labelledby="full-draft-title">
      <header><div><small>2026 ROOKIE DRAFT</small><h2 id="full-draft-title">FULL DRAFT BOARD</h2></div><button ref={closeRef} aria-label="전체 드래프트 닫기" onClick={onClose}>×</button></header>
      <DraftTable rows={data.fullDraftBoard}/>
    </section>
  </div>
}

export function DraftDayPage({data,onStartProCareer}:{data:DraftDayViewModel;onStartProCareer:()=>void}){
  const [fullOpen,setFullOpen]=useState(false)
  return <div className="dd-screen">
    <header className="dd-header">
      <div><strong>BASEBALL PLAYER SIM</strong><small>ONE PLAYER, A BIGGER STORY</small></div>
      <div className="dd-header-title"><h1>KBO DRAFT</h1><span>{data.year} ROOKIE DRAFT</span></div>
      <div className="dd-header-right"><span>DRAFT COMPLETE</span><i></i><button aria-label="설정" disabled title="설정 기능 준비 중">⚙</button></div>
    </header>

    <main className="dd-layout">
      <aside className="dd-left">
        <section className="dd-card dd-player-card">
          <div className="dd-player-art" aria-label="가상 고교 야구선수 이미지"><div className="dd-player-shape"></div><span>HIGH SCHOOL PROSPECT</span></div>
          <div className="dd-player-info">
            <h2>{data.player.name}</h2>
            <p>{data.player.school}<br/><small>{data.player.schoolEn}</small></p>
            <div className="dd-player-meta"><div><small>포지션</small><b>{data.player.position}</b></div><div><small>타석/투구</small><b>{data.player.batsThrows}</b></div><div><small>나이</small><b>{data.player.age}</b></div></div>
            <div className="dd-hs-stats">{[['AVG',fmt3(data.player.avg)],['OBP',fmt3(data.player.obp)],['SLG',fmt3(data.player.slg)],['OPS',fmt3(data.player.ops)]].map(([k,v])=><div key={k}><small>{k}</small><strong>{v}</strong></div>)}</div>
            <div className="dd-eval-strip"><div><small>Performance Score</small><strong>{data.player.performanceScore}</strong></div><div><small>전국 순위</small><strong>#{data.player.nationalRank}</strong></div><div><small>포지션 순위</small><strong>{data.player.positionRank}</strong></div></div>
            <div className="dd-scouted"><small>Scouted Grade</small><strong>{data.player.scoutedGrade}</strong></div>
          </div>
        </section>
        <section className="dd-card dd-resume"><div className="dd-title"><h3>FINAL HS RESUME</h3></div><div className="dd-resume-grid">{data.finalHighSchoolResume.map(x=><div key={x.tournament}><small>{x.tournament}</small><strong>{x.result}</strong></div>)}</div><footer>시즌 OPS {fmt3(data.resumeFooter.ops)} <span>·</span> HR {data.resumeFooter.hr} <span>·</span> SB {data.resumeFooter.sb}</footer></section>
      </aside>

      <section className="dd-center">
        <section className="dd-card dd-hero">
          <div className="dd-stage-lights"/><div className="dd-back-player"><span>{data.player.name.slice(-2)}</span></div>
          <div className="dd-hero-copy"><p>고교에서 프로로,<br/>더 큰 꿈의 무대가 시작됩니다.</p><small>KBO DRAFT {data.year}</small><h2>SELECTED</h2><em>꿈은 계속된다.</em></div>
          <div className="dd-selection-card">
            <div className="dd-crest" aria-hidden="true">{data.selectedTeam.crestLetter}</div>
            <div className="dd-team"><strong>{data.selectedTeam.name}</strong><small>{data.selectedTeam.shortName}</small><p>{data.player.name} <span>·</span> {data.player.position} <span>·</span> {data.player.school}</p></div>
            <div className="dd-result-block"><small>ROUND</small><strong>{data.draftResult.round}</strong></div>
            <div className="dd-result-block pick"><small>OVERALL PICK</small><strong>{data.draftResult.overallPick}</strong></div>
          </div>
        </section>

        <section className="dd-card dd-board"><div className="dd-title"><h3>DRAFT BOARD</h3><button onClick={()=>setFullOpen(true)}>전체 드래프트 보기 →</button></div><DraftTable rows={data.draftBoard}/></section>

        <div className="dd-center-bottom">
          <section className="dd-card dd-feed"><div className="dd-title"><h3>DRAFT FEED</h3><small>최근 지명</small></div><div className="dd-feed-list">{data.draftFeed.map((x,i)=><div key={`${x.round}-${x.pick}-${i}`}><b>{x.round}</b><span>{x.pick}</span><strong>{x.player}</strong><span>{x.pos}</span><span>{x.school}</span><span>{x.team}</span></div>)}</div></section>
          <section className="dd-card dd-progress"><div className="dd-title"><h3>ROUND PROGRESS</h3></div>{data.roundProgress.map(x=><div key={x.round} className={`dd-progress-row ${x.status.toLowerCase()}`}><strong>ROUND {x.round}</strong><span>{x.status}</span><small>{x.progress??'(–)'}</small></div>)}</section>
        </div>
      </section>

      <aside className="dd-right">
        <section className="dd-card dd-projection"><div className="dd-title"><h3>PRE-DRAFT PROJECTION</h3><small>PRE-DRAFT SCOUTING REPORT</small></div><div className="dd-kv-list">{data.preDraftProjection.map(x=><div key={x.label}><span>{x.label}</span><strong className={x.tone??''}>{x.value}</strong></div>)}</div></section>
        <section className="dd-card dd-fit"><div className="dd-title"><h3>TEAM FIT</h3><small>SELECTED ORGANIZATION</small></div><div className="dd-fit-list">{data.teamFit.map(x=><div key={x.label}><div><span>{x.label}</span><strong>{x.value}</strong></div><div className="dd-fit-track"><i style={{width:`${x.percent}%`}}/></div></div>)}</div></section>
        <section className="dd-card dd-draft-result"><div className="dd-title"><h3>DRAFT RESULT</h3><small>YOUR NEXT CHAPTER</small></div><div className="dd-kv-list"><div><span>지명 라운드</span><strong>ROUND {data.draftResult.round}</strong></div><div><span>전체 지명 순번</span><strong>{data.draftResult.overallPick}</strong></div><div><span>지명 구단</span><strong>{data.selectedTeam.name}</strong></div><div><span>포지션</span><strong>{data.player.position}</strong></div><div><span>선수 구분</span><strong>{data.draftResult.playerType}</strong></div><div><span>계약 진행 상태</span><strong>{data.draftResult.contractStatus}</strong></div></div><button className="dd-primary-cta" onClick={onStartProCareer}>프로 커리어 시작 <span>▶</span></button><blockquote>“지금부터, 진짜 이야기가 시작된다.”</blockquote></section>
      </aside>
    </main>
    {fullOpen&&<FullDraftModal data={data} onClose={()=>setFullOpen(false)}/>} 
  </div>
}
