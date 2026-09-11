import { describe, expect, it } from 'vitest'
import type { BackendDashboardDto, BackendSeasonDto } from '../types/backendPresentation'
import { adaptDashboardDto, adaptSeasonDto } from './presentationAdapter'

const progress = { year:2029, game:47, games_completed:47, total_games:144, current_date:'2029-05-25', progress:33 }

const dashboardDto: BackendDashboardDto = {
  player: {
    name: '김건우', age: 22, position: 'SS', bats_throws: 'R/L', team: '키움 히어로즈', roster_level: 'FIRST', form: 'hot',
    number: null, career_year: 3, avatar_url: null,
  },
  abilities: [{ key:'contact', label:'컨택', rating:112, delta:0, trend:'flat' }],
  season_stats: { G:47, PA:198, AVG:.312, OBP:.382, SLG:.506, OPS:.888, HR:19, RBI:61, SB:14, WAR:null },
  condition: 'unknown', fatigue:34, injury:null, form:'hot', traits:[], league_code:'KBO', league_name:'KBO League',
  recent_games:[], next_game:null, season_story:[], title_race:{}, progress,
}

const seasonDto: BackendSeasonDto = {
  year:2029, league_code:'KBO', league_name:'KBO League', standings:[], hitting_leaderboards:{}, pitching_leaderboards:{}, recent_results:[],
  team_name:'키움 히어로즈', team_batting:[{ player:'김건우', G:47, PA:198, AB:176, R:28, H:55, '2B':12, '3B':1, HR:19, RBI:61, SB:14, BB:18, SO:32, AVG:.312, OBP:.382, SLG:.506, OPS:.888, WAR:null, is_user:true }],
  team_metrics:[], progress,
}

describe('production presentation adapter',()=>{
  it('preserves nullable backend values instead of fabricating display data',()=>{
    const dashboard = adaptDashboardDto(dashboardDto)
    expect(dashboard.player.number).toBeNull()
    expect(dashboard.seasonStats.war).toBeNull()
    expect(dashboard.nextGame).toBeNull()
    expect(dashboard.recentGames.points).toEqual([])
    expect(dashboard.recentGames.avg).toBeNull()
    expect(dashboard.status.condition).toBe('unknown')
    expect(dashboard.season.game).toBe(47)
    expect(dashboard.season.totalGames).toBe(144)
    expect(dashboard.season.progress).toBe(33)
    expect(dashboard.season.date).toBe('2029-05-25')
  })

  it('maps the production SeasonService uppercase stat contract exactly',()=>{
    const season = adaptSeasonDto(seasonDto)
    expect(season.season.year).toBe(2029)
    expect(season.teamBatting).toHaveLength(1)
    expect(season.teamBatting[0]).toMatchObject({ player:'김건우', g:47, pa:198, ab:176, doubles:12, triples:1, hr:19, war:null, isUser:true })
    expect(season.standings).toEqual([])
  })
})
