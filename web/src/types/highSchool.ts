export type TournamentState = 'ELIMINATED' | 'ACTIVE' | 'UPCOMING'

export interface HighSchoolPlayerVm {
  name: string
  school: string
  schoolEnglish: string
  position: string
  batsThrows: string
  age: number
  yearLabel: string
  scoutedGrade: string
  condition: string
  seasonGrowth: number
}

export interface BracketTeamVm {
  id: string
  name: string
  score?: number
  state: 'player' | 'opponent' | 'eliminated' | 'future' | 'neutral'
}

export interface BracketMatchVm {
  id: string
  round: '32강' | '16강' | '8강'
  top: BracketTeamVm
  bottom: BracketTeamVm
  winnerId?: string
  isCurrent?: boolean
}

export interface HighSchoolHubViewModel {
  seasonLabel: string
  player: HighSchoolPlayerVm
  currentTournament: {
    name: string
    subtitle: string
    stage: string
    homeTeam: string
    awayTeam: string
    date: string
    time: string
    stadium: string
    bracket: BracketMatchVm[]
  }
  seasonTournaments: Array<{ name:string; status:string; state:TournamentState; note?:string }>
  performance: { avg:number; obp:number; slg:number; ops:number; hr:number; bb:number; so:number; sb:number }
  prospectEvaluation: {
    performanceScore: number
    nationalRank: number
    positionRank: number
    percentile: number
    projectedRange: string
  }
  draftStock: { direction:'RISING'|'FALLING'|'STEADY'; delta:number; span:string; projection:string; trend:number[] }
  development: Array<{ key:string; label:string; rating:number; change?:number }>
  recentGames: Array<{ date:string; tournament:string; opponent:string; result:string; outcome:'W'|'L'; line:string }>
  careerNews: Array<{ date:string; headline:string }>
  fullBracket: Array<{ round:string; games:Array<{ a:string; aScore?:number; b:string; bScore?:number; winner?:string }> }>
}
