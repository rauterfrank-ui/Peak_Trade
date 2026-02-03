#!/usr/bin/env bash
# Create stacked PRs PR-04, PR-05, PR-08 via GitHub CLI.
# Prereq: gh auth login (token valid)
set -euo pipefail

cd "$(dirname "$0")/../.."

command -v gh >/dev/null || (echo "gh not installed" && exit 1)
gh auth status || { echo "Run: gh auth login -h github.com"; exit 1; }

gh repo set-default rauterfrank-ui/Peak_Trade

# PR-04: base=main, head=pr-04-event-schemas
gh pr create \
  --base main \
  --head pr-04-event-schemas \
  --title "feat(PR-04): Event schemas + validator CLI + fixtures + smoke tests" \
  --body "Evidence: docs/ops/evidence/packs/PR-04/EV-2026-02-PR04-001.json
Verify:
- python3 -m pytest -q tests/validation/test_event_schemas.py
- python3 -m scripts.validate_events --schema schemas/events/execution_event.schema.json --jsonl tests/fixtures/events/execution_events.valid.jsonl --strict" \
  --draft=false

# PR-05: base=pr-04-event-schemas, head=pr-05-observability-port-collision
gh pr create \
  --base pr-04-event-schemas \
  --head pr-05-observability-port-collision \
  --title "feat(PR-05): fail-fast metrics port collisions; unify env var + legacy fallback" \
  --body "Evidence: docs/ops/evidence/packs/PR-05/EV-2026-02-PR05-001.json
Verify:
- python3 -m pytest -q tests/ops/test_ports.py
- python3 -m pytest -q tests/obs/test_metrics_config.py" \
  --draft=false

# PR-08: base=pr-05-observability-port-collision, head=pr-08-stage1-validation
gh pr create \
  --base pr-05-observability-port-collision \
  --head pr-08-stage1-validation \
  --title "feat(PR-08): Stage1 runners validate artifacts (exit 2 on validation failure)" \
  --body "Evidence: docs/ops/evidence/packs/PR-08/EV-2026-02-PR08-001.json
Verify (fixtures):
- python3 scripts/obs/stage1_report_index.py --root tests/fixtures/stage1_reports/sample_a --out /tmp/stage1_index.json --run-date 2026-02-02
- python3 scripts/obs/validate_stage1_index.py --root tests/fixtures/stage1_reports/sample_a --index /tmp/stage1_index.json --out /tmp/stage1_validation.json --require data.json --require report.md" \
  --draft=false

gh pr list --limit 20
