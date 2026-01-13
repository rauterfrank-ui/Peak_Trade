# PR 688 — Merge Log

## Summary
PR #688 (squash-merge) liefert Phase 8 „Docs Integrity Hardening": deterministischer Docs-Graph Snapshot (Nodes/Edges), Broken Target/Anchor Reporting sowie Orphan Detector inkl. Operator-Runbook und Unit Tests.

## Why
- Schnell erkennbare Docs-Integritätsprobleme (broken targets/anchors, Orphans) auf Repo-Basis
- Deterministisch, offline, ohne externe URL-Validierung
- Operierbar via klarer CLI und Runbook, geeignet für regelmäßige Repo-Snapshots

## Changes
- New: `scripts/ops/docs_graph_snapshot.py` (CLI; JSON Snapshot v1.0.0)
- New: `scripts/ops/_docs_graph.py` (shared parsing/graph module)
- New/Updated: Operator Runbook (Phase 8) unter `docs/ops/runbooks/`
- New: Unit Tests + Fixtures unter `tests/`
- New/Updated: CI Integration (Workflow/Job(s) im PR-Scope)
- Git hygiene: `docs/_generated/` ist excluded (generated output wird nicht committed)

## Verification
Local (fast, deterministic):
- Tests:
  - pytest -q`
- Example snapshot (no generated output committed):
  - `uv run python scripts/ops/docs_graph_snapshot.py --roots docs/WORKFLOW_FRONTDOOR.md WORKFLOW_RUNBOOK_OVERVIEW_2026-01-12.md docs/ops/README.md docs/INSTALLATION_QUICKSTART.md --out docs/_generated/docs_graph_snapshot.json`

CI:
- All required checks: PASS (22/22), PR merged via squash.

## Risk
LOW (docs/ops tooling only)
- No runtime trading/execution logic touched
- No network activity; ignores external URLs and mailto
- Deterministic ordering to stabilize results across runs

## Operator How-To
1) Run snapshot (default excludes archives):
   - `uv run python scripts/ops/docs_graph_snapshot.py --roots docs/WORKFLOW_FRONTDOOR.md WORKFLOW_RUNBOOK_OVERVIEW_2026-01-12.md docs/ops/README.md docs/INSTALLATION_QUICKSTART.md --out docs/_generated/docs_graph_snapshot.json`
2) Optional: include archives:
   - Add `--include-archives`
3) Triage:
   - `broken_targets`: missing files/targets (path resolution)
   - `broken_anchors`: anchor slug mismatch / missing heading
   - `orphans`: pages not reachable from roots (crosslink/navigate as needed)

## References
- PR: https://github.com/rauterfrank-ui/Peak_Trade/pull/688
- Merge commit (main): e9877c5d
- Key files:
  - `scripts/ops/docs_graph_snapshot.py`
  - `scripts/ops/_docs_graph.py`
  - `docs/ops/runbooks/` (Phase 8 runbook)
  - `tests/` (Phase 8 unit tests/fixtures)
