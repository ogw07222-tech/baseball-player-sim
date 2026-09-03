# Baseball Player Career Simulator

선수 한 명의 야구 인생을 숫자와 확률로 따라가는 Python 커리어 시뮬레이터.

현재 구현은 **Pre-Alpha v0.3 growth & career-event balance prototype**다. 고3 선수 생성부터 전국대회, 드래프트, KBO 1·2군, 성장/코칭/커리어 이벤트/부상/슬럼프/수상/노쇠를 거쳐 은퇴까지 한 커리어를 끝까지 진행할 수 있다.

## 핵심 방향

- 구단 운영이 아니라 **선수 1명 중심**
- 경기 직접 조작보다 **숫자 기반 자동 시뮬레이션**
- 전략 최적화보다 **랜덤성, 성장, 특성, 커리어 변동성** 중시
- 플레이어의 선택은 결과를 확정하지 않고 **결과 확률분포를 바꿈**
- 기본 능력치는 최대 제한이 없는 절대값 구조
- 유저 선수 타석은 다단계(투구 → 볼/스트라이크 → 스윙 → 컨택 → 타구 결과) 판정
- 배경 세계는 추상화/fast simulation 방식
- KBO를 시작점으로 NPB/MLB/국가대표 확장이 가능하도록 리그와 선수 능력값을 분리

## 기획 문서 우선순위

`DESIGN.md`가 게임 기획의 source of truth다. 확률식, 성장 공식, 드래프트 가중치 등 아직 기획에서 확정하지 않은 값은 `src/config.py`의 **프로토타입 밸런스 값**으로만 관리한다.

세부 문서:

- `STATS.md` — 기본 스탯
- `TRAITS.md` — 특성
- `SYSTEMS.md` — 전체 시스템
- `ROADMAP.md` — 장기 개발 순서
- `docs/growth-system.md` — 성장/노쇠/코칭/출전 경험
- `docs/career-events.md` — 커리어 이벤트와 선택 철학
- `docs/league-system.md` — 리그 확장
- `docs/national-team.md` — 국가대표 확장
- `docs/balance-v0.3.md` — v0.3 Monte Carlo 밸런스 스냅샷

## 실행

Python 3.10+ 권장. 외부 패키지는 필요하지 않는다.

대화형 CLI:

```bash
python -m src.main --seed 12345
```

고교부터 은퇴까지 자동 스모크런:

```bash
python -m src.main --seed 12345 --auto --name "김OO" --position SS --bats-throws R/R --traits 3
```

테스트:

```bash
python -m unittest discover -s tests -v
```

Monte Carlo 밸런스 리포트:

```bash
python -m src.balance --samples 1000 --careers 250 --coach-samples 100 --event-samples 1000
```

JSON 파일로 저장:

```bash
python -m src.balance --output balance-report.json
```

## 현재 구현

- 이름/포지션/투타/초기 특성 0~3개 선택
- 스탯별 truncated normal 초기 생성 + 포지션 보정
- 일반/상급/특급/세대급 mixture 기반 재능 생성
- 긍정/부정 Trait, 중복 및 상충 방지
- hidden development profile: early / normal / late / very late bloomer
- 청룡기/황금사자기/대통령배/봉황대기
- pitch-by-pitch 타석 판정 및 AVG/OBP/SLG/OPS 누적
- 실제 재능과 분리된 스카우트 추정 재능
- KBO 10개 팀 데이터, 1군/2군 승강
- 팀별 batting/fielding coaching staff와 낮은 확률의 코치 교체
- 약한 자연 성장 + 재능 + 코치 + 출전 경험 + 이벤트 + 랜덤성 기반 성장
- 성장 폭발/성장 실패/늦은 성장/노쇠
- 데이터 중심 커리어 이벤트와 interactive/auto 선택
- 슬럼프/핫스트릭/피로/부상
- 낮은 빈도의 Trait 획득/소멸
- MVP/골든글러브/타격왕/홈런왕/타점왕/도루왕
- 은퇴 및 최종 커리어 요약
- JSON save/load + RNG state 보존
- save v2 및 v1 세이브 하위 호환
- Monte Carlo 밸런스 분석 도구

## v0.3 핵심 밸런스 변경

- 18~22세 자연 성장 bias: `4.6 → 2.0`
- 23~27세 자연 성장 bias: `2.7 → 1.2`
- 드래프트 기준: `98 / 90 / 80 / 70`
- 2군 출장 기준: ability baseline `68 → 63`
- 1군 출장 baseline은 `92` 유지
- 콜업 경쟁 기준은 약 3포인트 완화
- 시즌당 중요한 커리어 이벤트 목표: 약 1~3회
- 성장 폭발은 여전히 희귀 이벤트로 유지

고정 seed의 1,000명 드래프트 샘플에서 v0.3 분포는 대략 1R 7.7%, 2~3R 12.0%, 4~7R 27.6%, 8~11R 30.2%, 미지명 22.5%였다. 자세한 결과는 `docs/balance-v0.3.md`에 기록한다.

## 알려진 한계

- 투수 커리어는 미구현이며 타자 상대 투수는 프로필 분포로 생성한다.
- 팀별 실제 선수 로스터/순위/포스트시즌은 아직 추상화되어 있다.
- 수상 경쟁자는 실제 전체 리그 선수 객체가 아니라 시즌별 가상 경쟁 표본이다.
- 코치는 개별 인물 로스터가 아니라 성장 철학 중심의 추상화 모델이다.
- 이벤트는 현재 시즌 종료 시점의 주요 선택 이벤트가 중심이며 경기 중 실시간 이벤트는 제한적이다.
- NPB/MLB/국가대표/FA/트레이드/포스팅은 데이터 구조 확장 지점만 준비되어 있고 완전 구현되지 않았다.
- 현재 2군 체류 시간이 길고 부상 빈도가 높은 경향이 있어 후속 밸런스 조정이 필요하다.

## 다음 추천 단계

1. 1,000~10,000개 완전 커리어 배치 시뮬레이션으로 2군 체류/부상/스타 비율 재조정
2. KBO 전체 배경 선수 풀과 실제 시즌 순위/수상 경쟁 구조
3. 포지션별 수비 가치 및 출장 경쟁 고도화
4. 이벤트 조건과 시즌 중 발생 시점 세분화
5. 투수 전용 스탯/구종/투수 커리어
6. 국가대표 및 NPB/MLB 확장
