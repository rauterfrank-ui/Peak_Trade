# Entry-effective MR eligibility — preregistered hypothesis and measurement v1

## Status

`DEFINITION_ONLY` — hypothesis and measurement contract preregistered; no evaluation.

## Binding

- Hypothesis: `ENTRY_EFFECTIVE_MR_ELIGIBILITY_MEAN_REVERSION_NON_BITCOIN_PERPETUALS_V1`
- Contract: `entry_effective_mr_eligibility_preregistered_economic_hypothesis_measurement_contract.v1`
- Dataset: `pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1` (`DEVELOPMENT_ONLY`)
- Multiple-testing budget: `1`
- Authorized later development evaluation runs: `1`
- Holdout: `offline_economic_reevaluation_sealed_long_panel_v1` opaque exclusion only
- Baseline: `bollinger_bands_v2_full_canonical_system_economic_binding_v1` (immutable)
- Treatment: `ENTRY_EFFECTIVE_PRE_ENTRY_ELIGIBILITY_FILTER` (not implemented in this slice)

## Filter (ex ante, deterministic)

Canonical `vol_regime_filter` ATR percentile mid-band from `config/config.toml` defaults:

- `vol_window=14`, `vol_method=atr`
- `vol_percentile_low=25`, `vol_percentile_high=75`
- `lookback_percentile=100`, `min_bars=30`, `regime_mode=false`, `invert=false`

`ENTRY_ELIGIBILITY_DIVERGENCE_REQUIRED=true` — absence ⇒ `RESULT_CLASS=FAIL`.

Not a rename/retune of the failed regime-gate (`identical_arms_gate_inactive_on_entries`).

## Gates

- `PROMOTION_ELIGIBLE=false`
- Economic offline gate unchanged/closed
- No runtime / shadow / testnet / live / orders
- `PRODUCTIVE_TRADING_LOGIC_CHANGED=false`
- `AUTHORITY_CHANGED=false`

## Next step

Review and merge this definition-only PR before any development evaluation.
