# Featured High School Prospects

This directory contains a small, manually curated **public-identity/reference dataset** for notable Korean high school baseball prospects relevant to the player's first high-school season.

## Scope

`featured_prospects_2026.json` is static reference data only. It may contain public facts such as a player's name, school, grade, broad position, publicly confirmed handedness, public achievements, and source provenance.

It must not contain or infer:

- gameplay ratings or grades;
- Talent, Resilience, mentality, injury proneness, personality, or private reputation;
- scouting grades, overall/potential ratings, Performance Score, draft score, or draft projection;
- gameplay archetypes;
- roster slots, draft eligibility/state, save state, or simulation state.

Unknown public facts stay `null`. Do not guess them.

## Provenance

Every real prospect must have at least one `sources` entry. Prefer sources in this order:

1. official association/tournament/school rosters or records;
2. official competition records;
3. established sports/news media;
4. other public reference sources.

Do not use community posts, rumors, private accounts, or automated/social-media scraping as identity sources. The dataset is intentionally curated by hand and is not a complete high-school roster database.

A source object uses:

```json
{
  "type": "news_article",
  "publisher": "Publisher",
  "title": "Article title",
  "date": "YYYY-MM-DD",
  "url": "https://..."
}
```

`date` may be `null` when a public reference page has no clear publication date.

## Versioning and yearly updates

The top-level `dataset_year`, `version`, `data_version`, and `last_updated` fields track the curated snapshot. This project does **not** require a real-world dataset for every future year. Future draft classes are expected to be fictional unless a separate product decision changes that policy.

When updating this dataset:

1. verify the public source;
2. change only factual reference fields;
3. leave unknown values as `null`;
4. add/update provenance;
5. run `python tools/validate_featured_prospects.py`.

## Real identity vs. future game state

A Featured Prospect Dataset record is a real-world public identity/reference record. A future game prospect instance is a separate simulation object. This data-preparation branch does not create or merge simulation objects.

## Name collision policy for future integration

If the user creates a player with the exact same full name as a featured prospect, keep the user player's chosen name. A future integration may omit that featured prospect from the save. Do not mutate the real person's name by adding suffixes such as `(2)` or `(3)`.

Actual same-name people inside the dataset are allowed and are distinguished by stable `id`, `school_name`, and `position`.

## Privacy and safety

Store only public, baseball-relevant facts. Do not add private contact details, personal social-media identifiers, rumors, behavioral judgments, or inferred sensitive/private traits.

## Integration boundary

This directory is data preparation only. Pitcher/hitter foundations, generation formulas, roster generation, draft logic, Performance Score, save schema, UI, and gameplay engine integration belong in a separate follow-up branch.
