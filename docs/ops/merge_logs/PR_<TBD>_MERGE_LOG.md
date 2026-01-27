# PR <TBD> — Merge Log

## Summary
Adds watch-only trade-flow Prometheus counters for signals + order approval/blocking, and surfaces them in the Execution Watch Overview dashboard.

## Why
- Operator needs low-cardinality, deterministic throughput counters for the “signal → gate decision” flow (signals, approved, blocked) in watch-only mode.

## Changes
- **Code (telemetry-only):**
  - `src/obs/trade_flow_telemetry.py` (new): Prometheus counters + finite reason mapping/allowlist + graceful no-op when `prometheus_client` missing.
  - `src/execution/pipeline.py`: increments **once per final gate outcome** in `execute_with_safety()`:
    - approved: after all gates pass
    - blocked: on governance/env/safety/risk blocks (finite allowlist)
  - `src/execution/live_session.py`: increments **once per signal-change** in `step_once()`.
- **Dashboard:**
  - `docs/webui/observability/grafana/dashboards/execution/peaktrade-execution-watch-overview.json`:
    - Stat panels: Total Signals / Orders Approved / Orders Blocked (range via `increase(...[$__range])`).
- **Demo / Ops:**
  - `scripts/obs/mock_shadow_mvs_exporter.py`: emits deterministic demo series for the 3 new counters (so local dashboard is non-empty).
  - `docs/ops/runbooks/RUNBOOK_EXECUTION_WATCH_DEMO_STACK.md`: adds minimal Prometheus queries for the new counters.
- **Tests:**
  - `tests/obs/test_trade_flow_telemetry_metrics.py`: smoke tests for import safety (no-crash without Prometheus) + counter increments when Prometheus is available.

## Verification
- Local tests:
  - `python3 -m pytest -q tests/obs/test_trade_flow_telemetry_metrics.py`
  - `python3 -m pytest -q tests/obs/test_grafana_dashpack_integrity_v1.py -q`
- Demo-Stack (watch-only):
  - `bash scripts/obs/shadow_mvs_local_up.sh`
  - Verify in Prometheus that `peaktrade_signals_total`, `peaktrade_orders_approved_total`, `peaktrade_orders_blocked_total` exist and are non-zero over time.
  - Grafana: **Peak_Trade → execution → Peak_Trade — Execution Watch Overview** shows non-empty new Stat panels.

## Risk
HIGH (touches `src/execution/**`) but **telemetry-only / watch-only**:
- No trading decision logic changed; only counter increments + reason mapping.
- No order IDs / UUIDs / dynamic reason strings are used as labels.

## Operator How-To
1. Start demo stack: `bash scripts/obs/shadow_mvs_local_up.sh`
2. Check metrics endpoint: `curl -s http://127.0.0.1:9109/metrics | grep -E '^(peaktrade_(signals|orders_approved|orders_blocked)_total)\\b' | head`
3. Prometheus queries:
   - `sum(increase(peaktrade_signals_total[15m]))`
   - `sum(increase(peaktrade_orders_approved_total[15m]))`
   - `sum(increase(peaktrade_orders_blocked_total[15m]))`
4. Grafana: open **Peak_Trade — Execution Watch Overview**, confirm new Stats change over time.

## References
- PR: #<TBD>
- Runbook: `docs/ops/runbooks/RUNBOOK_EXECUTION_WATCH_DEMO_STACK.md`
- Dashboard: `docs/webui/observability/grafana/dashboards/execution/peaktrade-execution-watch-overview.json`
- Tests: `tests/obs/test_trade_flow_telemetry_metrics.py`, `tests/obs/test_grafana_dashpack_integrity_v1.py`
