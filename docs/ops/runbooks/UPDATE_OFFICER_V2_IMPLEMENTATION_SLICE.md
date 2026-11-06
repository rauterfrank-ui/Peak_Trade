# Update Officer v2 – Implementation Slice

## Goal

Build on **Update Officer v1** (`v1-min`) with **deterministic next-topic prioritization** and
**notifier-oriented** top-level fields, without changing read-only posture.

## Added in v2

| Field | Purpose |
|-------|---------|
| `next_recommended_topic` | Topic id (`category` bucket) to address first |
| `top_priority_reason` | Short deterministic explanation |
| `recommended_update_queue` | Ordered list of topic aggregates (rank, counts, headline) |

**Ranking:** Group findings by `category`. Per bucket, `worst_priority` = minimum of member
`recommended_priority` ranks. Sort buckets by `(worst_rank asc, -finding_count, topic_id asc)`.

## Markdown

New sections (exact headings):

- **Next best update topic**
- **Why now**
- **What to review first** (numbered queue + sorted items for the top topic)

## Guardrails

- Read-only; no dependency bumps, lockfile writes, or installs
- No paper/shadow/evidence mutation
- No runtime/live authority
- `success=false` can still mean **content** requires review (blocked findings), not a tool crash

## Deliverables (code)

- `src&#47;ops&#47;update_officer.py` — queue + top-level fields
- `src&#47;ops&#47;update_officer_schema.py` — validate queue + v2 report keys
- `src&#47;ops&#47;update_officer_markdown.py` — new sections
- Tests under `tests&#47;ops&#47;test_update_officer*.py`
- This runbook

## Version

- `officer_version`: **`v2-min`**
