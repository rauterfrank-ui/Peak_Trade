# PR #755 — Merge Log

## Summary
- PR: #755
- Title: docs(observability): clarify default /metrics output when flag off
- Scope: docs-only (observability quick-verify nuance)
- Risk: Low

## Why
- Clarify runtime behavior of `/metrics` when `prometheus_client` is installed but `PEAK_TRADE_PROMETHEUS_ENABLED=0`:
  - Default Prometheus client metrics (`python_*`, `process_*`) are still present.
  - Peak_Trade-specific HTTP metrics (`peak_trade_http_*`) are gated behind enablement.

## Changes
- Updated:
  - `docs/webui/observability/README.md`
    - Added Quick Verify bullet for: **client present + flag off ⇒ default metrics only; no `peak_trade_http_*`**.

## Verification
- Local docs gates (changed scope):
  - `bash scripts/ops/pt_docs_gates_snapshot.sh --changed` → PASS
- CI:
 checks: all green prior to merge

## Merge
- Method: Squash merge
- Merge commit: `c13a42a1`

## Operator How-To
- Quick verify matrix (at a glance):
  - `prometheus_client` present + `PEAK_TRADE_PROMETHEUS_ENABLED=0` → `/metrics` contains `python_*`, `process_*`; does **not** contain `peak_trade_http_*`.
  - `prometheus_client` present + `PEAK_TRADE_PROMETHEUS_ENABLED=1` → `/metrics` contains defaults plus `peak_trade_http_*` (Peak_Trade instrumentation enabled).
  - `prometheus_client` missing + `REQUIRE_PROMETHEUS_CLIENT=0` → `/metrics` returns `peak_trade_metrics_fallback 1` (fail-open).
  - `prometheus_client` missing + `REQUIRE_PROMETHEUS_CLIENT=1` → `/metrics` returns HTTP 503 (strict).

## References
- Docs:
  - `docs/webui/observability/README.md`
- Prior observability chain:
  - `docs/ops/merge_logs/PR_753_MERGE_LOG.md`
