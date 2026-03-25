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
- Report summary may include `followup_topic_ranking`: ordered follow-up topics derived from check rows (`recommended_priority`, then `effective_level`, then `check_id`). No registry writes; no separate handoff artifact beyond embedded summary fields.

## Read-only handoff context
- Report summary may include `handoff_context`: a bounded, deterministic excerpt derived from summary rollups and `followup_topic_ranking` (primary follow-up id, top five follow-ups, strict flag). For human/tool consumption only; no registry writes and no separate handoff artifact files.

## Read-only registry / pointer inputs
- Report summary may include `registry_inputs`: parsed `docs&#47;ops&#47;registry&#47;*.pointer` files (sorted by filename, `fields` sorted by key). Missing directory yields an empty stable payload. `handoff_context.registry_inputs_rollup` mirrors pointer count and the first `run_id` found in that order (operators/evidence cross-check).

## Next
- map existing building blocks
- define snapshot schema
- expand next-topic inputs beyond check-derived ranking
- define operator handoff contract
