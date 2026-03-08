# WebUI Ops Cockpit v2.7 Truth-First

## Purpose
Adds tiny read-only source-group refinements:
- source filter chips / grouped source visibility
- canonical/runtime/supporting grouping
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
