# PR 1057 — MERGE LOG

## Summary
Merged PR #1057: Test-only pinning — WAC/Double-Entry legacy tests explicitly use legacy ledger semantics.

## Why
Prevent FIFO Slice2 engine from implicitly changing legacy test expectations; reduce CI noise and protect determinism baselines.

## Changes
- Updates legacy ledger tests/integration tests to pin to legacy ledger semantics.

## Verification
- Required checks: PASS (CI)
- Local (reported): legacy tests PASS once stacked appropriately.

## Risk
Low–Medium. Test-only scope; guards against regressions and mixed semantics.

## Operator How-To
- Run key legacy tests:
  - `uv run pytest -q tests/execution/test_ledger_pnl_golden.py`
  - `uv run pytest -q tests/execution/test_ledger_double_entry.py`
  - `uv run pytest -q tests/execution/test_execution_slice1_to_ledger_integration.py`

## References
- PR: #1057
- Merge commit: `1a2e5ecd8c040e46dea921afc707bcf632930158`
- Merged at: `2026-01-28T17:51:19Z`
