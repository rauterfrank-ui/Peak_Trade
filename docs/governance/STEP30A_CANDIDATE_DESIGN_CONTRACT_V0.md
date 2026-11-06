# STEP30A Candidate Design Contract v0

## Candidate
- Strategy: `rsi_reversion` (`v1`)
- Owner: `src.strategies.rsi_reversion.RsiReversionStrategy`
- Signal semantics: `LONG_SHORT_REVERSION_-1_0_1`

## Ratified Strategy Parameters
- `rsi_window=14`
- `lower=30.0`
- `upper=70.0`
- `price_col=close`
- Forbidden field in `economic_evaluation_v1.strategy_params`: `use_trend_filter`

## Economic Evaluation Configuration
- Canonical config path:
  `config/ops/step30a_okx_inst_eth_usdt_perp_rsi_reversion_v1_economic_evaluation_v1.json`
- Config schema:
  `step30a_rsi_reversion_v1_economic_evaluation_admissibility_v1`

## Split Policy (Holdout-Separated)
- Training: `2026-04-02 10:07:00+00:00..2026-05-18 23:59:00+00:00`
- Validation: `2026-05-19 00:00:00+00:00..2026-06-16 23:59:00+00:00`
- Holdout/OOS: `2026-06-17 10:07:00+00:00..2026-07-01 10:07:00+00:00`
- Contract condition: training and validation both end before holdout start

## Dataset v2 and Placeholders
- Dataset path:
  `/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/datasets/admissible_futures/inst-eth-usdt-perp/v2/bars.parquet`
- Placeholder digests (to be replaced post-ingestion):
  - `PLACEHOLDER_V2_DATASET_DIGEST`
  - `PLACEHOLDER_V2_MANIFEST_DIGEST`
  - `PLACEHOLDER_SIZING_CONFIG_DIGEST`

## Authority Constraints
- `evaluation_authorized=false`
- `promotion_authorized=false`
- `runtime_authorized=false`
