# Baseball Player Simulator

선수 한 명의 야구 인생을 숫자와 확률로 따라가는 커리어 시뮬레이션 프로젝트.

## 핵심 방향

- 구단 운영이 아니라 **선수 1명 중심**
- 경기 직접 조작보다 **숫자 기반 자동 시뮬레이션**
- 전략 최적화보다 **랜덤성, 성장, 특성, 커리어 변동성**을 중시
- 기본 능력치는 상한이 없는 절대값 구조
- 특성(Trait)으로 직구 특화, 변화구 취약 같은 개성을 부여
- KBO를 시작점으로 NPB, MLB, 마이너리그 등 확장 가능하도록 설계
- 국가대표, WBC, 프리미어12 등 국제대회 시스템 추가 예정

## 현재 단계

현재는 코딩보다 **게임 시스템 설계**가 우선이다.

기획 기준 문서: [`DESIGN.md`](DESIGN.md)

세부 문서:

- [`STATS.md`](STATS.md) — 기본 스탯 체계
- [`TRAITS.md`](TRAITS.md) — 특성 시스템
- [`SYSTEMS.md`](SYSTEMS.md) — 전체 시스템 개요
- [`ROADMAP.md`](ROADMAP.md) — 개발 순서
- [`docs/growth-system.md`](docs/growth-system.md) — 성장/노쇠
- [`docs/league-system.md`](docs/league-system.md) — 리그 구조
- [`docs/national-team.md`](docs/national-team.md) — 국가대표

## 프로젝트 원칙

1. 스탯에 고정 최대치를 두지 않는다.
2. 높은 스탯이 결과를 보장하지 않게 한다.
3. 같은 능력의 선수도 특성과 운에 따라 다른 커리어를 만들 수 있어야 한다.
4. 유저가 모든 결과를 통제하지 못하게 한다.
5. 세부 밸런스 수치는 구현 단계에서 반복 시뮬레이션으로 조정한다.
6. 기획 문서가 코드보다 먼저 확정되며, 구현은 이 문서를 기준으로 진행한다.

## 상태

**Pre-Alpha / Game Design Phase**
