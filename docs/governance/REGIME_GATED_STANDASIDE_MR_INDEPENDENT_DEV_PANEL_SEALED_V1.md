# Independent OKX development panel sealed v1

## Status

`DECISION_CLASS=SEALED_INDEPENDENT_DEV_PANEL`

## Dataset

- ID: `pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1`
- Class: `DEVELOPMENT_ONLY` / `HOLDOUT_FORBIDDEN` / `RESEARCH_ONLY`
- Common panel: `2022-06-01T03:55:17Z` .. `2023-08-16T05:55:00Z` (PT1H)
- Width: 46 non-Bitcoin OKX linear USDT perpetual swaps

## Owners

- Acquisition contract: `config/research/regime_gated_standaside_mr_independent_dev_panel_acquisition_contract_v1.json`
- Seal registry: `config/research/regime_gated_standaside_mr_independent_dev_panel_seal_registry_v1.json`
- Evidence: `docs/evidence/acquire_and_seal_okx_independent_dev_panel_v1/`
- Scaffold reuse: `src/research/longer_chronological_pit_acquisition_v1/`

## Gates

- `PROMOTION_ELIGIBLE=false`
- Economic offline gate unchanged/closed
- Sealed holdout `offline_economic_reevaluation_sealed_long_panel_v1` not content-inspected
- No runtime / orders / testnet / shadow

## Next step

Separate operator GO for hypothesis binding definition only — still no sealed-holdout tuning.
