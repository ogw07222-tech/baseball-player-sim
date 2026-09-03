# Career Event System

## 목적

커리어 이벤트는 플레이어에게 미래를 통제할 버튼을 주는 시스템이 아니다.

핵심 원칙은 다음과 같다.

> 선택은 결과를 결정하지 않고 앞으로 굴릴 주사위의 모양을 바꾼다.

같은 선택을 해도 seed, 재능, 멘탈, Trait, 현재 상태에 따라 다른 결과가 나와야 한다.

## 데이터 구조

이벤트는 `src/events.py`의 데이터 중심 카탈로그로 관리한다.

주요 구조:

- `CareerEvent`
  - id
  - name
  - description
  - rarity
  - condition
  - choices
- `EventChoice`
  - id
  - name
  - risk (`stable`, `medium`, `risky`)
  - outcomes
- `Outcome`
  - weight
  - quality
  - 즉시 stat range
  - 시즌 growth mean modifier
  - growth variance modifier
  - growth explosion modifier
  - injury result
  - fatigue change
  - Trait add/remove

## 현재 이벤트

- 햄스트링 이상 징후
- 타격폼 변경
- 벌크업
- 2군 장기체류
- 겨울 훈련
- 코치와의 의견 충돌
- 슬럼프 대응
- 부상 복귀 시점

조건에 맞는 이벤트만 후보가 된다.

예를 들어 2군 장기체류 이벤트는 FARM PA가 충분히 많고 1군 PA가 적을 때 발생 후보가 된다.

## 발생 빈도와 희귀도

시즌당 주요 이벤트 목표는 1~3회다.

현재 기본 가중치:

- 1회: 35%
- 2회: 50%
- 3회: 15%

이벤트 자체는 common / uncommon / rare / career_defining 희귀도를 지원한다. 현재 카탈로그는 주로 common~rare이며 career_defining 확장을 위한 구조를 준비해 둔다.

250개 완전 커리어 Monte Carlo에서는 시즌당 평균 약 1.786회의 주요 이벤트가 기록됐다.

## 결과 확률 보정

기본 outcome weight에 다음이 제한적으로 개입할 수 있다.

- talent: 좋은 결과 확률을 조금 이동
- mentality: risky 선택에서 일부 영향
- 빠른 성장 / 느린 성장
- 부상 위험 / 빠른 회복
- 기복이 심함 / 꾸준함

어떤 값도 성공을 확정하지 않는다.

## Auto decision

자동 진행과 Monte Carlo에서는 이벤트를 자동 선택한다.

기본 위험도 가중치:

- stable: 40%
- medium: 35%
- risky: 25%

mentality가 높은 선수는 risky 선택 확률이 조금 높아질 수 있지만 특정 선택지만 반복하도록 만들지 않는다.

## 햄스트링 이벤트의 trade-off

동일 조건에서 1,000회씩 반복한 v0.3 샘플:

### 참고 계속 출전

- 대실패/중상: 12.3%
- 시즌 성장까지 포함한 ability 변화 평균: +2.041
- ability 변화 표준편차: 1.471
- 하위 10%: +0.220
- 이벤트 후 평균 결장: 18.92경기

### 재활 치료

- 대실패/중상: 0%
- 시즌 성장까지 포함한 ability 변화 평균: +1.866
- ability 변화 표준편차: 0.928
- 하위 10%: +0.742
- 이벤트 후 평균 결장: 19.82경기

따라서 참고 출전은 기대 성장량이 조금 더 높지만 하방 위험과 분산이 크고, 재활은 더 안정적이지만 큰 성공 가능성을 줄인다.

## 기록과 세이브

`Player.event_history`에는 최소 다음을 저장한다.

- year
- age
- event id/name
- chosen option id/name
- choice risk
- result id/name
- outcome quality
- stat changes
- trait changes
- injury changes

코칭스태프 교체도 플레이어 소속팀에서 발생하면 event history에 기록된다.

save version 2에서 이 필드를 저장하며 save version 1은 기본값을 주어 계속 읽을 수 있다.
