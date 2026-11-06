# PR 1063 — MERGE LOG

## Summary
ReplayPack CLI/Runner UX: operator-facing build/validate/inspect workflow wired to ReplayPack v1/v2, with deterministic CLI smoke test and updated vNext docs.

## Why
Make ReplayPack v2 practically usable for operators (build/validate via a stable entrypoint) while preserving v1 no-regression guarantees.

## Changes
- Adds operator CLI script: scripts/execution/pt_replay_pack.py
- Builder wiring updated to support v1 vs v2 build mode via CLI-facing API hooks.
- Adds deterministic subprocess smoke test for CLI workflows.
- Extends docs/execution/REPLAY_PACK_VNEXT.md with CLI usage/examples.

## Verification
- CI required checks: PASS (pre-merge).
- Local (reported):
  - uv run pytest -q tests/replay_pack/test_golden_bundle_v1.py
  - uv run pytest -q tests/replay_pack/test_hash_validation.py
  - uv run pytest -q tests/replay_pack/test_golden_bundle_v2.py
  - uv run pytest -q tests/replay_pack/test_replay_pack_cli_smoke.py

## Risk
MEDIUM (operator UX wiring + subprocess smoke). Mitigation: deterministic smoke test + existing v1/v2 golden tests.

## Operator How-To
- Run CLI smoke test:
  - uv run pytest -q tests/replay_pack/test_replay_pack_cli_smoke.py
- Typical flows (see docs/execution/REPLAY_PACK_VNEXT.md):
  - build v1/v2 replay packs
  - validate bundle integrity/hashes

## References
- PR: #1063
- Merge commit: 431080500778addef68397efbb646337076962a1
- Merged at: 2026-01-28T19:49:20Z
