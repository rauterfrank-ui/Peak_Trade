# PR 1058 — MERGE LOG

## Summary
Merged PR #1058: Legacy plumbing for determinism-sensitive paths (BetaBridge + ReplayPack pinned to legacy ledger engine).

## Why
Keep existing determinism/golden artifacts stable while introducing the new FIFO Slice2 engine.

## Changes
- Keeps/uses legacy ledger engine for:
  - BetaBridge
  - ReplayPack
- Adds/adjusts ledger legacy plumbing/adapters as required.

## Verification
- Required checks: PASS (CI)
- Determinism-sensitive tests: PASS (reported in PR context).

## Risk
High (determinism-critical). Any wrong pinning can break golden bundles / hash expectations.

## Operator How-To
- Run determinism-critical tests (examples):
  - `uv run pytest -q tests/execution/test_beta_event_bridge_determinism.py`
  - `uv run pytest -q tests/execution/test_beta_event_bridge_ordering.py`
  - `uv run pytest -q tests/replay_pack/test_golden_bundle_v1.py`
  - `uv run pytest -q tests/replay_pack/test_hash_validation.py`

## References
- PR: #1058
- Merge commit: `aaac49fc9521de5f3ada4d96881101808cf2c638`
- Merged at: `2026-01-28T17:50:41Z`
