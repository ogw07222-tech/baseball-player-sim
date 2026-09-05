import type { DashboardViewModel, SeasonViewModel } from '../types/viewModels'
import type { NewCareerRequest } from '../types/newCareer'

export interface GameDataProvider {
  hasCareer(): Promise<boolean>
  createCareer(request: NewCareerRequest): Promise<DashboardViewModel>
  getDashboard(): Promise<DashboardViewModel>
  getSeason(): Promise<SeasonViewModel>
  advanceNextGame(): Promise<DashboardViewModel>
  advanceWeek(): Promise<DashboardViewModel>
  advanceMonth(): Promise<DashboardViewModel>
  advanceSeason(): Promise<DashboardViewModel>
  saveGame(): Promise<void>
}

export type AdvanceCommand = 'nextGame' | 'week' | 'month' | 'season'
