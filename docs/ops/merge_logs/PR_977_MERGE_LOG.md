# PR #977 — Merge Log

## Summary
Docs-only: Add `RUNBOOK_BRANCH_CLEANUP_RECOVERY` (Recovery via Tags + Bundles) and wire it into runbooks index + workflow frontdoor.

## Why
Provide a deterministic, low-risk recovery procedure for branch cleanup operations:
- Tags pinned by SHA enable restoring deleted branches.
- Bundles provide a portable snapshot for removed worktree branches.

## Changes
- Runbook: `docs&#47;ops&#47;runbooks&#47;RUNBOOK_BRANCH_CLEANUP_RECOVERY.md` (new)
- Index: `docs&#47;ops&#47;runbooks&#47;README.md` (link)
- Frontdoor: `docs&#47;WORKFLOW_FRONTDOOR.md` (link)

## Verification
- CI: required checks PASS (per merge).
- Local: Docs Gates Snapshot (changed) PASS: Token Policy, Reference Targets, Diff Guard (per PR).

## Risk
LOW — docs-only. Kein Einfluss auf produktive Execution Paths (keine `src&#47;**` Änderungen).

## Operator How-To
Follow the runbook steps for:
- restoring from `cleanup&#47;*` tags
- restoring from `.bundle` for removed worktrees
- sanity checks (`git tag -l`, `git bundle verify`, etc.)

## References
- PR: https://github.com/rauterfrank-ui/Peak_Trade/pull/977
- Merge commit (main): 745f322ca1af374dc10217dc4afa86431e3249d5
