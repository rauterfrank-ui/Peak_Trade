# Bypass Identity

Source of `CONFIRMED_BYPASS_COUNT=1` (merged audits):

- `docs&#47;evidence&#47;bollinger_entry_side_canonical_authority_read_only_audit_v1&#47;bypass_and_competing_authority_findings.md`
- restated in plan `docs&#47;evidence&#47;bollinger_entry_side_canonical_composition_slice_plan_v1&#47;`

| Field | Value |
|-------|-------|
| File | `src&#47;backtest&#47;engine.py` |
| Symbol | `BacktestEngine.run_realistic` |
| Behavior | `signal == 1` → LONG ENTRY; `signal == -1` → EXIT open long |
| Docstring | `1=Buy, -1=Sell, 0=Hold` (Sell = exit, not short open) |
| OBL_B07 flags | `CLASSIC_LONG_IS_CANONICAL=false`, `CLASSIC_LONG_PROPAGATES_TO_INTEGRATED=false` |
| Sets `StrategyEntrySideCarrierV1`? | **No** |
| Uses `transition_state`? | **No** |
| Uses composition matrix? | **No** |

This is the sole confirmed bypass counted by the authority audit.
