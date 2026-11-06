# PR #309 — feat(ops): add branch hygiene script (origin/main enforcement)

## Summary
PR #309 wurde gemerged am 2025-12-25T03:14:06Z.
Squash-Commit: 8346619 — "feat(ops): add branch hygiene script (origin/main enforcement) (#309)".

## Why
Verhindert PR-Drift durch lokale (unpushed) Commits auf `main` (Lessons Learned aus PR #305).
Neue Branches werden explizit von `origin&#47;main` erstellt und der Prozess bricht ab, wenn lokaler `main` ahead ist.

## Changes
- scripts/ops/new_branch_from_origin_main.sh (neu, executable)
- docs/ops/README.md (Dokumentation: Branch Hygiene Abschnitt)

## Verification
- CI: alle Required Checks PASS (Auto-Merge)
- Lokal:
  - `scripts&#47;ops&#47;new_branch_from_origin_main.sh <branch>` zeigt Usage & Checks
  - `scripts&#47;ops&#47;ops_center.sh doctor` bleibt grün

## Risk
Low (Ops Script + Docs).

## Operator How-To
```bash
git checkout main
scripts/ops/new_branch_from_origin_main.sh feat/my-feature
```

## References
- PR #309
- Commit 8346619
