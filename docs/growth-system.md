# Growth & Aging System — v0.4

## 핵심 원칙

성장은 확률적이다. 재능이 높으면 장기 평균은 유리하지만 매 시즌 성공을 보장하지 않는다.

v0.4의 구조:

> 약한 자연 성장 + 재능 + development profile + 코치 + 출전 경험 + 시즌 중 이벤트 + Trait + 랜덤성

v0.4는 v0.3에서 낮춘 자연 성장량을 다시 올리지 않는다. 평균 peak ability가 낮았던 문제는 고졸 시작 능력 스케일을 상향하고 이벤트 시간축을 강화하는 방식으로 해결한다.

## 자연 성장

프로토타입 기본값:

- 18~22세: +2.0
- 23~27세: +1.2
- 28~31세: +0.15
- 32~35세: -1.25
- 36세 이상: -2.65

각 스탯은 이 평균 주변의 확률분포에서 성장량을 별도로 뽑는다. 고재능 선수도 `0`, `-1` 같은 시즌 결과가 가능하다.

## 고졸 시작 스케일

v0.4는 고3 current ability 평균을 약 70으로 이동했다.

1,000명 fixed-seed 표본:

- 평균 70.207
- P10 63.295
- P50 70.312
- P90 77.538
- 80+ 3.3%
- 90+ 0.0% (1,000명 표본에서는 미출현, 분포 자체에는 상한 없음)

100은 여전히 KBO 1군 평균급을 해석하기 위한 기준점이지 상한이 아니다.

## Development profile

- early_bloomer 20%
- normal 55%
- late_bloomer 20%
- very_late_bloomer 5%

profile은 성장 평균을 이동시키지만 결과를 결정하지 않는다.

## 코치

각 팀은 batting/fielding coach를 가진다. 코치 효과는 능력치를 직접 지급하지 않고 성장 평균과 분산을 바꾼다.

5시즌 비교 예:

| 코치 | contact | power | discipline | peak ability |
|---|---:|---:|---:|---:|
| power | +10.44 | +14.02 | +10.46 | 93.787 |
| precision | +15.73 | +8.98 | +14.64 | 94.601 |
| balanced | +13.02 | +11.45 | +12.90 | 94.209 |

코치는 성장 방향을 바꾸지만 미래를 결정하지 않는다.

## 출전 경험

1군/2군 PA는 시즌 종료 자연 성장의 기대값에 작은 영향을 준다. 출전 경험은 talent·이벤트·랜덤성을 압도하지 않는다.

## 이벤트 성장과 자연 성장 분리

v0.4에서 가장 중요한 변경이다.

- 이벤트의 직접 stat change: **발생 즉시 적용**
- 잔여 시즌 temporary modifier: **다음 경기부터 적용, 시즌 종료 시 제거**
- 이벤트가 주는 growth mean/variance modifier: **시즌 종료 자연 성장에 합산**
- 자연 성장/코치/PA 경험: **시즌 종료 처리**

따라서 Game 70에서 power +5 이벤트가 발생하면 Game 71부터 power +5가 실제 타석 판정에 사용된다.

## Growth explosion vs breakthrough

기존 희귀 `growth explosion`은 유지한다. 이는 시즌 종료 성장 엔진의 희귀 추가 보너스다.

Career Event의 `major_breakthrough`/`legendary_breakthrough`는 별도 사건이다. 실제 커리어 시간축에서 발생하며 선택과 결과 추첨을 거친다.

## Breakthrough affinity

선수마다 hidden `breakthrough_affinity`가 생성된다. 이는 대박 이벤트의 등장 가중치만 이동시키며 성공 결과를 보장하지 않는다.

목적은 대박 사건 횟수가 모든 선수에게 4~5회로 몰리는 것을 막는 것이다.

300커리어 결과에서 major 횟수는 0~11회까지 분포했다. 평균은 4.627회이며 시즌당 0.238회다.

## 노쇠

32세 이후 음의 성장 평균은 스탯별 aging multiplier를 사용한다. 주력/체력/내구성은 상대적으로 빠르게 감소할 수 있고 contact/discipline/mentality는 더 오래 유지될 수 있다.

## 검증

`python -m src.balance`는 초기 ability, 드래프트, 데뷔, FARM PA, peak ability/age, talent 상관, 이벤트 빈도, breakthrough, 부상, 코치 비교 등을 출력한다.
