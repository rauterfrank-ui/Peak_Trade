# PR 1068 — MERGE LOG

## Summary
Grafana: Operator Summary dashboard updated with Strategy/Risk telemetry panels (v1 metrics) to visualize runtime stream in watch/paper/shadow sessions.

## Why
Provide an operator-visible “data stream” view for Strategy and Risk telemetry (decisions/signals, risk blocks, utilization, exposure) with bounded label cardinality (no symbol/instrument labels).

## Changes
- Updates:
  - `docs/webui/observability/grafana/dashboards/overview/peaktrade-operator-summary.json`
- Adds a “Strategy & Risk Telemetry” section (panels/PromQL) over:
  - `peaktrade_strategy_decisions_total`
  - `peaktrade_strategy_signals_total`
  - `peaktrade_strategy_position_gross_exposure`
  - `peaktrade_risk_checks_total{result="block"}`
  - `peaktrade_risk_blocks_total`
  - `peaktrade_risk_limit_utilization`

## Verification
- CI required checks: PASS (pre-merge).
- Repo dashboard verification: Grafana dashpack hermetic verify ran in PR.

## Risk
LOW (Grafana JSON only; no runtime behavior change).

## Operator How-To
- Open Grafana “Operator Summary” dashboard and locate Strategy/Risk Telemetry section.
- If panels show “No data”, verify:
  - Prometheus targets UP
  - metrics exist in Prometheus (search for `peaktrade_strategy_*` / `peaktrade_risk_*`)

## References
- PR: #1068
- Merge commit: 3f5e7740ee068e182f3e499035940b3b89d42099
- Merged at: 2026-01-28T21:25:05Z
