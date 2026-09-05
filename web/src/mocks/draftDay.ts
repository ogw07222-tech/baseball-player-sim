import type { DraftDayViewModel } from '../types/draftDay'

export const draftDayMock: DraftDayViewModel = {
  year: 2026,
  draftStatus: 'SELECTED',
  player: {
    name: '김도윤', school: '서울 한빛고등학교', schoolEn: 'HANBIT HIGH SCHOOL', position: 'SS', batsThrows: 'R / R', age: 18,
    avg: .342, obp: .421, slg: .557, ops: .978, performanceScore: 132, nationalRank: 14, positionRank: 'SS #3', scoutedGrade: 'A-',
  },
  finalHighSchoolResume: [
    { tournament:'청룡기', result:'8강' },
    { tournament:'황금사자기', result:'4강' },
    { tournament:'대통령배', result:'16강' },
    { tournament:'봉황대기', result:'준우승' },
  ],
  resumeFooter: { ops:.978, hr:4, sb:6 },
  selectedTeam: { name:'키움 히어로즈', shortName:'KIWOOM HEROES', crestLetter:'K' },
  draftResult: { round:3, overallPick:27, playerType:'PROSPECT', contractStatus:'입단 협상 예정' },
  preDraftProjection: [
    {label:'예상 지명 범위',value:'2–3 ROUND'},
    {label:'Consensus',value:'Late 2R / Early 3R'},
    {label:'Performance Rank',value:'#14'},
    {label:'Scout Rank',value:'#22'},
    {label:'Position Rank',value:'SS #3'},
    {label:'Draft Stock',value:'RISING',tone:'positive'},
    {label:'Confidence',value:'MEDIUM',tone:'warning'},
  ],
  teamFit: [
    {label:'팀 적합도',value:'HIGH',percent:92},
    {label:'Need at SS',value:'HIGH',percent:88},
    {label:'Performance Fit',value:'HIGH',percent:90},
    {label:'Upside Fit',value:'MEDIUM',percent:71},
    {label:'Immediate Readiness',value:'MEDIUM',percent:66},
  ],
  draftBoard: [
    {pick:25,team:'서울 블루스',player:'박민재',pos:'CF',school:'경기 서원고',grade:'A'},
    {pick:26,team:'부산 웨이브',player:'이준호',pos:'RHP',school:'부산 해성고',grade:'A-'},
    {pick:27,team:'키움 히어로즈',player:'김도윤',pos:'SS',school:'서울 한빛고',grade:'SELECTED',selected:true},
    {pick:28,team:'대전 이글스',player:'—',pos:'—',school:'—',grade:'—'},
    {pick:29,team:'광주 타이거즈',player:'—',pos:'—',school:'—',grade:'—'},
  ],
  fullDraftBoard: [
    {pick:21,team:'인천 랜더스',player:'정우진',pos:'3B',school:'서울 성광고',grade:'A-'},
    {pick:22,team:'수원 위즈',player:'박준서',pos:'SS',school:'인천 대명고',grade:'B+'},
    {pick:23,team:'창원 다이노스',player:'최민석',pos:'CF',school:'부산 해원고',grade:'A-'},
    {pick:24,team:'대구 드래곤즈',player:'이현우',pos:'RHP',school:'대구 중앙고',grade:'A'},
    {pick:25,team:'서울 블루스',player:'박민재',pos:'CF',school:'경기 서원고',grade:'A'},
    {pick:26,team:'부산 웨이브',player:'이준호',pos:'RHP',school:'부산 해성고',grade:'A-'},
    {pick:27,team:'키움 히어로즈',player:'김도윤',pos:'SS',school:'서울 한빛고',grade:'SELECTED',selected:true},
    {pick:28,team:'대전 이글스',player:'—',pos:'—',school:'—',grade:'—'},
    {pick:29,team:'광주 타이거즈',player:'—',pos:'—',school:'—',grade:'—'},
    {pick:30,team:'서울 베어스',player:'—',pos:'—',school:'—',grade:'—'},
  ],
  draftFeed: [
    {round:'R2',pick:18,player:'이현우',pos:'RHP',school:'대구 중앙고',team:'대구 드래곤즈'},
    {round:'R2',pick:19,player:'최민석',pos:'CF',school:'부산 해원고',team:'창원 다이노스'},
    {round:'R3',pick:21,player:'정우진',pos:'3B',school:'서울 성광고',team:'인천 랜더스'},
    {round:'R3',pick:22,player:'박준서',pos:'SS',school:'인천 대명고',team:'수원 위즈'},
  ],
  roundProgress: [
    {round:1,status:'COMPLETE',progress:'30/30'},
    {round:2,status:'COMPLETE',progress:'30/30'},
    {round:3,status:'CURRENT',progress:'27/30'},
    {round:4,status:'NEXT'},
  ],
}

export function draftDayForPlayer(overrides?:Partial<DraftDayViewModel['player']>):DraftDayViewModel {
  return { ...draftDayMock, player:{...draftDayMock.player,...overrides} }
}
