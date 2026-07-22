# Cross-sectional relative-strength momentum v1 — strategy implementation only

## Status

`STRATEGY_IMPLEMENTATION_PRESENT` under operator GO `STRATEGY_IMPLEMENTATION_ONLY`.

## Binding

- Strategy identity: `CROSS_SECTIONAL_RELATIVE_STRENGTH_MOMENTUM_V1`
- Signal family: `CROSS_SECTIONAL_MOMENTUM`
- Directional form: `D_MUTUALLY_EXCLUSIVE_DIRECTIONAL_SELECTION`
- Implementation binding: `config&#47;research&#47;cross_sectional_relative_strength_momentum_v1_strategy_implementation_binding_v1.json`
- Frozen measurement contract digest: `2a2c0133c6f488b3aa5b14d9c85f7008b7711ad60f1d87e544330cec4c583869` (unmutated)
- Score: `src&#47;research&#47;cross_sectional_relative_strength_momentum_v1_score_v1.py`
- Selection: `src&#47;research&#47;cross_sectional_relative_strength_momentum_v1_selection_v1.py`

## Semantics

- Raw trailing log return fixed lookback (no vol normalization)
- `single_top1_by_score_desc` + `symmetric_top1_sign`
- Defaults: `lookback_N=20`, `rebalance_interval_bars=1`, `signal_lag_bars=1`, `min_eligible_members_for_rank=5`
- Grid candidates accepted as inputs only; no model selection in this slice
- Rank intent only; Double-Play remains sole directional transition authority

## Explicit non-actions

No evaluation, runner, holdout access, promotion, runtime, Master V2 mutation,
Double-Play authority change, or parameter optimization.

## Next step

`SEPARATE_OPERATOR_GO_FOR_MERGE_READINESS_AUDIT` then, separately,
pending-threshold resolution and development-evaluation GO.

---
docs_token: DOCS_TOKEN_CROSS_SECTIONAL_RELATIVE_STRENGTH_MOMENTUM_V1_STRATEGY_IMPLEMENTATION_ONLY_V1
STATUS: STRATEGY_IMPLEMENTATION_PRESENT
scope: research, offline-only, non-authorizing, strategy-implementation
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---
