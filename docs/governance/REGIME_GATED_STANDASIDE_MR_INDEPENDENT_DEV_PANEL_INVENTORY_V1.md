# Independent development panel inventory — regime-gated standaside MR v1

## Status

`RESEARCH_STATUS=ACQUISITION_CONTRACT_REQUIRED`

## Hypothesis (research-only, not implemented)

`REGIME_GATED_STANDASIDE_MEAN_REVERSION_NON_BITCOIN_PERPETUALS_V1`

## Sealed holdout (opaque exclusion)

- Evidence ID: `offline_economic_reevaluation_sealed_long_panel_v1`
- Content inspection: forbidden in this slice
- Role: final audit only; no development / tuning / selection

## Inventory verdict

No existing local or versioned dataset fully satisfies independence + PIT +
non-Bitcoin futures PT1H development requirements with proven separation from the
sealed holdout window. Therefore no development panel was sealed.

## Acquisition contract (defined, not executed)

Owner config:

`config/research/regime_gated_standaside_mr_independent_dev_panel_acquisition_contract_v1.json`

Evidence pack:

`docs/evidence/inventory_independent_dev_panel_regime_gated_mr_v1/`

## Gates

- `PROMOTION_ELIGIBLE=false`
- Economic offline gate unchanged/closed
- No runtime / orders / testnet / shadow activation
