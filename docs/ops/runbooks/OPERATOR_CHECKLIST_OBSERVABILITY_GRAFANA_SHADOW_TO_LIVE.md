# Operator-Checkliste — Observability (Grafana) Shadow → Live (watch-only)

**Scope:** read‑only / watch‑only Observability.  
**No‑Live:** keine Trading-/Execution-Aktionen; keine mutierenden API‑Methoden; keine Live‑Enablement‑Anleitung.

---

## A) Pre-Flight (Snapshot-only)

```bash
cd /Users/frnkhrz/Peak_Trade
git status -sb
```

---

## B) Runbook & Contracts lesen (1x)

- Runbook (Grafana Shadow→Live): `docs/webui/observability/RUNBOOK_Peak_Trade_Grafana_Shadow_to_Live_Cursor_Multi_Agent.md`
- Governance NO‑LIVE: `docs/webui/DASHBOARD_GOVERNANCE_NO_LIVE.md`
- Observability Data Contract v1: `docs/webui/DASHBOARD_DATA_CONTRACT_OBS_v1.md`
- Grafana Dashboard Spec v1: `docs/webui/GRAFANA_DASHBOARD_SPEC_PEAK_TRADE_OBS_v1.md`
- Iststand Observability (Prometheus/Grafana): `docs/webui/observability/README.md`

---

## C) Quick Verify: Metrics Endpoint (watch-only)

Wenn ein lokaler Watch‑Only Server läuft:

```bash
curl -sS http://127.0.0.1:8000/metrics | head -n 50
```

Erwartungen:
- Ohne `prometheus_client` (fail-open): `peak_trade_metrics_fallback 1`
- Mit `prometheus_client` + enabled: `peak_trade_http_*` Serien sichtbar

---

## D) Quick Verify: Prometheus/Grafana (optional, lokal)

Wenn du den mini-stack nutzt (optional):
- Compose: `docs/webui/observability/DOCKER_COMPOSE_PROM_GRAFANA.yml`
- Scrape config: `docs/webui/observability/PROMETHEUS_SCRAPE_EXAMPLE.yml`
- Dashboard JSON: `docs/webui/observability/GRAFANA_DASHBOARD_PEAK_TRADE_WATCH_ONLY.json`

---

## E) v1 Pipeline Panels (Hinweis)

Die Panels/PromQL aus dem v1 Spec sind **erst dann** „live“, wenn die Pipeline‑Metriken instrumentiert sind.
Bis dahin liefert Grafana primär **HTTP/Service‑Health** Signale.

---

## F) Safety Check (immer)

- Keine UI/Docs dürfen Live‑Execution auslösen.
- Keine high‑cardinality Labels in Prometheus (kein `run_id`, keine Order‑IDs).
- Bei Unsicherheit: stop, Review, Governance.
