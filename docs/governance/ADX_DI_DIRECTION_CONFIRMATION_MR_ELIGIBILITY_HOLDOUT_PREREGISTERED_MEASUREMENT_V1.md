# ADX DI direction confirmation MR eligibility — holdout preregistration v1

## Status

`DEFINITION_ONLY_HOLDOUT_PREREGISTERED` — holdout measurement contract preregistered;
no holdout execution; no holdout data access.

## Binding

- Hypothesis: `ADX_DI_DIRECTION_CONFIRMATION_MR_ENTRY_ELIGIBILITY_NON_BITCOIN_PERPETUALS_V1`
- Development result: `PASS` / `ALL_PASS_REQUIRES_MET` (run count `1` / limit `1`)
- Holdout run count now: `0`
- Holdout run limit: `1`
- Retry / restart / post-result tuning: forbidden
- Dataset: `pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_chrono_3y_v1`
  (`SEALED_HOLDOUT_FINAL_AUDIT_ONLY`)
- Opaque evidence ID: `offline_economic_reevaluation_sealed_long_panel_v1`
- Panel (from existing SSOT only): `2023-08-16T05:55:00Z` .. `2024-09-01T00:00:00Z`
- Universe: OKX Linear-USDT Non-Bitcoin Perpetuals PT1H (BTC excluded; Spot excluded)
- Baseline: `bollinger_bands_v2_full_canonical_system_economic_binding_v1` (immutable)
- Treatment: identical frozen Wilder ADX(14) +DI/-DI direction-confirmation filter
- Primary decision metric: `NET_PROFIT_FACTOR`
- Costs: fee `10` bps, slippage `5` bps, half-spread `5` bps, stop `2.5%`
- Minimum trade count: `50`; max trade-count reduction vs control: `0.5`

## Split digest source

Holdout split digest is computed from existing registry metadata only
(acquisition opaque exclusion + dataset_split_policy + bollinger sealed-panel
archive). No sealed holdout content inspection.

## Execution gate

- Definition-only PR does **not** authorize holdout execution
- Requires separate explicit operator GO (`PEAK_TRADE_ADX_DI_HOLDOUT_EXECUTION_GO=true`)
- Declared future runner path is frozen in the contract and is **not** present /
  authorized in this slice
- Development contract remains `holdout_forbidden=true`

## Terminal transitions

`PASS` / `FAIL` / `INCONCLUSIVE` / `ARTIFACT_OR_EXECUTION_FAILURE_NO_RERUN` are all
terminal, consume the single holdout run, keep the economic offline gate closed,
forbid promotion/runtime/orders, and forbid reopen without a new hypothesis ID.

## Gates

- `PROMOTION_ELIGIBLE=false`
- Economic offline gate unchanged/closed regardless of future holdout result
- No runtime / shadow / paper / testnet / live / orders
- `PRODUCTIVE_TRADING_LOGIC_CHANGED=false`
- `AUTHORITY_CHANGED=false`
- `NO HOLDOUT EXECUTED`

## Next step

Review and merge this definition-only holdout preregistration PR, then request a
separate operator GO for exactly one holdout run.
