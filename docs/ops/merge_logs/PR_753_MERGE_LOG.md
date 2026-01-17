# PR #753 — Merge Log

## Summary
Watch-only Observability (Grafana + Prometheus) Dokumentation auf das **reale** Laufzeitverhalten harmonisiert (Fallback vs Strict-Mode), inkl. reproduzierbarem Troubleshooting-Flow fuer Docker Networking und Prometheus Reload.

## Why
Die Observability-Doku war inkonsistent zum Ist-Zustand:
- `&#47;metrics` ist **immer** erreichbar (Fallback oder 503 im Strict-Mode).
- Peak_Trade HTTP-Metriken erscheinen nur, wenn Prometheus-Export explizit aktiviert ist **und** `prometheus_client` verfuegbar ist.
- Prometheus-in-Docker kann `localhost:8000` nicht scrapen (zeigt auf Container), daher Host-Addressing benoetigt.

## Changes
### Docs / Runbook Updates (docs-only)
- Observability README: konsistente Verhaltensbeschreibung + Troubleshooting (Docker Scrape, Strict-Mode, Reload).
- Dashboard Overviews: Observability-Setup und erwtete Metriken/Verhalten konsolidiert.
- Watch-only Runbook: reproduzierbarer Step-by-step Troubleshooting-Abschnitt.

### Config Examples
- Prometheus scrape example: Host-Scrape via `host.docker.internal:8000` (macOS Docker Desktop).
- Docker compose example: konsistente Prometheus Target Konfiguration.

## Files Changed
- docs/ops/runbooks/RUNBOOK_DASHBOARD_WATCH_ONLY_START_TO_FINISH.md
- docs/webui/DASHBOARD_OVERVIEW.md
- docs/webui/DASHBOARD_V0_OVERVIEW.md
- docs/webui/observability/DOCKER_COMPOSE_PROM_GRAFANA.yml
- docs/webui/observability/PROMETHEUS_SCRAPE_EXAMPLE.yml
- docs/webui/observability/README.md

## Verification
- Tests:
  - `.venv&#47;bin&#47;python -m pytest -q tests&#47;live&#47;test_prometheus_metrics_endpoint.py`  (2 passed)
- Docs gates (changed-only):
  - `bash scripts&#47;ops&#47;pt_docs_gates_snapshot.sh --changed`  (PASS: Token Policy, Reference Targets, Diff Guard)
- CI:
  - PR #753: 24 successful, 4 skipped, 0 pending, 0 failing

## Risk
Low — Docs/Observability-Assets only (wat-only). Keine Aenderungen an Execution/Risk/Governance Codepfaden.

## Operator How-To (Troubleshooting Outline)
- Symptom: `&#47;metrics` zeigt nur Fallback oder keine Peak_Trade-Metriken.
- Checks:
  - Sicherstellen, dass der Live-Web-Server im Repo-Venv laeuft (nicht System-Python).
  - Prometheus Export einschalten (ENV) und `prometheus_client` verfuegbar machen.
  - Docker Prometheus Target: **nicht** `localhost:8000`, sondern `host.docker.internal:8000` (macOS Docker Desktop).
- Reload Hinweis:
  - `POST &#47;-&#47;reload` kann 403 liefern, wenn Prometheus nicht mit `--web.enable-lifecycle` gestartet wurde → Container Restart notwendig.

## References
- PR #753 (merged): docs(observability): align Prometheus/Grafana watch-only behavior + troubleshooting
- Merge commit: 5a4db1bb
- Related:
  - PR #751: strict `&#47;metrics` mode + web extra prometheus-client
  - PR #752: ignore docs/scratch
