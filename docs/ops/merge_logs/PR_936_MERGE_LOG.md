## PR #936 — MERGE LOG

## Summary
- PR: [#936](https://github.com/rauterfrank-ui/Peak_Trade/pull/936)
- Title: ops: replay regression pack operator shortcut (Slice 3.6)
- Scope: ops script + hermetic test + runbook index and new runbook
- Risk: HIGH
- Merge mode: ADMIN SQUASH (bypass), branch deleted, match-head-commit
- Merged at (UTC): 2026-01-22T09:21:13Z
- Merge commit: 83db48febdb9185213cbd4ce6eccc4c784699a82

## Why
Adds a single-command operator shortcut that runs an offline deterministic replay regression pack. The script orchestrates bundle usage, compare execution, and consumer summary generation into a stable OUT_DIR layout, preserving exit codes and producing dashboard-ready artifacts. This reduces operator friction for regression replays while keeping execution strictly offline and additive.

## Changes
- Adds operator shortcut script for offline deterministic replay regression pack.
- Adds hermetic integration test for the script behavior.
- Adds a dedicated operator runbook and links it from the runbooks index.

## Verification

### Local testing
```bash
python3 -m pytest -q
```

### Result
- 6518 passed, 47 skipped, 3 xfailed, 1 warning

### Files
```text
scripts/ops/pt_replay_regression_pack.sh
tests/ops/test_replay_regression_pack_script.py
docs/ops/runbooks/RUNBOOK_SLICE_3_6_REPLAY_REGRESSION_PACK_OPERATOR_SHORTCUT.md
docs/ops/runbooks/README.md
```
