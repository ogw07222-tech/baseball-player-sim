import type { DashboardViewModel, SeasonViewModel } from '../types/viewModels'
import type { NewCareerRequest } from '../types/newCareer'
import type { BackendDashboardDto, BackendSeasonDto } from '../types/backendPresentation'
import { adaptDashboardDto, adaptSeasonDto } from './presentationAdapter'

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

export interface BackendPresentationGateway {
  hasCareer(): Promise<boolean>
  createCareer(request: NewCareerRequest): Promise<BackendDashboardDto>
  getDashboard(): Promise<BackendDashboardDto>
  getSeason(): Promise<BackendSeasonDto>
  advanceNextGame(): Promise<BackendDashboardDto>
  advanceWeek(): Promise<BackendDashboardDto>
  advanceMonth(): Promise<BackendDashboardDto>
  advanceSeason(): Promise<BackendDashboardDto>
  saveGame(): Promise<void>
}

export class ProductionPresentationProvider implements GameDataProvider {
  constructor(private readonly gateway: BackendPresentationGateway) {}
  hasCareer() { return this.gateway.hasCareer() }
  async createCareer(request:NewCareerRequest) { return adaptDashboardDto(await this.gateway.createCareer(request)) }
  async getDashboard() { return adaptDashboardDto(await this.gateway.getDashboard()) }
  async getSeason() { return adaptSeasonDto(await this.gateway.getSeason()) }
  async advanceNextGame() { return adaptDashboardDto(await this.gateway.advanceNextGame()) }
  async advanceWeek() { return adaptDashboardDto(await this.gateway.advanceWeek()) }
  async advanceMonth() { return adaptDashboardDto(await this.gateway.advanceMonth()) }
  async advanceSeason() { return adaptDashboardDto(await this.gateway.advanceSeason()) }
  saveGame() { return this.gateway.saveGame() }
}

export type AdvanceCommand = 'nextGame' | 'week' | 'month' | 'season'
