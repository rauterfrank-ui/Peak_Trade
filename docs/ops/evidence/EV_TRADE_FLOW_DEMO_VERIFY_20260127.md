# EV — Trade-Flow Demo Verify (Signals / Approved / Blocked)

## Context
Watch-only demo verification for the trade-flow telemetry counters and Grafana execution dashboard panels.

## Source (local, ignored by git)
- Local report (gitignored): `reports&#47;ops&#47;trade_flow_demo_verify_20260127T074612.txt`
- Timestamp (from report): `utc=2026-01-27T06:46:12Z`

## Results (from report)
### Endpoints
- Prometheus READY (9092): ✅
- Grafana HEALTH (3000): ✅

### Exporter metrics present (9109)
- `peaktrade_signals_total` (buy/sell/flat)
- `peaktrade_orders_approved_total`
- `peaktrade_orders_blocked_total` (reasons observed: limits, governance)

Example series (report excerpt):
- signals: buy=708, sell=531, flat=118
- approved=649
- blocked: limits=88, governance=17

### Prometheus quick queries (1m) — non-zero
- signals: `sum(increase(peaktrade_signals_total[1m]))` → 137.4645…
- approved: `sum(increase(peaktrade_orders_approved_total[1m]))` → 66.5502…
- blocked: `sum(increase(peaktrade_orders_blocked_total[1m]))` → 12.0009…

## Notes
- The source report is intentionally not committed because `reports&#47;` is ignored by repo policy.
- This evidence doc captures the operator-relevant outputs for reviewability and audit trail.
