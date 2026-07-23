# Cross-sectional intrabar close-location pressure continuation v1 — strategy implementation only

## Status

`STRATEGY_IMPLEMENTATION_PRESENT` under operator GO
`GO_CROSS_SECTIONAL_INTRABAR_CLOSE_LOCATION_PRESSURE_CONTINUATION_V1_STRATEGY_IMPLEMENTATION_ONLY_V1`.

## Binding

- Strategy identity: `CROSS_SECTIONAL_INTRABAR_CLOSE_LOCATION_PRESSURE_CONTINUATION_V1`
- Signal family: `CROSS_SECTIONAL_INTRABAR_CLOSE_LOCATION_PRESSURE`
- Directional form: `D_MUTUALLY_EXCLUSIVE_DIRECTIONAL_SELECTION`
- Implementation binding: `config&#47;research&#47;cross_sectional_intrabar_close_location_pressure_continuation_v1_strategy_implementation_binding_v1.json`
- Frozen measurement contract digest: `2bc7e062d41bca4dee5c1b4a36c4e108903d5825cf5819f9214e8799cd98f859` (unmutated)
- Score: `src&#47;research&#47;cross_sectional_intrabar_close_location_pressure_continuation_v1_score_v1.py`
- Selection: `src&#47;research&#47;cross_sectional_intrabar_close_location_pressure_continuation_v1_selection_v1.py`

## Semantics

- Mean intrabar close-location value (CLV) fixed lookback (no vol normalization; no
  parameter grid)
- CLV bar: `0` if `high==low` else `(2*close-high-low)&#47;(high-low)`
- `single_top1_by_score_desc` + `symmetric_top1_sign`
- Frozen: `lookback_N=36`, `rebalance_interval_bars=6`, `signal_lag_bars=1`,
  `min_eligible_members_for_rank=5`
- Fail-closed: non-finite OHLC → ineligible; `score==0` → ineligible; eligible &lt; 5 →
  rebalance not evaluable
- Rank intent only; Double-Play remains sole directional transition authority

## Explicit non-actions

No evaluation, runner, holdout access, promotion, runtime, Master V2 mutation,
Double-Play authority change, parameter optimization, CSRHR continue/reuse/mutation,
path-efficiency retry, or development-run consumption.

## Next step

Separate operator GO for PR merge readiness, then separately a bounded
development-evaluation GO. `EVALUATION_AUTHORIZED` remains false;
`DEVELOPMENT_RUN_COUNT` remains 0.

---
docs_token: DOCS_TOKEN_CROSS_SECTIONAL_INTRABAR_CLOSE_LOCATION_PRESSURE_CONTINUATION_V1_STRATEGY_IMPLEMENTATION_ONLY_V1
STATUS: STRATEGY_IMPLEMENTATION_PRESENT
scope: research, offline-only, non-authorizing, strategy-implementation
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---
