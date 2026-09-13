# 04 - Events & Story

WORKSTREAM: 04 - Events & Story
UPDATED_AT: 2026-09-13
SOURCE_OF_TRUTH: `main@ebe1d5132271ca538013d1966f1b7e257cd63fa3`
STATE: ACTIVE
CURRENT_TASK: Normal EVENT 50 + data-driven Trait content contract
IMPLEMENTATION_BRANCH: `feature/data-driven-events-traits-catalog`
RESULT: DATA_CONTRACT_IMPLEMENTED_PENDING_REPO_CI

## TERMINOLOGY
- EVENT = player-facing interactive decision with choices.
- CAREER = automatic factual Career Timeline / Career Records entry.
- `CareerSourceFact -> CanonicalEventDTO` remains CAREER and is never reused as an Interactive EVENT DTO.

## SOURCE DOCUMENTS
Content source is limited to:
- `Baseball_Player_Career_Simulator_Normal_Events_50.docx`
- `Baseball_Player_Career_Simulator_Normal_Events_50_Effect_Contract_v2_Permanent_Ratings.docx`

Source counts imported:
- 50 EVENTs
- 146 choices
- 400 effect rows
- 239 permanent rating delta rows
- 125 temporary state rows
- 16 positive Trait candidate rows
- 20 negative Trait risk rows

The English display text is an assistant-authored reference translation; Korean source text remains the default UI copy and source of intent.

## DATA FILES
- `data/events/normal_events.json`
- `data/traits/traits.json`

Content is not embedded in Python conditionals. Stable snake_case IDs are mechanics/save identities; Korean/English display text may change without changing IDs.

## EVENT DATA CONTRACT
Each EVENT stores:
- stable `id`
- `rarity`
- `name_ko`, `name_en`
- `description_ko`, `description_en`
- category/tags
- `trigger_type`
- source eligibility text + support status
- cooldown/dedupe declaration
- exact Korean source context/design intent
- choices[]

Each choice stores:
- stable choice `id`
- bilingual label/description
- source reward/cost text
- `effects[]`
- `trait_requests[]`
- `negative_trait_risks[]`

Normalized EVENT effect types:
- `permanent_rating_delta`
- `temporary_state_modifier`
- `form_modifier`
- `fatigue_modifier`
- `fatigue_delta`

Current permanent rating targets are restricted to production core ratings:
`contact, power, discipline, speed, defense, throwing, stamina, durability, mentality`.

## TRAIT DATA CONTRACT
Extracted and normalized unique Common EVENT candidates:
- 11 positive Traits
- 7 negative Traits
- 18 unique candidate IDs total

Each Trait stores:
- stable `id`
- bilingual name/description
- rarity
- polarity
- category/tags
- conditional trigger
- effects
- conflicts
- `upgrades_to`
- progression group
- acquisition sources
- acquisition probability placeholder (not invented by 04)

Rarity enum is future-safe:
`common -> rare -> epic -> legendary`.
The 50 normal EVENT catalog directly references Common candidates only.

## TRAIT PHILOSOPHY
New Trait candidate data follows:
`condition -> Trait activation -> situational modifier`.

No new EVENT Trait is modeled as an unconditional permanent `rating +N`.
Effect strength uses non-final semantic classes such as `small`; 05/01 own later calibration/consumption.

## TRIGGER SUPPORT CLASSIFICATION
Candidate trigger declarations use:
- `supported`: source state already exists in current production representation.
- `mappable`: source state exists or can be derived without inventing new simulation truth, but a generic Trait hook is not wired yet.
- `new_contract_required`: production does not yet expose the exact context required by the Trait.
- `unsupported`: not representable without violating current architecture.

Observed current production anchors include count state, pitch type, pitcher handedness snapshot, batted-ball spray/trajectory, fatigue and recent form. Defensive/baserunning/environment/scouting contexts need varying degrees of adapter work before Trait consumption.

## VALIDATION LOADER
`src/content_catalog.py` is a pure data loader/validator. It does not mutate Player state, award Traits, resolve EVENT effects, or consume simulation RNG.

Validation fails explicitly for:
- duplicate EVENT/Trait IDs
- missing Korean/English display text
- invalid rarity
- invalid polarity
- unknown permanent rating target
- unknown EVENT effect type
- unknown Trait effect type
- broken EVENT -> Trait reference
- conflict self-reference
- unknown conflict/upgrade reference
- upgrade cycle
- missing choices
- duplicate choice ID
- invalid support status / malformed structures

Invalid content is never silently skipped.

## AUTHORITATIVE BOUNDARIES
04 owns:
- EVENT catalog
- Trait catalog
- trigger/effect declaration schema
- content validation

03 owns:
- permanent rating delta application
- Trait acquisition/removal/replacement/progression
- state mutation and atomic EVENT-choice application

01 owns:
- consuming conditional Trait triggers/effects in gameplay judgments

07 owns:
- persistence/API integration for stable IDs and catalog versions

06 owns:
- Korean-default UI presentation; English text remains reference/fallback content

05 owns:
- acquisition probabilities
- effect magnitudes
- EVENT frequency
- long-term balance/regression validation

## IMPLEMENTATION NOTE
This task deliberately does not activate all 50 EVENTs in production generation and does not replace legacy `src/traits.py` consumers. Many source eligibility rules and conditional Trait hooks require 01/03/07 contracts first. The catalog layer is ready for those authority integrations without embedding content-specific `if event_id == ...` or `if trait_id == ...` branches.

## TESTS
`tests/test_event_trait_content_catalog.py` covers:
- exact 50 / 146 / 400 source counts
- 11 positive / 7 negative unique candidate Traits
- bilingual display contract
- common-only EVENT/Trait candidate rarity
- duplicate IDs
- missing bilingual fields
- invalid rarity/polarity
- unknown rating target/effect type
- broken EVENT -> Trait reference
- conflict self-reference
- upgrade cycle
- missing/duplicate choices

Local isolated loader tests: 12 / 12 PASS before repository CI.

## HANDOFF
03:
- add atomic handlers for `permanent_rating_delta`, state effects and Trait acquisition decisions
- acquisition probabilities remain unset until balance ownership approves them
- use stable Trait IDs, not display names

01:
- define generic conditional Trait hook(s) against existing count/pitch/physical/base-state contexts
- do not branch on individual Trait IDs
- reject/leave inactive `new_contract_required` triggers until the state exists

07:
- persist Trait IDs + catalog/schema version
- transport bilingual EVENT/Trait content without merging it with CanonicalEventDTO CAREER records
- cache/load catalog at process startup and fail closed on validation error

## GATES
- DATA_FILE_LAYOUT = PASS
- EVENT_SCHEMA = PASS
- TRAIT_SCHEMA = PASS
- NORMAL_EVENT_50_IMPORT = PASS
- TRAIT_CANDIDATE_EXTRACTION = PASS
- CONTENT_VALIDATION = PASS_LOCAL
- CAREER_EVENT_SEPARATION = PASS
- PRODUCTION_EVENT_ACTIVATION = OPEN_01_03_07
- TRAIT_GAMEPLAY_CONSUMPTION = OPEN_01
- TRAIT_AUTHORITY = OPEN_03
- FINAL_BALANCE = OPEN_05
