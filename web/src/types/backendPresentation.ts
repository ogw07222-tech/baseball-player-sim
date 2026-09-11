export interface BackendAbilityDto {
  key: string
  label: string
  rating: number
  delta?: number
  trend?: string
}

export interface BackendTraitDto {
  name: string
  category: string
  tone: string
}

export interface BackendPlayerSummaryDto {
  name: string
  age: number
  position: string
  bats_throws: string
  team: string | null
  roster_level: string
  form: string
  number: number | null
  career_year: number | null
  avatar_url: string | null
}

export interface BackendSeasonStatsDto {
  G: number
  PA: number
  AVG: number
  OBP: number
  SLG: number
  OPS: number
  HR: number
  RBI: number
  SB: number
  WAR: number | null
}

export interface BackendTeamBattingDto {
  player: string
  G: number
  PA: number
  AB: number
  R: number
  H: number
  '2B': number
  '3B': number
  HR: number
  RBI: number
  SB: number
  BB: number
  SO: number
  AVG: number
  OBP: number
  SLG: number
  OPS: number
  WAR: number | null
  is_user?: boolean
}

export type BackendProgressDto = Record<string, unknown> & {
  year: number
  game: number
  games_completed: number
  total_games: number
  current_date: string | null
  progress: number
}

export interface BackendDashboardDto {
  player: BackendPlayerSummaryDto
  abilities: BackendAbilityDto[]
  season_stats: BackendSeasonStatsDto
  condition: string
  fatigue: number
  injury: string | null
  form: string
  traits: BackendTraitDto[]
  league_code: string
  league_name: string
  recent_games: Record<string, unknown>[]
  next_game: Record<string, unknown> | null
  season_story: Record<string, unknown>[]
  title_race: Record<string, Record<string, unknown>[]>
  progress: BackendProgressDto
}

export interface BackendSeasonDto {
  year: number
  league_code: string
  league_name: string
  standings: Record<string, unknown>[]
  hitting_leaderboards: Record<string, Record<string, unknown>[]>
  pitching_leaderboards: Record<string, Record<string, unknown>[]>
  recent_results: Record<string, unknown>[]
  team_name: string | null
  team_batting: BackendTeamBattingDto[]
  team_metrics: Record<string, unknown>[]
  progress: BackendProgressDto
}

export interface BackendRevisionMetaDto {
  revision: number
}

export interface BackendSessionDto {
  has_career: boolean
  revision: number | null
}

export interface BackendAdvanceEventDto {
  date: string | null
  kind: string
  message: string
}

export interface BackendAdvanceResultDto {
  period_label: string
  date_range: string
  games_played: number
  hitter_period_line: Record<string, unknown>
  pitcher_period_line: Record<string, unknown>
  team_record_delta: { wins: number; losses: number; ties: number } | null
  season_total_line: Record<string, unknown>
  notable_events: BackendAdvanceEventDto[]
  rating_changes: Record<string, number>
}

export type BackendAdvanceCommandDto = 'next_game' | 'week' | 'month' | 'season'

export interface BackendAdvanceMutationDto {
  kind: 'advance'
  command: BackendAdvanceCommandDto
  result: BackendAdvanceResultDto
}

export interface BackendSnapshotDto {
  data: {
    dashboard: BackendDashboardDto
    season: BackendSeasonDto
  }
  meta: BackendRevisionMetaDto
  mutation?: BackendAdvanceMutationDto
}

export interface BackendErrorEnvelopeDto {
  error?: {
    code?: string
    message?: string
    retryable?: boolean
    details?: unknown
  }
  meta?: {
    revision?: number | null
  }
}
