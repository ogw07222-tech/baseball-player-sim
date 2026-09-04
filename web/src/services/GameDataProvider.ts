import type { DashboardViewModel, SeasonViewModel } from '../types/viewModels'

export interface GameDataProvider {
  getDashboard(): Promise<DashboardViewModel>
  getSeason(): Promise<SeasonViewModel>
  advanceNextGame(): Promise<DashboardViewModel>
  advanceWeek(): Promise<DashboardViewModel>
  advanceMonth(): Promise<DashboardViewModel>
  advanceSeason(): Promise<DashboardViewModel>
  saveGame(): Promise<void>
}

export type AdvanceCommand = 'nextGame' | 'week' | 'month' | 'season'
