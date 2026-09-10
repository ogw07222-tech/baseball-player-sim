# Baseball Player Career Simulator

선수 한 명의 야구 인생을 숫자와 확률로 따라가는 Python 커리어 시뮬레이터.

현재 구현은 **Pre-Alpha v0.4 — Starting Ability & In-Season Event Flow** 프로토타입이다. 고3 선수 생성부터 전국대회, 드래프트, KBO 1·2군, 성장/코칭/커리어 이벤트/부상/슬럼프/수상/노쇠를 거쳐 은퇴까지 한 커리어를 끝까지 진행할 수 있다.

## 핵심 철학

- 구단 운영이 아니라 **선수 1명 중심**
- 전략 최적화보다 **운, 성장, 사건, 커리어 변동성** 중시
- 플레이어의 선택은 결과를 확정하지 않고 **앞으로 굴릴 확률분포를 변경**
- 기본 능력치는 최소 0, 최대 제한 없음
- `100`은 만점이 아니라 KBO 1군 평균급을 해석하기 위한 기준점
- 재능과 현재 능력은 별개이며 고재능도 실패, 저재능도 대폭발 가능
- 유저 선수 타석은 투구 → 존/스윙 → 컨택 → 타구 → 결과의 다단계 판정

`DESIGN.md`가 게임 기획의 source of truth이며 확정되지 않은 수치는 `src/config.py`의 프로토타입 밸런스 값으로 관리한다.

## 실행

Python 3.10+ / 외부 의존성 없음.

```bash
python -m src.main --seed 12345
```

자동 커리어:

```bash
python -m src.main --seed 12345 --auto --name "김OO" --position SS --bats-throws R/R --traits 3
```

테스트:

```bash
python -m unittest discover -s tests -v
```

Monte Carlo:

```bash
python -m src.balance --samples 1000 --careers 300 --event-samples 3000 --coach-samples 100 --seed 20260904
```

## v0.4 핵심 변경

### 고졸 시작 스케일

v0.3의 평균 current ability 약 60에서 **약 70**으로 이동했다. 자연 성장량을 다시 크게 올리는 대신 프로 입단 시점의 기본 스케일을 상향했다.

초기 분포 중심값:

- contact 69
- power 65
- discipline 63
- speed 75
- defense 70
- throwing 70
- stamina 78
- durability 80
- mentality 63

재능 mixture는 v0.3 구조를 유지한다.

### 드래프트 / 1·2군

- 드래프트 컷: `105 / 97 / 86.8 / 76.2`
- FARM play baseline: `71`
- FIRST play baseline: `92`
- 1군 콜업은 ability 85~90에서 낮은 가능성, 90~95에서 실질 경쟁, 100 전후에서 높은 기회가 되도록 비선형 판정
- 이미 1군 PA를 충분히 확보한 선수는 다음 시즌 로스터 안정성을 일부 얻음

### 시즌 중 Career Event

v0.3의 시즌 종료 일괄 이벤트를 제거했다.

현재 프로 시즌 루프:

`경기 → 이벤트 발생 판정 → 선택/자동선택 → 결과 즉시 적용 → 다음 경기`

Interactive에서 `시즌 종료까지`를 선택해도 중요 이벤트가 발생하면 해당 경기에서 멈춘다. 선택 후 같은 시즌을 이어간다. Auto/Monte Carlo는 같은 scheduler를 사용하되 자동으로 선택한다.

영구 능력치 변화는 다음 경기부터 적용되고, `season_modifiers`는 잔여 시즌에만 적용된 뒤 시즌 종료 시 제거된다.

### Breakthrough

- `major_breakthrough`: 평균 약 4시즌당 1회
- `legendary_breakthrough`: 대부분의 커리어에서 0회, 일부 1회
- hidden `breakthrough_affinity`로 선수마다 대박 사건 빈도의 장기 분산을 다르게 함
- 같은 major 이벤트도 일부는 반복 가능하지만 반복할수록 등장 가중치가 급감

## v0.4 Monte Carlo 스냅샷

고정 seed `20260904`:

- 생성/드래프트 1,000명
- 고교→은퇴 완전 커리어 300명
- 이벤트 선택지별 3,000회
- 코치 archetype별 100명

주요 결과:

- 초기 ability 평균 **70.207**
- 드래프트: **1R 6.9 / 2~3R 10.0 / 4~7R 25.3 / 8~11R 33.5 / 미지명 24.3%**
- 평균 1군 데뷔 **22.258세**, 데뷔 실패 **9.67%**
- 평균 FARM PA **4,456.5**
- 평균 peak ability **102.086**, P90 **116.729**, P99 **133.273**
- 시즌당 이벤트 **2.565회**
- 이벤트 구성: 훈련 62.77 / 경기력 22.21 / 부상 5.01 / breakthrough 10.00%
- major breakthrough **0.238회/시즌**, 평균 **4.627회/커리어**
- legendary breakthrough **0.019회/시즌**, 63.67%의 커리어에서 0회

자세한 내용은 `docs/balance-v0.4.md` 참고.

## 세이브

`SAVE_VERSION = 3`.

v1/v2/v3 로드를 지원한다. v0.4에서 추가된 시즌 중 pending event, cooldown, temporary modifier, 성장 modifier, breakthrough affinity도 저장된다.

## 현재 알려진 한계

- 투수 커리어 미구현
- 팀 전체 실제 로스터/순위/포스트시즌은 아직 추상화
- 수상 경쟁자는 실제 전체 리그 선수 객체가 아니라 가상 경쟁 표본이라 v0.4에서 상위 선수의 MVP/GG 빈도가 높게 나오는 경향이 있음
- 평균 FARM PA는 v0.3보다 크게 감소했지만, 긴 커리어에서 5시즌 이상 2군 중심 시즌을 경험하는 비율은 여전히 높음
- FA/트레이드/포스팅/NPB/MLB/국가대표는 향후 확장
