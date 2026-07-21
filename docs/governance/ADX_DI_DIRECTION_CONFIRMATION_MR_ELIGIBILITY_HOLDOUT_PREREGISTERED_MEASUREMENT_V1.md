# ADX DI direction confirmation MR eligibility — holdout preregistration / evaluation v1

## Status

`HOLDOUT_EVALUATION_EXECUTED_TERMINAL` — single authorized holdout run executed and
terminalized as `ARTIFACT_OR_EXECUTION_FAILURE_NO_RERUN`. No retry. Economic offline
gate remains closed. No runtime / orders / strategy activation.

## Binding

- Hypothesis: `ADX_DI_DIRECTION_CONFIRMATION_MR_ENTRY_ELIGIBILITY_NON_BITCOIN_PERPETUALS_V1`
- Development result: `PASS` / `ALL_PASS_REQUIRES_MET` (run count `1` / limit `1`)
- Holdout run count now: `1`
- Holdout run limit: `1`
- Holdout result class: `ARTIFACT_OR_EXECUTION_FAILURE_NO_RERUN`
- Terminal reason: MV2 replay signal-index mismatch after sealed panel data access
- Retry / restart / post-result tuning: forbidden
- Dataset: `pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_chrono_3y_v1`
  (`SEALED_HOLDOUT_FINAL_AUDIT_ONLY`)
- Opaque evidence ID: `offline_economic_reevaluation_sealed_long_panel_v1`
- Panel (from existing SSOT only): `2023-08-16T05:55:00Z` .. `2024-09-01T00:00:00Z`
- Universe: OKX Linear-USDT Non-Bitcoin Perpetuals PT1H (BTC excluded; Spot excluded)
- Primary decision metric: `NET_PROFIT_FACTOR`
- Frozen preregistration digest: `014a6955354be19d0abbae65269a816743347975647b448f58ea61ad37647e6f`
- Frozen holdout split digest: `e29eeb4e9d264e1529a0c7419d707ce84df7919ee6ed95a833612fca46a7184d`

## Evidence

- Evaluation evidence: `docs/evidence/evaluate_adx_di_direction_confirmation_mr_eligibility_holdout_v1/`
- Preregistration evidence (definition-only historical): `docs/evidence/preregister_adx_di_direction_confirmation_mr_eligibility_holdout_v1/`

## Gates

- `PROMOTION_ELIGIBLE=false`
- Economic offline gate unchanged/closed
- No runtime / shadow / paper / testnet / live / orders
- `PRODUCTIVE_TRADING_LOGIC_CHANGED=false`
- `AUTHORITY_CHANGED=false`
- Second holdout run forbidden

## Next step

Review the terminal holdout evidence PR. Do **not** re-run the holdout evaluation.
