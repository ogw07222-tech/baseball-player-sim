import type { HighSchoolHubViewModel } from '../types/highSchool'

export const highSchoolCareerMock: HighSchoolHubViewModel = {
  seasonLabel: '2026 HIGH SCHOOL SEASON',
  player: {
    name: '김도윤', school: '서울 한빛고등학교', schoolEnglish: 'HANBIT HIGH SCHOOL', position: 'SS', batsThrows: 'R / R', age: 18, yearLabel: '고3', scoutedGrade: 'A-', condition: 'GOOD', seasonGrowth: 3,
  },
  currentTournament: {
    name: '황금사자기', subtitle: '전국고교야구대회', stage: 'ROUND OF 16', homeTeam: '서울 한빛고', awayTeam: '부산 해원고', date: '2026.05.19', time: '14:00', stadium: '목동야구장',
    bracket: [
      { id:'m1', round:'32강', top:{id:'hanbit',name:'서울 한빛고',score:5,state:'player'}, bottom:{id:'cheongmyeong',name:'대구 청명고',score:3,state:'eliminated'}, winnerId:'hanbit' },
      { id:'m2', round:'32강', top:{id:'haewon',name:'부산 해원고',score:4,state:'opponent'}, bottom:{id:'segwang',name:'광주 세광고',score:2,state:'eliminated'}, winnerId:'haewon' },
      { id:'m3', round:'32강', top:{id:'jungang',name:'대전 중앙고',score:6,state:'neutral'}, bottom:{id:'seongnam',name:'인천 성남고',score:1,state:'eliminated'}, winnerId:'jungang' },
      { id:'m4', round:'32강', top:{id:'dongwon',name:'경기 동원고',score:3,state:'neutral'}, bottom:{id:'younggwang',name:'서울 영광고',score:2,state:'eliminated'}, winnerId:'dongwon' },
      { id:'m5', round:'16강', top:{id:'hanbit',name:'서울 한빛고',state:'player'}, bottom:{id:'haewon',name:'부산 해원고',state:'opponent'}, isCurrent:true },
      { id:'m6', round:'16강', top:{id:'jungang',name:'대전 중앙고',state:'neutral'}, bottom:{id:'dongwon',name:'경기 동원고',state:'neutral'} },
      { id:'m7', round:'8강', top:{id:'future1',name:'?',state:'future'}, bottom:{id:'future2',name:'?',state:'future'} },
    ],
  },
  seasonTournaments: [
    {name:'청룡기',status:'8강 탈락',state:'ELIMINATED'},
    {name:'황금사자기',status:'16강 진행중',state:'ACTIVE'},
    {name:'대통령배',status:'예정',note:'7월',state:'UPCOMING'},
    {name:'봉황대기',status:'예정',note:'8월',state:'UPCOMING'},
  ],
  performance: {avg:.342,obp:.421,slg:.557,ops:.978,hr:4,bb:11,so:8,sb:6},
  prospectEvaluation: {performanceScore:132,nationalRank:14,positionRank:3,percentile:98.2,projectedRange:'2–3 ROUND'},
  draftStock: {direction:'RISING',delta:8,span:'최근 10경기 기준',projection:'2–3 ROUND',trend:[101,104,103,108,110,114,118,120,126,132]},
  development: [
    {key:'contact',label:'Contact',rating:87,change:2}, {key:'power',label:'Power',rating:79,change:1}, {key:'discipline',label:'Discipline',rating:83,change:1}, {key:'speed',label:'Speed',rating:91,change:0}, {key:'defense',label:'Defense',rating:89,change:1}, {key:'resilience',label:'Resilience',rating:78,change:0},
  ],
  recentGames: [
    {date:'5/15',tournament:'황금사자기',opponent:'대구 청명고',result:'W 4–2',outcome:'W',line:'1 HR / 2 RBI'},
    {date:'5/12',tournament:'황금사자기',opponent:'대전 중앙고',result:'L 1–3',outcome:'L',line:'1 BB / 1 SB'},
    {date:'5/10',tournament:'황금사자기',opponent:'인천 성남고',result:'W 5–3',outcome:'W',line:'2B / 1 RBI'},
    {date:'5/07',tournament:'서울권 예선',opponent:'경기 동산고',result:'W 4–1',outcome:'W',line:'2 H / 1 SB'},
    {date:'5/04',tournament:'서울권 예선',opponent:'서울 영광고',result:'W 3–2',outcome:'W',line:'1 HR / 3 RBI'},
  ],
  careerNews: [
    {date:'5/16',headline:'김도윤, 황금사자기 16강 진출 견인'},
    {date:'5/13',headline:'스카우트 평가 상승… 유격수 전국 랭킹 3위 진입'},
    {date:'5/11',headline:'최근 5경기 OPS 1.124'},
    {date:'5/05',headline:'서울권 예선 MVP 선정'},
    {date:'4/28',headline:'“수비에서 확실한 존재감” — 스카우트 리포트'},
  ],
  fullBracket: [
    {round:'32강',games:[
      {a:'서울 한빛고',aScore:5,b:'대구 청명고',bScore:3,winner:'서울 한빛고'},
      {a:'부산 해원고',aScore:4,b:'광주 세광고',bScore:2,winner:'부산 해원고'},
      {a:'대전 중앙고',aScore:6,b:'인천 성남고',bScore:1,winner:'대전 중앙고'},
      {a:'경기 동원고',aScore:3,b:'서울 영광고',bScore:2,winner:'경기 동원고'},
      {a:'전주 상산고',aScore:7,b:'제주 중앙고',bScore:1,winner:'전주 상산고'},
      {a:'울산 해성고',aScore:2,b:'춘천 북일고',bScore:1,winner:'울산 해성고'},
      {a:'창원 대성고',aScore:5,b:'수원 광명고',bScore:4,winner:'창원 대성고'},
      {a:'포항 제일고',aScore:3,b:'강릉 동해고',bScore:0,winner:'포항 제일고'},
    ]},
    {round:'16강',games:[
      {a:'서울 한빛고',b:'부산 해원고'}, {a:'대전 중앙고',b:'경기 동원고'}, {a:'전주 상산고',b:'울산 해성고'}, {a:'창원 대성고',b:'포항 제일고'},
    ]},
    {round:'8강',games:[{a:'?',b:'?'},{a:'?',b:'?'}]},
  ],
}

export const highSchoolCareerForPlayer = (name:string, position:string, batsThrows:string):HighSchoolHubViewModel => ({
  ...structuredClone(highSchoolCareerMock),
  player:{...highSchoolCareerMock.player,name,position,batsThrows},
})
