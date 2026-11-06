# WebUI Ops Cockpit v2.6 Truth-First

## Purpose
Adds tiny read-only UX refinements:
- freshness legend
- availability legend
- compact status chips
- unchanged truth-first boundaries

## Scope
- read-only only
- no execution logic changes
- no config changes
- no gate changes

## Routes
- `/ops`
- `/api/ops-cockpit`

## Implementation Targets
- `src/webui/ops_cockpit.py`
- `src/webui/app.py`
- `tests/webui/test_ops_cockpit.py`
