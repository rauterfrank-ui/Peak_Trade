# PR #763 — Merge Log

## Summary
- PR: #763
- Title: docs(observability): shadow-mvs local exporter + prometheus-local pack
- Scope: watch-only local observability pack (docs + compose + scripts)
- Risk: Low

## Why
- Make the “Shadow Pipeline (MVS)” Grafana dashboard locally runnable in <10 minutes without manual Grafana import/click-work.
- Provide hard verification that targets are UP and panels have data sources available.

## Changes
- Added a local **Shadow MVS mock exporter** (host process) exposing `/metrics` on `:9109`.
- Added `prometheus-local` compose + scrape config (host port `:9092`) to scrape:
  - `host.docker.internal:9109` (shadow_mvs exporter)
  - `host.docker.internal:8000` (Peak_Trade web `/metrics`, optional)
- Kept Grafana **file provisioning** and ensured the dashboard provider uses the `Peak_Trade` folder/provider settings.
- Added operator scripts:
  - `bash scripts/obs/shadow_mvs_local_up.sh`
  - `bash scripts/obs/shadow_mvs_local_verify.sh`
  - `bash scripts/obs/shadow_mvs_local_down.sh`

## Verification
- Local operator proof:
  - `bash scripts/obs/shadow_mvs_local_up.sh`
  - `bash scripts/obs/shadow_mvs_local_verify.sh` → PASS (checks exporter reachable, Prometheus targets UP, Grafana datasource + dashboard visible, core PromQL queries return data)
  - `bash scripts/obs/shadow_mvs_local_down.sh`
- CI: all checks green prior to merge.

## Merge
- Method: Squash merge
- Merge commit: `39128187`
- Merged at: 2026-01-17

## Operator How-To
- Start:
  - `bash scripts/obs/shadow_mvs_local_up.sh`
- Verify:
  - `bash scripts/obs/shadow_mvs_local_verify.sh`
- Stop:
  - `bash scripts/obs/shadow_mvs_local_down.sh`

Key URLs:
- Grafana: `http://127.0.0.1:3000` (admin/admin)
- Prometheus-local: `http://127.0.0.1:9092`
- Exporter: `http://127.0.0.1:9109/metrics`

Grafana Explore smoke queries:
- `up{job="shadow_mvs"}`
- `sum by (mode, stage) (rate(peak_trade_pipeline_events_total{mode="shadow"}[1m]))`

## References
- PR: `https://github.com/rauterfrank-ui/Peak_Trade/pull/763`
- Docs:
  - `docs/webui/observability/README.md`
  - `docs/webui/observability/DASHBOARD_WORKFLOW.md`
  - `docs&#47;webui&#47;observability&#47;grafana&#47;dashboards&#47;shadow&#47;peaktrade-shadow-pipeline-mvs.json`
