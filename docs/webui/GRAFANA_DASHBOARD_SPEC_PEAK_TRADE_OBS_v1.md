# Grafana Dashboard Spec — Peak_Trade Observability v1 (Shadow → Live)

Diese Spezifikation beschreibt ein **Grafana Dashboard** (Prometheus Datasource), das sowohl den **Iststand** (HTTP/Service‑Health) als auch den **v1 Ziel‑Contract** (Pipeline Stages Shadow→Live) abdeckt.

**Scope:** Watch‑only / read‑only Observability.  
**No‑Live:** Siehe `docs/webui/DASHBOARD_GOVERNANCE_NO_LIVE.md`.

---

## Datasource

- **Type:** Prometheus
- **Naming/Provisioning (Repo):**
  - Siehe `docs/webui/observability/grafana/provisioning/datasources/`

---

## Dashboard: Iststand (ready today)

### Option A — Import/Provision Existing Dashboard JSON (empfohlen)

- **JSON:** `docs/webui/observability/GRAFANA_DASHBOARD_PEAK_TRADE_WATCH_ONLY.json`
- **Metriken:** `peak_trade_http_*`
- **Typische Panels:**
  - RPS gesamt
  - RPS pro Route
  - Error Rate (Status‑Class Anteil)
  - In‑Flight Requests
  - Latency Quantiles pro Route
  - Top Routes by p95 latency

---

## Dashboard: v1 Pipeline (Shadow → Live) — Spec/Contract (requires instrumentation)

> Hinweis: Die folgenden Panels setzen voraus, dass die Metriken aus `docs/webui/DASHBOARD_DATA_CONTRACT_OBS_v1.md` implementiert sind.

### Variables (empfohlen)

- `mode`: `label_values(peak_trade_pipeline_events_total, mode)`
- `exchange`: `label_values(peak_trade_pipeline_events_total, exchange)`
- `stage`: `label_values(peak_trade_pipeline_events_total, stage)`

Optional (nur wenn streng begrenzt):
- `symbol`: `label_values(peak_trade_pipeline_events_total, symbol)`

### Panel 1 — Event Throughput by Stage

```promql
sum by (mode, stage) (rate(peak_trade_pipeline_events_total{exchange=~"$exchange"}[5m]))
```

### Panel 2 — Error Rate

```promql
sum(rate(peak_trade_pipeline_events_total{stage="error", exchange=~"$exchange"}[5m]))
/
sum(rate(peak_trade_pipeline_events_total{exchange=~"$exchange"}[5m]))
```

### Panel 3 — Risk Blocks by Reason

```promql
sum by (mode, reason) (rate(peak_trade_risk_blocks_total[5m]))
```

### Panel 4 — Latency P95 (intent → ack)

```promql
histogram_quantile(
  0.95,
  sum by (le, mode) (
    rate(peak_trade_pipeline_latency_seconds_bucket{edge="intent_to_ack", exchange=~"$exchange"}[5m])
  )
)
```

### Panel 5 — Feed Gaps (optional)

```promql
sum by (mode, feed) (rate(peak_trade_feed_gaps_total[15m]))
```

### Panel 6 — Run State (optional gauge)

```promql
sum by (mode, state) (peak_trade_run_state)
```

---

## Alerts (Vorschläge; disabled by default)

- **No events while run expected**
  - Expression:

```promql
sum(rate(peak_trade_pipeline_events_total{mode="shadow"}[5m])) == 0
```
- **Error rate spike**
  - Expression:

```promql
sum(rate(peak_trade_pipeline_events_total{stage="error"}[5m]))
/
sum(rate(peak_trade_pipeline_events_total[5m]))
> 0.01
```
- **Risk blocks spike**
  - Expression:

```promql
sum(rate(peak_trade_risk_blocks_total[5m])) > 0
```

---

## Referenzen

- Observability Workflow (Provisioning): `docs/webui/observability/DASHBOARD_WORKFLOW.md`
- Observability README (Iststand): `docs/webui/observability/README.md`
- Data Contract v1 (Names/Labels/Cardinality): `docs/webui/DASHBOARD_DATA_CONTRACT_OBS_v1.md`
- Runbook (Shadow→Live): `docs/webui/observability/RUNBOOK_Peak_Trade_Grafana_Shadow_to_Live_Cursor_Multi_Agent.md`
