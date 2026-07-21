# ADX DI direction confirmation MR eligibility — holdout preregistration v2

## Status

`DEFINITION_ONLY_HOLDOUT_PREREGISTERED` — new independently versioned holdout
measurement contract preregistered; no holdout execution; no holdout data access.

## Binding

- Hypothesis / evaluation ID: `ADX_DI_DIRECTION_CONFIRMATION_MR_ENTRY_ELIGIBILITY_NON_BITCOIN_PERPETUALS_HOLDOUT_V2`
- New evaluation, not a V1 rerun: `true`
- Predecessor V1 hypothesis: `ADX_DI_DIRECTION_CONFIRMATION_MR_ENTRY_ELIGIBILITY_NON_BITCOIN_PERPETUALS_V1`
- Predecessor V1 state: terminal `ARTIFACT_OR_EXECUTION_FAILURE_NO_RERUN` (run count `1/1`)
- Predecessor V1 rationale preserved: MV2 replay signal-index mismatch after sealed
  panel data access; primary economic metrics were not produced
- Repair context: generic MV2 replay signal-index binding contract repaired on main
  (`55757341740de5be7413da5c9c4e76173ca4278a` / PR #5387)
- Development result (unchanged): `PASS` / `ALL_PASS_REQUIRES_MET` (run count `1` / limit `1`)
- Holdout V2 run count now: `0`
- Holdout V2 run limit: `1`
- Identical fachliche ADX-DI hypothesis and identical preregistered economic
  pass/fail rules as holdout V1
- No post-hoc threshold optimization
- Retry / restart / post-result tuning: forbidden
- Dataset: `pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_chrono_3y_v1`
  (`SEALED_HOLDOUT_FINAL_AUDIT_ONLY`; sealed dataset unchanged)
- Opaque evidence ID: `offline_economic_reevaluation_sealed_long_panel_v1`
- Panel (from existing SSOT only): `2023-08-16T05:55:00Z` .. `2024-09-01T00:00:00Z`
- Universe: OKX Linear-USDT Non-Bitcoin Perpetuals PT1H (BTC excluded; Spot excluded)
- Baseline: `bollinger_bands_v2_full_canonical_system_economic_binding_v1` (immutable)
- Treatment: identical frozen Wilder ADX(14) +DI/-DI direction-confirmation filter
- Primary decision metric: `NET_PROFIT_FACTOR`
- Costs: fee `10` bps, slippage `5` bps, half-spread `5` bps, stop `2.5%`
- Minimum trade count: `50`; max trade-count reduction vs control: `0.5`
- Frozen preregistration digest: `4d1ec324977e33a808d40778548523b95df472b72f3d9133fcdf606a4796c332`
- Frozen holdout split digest: `e29eeb4e9d264e1529a0c7419d707ce84df7919ee6ed95a833612fca46a7184d`

## Split digest source

Holdout split digest is computed from existing registry metadata only
(acquisition opaque exclusion + dataset_split_policy + bollinger sealed-panel
archive). No sealed holdout content inspection.

## Execution gate

- Definition-only PR does **not** authorize holdout execution
- Requires separate explicit operator GO (`PEAK_TRADE_ADX_DI_HOLDOUT_V2_EXECUTION_GO=true`) after merge
- Declared future runner path is frozen in the contract and is **not** present /
  authorized in this slice
- Development contract remains `holdout_forbidden=true`
- Holdout V1 remains terminal and must not be re-executed

## Terminal transitions

`PASS` / `FAIL` / `INCONCLUSIVE` / `ARTIFACT_OR_EXECUTION_FAILURE_NO_RERUN` are all
terminal for V2, consume the single V2 holdout run, keep the economic offline gate
closed, forbid promotion/runtime/orders, and forbid reopen without a new hypothesis ID.

## Gates

- `PROMOTION_ELIGIBLE=false`
- Economic offline gate unchanged/closed regardless of future holdout result
- No runtime / shadow / paper / testnet / live / orders
- `PRODUCTIVE_TRADING_LOGIC_CHANGED=false`
- `PRODUCTION_STRATEGY_SEMANTICS_CHANGED=false`
- `DOUBLE_PLAY_AUTHORITY_CHANGED=false`
- `RISK_SIZING_EXECUTION_SEMANTICS_CHANGED=false`
- `AUTHORITY_CHANGED=false`
- `NO HOLDOUT EXECUTED`
- `NO HOLDOUT DATA ACCESSED`

## Next step

Review and merge this definition-only holdout v2 preregistration PR, then request a
separate operator GO for exactly one holdout v2 run.
