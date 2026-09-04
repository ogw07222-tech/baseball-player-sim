export type Trend = 'up' | 'down' | 'flat'
export type TraitTone = 'positive' | 'negative' | 'neutral'

export interface AbilityViewModel {
  key: string
  label: string
  rating: number
  delta: number
  trend: Trend
}

export interface PlayerViewModel {
  name: string
  number: number
  age: number
  position: string
  batsThrows: string
  team: string
  rosterLevel: string
  careerYear: number
  form: string
  avatarUrl?: string
}

export interface SeasonStatsViewModel {
  g: number
  pa: number
  avg: number
  obp: number
  slg: number
  ops: number
  hr: number
  rbi: number
  sb: number
  war: number
}

export interface RecentGamePoint {
  label: string
  value: number
  outcome: string
}

export interface TraitViewModel {
  name: string
  category: string
  tone: TraitTone
}

export interface NextGameViewModel {
  homeTeam: string
  awayTeam: string
  homeRank: number
  awayRank: number
  homeRecord: string
  awayRecord: string
  date: string
  time: string
  stadium: string
  opposingStarter: string
  throwingHand: string
  era: number
  homeAway: 'HOME' | 'AWAY'
  expectedLineupSpot?: number
}

export interface StoryEventViewModel {
  date: string
  title: string
  detail: string
  category: 'NORMAL' | 'TRAINING' | 'PERFORMANCE' | 'INJURY' | 'ROSTER' | 'RECORD' | 'MAJOR' | 'LEGENDARY'
}

export interface LeaderboardEntry {
  rank: number
  player: string
  team: string
  value: number
  display: string
  isUser?: boolean
}

export interface DashboardViewModel {
  league: { code: string; name: string }
  season: { year: number; game: number; totalGames: number; date: string; progress: number }
  player: PlayerViewModel
  abilities: AbilityViewModel[]
  seasonStats: SeasonStatsViewModel
  recentGames: { metric: string; avg: number; hr: number; ops: number; points: RecentGamePoint[] }
  status: { condition: string; fatigue: number; injury: string; form: string }
  traits: TraitViewModel[]
  nextGame: NextGameViewModel
  seasonStory: StoryEventViewModel[]
  titleRace: Record<string, LeaderboardEntry[]>
}

export interface StandingRow {
  rank: number
  team: string
  w: number
  l: number
  d: number
  pct: number
  gb: string
  streak: string
  isUserTeam?: boolean
}

export interface RecentResult {
  date: string
  awayTeam: string
  awayScore: number
  homeScore: number
  homeTeam: string
  result: 'W' | 'L'
  stadium: string
}

export interface TeamBattingRow {
  player: string
  g: number
  pa: number
  ab: number
  r: number
  h: number
  doubles: number
  triples: number
  hr: number
  rbi: number
  sb: number
  bb: number
  so: number
  avg: number
  obp: number
  slg: number
  ops: number
  war: number
  isUser?: boolean
}

export interface TeamMetric {
  label: string
  value: string
  rank: number
}

export interface SeasonViewModel {
  league: { code: string; name: string }
  season: DashboardViewModel['season']
  standings: StandingRow[]
  hittingLeaderboards: Record<string, LeaderboardEntry[]>
  pitchingLeaderboards: Record<string, LeaderboardEntry[]>
  recentResults: RecentResult[]
  teamName: string
  teamBatting: TeamBattingRow[]
  teamMetrics: TeamMetric[]
}
