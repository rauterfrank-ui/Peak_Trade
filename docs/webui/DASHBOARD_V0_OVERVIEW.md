# Peak_Trade Dashboard v0 — Watch-Only Overview

## Summary
- Scope: **Watch-only / read-only** Monitoring UI + API for Run-Artefakte.
- No-Live Safety: **keine** Trading-/Execution-Aktionen; keine mutierenden API-Methoden.
- Implementation (Server): Live Web Dashboard v0 (Composition Root + Watch Pages + API Router)
- Start Script: Live Web Dashboard Start Script

**Code Map (repo targets):**
- [Composition Root](../../src/live/web/app.py)
- [API v0 Router](../../src/live/web/api_v0.py)
- [API v0 Models](../../src/live/web/models_v0.py)
- [Start Script](../../scripts/live_web_server.py)

## Architektur (High-Level)
- **FastAPI App**: `create_app(...)` (Composition Root)
- **Watch Pages (HTML)**:
  - /watch (Runs-Liste)
  - /watch/runs/{run_id} (Run-Detail, server-rendered + minimal JS)
  - /sessions/{run_id} (Alias)
- **API (read-only, v0 Namespace)**: /api/v0/...
- **Safety Gate**: Middleware reject für mutierende Methoden auf `&#47;api&#47;...` (405)

## Datenquelle (Run-Artefakte)
Das Dashboard liest Run-Artefakte aus einem **Runs Directory** (Default im Start Script: live_runs).
Die v0.1B Operator-Doku nutzt für illustrative Inline-Code Tokens die Encoding-Regel `&#47;` (z.B. `live_runs&#47;`), siehe Runbook.

## Contracts & Docs
- [API Contract v0](./DASHBOARD_API_CONTRACT_v0.md)
- [Data Contract v0](./DASHBOARD_DATA_CONTRACT_v0.md)
- [Operator Runbook: Watch-Only Start → Finish](../ops/runbooks/RUNBOOK_DASHBOARD_WATCH_ONLY_START_TO_FINISH.md)
- Operator Runbook (v0.1B, Observability): ../ops/runbooks/RUNBOOK_DASHBOARD_WATCH_ONLY_V01B.md

## Observability Contract (Prometheus) — Service Health only

Peak_Trade Dashboard v0 bleibt **watch-only**. Prometheus-Metriken decken ausschließlich **Service Health / HTTP Layer** ab:

- `&#47;metrics` ist **immer** erreichbar, aber Peak_Trade-spezifische HTTP-Metriken (z.B. `peak_trade_http_requests_total`) werden nur instrumentiert, wenn `PEAK_TRADE_PROMETHEUS_ENABLED=1` gesetzt ist **und** `prometheus_client` im Environment verfügbar ist.
- Fail-open (Default): Wenn `prometheus_client` fehlt, liefert `&#47;metrics` ein Fallback-Signal `peak_trade_metrics_fallback 1` (HTTP 200).
- Strict Mode: Mit `REQUIRE_PROMETHEUS_CLIENT=1` liefert `&#47;metrics` bei fehlendem `prometheus_client` HTTP **503** (Scrape soll rot werden, statt “grün fake”).
- Labels sind cardinality-safe: `method`, `route` (Route-Template wie `&#47;api&#47;v0&#47;runs&#47;{run_id}`), `status_code`.
- Keine run-spezifischen IDs (z.B. `run_id`) in Prometheus-Labels.

Run-/Artefakt-Details bleiben im JSON API Contract unter `&#47;api&#47;v0&#47;...` (Snapshots, Events, Signals, Positions, Orders).

**Operator / Assets:**
- `docs/webui/observability/PROMETHEUS_SCRAPE_EXAMPLE.yml`
- `docs/webui/observability/DOCKER_COMPOSE_PROM_GRAFANA.yml`
- `docs/webui/observability/GRAFANA_DASHBOARD_PEAK_TRADE_WATCH_ONLY.json`

## Tests
- API Tests: tests/live/test_live_web_api_v0.py
