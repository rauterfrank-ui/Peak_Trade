## PR #937 — MERGE LOG

## Summary
- PR: [#937](https://github.com/rauterfrank-ui/Peak_Trade/pull/937)
- Title: fix(ops): preserve exit_code=0 in compare consumer stdout
- Scope: ops compare consumer output formatting + unit test
- Risk: LOW
- Merge mode: ADMIN SQUASH, branch deleted, match-head-commit
- Merged at (UTC): 2026-01-22T14:56:12Z
- Merge commit: a6949aa71d85b346d5f16161f12a4d7ee58fea9b

## Why
Ensures exit_code preserves the value 0 when present. Previously, a falsey default caused exit_code=0 to be printed as EXIT=1, which is misleading for PASS cases and breaks operator trust in the summary output.

## Changes
- Fixes exit_code defaulting logic to default only when the field is missing.
- Adds a regression assertion to ensure EXIT=0 is rendered in stdout.

## Verification

### Local testing
```bash
python3 -m pytest -q tests/ops/test_compare_consume.py
```

### Files
```text
scripts/ops/pt_compare_consume.py
tests/ops/test_compare_consume.py
```

### Evidence
```text
docs/ops/merge_logs/snapshots/PR_937_gate_snapshot.json
docs/ops/merge_logs/snapshots/PR_937_post_merge_evidence.json
```
