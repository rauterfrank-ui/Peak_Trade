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
python3 scripts&#47;ops/pr_closure_canonical_checklist_v1.py <!-- pt:ref-target-ignore -->
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
| `origin_main` | `origin&#47;main` SHA |
| `ahead_origin_main` | Commits ahead of `origin&#47;main` |
| `behind_origin_main` | Commits behind `origin&#47;main` |
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

- `docs&#47;ops/GIT_STATE_VALIDATION.md` <!-- pt:ref-target-ignore -->
