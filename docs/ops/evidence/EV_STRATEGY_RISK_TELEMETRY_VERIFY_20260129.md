# EV — Strategy/Risk Telemetry v1 — Verify (2026-01-29)

## Goal
Prove that Strategy/Risk telemetry v1 metrics are exported from the **session process** (Prometheus HTTP server on :9111) and scraped/stored by Prometheus-local (:9092).

## Environment
- Prometheus-local: `http://localhost:9092`
- Session metrics endpoint: `http://localhost:9111/metrics`
- Prometheus job: `peak_trade_session` (scrape target `host.docker.internal:9111`)

## Evidence

### 1) Target UP (Prometheus-local)
Command:

```bash
curl -fsS --get "http://localhost:9092/api/v1/query" \
  --data-urlencode 'query=up{job="peak_trade_session"}'
```

Observed:

```text
series: 1
instance= host.docker.internal:9111 up= 1
```

### 2) Metrics exported by session process (:9111)
Precondition: a shadow/paper session is running and has reached `run_forever()` (so the in-process metrics server exists).

Command:

```bash
curl -fsS -m 2 "http://localhost:9111/metrics" \
  | rg -n '^# (HELP|TYPE) peaktrade_(strategy|risk)_'
```

Observed (registered metric families):

```text
# HELP peaktrade_strategy_decisions_total Total number of strategy decisions finalized (watch/paper/shadow).
# TYPE peaktrade_strategy_decisions_total counter
# HELP peaktrade_strategy_signals_total Total number of final strategy signal changes emitted (watch/paper/shadow).
# TYPE peaktrade_strategy_signals_total counter
# HELP peaktrade_strategy_position_gross_exposure Gross exposure (abs notional) per strategy in ccy units.
# TYPE peaktrade_strategy_position_gross_exposure gauge
# HELP peaktrade_risk_checks_total Total number of risk check evaluations (watch/paper/shadow).
# TYPE peaktrade_risk_checks_total counter
# HELP peaktrade_risk_limit_utilization Risk limit utilization ratio (clamped 0..1).
# TYPE peaktrade_risk_limit_utilization gauge
# HELP peaktrade_risk_blocks_total Total number of risk blocks by finite reason allowlist.
# TYPE peaktrade_risk_blocks_total counter
```

### 3) Stored series examples (Prometheus-local)
Command:

```bash
curl -fsS --get "http://localhost:9092/api/v1/series" \
  --data-urlencode 'match[]=peaktrade_strategy_decisions_total' \
  --data-urlencode 'match[]=peaktrade_risk_checks_total'
```

Observed (examples):

```text
peaktrade_risk_checks_total{check="live_limits.check_orders", result="block", job="peak_trade_session", instance="host.docker.internal:9111"}
peaktrade_strategy_decisions_total{strategy_id="ma_crossover", decision="entry_long", job="peak_trade_session", instance="host.docker.internal:9111"}
```

### 4) Presence sanity (Prometheus-local)
Command:

```bash
curl -fsS --get "http://localhost:9092/api/v1/query" \
  --data-urlencode 'query=count(peaktrade_risk_limit_utilization)'
```

Observed:

```text
{} -> 6
```

## Notes
- :9111 exists only when the shadow/paper session reaches `run_forever()` (in-process metrics server).
- NO-LIVE remains enforced; telemetry-only wiring.
