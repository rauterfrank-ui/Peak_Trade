# PR 1065 — MERGE LOG

## Summary
ReplayPack inspect UX + evidence pack: stable human-readable inspect output (plus `--json`), stability coverage, CLI smoke refinement, and ops evidence/index updates.

## Why
Provide operator-grade inspection output for ReplayPack v1/v2 bundles and a reproducible evidence trail for v2 CLI verification.

## Changes
- `scripts/execution/pt_replay_pack.py`: inspect UX improvements (stable text + optional JSON output).
- `tests/replay_pack/test_inspect_output_stability.py`: stability coverage for inspect output.
- `tests/replay_pack/test_replay_pack_cli_smoke.py`: updated/extended smoke coverage (as per PR diff).
- `docs/execution/REPLAY_PACK_VNEXT.md`: updated inspect/CLI usage.
- `docs/ops/evidence/EV_REPLAY_PACK_V2_CLI_VERIFY_20260128.md`: evidence pack for v2 CLI verify.
- `docs/ops/EVIDENCE_INDEX.md`: indexed new evidence entry.

## Verification
- CI required checks: PASS (incl. tests (3.11), strategy-smoke, lint gate).
- Local (reported earlier in PR):
  - python3 -m pytest -q tests/replay_pack/test_golden_bundle_v1.py
  - python3 -m pytest -q tests/replay_pack/test_hash_validation.py
  - python3 -m pytest -q tests/replay_pack/test_golden_bundle_v2.py
  - python3 -m pytest -q tests/replay_pack/test_replay_pack_cli_smoke.py
  - python3 -m pytest -q tests/replay_pack/test_inspect_output_stability.py

## Risk
LOW (offline-only CLI UX + tests + docs/evidence; deterministic outputs).

## Operator How-To
- Run ReplayPack verification suite:
  - python3 -m pytest -q tests/replay_pack/test_golden_bundle_v1.py
  - python3 -m pytest -q tests/replay_pack/test_hash_validation.py
  - python3 -m pytest -q tests/replay_pack/test_golden_bundle_v2.py
  - python3 -m pytest -q tests/replay_pack/test_replay_pack_cli_smoke.py
  - python3 -m pytest -q tests/replay_pack/test_inspect_output_stability.py
- Evidence reference:
  - docs/ops/evidence/EV_REPLAY_PACK_V2_CLI_VERIFY_20260128.md

## References
- PR: #1065
- Merge commit: afe0a591211a19fb6862c00f6b1e9cd897005867
- Merged at: 2026-01-28T20:33:24Z
