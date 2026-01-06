# Wave Restore Runbook (Docs/Small PRs)

This runbook standardizes "restore waves" (e.g., Wave2/Wave3) to be reproducible, audit-stable, and low-risk.

## Objectives
- Restore queued branches safely and quickly.
- Maintain single source of truth (dedupe duplicated PRs/branches).
- Keep an audit trail: closeout snapshots for each wave.

## Scope (default)
- Documentation-only changes and small ops/tooling PRs.
- No runtime behavior changes unless explicitly approved.

## Naming conventions
- Restore branches: `restore/w<N>-<topic-slug>`
- Closeout branch: `docs/ops-wave<N>-restore-closeout`
- Closeout file: `docs/ops/WAVE<N>_RESTORE_CLOSEOUT_<UTCSTAMP>.md`

## Gates
- Repo clean on start and end.
- PR checks must be green before merge (unless explicitly waived).
- Dedupe rule: if same file set + same diffstat/content already merged, close duplicates with comment referencing the merged PR.

## Standard workflow
1. Inventory candidates (branches/PRs)
2. For each candidate:
   - fingerprint: files, additions/deletions, commit sha
   - open PR (or validate existing)
   - enable auto-merge (squash)
   - if duplicate: close + delete branch
3. Closeout:
   - create closeout md with PR outcomes
   - merge closeout PR
4. Cleanup:
   - ensure `main` sync
   - prune remotes
   - verify no restore branches, no open PRs

## Commands (canonical)

### Status Dashboard
```bash
bash scripts/ops/wave_restore_status.sh
```

### PR Management
```bash
# Open restore PR list
gh pr list --state open --limit 200

# Filter restore branches (remote)
git branch -r | grep -E '^  origin/restore/'

# Close duplicate PR
gh pr close <N> --comment "Closing as duplicate of #<merged> ..." --delete-branch

# Enable auto-merge
gh pr merge <N> --squash --auto

# Admin override (if checks are blocked)
gh pr merge <N> --squash --admin --delete-branch
```

### Cleanup
```bash
# Switch to main and update
git switch main
git pull --ff-only

# Delete local branch
git branch -D <branch-name>

# Prune remote branches
git fetch --prune

# Verify clean state
git status -sb
git branch -r | grep -E 'restore/' || echo "✅ No restore branches"
```

## Dashboard Tool
Use `scripts/ops/wave_restore_status.sh` for quick status checks:
- Repo status and branch
- All open PRs
- Filtered `restore/*` PRs with metadata
- Remote `restore/*` branches

## Closeout Template
```markdown
# Wave<N> Restore – Closeout Snapshot

Status: COMPLETED
Scope: Documentation restore queue (Wave<N>)
Result: Repository clean; no open PRs; main synchronized.

## Summary
- Wave<N> restore documentation PRs processed end-to-end.
- Duplicate PRs closed to maintain single source of truth.

## PR Outcomes
- PR #XXX: MERGED (<description>)
- PR #YYY: MERGED (<description>)
- PR #ZZZ: CLOSED (duplicate of #XXX)

## Verification
- `gh pr list --state open` returns none
- `gh pr list --state open --search "head:restore/"` returns none
- local `main` is synchronized with `origin/main`

## Notes
This file is an audit artifact. It captures the final state after completion of the Wave<N> restore queue.
```

## Notes
- Prefer small, frequent merges over batching.
- Always comment on duplicates: preserve traceability.
- Dashboard script provides at-a-glance status during sessions.

## References
- Wave2 Example: `docs/ops/WAVE2_RESTORE_CLOSEOUT_20260106_214505Z.md`
- Dashboard: `scripts/ops/wave_restore_status.sh`
