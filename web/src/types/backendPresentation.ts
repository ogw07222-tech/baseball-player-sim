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
  progress: Record<string, unknown>
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
  progress: Record<string, unknown>
}
