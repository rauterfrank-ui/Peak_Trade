# Boundary attestation — sealed holdout non-access

## Opaque exclusion only

- Holdout evidence ID: `offline_economic_reevaluation_sealed_long_panel_v1`
- Holdout period (from prior registry / dataset_split_policy metadata only):
  `2023-08-16T05:55:00Z..2024-09-01T00:00:00Z`
- Holdout dataset ID (registry metadata only):
  `pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_chrono_3y_v1`

## Explicitly not done

- No read of files under `docs/evidence/offline_economic_reevaluation_sealed_long_panel_v1/`
- No inspection of holdout bars, metrics, instrument lists beyond already published registry fields
- No derivation of a development subset from holdout raw/normalized artifacts
- No tuning or hypothesis selection on the sealed panel

## Allowed inventory sources used

- Versioned research configs under `config/research/`
- Prior acquisition / probe / gap-analysis evidence packs outside the sealed holdout pack
- Local archive **metadata-only** paths under `peak_trade_data_archive` (period/count/hash fields)
- Hypothesis / split-policy artifacts from the archive-and-next-hypothesis pack
