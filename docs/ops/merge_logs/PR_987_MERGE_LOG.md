# PR #987 — MERGE LOG

## Summary
- Adds AI Live activity demo helper and proof test.
- Extends local AI Live ops runbook with activity/demo guidance.

## Why
- Ensure operator can reliably produce **non-empty** AI telemetry (decisions/actions) for dashboard + alert verification.

## Changes
- scripts/obs/ai_live_activity_demo.sh (new)
- scripts/obs/emit_ai_live_sample_events.py (update)
- tests/obs/test_ai_live_activity_demo_v1.py (new)
- docs/ops/runbooks/RUNBOOK_AI_LIVE_OPS_LOCAL.md (update)

## Verification
- Local:
  - pytest: `python3 -m pytest -q tests/obs/test_ai_live_activity_demo_v1.py`
- CI:
  - Required checks green (lint, docs gates, tests matrix).

## Merge Evidence
- PR: #987
- MergedAt (UTC): 2026-01-24T22:15:14Z
- Merge Commit: 1ac992108ea3fe414f87eb57689f19fd15d7980b

## Risk
- Low/Med: scripts/obs + docs + tests only; no src/** changes.
