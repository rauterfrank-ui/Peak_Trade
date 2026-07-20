# Regime-gated standaside MR — preregistered hypothesis and measurement v1

## Status

`DEFINITION_ONLY` — hypothesis and measurement contract preregistered; no evaluation.

## Binding

- Hypothesis: `REGIME_GATED_STANDASIDE_MEAN_REVERSION_NON_BITCOIN_PERPETUALS_V1`
- Dataset: `pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1` (`DEVELOPMENT_ONLY`)
- Multiple-testing budget: `1`
- Holdout: `offline_economic_reevaluation_sealed_long_panel_v1` opaque exclusion only
- Baseline: `bollinger_bands_v2_full_canonical_system_economic_binding_v1` (immutable)
- Treatment: `ENTRY_ELIGIBILITY_STANDASIDE_GATE` (not implemented in this slice)

## Gates

- `PROMOTION_ELIGIBLE=false`
- Economic offline gate unchanged/closed
- No runtime / shadow / testnet / live / orders

## Next step

Review and merge this definition-only PR before any development evaluation.
