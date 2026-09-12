# 04 - Events & Story

WORKSTREAM: 04 - Events & Story
UPDATED_AT: 2026-09-12
SOURCE_OF_TRUTH: `main@3a4fc58a3c56d9042561494a08a676762fb4661d`
STATE: ACTIVE
CURRENT_TASK: Expand current CanonicalEventDTO story/presentation layer without inventing new simulation truth
RESULT: PASS_WITH_PREEXISTING_BALANCE_CI_BLOCKER

## CURRENT_PRODUCTION_STATE
- PR #54 (03 CareerSourceFact) is merged.
- PR #56 (04 CanonicalEventDTO v1) is merged as `05a9c0b23eb8da27c4de42e4b4e16c92a559cf6a`.
- PR #57 (07 canonical event HTTP/frontend transport) is merged as `aa3dea91f652d157d9dc19f26deeab61cce9488c`.
- Production transport contract is `mutation.result.notable_events: CanonicalEventDTO[]` and `advanceResult.notable_events: CanonicalEventDTO[]`.
- 07 preserves backend order/sequence and does not rewrite story text or event semantics.
- 06 visual timeline rendering remains consumer-owned.

## CURRENT_EVENT_PIPELINE
Authoritative pipeline remains:
`03 CareerSourceFact OR authoritative gameplay notable marker -> 04 CanonicalEventDTO -> 07 unchanged transport -> 06 presentation`.

04 does not:
- infer transitions from final snapshots;
- emit source facts;
- mutate gameplay/career state;
- append durable history;
- consume simulation RNG;
- fabricate unsupported categories.

## STORY_TEMPLATE_SYSTEM_V2
`src/event_timeline.py` now uses a deterministic presentation registry (`PRESENTATION_BUILDERS`) instead of one large conditional presentation block.

Same source fact produces the same canonical base text. No random variant selection is used in v2. Hash-based variants remain possible later, but only if semantics stay identical and they remain completely independent from simulation RNG.

Current deterministic templates:
- roster promotion: `1군 등록`
- roster demotion: `1군 말소`
- first-team debut: `1군 데뷔`
- injury created / cleared / changed
- recovery completed
- form transition
- Trait gained / lost
- event rating change
- season growth
- season finalized
- gameplay notable adapter: `경기 주요 장면`

FARM wording remains `비1군/개발군` roster-state wording. No Futures/minor-league game simulation is implied.

## IMPORTANCE_POLICY
Canonical hierarchy:
- `minor`
- `normal`
- `major`
- `career-defining`

Current production policy only uses what source metadata supports:
- routine form transition -> `minor`
- minor injury (`경미`) -> `minor`
- roster promotion/demotion -> `normal`
- recovery -> `normal`
- Trait gain/loss -> `normal`
- event rating change -> `normal`
- season growth -> `normal`
- season finalized -> `normal`
- gameplay notable marker -> `normal`
- first-team debut -> `major`
- severe injury (`중상`) -> `major`

No current source fact is classified `career-defining`; that label is reserved for future authoritative facts such as truly major milestones/awards/retirement where source semantics justify it.

`presentation_priority` is independent UI emphasis metadata and does not affect ordering, retention, or simulation semantics.

## TIMELINE_ORDERING
Unchanged canonical order:
1. occurred_at / simulated date
2. game_number
3. phase rank
4. source-local ordinal
5. deterministic event_id tie-breaker
6. contiguous sequence reassignment after dedupe

Category collapse remains prohibited. Multiple events from the same game/date/category remain distinct if their logical identity differs.

## FUTURE_EVENT_NAMESPACE
Reserved extension namespace only; no production events are fabricated:
- `milestone*` -> future category `career`
- `record*` -> `record`
- `award*` -> `award`
- `trade*` -> `transaction`
- `contract*` -> `transaction`
- `fa*` -> `transaction`
- `transfer*` -> `transaction`
- `retirement*` -> `career`

Unsupported CareerSourceFact types still raise `ValueError` until an authoritative source fact and explicit 04 mapper are added.

## PLAYER_CAREER_STORY_VIEW_READINESS
The DTO itself remains UI-agnostic. Module-level advisory filter mapping shows current/future categories are sufficient for:
- All -> all events
- Games -> `gameplay`
- Development -> `development`, `form`, `trait`
- Injuries -> `injury`
- Roster -> `roster`
- Awards -> future `award`
- Records -> future `record`
- Transactions -> future `transaction`
- Career -> `lifecycle`, future `career`

No UI-specific filter field was added to CanonicalEventDTO.

## VALIDATION
PR #62 branch code/status HEAD before this status-only commit: `4bc7a9aeef479d377ce2613bbd79c7a5f35f132f`.
Workflow #914 / run `34664934315`:

PASS:
- Vercel Python packaging
- compile
- external PostgreSQL durable-store tests
- Vercel entrypoint
- API vertical-slice tests
- related production integration tests
- all CanonicalEventDTO/source-fact tests
- all new `test_event_presentation_v2.py` tests
- web build/tests

New presentation tests specifically PASS:
- same input -> byte-stable DTO
- no simulation RNG consumption
- deterministic template metadata
- importance policy
- multiple same-category events retained
- multiple same-game/multi-category events retained
- duplicate suppression without collapsing distinct fact types
- durable/transient separation
- empty timeline
- unsupported future facts raise instead of fabricating
- career-story filter namespace readiness without DTO pollution

### PRE-EXISTING FULL-SUITE BLOCKER
Full `unittest discover` is not globally green because existing `test_balance_v04.BalanceV04Tests.test_draft_distribution_not_extreme` fails:
- fixed-seed undrafted rate = `0.056666...`
- stale assertion requires `> 0.10`

This is not caused by PR #62:
- PR #62 changes only `src/event_timeline.py`, this 04 status file, and presentation tests.
- The exact same deterministic balance failure already occurs on predecessor PR #61 / workflow #902 before PR #62 exists.
- PR #61 is the merge that produced current main `3a4fc58...`.
- 04 does not modify draft/generation/balance thresholds to make an unrelated legacy gate pass.

Because that full-suite step fails, downstream auto-career/balance-smoke/draft-calibration workflow steps are skipped in PR #62. This remains an external main-baseline CI issue, not an Events & Story implementation failure.

## UNSUPPORTED
Still OPEN until authoritative production source facts exist:
- off-day story facts
- lineup/role changes
- coach/manager interactions not emitted as CareerSourceFact
- rivalry
- milestone
- record
- award-specific timeline event
- contract / salary / service time
- FA / posting
- trade / transfer / release
- retirement timeline
- full Futures/minor-league game simulation

## GATES
- CURRENT_EVENT_PRESENTATION = PASS
- DETERMINISTIC_RENDERING = PASS
- NO_STATE_MUTATION = PASS
- MULTI_EVENT_RETENTION = PASS
- FUTURE_FACT_READINESS = PASS
- PR56_CANONICAL_EVENT_DTO = PASS_MERGED
- PR57_HTTP_TRANSPORT = PASS_MERGED
- PR62_TARGETED_AND_INTEGRATION_TESTS = PASS
- REPOSITORY_FULL_CI = OPEN_PREEXISTING_DRAFT_BALANCE_GATE
- UI_TIMELINE_RENDERING = OPEN_06
