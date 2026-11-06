# EV — Strategy/Risk Telemetry Stream Visible (2026-01-28)

## Pre-flight
- pwd:
- git status -sb:

## Stack
- Grafana URL:
- Prometheus base URL/port: (9090/9091/9092)

## Prometheus Targets
Command(s):

```bash
curl -fsS "http://localhost:9090/api/v1/query?query=up"
```

Notes:
- Confirm relevant jobs are UP.

## Metric presence (Prometheus)
Command(s):

```bash
curl -fsS "http://localhost:9090/api/v1/query?query=count(peaktrade_strategy_decisions_total)"
curl -fsS "http://localhost:9090/api/v1/query?query=count(peaktrade_risk_checks_total)"
curl -fsS "http://localhost:9090/api/v1/query?query=count(peaktrade_risk_limit_utilization)"
```

## Generate activity (watch/paper/shadow)
- Mode used (watch/paper/shadow):
- Command(s) run:
- Notes:

## PromQL sanity queries
- Decisions rate:

```promql
sum by (strategy_id, decision) (rate(peaktrade_strategy_decisions_total[5m]))
```

- Signals rate:

```promql
sum by (strategy_id, signal) (rate(peaktrade_strategy_signals_total[5m]))
```

- Risk block rate:

```promql
sum by (check) (rate(peaktrade_risk_checks_total{result="block"}[5m]))
```

- Utilization:

```promql
max by (limit_id) (peaktrade_risk_limit_utilization)
```

## Grafana verification
- Open Operator Summary dashboard
- Locate “Strategy & Risk Telemetry (watch/paper/shadow)” section
- Confirm panels show non-empty legends and update during activity

If “No data”:
- Confirm Prometheus datasource selection is correct
- Confirm targets UP
- Confirm metric presence via Prometheus API queries above

## Notes / Risk
- NO-LIVE HARD: watch/paper/shadow only; metrics are observational and bounded-label by design.
