# Shadow MVS Contract — Observability (Watch-Only, Local)
**Version:** 1.0  
**Scope:** Shadow-MVS local backbone (Mock Exporter → Prometheus-local → Grafana-only)  
**Mode:** Snapshot-only (kein Watch), governance-safe, **NO-LIVE**

Dieses Dokument ist die **Single Source of Truth** für den lokalen Shadow-MVS Observability-Stack.  
Es beschreibt Ports/Endpoints, Prometheus Job-Contract, Grafana Provisioning, Golden Queries und Failure-Mappings (→ Phase F).

---

## 1) Ports & Endpoints (Contract)

| Komponente | Zweck | Endpoint |
|---|---|---|
| Shadow-MVS Exporter (Mock) | Metriken Quelle | `http:&#47;&#47;127.0.0.1:9109&#47;metrics` |
| Prometheus-local | Scrape + Query API | `http:&#47;&#47;127.0.0.1:9092` |
| Prometheus Targets UI | Target Status | `http:&#47;&#47;127.0.0.1:9092&#47;targets` |
| Grafana-only | Dashboard UI | `http:&#47;&#47;127.0.0.1:3000` |

Start/Stop/Verify:
- Up: `bash scripts&#47;obs&#47;shadow_mvs_local_up.sh`
- Verify: `bash scripts&#47;obs&#47;shadow_mvs_local_verify.sh`
- Down: `bash scripts&#47;obs&#47;shadow_mvs_local_down.sh`

---

## 2) Prometheus Job Contract

**Job Name (hart):**
- `job="shadow_mvs"`

**UP muss 1 sein:**
- `up{job="shadow_mvs"} == 1`

**Hinweis (Snapshot Race nach `up`):**
- Direkt nach `bash scripts&#47;obs&#47;shadow_mvs_local_up.sh` kann `http:&#47;&#47;127.0.0.1:9092&#47;api&#47;v1&#47;targets` kurz **leer** sein (keine `activeTargets`), obwohl `&#47;-&#47;ready` bereits OK ist.
- `scripts&#47;obs&#47;shadow_mvs_local_verify.sh` nutzt dafür **bounded retries** (snapshot-only, kein watch) und emittiert:
  - `INFO&#124;targets_retry=max_attempts=...&#124;sleep_s=...`
  - `INFO&#124;targets_retry=attempts_used=...`

**Retries & Warmup Semantics (Deterministic Verify PASS):**
- **Grafana health warmup**: Direkt nach `up` kann `http:&#47;&#47;127.0.0.1:3000&#47;api&#47;health` kurz nicht erreichbar sein. `shadow_mvs_local_verify.sh` nutzt dafür **bounded retries** (snapshot-only).
  - Env overrides: `GRAFANA_HEALTH_MAX_ATTEMPTS` (default `12`), `GRAFANA_HEALTH_SLEEP_S` (default `1`)
- **Golden Queries warmup (rate&#47;histogram_quantile)**: Bei `rate(...[5m])` und `histogram_quantile(...)` können die ersten Instant-Queries kurz **leer** sein oder `NaN` liefern (erste Scrapes/Window-Warmup).
  - Verify behandelt `empty`/`NaN` als “not ready” und nutzt **bounded warmup retries** (snapshot-only).
  - Env overrides: `WARMUP_MAX_ATTEMPTS` (default `4`), `WARMUP_SLEEP_S` (default `6`)
- **UP query** (`up{job="shadow_mvs"}`) hat separate, kurze Retries:
  - Env overrides: `UP_QUERY_MAX_ATTEMPTS` (default `3`), `UP_QUERY_SLEEP_S` (default `1`)

**Scrape-Quelle (macOS Docker Desktop):**
- Prometheus scrapt den Host-Exporter via `host.docker.internal:9109`
- Scrape Config (expected): `docs&#47;webui&#47;observability&#47;PROMETHEUS_LOCAL_SCRAPE.yml`

**Nicht erlaubt (Cardinality Rules):**
- `run_id`, `intent_id`, `client_order_id`, `broker_order_id` **dürfen nicht** als Prometheus Label auftauchen.

---

## 3) Grafana Provisioning Contract

### 3.1 Datasource (Default)
**Hard Contract (UID):**
- UID: `peaktrade-prometheus-local`

**Recommended Display Name (UI):**
- Name: `peaktrade-prometheus-local`  
  (Falls euer Setup aktuell `prometheus-local` als Name nutzt, ist das ok; UID bleibt hart.)

**URL (aus Grafana Container):**
- `http:&#47;&#47;host.docker.internal:9092`

Provisioning (expected):
- `docs&#47;webui&#47;observability&#47;grafana&#47;provisioning&#47;datasources&#47;datasources.prometheus-local.yaml`

### 3.2 Optional: Live-Ready Datasource Toggle (Docs/Config only)
Ziel: **Shadow-baseline behalten**, aber später (oder parallel) auf einen zweiten Prometheus-Endpunkt umschalten können, ohne Code/Execution zu berühren.

Zusatz-Datasource (nicht default):
- UID: `peaktrade-prometheus-main`
- Name: `peaktrade-prometheus-main`
- URL: `http:&#47;&#47;host.docker.internal:9090`
- Provisioning (expected): `docs&#47;webui&#47;observability&#47;grafana&#47;provisioning&#47;datasources&#47;datasources.prometheus-main.yaml`

**Umschalten (watch-only):**
- Im Dashboard über die Datasource-Variable `DS_PROM` (Dropdown) von local → main  
- Alternativ (Repo-Config): Default Datasource im Dashboard JSON anpassen (**nur wenn gewollt; additive-only**)

### 3.3 Dashboard (file-provisioned)
Hard Contract:
- Dashboard UID: `peaktrade-shadow-pipeline-mvs`

Expected JSON:
- `docs&#47;webui&#47;observability&#47;grafana&#47;dashboards&#47;peaktrade-shadow-pipeline-mvs.json`

Provider (expected):
- `docs&#47;webui&#47;observability&#47;grafana&#47;provisioning&#47;dashboards&#47;dashboards.yaml`

---

## 4) Exporter Metric Families (Shadow-MVS Mock)
Quelle (expected): `scripts&#47;obs&#47;mock_shadow_mvs_exporter.py`

### 4.1 Health
- `shadow_mvs_up{mode,exchange}` (gauge)  
  Erwartung: `1` im Normalfall.

### 4.2 Pipeline Events
- `peak_trade_pipeline_events_total{mode,stage,exchange}` (counter)

Stages (Set):
- `signal|intent|submit|ack|fill|cancel|risk_block|error`

### 4.3 Latency (Histogram)
- `peak_trade_pipeline_latency_seconds_bucket{mode,edge,exchange,le}`
- `peak_trade_pipeline_latency_seconds_sum{mode,edge,exchange}`
- `peak_trade_pipeline_latency_seconds_count{mode,edge,exchange}`

Edges (Set, minimal):
- `intent_to_submit`
- `submit_to_ack`
- `ack_to_fill`
- Optional (wenn vorhanden): `intent_to_fill`

### 4.4 Risk / Blocking (optional, wenn instrumentiert)
- `peak_trade_risk_blocks_total{mode,reason,exchange}` (counter)

Reason (Set, minimal):
- `max_drawdown|equity_floor|position_limit|invalid_state|other`

### 4.5 Exporter/Process (optional)
Wenn ihr generische Python/Exporter Metriken exportiert, sind diese **allowed**, aber nicht required:
- `process_*`, `python_*` (nur low-cardinality)

---

## 5) Golden Queries (Contract)
Diese Queries müssen im Baseline-Setup Daten liefern (Time-Range: Last 15m oder 1h).

```promql
# 1) Target ist UP
up{job="shadow_mvs"}

# 2) Scrape Samples (Debug-Liveness)
scrape_samples_scraped{job="shadow_mvs"}

# 3) Pipeline Throughput by stage
sum by (mode, stage) (rate(peak_trade_pipeline_events_total{job="shadow_mvs"}[5m]))

# 4) Error rate (wenn stage="error" existiert)
sum(rate(peak_trade_pipeline_events_total{job="shadow_mvs",stage="error"}[5m]))
/
clamp_min(sum(rate(peak_trade_pipeline_events_total{job="shadow_mvs"}[5m])), 1)

# 5) Latency P95 (Beispiel: submit_to_ack)
histogram_quantile(
  0.95,
  sum by (le) (rate(peak_trade_pipeline_latency_seconds_bucket{job="shadow_mvs",edge="submit_to_ack"}[5m]))
)
```

---

## 6) Evidence Snapshot (PASS) — 2026-01-18T01:17:13Z

**Mode:** snapshot-only (no-watch)  
**Result:** PASS (`EXIT_CODE=0`)  
**Purpose:** Deterministic proof that the Shadow MVS local observability stack is healthy and the contract endpoints/series are present.

### Ready Endpoints (HTTP 200)
- Prometheus Ready: `http:&#47;&#47;127.0.0.1:9092&#47;-&#47;ready` → `HTTP&#47;1.1 200 OK`
- Grafana Health: `http:&#47;&#47;127.0.0.1:3000&#47;api&#47;health` → `HTTP&#47;1.1 200 OK`

### Prometheus Targets (active)
- `job="shadow_mvs"` → `health="up"` (instance: `host.docker.internal:9109`)
- `job="peak_trade_web"` → `health="up"` (instance: `host.docker.internal:8000`)

### Golden Query (PromQL)
Query:
- `up{job="shadow_mvs"}`

Evidence (vector contains value `1`):
- `instance="host.docker.internal:9109" job="shadow_mvs" value=1`

### Exporter Contract Series (excerpt)
- `shadow_mvs_up{mode="shadow",exchange="sim"} 1`
- `peak_trade_pipeline_events_total{mode="shadow",stage="signal",exchange="sim"} 308`
- `peak_trade_pipeline_events_total{mode="shadow",stage="intent",exchange="sim"} 1027`
- `peak_trade_pipeline_events_total{mode="shadow",stage="submit",exchange="sim"} 925`
- `peak_trade_pipeline_events_total{mode="shadow",stage="ack",exchange="sim"} 925`
- `peak_trade_pipeline_events_total{mode="shadow",stage="fill",exchange="sim"} 822`
- `peak_trade_pipeline_events_total{mode="shadow",stage="cancel",exchange="sim"} 41`
- `peak_trade_pipeline_events_total{mode="shadow",stage="risk_block",exchange="sim"} 71`
- `peak_trade_pipeline_events_total{mode="shadow",stage="error",exchange="sim"} 20`
