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
  total_games: number
  games_completed?: number
  current_date?: string | null
  progress?: number
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

export interface BackendEventChoiceEffectDto {
  effect_type: string
  target: string
  magnitude: string
  duration: number | null
  metadata: Record<string, unknown>
}

export interface BackendInteractiveEventChoiceDto {
  choice_id: string
  label: string
  description: string
  preview_effects: BackendEventChoiceEffectDto[]
  risk_level: string | null
  requirements: Record<string, unknown> | null
}

export interface BackendInteractiveEventDto {
  event_id: string
  event_type: string
  category: string
  title: string
  description: string
  occurred_at: string | null
  generated_at: string | null
  season: number
  game_number: number
  importance: string
  trigger_context: Record<string, unknown>
  choices: BackendInteractiveEventChoiceDto[]
  status: string
  expires_at: string | null
  source: string
  dedupe_key: string
  blocking: boolean
  selected_choice_id: string | null
  resolved_at: string | null
  resolution_summary: string | null
}

export interface BackendActiveCareerEffectDto {
  effect_type: string
  target: string
  magnitude: string
  games_remaining: number
  source_event_id: string
  parameters: Record<string, unknown>
}

export interface BackendInteractiveEventResolutionDto {
  event_id: string
  selected_choice_id: string
  effects: BackendEventChoiceEffectDto[]
  resolved_at: string | null
  resolution_summary: string
}

export interface BackendResolveEventResultDto {
  resolved_event: BackendInteractiveEventDto
  applied_effects: BackendActiveCareerEffectDto[]
  resolution: BackendInteractiveEventResolutionDto
  pending_events: BackendInteractiveEventDto[]
}

export type BackendCanonicalEventImportanceDto = 'info' | 'normal' | 'major' | 'critical' | string
export type BackendCanonicalEventSourceCommandDto = 'next_game' | 'week' | 'month' | 'lifecycle'

export interface BackendCanonicalEventDto {
  event_id: string
  event_type: string
  category: string
  occurred_at: string | null
  season: number | null
  game_number: number | null
  sequence: number
  title: string
  summary: string
  importance: BackendCanonicalEventImportanceDto
  player_id: string | null
  team_id: string | null
  related_entity_ids: string[]
  state_effects: Record<string, unknown> | null
  rating_changes: Record<string, number> | null
  injury_effect: Record<string, unknown> | null
  trait_changes: string[]
  source_command: BackendCanonicalEventSourceCommandDto
  presentation_priority: number
  persistence: string
  dedupe_key: string
}

export interface BackendAdvanceResultDto {
  period_label: string
  date_range: string
  games_played: number
  hitter_period_line: Record<string, unknown>
  pitcher_period_line: Record<string, unknown>
  team_record_delta: { wins: number; losses: number; ties: number } | null
  season_total_line: Record<string, unknown>
  notable_events: BackendCanonicalEventDto[]
  rating_changes: Record<string, number>
  pending_events: BackendInteractiveEventDto[]
}

export type BackendAdvanceCommandDto = 'next_game' | 'week' | 'month' | 'season'

export interface BackendAdvanceMutationDto {
  kind: 'advance'
  command: BackendAdvanceCommandDto
  result: BackendAdvanceResultDto
}

export interface BackendResolveEventMutationDto {
  kind: 'resolve_event'
  event_id: string
  choice_id: string
  result: BackendResolveEventResultDto
}

export type BackendMutationDto = BackendAdvanceMutationDto | BackendResolveEventMutationDto

export interface BackendSnapshotDto {
  data: {
    dashboard: BackendDashboardDto
    season: BackendSeasonDto
    pending_events: BackendInteractiveEventDto[]
  }
  meta: BackendRevisionMetaDto
  mutation?: BackendMutationDto
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
