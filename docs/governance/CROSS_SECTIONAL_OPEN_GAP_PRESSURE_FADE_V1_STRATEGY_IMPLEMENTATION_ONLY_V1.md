# Cross-sectional open-gap pressure fade v1 — strategy implementation only

## Status

`STRATEGY_IMPLEMENTATION_PRESENT` under operator GO
`GO_CROSS_SECTIONAL_OPEN_GAP_PRESSURE_FADE_V1_STRATEGY_IMPLEMENTATION_ONLY_V1`.

Implementation matches preregistration. Evaluation unauthorized and not executed.
Development run count remains 0. Run slot remains unconsumed.

## Binding

- Scope: `CROSS_SECTIONAL_OPEN_GAP_PRESSURE_FADE_V1_DEFINITION_ONLY_PREREGISTRATION_V1`
- Strategy identity: `CROSS_SECTIONAL_OPEN_GAP_PRESSURE_FADE_V1`
- Hypothesis: `CROSS_SECTIONAL_OPEN_GAP_PRESSURE_FADE_NON_BITCOIN_PERPETUALS_V1`
- Signal family: `CROSS_SECTIONAL_OPEN_GAP_PRESSURE`
- Directional form: `D_MUTUALLY_EXCLUSIVE_DIRECTIONAL_SELECTION`
- Dataset: `pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1`
- Implementation binding: `config&#47;research&#47;cross_sectional_open_gap_pressure_fade_v1_strategy_implementation_binding_v1.json`
- Frozen measurement contract digest: `7f8d361b597825428eecb2f6f791fcef07fe5a0dd92f9613f99b5d15e95b5768` (unmutated)
- Score: `src&#47;research&#47;cross_sectional_open_gap_pressure_fade_v1_score_v1.py`
- Selection: `src&#47;research&#47;cross_sectional_open_gap_pressure_fade_v1_selection_v1.py`

## Semantics

- `gap_b=log(open_b&#47;close_{b-1})`; `score_i=-mean(gap)` over frozen lookback
- `single_top1_by_score_desc` + `symmetric_top1_sign`
- Frozen: `lookback_N=30`, `rebalance_interval_bars=5`, `signal_lag_bars=1`,
  `min_eligible_members_for_rank=5`, `n=1`
- Fail-closed: non-finite&#47;non-positive prior close ineligible; `score==0` ineligible;
  eligible &lt; 5 → no selection
- Fade: gap-down → positive score → LONG; gap-up → negative score → SHORT
- Rank intent only; Double-Play remains sole directional transition authority
- Not a CLV pressure retry; no shared CLV utility; no values 36&#47;6

## Explicit non-actions

No evaluation, runner, holdout access, promotion, runtime, Master V2 mutation,
Double-Play authority change, parameter optimization, CSRHR continue&#47;reuse&#47;mutation,
path-efficiency retry, CLV pressure retry, development-run consumption, or
run-slot consumption.

## Next step

`EXPLICIT_DEVELOPMENT_EVALUATION_GO` (separate). Until then
`EVALUATION_AUTHORIZED` remains false and `DEVELOPMENT_RUN_COUNT` remains 0.

---
docs_token: DOCS_TOKEN_CROSS_SECTIONAL_OPEN_GAP_PRESSURE_FADE_V1_STRATEGY_IMPLEMENTATION_ONLY_V1
STATUS: STRATEGY_IMPLEMENTATION_PRESENT
scope: research, offline-only, non-authorizing, strategy-implementation
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---
