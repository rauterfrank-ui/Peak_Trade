# Futures Market Data Provenance Contract v0

## Purpose

This contract defines the minimum market-data provenance required before Peak_Trade can treat futures or perpetual market data as a governed futures-aware surface.

It supports the F2 Market Data Provenance stage in the Futures Capability Spec v0.

The contract exists to prevent dashboards, backtests, testnet paths, or evidence packets from confusing a displayed price, cached dataset, or provenance label with complete futures data readiness.

## Non-authority note

This is a docs-only provenance contract.

It does not implement a market-data model, exchange adapter, dashboard, backtest engine, testnet path, or Live path.

It does not grant Master V2 approval, Double Play authority, PRE_LIVE completion, First-Live readiness, operator authorization, production readiness, testnet execution permission, or Live permission.

It does not permit orders, exchange calls, market-data fetches, execution sessions, bounded-pilot sessions, Paper, Shadow, Testnet, or Live.

## Scope

This contract applies to market data used for futures, perpetual swaps, and derivative-like instruments.

It covers:

- displayed market data,
- OHLCV candles,
- last / mark / index prices,
- funding data,
- data freshness,
- source metadata,
- cache/write status,
- provenance references.

This contract does not authorize data fetching. It defines what must be known and recorded if futures market data is used later by a governed slice.

## Required data identity fields

| Field | Required | Description |
|---|---:|---|
| `dataset_id` | yes | Stable id for the market-data snapshot or stream descriptor. |
| `instrument_id` | yes | Instrument id bound to the futures metadata contract. |
| `exchange` | yes | Exchange or venue name. |
| `market_type` | yes | Explicit `futures`, `perpetual`, `swap`, `spot`, or documented equivalent. |
| `symbol` | yes | Exchange-facing symbol. |
| `interval` | conditional | Candle interval when OHLCV is used. |
| `time_range_start_utc` | conditional | Required for historical data. |
| `time_range_end_utc` | conditional | Required for historical data. |

Rules:

- `market_type` must not be inferred from `symbol` alone.
- `instrument_id` must map to a futures instrument metadata record before futures capability is claimed.
- Dashboard labels must show missing identity fields as missing, not supported.

## Required price fields

| Field | Required | Description |
|---|---:|---|
| `last_price_available` | yes | Whether last traded price is available. |
| `mark_price_available` | yes for futures/perps | Whether mark price is available. |
| `index_price_available` | yes for futures/perps | Whether index price is available. |
| `price_source` | yes | Source of price data. |
| `price_timestamp_utc` | yes if any price is available | Timestamp of the displayed/used price. |

Rules:

- Futures dashboards should distinguish last, mark, and index price.
- Liquidation or margin views must not use last price as mark price unless explicitly governed.
- Missing mark/index price must be visible before testnet/live-like paths.

## Required OHLCV fields

| Field | Required | Description |
|---|---:|---|
| `ohlcv_available` | yes | Whether OHLCV candles are available. |
| `candle_count` | conditional | Required when OHLCV is available. |
| `candle_interval` | conditional | Required when OHLCV is available. |
| `ohlcv_source` | conditional | Required when OHLCV is available. |
| `ohlcv_timestamp_utc` | conditional | Timestamp of last candle or dataset refresh. |

Rules:

- OHLCV data alone does not prove futures readiness.
- OHLCV source must distinguish spot, futures, perpetual, or unknown market type.
- Backtests must record candle source, interval, time range, and refresh timestamp.

## Required funding fields

| Field | Required | Description |
|---|---:|---|
| `funding_rate_available` | yes | Whether funding rate data is available. |
| `funding_rate` | conditional | Required when funding rate is available. |
| `next_funding_time_utc` | conditional | Required when provided by the venue. |
| `funding_interval` | conditional | Required for perpetuals when funding applies. |
| `funding_source` | conditional | Required when funding data is available. |

Rules:

- Perpetuals must expose funding-data availability.
- Backtests that ignore funding must mark futures realism incomplete.
- Dashboards may show funding as missing, but must not imply funding-aware support.

## Freshness / timestamp contract

| Field | Required | Description |
|---|---:|---|
| `last_refresh_utc` | yes | Last metadata/data refresh timestamp. |
| `max_allowed_staleness_seconds` | yes | Maximum staleness allowed by the consuming surface. |
| `freshness_status` | yes | `fresh`, `stale`, `expired`, `unknown`, or equivalent. |

Rules:

- Stale data may be displayed only with explicit stale labeling.
- Testnet/live-like paths must fail closed on expired or unknown required data freshness.
- Dashboard cards must show freshness status for futures-relevant prices and funding.

## Source / cache / write-surface contract

| Field | Required | Description |
|---|---:|---|
| `data_source` | yes | Exchange/API/cache/file/source identifier. |
| `fetch_mode` | yes | `static`, `fixture`, `cache_read`, `live_fetch`, `unknown`, or equivalent. |
| `cache_status` | yes | `none`, `read_only`, `write_enabled`, `written`, `unknown`, or equivalent. |
| `cache_path` | conditional | Required if cache is used. |
| `local_write_performed` | yes | Whether local writes occurred. |
| `artifact_write_performed` | yes | Whether report/artifact writes occurred. |
| `evidence_write_performed` | yes | Whether evidence writes occurred. |
| `s3_write_performed` | yes | Whether S3/external writes occurred. |
| `provenance_ref` | yes | Reference to provenance record or explicit `not_available`. |

Rules:

- Provenance-only construction is not equivalent to no local writes in caller paths.
- Read-only dashboard views must not call write-enabled fetch/cache paths unless a future governed slice explicitly allows it.
- Cache writes must be explicit in provenance.
- Evidence/archive writes require separate operator/governance approval.
- S3/external writes are out of scope unless a governed slice adds them.

## Dashboard display contract

A futures-aware dashboard may display market data only if source, freshness, and cache/write state are visible.

Required dashboard fields include:

- instrument id,
- exchange,
- market type,
- symbol,
- last price availability,
- mark price availability,
- index price availability,
- funding availability,
- freshness status,
- data source,
- fetch mode,
- cache status,
- local write status,
- provenance reference,
- no-live banner.

Dashboard status values should include:

- `fixture_only`,
- `cache_read_only`,
- `cache_write_enabled_do_not_call`,
- `live_fetch_prohibited_for_dashboard_v0`,
- `stale`,
- `unknown_source`,
- `unsupported_for_execution`.

The dashboard must not provide controls for orders, session starts, market-data refresh through write-enabled paths, testnet enablement, Live enablement, evidence writes, archive writes, risk-gate toggles, or kill-switch toggles.

## Backtest contract

A futures-realistic backtest must record:

- dataset id,
- instrument id,
- market type,
- OHLCV source,
- time range,
- candle interval,
- funding source and interval when applicable,
- cache/write status,
- fees/slippage assumptions,
- provenance reference.

Backtests must not claim futures realism when:

- futures market type is unknown,
- funding is missing for perpetuals without explicit incompleteness labeling,
- mark/index price assumptions are missing where required,
- cache/write provenance is unknown,
- instrument metadata is incomplete.

## Testnet contract

A futures testnet candidate requires:

- explicit testnet/sandbox data source,
- complete futures instrument metadata,
- mark/index/last price semantics,
- funding availability or explicit not-available state,
- freshness thresholds,
- cache/write policy,
- provenance record,
- risk/safety integration,
- operator approval.

A testnet label is not testnet data proof.

## Evidence / archive boundary

This contract does not authorize evidence capture.

Future evidence packets must record:

- dataset id,
- instrument id,
- git head,
- config version,
- data source,
- time range,
- funding source,
- freshness status,
- cache/write state,
- checksums if artifacts are captured,
- archive URI if approved,
- operator/reviewer signoff.

Repo docs alone cannot satisfy G4-G8.

## Unknown / missing field semantics

Unknown or missing fields must be explicit.

Allowed values:

- `unknown`
- `not_available`
- `not_applicable`
- `not_verified`

Rules:

1. Unknown values are acceptable for inventory and dashboard display.
2. Unknown required values are not acceptable for execution, testnet proof, or Live.
3. Backtests with unknown required data provenance must mark futures realism incomplete.
4. Missing provenance must not silently fall back to spot assumptions.
5. Missing funding must not be ignored for perpetuals without explicit labeling.

## Validation / future tests

Future tests should prove:

1. Dashboard futures cards expose source/freshness/cache status.
2. Write-enabled fetch/cache paths are not called by read-only dashboard endpoints.
3. Backtests cannot claim futures realism without required provenance fields.
4. Perpetual datasets expose funding availability.
5. Unknown market type fails closed for testnet/live-like consumers.
6. Provenance records distinguish local writes, artifact writes, evidence writes, and S3 writes.

## References

- [Futures Capability Spec v0](FUTURES_CAPABILITY_SPEC_V0.md)
- [Futures Instrument Metadata Contract v0](FUTURES_INSTRUMENT_METADATA_CONTRACT_V0.md)
- [Session env_name and exchange surfaces non-authority v0](SESSION_ENV_NAME_AND_EXCHANGE_SURFACES_NON_AUTHORITY_V0.md)
- [Futures Trading Readiness Runbook v0](../runbooks/futures/FUTURES_TRADING_READINESS_RUNBOOK_V0.md)
