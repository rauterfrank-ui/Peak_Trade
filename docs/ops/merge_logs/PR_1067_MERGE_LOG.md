# PR 1067 — MERGE LOG

## Summary
Strategy/Risk runtime telemetry v1: bounded Prometheus metrics with strict allowlists + fail-open behavior, instrumented across execution pipeline, runtime risk, and live/shadow sessions; adds tests.

## Why
Enable a visible Strategy/Risk “data stream” (Prometheus → Grafana) during watch/paper/shadow runs without symbol/instrument label cardinality.

## Metrics
- `peaktrade_strategy_decisions_total{strategy_id,decision}`
- `peaktrade_strategy_signals_total{strategy_id,signal}`
- `peaktrade_strategy_position_gross_exposure{strategy_id,ccy}`
- `peaktrade_risk_checks_total{check,result}`
- `peaktrade_risk_limit_utilization{limit_id}` (0..1 clamped)
- `peaktrade_risk_blocks_total{reason}`

## Changes
- New: `src/obs/strategy_risk_telemetry.py`
- Instrumentation:
  - `src/execution/pipeline.py`
  - `src/execution/risk_hook_impl.py`
  - `src/live/risk_limits.py`
  - `src/live/shadow_session.py`
  - `src/execution/live_session.py`
- Tests:
  - `tests/obs/test_strategy_risk_telemetry_metrics.py`

## Verification
- CI required checks: PASS (incl. tests (3.11) and strategy-smoke).
- Local (as per PR workflow): ruff check/format + obs telemetry tests.

## Risk
LOW (telemetry-only; bounded labels; fail-open; watch/paper/shadow).

## Operator How-To
- Validate metrics exist:
  - search in Prometheus for `peaktrade_strategy_` and `peaktrade_risk_`
- Grafana panels are in Operator Summary (Strategy & Risk Telemetry section) from PR #1068.

## References
- PR: #1067
- Merge commit: a9b4845bb9b6f014b2eeb0a9126861a1ed4fb34a
- Merged at: 2026-01-28T21:49:10Z
