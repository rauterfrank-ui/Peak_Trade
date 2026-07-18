# Canonical SHORT Binding Miswiring Repair v1

Productive repair for the first miswiring boundary proven in
`docs/evidence/canonical_short_binding_miswiring_trace_v1/` (PR #5345).

## Repair

1. MV2 research wiring binds `BacktestEngine(use_execution_pipeline=True)`.
2. Feedback bar loop passes `honor_mapped_short_entry=True` so mapped `-1`
   opens a short (negative size) instead of the legacy flat no-op.
3. Position feedback reports SHORT observation without writing SideState authority.

## Invariants preserved

- Master V2 / Double Play remain sole direction authority
- `entry_side=NONE` fail-closed (no implicit LONG)
- LONG path still opens on `+1`
- Default stepper (`honor_mapped_short_entry=False`) keeps classic long-only semantics
- `LIVE_AUTHORIZED=false`, `ORDERS=false`, Runtime Bridge `BOUND_NOT_ACTIVATED`

## Tests

`tests/backtest/test_canonical_short_binding_miswiring_repair_v1.py`

