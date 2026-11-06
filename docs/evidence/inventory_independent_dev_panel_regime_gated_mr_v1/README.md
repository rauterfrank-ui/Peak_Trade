# Inventory — independent development panel for regime-gated MR v1

```text
SLICE=INVENTORY_INDEPENDENT_DEV_PANEL_REGIME_GATED_MR_V1
BASE_SHA=cc5e058df264d5bf4bcd4c20bc94cd58fd5ce570
HYPOTHESIS=REGIME_GATED_STANDASIDE_MEAN_REVERSION_NON_BITCOIN_PERPETUALS_V1
SEALED_HOLDOUT_ID=offline_economic_reevaluation_sealed_long_panel_v1
SEALED_HOLDOUT_CONTENT_INSPECTED=false
NETWORK_ACQUISITION=false
RESEARCH_STATUS=ACQUISITION_CONTRACT_REQUIRED
PROMOTION_ELIGIBLE=false
ECONOMIC_GATE_OPENED=false
IMPLEMENTATION=false
RUNTIME=false
ORDERS=false
```

## Purpose

Fail-closed inventory only: determine whether a temporally and provenance-independent
development panel already exists for the research-only hypothesis
`REGIME_GATED_STANDASIDE_MEAN_REVERSION_NON_BITCOIN_PERPETUALS_V1`, outside the sealed
holdout. No acquisition, no tuning, no strategy code.

## Result

No suitable existing independent development panel was proven. A bounded acquisition
contract is defined and **not** executed:

- Config: `config/research/regime_gated_standaside_mr_independent_dev_panel_acquisition_contract_v1.json`
- Proposed dataset ID: `pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1`
- Proposed period end-exclusive: `2023-08-16T05:55:00Z` (before sealed holdout start from registry metadata)

## Inventory sources (non-holdout)

- Sealed-lifecycle acquisition evidence (common panel starts at holdout window)
- History-depth probe evidence (no materialized OHLCV panel)
- Prior short chronological research panel metadata (overlaps holdout calendar)
- Local `peak_trade_data_archive` metadata-only listing (`PEAK_TRADE_DATA_ARCHIVE_ROOT` unset)

## Hard boundary

Sealed holdout pack content was not opened. Only the opaque evidence ID and already
published registry period/dataset fields were used as exclusion references.
