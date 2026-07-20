# Regime-gated standaside MR — DEVELOPMENT evaluation v1

## Status

`DEVELOPMENT_EVALUATION_COMPLETE` — single preregistered evaluation on the sealed
independent DEVELOPMENT_ONLY panel. Result class: **FAIL**.

## Binding

- Contract: `config/research/regime_gated_standaside_mr_preregistered_economic_hypothesis_measurement_contract_v1.json`
- Dataset: `pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1`
- Baseline: `bollinger_bands_v2_full_canonical_system_economic_binding_v1`
- Treatment: research-only `ENTRY_ELIGIBILITY_STANDASIDE_GATE`
- Decision segment: `final_development_confirmation` only
- Seed: `20220601`

## Gates

- `PROMOTION_ELIGIBLE=false`
- Economic offline gate unchanged/closed
- Holdout untouched
- No runtime / shadow / testnet / live / orders

## Evidence

`docs/evidence/evaluate_regime_gated_standaside_mr_development_v1/`
