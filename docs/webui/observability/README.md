# Observability (Prometheus / Grafana) — Peak_Trade Watch-Only

Diese Assets sind **optional** und betreffen ausschließlich **Service Health / HTTP Layer** der Watch-Only Web-App.

## Aktivierung (Peak_Trade Web-App)

- Env-Flag: `PEAK_TRADE_PROMETHEUS_ENABLED=1`
- Voraussetzung: `prometheus_client` ist im Python Environment verfügbar
- **Wichtig (tatsächliches Verhalten)**:
  - `&#47;metrics` ist **immer** erreichbar, aber:
    - Ohne `prometheus_client` liefert es im Default (fail-open) nur ein Fallback-Signal: `peak_trade_metrics_fallback 1` (HTTP 200).
    - Mit `REQUIRE_PROMETHEUS_CLIENT=1` wird es **strict** und liefert bei fehlendem `prometheus_client` HTTP **503** (Scrape soll rot werden, statt “grün fake”).
    - Peak_Trade HTTP-Metriken (z.B. `peak_trade_http_requests_total`) werden nur instrumentiert, wenn `PEAK_TRADE_PROMETHEUS_ENABLED=1` gesetzt ist **und** `prometheus_client` verfügbar ist.

## Quick Verify

- `curl http://127.0.0.1:8000/metrics | head`
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
  - `.venv/bin/python scripts/live_web_server.py --host 127.0.0.1 --port 8000`

**Docker/Prometheus Networking Fix (macOS Docker Desktop):**
- Scrape Target im Container: `localhost:8000` → **falsch** (zeigt auf den Container)
- Korrekt: `host.docker.internal:8000`

**Prometheus Reload/Restart Outcome:**
- `POST /-/reload`: **403 Forbidden** (wenn Prometheus ohne `--web.enable-lifecycle` läuft)
- Workaround: Prometheus Container neu starten, damit Config neu geladen wird

## Dateien

- Prometheus Scrape Example: `docs/webui/observability/PROMETHEUS_SCRAPE_EXAMPLE.yml`
- Docker Compose (lokal): `docs/webui/observability/DOCKER_COMPOSE_PROM_GRAFANA.yml`
- Grafana Dashboard JSON: `docs/webui/observability/GRAFANA_DASHBOARD_PEAK_TRADE_WATCH_ONLY.json`

## Operator Runbook

- `docs/ops/runbooks/RUNBOOK_DASHBOARD_WATCH_ONLY_START_TO_FINISH.md`
