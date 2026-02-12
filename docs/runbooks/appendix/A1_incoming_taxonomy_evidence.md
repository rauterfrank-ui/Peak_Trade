# A1 Incoming Taxonomy – Evidence

## Candidate source directories/files (existence check)

- OK: src
- OK: scripts
- OK: docs
- OK: config
- OK: tests

## Top-level src inventory

src/__init__.py
src/ai_orchestration
src/analytics
src/autonomous
src/backtest
src/core
src/data
src/docs
src/execution
src/execution_pipeline
src/execution_simple
src/exchange
src/experiments
src/features
src/forward
src/governance
src/infra
src/knowledge
src/live
src/live_eval
src/macro_regimes
src/market_sentinel
src/markets
src/meta
src/notifications
src/obs
src/observability
src/ops
src/orders
src/peak_trade
src/portfolio
src/regime
src/reporting
src/research
src/risk
src/risk_layer
src/scheduler
src/strategies
src/sweeps
src/theory
src/trigger_training
src/utils
src/webui

## Likely ingress keywords (ripgrep hits)

Keyword scan targets: `ingress`, `event`, `normalize`, `writer`, `jsonl`, `market_data`, `trade`, `fill`, `order`, `balance`, `position`, `ticker`, `book`, `ohlc`, `kline`, `websocket`, `rest`, `stream`, `snapshot`.

Relevant areas (file-level):

- **Market data / OHLC**: `src/data/kraken_live.py`, `src/data/kraken.py`, `src/data/providers/kraken_ccxt_backend.py`, `src/data/shadow/ohlcv_builder.py`, `src/data/feeds/`, `src/data/normalizer.py`, `src/data/contracts.py`
- **Execution / orders / fills**: `src/exchange/kraken_testnet.py`, `src/exchange/ccxt_client.py`, `src/execution/`, `src/orders/`, `src/execution/ledger/`, `src/execution/venue_adapters/`, `src/execution/broker/`, `src/execution/paper/`
- **Account / balance / position**: `src/execution/ledger/`, `src/live/portfolio_monitor.py`, `src/risk/portfolio.py`, `src/risk/position_sizer.py`
- **Ops / audit / run_id / metrics**: `src/live/audit.py`, `src/execution/live/audit.py`, `src/risk_layer/audit_log.py`, `src/obs/`, `src/live/web/metrics_prom.py`, `src/observability/`, `src/execution_pipeline/events_v0.py`, `src/execution_pipeline/telemetry.py`
- **Orchestration / shadow / testnet / pipeline**: `src/live/shadow_session.py`, `src/live/testnet_orchestrator.py`, `src/execution/live_session.py`, `src/execution/orchestrator.py`, `src/execution_pipeline/pipeline.py`, `src/execution/live/orchestrator.py`
- **Storage / jsonl / writer**: `src/data/shadow/jsonl_logger.py`, `src/meta/infostream/collector.py` (save_intel_event), `src/trigger_training/session_store.py`, `src/execution_pipeline/store.py`
- **Events (normalized / Intel)**: `src/meta/infostream/models.py` (IntelEvent), `src/meta/infostream/collector.py`, `src/execution_pipeline/events_v0.py`, `src/execution/events.py`

## Scripts (ingress entry points)

- `scripts/run_shadow_execution.py` – Shadow-Pipeline
- `scripts/run_testnet_session.py` – Testnet-Orders
- `scripts/check_live_readiness.py` – Readiness-Check (ENV/Creds)
- `scripts/run_registry_portfolio_backtest.py` – Kraken-Daten + Backtest
- `scripts/run_sweep.py`, `scripts/run_strategy_from_config.py` – Research/Backtest

## Config

- `config/config.toml`, `config/config.test.toml` – Exchange/Testnet, run_id-Kontext

## Next steps (Phase A1 checklist)

- [ ] For each domain: identify producer (module/service) and transport (WS/REST/file).
- [ ] Identify raw schema(s) and normalization targets (e.g. NormalizedEvent).
- [ ] Identify Shadow vs Live differences and gating points.
- [ ] Record storage writer format(s) + retention.
