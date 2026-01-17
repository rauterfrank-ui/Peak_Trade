# Dashboard Data Contract — Observability v1 (Shadow → Live)

Diese Spezifikation definiert einen **Observability‑Contract v1** für Peak_Trade, der **Shadow** und **später Live** konsistent abbildet.

**Wichtig:**  
- Dieser Contract ist **additive‑only** (bestehende Felder/Labels nicht entfernen/umbennen).  
- **Metrics sind low‑cardinality**, Details gehören in Logs/Ledger.  
- Observability bleibt **watch‑only** (siehe `docs/webui/DASHBOARD_GOVERNANCE_NO_LIVE.md`).

---

## 1) Begriffe & Scope

- **Metrics (Prometheus)**: aggregierte Health/Rate/Latency Signale.
- **Logs/Ledger**: konkrete Events (high‑cardinality erlaubt).
- **WebUI/Watch‑Only**: read‑only Detailansicht (Run‑Snapshot, Timeline, Blotter).

Nicht im Scope:
- UI‑Trading, Run‑Start/Stop via UI, Live‑Enable Anleitungen.

---

## 2) Cardinality Regeln (hart)

- **Verboten als Prometheus‑Label**: `run_id`, `intent_id`, `client_order_id`, `broker_order_id`, `correlation_id` (und generell alle IDs).
- `symbol` nur, wenn strikt begrenzt (Whitelist / fixed set); sonst in Logs/Ledger.
- `stage`, `mode`, `exchange`, `reason` nur aus **kleinen** kontrollierten Sets.
- `route` ist nur ok, wenn es ein **Route‑Template** ist (cardinality‑safe), nicht eine konkrete URL mit IDs.

---

## 3) Observability v1 — Event/Ledger Schema (Logs)

Empfohlenes Minimal‑Event (JSONL; eine Zeile pro Event):

- `ts` (ISO8601)
- `mode`: `shadow` | `live`
- `run_id` (Session ID; high‑cardinality ok in Logs/Ledger)
- `stage`: `signal` | `intent` | `submit` | `ack` | `fill` | `cancel` | `risk_block` | `error`
- `strategy_id`
- `symbol` (optional, wenn nicht sensitive; ansonsten in detail payload)
- IDs (optional je Mode):
  - `intent_id`
  - `client_order_id`
  - `broker_order_id` (live only)
  - `correlation_id` (trace)
- State/Fields (best effort):
  - `status`, `qty`, `price`, `fee`, `reason`, `latency_ms`

Beispiel:

```json
{"ts":"2026-01-17T12:00:00Z","mode":"shadow","run_id":"run_123","stage":"intent","strategy_id":"ma_crossover_v1","symbol":"BTC/EUR","intent_id":"i_456","client_order_id":"co_789","status":"created","qty":1.0,"price":123.4,"fee":0.0,"reason":"","latency_ms":12}
```

---

## 4) Prometheus Metrics — Iststand (bereits im Repo vorhanden)

### 4.1 Watch‑Only Live Dashboard v0 (HTTP/Service‑Health)

Quelle: `src/live/web/metrics_prom.py` + `/metrics` in `src/live/web/app.py`

- `peak_trade_http_requests_total{method,route,status_code}`
- `peak_trade_http_request_duration_seconds_bucket{method,route,status_code,le}`
- `peak_trade_http_in_flight_requests`
- Labeled variants (const labels):
  - `peak_trade_http_requests_total_labeled{service,env,stack,method,route,status_code}`
  - `peak_trade_http_request_duration_seconds_labeled_bucket{service,env,stack,method,route,status_code,le}`
  - `peak_trade_http_in_flight_requests_labeled{service,env,stack}`
- Fallback, wenn `prometheus_client` nicht verfügbar (fail‑open):
  - `peak_trade_metrics_fallback 1`

Dashboard‑JSON (ready):
- `docs/webui/observability/GRAFANA_DASHBOARD_PEAK_TRADE_WATCH_ONLY.json`

### 4.2 Core Metrics (Resilience/Health, Prometheus optional)

Quelle: `src/core/metrics.py` (`MetricsCollector`, Namespace `peak_trade`)

Beispiele (je nach Laufzeit/Instrumentation):
- `peak_trade_circuit_breaker_state{name}`
- `peak_trade_circuit_breaker_failures_total{name}`
- `peak_trade_circuit_breaker_state_changes_total{name,from_state,to_state}`
- `peak_trade_rate_limit_hits_total{limiter,endpoint}`
- `peak_trade_rate_limit_rejections_total{limiter,endpoint}`
- `peak_trade_request_duration_seconds_bucket{operation,le}`
- `peak_trade_operation_failures_total{operation,error_type}`
- `peak_trade_operation_successes_total{operation}`
- `peak_trade_health_check_status{check_name}`

Hinweis: Diese Core‑Metriken sind **nicht** Order/Execution‑Pipeline‑Metriken; sie sind System/Resilience‑Signale.

---

## 5) Prometheus Metrics — v1 (Shadow/Live Pipeline) [Contract / geplant]

Diese Metriken sind der **Ziel‑Contract** für Shadow→Live‑Pipeline‑Observability.

### 5.1 Pipeline Events Counter

- Name: `peak_trade_pipeline_events_total`
- Type: Counter
- Labels (low‑cardinality):
  - `mode`: `shadow|live`
  - `stage`: `signal|intent|submit|ack|fill|cancel|risk_block|error`
  - `exchange`: z.B. `kraken` (oder `sim`)

### 5.2 Pipeline Latency Histogram

- Name: `peak_trade_pipeline_latency_seconds`
- Type: Histogram
- Labels:
  - `mode`
  - `edge`: `intent_to_ack|intent_to_fill|ack_to_fill` (kleines Set)
  - `exchange`

### 5.3 Risk Blocks Counter

- Name: `peak_trade_risk_blocks_total`
- Type: Counter
- Labels:
  - `mode`
  - `reason` (kleines, kontrolliertes Set; z.B. `max_notional|max_loss|cooldown|unknown`)

### 5.4 Feed Gaps Counter (optional)

- Name: `peak_trade_feed_gaps_total`
- Type: Counter
- Labels:
  - `mode`
  - `feed` (kleines Set, z.B. `ohlcv|ticker|trades`)

### 5.5 Run State Gauge (optional, low‑cardinality)

- Name: `peak_trade_run_state`
- Type: Gauge
- Labels:
  - `mode`
  - `state`: `idle|running|stopped|degraded|error` (kleines Set)

---

## 6) PromQL — MVS Panels (v1 Contract)

Diese Queries funktionieren **sobald** die v1 Pipeline‑Metriken implementiert sind:

1) Event throughput:
```promql
sum by (mode, stage) (rate(peak_trade_pipeline_events_total[5m]))
```

2) Error rate:
```promql
sum(rate(peak_trade_pipeline_events_total{stage="error"}[5m]))
/
sum(rate(peak_trade_pipeline_events_total[5m]))
```

3) Risk blocks:
```promql
sum by (mode, reason) (rate(peak_trade_risk_blocks_total[5m]))
```

4) Latency P95:
```promql
histogram_quantile(0.95, sum by (le, mode) (rate(peak_trade_pipeline_latency_seconds_bucket{edge="intent_to_ack"}[5m])))
```

---

## 7) Referenzen

- Runbook (Shadow→Live, Grafana): `docs/webui/observability/RUNBOOK_Peak_Trade_Grafana_Shadow_to_Live_Cursor_Multi_Agent.md`
- Observability Workflow (Grafana provisioning, docker-compose): `docs/webui/observability/DASHBOARD_WORKFLOW.md`
- Observability README (Iststand `/metrics` etc.): `docs/webui/observability/README.md`
