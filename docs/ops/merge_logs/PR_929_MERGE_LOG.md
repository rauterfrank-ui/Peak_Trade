# PR #929 — Merge Log

## Summary
Slice 3: Equity Curve Snapshot-Serie als Golden Regression (byte-identisch) + optionales Artifact-Manifest (sha256). Operator-only Golden Update Script. RISK: HIGH.

## Why
Determinismus-kritische Regression: Equity Curve Output muss drift-fest sein (byte-identisch), um Änderungen an Bridge/Ledger/Canonical JSON sofort in CI zu erkennen.

## Changes
- Golden files:
  - `tests/golden/slice3_equity_curve_minimal.jsonl`
  - `tests/golden/slice3_artifact_manifest_minimal.json`
- Tests:
  - `tests/execution/test_beta_event_bridge_equity_curve_golden.py` (byte-identity vs golden + manifest verify)
- Tooling:
  - `scripts/testing/update_slice3_golden.py` (deterministic golden regeneration; operator-only)
- Bridge/Docs:
  - `src/execution/bridge/beta_event_bridge.py` (equity_curve snapshot output contract)
  - `docs/execution/SLICE_3_BETA_BRIDGE.md` (Golden contract + operator process)

## Verification
- `uv run pytest -q tests/execution/test_beta_event_bridge_determinism.py` → PASS
- `uv run pytest -q tests/execution/test_beta_event_bridge_ordering.py` → PASS
- `uv run pytest -q tests/execution/test_beta_event_bridge_equity_curve_golden.py` → PASS
- `uv run ruff format --check .` → PASS
- `uv run ruff check .` → PASS
- docs-token-policy-gate: PASS

## Risk
HIGH — `src&#47;execution&#47;**` determinism + artifact contract changes; no live unlocks. Golden regression reduces drift risk.

## Operator How-To
- Golden update (explicit operator action only):
  - `uv run python scripts/testing/update_slice3_golden.py --fixture tests/fixtures/slice3_beta_events_minimal.jsonl`
- Review checklist for golden diffs:
  - fixture unchanged unless justified
  - schema/cadence unchanged unless explicitly breaking
  - canonical JSON invariants intact
  - manifest sha256 matches emitted artifacts

## References
- PR: `https://github.com/rauterfrank-ui/Peak_Trade/pull/929`
- Merge Commit: `392c1e054a89d56e893cd76fef9718f8927ccffb`
- mergedAt: `2026-01-22T02:10:58Z`
