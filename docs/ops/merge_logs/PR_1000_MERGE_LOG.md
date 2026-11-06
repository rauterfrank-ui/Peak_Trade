# PR 1000 — Merge Log

## Summary
Adds a **Signals / min (1m)** rate Stat panel to the Execution Watch Overview dashboard to complement the existing range counters (signals/approved/blocked).

## Why
Operators need a stable, low-cardinality **throughput rate** view (signals per minute) alongside range totals to quickly validate live activity and demo health.

## Changes
- Dashboard: Execution Watch Overview
  - Adds “Signals / min (1m)” Stat panel using a 1m-rate query derived from `peaktrade_signals_total`.

## Verification
- Demo stack health:
  - Prometheus ready: http://127.0.0.1:9092/-/ready
  - Grafana healthy: http://127.0.0.1:3000/api/health
- Prometheus query sanity (examples):
  - `sum(increase(peaktrade_signals_total[1m]))` is non-zero during demo activity.
- Grafana UI:
  - Dashboard shows “Signals / min (1m)” with a non-zero value consistent with Prometheus 1m activity.

## Risk
Low (docs-only Grafana dashboard JSON).

## Post-Merge Anchor
- PR: #1000
- mergedAt: 2026-01-27T07:51:17Z
- mergeCommit: 1def2d2e8a89578159af357b4d920d2ddf6294f4
- title: docs(grafana): add signals rate stat panel (1m)
- url: https://github.com/rauterfrank-ui/Peak_Trade/pull/1000
