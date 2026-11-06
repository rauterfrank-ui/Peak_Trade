# WebUI Ops Cockpit v2.8 Truth-First

## Purpose
Adds tiny read-only compact-source refinements:
- compact grouped source summaries
- grouped availability/freshness totals
- unchanged truth-first boundaries

## Scope
- read-only only
- no execution logic changes
- no config changes
- no gate changes

## Routes
- `&#47;ops`
- `&#47;api&#47;ops-cockpit`

## Implementation Targets
- `src&#47;webui&#47;ops_cockpit.py`
- `src&#47;webui&#47;app.py`
- `tests&#47;webui&#47;test_ops_cockpit.py`
