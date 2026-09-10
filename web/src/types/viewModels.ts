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
  number: number | null
  age: number
  position: string
  batsThrows: string
  team: string | null
  rosterLevel: string
  careerYear: number | null
  form: string
  avatarUrl?: string | null
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
  war: number | null
}

export interface RecentGamePoint {
  label: string
  value: number
  outcome: string
}

export interface RecentGamesViewModel {
  metric: string | null
  avg: number | null
  hr: number | null
  ops: number | null
  points: RecentGamePoint[]
}

export interface TraitViewModel {
  name: string
  category: string
  tone: TraitTone
}

export interface SeasonProgressViewModel {
  year: number | null
  game: number | null
  totalGames: number | null
  date: string | null
  progress: number | null
}

export interface NextGameViewModel {
  homeTeam: string
  awayTeam: string
  homeRank: number | null
  awayRank: number | null
  homeRecord: string | null
  awayRecord: string | null
  date: string
  time: string | null
  stadium: string | null
  opposingStarter: string | null
  throwingHand: string | null
  era: number | null
  homeAway: 'HOME' | 'AWAY' | null
  expectedLineupSpot?: number | null
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
  season: SeasonProgressViewModel
  player: PlayerViewModel
  abilities: AbilityViewModel[]
  seasonStats: SeasonStatsViewModel
  recentGames: RecentGamesViewModel
  status: { condition: string; fatigue: number; injury: string | null; form: string }
  traits: TraitViewModel[]
  nextGame: NextGameViewModel | null
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
  war: number | null
  isUser?: boolean
}

export interface TeamMetric {
  label: string
  value: string
  rank: number
}

export interface SeasonViewModel {
  league: { code: string; name: string }
  season: SeasonProgressViewModel
  standings: StandingRow[]
  hittingLeaderboards: Record<string, LeaderboardEntry[]>
  pitchingLeaderboards: Record<string, LeaderboardEntry[]>
  recentResults: RecentResult[]
  teamName: string | null
  teamBatting: TeamBattingRow[]
  teamMetrics: TeamMetric[]
}
