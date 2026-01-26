# RUNBOOK — AI Live Ops Pack (Local, Snapshot-only)

**Status:** READY  
**Owner:** ops  
**Risk:** LOW (watch-only; read-only)  
**No-Live:** Keine Trading-/Execution-Aktionen; keine mutierenden Web-API-Methoden.

---

## 1) Purpose
Dieses Runbook beschreibt, wie du AI Live Telemetry lokal **startest**, **verifizierst** und **troubleshootest** – deterministisch, snapshot-only, file-backed evidence.

---

## 2) Scope
Nutze dieses Runbook, wenn:
- Prometheus-local auf `:9092` läuft und `job="ai_live"` scrapen soll.
- Der AI Live Exporter lokal auf `:9110` laufen soll (Port Contract v1).
- Du einen **kanonischen One-Command Proof** brauchst (OUT dir + Summary + PromQL snapshots).

---

## 3) Preconditions / Contracts

### Port Contract v1 (lokal)
- **Exporter Port:** `:9110`
- **Warum:** Prometheus-local scrapt `job="ai_live"` fest auf `host.docker.internal:9110`.
- **Wichtig:** Kein stiller Fallback auf andere Ports (würde Prometheus/Grafana “leer” wirken lassen).

### Python Env Contract (deterministisch)
Die Ops-Skripte wählen standardmäßig:
- `uv run python` (wenn `uv` verfügbar ist)
- sonst `python3`

Override (optional):
```bash
export PY_CMD="uv run python"
# oder:
export PY_CMD="python3"
```

---

## 4) Start (lokal)

### 4.1 Prometheus-local (und optional Grafana)
Wenn du den lokalen Observability-Stack verwendest:
```bash
bash scripts/obs/grafana_local_up.sh
```

### 4.2 Exporter starten (watch-only)
```bash
mkdir -p logs/ai
export PEAK_TRADE_AI_EVENTS_JSONL="logs/ai/ai_events.jsonl"
export PEAK_TRADE_AI_RUN_ID="demo"
export PEAK_TRADE_AI_COMPONENT="execution_watch"
export PEAK_TRADE_AI_EXPORTER_PORT="9110"

python3 -u scripts/obs/ai_live_exporter.py --port 9110
```

### 4.3 Sample Events emittieren (optional, zum “warmup”)
```bash
python3 -u scripts/obs/emit_ai_live_sample_events.py --out "logs/ai/ai_events.jsonl" --n 50 --interval-ms 200
```

---

## 5) Verify (canonical, one command proof)

## 5.0 Quickstart (recommended): One Command Wrapper

Empfohlen (Single Source of Truth, snapshot-only, file-backed evidence; keine Inline-Code-Duplizierung im Runbook):

```bash
bash scripts/obs/ai_live_local_verify.sh
```

**Outputs (wo du nachsehen sollst):**
- Wrapper OUT: `.local_tmp/ai_live_local_verify_<timestamp>`
  - `OPERATOR_NOTE.txt`
  - `MANIFEST_SHA256.txt`
  - `KEY_MATERIAL_SCAN.txt` (head-only heuristic)
  - `LATEST_DIRS.txt` (zeigt zuletzt erzeugte `.local_tmp/ai_live_ops_verify_*` und `.local_tmp/ai_live_activity_demo_*`)
- Canonical verify evidence: `.local_tmp/ai_live_ops_verify_<timestamp>`
- Activity demo evidence: `.local_tmp/ai_live_activity_demo_<timestamp>` (nur wenn Exporter auf `:9110` erreichbar ist)

### 5.1 Canonical Proof Command
```bash
chmod +x scripts/obs/ai_live_ops_verify.sh
bash scripts/obs/ai_live_ops_verify.sh
```

### 5.2 Evidence Artifacts (file-backed)
Das Script schreibt ein OUT-Verzeichnis (Default):
```text
.local_tmp/ai_live_ops_verify_<timestamp>
```
und darin u.a.:
- `AI_LIVE_OPS_SUMMARY.txt` (Hard-Checks + Verdict)
- `PROM_REQUIRED_SERIES.tsv` (PromQL + result_count + scalar values)
- `prom&#47;*.json` (Prometheus Query Snapshots)
- `exporter_metrics.txt` (Exporter `/metrics` snapshot)

### 5.3 Hard Checks (Finish-ready)
Das Script muss in der Summary zeigen (und als Gate enforce):
- `up_jobs_rc=3` (jobs: `ai_live`, `peak_trade_web`, `shadow_mvs`)
- `heartbeat_rc=1`
- `decisions_sum > 0`
- `run_id_count >= 1`
- `last_event_ts_by_run_id_count >= 1`

---

## 5.4 Generate activity (demo)

Ziel: In einem deterministischen lokalen Demo-Run sicherstellen, dass `peaktrade_ai_decisions_total` und `run_id`‑scoped Serien **non-empty** sind (Prometheus snapshots + Exporter snapshot).

Single command (snapshot-only, file-backed evidence; keine Pipes):

```bash
bash scripts/obs/ai_live_activity_demo.sh
```

Defaults:
- `RUN_ID=demo`
- Ports: Prometheus `:9092`, Exporter `:9110`
- Evidence dir: `.local_tmp&#47;ai_live_activity_demo_<timestamp>`

Override (optional):
```bash
RUN_ID="demo" COMPONENT="execution_watch" bash scripts/obs/ai_live_activity_demo.sh
```

---

## 6) Known-good PromQL (Operator Queries)

### 6.1 Liveness / Targets
```promql
up{job=~"ai_live|peak_trade_web|shadow_mvs"}
max(up{job="ai_live"})
```

### 6.2 AI Activity
```promql
peaktrade_ai_live_heartbeat
sum(peaktrade_ai_decisions_total)
sum(peaktrade_ai_actions_total)
```

### 6.3 Run-ID Drilldown Readiness
```promql
count(count by (run_id) (peaktrade_ai_decisions_total))
count(peaktrade_ai_last_event_timestamp_seconds_by_run_id)
```

### 6.4 Freshness (worst-case age in seconds)
```promql
max(clamp_min(time() - max by (source) (peaktrade_ai_last_event_timestamp_seconds), 0))
```

### 6.5 Quality (5m)
```promql
increase(peaktrade_ai_events_parse_errors_total[5m])
increase(peaktrade_ai_events_dropped_total[5m])
```

### 6.6 Latency (p95/p99, 5m)
```promql
histogram_quantile(0.95, sum by (le) (rate(peaktrade_ai_decision_latency_ms_bucket[5m])))
histogram_quantile(0.99, sum by (le) (rate(peaktrade_ai_decision_latency_ms_bucket[5m])))
```

---

## 7) Troubleshooting (Snapshot-only)

### 7.1 `:9110` ist belegt (Port Contract violation)
```bash
lsof -nP -iTCP:9110 -sTCP:LISTEN
```
Stoppe den Listener und starte den Exporter neu (empfohlen).

### 7.2 Prometheus ready, aber `job="ai_live"` nicht UP
- Prüfe, ob der Exporter wirklich auf `:9110` läuft und `/metrics` liefert:
```bash
curl -fsS http://127.0.0.1:9110/metrics > /tmp/pt_ai_live_exporter_metrics.txt
head -n 30 /tmp/pt_ai_live_exporter_metrics.txt
```
- Prüfe Prometheus Targets:
```bash
curl -fsS http://127.0.0.1:9092/api/v1/targets > /tmp/pt_prom_targets.json
head -c 2000 /tmp/pt_prom_targets.json
```

### 7.3 `run_id_count` ist 0
Das ist fast immer “kein Traffic / keine Events”. Emittiere Sample Events (siehe 4.3) und rerun den Verify.

---

## 8) References
- Canonical verify script:
```text
scripts/obs/ai_live_ops_verify.sh
```
- Exporter:
```text
scripts/obs/ai_live_exporter.py
```
- Dashboard/Observability doc:
```text
docs/webui/observability/README.md
```
