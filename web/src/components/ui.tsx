import type { ReactNode } from 'react'
import type { AbilityViewModel, LeaderboardEntry } from '../types/viewModels'

export function Panel({ title, action, className='', children }: { title:string; action?:ReactNode; className?:string; children:ReactNode }) {
  return <section className={`panel ${className}`}><header className="panel-header"><h2>{title}</h2>{action}</header>{children}</section>
}

export function Tabs({ items, value, onChange, ariaLabel }: { items:string[]; value:string; onChange:(value:string)=>void; ariaLabel:string }) {
  return <div className="tabs" role="tablist" aria-label={ariaLabel}>{items.map(item => <button key={item} role="tab" aria-selected={value===item} className={value===item?'active':''} onClick={()=>onChange(item)}>{item}</button>)}</div>
}

export function AbilityBar({ stat }: { stat:AbilityViewModel }) {
  const projected = Math.min(100, (Math.log1p(stat.rating) / Math.log1p(200)) * 100)
  const reference = (Math.log1p(100) / Math.log1p(200)) * 100
  const trendIcon = stat.trend==='up'?'▲':stat.trend==='down'?'▼':'–'
  return <div className="ability-row" data-testid={`ability-${stat.key}`}>
    <span className="ability-label">{stat.label}</span>
    <div className="ability-track" aria-label={`${stat.label} ${stat.rating}, KBO 평균 기준 100`}>
      <span className="ability-fill" style={{width:`${projected}%`}} />
      <span className="ability-reference" style={{left:`${reference}%`}}><span className="sr-only">100 기준선</span></span>
    </div>
    <strong>{stat.rating}</strong>
    <span className={`trend ${stat.trend}`}>{trendIcon}{stat.delta===0?'':` ${Math.abs(stat.delta)}`}</span>
  </div>
}

export function Leaderboard({ rows }: { rows:LeaderboardEntry[] }) {
  return <div className="leaderboard">{rows.slice(0,10).map(row => <div className={`leader-row ${row.isUser?'user-row':''}`} key={`${row.rank}-${row.player}`}><span>{row.rank}</span><span className="leader-name">{row.player}<small>{row.team}</small></span><strong>{row.display}</strong></div>)}</div>
}

export function ProgressRing({ value, label }: { value:number; label:string }) {
  return <div className="progress-ring" style={{background:`conic-gradient(var(--accent-cyan) ${Math.min(100,value)}%, var(--panel-alt) 0)`}} aria-label={`${label} ${value}%`}><span>{value}%</span></div>
}

export function LoadingState() {
  return <div className="state-card" role="status"><div className="skeleton wide"/><div className="skeleton"/><div className="skeleton"/>데이터를 불러오는 중입니다.</div>
}

export function ErrorState({ onRetry }: { onRetry:()=>void }) {
  return <div className="state-card error" role="alert"><strong>시즌 정보를 불러올 수 없습니다.</strong><button onClick={onRetry}>다시 시도</button></div>
}
