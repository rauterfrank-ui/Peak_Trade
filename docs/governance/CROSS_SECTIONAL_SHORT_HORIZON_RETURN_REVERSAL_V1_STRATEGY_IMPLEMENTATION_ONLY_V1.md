# Cross-sectional short-horizon return-reversal v1 — strategy implementation only

## Status

`STRATEGY_IMPLEMENTATION_PRESENT` under operator GO
`GO_CROSS_SECTIONAL_SHORT_HORIZON_RETURN_REVERSAL_V1_STRATEGY_IMPLEMENTATION_ONLY_V1`.

## Binding

- Hypothesis ID: `CROSS_SECTIONAL_SHORT_HORIZON_RETURN_REVERSAL_NON_BITCOIN_PERPETUALS_V1`
- Strategy identity: `CROSS_SECTIONAL_SHORT_HORIZON_RETURN_REVERSAL_V1`
- Signal family: `CROSS_SECTIONAL_RETURN_REVERSAL`
- Directional form: `D_MUTUALLY_EXCLUSIVE_DIRECTIONAL_SELECTION`
- Implementation binding: `config&#47;research&#47;cross_sectional_short_horizon_return_reversal_v1_strategy_implementation_binding_v1.json`
- Frozen measurement contract digest: `3d983bbfa1db6c319f6c4399549679a5b7fd2d635d8e72d4452330da9059729a` (unmutated)
- Score: `src&#47;research&#47;cross_sectional_short_horizon_return_reversal_v1_score_v1.py`
- Selection: `src&#47;research&#47;cross_sectional_short_horizon_return_reversal_v1_selection_v1.py`

## Semantics

- Negated raw trailing log return fixed lookback (reversal polarity; no vol normalization)
- `score_i = -trailing_log_return`
- `single_top1_by_score_desc` + `symmetric_top1_sign`
- Frozen parameters: `lookback_N=24`, `rebalance_interval_bars=4`, `signal_lag_bars=1`, `min_eligible_members_for_rank=5`
- Positive top1 score → `LONG_TOP1` on relative loser; negative → `SHORT_TOP1`
- Rank intent only; Double-Play remains sole directional transition authority
- Backlog remains `OPEN_BACKLOG` / `PREREGISTERED_DEFINITION_ONLY`; `run_slot_consumed=false`

## Explicit non-actions

No evaluation, runner, holdout/sealed access, promotion, runtime, Master V2 mutation,
Double-Play authority change, Risk/Sizing change, automatic backlog selection,
production strategy selection, run-slot consumption, or economic PASS claim.

## Next step

Separate operator GO for bounded development evaluation (not authorized here).

---
docs_token: DOCS_TOKEN_CROSS_SECTIONAL_SHORT_HORIZON_RETURN_REVERSAL_V1_STRATEGY_IMPLEMENTATION_ONLY_V1
STATUS: STRATEGY_IMPLEMENTATION_PRESENT
scope: research, offline-only, non-authorizing, strategy-implementation
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---
