# Peak_Trade Dashboard – Übersicht (WebUI + Live Dashboard)

Diese Übersicht beantwortet:

- **Wo ist das Dashboard aufrufbar (URLs / Ports / Routen)?**
- **Wie ist das Dashboard mit Kraken verknüpft (Datenfluss, read-only vs. Execution)?**
- **Kann ich beim Shadow-Trading „live zuschauen“ (HTML/Auto-Refresh, Snapshots)?**

> **Safety-Note:** Beide Dashboards sind **read-only** (keine Order-Erzeugung, kein Start/Stop von Runs über die UI). Live bleibt governance-locked.

---

## 0) Start here (Navigation)

- [Dashboard v0 (Watch-Only) Overview](./DASHBOARD_V0_OVERVIEW.md)
- [API Contract v0 (Read-only)](./DASHBOARD_API_CONTRACT_v0.md)
- [Data Contract v0 (Artifacts)](./DASHBOARD_DATA_CONTRACT_v0.md)
- [Operator Runbook: Watch-Only Start → Finish](../ops/runbooks/RUNBOOK_DASHBOARD_WATCH_ONLY_START_TO_FINISH.md)
- [Observability (Prometheus/Grafana)](./observability/README.md)

## 1) Es gibt zwei „Dashboards“ (wichtig für die richtige Erwartung)

### A) WebUI Dashboard v1.x (`src/webui/app.py`)

**Stärken:**
- „Projekt-/Ops-Console“: Live-Track Panel, Session Explorer, Alerts, Telemetry, Ops Panels
- Viele HTML-Pages + JSON APIs (server-rendered, teilweise XSS-safe HTML Snapshots)

**Start:**
- Via Uvicorn (direkt): `uvicorn src.webui.app:app --host 127.0.0.1 --port 8000`
- Oder Dev-Runner: `python scripts/run_web_dashboard.py` (reload)

### B) „Live Dashboard“ v0.1 (Phase 67) (`scripts/live_web_server.py` / `src/live/web/app.py`)

**Stärken:**
- Fokus: „Run Monitoring“ von **Shadow-/Paper-Runs** auf Basis von Dateien unter `live_runs&#47;`
- **Auto-Refresh HTML**, Run-Liste, Snapshot-Kacheln, Tail-Events, Alerts pro Run

**Start:**
- `python scripts/live_web_server.py --host 127.0.0.1 --port 8000`
- Optionaler Override: `--base-runs-dir live_runs`

---

## 2) Wo aufrufbar? (URLs / Endpoints)

### 2.1 WebUI v1.x (Standard-Port: 8000)

**Basis:**
- **Home (HTML):** `http://127.0.0.1:8000/`
- **OpenAPI/Swagger:** `http://127.0.0.1:8000/docs`

**Live-Track / Sessions (HTML):**
- **Session-Detail:** `http://127.0.0.1:8000/session/<session_id>`
- **Execution Timeline (HTML):** `http://127.0.0.1:8000/live/execution/<session_id>`
- **Alerts (HTML):** `http://127.0.0.1:8000/live/alerts`
- **Telemetry Console (HTML):** `http://127.0.0.1:8000/live/telemetry`

**Live-Track / Sessions (JSON APIs):**
- **Session-Liste:** `http://127.0.0.1:8000/api/live_sessions?limit=10`
  - Filter: `mode=shadow|testnet|paper|live`, `status=started|completed|failed|aborted`
  - Beispiel: `http://127.0.0.1:8000/api/live_sessions?mode=shadow&status=completed`
- **Session-Detail:** `http://127.0.0.1:8000/api/live_sessions/<session_id>`
- **Session-Stats:** `http://127.0.0.1:8000/api/live_sessions/stats`

**Status-Snapshot (wichtig für „HTML zuschauen“):**
- **Deterministischer Snapshot (JSON):** `http://127.0.0.1:8000/api/live/status/snapshot.json`
- **Deterministischer Snapshot (HTML):** `http://127.0.0.1:8000/api/live/status/snapshot.html`
  - Diese HTML-Seite ist bewusst schlicht, **Cache-Control: no-store** und XSS-safe gerendert.

### 2.2 Live Dashboard v0.1 (Phase 67)

**HTML:**
- **Dashboard (HTML):** `http://127.0.0.1:8000/` (alias auch `/dashboard`)

**JSON APIs:**
- **Health:** `http://127.0.0.1:8000/health`
- **Runs-Liste:** `http://127.0.0.1:8000/runs`
- **Run Snapshot:** `http://127.0.0.1:8000/runs/<run_id>/snapshot`
- **Run Tail-Events:** `http://127.0.0.1:8000/runs/<run_id>/tail?limit=50`
- **Run Alerts:** `http://127.0.0.1:8000/runs/<run_id>/alerts?limit=20`

---

## 3) Wie ist das mit Kraken verknüpft?

### 3.1 Wichtigste Klarstellung: Dashboard ↔ Kraken ist indirekt

Das Dashboard ruft typischerweise **nicht direkt** Kraken auf.

Stattdessen:

- **Runner / Session / Pipeline** holt Daten (oder simuliert sie) und schreibt **Artefakte** (Registry JSONs, Run-Events, Telemetry Logs).
- **Dashboard** liest diese Artefakte (read-only) und visualisiert sie als HTML/JSON.

### 3.2 Kraken-Anbindung im Code (CCXT, resilient)

Die Kraken/CCXT-Anbindung sitzt im Data/Exchange-Layer, z.B.:

- `src/data/exchange_client.py` → `ResilientExchangeClient(exchange_id="kraken", ...)`
  - CCXT wrapper mit Circuit Breaker + Retry
  - Beispiel-Methoden: `fetch_ohlcv()`, `fetch_ticker()`, `fetch_balance()`

Die Wahl des Exchanges erfolgt über Config (z.B. `config.toml` / `config/config.toml`), typischerweise:

- `[exchange] id = "kraken"`
- `sandbox = true` (für sichere Umgebungen)

### 3.3 Was bedeutet das für Shadow Trading?

Es gibt **mehrere Shadow-Formen** im Repo:

- **Offline Shadow Run (Phase 24)**: `scripts/run_shadow_execution.py`
  - nutzt CSV/Dummy/normalisierte OHLCV-Daten
  - **macht keine echten Exchange-API Calls** (explizit im Header)
  - kann aber Kraken-CSV-Formate lesen (`KrakenCsvLoader`)

- **Strategy-to-Execution Session (Phase 80/81)**: `scripts/run_execution_session.py`
  - Mode `shadow` (Simulation ohne echte Orders)
  - Mode `testnet` (validate_only / Dry-Run)
  - schreibt Session-Registry Einträge nach `reports&#47;experiments&#47;live_sessions&#47;*.json`

---

## 4) Kann ich „live zuschauen“ beim Shadow Trading (HTML)?

### 4.1 Ja – aber das „Live-Gefühl“ kommt aus Artefakten + Polling

Du bekommst „live“ Sichtbarkeit, wenn während eines Runs laufend Artefakte geschrieben werden.

**Bestes Setup für Live-„Zuschauen“:**

- **Live Dashboard v0.1 (Phase 67)** + ein Runner, der nach `live_runs&#47;` loggt  
  → HTML Seite pollt per JS (Auto-Refresh) und zeigt Run-Events + Snapshot-Metriken.

**Zusätzlich / Deep Dive:**

- **WebUI v1.x**:
  - Execution Timeline: `/live/execution/<session_id>`
  - Telemetry Console: `/live/telemetry`
  - Snapshot HTML: `/api/live/status/snapshot.html`

### 4.2 Welche Datenquellen werden gelesen?

- **WebUI Live-Track Panel**: `reports&#47;experiments&#47;live_sessions&#47;*.json`
  - Quelle: `src/experiments/live_session_registry.py`
  - Hinweis: manche CLIs schreiben den Registry-Eintrag erst „am Ende“ (dann siehst du die Session in der Liste erst nach Abschluss).

- **Live Dashboard v0.1**: `live_runs&#47;<run_id>&#47;...`
  - Quelle: `src/live/monitoring.py` + `src/live/run_logging.py`
  - Vorteile: kann während des Runs laufend aktualisiert werden (Snapshot + Tail).

- **Execution/Telemetry (WebUI)**: `logs&#47;execution&#47;*.jsonl`
  - Quelle: Execution-Telemetry Writer (wird während des Runs append-only geschrieben)

---

## 5) Quick How-To (typische Operator-Workflows)

### 5.1 WebUI v1.x starten und Sessions filtern

1. WebUI starten:
   - `uvicorn src.webui.app:app --host 127.0.0.1 --port 8000`
2. Dashboard öffnen:
   - `http://127.0.0.1:8000/`
3. Shadow Sessions filtern (HTML Home nimmt Query-Filter):
   - `http://127.0.0.1:8000/?mode=shadow&status=completed`
4. API direkt:
   - `http://127.0.0.1:8000/api/live_sessions?mode=shadow&status=completed`

### 5.2 Live Dashboard v0.1 starten (Run Monitoring)

1. Dashboard starten:
   - `python scripts/live_web_server.py --host 127.0.0.1 --port 8000`
2. Öffnen:
   - `http://127.0.0.1:8000/`
3. Runs prüfen:
   - `http://127.0.0.1:8000/runs`

---

## 6) Contracts (v0)

- Data Contract (Artifacts): [DASHBOARD_DATA_CONTRACT_v0.md](DASHBOARD_DATA_CONTRACT_v0.md)
- API Contract (Read-only): [DASHBOARD_API_CONTRACT_v0.md](DASHBOARD_API_CONTRACT_v0.md)

### 5.3 „HTML Snapshot“ ohne UI-Landingpage (minimal, XSS-safe)

- `http://127.0.0.1:8000/api/live/status/snapshot.html`

Das ist praktisch für:
- „Read-only Monitoring“ im Browser
- Copy/paste in Ops Notes (Screenshots)
- deterministische Darstellung (kein JS erforderlich)

---

## 6) Weiterführende Doku (sehr relevant)

- Watch-only Start→Finish Runbook: [`docs/ops/runbooks/RUNBOOK_DASHBOARD_WATCH_ONLY_START_TO_FINISH.md`](../ops/runbooks/RUNBOOK_DASHBOARD_WATCH_ONLY_START_TO_FINISH.md)
- Live-Track Panel: [`docs/PHASE_82_LIVE_TRACK_DASHBOARD.md`](../PHASE_82_LIVE_TRACK_DASHBOARD.md)
- Session Explorer (Filter/Details): `docs/PHASE_85_LIVE_TRACK_SESSION_EXPLORER.md`
- Ops Runbooks: [`docs/LIVE_OPERATIONAL_RUNBOOKS.md`](../LIVE_OPERATIONAL_RUNBOOKS.md)
- Live Status Panels: [`docs/webui/LIVE_STATUS_PANELS.md`](LIVE_STATUS_PANELS.md)
- Positions/Portfolio/Risk Panels: [`docs/webui/LIVE_PANELS_POSITIONS_PORTFOLIO_RISK.md`](LIVE_PANELS_POSITIONS_PORTFOLIO_RISK.md)

---

## 7) Observability (Prometheus / Grafana) — optional, watch-only

Die Live Web Dashboard App kann optional Prometheus-Metriken exponieren (**watch-only**, ohne Trading/Execution Side-Effects).

**Aktivierung:**
- Env-Flag: `PEAK_TRADE_PROMETHEUS_ENABLED=1`
- Voraussetzung: `prometheus_client` ist im Python Environment verfügbar
- `&#47;metrics` ist **immer** erreichbar, aber:
  - Peak_Trade HTTP-Metriken (z.B. `peak_trade_http_requests_total`) werden nur instrumentiert, wenn `PEAK_TRADE_PROMETHEUS_ENABLED=1` gesetzt ist **und** `prometheus_client` verfügbar ist.
  - Fail-open (Default): Wenn `prometheus_client` fehlt, liefert `&#47;metrics` nur `peak_trade_metrics_fallback 1` (HTTP 200).
  - Strict Mode: Mit `REQUIRE_PROMETHEUS_CLIENT=1` liefert `&#47;metrics` bei fehlendem `prometheus_client` HTTP **503**.

**Artefakte (Repo-Pfade):**
- Prometheus Scrape Example: `docs/webui/observability/PROMETHEUS_SCRAPE_EXAMPLE.yml`
- Docker Compose (lokal): `docs/webui/observability/DOCKER_COMPOSE_PROM_GRAFANA.yml`
- Grafana Dashboard JSON: `docs/webui/observability/GRAFANA_DASHBOARD_PEAK_TRADE_WATCH_ONLY.json`

**Runbook (Operator Flow inkl. Prometheus):**
- `docs/ops/runbooks/RUNBOOK_DASHBOARD_WATCH_ONLY_START_TO_FINISH.md`
