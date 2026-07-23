# Cross-sectional intrabar CLV pressure continuation v1 — DEVELOPMENT evaluation entry point

## Status

`DEVELOPMENT_EVALUATION_EXECUTED_TERMINAL` under operator GO
`GO_CROSS_SECTIONAL_INTRABAR_CLOSE_LOCATION_PRESSURE_CONTINUATION_V1_BOUNDED_DEVELOPMENT_EVALUATION_EXECUTION_V1`.

## Result

`DEVELOPMENT_FAIL` — single authorized DEVELOPMENT slot consumed (`development_run_count=1`);
retry forbidden.

## Binding

- Entry point: `scripts&#47;research&#47;run_evaluate_cross_sectional_intrabar_close_location_pressure_continuation_development_v1.py`
- Binding: `config&#47;research&#47;cross_sectional_intrabar_close_location_pressure_continuation_v1_development_evaluation_entry_point_binding_v1.json`
- Evidence: `docs&#47;evidence&#47;evaluate_cross_sectional_intrabar_close_location_pressure_continuation_development_v1&#47;`
- Dataset: `pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1`
- Frozen params: `lookback_N=36`, `rebalance_interval_bars=6`, `signal_lag_bars=1`

## Explicit non-actions

No holdout access, no CSRHR mutation, no promotion, no runtime&#47;LIVE&#47;orders, no second development run,
no parameter retune.

## Next step

Separate operator GO for PR merge then terminal closeout.

---
docs_token: DOCS_TOKEN_CROSS_SECTIONAL_INTRABAR_CLOSE_LOCATION_PRESSURE_CONTINUATION_V1_DEVELOPMENT_EVALUATION_ENTRY_POINT_V1
STATUS: DEVELOPMENT_EVALUATION_EXECUTED_TERMINAL
scope: research, offline-only, non-authorizing, development-evaluation
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---
