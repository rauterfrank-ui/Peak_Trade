# Phase A1 – Incoming Taxonomy (Draft)

> Generated from repo keyword scan. Refine manually by following evidence links.

## Taxonomy Table

| Domain | Ingress Sources (files) | Notes/Next step |
|---|---|---|
| `account` | src/execution/ledger/valuation.py<br>src/execution/ledger/models.py<br>src/execution/ledger/engine.py<br>src/live/portfolio_monitor.py<br>src/risk/portfolio.py<br>src/risk/position_sizer.py<br>src/execution/position_ledger.py | Validate: balance/position events from ledger + exchange; identify producer and schema. |
| `execution` | src/exchange/kraken_testnet.py<br>src/exchange/ccxt_client.py<br>src/orders/base.py<br>src/orders/exchange.py<br>src/execution/ledger/<br>src/execution/broker/<br>src/execution/venue_adapters/<br>src/execution/paper/<br>src/execution/live_session.py<br>src/execution/order_ledger.py<br>src/execution/events.py | Validate: order_intent, order_result, fill; Shadow vs Live gating. |
| `market_data` | src/data/kraken_live.py<br>src/data/kraken.py<br>src/data/providers/kraken_ccxt_backend.py<br>src/data/shadow/ohlcv_builder.py<br>src/data/feeds/<br>src/data/normalizer.py<br>src/data/contracts.py | Validate: ohlcv, ticker payload shapes; REST vs future WS; sensitivity (none for public). |
| `ops` | src/live/audit.py<br>src/execution/live/audit.py<br>src/risk_layer/audit_log.py<br>src/obs/<br>src/live/web/metrics_prom.py<br>src/observability/<br>src/execution_pipeline/events_v0.py<br>src/execution_pipeline/telemetry.py<br>src/ops/evidence.py | Validate: run_id, metrics, alert, config_change; retention and writer. |
| `orchestration` | src/live/shadow_session.py<br>src/live/testnet_orchestrator.py<br>src/execution/live_session.py<br>src/execution/orchestrator.py<br>src/execution_pipeline/pipeline.py<br>src/execution/live/orchestrator.py | Validate: pipeline events, layer triggers; single ingress tap points. |
| `storage` | src/data/shadow/jsonl_logger.py<br>src/meta/infostream/collector.py<br>src/trigger_training/session_store.py<br>src/execution_pipeline/store.py | Validate: writer format (JSONL/Parquet), checksum/sha256, allowlist for Artifact Resolver. |

## Checklist

- [ ] For each domain: identify producer (module/service) and transport (WS/REST/file).
- [ ] Identify raw schema(s) and normalization targets.
- [ ] Identify Shadow vs Live differences and gating points.
- [ ] Record storage writer format(s) + retention.

## Source / Kind / Sensitivity (draft)

| Source | Kind (candidate) | Sensitivity |
|--------|------------------|-------------|
| Kraken REST (public) | ohlcv, ticker | none |
| Kraken REST (private) | order_result, balance | risk_strat_raw / ops_internal |
| Shadow / Testnet runner | order_intent, order_result, metrics | ops_internal |
| Intel/Infostream | metrics, alert, transcript | ops_internal |
| CI / test health | metrics, config_change | none / ops_internal |
| Config files | config_change | ops_internal (no secrets in events) |
