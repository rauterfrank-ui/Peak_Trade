# Update Officer v4 – Consumer layer

## Goal
Extend **Update Officer v3** with a deterministic consumer/parser layer for
`notifier_payload.json`, without adding transport, scheduling, or autonomous behavior.

## Added in v4
| Component | Purpose |
|-----------|---------|
| `src/ops/update_officer_consumer.py` | Load, validate, normalize, and render notifier payloads |
| `load_notifier_payload()` | Read JSON payload and validate via schema |
| `build_notifier_view_model()` | Deterministic consumer-facing normalized contract |
| `render_notifier_text_summary()` | Stable text summary for CLI/operator use |

## Consumer view model
- `headline`
- `status`
- `next_topic`
- `why_now`
- `next_action`
- `review_paths`
- `queue_preview` (entries: `rank`, `topic_id`, `worst_priority`, `finding_count`)
- `requires_manual_review`
- `severity`
- `reminder_class`

Queue entries mirror v3 notifier/schema fields (`topic_id`, `worst_priority` as `p0`–`p3`).

## Guardrails
- Read-only only
- No dependency bumps
- No lockfile writes
- No paper/shadow/evidence mutation
- No runtime/live authority
- No background execution
- No external transport in this slice

## Deliverables
- `src/ops/update_officer_consumer.py`
- `tests/ops/test_update_officer_consumer.py`
- This runbook

## Version
- consumer slice built on top of `v3-min`
