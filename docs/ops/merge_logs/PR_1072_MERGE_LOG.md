# PR 1072 — MERGE LOG

## Summary
Expose Strategy/Risk telemetry via an in-process Prometheus /metrics endpoint started inside Shadow/Live session runners (default :9111), plus Prometheus-local scrape job.

## Why
Targets were UP but peaktrade_strategy_* / peaktrade_risk_* were missing because the scraped processes did not register/emit those metrics. Starting /metrics in the session process ensures emitted counters/gauges are exported.

## Changes
- New: src/obs/metrics_server.py
  - idempotent, fail-open in-process /metrics server
  - default port: 9111
- Update: src/obs/strategy_risk_telemetry.py
  - add ensure_registered() to register metric names eagerly
- Wire-in (session entry):
  - src/live/shadow_session.py: ensure_metrics_server() + ensure_registered() in run_forever()
  - src/execution/live_session.py: ensure_metrics_server() + ensure_registered() in run_forever()
- Prometheus-local scrape:
  - docs/webui/observability/PROMETHEUS_LOCAL_SCRAPE.yml: new job peak_trade_session → host.docker.internal:9111

## Verification
- CI required checks PASS (tests 3.11, strategy-smoke, Lint Gate).
- Runtime verify path:
  - start shadow/paper session → :9111/metrics exports peaktrade_strategy_*/peaktrade_risk_*
  - Prometheus-local (9092) shows series presence via new scrape job.

## Risk
MEDIUM–HIGH (touches session loop entry points), mitigated by:
- fail-open server start (no crash on bind/import failure)
- idempotent start
- no order/decision logic changes
- NO-LIVE policy unchanged

## Operator How-To
- Start a shadow/paper session.
- Verify metrics endpoint:
  - curl http://localhost:9111/metrics | rg '^peaktrade_(strategy|risk)_'
- Verify Prometheus-local scrape:
  - curl "http://localhost:9092/api/v1/query?query=up{job=\"peak_trade_session\"}"

## References
- PR: #1072
- Merge commit: 3d48e64ed07c9e1f464e28fe9cfff21eb93597a6
- Merged at: 2026-01-29T00:58:57Z
