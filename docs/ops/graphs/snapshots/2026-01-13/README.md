# Docs Graph Snapshot — 2026-01-13

## Context
Post-merge snapshot after runbooks frontdoor reintegration (PR #706, PR #707).

## Snapshot Details
- **Date:** 2026-01-13
- **Trigger:** Post-merge ops hygiene
- **Tool:** `scripts/ops/docs_graph_snapshot.py`
- **Runtime:** 0.411s

## Metrics
- **Nodes:** 957
- **Edges:** 1645
- **Broken targets:** 181
- **Broken anchors:** 7
- **Orphaned pages:** 610

## Status
This snapshot reflects the current state of the docs graph including pre-existing broken links and orphaned pages. This is a baseline snapshot for tracking improvements over time.

## Files
- `docs_graph_snapshot.json` — Full graph data (nodes, edges, broken links, orphans)
- `broken_targets.md` — Triage report for broken link targets (generated)
- `orphans.md` — Triage report for orphaned pages (generated)

## Triage Outputs

### How to Run Triage

Generate triage reports from this snapshot:

```bash
./scripts/ops/pt_docs_graph_triage.sh
```

This will create/update:
- `broken_targets.md` — Categorized by reason (file not found, outside repo, etc.)
- `orphans.md` — Categorized by doc area (root, docs/ops, docs/ops/runbooks, etc.)

### Interpretation Notes

**What to fix first:**
1. **Broken targets in user-facing docs** (quickstarts, frontdoors) — HIGH priority
2. **Placeholder paths** (e.g., `...` in links) — HIGH priority
3. **Orphaned runbooks** — MEDIUM priority (link from appropriate index)
4. **Historical artifacts in root** — LOW priority (archive candidates)

See [`../../TRIAGE_2026-01-13.md`](../../TRIAGE_2026-01-13.md) for detailed analysis and remediation backlog.

## Operator Runbook

For step-by-step remediation guidance, see:
- [`../../runbooks/RUNBOOK_DOCS_GRAPH_TRIAGE_AND_REMEDIATION.md`](../../runbooks/RUNBOOK_DOCS_GRAPH_TRIAGE_AND_REMEDIATION.md)

## Notes
- Exit code 1 from snapshot tool is expected due to broken links (fail-on-broken flag)
- Snapshot is informational; no action required for initial snapshot PR
- Future work: Address broken links and orphaned pages systematically (Phase 9B)
