# EV: metricsd Mode B Operator Verify (2026-01-29)

> **Purpose**: Evidence that **Mode B** telemetry wiring works end-to-end: **metricsd always-on exporter** on **:9111**, sessions **update-only** (no bind), Prometheus-local scrapes `peak_trade_metricsd`, and strategy/risk series persist and update during session runtime.  
> **Scope**: Local operator verification (watch-only / NO-LIVE).  
> **Policy**: No symbol/instrument labels. Fail-open telemetry tolerated if `prometheus_client` missing (must be present for this verify).

---

## 1) Environment

- Metrics mode: `PEAKTRADE_METRICS_MODE=B`
- Multiprocess dir (operator override): `.ops_local&#47;prom_multiproc`
- Exporter port: `9111`
- Prometheus-local scrape target: `host.docker.internal:9111`
- Expected Prometheus job: `peak_trade_metricsd`

---

## 2) Preconditions / Gates

- [x] **NO-LIVE** enforced (no live execution enable flags)
- [x] **Port ownership**: :9111 bound **only** by metricsd (sessions must not bind)
- [x] Prometheus-local scrape config contains job `peak_trade_metricsd`
- [x] Session runs in **Mode B** (sessions update metrics, no HTTP server)

---

## 3) Commands (Terminal Evidence)

### 3.1 Repo pre-flight (common)

```bash
# == PRE-FLIGHT (Ctrl-C if you see: >  dquote>  heredoc>) ==
cd /Users/frnkhrz/Peak_Trade 2>/dev/null || cd "$HOME/Peak_Trade" 2>/dev/null || true
pwd
git rev-parse --show-toplevel 2>/dev/null || true
git status -sb 2>/dev/null || true
```

### 3.2 Terminal A — Start metricsd (always-on exporter)

```bash
export PEAKTRADE_METRICS_MODE="B"
export PEAKTRADE_METRICS_MULTIPROC_DIR=".ops_local/prom_multiproc"
export PROMETHEUS_MULTIPROC_DIR=".ops_local/prom_multiproc"

# Optional: confirm port 9111 not already bound
lsof -nP -iTCP:9111 -sTCP:LISTEN || true

./.venv/bin/python3 scripts/obs/pt_metricsd.py --port 9111 --multiproc-dir ".ops_local/prom_multiproc" --log-level INFO
```

**Paste metricsd evidence (port ownership + exporter 200 OK):**

```text
COMMAND     PID    USER   FD   TYPE            DEVICE SIZE/OFF NODE NAME
python3.1 83393 frnkhrz    3u  IPv4 0x3cf4a4128cc0937      0t0  TCP *:9111 (LISTEN)
83393 /Users/frnkhrz/Peak_Trade/.venv/bin/python3 scripts/obs/pt_metricsd.py --port 9111 --multiproc-dir .ops_local/prom_multiproc --log-level INFO

HTTP/1.0 200 OK
Content-Type: text/plain; version=0.0.4; charset=utf-8
Content-Length: 1587
```

### 3.3 Terminal B — Start a short Shadow Session (Mode B)

```bash
export PEAKTRADE_METRICS_MODE="B"
export PEAKTRADE_METRICS_MULTIPROC_DIR=".ops_local/prom_multiproc"
export PROMETHEUS_MULTIPROC_DIR=".ops_local/prom_multiproc"

# Start short shadow session (2 minutes)
./.venv/bin/python3 -m scripts.run_shadow_paper_session \
  --config config/config.toml \
  --strategy ma_crossover \
  --duration 2 \
  --log-level INFO
```

**Paste session snippet (Mode B, no :9111 bind):**

```text
2026-01-29 ... [SHADOW SESSION] Orders blockiert durch Risk-Limits: [...]
2026-01-29 ... [SHADOW SESSION] === Session-Zusammenfassung ===
  Steps: 2
  Total Orders: 0
  Filled: 0
  Rejected: 0
  Blocked (Risk): 1
  Fill Rate: 0.0%
  Current Position: 0.000000
```

### 3.4 Port ownership check (recommended)

```bash
lsof -nP -iTCP:9111 -sTCP:LISTEN || true
```

**Paste output (metricsd only):**

```text
COMMAND     PID    USER   FD   TYPE            DEVICE SIZE/OFF NODE NAME
python3.1 83393 frnkhrz    3u  IPv4 0x3cf4a4128cc0937      0t0  TCP *:9111 (LISTEN)
```

### 3.5 Multiprocess shards present (required for Mode B)

```bash
ls -la .ops_local/prom_multiproc/*.db 2>/dev/null || true
```

**Evidence (shards exist):**

```text
-rw-r--r--@ 1 frnkhrz  staff  65536 Jan 29 09:30 .ops_local/prom_multiproc/counter_91492.db
-rw-r--r--@ 1 frnkhrz  staff  65536 Jan 29 09:30 .ops_local/prom_multiproc/gauge_livemax_91492.db
```

### 3.6 Exported metrics include peaktrade_* series (post-session ok)

```bash
curl -fsS "http://127.0.0.1:9111/metrics" \
  | rg '^(# (HELP|TYPE) peaktrade_|peaktrade_)' \
  | head -n 60 || true
```

**Evidence (representative output):**

```text
# HELP peaktrade_risk_limit_utilization Risk limit utilization ratio (clamped 0..1).
# TYPE peaktrade_risk_limit_utilization gauge
peaktrade_risk_limit_utilization{limit_id="max_order_notional"} 1.0
peaktrade_risk_limit_utilization{limit_id="max_total_exposure"} 1.0
peaktrade_risk_limit_utilization{limit_id="max_symbol_exposure"} 1.0
peaktrade_risk_limit_utilization{limit_id="max_open_positions"} 0.2
peaktrade_risk_limit_utilization{limit_id="max_daily_loss_abs"} 0.0
peaktrade_risk_limit_utilization{limit_id="max_daily_loss_pct"} 0.0
# HELP peaktrade_strategy_signals_total Total number of final strategy signal changes emitted (watch/paper/shadow).
# TYPE peaktrade_strategy_signals_total counter
peaktrade_strategy_signals_total{signal="long",strategy_id="ma_crossover"} 1.0
# HELP peaktrade_strategy_decisions_total Total number of strategy decisions finalized (watch/paper/shadow).
# TYPE peaktrade_strategy_decisions_total counter
peaktrade_strategy_decisions_total{decision="entry_long",strategy_id="ma_crossover"} 1.0
# HELP peaktrade_risk_checks_total Total number of risk check evaluations (watch/paper/shadow).
# TYPE peaktrade_risk_checks_total counter
peaktrade_risk_checks_total{check="live_limits.check_orders",result="block"} 1.0
# HELP peaktrade_risk_blocks_total Total number of risk blocks by finite reason allowlist.
# TYPE peaktrade_risk_blocks_total counter
peaktrade_risk_blocks_total{reason="limit:max_order_notional"} 1.0
peaktrade_risk_blocks_total{reason="limit:max_total_exposure"} 1.0
peaktrade_risk_blocks_total{reason="limit:max_symbol_exposure"} 1.0
```

---

## 4) Prometheus-local Verification (PromQL)

### 4.1 Scrape health (stable)

**Query**

```promql
up{job="peak_trade_metricsd"} == 1
```

**Evidence**

```text
instance="host.docker.internal:9111", job="peak_trade_metricsd" => 1
```

---

## 5) Expected Outcome Checklist

- [x] `up{job="peak_trade_metricsd"} == 1` is **stable** (does not flap when session ends)
- [x] `peaktrade_strategy_*` series exist and remain visible after session stop
- [x] `peaktrade_risk_*` series exist and remain visible after session stop
- [x] At least one strategy/risk metric shows **non-zero** update during session runtime
- [x] :9111 is bound by **metricsd only** (sessions do not bind)

---

## 6) Notes / Anomalies

```text
Important: For true Prometheus multiprocess mode, PROMETHEUS_MULTIPROC_DIR must be set in the session process before importing prometheus_client.
```

---

## 7) Verdict

- **Result**: [x] PASS  [ ] FAIL
