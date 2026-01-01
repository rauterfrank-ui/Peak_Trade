# PR #486 — chore(gitignore): ignore .logs from bg jobs

## Summary
Adds `.gitignore` entry to ignore runtime background job artifacts (`.logs/`), in preparation for background job tooling.

## Why
Background job runners (future tooling) generate runtime artifacts that should not be tracked in version control. This PR prepares the repository by ignoring these artifacts.

## Changes
- Added `.logs/` to `.gitignore` to ignore runtime job artifacts

## Verification
- Git diff shows only `.gitignore` modification
- No tracked files affected

## Risk
None. Gitignore-only change.

## Erratum (2026-01-01)
Earlier versions of this merge log incorrectly stated that `scripts/ops/bg_job.sh` was added in this PR. That was not accurate. PR #486 contained only the `.gitignore` change. The actual bg_job runner was delivered later in PR #491.

## References
- PR: https://github.com/rauterfrank-ui/Peak_Trade/pull/486
- Merged at: 2026-01-01T11:04:15Z
- Merge SHA (main tip at time of log creation): 11f0233
