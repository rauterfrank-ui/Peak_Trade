# PR #937 — MERGE LOG

## Summary
- PR: https://github.com/rauterfrank-ui/Peak_Trade/pull/937
- Title: fix(ops): preserve exit_code 0 in compare consumer stdout
- Scope: ops consumer bugfix + test
- Risk: LOW
- Merge mode: SQUASH

## Why
Fixes a consumer formatting bug where an exit code of 0 was rendered as 1 due to a falsey default.

## Changes
- Preserve exit code 0 (default only when missing).
- Add test asserting PASS prints EXIT 0.

### Files
```text
scripts/ops/pt_compare_consume.py
tests/ops/test_compare_consume.py
```
