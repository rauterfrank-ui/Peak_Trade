# PR #968 — Merge Log

## Summary
AI Live Drilldown v1: Dashboard-Variable `run_id` (DS_LOCAL) + Panels scoped to `run_id=~"$run_id"`. Exporter ergänzt `peaktrade_ai_last_event_timestamp_seconds_by_run_id{run_id,...}` mit Kardinalitäts-Guardrails. Docs/Workflow aktualisiert; neue Drilldown-Tests.

## Why
Operator needs per-run visibility (“wie arbeitet die AI live?”) statt nur globaler Counters. `run_id` ermöglicht reproduzierbares Debugging und schnelle Ursachenanalyse ohne Log-Suche.

## Changes
- Grafana: `run_id` Variable + AI Live Panels/queries auf `run_id` scoped; no-data hardening (vector(0), clamp_min).
- Exporter: additional per-run freshness gauge + `run_id` normalization/limits (max length, charset).
- Tests: Drilldown contract test added.
- Docs: README + DASHBOARD_WORKFLOW ergänzt (inkl. Token-Policy Safe Darstellung).

## Verification
- CI: required checks PASS (inkl. docs-token-policy-gate).
- Local: `pytest -q tests/obs` PASS (per PR).

## Risk
LOW–MED — watch-only observability (docs/**, scripts/**, tests/**). No `src/**` changes. Cardinality risk mitigated via `run_id` guardrails + documented constraints.

## Operator How-To
1. Start Prometheus/Grafana (local stack) und AI Live exporter auf Port 9110 (Port Contract v1).
2. Open Grafana → Dashboard: **Peak_Trade — Execution Watch Overview**.
3. Set variable **run_id** (regex / dropdown). Observe:
   - per-run “Recent activity” + freshness age
   - per-run timestamps gauge
4. If panels show no data:
   - confirm target `up{job="ai_live"} == 1`
   - ensure events include/run_id and exporter is scraping expected port.

## References
- PR: https://github.com/rauterfrank-ui/Peak_Trade/pull/968
- Merge commit (main): fad6a319bd4f41e46a6b939b50bb987b8b77fdfd
