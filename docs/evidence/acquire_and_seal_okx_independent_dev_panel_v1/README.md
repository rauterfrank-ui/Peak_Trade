# Acquire and seal OKX independent development panel v1

```text
SLICE=ACQUIRE_AND_SEAL_OKX_INDEPENDENT_DEV_PANEL_V1
BASE_SHA=46fd2fa1b397302539faa982f055f1df52a26f24
DATASET_ID=pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1
DECISION=SEALED_INDEPENDENT_DEV_PANEL
DEVELOPMENT_ONLY=true
HOLDOUT_FORBIDDEN=true
SEALED_HOLDOUT_CONTENT_INSPECTED=false
PUBLIC_OKX_ONLY=true
CREDENTIALS=false
ORDERS=false
PROMOTION_ELIGIBLE=false
RAW_IN_GIT=false
```

## Purpose

Execute the bounded public OKX acquisition defined by
`config/research/regime_gated_standaside_mr_independent_dev_panel_acquisition_contract_v1.json`
and seal an independent DEVELOPMENT_ONLY panel ending before the sealed holdout start.

## Result

| Field | Value |
|---|---|
| Common panel | `2022-06-01T03:55:17Z` .. `2023-08-16T05:55:00Z` (~441.08d) |
| Instruments acquired/valid | 46 / 46 |
| Gaps / dups / ordering errors | 0 / 0 / 0 |
| Root manifest sha256 | `c91ec9da31e6dc838ff16a2a47d91db8d428445084bd4a2960c7fb664e0b0ffa` |
| Raw archive | external under `PEAK_TRADE_DATA_ARCHIVE_ROOT` / `dev_pre_holdout_panel_v1_20260720T2052Z` |

## Non-blocking known issue

`LRC-USDT-SWAP` returns OKX `51001` on public endpoints and is excluded (same class of blocker as prior chrono seal).

## Explicit non-claims

No strategy run, no regime filter, no economic metrics, no promotion, no runtime activation.
