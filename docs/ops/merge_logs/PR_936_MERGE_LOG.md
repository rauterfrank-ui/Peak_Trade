# PR #936 — MERGE LOG

## Summary
- PR: https://github.com/rauterfrank-ui/Peak_Trade/pull/936
- Title: ops: add replay regression pack operator shortcut (Slice 3.6)
- Scope: ops replay regression pack script + runbook docs + tests
- Risk: MED
- Merge mode: SQUASH

## Why
Adds an operator-friendly shortcut to replay the Slice 3.6 regression pack, with documentation and tests to ensure the script remains stable.

## Changes
- Add replay regression pack script and operator workflow.
- Add/expand runbook docs for the Slice 3.6 replay workflow.
- Add tests covering the replay regression pack script behavior.

### Files
```text
docs/ops/runbooks/README.md
docs/ops/runbooks/RUNBOOK_SLICE_3_6_REPLAY_REGRESSION_PACK_OPERATOR_SHORTCUT.md
scripts/ops/pt_replay_regression_pack.sh
tests/ops/test_replay_regression_pack_script.py
```
