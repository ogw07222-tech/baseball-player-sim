#!/usr/bin/env bash
set -euo pipefail

mkdir -p reports/integration-local

python -m compileall -q src tests tools

python -m unittest \
  tests.test_persistent_inning \
  tests.test_natural_baseball_events \
  tests.test_pr33_blocking_fixes \
  tests.test_stat_aggregation_advance \
  tests.test_production_game_provider \
  tests.test_production_game_provider_contracts \
  tests.test_pitcher_usage_foundation \
  tests.test_catcher_foundation \
  tests.test_production_integration_consolidation -v

python -m unittest discover -s tests -v

python tools/natural_event_sanity.py \
  > reports/integration-local/natural-events.json

python tools/production_game_provider_sanity.py \
  --games 10000 --seed 20260906 \
  --output reports/integration-local/full-game.json

python tools/pitcher_usage_sanity.py \
  --seasons 500 --seed 20260906 \
  > reports/integration-local/pitcher-usage.json

python tools/catcher_generation_sanity.py \
  --samples 200000 --seed 20260906 \
  > reports/integration-local/catcher-generation.json

(
  cd web
  npm ci
  npm run test
  npm run build
)

echo "Production integration consolidation checks completed."
