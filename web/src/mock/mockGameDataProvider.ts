import type { GameDataProvider } from '../services/GameDataProvider'
import type { NewCareerRequest } from '../types/newCareer'
import type { DashboardViewModel, LeaderboardEntry, SeasonViewModel, TeamBattingRow, TraitViewModel } from '../types/viewModels'

const teams = ['LG 트윈스','KIA 타이거즈','삼성 라이온즈','SSG 랜더스','두산 베어스','KT 위즈','한화 이글스','롯데 자이언츠','NC 다이노스','키움 히어로즈']

const leaderboard = (metric: string): LeaderboardEntry[] => {
  const names = ['최준호','김도영','구자욱','박성진','문보경','노시환','김건우','문동희','강백호','박민우']
  return names.map((player, index) => ({
    rank: index + 1,
    player,
    team: teams[index % teams.length],
    value: metric === 'HR' ? 38 - index * 2 : metric === 'WAR' ? 5.7 - index * 0.25 : .342 - index * .004,
    display: metric === 'HR' ? String(38 - index * 2) : metric === 'WAR' ? (5.7 - index * .25).toFixed(1) : (0.342 - index * .004).toFixed(3).replace(/^0/, ''),
    isUser: player === '김건우',
  }))
}

const pitching = (metric: string): LeaderboardEntry[] => {
  const names = ['김윤식','원태인','에레디아','곽빈','양현종','고영표','류현진','신민혁','박세웅','하영민']
  return names.map((player, index) => ({
    rank: index + 1,
    player,
    team: teams[index % teams.length],
    value: metric === 'ERA' ? 2.31 + index * .1 : 12 - index,
    display: metric === 'ERA' ? (2.31 + index * .1).toFixed(2) : String(12 - index),
  }))
}

const teamBatting: TeamBattingRow[] = [
  ['김건우',47,198,176,28,55,12,1,19,61,14,18,32,.312,.382,.506,.888,3.2,true],
  ['이주형',52,214,196,25,58,10,2,6,27,4,13,41,.296,.340,.459,.799,2.1,false],
  ['송성문',50,208,187,27,52,9,3,8,32,6,19,38,.278,.356,.486,.842,2.4,false],
  ['최주환',46,180,163,18,41,8,0,5,24,1,14,36,.252,.311,.393,.704,1.1,false],
  ['김혜성',44,176,159,22,47,6,2,4,20,12,15,29,.296,.361,.434,.795,2.0,false],
  ['이형종',41,162,148,17,36,7,1,5,21,2,11,40,.243,.302,.405,.707,.8,false],
  ['김동헌',38,121,105,12,24,5,0,2,14,3,12,33,.229,.310,.333,.643,.6,false],
  ['박수종',33,98,91,11,22,4,1,1,9,5,6,27,.242,.286,.341,.627,.4,false],
].map(([player,g,pa,ab,r,h,doubles,triples,hr,rbi,sb,bb,so,avg,obp,slg,ops,war,isUser]) => ({ player: String(player), g:Number(g), pa:Number(pa), ab:Number(ab), r:Number(r), h:Number(h), doubles:Number(doubles), triples:Number(triples), hr:Number(hr), rbi:Number(rbi), sb:Number(sb), bb:Number(bb), so:Number(so), avg:Number(avg), obp:Number(obp), slg:Number(slg), ops:Number(ops), war:Number(war), isUser:Boolean(isUser) }))

const dashboard: DashboardViewModel = {
  league: { code: 'KBO', name: 'KBO League' },
  season: { year: 2029, game: 47, totalGames: 144, date: '2029년 5월 20일 (월)', progress: 32 },
  player: { name: '김건우', number: 7, age: 22, position: 'SS', batsThrows: 'R/L', team: '키움 히어로즈', rosterLevel: '1군', careerYear: 3, form: 'HOT' },
  abilities: [
    ['contact','컨택',112,2],['power','파워',137,4],['discipline','선구안',98,0],['speed','주력',89,-2],['defense','수비',121,1],['throwing','송구',118,0],['stamina','체력',115,0],['durability','내구성',82,-1],['mentality','멘탈',110,2],['talent','재능',125,0],
  ].map(([key,label,rating,delta]) => ({ key:String(key), label:String(label), rating:Number(rating), delta:Number(delta), trend:Number(delta)>0?'up':Number(delta)<0?'down':'flat' } as const)),
  seasonStats: { g:47, pa:198, avg:.312, obp:.382, slg:.506, ops:.888, hr:19, rbi:61, sb:14, war:3.2 },
  recentGames: {
    metric: 'Game AVG', avg:.341, hr:3, ops:1.021,
    points: [.320,.305,.410,.315,.420,.325,.405,.470,.390,.310].map((value,index) => ({ label:`5/${10+index}`, value, outcome:['H','2B','K','HR','BB','H','H','K','1B','H'][index] })),
  },
  status: { condition:'좋음', fatigue:34, injury:'없음', form:'HOT' },
  traits: [
    { name:'클러치', category:'performance', tone:'positive' },
    { name:'직구 특화', category:'pitch', tone:'positive' },
    { name:'꾸준함', category:'mental', tone:'positive' },
    { name:'변화구 취약', category:'pitch', tone:'negative' },
  ],
  nextGame: { homeTeam:'LG 트윈스', awayTeam:'키움 히어로즈', homeRank:1, awayRank:3, homeRecord:'32-15', awayRecord:'28-18', date:'5월 21일 (화)', time:'18:30', stadium:'고척스카이돔', opposingStarter:'김윤식', throwingHand:'LHP', era:3.21, homeAway:'HOME', expectedLineupSpot:2 },
  seasonStory: [
    { date:'5/18', title:'3경기 연속 홈런', detail:'팀의 4연승을 이끄는 결승 홈런', category:'PERFORMANCE' },
    { date:'5/12', title:'파워 +2', detail:'타격 훈련의 효과가 나타나고 있습니다.', category:'TRAINING' },
    { date:'5/03', title:'타격코치와 면담', detail:'새로운 스윙 메커니즘에 대한 논의.', category:'NORMAL' },
    { date:'4/24', title:'타격폼 일부 수정', detail:'적응 기간이 필요해 보입니다.', category:'TRAINING' },
    { date:'4/03', title:'2029 시즌 개막', detail:'올 시즌, 더 높은 목표를 향해.', category:'MAJOR' },
  ],
  titleRace: { AVG: leaderboard('AVG'), HR: leaderboard('HR'), OPS: leaderboard('AVG'), WAR: leaderboard('WAR') },
}

const season: SeasonViewModel = {
  league: dashboard.league,
  season: dashboard.season,
  standings: teams.map((team,index) => ({ rank:index+1, team, w:68-index*3- (index>6?2:0), l:44+index*3, d:2, pct:Number((.607-index*.029).toFixed(3)), gb:index===0?'-':(index*3).toFixed(1), streak:['4승','2승','1패','1승','3승','1패','2패','1승','4패','2패'][index], isUserTeam:team==='키움 히어로즈' })),
  hittingLeaderboards: { AVG:leaderboard('AVG'), HR:leaderboard('HR'), RBI:leaderboard('HR'), H:leaderboard('HR'), OBP:leaderboard('AVG'), SLG:leaderboard('AVG'), OPS:leaderboard('AVG'), WAR:leaderboard('WAR') },
  pitchingLeaderboards: { ERA:pitching('ERA'), W:pitching('W'), K:pitching('K'), SV:pitching('SV'), WHIP:pitching('ERA') },
  recentResults: [
    { date:'5/20', awayTeam:'키움', awayScore:3, homeScore:5, homeTeam:'LG', result:'L', stadium:'고척스카이돔' },
    { date:'5/19', awayTeam:'키움', awayScore:6, homeScore:4, homeTeam:'KIA', result:'W', stadium:'고척스카이돔' },
    { date:'5/18', awayTeam:'KIA', awayScore:4, homeScore:2, homeTeam:'키움', result:'W', stadium:'고척스카이돔' },
    { date:'5/17', awayTeam:'한화', awayScore:5, homeScore:1, homeTeam:'키움', result:'L', stadium:'대전 한화생명 이글스파크' },
    { date:'5/16', awayTeam:'한화', awayScore:3, homeScore:7, homeTeam:'키움', result:'W', stadium:'대전 한화생명 이글스파크' },
  ],
  teamName:'키움 히어로즈',
  teamBatting,
  teamMetrics: [
    {label:'팀 타율',value:'.259',rank:9},{label:'팀 OPS',value:'.721',rank:9},{label:'팀 홈런',value:'82',rank:8},{label:'팀 타점',value:'410',rank:9},{label:'팀 도루',value:'62',rank:7},{label:'팀 ERA',value:'4.92',rank:10},{label:'팀 WHIP',value:'1.48',rank:10},{label:'팀 탈삼진',value:'1,012',rank:8},{label:'팀 세이브',value:'28',rank:9},{label:'팀 수비 WAR',value:'-4.1',rank:10},
  ],
}

const traitPool: TraitViewModel[] = [
  {name:'클러치',category:'performance',tone:'positive'},
  {name:'꾸준함',category:'mental',tone:'positive'},
  {name:'직구 특화',category:'pitch',tone:'positive'},
  {name:'빠른 적응',category:'growth',tone:'positive'},
  {name:'변화구 취약',category:'pitch',tone:'negative'},
  {name:'기복',category:'mental',tone:'negative'},
  {name:'슬로 스타터',category:'performance',tone:'negative'},
  {name:'침착함',category:'mental',tone:'neutral'},
]

const clone = <T>(value:T):T => structuredClone(value)
const handCode = (value:'LEFT'|'RIGHT') => value === 'LEFT' ? 'L' : 'R'
const seedFor = (request:NewCareerRequest) => Array.from(`${request.name}|${request.position}|${request.bats}|${request.throws}|${request.traitCount}`).reduce((seed,ch)=>((seed*31)+ch.charCodeAt(0))>>>0,2166136261)
const nextRandom = (state:{value:number}) => { state.value = (1664525*state.value+1013904223)>>>0; return state.value/4294967296 }

function generatedAbilities(request:NewCareerRequest) {
  const state = {value:seedFor(request)}
  const specs = [['contact','컨택'],['power','파워'],['discipline','선구안'],['speed','주력'],['defense','수비'],['throwing','송구'],['stamina','체력'],['durability','내구성'],['mentality','멘탈']] as const
  const abilities = specs.map(([key,label])=>{
    const rating = Math.max(45,Math.min(120,Math.round(80+(nextRandom(state)-.5)*40+(nextRandom(state)-.5)*18)))
    return {key,label,rating,delta:0,trend:'flat' as const}
  })
  const talent = Math.round(75+nextRandom(state)*65)
  return [...abilities,{key:'talent',label:'재능',rating:talent,delta:0,trend:'flat' as const}]
}

function generatedTraits(request:NewCareerRequest) {
  const state = {value:seedFor(request)^0x9e3779b9}
  const pool = clone(traitPool)
  const result:TraitViewModel[] = []
  while(result.length<request.traitCount && pool.length){ const index=Math.floor(nextRandom(state)*pool.length); result.push(pool.splice(index,1)[0]) }
  return result
}

export class MockGameDataProvider implements GameDataProvider {
  private careerExists:boolean
  private dashboardState:DashboardViewModel
  private seasonState:SeasonViewModel

  constructor(options:{hasCareer?:boolean}={}) {
    this.careerExists = options.hasCareer ?? false
    this.dashboardState = clone(dashboard)
    this.seasonState = clone(season)
  }

  async hasCareer() { return this.careerExists }

  async createCareer(request:NewCareerRequest) {
    const abilities = generatedAbilities(request)
    const traits = generatedTraits(request)
    this.dashboardState = clone(dashboard)
    this.dashboardState.league = {code:'HS',name:'High School Baseball'}
    this.dashboardState.season = {year:2026,game:0,totalGames:20,date:'2026년 고교 시즌 개막 전',progress:0}
    this.dashboardState.player = {name:request.name,number:7,age:18,position:request.position,batsThrows:`${handCode(request.bats)}/${handCode(request.throws)}`,team:'고교 유망주',rosterLevel:'고교',careerYear:1,form:'NORMAL'}
    this.dashboardState.abilities = abilities
    this.dashboardState.traits = traits
    this.dashboardState.seasonStats = {g:0,pa:0,avg:0,obp:0,slg:0,ops:0,hr:0,rbi:0,sb:0,war:0}
    this.dashboardState.recentGames = {metric:'Game AVG',avg:0,hr:0,ops:0,points:[]}
    this.dashboardState.status = {condition:'좋음',fatigue:0,injury:'없음',form:'NORMAL'}
    this.dashboardState.seasonStory = [{date:'DAY 1',title:'새 커리어 시작',detail:'고교 야구 선수로 첫 시즌을 준비합니다.',category:'MAJOR'}]
    Object.values(this.dashboardState.titleRace).forEach(rows=>rows.forEach(row=>{if(row.isUser) row.player=request.name}))

    this.seasonState = clone(season)
    this.seasonState.league = clone(this.dashboardState.league)
    this.seasonState.season = clone(this.dashboardState.season)
    this.seasonState.teamBatting = this.seasonState.teamBatting.map(row=>row.isUser?{...row,player:request.name,g:0,pa:0,ab:0,r:0,h:0,doubles:0,triples:0,hr:0,rbi:0,sb:0,bb:0,so:0,avg:0,obp:0,slg:0,ops:0,war:0}:row)
    Object.values(this.seasonState.hittingLeaderboards).forEach(rows=>rows.forEach(row=>{if(row.isUser) row.player=request.name}))
    this.careerExists = true
    return clone(this.dashboardState)
  }

  async getDashboard() { return clone(this.dashboardState) }
  async getSeason() { return clone(this.seasonState) }
  async advanceNextGame() { return this.advance(1) }
  async advanceWeek() { return this.advance(6) }
  async advanceMonth() { return this.advance(24) }
  async advanceSeason() {
    const totalGames = this.dashboardState.season.totalGames ?? 0
    const game = this.dashboardState.season.game ?? 0
    return this.advance(Math.max(0, totalGames - game))
  }
  async saveGame() { await Promise.resolve() }
  private async advance(games:number) {
    const next = clone(this.dashboardState)
    const currentGame = next.season.game ?? 0
    const totalGames = next.season.totalGames ?? currentGame
    next.season.game = Math.min(totalGames, currentGame + games)
    next.season.progress = totalGames > 0 ? Math.round((next.season.game / totalGames) * 100) : 0
    this.dashboardState = clone(next)
    this.seasonState.season = clone(next.season)
    return next
  }
}
