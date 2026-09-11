import type { BackendDashboardDto, BackendSeasonDto } from '../types/backendPresentation'
import type { NewCareerRequest } from '../types/newCareer'
import type { BackendPresentationGateway } from './GameDataProvider'

type Snapshot = {
  data: { dashboard: BackendDashboardDto; season: BackendSeasonDto }
  meta: { revision: number }
}

type ErrorPayload = {
  error?: { code?: string; message?: string; retryable?: boolean; details?: unknown }
  meta?: { revision?: number | null }
}

export class BackendTransportError extends Error {
  constructor(
    readonly status: number,
    readonly code: string,
    message: string,
    readonly retryable: boolean,
    readonly revision: number | null,
  ) {
    super(message)
    this.name = 'BackendTransportError'
  }
}

export class HttpBackendPresentationGateway implements BackendPresentationGateway {
  private revision: number | null = null
  private inflightState: Promise<Snapshot> | null = null
  private postMutationSnapshot: Snapshot | null = null

  constructor(private readonly baseUrl = '/api/v1') {}

  private async json<T>(path: string, init?: RequestInit): Promise<T> {
    let response: Response
    try {
      response = await fetch(`${this.baseUrl}${path}`, {
        credentials: 'same-origin',
        headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) },
        ...init,
      })
    } catch {
      throw new BackendTransportError(0, 'NETWORK_ERROR', 'backend network request failed', true, this.revision)
    }
    if (!response.ok) {
      let payload: ErrorPayload = {}
      try { payload = await response.json() as ErrorPayload } catch { /* non-JSON fallback */ }
      throw new BackendTransportError(
        response.status,
        payload.error?.code ?? 'INTERNAL_ERROR',
        payload.error?.message ?? `backend request failed (${response.status})`,
        payload.error?.retryable ?? false,
        payload.meta?.revision ?? null,
      )
    }
    if (response.status === 204) return undefined as T
    return await response.json() as T
  }

  private remember(snapshot: Snapshot) {
    this.revision = snapshot.meta.revision
    this.postMutationSnapshot = snapshot
    return snapshot
  }

  private loadState(): Promise<Snapshot> {
    if (!this.inflightState) {
      this.inflightState = this.json<Snapshot>('/state')
        .then(snapshot => {
          this.revision = snapshot.meta.revision
          return snapshot
        })
        .finally(() => { this.inflightState = null })
    }
    return this.inflightState
  }

  async hasCareer() {
    const session = await this.json<{ has_career: boolean; revision: number | null }>('/session')
    this.revision = session.revision
    if (!session.has_career) this.postMutationSnapshot = null
    return session.has_career
  }

  async createCareer(request: NewCareerRequest) {
    const snapshot = this.remember(await this.json<Snapshot>('/career', {
      method: 'POST',
      body: JSON.stringify(request),
    }))
    return snapshot.data.dashboard
  }

  async getDashboard() {
    const snapshot = this.postMutationSnapshot ?? await this.loadState()
    return snapshot.data.dashboard
  }

  async getSeason() {
    const snapshot = this.postMutationSnapshot ?? await this.loadState()
    if (this.postMutationSnapshot === snapshot) this.postMutationSnapshot = null
    return snapshot.data.season
  }

  private async advance(command: 'next_game' | 'week' | 'month' | 'season') {
    if (this.revision === null) {
      const snapshot = await this.loadState()
      this.revision = snapshot.meta.revision
    }
    const expectedRevision = this.revision
    if (expectedRevision === null) throw new BackendTransportError(409, 'NO_REVISION', 'cannot advance without a backend revision', false, null)
    const snapshot = this.remember(await this.json<Snapshot>('/advance', {
      method: 'POST',
      body: JSON.stringify({
        command,
        expected_revision: expectedRevision,
        idempotency_key: crypto.randomUUID(),
      }),
    }))
    return snapshot.data.dashboard
  }

  advanceNextGame() { return this.advance('next_game') }
  advanceWeek() { return this.advance('week') }
  advanceMonth() { return this.advance('month') }
  advanceSeason() { return this.advance('season') }

  async saveGame() {
    if (this.revision === null) return
    await this.json<void>('/save', {
      method: 'POST',
      body: JSON.stringify({ expected_revision: this.revision }),
    })
  }
}
