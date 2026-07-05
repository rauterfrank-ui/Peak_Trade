# PR Closure Canonical Checklist Hook v1

Purpose: provide a deterministic local post-PR closeout check for Peak_Trade.

The hook verifies:
- current branch
- HEAD and origin/main identity
- clean working tree
- local ahead/behind divergence against origin/main
- stash presence as warning-only

It does not mutate repository state.
It does not merge, push, delete branches, or touch runtime systems.

## Canonical usage

```bash
python3 scripts/ops/pr_closure_canonical_checklist_v1.py
```

## Exit codes

- `0` when verdict is `PASS`
- `1` when verdict is `FAIL`

## Output

Single JSON object on stdout with sorted keys.

| Field | Description |
|-------|-------------|
| `verdict` | `PASS` or `FAIL` |
| `branch` | Current branch name |
| `head` | Current `HEAD` SHA |
| `origin_main` | `origin/main` SHA |
| `ahead_origin_main` | Commits ahead of `origin/main` |
| `behind_origin_main` | Commits behind `origin/main` |
| `worktree_clean` | Whether `git status --short` is empty |
| `stash_entries` | Count of stash entries |
| `findings` | List of finding codes |

## Finding codes

| Code | Verdict impact |
|------|----------------|
| `WORKTREE_NOT_CLEAN` | Fails |
| `MAIN_DIVERGED_FROM_ORIGIN_MAIN` | Fails when on `main` and ahead/behind is non-zero |
| `STASH_PRESENT_WARN_ONLY` | Warning only |

## Related documentation

- `docs/ops/GIT_STATE_VALIDATION.md`
