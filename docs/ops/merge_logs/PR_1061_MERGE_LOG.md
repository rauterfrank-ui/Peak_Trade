# PR 1061 — MERGE LOG

## Summary
ReplayPack v2 (contract_version=2): additive FIFO Slice2 ledger artifacts + v1/v2 validator dispatch + v2 golden determinism tests + vNext docs stub.

## Why
Enable forward-compatible FIFO ledger artifacts without breaking ReplayPack v1 golden bundles (v1 remains default and must stay byte-identical).

## Changes
- Adds v2 contract/schema modules.
- Updates builder/validator/loader for v1 vs v2 dispatch (v1 path unchanged by default).
- v2 bundle adds deterministic FIFO ledger snapshot (+ optional entries) derived from execution_events fills only (no MARK synthesis).
- Adds v2 tests enforcing determinism and legacy-unchanged bytes.
- Adds docs stub: docs/execution/REPLAY_PACK_VNEXT.md.

## Verification
- CI required checks: PASS (pre-merge).
- Local (reported):
  - uv run pytest -q tests/replay_pack/test_golden_bundle_v1.py
  - uv run pytest -q tests/replay_pack/test_hash_validation.py
  - uv run pytest -q tests/replay_pack/test_golden_bundle_v2.py

## Risk
MEDIUM-HIGH (determinism/golden-sensitive). Mitigation: v1 default unchanged + explicit tests for determinism and legacy byte-identity.

## Operator How-To
- Validate replay pack tests:
  - uv run pytest -q tests/replay_pack/test_golden_bundle_v1.py
  - uv run pytest -q tests/replay_pack/test_hash_validation.py
  - uv run pytest -q tests/replay_pack/test_golden_bundle_v2.py

## References
- PR: #1061
- Merge commit: a962e92cb170dff9951b36e3b9e112dd7646c262
- Merged at: 2026-01-28T19:18:31Z
