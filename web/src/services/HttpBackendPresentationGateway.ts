import type {
  BackendErrorEnvelopeDto,
  BackendSessionDto,
  BackendSnapshotDto,
} from '../types/backendPresentation'
import type { NewCareerRequest } from '../types/newCareer'
import type {
  BackendAdvancePresentation,
  BackendPresentationGateway,
  BackendResolveEventPresentation,
} from './GameDataProvider'

export class BackendTransportError extends Error {
  constructor(
    readonly status: number,
    readonly code: string,
    message: string,
    readonly retryable: boolean,
    readonly revision: number | null,
    readonly details: unknown = null,
  ) {
    super(message)
    this.name = 'BackendTransportError'
  }
}

export class HttpBackendPresentationGateway implements BackendPresentationGateway {
  private revision: number | null = null
  private inflightState: Promise<BackendSnapshotDto> | null = null
  private postMutationSnapshot: BackendSnapshotDto | null = null

  constructor(
    private readonly baseUrl = '/api/v1',
    private readonly idempotencyKeyFactory: () => string = () => crypto.randomUUID(),
  ) {}

  private async json<T>(path: string, init?: RequestInit): Promise<T> {
    let response: Response
    try {
      response = await fetch(`${this.baseUrl}${path}`, {
        credentials: 'same-origin',
        headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) },
        ...init,
      })
    } catch {
      throw new BackendTransportError(
        0,
        'NETWORK_ERROR',
        'backend network request failed',
        true,
        this.revision,
      )
    }
    if (!response.ok) {
      let payload: BackendErrorEnvelopeDto = {}
      try { payload = await response.json() as BackendErrorEnvelopeDto } catch { /* non-JSON fallback */ }
      throw new BackendTransportError(
        response.status,
        payload.error?.code ?? 'INTERNAL_ERROR',
        payload.error?.message ?? `backend request failed (${response.status})`,
        payload.error?.retryable ?? false,
        payload.meta?.revision ?? null,
        payload.error?.details ?? null,
      )
    }
    if (response.status === 204) return undefined as T
    return await response.json() as T
  }

  private remember(snapshot: BackendSnapshotDto) {
    this.revision = snapshot.meta.revision
    this.postMutationSnapshot = snapshot
    return snapshot
  }

  private loadState(): Promise<BackendSnapshotDto> {
    if (!this.inflightState) {
      this.inflightState = this.json<BackendSnapshotDto>('/state')
        .then(snapshot => {
          this.revision = snapshot.meta.revision
          return snapshot
        })
        .finally(() => { this.inflightState = null })
    }
    return this.inflightState
  }

  private async postMutation(path: string, body: string): Promise<BackendSnapshotDto> {
    for (let attempt = 0; attempt < 2; attempt += 1) {
      try {
        return await this.json<BackendSnapshotDto>(path, { method: 'POST', body })
      } catch (error) {
        const retryable = error instanceof BackendTransportError && error.retryable
        if (attempt === 0 && retryable) continue
        throw error
      }
    }
    throw new Error('unreachable mutation retry state')
  }

  private async requireRevision() {
    if (this.revision === null) {
      const snapshot = await this.loadState()
      this.revision = snapshot.meta.revision
    }
    if (this.revision === null) {
      throw new BackendTransportError(
        409,
        'NO_REVISION',
        'cannot mutate without a backend revision',
        false,
        null,
      )
    }
    return this.revision
  }

  async hasCareer() {
    const session = await this.json<BackendSessionDto>('/session')
    this.revision = session.revision
    if (!session.has_career) this.postMutationSnapshot = null
    return session.has_career
  }

  async createCareer(request: NewCareerRequest) {
    const snapshot = this.remember(await this.json<BackendSnapshotDto>('/career', {
      method: 'POST',
      body: JSON.stringify(request),
    }))
    return snapshot.data.dashboard
  }

  async getDashboard() {
    const snapshot = this.postMutationSnapshot ?? await this.loadState()
    return snapshot.data.dashboard
  }

  async getPendingEvents() {
    const snapshot = this.postMutationSnapshot ?? await this.loadState()
    return snapshot.data.pending_events ?? []
  }

  async getSeason() {
    const snapshot = this.postMutationSnapshot ?? await this.loadState()
    if (this.postMutationSnapshot === snapshot) this.postMutationSnapshot = null
    return snapshot.data.season
  }

  private requireAdvanceMutation(snapshot: BackendSnapshotDto): BackendAdvancePresentation {
    if (!snapshot.mutation || snapshot.mutation.kind !== 'advance') {
      throw new BackendTransportError(
        502,
        'INVALID_RESPONSE',
        'advance response is missing mutation result',
        false,
        snapshot.meta.revision,
      )
    }
    return {
      dashboard: snapshot.data.dashboard,
      result: snapshot.mutation.result,
      pendingEvents: snapshot.data.pending_events ?? snapshot.mutation.result.pending_events ?? [],
    }
  }

  private async advance(command: 'next_game' | 'week' | 'month' | 'season') {
    const expectedRevision = await this.requireRevision()
    const body = JSON.stringify({
      command,
      expected_revision: expectedRevision,
      idempotency_key: this.idempotencyKeyFactory(),
    })
    const snapshot = this.remember(await this.postMutation('/advance', body))
    return this.requireAdvanceMutation(snapshot)
  }

  advanceNextGame() { return this.advance('next_game') }
  advanceWeek() { return this.advance('week') }
  advanceMonth() { return this.advance('month') }
  advanceSeason() { return this.advance('season') }

  async resolveEvent(eventId: string, choiceId: string): Promise<BackendResolveEventPresentation> {
    const expectedRevision = await this.requireRevision()
    const body = JSON.stringify({
      choice_id: choiceId,
      expected_revision: expectedRevision,
      idempotency_key: this.idempotencyKeyFactory(),
    })
    const snapshot = this.remember(await this.postMutation(`/events/${encodeURIComponent(eventId)}/resolve`, body))
    if (!snapshot.mutation || snapshot.mutation.kind !== 'resolve_event') {
      throw new BackendTransportError(
        502,
        'INVALID_RESPONSE',
        'event resolve response is missing mutation result',
        false,
        snapshot.meta.revision,
      )
    }
    return {
      dashboard: snapshot.data.dashboard,
      season: snapshot.data.season,
      pendingEvents: snapshot.data.pending_events ?? snapshot.mutation.result.pending_events ?? [],
      result: snapshot.mutation.result,
    }
  }

  async saveGame() {
    if (this.revision === null) return
    await this.json<void>('/save', {
      method: 'POST',
      body: JSON.stringify({ expected_revision: this.revision }),
    })
  }
}
