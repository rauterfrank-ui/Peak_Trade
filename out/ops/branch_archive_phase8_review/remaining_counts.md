# Remaining Branch Counts — Phase 8 Review

**Stand:** 2026-03-10  
**Branch:** feat/full-scan-wave17-branch-archive-phase8-review  
**Scope:** recover/*, wip/*, backup/*, tmp/*

## Summary

| Category | Count | Notes |
|----------|-------|-------|
| recover/* | 44 | Execution-networked p122–p132 subset; supervisor/launchd; stash |
| wip/* | 8 | Stash/restore, salvage, local snapshots |
| backup/* | 9 | Docs merge-log, PR snapshots, local-main snapshots |
| tmp/* | 2 | docs-runbook, stack-test |
| **Total** | **63** | |

## By Prior Bucket (from naming)

- **recover**: 44 branches — largest set; mix of execution-networked (closed cycle), supervisor, online-readiness, accounting, reporting
- **wip**: 8 branches — stash/restore, salvage, cleanup recovery
- **backup**: 9 branches — historical snapshots
- **tmp**: 2 branches — scratch/runbook

## Upstream Status

- **none** (local-only): 61 branches
- **origin/main**: 1 branch (tmp/docs-runbook-to-finish-clean)
- **other**: 1 branch (wip/pausepoint — invalid upstream ref)

## Divergence vs main

- All branches are behind main (48–1651 commits)
- Ahead counts: 0–6 commits per branch
- Most recover branches: 1 ahead, 260–438 behind
- wip/salvage branches: 1–3 ahead, 898–1651 behind (high divergence)
