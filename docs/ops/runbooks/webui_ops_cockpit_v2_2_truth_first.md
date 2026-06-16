> **SUPERSEDED (Runbooks index):** Canonical Ops Cockpit truth-first runbook is [`webui_ops_cockpit_v2_5_truth_first.md`](./webui_ops_cockpit_v2_5_truth_first.md). This file is kept for historical reference only.

# WebUI Ops Cockpit v2.2 Truth-First

## Purpose
Refines the existing read-only Ops Cockpit UX with:
- source prioritization
- stronger truth coverage emphasis
- clearer unavailable-source rendering
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
