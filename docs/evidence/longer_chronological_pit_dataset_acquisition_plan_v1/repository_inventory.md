# Repository inventory — PIT / OKX research data chain

BASE_SHA=`b242db1b3b16582ff5b63153f647e980f1469e4a`  
Scope: read-only inventory. No downloads.

## 1. Current research dataset IDs

| ID | Role |
|---|---|
| `pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_v1` | Canonical OHLCV research panel used by post-#5348 &#47; #5349 &#47; #5350 |
| `pit_okx_linear_usdt_non_bitcoin_perpetual_universe_manifest_v1` | PIT universe manifest ref (cross-sectional non-BTC) |
| `pit_okx_linear_usdt_non_bitcoin_perpetual_cross_sectional_universe` | Universe policy id |
| `pit_okx_linear_usdt_non_bitcoin_open_interest_panel` &#47; self-accumulated variants | Separate OI research panels (not this acquisition target) |

Local staging root observed in evidence (operator machine path; not in git):

`...&#47;datasets&#47;admissible_futures&#47;pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_v1&#47;extended_chronological_v1`

## 2. PIT universe / listing / delisting owners

| Owner | Path | Role |
|---|---|---|
| Manifest schema | `src&#47;research&#47;pit_futures_universe_manifest_v1.py` | Members with `listing_time`, `delisting_time`, `eligible_from` &#47; `eligible_until`, exclusion reason codes including `NOT_LISTED_AT_SCORE_EPOCH`, `DELISTED_AT_SCORE_EPOCH`, `BITCOIN_DIRECTION_DISALLOWED`, `SPOT_MARKET` |
| Generator | `src&#47;research&#47;pit_futures_universe_manifest_generator_v1.py` | Build manifests |
| Validator | `src&#47;research&#47;pit_futures_universe_manifest_validator_v1.py` | Fail-closed validation |
| Production materialization | `src&#47;research&#47;pit_futures_universe_manifest_production_materialization_v1.py` | Offline materialization |
| Period binding | `src&#47;research&#47;pit_futures_universe_manifest_dataset_period_binding_v0.py` + `config&#47;research&#47;pit_futures_universe_manifest_dataset_period_binding_policy_v1.json` | Bind dataset period to universe policy |
| Survivorship flag | research bindings (e.g. relative strength) | `survivorship_bias_forbidden: true` |

## 3. Panel OHLCV / funding schemas

| Owner | Path | Notes |
|---|---|---|
| OHLCV panel core | `src&#47;research&#47;pit_okx_pt1h_panel_ohlcv_dataset_v1.py` | `BAR_GRANULARITY=PT1H`, `TIMEZONE=UTC`, `TIMESTAMP_SEMANTICS=utc_bar_close_exclusive_end`, alignment `common_utc_hourly_close_intersection_no_forward_fill`; validation codes for gaps, duplicates, OHLC inconsistency, bitcoin presence, future leakage |
| Funding panel | `src&#47;research&#47;pit_okx_pt1h_panel_funding_dataset_v1.py` | Funding companion schema |
| OI panel | `src&#47;research&#47;pit_okx_pt1h_panel_open_interest_dataset_v1.py` | Not required for initial chrono OHLCV plan |

## 4. Public fetch / acquisition surfaces already in repo

| Owner | Path | Endpoints / role |
|---|---|---|
| Bounded panel fetch | `src&#47;research&#47;cross_sectional_bounded_panel_fetch_v0.py` | `&#47;api&#47;v5&#47;market&#47;history-candles`, `&#47;api&#47;v5&#47;public&#47;funding-rate-history` with rate limiter |
| Full panel completeness evidence | `src&#47;research&#47;okx_full_panel_fetch_completeness_evidence_v0.py` | Completeness &#47; rate-limit policy evidence |
| OI public fetch | `src&#47;research&#47;okx_historical_open_interest_public_fetch_v0.py` and related self-accumulation modules | Pattern for idempotent public acquisition (OI, not OHLCV target) |

**This plan reuses these patterns; it does not start a bulk download.**

## 5. Fee &#47; slippage provenance (research measurement)

| Owner | Path | Notes |
|---|---|---|
| Cost config | `src&#47;backtest&#47;cost_config_v0.py` | Bound `taker_fee_bps`, entry&#47;exit `slippage_bps` |
| Cost application | `src&#47;backtest&#47;engine.py` + MV2 adapter | Cash-drag model; fills stay bar&#47;stop prices |
| Economic binding config | `config&#47;research&#47;bollinger_bands_v2_full_canonical_system_economic_binding_v1.json` | fee_bps=10, slippage_bps=5 (post-#5349 sample) |

Historical venue fee schedule reconstruction is a **blind spot** (see source matrix). Default plan: versioned fee policy table with explicit fallback provenance, not silent constant.

## 6. Reproducibility &#47; hashing

- Panel manifests carry `config_digest`, `implementation_digest`, `normalized_panel_digest`, `manifest_digest`, `source_provenance_digest`.
- Universe manifests use canonical SHA-256 digests (`compute_sha256_digest` in universe manifest module).
- Evidence `dataset_manifest.json` (post-#5348) seals digests for the 118-member, 2024-05..2024-09 panel.

## 7. Evidence anchors for this plan

- `docs&#47;evidence&#47;canonical_economic_reevaluation_post_5348_v1&#47;` — measurement repair + period blocker
- `docs&#47;evidence&#47;separate_read_only_robustness_attribution_audit_v1&#47;` — attribution; next action acquire longer PIT
- Merge #5350 on `b242db1b...`

## 8. Explicit non-owners (must not change in this workstream)

- Master V2 &#47; Double Play direction &#47; switch authority
- Risk &#47; sizing &#47; execution kernel
- Safety &#47; reconciliation &#47; live bridges
- Strategy parameters (`bb_period`, thresholds, stops)
