# Featured Prospects 2026 Data Report

Snapshot date: 2026-09-05  
Dataset: `data/high_school/featured_prospects_2026.json`  
Data version: `2026.1`

## Summary

- Total prospects: **20**
- Grade 3: **19**
- Grade 2: **1**
- Grade 1: **0**
- Pitchers (`P`): **6**
- Catchers (`C`): **4**
- Broad infielders (`IF`): **6**
- Broad outfielders (`OF`): **4**

Broad `IF` / `OF` is deliberately retained when the public source does not justify a narrower defensive position.

## Public field coverage

- Throws known: **5 / 20 (25%)**
- Bats known: **4 / 20 (20%)**
- Height known: **0 / 20 (0%)**
- Weight known: **0 / 20 (0%)**
- At least one source: **20 / 20 (100%)**

Optional physical measurements were intentionally left `null` in v1 rather than expanding collection scope. Unknown handedness is also left `null`; no inference is performed.

## Selection basis

The core selection is the publicly announced 2026 Korean youth national-team roster for the 14th Asian Youth Baseball Championship, supplemented by two prominently covered 2026 high-school catchers. The national-team announcement is used as a high-signal, limited curated pool rather than attempting to collect every high-school player.

This dataset is not a ranking and does not encode scouting judgments. Inclusion means only that the player was selected for this small featured reference set.

## Provenance approach

Each record stores structured source metadata (`type`, `publisher`, `title`, `date`, `url`). The primary roster source is an established national news report explicitly based on the Korea Baseball Softball Association announcement. Supplemental public player-profile pages are used only where they directly confirm handedness; no contact/social fields from those pages are stored.

No SNS/community claims and no automated scraping were used.

## Missing / null fields

The main missing optional fields are:

- handedness for players where no checked source in this curation pass directly confirmed it;
- height and weight for all players;
- `public_stats` (not collected in v1);
- `notes` unless a neutral factual note becomes necessary.

These omissions are intentional. `null` is preferred over guessing.

## Validation expectations

`tools/validate_featured_prospects.py` checks:

- JSON parsing;
- stable ID format and duplicate IDs;
- required fields;
- grades;
- position enum;
- handedness enum;
- empty names/schools;
- source object shape and absolute URLs;
- basic physical-value bounds when optional measurements are present;
- duplicate `(display_name, school_name, grade, position)` records;
- forbidden gameplay/integration fields.

Expected v1 acceptance results:

- duplicate IDs: **0**
- required-field errors: **0**
- source coverage: **100%**
- gameplay/integration fields: **0**

## Limitations

1. This is a curated 20-player snapshot, not a comprehensive national prospect database.
2. Public roster/news sources can change or be corrected; future revisions should preserve version history.
3. Broad positions are retained rather than inferred into specific fielding positions.
4. One Grade-2 player is intentionally included because the public national-team roster identified him as the lone second-year selection.
5. Real-world signing/eligibility status is not represented. Draft eligibility and simulation behavior must be determined later by engine integration, not by this dataset.

## Integration boundary

No roster insertion, draft-pool connection, gameplay rating generation, pitcher/hitter archetype assignment, Performance Score mapping, save-schema change, or frontend work is part of this report or dataset.

Recommended next step after the Pitcher Foundation is finalized: create a separate integration branch that maps a Featured Prospect reference record into a simulation instance while generating all gameplay state independently from the real-world identity data.
