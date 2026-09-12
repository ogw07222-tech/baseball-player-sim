import type { DashboardViewModel, SeasonViewModel } from '../types/viewModels'
import type { NewCareerRequest } from '../types/newCareer'
import type {
  BackendAdvanceResultDto,
  BackendDashboardDto,
  BackendInteractiveEventDto,
  BackendResolveEventResultDto,
  BackendSeasonDto,
} from '../types/backendPresentation'
import { adaptDashboardDto, adaptSeasonDto } from './presentationAdapter'

export interface AdvancePresentationResult extends DashboardViewModel {
  advanceResult: BackendAdvanceResultDto
  pendingEvents: BackendInteractiveEventDto[]
}

export interface ResolveEventPresentationResult {
  dashboard: DashboardViewModel
  season: SeasonViewModel
  pendingEvents: BackendInteractiveEventDto[]
  result: BackendResolveEventResultDto
}

export interface BackendAdvancePresentation {
  dashboard: BackendDashboardDto
  result: BackendAdvanceResultDto
  pendingEvents: BackendInteractiveEventDto[]
}

export interface BackendResolveEventPresentation {
  dashboard: BackendDashboardDto
  season: BackendSeasonDto
  pendingEvents: BackendInteractiveEventDto[]
  result: BackendResolveEventResultDto
}

export interface GameDataProvider {
  hasCareer(): Promise<boolean>
  createCareer(request: NewCareerRequest): Promise<DashboardViewModel>
  getDashboard(): Promise<DashboardViewModel>
  getSeason(): Promise<SeasonViewModel>
  getPendingEvents(): Promise<BackendInteractiveEventDto[]>
  advanceNextGame(): Promise<AdvancePresentationResult>
  advanceWeek(): Promise<AdvancePresentationResult>
  advanceMonth(): Promise<AdvancePresentationResult>
  advanceSeason(): Promise<AdvancePresentationResult>
  resolveEvent(eventId: string, choiceId: string): Promise<ResolveEventPresentationResult>
  saveGame(): Promise<void>
}

export interface BackendPresentationGateway {
  hasCareer(): Promise<boolean>
  createCareer(request: NewCareerRequest): Promise<BackendDashboardDto>
  getDashboard(): Promise<BackendDashboardDto>
  getSeason(): Promise<BackendSeasonDto>
  getPendingEvents(): Promise<BackendInteractiveEventDto[]>
  advanceNextGame(): Promise<BackendAdvancePresentation>
  advanceWeek(): Promise<BackendAdvancePresentation>
  advanceMonth(): Promise<BackendAdvancePresentation>
  advanceSeason(): Promise<BackendAdvancePresentation>
  resolveEvent(eventId: string, choiceId: string): Promise<BackendResolveEventPresentation>
  saveGame(): Promise<void>
}

const adaptAdvance = (payload: BackendAdvancePresentation): AdvancePresentationResult => ({
  ...adaptDashboardDto(payload.dashboard),
  advanceResult: payload.result,
  pendingEvents: payload.pendingEvents,
})

export class ProductionPresentationProvider implements GameDataProvider {
  constructor(private readonly gateway: BackendPresentationGateway) {}
  hasCareer() { return this.gateway.hasCareer() }
  async createCareer(request:NewCareerRequest) { return adaptDashboardDto(await this.gateway.createCareer(request)) }
  async getDashboard() { return adaptDashboardDto(await this.gateway.getDashboard()) }
  async getSeason() { return adaptSeasonDto(await this.gateway.getSeason()) }
  getPendingEvents() { return this.gateway.getPendingEvents() }
  async advanceNextGame() { return adaptAdvance(await this.gateway.advanceNextGame()) }
  async advanceWeek() { return adaptAdvance(await this.gateway.advanceWeek()) }
  async advanceMonth() { return adaptAdvance(await this.gateway.advanceMonth()) }
  async advanceSeason() { return adaptAdvance(await this.gateway.advanceSeason()) }
  async resolveEvent(eventId:string, choiceId:string): Promise<ResolveEventPresentationResult> {
    const payload = await this.gateway.resolveEvent(eventId, choiceId)
    return {
      dashboard: adaptDashboardDto(payload.dashboard),
      season: adaptSeasonDto(payload.season),
      pendingEvents: payload.pendingEvents,
      result: payload.result,
    }
  }
  saveGame() { return this.gateway.saveGame() }
}

export type AdvanceCommand = 'nextGame' | 'week' | 'month' | 'season'
