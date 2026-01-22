# Observability (Prometheus / Grafana) — Peak_Trade Watch-Only

Diese Assets sind **optional** und betreffen ausschließlich **Service Health / HTTP Layer** der Watch-Only Web-App.

## Quickstart (lokal, <10 Min): Shadow Pipeline MVS Dashboard (provisioned + verified)

Ziel: **Grafana-only UI** + **prometheus-local** (Host-Port `:9092`) + **automatisch provisioniertes** Dashboard
`Peak_Trade — Shadow Pipeline (MVS, Contract v1)` **ohne manuelles Grafana-Import/Klick-Orgie**.

> Hinweis: Der Shadow-MVS Quickstart startet zusätzlich einen kleinen **Mock-Exporter** (Host-Port `:9109`),
> lokal deterministisch Daten sehen (auch wenn du die Peak_Trade Web-App noch nicht laufen hast).

Start:

```bash
bash scripts/obs/shadow_mvs_local_up.sh
```

Verifikation (harte Checks: Targets UP, Datasource/Dashboard da, Kernqueries liefern Daten):

```bash
bash scripts/obs/shadow_mvs_local_verify.sh
```

Stop:

```bash
bash scripts/obs/shadow_mvs_local_down.sh
```

URLs:
- Grafana: http://127.0.0.1:3000 (admin/admin)
- Prometheus-local: http://127.0.0.1:9092
- Shadow-MVS Exporter: http://127.0.0.1:9109/metrics

Relevante Compose-Files:
- docs/webui/observability/DOCKER_COMPOSE_GRAFANA_ONLY.yml
- docs/webui/observability/DOCKER_COMPOSE_PROMETHEUS_LOCAL.yml

## Quickstart (lokal): Grafana-only Provisioning Smoke (ohne Mock-Exporter)

Ziel: Nur Prometheus-local + Grafana-only starten und per Snapshot verifizieren, dass:
- Grafana health OK
- Datasources local/main/shadow provisioned
- Dashboards aus den Subfoldern provisioned (execution/overview/shadow/http)

Start:

```bash
bash scripts/obs/grafana_local_up.sh
```

Verify:

```bash
bash scripts/obs/grafana_local_verify.sh
```

Stop:

```bash
bash scripts/obs/grafana_local_down.sh
```

## Troubleshooting (minimal, deterministisch)

- Wenn `grafana_local_up.sh` mit einer Docker-Daemon Meldung scheitert, starte Docker lokal und führe den Smoke erneut aus.
- Wenn `grafana_local_verify.sh` bei `prometheus.ready` scheitert, ist der Compose-Stack nicht gestartet oder Ports sind belegt.
- Wenn `grafana_local_verify.sh` bei `grafana.dashboards` scheitert, stimmt meist ein Mount oder die Provisioning-Config nicht.

Snapshot-Debug (keine Watch-Loops):

```bash
# Status
docker compose -p peaktrade-grafana-local -f docs/webui/observability/DOCKER_COMPOSE_PROMETHEUS_LOCAL.yml -f docs/webui/observability/DOCKER_COMPOSE_GRAFANA_ONLY.yml ps

# Grafana health
curl -fsS -u admin:admin http://127.0.0.1:3000/api/health

# Provisioning mounts (im Container)
docker compose -p peaktrade-grafana-local -f docs/webui/observability/DOCKER_COMPOSE_PROMETHEUS_LOCAL.yml -f docs/webui/observability/DOCKER_COMPOSE_GRAFANA_ONLY.yml exec grafana sh -lc 'ls -la /etc/grafana/provisioning/dashboards /etc/grafana/provisioning/datasources /etc/grafana/dashboards'
```

## Aktivierung (Peak_Trade Web-App)

- Env-Flag: `PEAK_TRADE_PROMETHEUS_ENABLED=1`
- Voraussetzung: `prometheus_client` ist im Python Environment verfügbar
- **Wichtig (tatsächliches Verhalten)**:
  - `&#47;metrics` ist **immer** erreichbar, aber:
    - Ohne `prometheus_client` liefert es im Default (fail-open) nur ein Fallback-Signal: `peak_trade_metrics_fallback 1` (HTTP 200).
    - Mit `REQUIRE_PROMETHEUS_CLIENT=1` wird es **strict** und liefert bei fehlendem `prometheus_client` HTTP **503** (Scrape soll rot werden, statt “grün fake”).
    - Peak_Trade HTTP-Metriken (z.B. `peak_trade_http_requests_total`) werden nur instrumentiert, wenn `PEAK_TRADE_PROMETHEUS_ENABLED=1` gesetzt ist **und** `prometheus_client` verfügbar ist.

## Quick Verify

- `curl http:&#47;&#47;127.0.0.1:8000&#47;metrics | head`
  - Erwartung (`prometheus_client` verfügbar, Flag **aus**): `python_*`, `process_*` (Default-Metriken), **keine** `peak_trade_http_*`
  - Erwartung (enabled + `prometheus_client`): `python_*`, `process_*`, plus `peak_trade_http_*`
  - Erwartung (kein `prometheus_client`, fail-open): `peak_trade_metrics_fallback 1`
  - Erwartung (strict): HTTP 503 + Text “prometheus_client required but unavailable”

## Step-by-step Log (Incident: `&#47;metrics` nur Fallback → echte Metriken)

**Status (jetzt grün):**
- Grafana Login: ✅
- Prometheus Data Source: ✅ (Prometheus API erfolgreich)
- Peak_Trade Live Dashboard liefert echte Prometheus-Metriken: ✅
  - `&#47;metrics`: `python_*`, `process_*`, `peak_trade_http_requests_total`
- Prometheus Targets: ✅ UP (auch im Observability-Stack)

**Root Cause:**
- Live-Web-App lief unter System-Python (`&#47;Library&#47;Developer&#47;CommandLineTools&#47;usr&#47;bin&#47;python3`)
- `prometheus_client` dort nicht vorhanden + `PEAK_TRADE_PROMETHEUS_ENABLED` nicht gesetzt
- Ergebnis: `&#47;metrics` lieferte nur `peak_trade_metrics_fallback 1`

**Fix (repo-lokal, governance-safe):**
- System-Python Server auf `:8000` beendet (SIGINT), Port freigemacht
- Live-Web-App repo-lokal gestartet (Beispiel):
  - `PEAK_TRADE_PROMETHEUS_ENABLED=1`
  - `REQUIRE_PROMETHEUS_CLIENT=1`
  - `.venv&#47;bin&#47;python scripts&#47;live_web_server.py --host 127.0.0.1 --port 8000`

**Docker/Prometheus Networking Fix (macOS Docker Desktop):**
- Scrape Target im Container: `localhost:8000` → **falsch** (zeigt auf den Container)
- Korrekt: `host.docker.internal:8000`

**Prometheus Reload/Restart Outcome:**
- `POST &#47;-&#47;reload`: **403 Forbidden** (wenn Prometheus ohne `--web.enable-lifecycle` läuft)
- Workaround: Prometheus Container neu starten, damit Config neu geladen wird

## Dateien

- Prometheus Scrape Example: docs/webui/observability/PROMETHEUS_SCRAPE_EXAMPLE.yml
- Docker Compose (lokal): docs/webui/observability/DOCKER_COMPOSE_PROM_GRAFANA.yml
- Grafana Dashboard JSON: docs/webui/observability/GRAFANA_DASHBOARD_PEAK_TRADE_WATCH_ONLY.json
- Grafana Dashboards (provisioned, foldered):
  - docs/webui/observability/grafana/dashboards/execution/peaktrade-execution-watch-overview.json
  - docs/webui/observability/grafana/dashboards/overview/peaktrade-overview.json
  - docs/webui/observability/grafana/dashboards/shadow/peaktrade-shadow-pipeline-mvs.json
  - docs/webui/observability/grafana/dashboards/http/peaktrade-labeled-local.json
- Hinweis: Grafana `label_values(...)` (Variable Queries) vs PromQL ist in `DASHBOARD_WORKFLOW.md` im Abschnitt „Grafana Variable Queries vs PromQL“ erklärt.

## Ports & Networking (wichtig)

- **Grafana UI (Host)**: http://localhost:3000
- **Prometheus UI (Host)**: http://localhost:9091
  - In `DOCKER_COMPOSE_PROM_GRAFANA.yml` ist Prometheus bewusst auf **Host-Port 9091** gemappt (`"9091:9090"`), um Konflikte mit anderen Prometheus-Instanzen auf `9090` zu vermeiden.
- **Grafana → Prometheus (Docker-intern)**:
  - Grafana muss Prometheus über **http://prometheus:9090** (Service-Name + Container-Port) erreichen.
  - Nicht http://prometheus:9091 (das ist nur der Host-Port und führt im Container zu connection refused).

## Operator Runbook

- docs/ops/runbooks/RUNBOOK_DASHBOARD_WATCH_ONLY_START_TO_FINISH.md

## Shadow → Live Observability Runbook (Grafana)

Dieses Repo enthält zusätzlich ein Runbook für den **symbiotischen Kern** (Shadow → später Live) mit klarer Trennung:
- Grafana = Aggregationen/Health
- Ledger/Logs = konkrete Events (audit/replay)
- WebUI/Watch-Only = Operator-Detailsicht (read-only)

Startpunkt:
- docs/webui/observability/RUNBOOK_Peak_Trade_Grafana_Shadow_to_Live_Cursor_Multi_Agent.md

Begleitende Specs/Contracts:
- docs/webui/DASHBOARD_GOVERNANCE_NO_LIVE.md
- docs/webui/DASHBOARD_DATA_CONTRACT_OBS_v1.md
- docs/webui/GRAFANA_DASHBOARD_SPEC_PEAK_TRADE_OBS_v1.md
