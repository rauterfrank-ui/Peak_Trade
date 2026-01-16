# Observability (Prometheus / Grafana) — Peak_Trade Watch-Only

Diese Assets sind **optional** und betreffen ausschließlich **Service Health / HTTP Layer** der Watch-Only Web-App.

## Aktivierung (Peak_Trade Web-App)

- Env-Flag: `PEAK_TRADE_PROMETHEUS_ENABLED=1`
- Voraussetzung: `prometheus_client` ist im Python Environment verfügbar
- Fail-open: Ohne Library oder ohne Flag läuft die App unverändert weiter; `&#47;metrics` wird **nicht** registriert.

## Dateien

- Prometheus Scrape Example: `docs/webui/observability/PROMETHEUS_SCRAPE_EXAMPLE.yml`
- Docker Compose (lokal): `docs/webui/observability/DOCKER_COMPOSE_PROM_GRAFANA.yml`
- Grafana Dashboard JSON: `docs/webui/observability/GRAFANA_DASHBOARD_PEAK_TRADE_WATCH_ONLY.json`

## Operator Runbook

- `docs/ops/runbooks/RUNBOOK_DASHBOARD_WATCH_ONLY_START_TO_FINISH.md`
