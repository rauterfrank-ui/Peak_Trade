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
- Report summary may include `followup_topic_ranking`: ordered follow-up topics derived from check rows (`recommended_priority`, then `effective_level`, then `outcome`, then `severity`, then `check_id`). Each row may include `followup_rank_heuristic` with a versioned `components` map (`priority_rank`, `effective_level_rank`, `outcome_rank`, `severity_rank`) and `tie_break: check_id_ascii` for inspection. No registry writes; no separate handoff artifact beyond embedded summary fields.

## Read-only handoff context
- Report summary may include `handoff_context`: a bounded, deterministic excerpt derived from summary rollups and `followup_topic_ranking` (primary follow-up id, top five follow-ups, strict flag). For human/tool consumption only; no registry writes and no separate handoff artifact files.

## Read-only registry / pointer inputs
- Report summary may include `registry_inputs`: parsed `docs&#47;ops&#47;registry&#47;*.pointer` files (sorted by filename, `fields` sorted by key). Missing directory yields an empty stable payload. `handoff_context.registry_inputs_rollup` mirrors pointer count and the first `run_id` found in that order (operators/evidence cross-check).

## Read-only merge log inputs
- Report summary may include `merge_log_inputs`: read-only scan of `docs&#47;ops&#47;merge_logs&#47;PR_*_MERGE_LOG.md` (PR number from filename), sorted by PR descending, capped recent slice with parsed `merge_commit_sha` and `merged_at` when detectable. `handoff_context.merge_log_inputs_rollup` summarizes total canonical files and the latest slice head.

## Read-only provenance
- Report summary may include `workflow_officer_provenance`: deterministic declaration of which check-row fields, profile plan fields, repo globs, and summary keys feed recommendations, `followup_topic_ranking`, registry/merge-log inputs, and `handoff_context`. No extra files; no writes.

## Read-only next chat preview
- Report summary may include `next_chat_preview`: a tiny embedded read-only slice derived only from `handoff_context` and `workflow_officer_provenance` (rollup counts, up to three queued follow-up `check_id`s in ranking order, primary follow-up id, registry pointer count and latest merge-log PR from handoff rollups, provenance schema label). No separate files; no writes.
- Rendered `summary.md` may include a deterministic **Next chat preview** section (from `render_next_chat_preview_markdown` in `src/ops/workflow_officer.py`, wired via `src/ops/workflow_officer_markdown.py`) when `next_chat_preview` is present with a non-empty `preview_schema_version`.

## Read-only operator consolidated view
- Report summary may include `operator_report`: a single embedded read-only snapshot from `build_operator_report_view` (only existing summary keys such as rollups, `followup_topic_ranking`, `handoff_context`, `next_chat_preview`, and `workflow_officer_provenance`). No extra files; no writes.
- Rendered `summary.md` may include a deterministic **Operator consolidated view** section (from `render_operator_report_markdown`, wired via `src/ops/workflow_officer_markdown.py`) when `operator_report` carries a non-empty `operator_report_schema_version`.

## Read-only executive decision package
- Report summary may include `executive_summary`: a compact embedded read-only decision view from `build_executive_summary_view`, derived from `operator_report` plus the same top-level rollups already on the summary (`total_checks`, `hard_failures`, `warnings`, `infos`, `strict`). No separate files; no writes.
- `followup_topic_ranking` rows include `recommended_action` (copied from each check row) so `operator_report.primary_followup` can surface the same text for executive excerpts.
- Rendered `summary.md` may include a deterministic **Executive decision package** section (from `render_executive_summary_markdown` in `src/ops/workflow_officer.py`, wired via `src/ops/workflow_officer_markdown.py`) immediately after **Run**, when `executive_summary` carries a non-empty `executive_summary_schema_version`.

## Next
- map existing building blocks
- define snapshot schema
- expand next-topic inputs beyond check-derived ranking
- define operator handoff contract
