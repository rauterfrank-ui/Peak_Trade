# Git State Validation

This document describes the repository git state validation utilities and how they are used in ops workflows (worktrees, merges, CI sanity checks).

## Overview

The validation scripts are designed to be safe-by-default and support both **graceful** and **strict** modes depending on whether warnings should fail the run.

Primary use-cases:
- pre-flight checks before merges
- post-merge verification (optionally with CI context)
- local operator sanity checks across git worktrees

## Related Documentation

### Scripts

- `scripts/validate_git_state.sh` - General git state validation
- `scripts/automation/post_merge_verify.sh` - Post-merge verification
- `scripts/automation/format_merge_log_snippet.sh` - Merge-log snippet generator
- `scripts/validate_rl_v0_1.sh` - RL v0.1 validation (similar pattern)

### Documentation

- `docs/ops/WORKTREE_POLICY.md` - Git worktree management policy
- `docs/ops/CI.md` - CI pipeline documentation
- `docs/ops/README.md` - Operations guide (quick reference)

## Notes

If a script relies on optional tooling (e.g. GitHub CLI), it must degrade gracefully when unavailable or unauthenticated.
