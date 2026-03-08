# WebUI Ops Cockpit v2.3 Truth-First

## Purpose
Adds small read-only UX refinements:
- source prioritization
- compact availability emphasis
- priority-bucket summary
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
