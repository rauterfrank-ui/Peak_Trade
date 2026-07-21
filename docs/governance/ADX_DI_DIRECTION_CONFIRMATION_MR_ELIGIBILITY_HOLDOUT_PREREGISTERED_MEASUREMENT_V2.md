# ADX DI direction confirmation MR eligibility — holdout evaluation v2

## Status

`HOLDOUT_EVALUATION_EXECUTED_TERMINAL` — independently versioned holdout evaluation
executed once and terminated as `FAIL` / `NET_PROFIT_FACTOR_NOT_IMPROVED`.

## Binding

- Hypothesis / evaluation ID: `ADX_DI_DIRECTION_CONFIRMATION_MR_ENTRY_ELIGIBILITY_NON_BITCOIN_PERPETUALS_HOLDOUT_V2`
- New evaluation, not a V1 rerun: `true`
- Predecessor V1 hypothesis: `ADX_DI_DIRECTION_CONFIRMATION_MR_ENTRY_ELIGIBILITY_NON_BITCOIN_PERPETUALS_V1`
- Predecessor V1 state: terminal `ARTIFACT_OR_EXECUTION_FAILURE_NO_RERUN` (run count `1&#47;1`)
- Holdout V2 result class: `FAIL`
- Holdout V2 reason: `NET_PROFIT_FACTOR_NOT_IMPROVED`
- Holdout V2 run count: `1`
- Holdout V2 run limit: `1`
- Primary metrics produced: `true`
- Frozen preregistration digest: `4d1ec324977e33a808d40778548523b95df472b72f3d9133fcdf606a4796c332`
- Frozen holdout split digest: `e29eeb4e9d264e1529a0c7419d707ce84df7919ee6ed95a833612fca46a7184d`
- Evidence: `docs&#47;evidence&#47;evaluate_adx_di_direction_confirmation_mr_eligibility_holdout_v2&#47;`

## Gates

- `PROMOTION_ELIGIBLE=false`
- Economic offline gate unchanged/closed
- No runtime / shadow / paper / testnet / live / orders
- `PRODUCTIVE_TRADING_LOGIC_CHANGED=false`
- `PRODUCTION_STRATEGY_SEMANTICS_CHANGED=false`
- `DOUBLE_PLAY_AUTHORITY_CHANGED=false`
- `RISK_SIZING_EXECUTION_SEMANTICS_CHANGED=false`
- Retry / restart / post-result tuning: forbidden
- V1 rerun: forbidden

## Next step

`REVIEW_TERMINAL_HOLDOUT_FAIL_NO_RETRY`
