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

## Notes
- Exit code 1 from tool is expected due to broken links (fail-on-broken flag)
- Snapshot is informational; no action required for this PR
- Future work: Address broken links and orphaned pages systematically
