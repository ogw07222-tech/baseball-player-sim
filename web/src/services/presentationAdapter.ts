import type { BackendDashboardDto, BackendSeasonDto } from '../types/backendPresentation'
import type {
  DashboardViewModel,
  LeaderboardEntry,
  NextGameViewModel,
  RecentGamePoint,
  RecentResult,
  SeasonProgressViewModel,
  SeasonViewModel,
  StandingRow,
  StoryEventViewModel,
  TeamMetric,
  TraitTone,
  Trend,
} from '../types/viewModels'

const finiteNumber = (value: unknown): number | null =>
  typeof value === 'number' && Number.isFinite(value) ? value : null

const nonEmptyString = (value: unknown): string | null =>
  typeof value === 'string' && value.trim().length > 0 ? value : null

const optionalBoolean = (value: unknown): boolean | undefined =>
  typeof value === 'boolean' ? value : undefined

const firstNumber = (source: Record<string, unknown>, keys: string[]) => {
  for (const key of keys) {
    const value = finiteNumber(source[key])
    if (value !== null) return value
  }
  return null
}

const firstString = (source: Record<string, unknown>, keys: string[]) => {
  for (const key of keys) {
    const value = nonEmptyString(source[key])
    if (value !== null) return value
  }
  return null
}

const adaptTrend = (value: unknown): Trend =>
  value === 'up' || value === 'down' ? value : 'flat'

const adaptTone = (value: unknown): TraitTone =>
  value === 'positive' || value === 'negative' ? value : 'neutral'

function adaptProgress(raw: Record<string, unknown>, fallbackYear: number | null = null): SeasonProgressViewModel {
  const game = firstNumber(raw, ['game', 'games_completed'])
  const totalGames = firstNumber(raw, ['total_games', 'totalGames'])
  const explicitProgress = firstNumber(raw, ['progress', 'progress_pct', 'progressPercent'])
  const computedProgress = game !== null && totalGames !== null && totalGames > 0
    ? Math.round((game / totalGames) * 100)
    : null

  return {
    year: firstNumber(raw, ['year', 'season_year']) ?? fallbackYear,
    game,
    totalGames,
    date: firstString(raw, ['date', 'current_date']),
    progress: explicitProgress ?? computedProgress,
  }
}

function adaptLeaderboardEntry(raw: Record<string, unknown>): LeaderboardEntry | null {
  const rank = finiteNumber(raw.rank)
  const player = nonEmptyString(raw.player)
  const team = nonEmptyString(raw.team)
  const value = finiteNumber(raw.value)
  if (rank === null || player === null || team === null || value === null) return null

  return {
    rank,
    player,
    team,
    value,
    display: nonEmptyString(raw.display) ?? String(value),
    isUser: optionalBoolean(raw.is_user ?? raw.isUser),
  }
}

function adaptNextGame(raw: Record<string, unknown> | null): NextGameViewModel | null {
  if (!raw) return null
  const homeTeam = firstString(raw, ['home_team', 'homeTeam'])
  const awayTeam = firstString(raw, ['away_team', 'awayTeam'])
  const date = nonEmptyString(raw.date)
  if (!homeTeam || !awayTeam || !date) return null

  const homeAway = raw.home_away ?? raw.homeAway
  return {
    homeTeam,
    awayTeam,
    homeRank: firstNumber(raw, ['home_rank', 'homeRank']),
    awayRank: firstNumber(raw, ['away_rank', 'awayRank']),
    homeRecord: firstString(raw, ['home_record', 'homeRecord']),
    awayRecord: firstString(raw, ['away_record', 'awayRecord']),
    date,
    time: nonEmptyString(raw.time),
    stadium: nonEmptyString(raw.stadium),
    opposingStarter: firstString(raw, ['opposing_starter', 'opposingStarter']),
    throwingHand: firstString(raw, ['throwing_hand', 'throwingHand']),
    era: finiteNumber(raw.era),
    homeAway: homeAway === 'HOME' || homeAway === 'AWAY' ? homeAway : null,
    expectedLineupSpot: firstNumber(raw, ['expected_lineup_spot', 'expectedLineupSpot']),
  }
}

function adaptRecentPoint(raw: Record<string, unknown>): RecentGamePoint | null {
  const label = nonEmptyString(raw.label)
  const value = finiteNumber(raw.value)
  const outcome = nonEmptyString(raw.outcome)
  return label && value !== null && outcome ? { label, value, outcome } : null
}

function adaptStory(raw: Record<string, unknown>): StoryEventViewModel | null {
  const title = nonEmptyString(raw.title)
  if (!title) return null
  const categories = ['NORMAL', 'TRAINING', 'PERFORMANCE', 'INJURY', 'ROSTER', 'RECORD', 'MAJOR', 'LEGENDARY'] as const
  const candidate = nonEmptyString(raw.category)?.toUpperCase()
  const category = (categories as readonly string[]).includes(candidate ?? '')
    ? candidate as StoryEventViewModel['category']
    : 'NORMAL'

  return {
    date: nonEmptyString(raw.date) ?? '',
    title,
    detail: nonEmptyString(raw.detail) ?? '',
    category,
  }
}

export function adaptDashboardDto(raw: BackendDashboardDto): DashboardViewModel {
  const recentPoints = raw.recent_games
    .map(adaptRecentPoint)
    .filter((row): row is RecentGamePoint => row !== null)
  const titleRace = Object.fromEntries(
    Object.entries(raw.title_race).map(([metric, rows]) => [
      metric,
      rows.map(adaptLeaderboardEntry).filter((row): row is LeaderboardEntry => row !== null),
    ]),
  )

  return {
    league: { code: raw.league_code, name: raw.league_name },
    season: adaptProgress(raw.progress),
    player: {
      name: raw.player.name,
      number: raw.player.number,
      age: raw.player.age,
      position: raw.player.position,
      batsThrows: raw.player.bats_throws,
      team: raw.player.team,
      rosterLevel: raw.player.roster_level,
      careerYear: raw.player.career_year,
      form: raw.player.form,
      avatarUrl: raw.player.avatar_url,
    },
    abilities: raw.abilities.map(stat => ({
      key: stat.key,
      label: stat.label,
      rating: stat.rating,
      delta: stat.delta ?? 0,
      trend: adaptTrend(stat.trend),
    })),
    seasonStats: {
      g: raw.season_stats.G,
      pa: raw.season_stats.PA,
      avg: raw.season_stats.AVG,
      obp: raw.season_stats.OBP,
      slg: raw.season_stats.SLG,
      ops: raw.season_stats.OPS,
      hr: raw.season_stats.HR,
      rbi: raw.season_stats.RBI,
      sb: raw.season_stats.SB,
      war: raw.season_stats.WAR,
    },
    recentGames: {
      metric: recentPoints.length ? '최근 경기' : null,
      avg: null,
      hr: null,
      ops: null,
      points: recentPoints,
    },
    status: {
      condition: raw.condition,
      fatigue: raw.fatigue,
      injury: raw.injury,
      form: raw.form,
    },
    traits: raw.traits.map(item => ({
      name: item.name,
      category: item.category,
      tone: adaptTone(item.tone),
    })),
    nextGame: adaptNextGame(raw.next_game),
    seasonStory: raw.season_story
      .map(adaptStory)
      .filter((row): row is StoryEventViewModel => row !== null),
    titleRace,
  }
}

function adaptStanding(raw: Record<string, unknown>): StandingRow | null {
  const rank = finiteNumber(raw.rank)
  const team = nonEmptyString(raw.team)
  const w = firstNumber(raw, ['w', 'W'])
  const l = firstNumber(raw, ['l', 'L'])
  const d = firstNumber(raw, ['d', 'D'])
  const pct = firstNumber(raw, ['pct', 'PCT'])
  if (rank === null || !team || w === null || l === null || d === null || pct === null) return null

  return {
    rank,
    team,
    w,
    l,
    d,
    pct,
    gb: firstString(raw, ['gb', 'GB']) ?? '—',
    streak: nonEmptyString(raw.streak) ?? '—',
    isUserTeam: optionalBoolean(raw.is_user_team ?? raw.isUserTeam),
  }
}

function adaptRecentResult(raw: Record<string, unknown>): RecentResult | null {
  const date = nonEmptyString(raw.date)
  const awayTeam = firstString(raw, ['away_team', 'awayTeam'])
  const homeTeam = firstString(raw, ['home_team', 'homeTeam'])
  const awayScore = firstNumber(raw, ['away_score', 'awayScore'])
  const homeScore = firstNumber(raw, ['home_score', 'homeScore'])
  const gameResult = raw.result
  if (!date || !awayTeam || !homeTeam || awayScore === null || homeScore === null || (gameResult !== 'W' && gameResult !== 'L')) return null

  return {
    date,
    awayTeam,
    awayScore,
    homeScore,
    homeTeam,
    result: gameResult,
    stadium: nonEmptyString(raw.stadium) ?? '',
  }
}

function adaptTeamMetric(raw: Record<string, unknown>): TeamMetric | null {
  const label = nonEmptyString(raw.label)
  const value = nonEmptyString(raw.value)
  const rank = finiteNumber(raw.rank)
  return label && value && rank !== null ? { label, value, rank } : null
}

function adaptLeaderboardMap(raw: Record<string, Record<string, unknown>[]>) {
  return Object.fromEntries(
    Object.entries(raw).map(([metric, rows]) => [
      metric,
      rows.map(adaptLeaderboardEntry).filter((row): row is LeaderboardEntry => row !== null),
    ]),
  )
}

export function adaptSeasonDto(raw: BackendSeasonDto): SeasonViewModel {
  return {
    league: { code: raw.league_code, name: raw.league_name },
    season: adaptProgress(raw.progress, raw.year),
    standings: raw.standings.map(adaptStanding).filter((row): row is StandingRow => row !== null),
    hittingLeaderboards: adaptLeaderboardMap(raw.hitting_leaderboards),
    pitchingLeaderboards: adaptLeaderboardMap(raw.pitching_leaderboards),
    recentResults: raw.recent_results.map(adaptRecentResult).filter((row): row is RecentResult => row !== null),
    teamName: raw.team_name,
    teamBatting: raw.team_batting.map(row => ({
      player: row.player,
      g: row.G,
      pa: row.PA,
      ab: row.AB,
      r: row.R,
      h: row.H,
      doubles: row['2B'],
      triples: row['3B'],
      hr: row.HR,
      rbi: row.RBI,
      sb: row.SB,
      bb: row.BB,
      so: row.SO,
      avg: row.AVG,
      obp: row.OBP,
      slg: row.SLG,
      ops: row.OPS,
      war: row.WAR,
      isUser: row.is_user,
    })),
    teamMetrics: raw.team_metrics.map(adaptTeamMetric).filter((row): row is TeamMetric => row !== null),
  }
}
