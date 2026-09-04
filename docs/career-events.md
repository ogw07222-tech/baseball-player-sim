# Career Event System — v0.4

## 철학

> 선택은 결과를 정하는 버튼이 아니라 앞으로 굴릴 주사위의 모양을 바꾸는 행동이다.

이벤트는 실제 커리어 시간축 안에서 발생한다. 시즌 종료 후 결과를 한꺼번에 붙이지 않는다.

## 시즌 진행 흐름

프로 시즌은 내부적으로 다음 순서를 반복한다.

1. 경기 진행
2. 부상/폼/로스터 상태 갱신
3. 해당 시점의 이벤트 발생 여부 판정
4. 조건을 만족하는 이벤트 후보 생성
5. Interactive면 pending event로 멈춤 / Auto면 자동 선택
6. 결과 추첨
7. 영구 스탯·Trait·부상·폼·temporary modifier 즉시 적용
8. 다음 경기 진행

미래 이벤트의 결과는 미리 결정하지 않는다.

## 이벤트 데이터

`CareerEvent`:

- id / name / description
- rarity
- category
- condition
- phases
- weight
- once_per_season
- cooldown_games
- career_once
- coach_tags

`Outcome`:

- weight / quality
- 영구 stat range
- temporary stat range
- 시즌 종료 growth mean modifier
- growth variance / explosion modifier
- injury / fatigue / Trait / form effect

## 시즌 구간

- `preseason`: 시즌 시작 전
- `early`: Game 1~45
- `mid`: Game 46~100
- `late`: Game 101~144

이벤트별로 가능한 구간과 조건을 제한한다. 예를 들어 겨울 훈련은 preseason, 2군 훈련 방향은 FARM PA가 쌓인 mid/late, 슬럼프 대응은 실제 slump 상태에서만 후보가 된다.

## 이벤트 카테고리

현재 카탈로그는 크게 다음으로 구성된다.

- training: 겨울훈련, 타격폼, 수비훈련, 영상분석, 벌크업, 2군 훈련, 코치 조언
- performance: 경기 접근법, 슬럼프 대응, 흐름 점검
- injury: 햄스트링 경고, 부상 복귀 시점
- breakthrough: major / legendary

300커리어 결과:

- training 62.77%
- performance 22.21%
- injury 5.01%
- breakthrough 10.00%
- 시즌당 전체 이벤트 2.565회

## Interactive / Auto

Interactive에서 `시즌 종료까지`를 선택해도 중요 이벤트가 발생하면 해당 경기에서 정지한다. 사용자가 선택하면 즉시 결과를 적용하고 같은 시즌을 이어간다.

Auto와 Monte Carlo에서는 `auto_choose()`가 stable/medium/risky 가중치를 이용해 선택하고 시즌을 계속 진행한다.

## Temporary modifier

일부 이벤트는 영구 성장 대신 잔여 시즌 modifier를 준다.

예:

- Game 60: 새 타격폼 적응 성공 → `contact_eff +4`
- Game 61~144: 실제 타석 엔진에서 +4 적용
- 시즌 종료: temporary modifier 제거

Player의 `season_modifiers`에 저장되며 중간 save/load도 지원한다.

## Major breakthrough

현재 예:

- 타격 메커니즘 완성
- 피지컬 완성
- 코치와 완벽한 궁합
- 완벽한 타격폼 발견
- 늦깎이 폭발
- 부상 후 각성

목표는 약 4시즌에 1회다. 300커리어에서는 **0.238회/시즌**, 평균 **4.627회/커리어**였다.

대박 이벤트가 발생해도 대박 결과가 확정되지는 않는다. 예를 들어 타격 메커니즘 완성의 적극적 선택은 안정 선택보다 평균 상승과 상방이 높지만 분산도 크다.

3,000회 비교:

| 선택 | ability 변화 평균 | 표준편차 | P10 | P90 |
|---|---:|---:|---:|---:|
| 안정적 refine | +1.691 | 0.870 | +0.400 | +2.633 |
| 적극적 commit | +2.824 | 1.760 | +0.767 | +5.283 |

## Major 횟수 분산

모든 선수가 동일하게 4~5회 받지 않도록 hidden `breakthrough_affinity`와 반복 감쇠를 사용한다.

최종 300커리어 원시 분포는 0~11회까지 퍼졌다. 일부 major 이벤트는 반복 가능하지만 같은 이벤트가 다시 등장할수록 weight가 급감한다.

## Legendary breakthrough

예:

- 세대급 재능 개화
- 예상 밖의 완성

300커리어:

- 0회: 63.67%
- 1회: 35.67%
- 2회 이상: 0.67%
- 평균 0.370회/커리어

낮은 talent 선수도 조건을 만족하면 `예상 밖의 완성` 후보가 될 수 있다.

## 부상 선택 trade-off

햄스트링 이벤트 3,000회씩 비교:

- 참고 출전: 직접 ability 평균 +0.182, quality 표준편차 1.521, 중상 11.73%
- 재활: 직접 ability 평균 +0.061, quality 표준편차 0.719, 중상 0%

안전 선택은 하방을 줄이고 위험 선택은 분산을 키운다. 이벤트 자체의 부상 비중은 낮게 유지하며 독립적인 경기 부상 엔진은 별도로 존재한다.

## Event History

각 이벤트는 최소 다음을 저장한다.

- year / age
- game_number / season_phase
- event_id / event_name
- rarity / category / breakthrough_tier
- choice / risk
- outcome / quality
- stat_changes
- temporary_effects
- trait_changes
- injury_changes
- ability_before / ability_after

따라서 향후 UI에서 시즌별 사건 타임라인을 직접 구성할 수 있다.
