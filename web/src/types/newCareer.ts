export type CareerPosition = '1B' | '2B' | '3B' | 'SS' | 'LF' | 'CF' | 'RF'
export type Handedness = 'LEFT' | 'RIGHT'
export type TraitCount = 0 | 1 | 2 | 3

export interface NewCareerRequest {
  name: string
  position: CareerPosition
  bats: Handedness
  throws: Handedness
  traitCount: TraitCount
}
