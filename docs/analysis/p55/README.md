# P55 — Switch-Layer E2E + Gated Runner v1

## Goal
End-to-end deterministic Switch-Layer pipeline (P52 + P53 + P54) with **paper/shadow-only** runner and evidence pack generation.

## Safety
- No live execution, no network I/O.
- Any live/record path must be denied by default unless P49/P50 policy explicitly enables + arms + token verifies.

## Outputs
- `out/ops/p55_<slug>_<TS>/` evidence directory
- `manifest.json`, `switch_decision.json`, `routing.json`, `meta.json` (names may evolve)

## Next
Implement `src/ops/p55/switch_layer_e2e_runner_v1.py` + tests.
