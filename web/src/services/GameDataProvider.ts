import type { DashboardViewModel, SeasonViewModel } from '../types/viewModels'
import type { NewCareerRequest } from '../types/newCareer'
import type {
  BackendAdvanceResultDto,
  BackendDashboardDto,
  BackendSeasonDto,
} from '../types/backendPresentation'
import { adaptDashboardDto, adaptSeasonDto } from './presentationAdapter'

export interface AdvancePresentationResult extends DashboardViewModel {
  advanceResult: BackendAdvanceResultDto
}

export interface BackendAdvancePresentation {
  dashboard: BackendDashboardDto
  result: BackendAdvanceResultDto
}

export interface GameDataProvider {
  hasCareer(): Promise<boolean>
  createCareer(request: NewCareerRequest): Promise<DashboardViewModel>
  getDashboard(): Promise<DashboardViewModel>
  getSeason(): Promise<SeasonViewModel>
  advanceNextGame(): Promise<AdvancePresentationResult>
  advanceWeek(): Promise<AdvancePresentationResult>
  advanceMonth(): Promise<AdvancePresentationResult>
  advanceSeason(): Promise<AdvancePresentationResult>
  saveGame(): Promise<void>
}

export interface BackendPresentationGateway {
  hasCareer(): Promise<boolean>
  createCareer(request: NewCareerRequest): Promise<BackendDashboardDto>
  getDashboard(): Promise<BackendDashboardDto>
  getSeason(): Promise<BackendSeasonDto>
  advanceNextGame(): Promise<BackendAdvancePresentation>
  advanceWeek(): Promise<BackendAdvancePresentation>
  advanceMonth(): Promise<BackendAdvancePresentation>
  advanceSeason(): Promise<BackendAdvancePresentation>
  saveGame(): Promise<void>
}

const adaptAdvance = (payload: BackendAdvancePresentation): AdvancePresentationResult => ({
  ...adaptDashboardDto(payload.dashboard),
  advanceResult: payload.result,
})

export class ProductionPresentationProvider implements GameDataProvider {
  constructor(private readonly gateway: BackendPresentationGateway) {}
  hasCareer() { return this.gateway.hasCareer() }
  async createCareer(request:NewCareerRequest) { return adaptDashboardDto(await this.gateway.createCareer(request)) }
  async getDashboard() { return adaptDashboardDto(await this.gateway.getDashboard()) }
  async getSeason() { return adaptSeasonDto(await this.gateway.getSeason()) }
  async advanceNextGame() { return adaptAdvance(await this.gateway.advanceNextGame()) }
  async advanceWeek() { return adaptAdvance(await this.gateway.advanceWeek()) }
  async advanceMonth() { return adaptAdvance(await this.gateway.advanceMonth()) }
  async advanceSeason() { return adaptAdvance(await this.gateway.advanceSeason()) }
  saveGame() { return this.gateway.saveGame() }
}

export type AdvanceCommand = 'nextGame' | 'week' | 'month' | 'season'
