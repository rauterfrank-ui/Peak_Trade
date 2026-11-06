# Cross-sectional path-efficiency continuation v1 — strategy implementation only

## Status

`STRATEGY_IMPLEMENTATION_PRESENT` under operator GO
`GO_CROSS_SECTIONAL_PATH_EFFICIENCY_CONTINUATION_V1_STRATEGY_IMPLEMENTATION_ONLY_V1`.

## Binding

- Strategy identity: `CROSS_SECTIONAL_PATH_EFFICIENCY_CONTINUATION_V1`
- Signal family: `CROSS_SECTIONAL_PATH_EFFICIENCY`
- Directional form: `D_MUTUALLY_EXCLUSIVE_DIRECTIONAL_SELECTION`
- Implementation binding: `config&#47;research&#47;cross_sectional_path_efficiency_continuation_v1_strategy_implementation_binding_v1.json`
- Frozen measurement contract digest: `ffd67182ca8942c0975e3a864382ad55d657e625968c40d8fd63fac83a409ef9` (unmutated)
- Score: `src&#47;research&#47;cross_sectional_path_efficiency_continuation_v1_score_v1.py`
- Selection: `src&#47;research&#47;cross_sectional_path_efficiency_continuation_v1_selection_v1.py`

## Semantics

- Kaufman path-efficiency ratio times sign(net log return), fixed lookback (no vol
  normalization; no parameter grid)
- `single_top1_by_score_desc` + `symmetric_top1_sign`
- Frozen: `lookback_N=48`, `rebalance_interval_bars=8`, `signal_lag_bars=1`,
  `min_eligible_members_for_rank=5`
- Fail-closed: `path_sum==0` or `sign(net)==0` ineligible; eligible &lt; 5 →
  rebalance not evaluable
- Rank intent only; Double-Play remains sole directional transition authority

## Explicit non-actions

No evaluation, runner, holdout access, promotion, runtime, Master V2 mutation,
Double-Play authority change, parameter optimization, CSRHR continue/reuse/mutation,
or development-run consumption.

## Next step

Separate operator GO for PR merge readiness, then separately a bounded
development-evaluation GO. `EVALUATION_AUTHORIZED` remains false;
`DEVELOPMENT_RUN_COUNT` remains 0.

---
docs_token: DOCS_TOKEN_CROSS_SECTIONAL_PATH_EFFICIENCY_CONTINUATION_V1_STRATEGY_IMPLEMENTATION_ONLY_V1
STATUS: STRATEGY_IMPLEMENTATION_PRESENT
scope: research, offline-only, non-authorizing, strategy-implementation
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---
