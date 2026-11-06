# Momentum V2 vol-scaled — strategy implementation + Development-eval prep v1

Status: `STRATEGY_IMPLEMENTATION_PRESENT` / Development evaluation **unauthorized**

## Selection

- Hypothesis: `MOMENTUM_V2_VOLATILITY_SCALED_OWN_INSTRUMENT_CONTINUATION_NON_BITCOIN_PERPETUALS_V1`
- Strategy identity: `MOMENTUM_V2_VOLATILITY_SCALED_OWN_INSTRUMENT_CONTINUATION_V1`
- Operator selection authorized: `true`
- Near-duplicate verdict: `MATERIALLY_DISTINCT`

## Scope

- Offline vol-scaled ENTRY&#47;EXIT event emitter (LONG entry only; exit event; no short entry)
- Frozen parameters: lookback=20, entry_z=1.0, exit_z=0.0, signal_lag_bars=1
- Dataset binding: `pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1`
- Realistic costs bound: fee 10 bps&#47;side, slippage 5 bps&#47;side
- Development evaluation runner prepared but fail-closed without separate GO
- Development run slot available and unconsumed

## Forbidden

- No Development evaluation execution in this slice
- No Holdout &#47; Sealed access
- No Runtime &#47; Scheduler &#47; Orders &#47; promotion &#47; activation
- No registry `momentum_1h` &#47; `MomentumStrategy` mutation
- No `momentum_1h&#47;v2` execution
- No CSRHR reopen
- No Master V2 &#47; Double-Play &#47; Risk authority mutation

## SSOT

- Selection: `config&#47;research&#47;momentum_v2_volatility_scaled_own_instrument_continuation_v1_operator_selection_record_v1.json`
- Near-duplicate gate: `config&#47;research&#47;momentum_v2_volatility_scaled_own_instrument_continuation_v1_near_duplicate_gate_v1.json`
- Implementation binding: `config&#47;research&#47;momentum_v2_volatility_scaled_own_instrument_continuation_v1_strategy_implementation_binding_v1.json`
- Dev-eval entry point: `config&#47;research&#47;momentum_v2_volatility_scaled_own_instrument_continuation_v1_development_evaluation_entry_point_binding_v1.json`
- Signal: `src&#47;research&#47;momentum_v2_volatility_scaled_own_instrument_continuation_v1_signal_v1.py`

---
docs_token: DOCS_TOKEN_MOMENTUM_V2_VOL_SCALED_STRATEGY_IMPLEMENTATION_AND_DEV_EVAL_PREP_V1
STATUS: STRATEGY_IMPLEMENTATION_PRESENT_DEV_EVAL_UNAUTHORIZED
scope: research, offline-only, non-authorizing
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---
