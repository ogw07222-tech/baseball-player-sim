# Future Expansion Roadmap

STATUS: FUTURE
CURRENT_PHASE: FREE_PLAYER_CAREER
IMPLEMENT_NOW: NO

## Purpose

This document records long-term expansion plans for Baseball Player Career Simulator.

The current project should remain focused on completing a strong free Player Career experience. The systems listed here are intentionally deferred so they are not forgotten, while also preventing premature premium implementation during the current public development phase.

## 1. Long-Term Product Direction

The long-term architecture should support one shared baseball simulation core with multiple game modes layered on top:

- Player Career Mode
- GM / Front Office Mode
- Manager Mode
- Commissioner / Sandbox Mode

The goal is one baseball simulation engine with multiple ways to control and observe the same simulated baseball world, rather than separate duplicated games.

## 2. Current Public Development Scope

Current priority: FREE PLAYER CAREER MODE.

Target experience:

High School -> Draft -> Professional Entry -> Farm / First Team -> Development -> Injuries -> Performance -> Awards -> Career Decisions -> Retirement

The current public repository should prioritize:

- gameplay simulation
- player generation and ratings
- growth and career progression
- events and career history
- statistics and season lifecycle
- save/load
- UI
- production integration
- real-baseball calibration and validation

Do not prioritize billing, subscriptions, entitlements, or premium-only systems yet.

## 3. Future Game Modes

### GM / Front Office Mode

Potential systems:

- full roster management
- player acquisition
- contracts
- FA
- trades
- draft management
- scouting
- coaches
- finances
- team building
- development strategy
- long-term club planning

The GM should control a Team through shared core systems, not through a special copy of Player Career logic.

### Manager Mode

Potential systems:

- lineup construction
- batting order
- defensive positioning
- starting rotation
- bullpen roles
- substitutions
- pinch hitting
- pinch running
- tactical decisions
- game-by-game player usage

Gameplay simulation must remain shared with other modes.

### Commissioner / Sandbox Mode

Potential systems:

- edit league rules
- create leagues
- create teams
- create players
- modify schedules
- modify roster rules
- modify development environments
- simulate decades automatically
- inspect league history
- experimentation tools

This mode should expose configuration over the simulation core rather than fork simulation logic.

## 4. Potential Premium Features

Future premium expansion may include:

- GM Mode
- Manager Mode
- Commissioner / Sandbox Mode
- multiple save slots
- career comparison
- advanced historical records
- deeper scouting information
- advanced progression analysis
- percentile and split reports
- player similarity and projection tools
- custom dashboards
- custom leagues, teams, players, and schedules
- fast multi-season simulation
- long-term league history simulation
- league-wide analysis
- data export

Exact product tiers and pricing are intentionally not defined yet.

## 5. Premium Design Rule

Premium access must never directly improve simulation outcomes.

Forbidden examples:

- paid users receive higher ratings
- paid users develop faster
- paid users receive fewer injuries
- paid users receive favorable RNG
- paid users receive better draft odds
- paid users receive easier gameplay probabilities

Acceptable premium design:

- additional game modes
- additional information
- deeper management controls
- additional customization
- additional save capacity
- advanced analytics
- sandbox capabilities

Premium should increase depth, control, and analysis, not player strength.

## 6. Architecture Rule

Every major future feature should be classified before implementation as one of:

- CORE
- PLAYER_MODE
- GM_MODE
- MANAGER_MODE
- SANDBOX
- PREMIUM_ENTITLEMENT

### CORE

Rules that belong to the baseball world itself, such as:

- Player
- Team
- League
- Game Simulation
- Growth
- Injury
- Schedule
- Contracts
- Transactions
- Statistics

Core systems must not depend on which game mode the user is playing.

### PLAYER_MODE

Features specific to controlling one player's career.

### GM_MODE

Features specific to controlling a club/front office.

### MANAGER_MODE

Features specific to tactical team/game management.

### SANDBOX

Administrative or simulation-experiment controls.

### PREMIUM_ENTITLEMENT

Access-control only. Premium entitlement must not contain baseball simulation formulas.

## 7. Architectural Direction

Long-term target direction:

```text
src/
  domain/
    player/
    team/
    league/
    game/
    season/
    contracts/
    transactions/

  simulation/
    gameplay/
    growth/
    injuries/
    roster/
    schedule/

  modes/
    player_career/
    gm/
    manager/
    sandbox/

  application/
    services/
    commands/
    queries/

  presentation/
  persistence/
  api/
```

Future private-only layers may later include:

```text
entitlements/
billing/
```

This is a direction, not an instruction to perform a large refactor now. Existing production code should only move when justified by actual feature work.

## 8. Public -> Private Development Transition

Current phase:

PUBLIC REPOSITORY -> FREE PLAYER CAREER DEVELOPMENT

Future transition:

PRIVATE DEVELOPMENT -> PREMIUM EXPANSION

Before beginning premium development:

1. Finish a viable free Player Career experience.
2. Stabilize the reusable simulation core.
3. Review repository licensing and data provenance.
4. Review what code/history has already been published.
5. Move future proprietary expansion development to the intended private workflow.
6. Design account/entitlement infrastructure.
7. Only then begin premium feature implementation.

Changing a repository from public to private does not revoke copies of code that were already publicly available. Proprietary premium implementation therefore should not be committed prematurely during the public phase.

## 9. Current Non-Goals

DO NOT IMPLEMENT YET:

- payment processing
- subscriptions
- premium entitlement checks
- premium UI
- GM Mode
- Manager Mode
- Commissioner Mode
- monetization-specific gameplay logic

Exceptions require an explicit decision from 00 - Game Design HQ.

## 10. Development Rule Going Forward

When designing a major new system, ask:

1. Is this a baseball-world rule or a game-mode rule?
2. Can every AI-controlled player/team use the same core system?
3. Is Player Career accidentally becoming the owner of a general baseball system?
4. Would this system still work if the user controlled a team instead of one player?
5. Is anything being implemented now only because of a hypothetical future premium feature?

If question 5 is yes, defer it unless it is necessary for the free game.

## 11. Current Priority

FREE PLAYER CAREER FIRST.

Build the reusable baseball world underneath it. Premium expansion comes later.
