## Summary
Docs reference-target verification parity + priority fixes (rescued).

## What changed
- Improved docs reference targets verifier (parity / changed-files focus).
- Added bounded ignore-list for legacy/worklog areas.
- Fixed priority missing targets in ops/risk docs.

## Verification
- `bash scripts/ops/verify_docs_reference_targets.sh --changed --base origin/main`
- Policy gates expected green (docs-only; no enable-patterns).

## Risk
Low (docs-only).

## Rollback
Revert PR commit(s).
