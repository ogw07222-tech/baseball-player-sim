export type DraftStatus = 'ON_THE_CLOCK' | 'WAITING' | 'SELECTED' | 'UNDRAFTED'

export interface DraftPlayerViewModel {
  name: string
  school: string
  schoolEn: string
  position: string
  batsThrows: string
  age: number
  avg: number
  obp: number
  slg: number
  ops: number
  performanceScore: number
  nationalRank: number
  positionRank: string
  scoutedGrade: string
}

export interface HighSchoolResumeItem { tournament:string; result:string }
export interface ProjectionRow { label:string; value:string; tone?:'positive'|'warning'|'neutral' }
export interface TeamFitRow { label:string; value:'HIGH'|'MEDIUM'|'LOW'; percent:number }
export interface DraftBoardRow { pick:number; team:string; player:string; pos:string; school:string; grade:string; selected?:boolean }
export interface DraftFeedRow { round:string; pick:number; player:string; pos:string; school:string; team:string }
export interface RoundProgressRow { round:number; status:'COMPLETE'|'CURRENT'|'NEXT'; progress?:string }

export interface DraftDayViewModel {
  year: number
  draftStatus: DraftStatus
  player: DraftPlayerViewModel
  finalHighSchoolResume: HighSchoolResumeItem[]
  resumeFooter: { ops:number; hr:number; sb:number }
  selectedTeam: { name:string; shortName:string; crestLetter:string }
  draftResult: { round:number; overallPick:number; playerType:string; contractStatus:string }
  preDraftProjection: ProjectionRow[]
  teamFit: TeamFitRow[]
  draftBoard: DraftBoardRow[]
  fullDraftBoard: DraftBoardRow[]
  draftFeed: DraftFeedRow[]
  roundProgress: RoundProgressRow[]
}
