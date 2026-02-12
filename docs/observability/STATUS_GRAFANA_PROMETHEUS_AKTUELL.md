# Grafana Dashboard + Prometheus — Ist-Zustand (Peak_Trade, Watch-Only)

**Stand:** 2026-01-17  
**Scope:** **Watch-Only / Read-Only** Observability rund um die Peak_Trade Web-UI (HTTP-Layer)  
**Nicht-Ziel:** Keine Live-Trading-/Execution-Funktionalität, keine mutierenden API-Methoden, keine Secrets in Dashboards/Configs.

---

## 1) Kurzüberblick (was aktuell “da” ist)

- **Peak_Trade Web-App** stellt einen Prometheus-kompatiblen Endpoint bereit: **`GET &#47;metrics`**
  - **Default (fail-open)**: Auch ohne `prometheus_client` bleibt `/metrics` erreichbar und liefert ein Fallback-Signal.
  - **Strict Mode**: Mit `REQUIRE_PROMETHEUS_CLIENT=1` liefert `/metrics` bei fehlendem `prometheus_client` **HTTP 503** (Scrape soll “rot” werden).
- **Optionales HTTP-Metrics-Instrumentation** via Middleware (Counters/Histogram/Gauge) ist vorhanden, aber **nur aktiv**, wenn:
  - `PEAK_TRADE_PROMETHEUS_ENABLED=1` gesetzt ist **und**
  - `prometheus_client` im Python-Environment verfügbar ist.
- **Grafana Dashboard JSON** für Watch-Only Prometheus-Metriken ist im Repo vorhanden und für manuelles Importieren gedacht.
- **Prometheus + Grafana Minimal-Compose** (lokal) ist im Repo vorhanden (`docs&#47;webui&#47;observability&#47;README.md`).

---

## 2) Verifiziert auf deinem System (Pre-Flight 2026-01-17)

Aus deinem Pre-Flight-Run:
- **Docker**: vorhanden
- **Docker Compose v2**: vorhanden
- **Mini-Stack Files**: `docs&#47;webui&#47;observability&#47;*` vorhanden
- **System-`python3`**: 3.9.6 (`/Library/Developer/CommandLineTools/usr/bin/python3`)
- **`prometheus_client` (System-`python3`)**: **nicht** installiert/verfügbar (find_spec=False)

Repo-lokal (workspace-safe):
- **`venv&#47;` (Python 3.9.6)**: `prometheus-client` ist installiert und importierbar (zuletzt verifiziert: 0.24.1)

Konsequenz:
- Wenn du die Web-App mit **System-`python3`** startest, liefert `/metrics` aktuell **Fallback** (`peak_trade_metrics_fallback 1`), bis `prometheus_client` installiert ist.
- Wenn du die Web-App mit dem **repo-lokalen `venv&#47;`** startest, kann `/metrics` echte Prometheus-Ausgabe liefern; Peak_Trade HTTP-Metriken erfordern zusätzlich `PEAK_TRADE_PROMETHEUS_ENABLED=1`.

---

## 3) Komponenten & Zuständigkeiten

### 3.1 Peak_Trade Web-App (FastAPI)

- **Factory**: `src/live/web/app.py` (`create_app`)
- **Prometheus Instrumentation**: `src/live/web/metrics_prom.py`
- **Watch-only Safety**: API mutierende Methods auf `"&#47;api&#47;"` werden serverseitig abgewiesen (405).

### 3.2 Prometheus (lokal, optional)

- **Scrape Config Beispiel**: `docs/webui/observability/PROMETHEUS_SCRAPE_EXAMPLE.yml`
- **Ziel**: `/metrics` der host-seitigen Peak_Trade Web-App scrapen (typisch Port 8000)
- **Docker Desktop (macOS/Windows)**: Host-Service aus Container via `host.docker.internal:8000`

### 3.3 Grafana (lokal, optional)

- **Dashboard**: `docs/webui/observability/GRAFANA_DASHBOARD_PEAK_TRADE_WATCH_ONLY.json`
- **Login (Default)**: `admin &#47; admin` (lokal, dev-only)

---

## 4) “Zwei Stacks” im Repo (wichtig für den Ist-Stand)

### 4.1 Mini-Stack: Prometheus + Grafana (Watch-Only HTTP-Metrics)

**Artefakte:**
- `docs/webui/observability/DOCKER_COMPOSE_PROM_GRAFANA.yml`
- `docs/webui/observability/PROMETHEUS_SCRAPE_EXAMPLE.yml`
- `docs/webui/observability/README.md`

**Ports laut Compose:**
- **Grafana**: `localhost:3000`
- **Prometheus**: Container-Port 9090 wird auf **Host-Port 9091** gemappt (`"9091:9090"`)
  - Effektiv: `http://localhost:9091`

**Hinweis:** Der Runbook-Text nennt teils `9090`; maßgeblich ist die Compose-Datei (hier: `9091`).

### 4.2 Größerer Observability-Stack (OTel/Tempo/Loki/Prometheus/Grafana) — “referenziert, aber hier nicht vorhanden”

Es existieren:
- `docs/observability/OBS_STACK_RUNBOOK.md` (beschreibt OTel Collector + Tempo + Loki + Prometheus + Grafana)
- `scripts/obs/up.sh` und `scripts/obs/down.sh` (versuchen `cd ops/observability` und dort `docker compose up|down` auszuführen)

**Ist-Zustand in diesem Workspace:** Der Ordner **`ops&#47;observability&#47;` existiert nicht**, daher sind `scripts/obs/up.sh`/`down.sh` **so nicht ausführbar** (Gap zwischen Doku/Skript und Repo-Inhalt).

---

## 5) Prometheus Scrape: aktuelles Beispiel

Datei: `docs/webui/observability/PROMETHEUS_SCRAPE_EXAMPLE.yml`

- **Scrape Interval**: 15s
- **Job**: `peak_trade_web`
- **Metrics Path**: `/metrics`
- **Target** (Default): `host.docker.internal:8000`

**Typische Anpassungen:**
- Wenn die Web-App auf anderem Port läuft: Target entsprechend ändern.
- Linux Docker: ggf. `extra_hosts`/`host-gateway` notwendig (Hinweis steht in der Datei).

---

## 6) `/metrics` Verhalten (Fail-open vs. Strict) und Flags

### 6.1 Endpoint-Verhalten (immer vorhanden)

Die Route **`GET &#47;metrics`** ist in `src/live/web/app.py` immer registriert und verhält sich so:

- **Wenn `prometheus_client` importierbar ist**: `generate_latest()` wird ausgeliefert (inkl. Standard-Collector-Metriken).
- **Wenn `prometheus_client` fehlt und `REQUIRE_PROMETHEUS_CLIENT!=1`** (Default): HTTP 200 + Fallback-Metrik:
  - `peak_trade_metrics_fallback 1`
- **Wenn `prometheus_client` fehlt und `REQUIRE_PROMETHEUS_CLIENT=1`**: HTTP **503** + Text “prometheus_client required but unavailable”

### 6.2 Instrumentation (Peak_Trade HTTP-Metriken) — nur wenn enabled

Env-Flag:
- `PEAK_TRADE_PROMETHEUS_ENABLED=1`

Nur wenn dieses Flag **und** `prometheus_client` verfügbar sind, wird Middleware-Instrumentation aktiv (in `src/live/web/metrics_prom.py` über `instrument_app(app)`).

---

## 7) Welche Prometheus-Metriken werden aktuell emittiert?

### 7.1 Peak_Trade-spezifisch (nur wenn `PEAK_TRADE_PROMETHEUS_ENABLED=1` und `prometheus_client` verfügbar)

- **Counter**: `peak_trade_http_requests_total`
  - Labels: `method`, `route`, `status_code`
  - Route-Label ist **cardinality-safe**: es wird (wo möglich) die Route-Template-Path verwendet, sonst `__unknown__`.
- **Histogram**: `peak_trade_http_request_duration_seconds`
  - Buckets: `(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10)`
  - Labels: `method`, `route`, `status_code`
- **Gauge**: `peak_trade_http_in_flight_requests`

### 7.2 Fallback (wenn `prometheus_client` nicht verfügbar und nicht-strict)

- **Gauge**: `peak_trade_metrics_fallback 1`

### 7.3 Standard-Collector (wenn `prometheus_client` verfügbar)

Je nach `prometheus_client` Standard-Collector sind typischerweise zu erwarten:
- `python_*`
- `process_*`

---

## 8) Grafana Dashboard (Watch-Only) — Inhalt & Queries

Datei: `docs/webui/observability/GRAFANA_DASHBOARD_PEAK_TRADE_WATCH_ONLY.json`  
Dashboard Titel: **“Peak_Trade — Watch-Only (Prometheus)”**  
UID: `peak-trade-watch-only-prom`

### 8.1 Variablen

- **datasource** (Prometheus datasource)
- **route** via `label_values(peak_trade_http_requests_total, route)` (multi/all)
- **method** via `label_values(peak_trade_http_requests_total, method)` (multi/all)
- **status_class** (custom): `2..,3..,4..,5..` (default `5..`)
- **quantile** (custom): `0.5,0.9,0.95,0.99` (default `0.95`)
- **window** (custom): `1m,5m,15m,1h` (default `5m`)

### 8.2 Panels (Kerndaten)

- **RPS (gesamt)**:
  - `sum(rate(peak_trade_http_requests_total{route=~"$route", method=~"$method"}[$window]))`
- **RPS (pro Route)**:
  - `sum by (route) (rate(peak_trade_http_requests_total{route=~"$route", method=~"$method"}[$window]))`
- **Error Rate (Status-Class Anteil)**:
  - `sum(rate(peak_trade_http_requests_total{status_code=~"$status_class", route=~"$route", method=~"$method"}[$window])) &#47; sum(rate(peak_trade_http_requests_total{route=~"$route", method=~"$method"}[$window]))`
- **In-Flight Requests**:
  - `max(peak_trade_http_in_flight_requests)`
- **Latency Quantiles (per Route)**:
  - `histogram_quantile($quantile, sum by (le, route) (rate(peak_trade_http_request_duration_seconds_bucket{route=~"$route", method=~"$method"}[$window])))`
- **Top Routes by Latency (p95)**:
  - `topk(10, histogram_quantile(0.95, sum by (le, route) (rate(peak_trade_http_request_duration_seconds_bucket{route!="__unknown__", method=~"$method"}[$window]))))`

**Refresh:** 10s, Default Range: last 30m.

---

## 9) Betriebs-/Verifikations-Checkliste (lokal, watch-only)

### 9.1 Web-App Metrics Quick-Check

- `GET http:&#47;&#47;127.0.0.1:8000&#47;metrics`
  - **Erwartung (prom verfügbar, flag AUS)**: `python_*`/`process_*` (aber **keine** `peak_trade_http_*`)
  - **Erwartung (prom verfügbar, flag EIN)**: `python_*`/`process_*` **und** `peak_trade_http_*`
  - **Erwartung (prom fehlt, fail-open)**: `peak_trade_metrics_fallback 1` (HTTP 200)
  - **Erwartung (prom fehlt, strict)**: HTTP 503

### 9.2 Prometheus Targets

- Prometheus UI (bei Mini-Compose: `http://localhost:9091`)
  - `Status -> Targets` prüfen: Job `peak_trade_web` sollte **UP** sein.

### 9.3 Grafana Dashboard

- Grafana: `http://localhost:3000` (Login: Credentials aus `.env` oder `GRAFANA_AUTH=user:pass`)
- Prometheus Datasources und Dashboards werden im Mini-Compose **automatisch provisioniert** (siehe `docs&#47;webui&#47;observability&#47;grafana&#47;provisioning&#47;`).

---

## 10) Bekannte Einschränkungen / Lücken (Ist-Stand)

- **Kein `ops&#47;observability&#47;` im Workspace**: Der in `docs/observability/OBS_STACK_RUNBOOK.md` und `scripts/obs/up.sh` referenzierte “full stack” ist hier **nicht tatsächlich startbar**.
- **Provisioning im Mini-Compose**:
  - Grafana provisioniert **Datasources** und ein **File-basiertes Dashboard** automatisch (siehe `docs&#47;webui&#47;observability&#47;grafana&#47;provisioning&#47;`).
  - Hinweis: Ohne persistente Volumes können Grafana-Einstellungen außerhalb des Provisionings nach Container-Neustart verloren gehen.
- **Prometheus Reload**:
  - Doku erwähnt: `POST &#47;-&#47;reload` kann **403** liefern, wenn Prometheus ohne `--web.enable-lifecycle` läuft → dann ist Restart der einfache Workaround.
- **Security**:
  - Grafana Default-Creds sind nur für lokale Dev-Setups akzeptabel.
  - `/metrics` ist (lokal) **unauthenticated**. In produktiven Umgebungen wäre Absicherung/Netzsegmentierung Pflicht.

---

## 11) Relevante Dateien (Index)

- **Mini-Compose / Watch-Only Prom/Grafana**:
  - `docs/webui/observability/DOCKER_COMPOSE_PROM_GRAFANA.yml`
  - `docs/webui/observability/PROMETHEUS_SCRAPE_EXAMPLE.yml`
  - `docs/webui/observability/GRAFANA_DASHBOARD_PEAK_TRADE_WATCH_ONLY.json`
  - `docs/webui/observability/README.md`
- **Web-App Metrics**:
  - `src/live/web/app.py` (`/metrics` fail-open/strict + API read-only guard)
  - `src/live/web/metrics_prom.py` (Middleware + `peak_trade_http_*`)
- **Runbooks**:
  - `docs/ops/runbooks/RUNBOOK_DASHBOARD_WATCH_ONLY_START_TO_FINISH.md`
  - `docs/ops/runbooks/RUNBOOK_DASHBOARD_WATCH_ONLY_V01B.md`
  - `docs/observability/OBS_STACK_RUNBOOK.md` (beschreibt vollen Stack, aber aktuell Gap)
- **Tests**:
  - `tests/live/test_prometheus_metrics_endpoint.py`

---

## 12) Live Runtime Snapshot (lokal) — verifiziert 2026-01-17

### 12.1 Peak_Trade Web (Watch-Only)

- **Host**: `127.0.0.1:8000`
- **Endpoints**:
  - `/health`: 200 OK (contract_version `v0.1B`)
  - `/metrics`: 200 OK, liefert `python_*` + `peak_trade_http_*` (kein Fallback), wenn gestartet mit:
    - `PEAK_TRADE_PROMETHEUS_ENABLED=1`
    - `REQUIRE_PROMETHEUS_CLIENT=1`
    - repo-`venv&#47;bin&#47;python3`

### 12.2 Prometheus (Docker, lokal)

- **Container**: `peaktrade-prometheus`
- **Ports**: `0.0.0.0:9090->9090&#47;tcp`
- **Config Mount**: `.local&#47;prometheus&#47;prometheus.local.yml` → `&#47;etc&#47;prometheus&#47;prometheus.yml` (ro)
- **Scrape**:
  - `job_name: peak_trade_uvicorn`
  - `scrape_interval: 2s`
  - `targets: ["host.docker.internal:8000"]`
- **Targets API**: `http://127.0.0.1:9090/api/v1/targets` liefert JSON; Peak_Trade Target war **health=up** (lastError leer).
- **Query**: `peak_trade_http_requests_total` lieferte Werte (z.B. Routen `/metrics`, `/health`).

### 12.3 Grafana (Docker, lokal)

- **Container**: `observability-grafana-1`
- **Ports**: `0.0.0.0:3000->3000&#47;tcp`
- **Health API (ohne Auth)**: `GET http:&#47;&#47;127.0.0.1:3000&#47;api&#47;health` lieferte:
  - `database: ok`
  - `version: 12.3.1`
- **Auth-Zustand (API)**:
  - Compose erwartet `GF_SECURITY_ADMIN_PASSWORD` (z.B. aus lokaler `.env`); User optional `GF_SECURITY_ADMIN_USER` (Default `admin`).
  - Grafana API Calls nutzen Basic Auth aus `GRAFANA_AUTH` (user:pass) oder aus `.env` (z.B. `GET &#47;api&#47;datasources`).
