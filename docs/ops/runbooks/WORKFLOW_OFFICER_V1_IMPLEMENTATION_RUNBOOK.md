# Workflow Officer v1 – Implementation Runbook

## Status
- bootstrap only

## Guardrails
- no mutation of paper or shadow data
- no runtime or live execution changes
- docs and operator workflow only until explicitly expanded

## Entry Points
- `src/ops/workflow_officer.py`
- `tests/ops/test_workflow_officer.py`

## Read-only follow-up ranking
- Report summary may include `followup_topic_ranking`: ordered follow-up topics derived from check rows (`recommended_priority`, then `effective_level`, then `check_id`). No registry or handoff output.

## Next
- map existing building blocks
- define snapshot schema
- expand next-topic inputs beyond check-derived ranking
- define operator handoff contract
