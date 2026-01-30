# RUNBOOK: Mode B – Always-on metricsd (Prometheus multiprocess) + Dashboard-Metriken

> **Ziel**: Stabiler, always-on Scrape-Target für Peak_Trade Telemetry über **metricsd** auf **:9111** (Multiprocess-Mode), ohne Scrape-Flapping durch kurzlebige Session-Prozesse.  
> **Scope**: Verdrahtung & Operator-Ablauf für **Mode B Dashboard-Metriken** (Prometheus-local ↔ metricsd ↔ Sessions). **Keine Grafana-Änderungen** notwendig.  
> **Policy**: **NO‑LIVE** (watch-only / paper), **keine Symbol-/Instrument-Labels**, **Allowlist-konforme Labels**, **fail-open** wenn `prometheus_client` fehlt.

---

## 0) Architektur & Verdrahtung

### Komponenten
- **metricsd** (Daemon):
  - Exportiert **&#47;metrics** kontinuierlich auf **:9111**
  - Aggregiert Multiprocess-Shards via `prometheus_client.multiprocess.MultiProcessCollector`
  - **Einziger Prozess**, der den Multiprocess-Dir beim Start **cleared**
- **Session-Prozesse** (shadow/live):
  - Starten **keinen** HTTP-Server in Mode B
  - Rufen nur `ensure_registered()` auf und **updaten** Metriken
- **Prometheus-local**:
  - Scraped **metricsd** als stabilen Job `peak_trade_metricsd` → `host.docker.internal:9111`
  - Optional kann weiterhin ein Session-Job bestehen (Mode A / legacy), ist aber für Mode B **nicht required**

### Port-Matrix (Soll-Zustand)
| Component | Role | Port | Binding | Notes |
|---|---|---:|---|---|
| metricsd | &#47;metrics exporter | 9111 | host (0.0.0.0) | **Stable** scrape target |
| Session (shadow/live) | telemetry writer | — | — | **Keine** Bindings in Mode B |
| Prometheus-local | scrape + UI | (bestehend) | (bestehend) | Scrape: `host.docker.internal:9111` |

> **Best practice**: In Mode B ist :9111 **exklusiv** für metricsd. Sessions dürfen :9111 **niemals** binden.

### Mode-Switch
- `PEAKTRADE_METRICS_MODE`:
  - **Default**: Mode A (bestehendes Verhalten)
  - **Mode B**: `PEAKTRADE_METRICS_MODE="B"`
- Multiprocess Dir (shared zwischen metricsd und Session-Prozessen):
  - **Operator-Override**: `PEAKTRADE_METRICS_MULTIPROC_DIR`
  - **Default**: `.ops_local&#47;prom_multiproc`
  - `PROMETHEUS_MULTIPROC_DIR` wird durch Code gesetzt (metricsd + worker), muss i. d. R. nicht manuell exportiert werden.

---

## 1) Preconditions / Gates

### Hard Gates (müssen erfüllt sein)
- **NO‑LIVE**: keine Broker-Orders / keine live execution enable flags.
- **Label Governance**: keine Symbol-/Instrument-Labels; nur allowlist-konforme Labels.
- **Port Ownership**: :9111 gehört dem metricsd (kein Session-Bind).
- **Fail-Open**: Wenn `prometheus_client` fehlt → kein Crash; Telemetry wird still/no-op.

### Soft Gates (Best practice)
- `PEAKTRADE_METRICS_MULTIPROC_DIR` liegt unter `.ops_local&#47;` (nicht commiten).
- metricsd wird **vor** Session-Start gestartet (damit Scrapes nie "down" sind).
- Prometheus-local Scrape-Config enthält `peak_trade_metricsd`.

---

## 2) Operator Quickstart (lokal)

### 2.1 Pre-flight (Repo + Shell safe)
> **Hinweis**: Wenn dein Prompt `>` / `dquote>` / heredoc zeigt: **Ctrl-C** und neu starten.

```bash
# == PRE-FLIGHT ==
cd /Users/frnkhrz/Peak_Trade 2>/dev/null || cd "$HOME/Peak_Trade" 2>/dev/null || true
pwd
git rev-parse --show-toplevel 2>/dev/null || true
git status -sb 2>/dev/null || true
```

### 2.2 Mode B Env setzen
```bash
export PEAKTRADE_METRICS_MODE="B"
export PEAKTRADE_METRICS_MULTIPROC_DIR=".ops_local/prom_multiproc"
```

### 2.3 Optional: Local Targets UP (Host-Prozesse) + Verify (Prometheus/Grafana)
> **Ziel**: Prometheus scrapt alle lokalen Watch-Only Targets erfolgreich (**0 DOWN**), Grafana kann via Datasource-Proxy `up` abfragen.  
> **Wichtig**: Der Web-Server muss auf **`0.0.0.0`** binden, sonst ist er aus dem Prometheus-Container via `host.docker.internal:8000` nicht erreichbar (Targets bleiben *down*).

```bash
OUT=".local_tmp/bring_targets_up_$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$OUT" .local_tmp/pylibs logs/ai
echo "OUT=$OUT"

# Optional: workspace-lokale Python deps (kein globales pip)
if ! python3 -c "import prometheus_client" >/dev/null 2>&1; then
  python3 -m pip install --target .local_tmp/pylibs prometheus-client
fi
export PYTHONPATH=".local_tmp/pylibs${PYTHONPATH:+:$PYTHONPATH}"

# 1) metricsd exporter (:9111)
python3 -u scripts/obs/pt_metricsd.py --port 9111 --multiproc-dir ".ops_local/prom_multiproc" >"$OUT/metricsd_9111.log" 2>&1 &
echo $! > "$OUT/pid_metricsd_9111.txt"

# 2) AI Live exporter (:9110)  (watch-only)
export PEAK_TRADE_AI_EVENTS_JSONL="logs/ai/ai_events.jsonl"
python3 scripts/obs/emit_ai_live_sample_events.py --out "$PEAK_TRADE_AI_EVENTS_JSONL" --n 5 --interval-ms 10 >/dev/null 2>&1 || true
python3 -u scripts/obs/ai_live_exporter.py >"$OUT/ai_live_9110.log" 2>&1 &
echo $! > "$OUT/pid_ai_live_9110.txt"

# 3) Watch-Only Web metrics (:8000) — bind 0.0.0.0
PEAK_TRADE_PROMETHEUS_ENABLED=1 \
python3 -u scripts/live_web_server.py --host 0.0.0.0 --port 8000 >"$OUT/web_8000.log" 2>&1 &
echo $! > "$OUT/pid_web_8000.txt"

sleep 2

echo "== Quick host port check =="
for P in 8000 9110 9111; do
  (curl -fsS "http://127.0.0.1:${P}/metrics" >/dev/null && echo "UP :$P") || echo "DOWN :$P"
done | tee "$OUT/ports_after.txt"

echo "== Prometheus verify (targets; expect 0 DOWN) =="
PROM_URL="http://localhost:9092"
curl -sS "$PROM_URL/api/v1/targets" > "$OUT/prom_targets.json"
python3 - <<'PY' "$OUT/prom_targets.json" | tee "$OUT/prom_targets_summary.txt"
import json,sys
j=json.load(open(sys.argv[1],"r"))
act=(j.get("data",{}) or {}).get("activeTargets",[]) or []
down=[]
for t in act:
    if t.get("health") != "up":
        lbl=t.get("labels",{}) or {}
        down.append((lbl.get("job"), lbl.get("instance"), t.get("health"), (t.get("lastError") or "")[:160]))
print("activeTargets:", len(act))
print("downTargets:", len(down))
for job,inst,h,err in down[:10]:
    print("-", job, inst, "|", h, "|", err)
PY

echo "== Grafana verify (datasource proxy query up) =="
GRAFANA_URL="http://localhost:3000"
curl -sS "$GRAFANA_URL/api/health" > "$OUT/grafana_health.json"
curl -sS -u "admin:admin" "$GRAFANA_URL/api/datasources/name/prometheus" > "$OUT/grafana_ds_prom.json"
DS_ID="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("id",""))' "$OUT/grafana_ds_prom.json" 2>/dev/null || true)"
echo "DS_ID=${DS_ID:-<EMPTY>}" | tee "$OUT/grafana_ds_id.txt"
if [ -n "$DS_ID" ]; then
  curl -sS -u "admin:admin" \
    "$GRAFANA_URL/api/datasources/proxy/$DS_ID/api/v1/query?query=up" \
    > "$OUT/grafana_proxy_query_up.json"
fi
```

### 2.3 metricsd starten (Terminal A)
Start Script: `scripts/obs/pt_metricsd.py`

```bash
python3 scripts/obs/pt_metricsd.py --port 9111 --multiproc-dir ".ops_local/prom_multiproc" --log-level INFO
```

Erwartung:
- Log enthält „metricsd started … :9111 … multiproc_dir=…“
- Keine Exceptions (fail-open toleriert fehlendes `prometheus_client` → Warning, kein Crash)

### 2.4 Shadow Session kurz starten (Terminal B)
> Start-Command hängt von deinem Shadow-Runbook ab (kurze Duration).  
> Wichtig ist nur: `ensure_registered()` wird ausgeführt und **kein** Session-Server bindet :9111.

Beispiel (pseudo):
```bash
export PEAKTRADE_METRICS_MODE="B"
export PEAKTRADE_METRICS_MULTIPROC_DIR=".ops_local/prom_multiproc"
# ... dein bestehender Shadow-Session Start (kurze Dauer) ...
```

---

## 3) Prometheus-local Verdrahtung (Scrape Config)

### 3.1 Erwarteter Job (Mode B)
In `docs&#47;webui&#47;observability&#47;PROMETHEUS_LOCAL_SCRAPE.yml` muss existieren:

```yaml
- job_name: peak_trade_metricsd
  static_configs:
    - targets: ['host.docker.internal:9111']
```

> **Keep**: Session-Job `peak_trade_session` darf bleiben, ist aber für Mode B optional (legacy / Mode A).

### 3.2 Wiring-Check
- Prometheus-local muss `host.docker.internal` resolve’n (Docker Desktop Standard).
- Wenn Prometheus-local selbst im Container läuft: `host.docker.internal` ist korrekt; alternativ: host-gateway mapping (nur falls nötig; nicht Teil dieses Runbooks).

---

## 4) Verify: PromQL / Expected Evidence

### 4.1 Up Check (stabil)
```promql
up{job="peak_trade_metricsd"} == 1
```

**Expected**: 1 (dauerhaft), auch wenn Session stoppt.

### 4.2 Series Presence (nach Session-Run)
- Serien existieren für:
  - `peaktrade_strategy_*`
  - `peaktrade_risk_*`

**Expected**: Serien bleiben sichtbar, obwohl Session beendet ist (Scrape bleibt stabil; Shards bleiben bis cleanup).

### 4.3 Werte ändern sich während Session läuft
- Wähle eine existierende Counter/Histogram-Serie aus den allowlisted Metrics.
- Prüfe Trend/Delta:

```promql
rate(peaktrade_strategy_*[1m])
```

oder

```promql
increase(peaktrade_risk_*[5m])
```

**Expected**: während Session aktiv: > 0 (oder Histogram-Buckets bewegen sich). Danach kann es auf 0 fallen, Serien bleiben aber weiterhin vorhanden.

---

## 5) Failure Modes & Triage

### A) `up{job="peak_trade_metricsd"}` ist 0
**Checklist**
1. Läuft metricsd? (Terminal A)
2. Port belegt? `lsof -i :9111` (macOS) / `ss -ltnp | grep 9111` (Linux)
3. Prometheus-local target richtig? `host.docker.internal:9111`
4. Docker Networking: kann der Prometheus-container host.docker.internal erreichen?

**Fix**
- metricsd neu starten
- sicherstellen, dass kein anderer Prozess :9111 bindet

### B) Serien fehlen trotz Session-Run
**Checklist**
1. Mode B wirklich aktiv? `echo $PEAKTRADE_METRICS_MODE` muss `B` sein (in Session-Umgebung!)
2. Multiproc dir konsistent?
   - `--multiproc-dir` (metricsd CLI) und `PEAKTRADE_METRICS_MULTIPROC_DIR` (Session) müssen zusammenpassen.
3. `prometheus_client` vorhanden? (wenn nicht: fail-open → keine Serien)

**Fix**
- beide env vars in Session-Prozess setzen
- multiproc dir konsistent machen

### C) values bleiben 0 während Session läuft
**Checklist**
1. Werden die richtigen Code-Pfade ausgeführt? (Telemetrie update calls)
2. Gibt es Gate/Allowlist Filter, der Updates verhindert?
3. Session läuft wirklich lang genug (mind. 30–60s für rate/increase)

---

## 6) Cleanup / Rollback

### Cleanup (Mode B)
- metricsd beendet → Shard-Files bleiben bestehen (bis daemon nächsten Start cleart)
- Best practice: metricsd startet beim nächsten Lauf erneut und cleart `*.db` im Multiproc-Dir.

### Rollback auf Mode A
- `unset PEAKTRADE_METRICS_MODE` oder `export PEAKTRADE_METRICS_MODE="A"`
- Session bindet wieder ihren (legacy) Metrics-Server (bestehendes Verhalten)

> **Wichtig**: Rollback darf Mode A Verhalten **nicht** verändern (nur Gate via env).

---

## 7) Evidence Pack (Operator)

Lege eine Evidence-Datei an (Beispiel):
- `docs&#47;ops&#47;evidence&#47;EV_METRICSD_MODE_B_VERIFY_YYYYMMDD.md`

### Template
```md
# EV: metricsd Mode B Verify (YYYY-MM-DD)

## Setup
- PEAKTRADE_METRICS_MODE=B
- PEAKTRADE_METRICS_MULTIPROC_DIR=.ops_local/prom_multiproc
- metricsd: port 9111

## Commands
- Start metricsd: `python3 scripts/obs/pt_metricsd.py --port 9111 --multiproc-dir .ops_local/prom_multiproc`
- Start short shadow session: (command)

## Observations
- Prometheus target: up{job="peak_trade_metricsd"} == 1 (screenshot / copy)
- Series exist: peaktrade_strategy_* / peaktrade_risk_* (screenshot / copy)
- Values update during session: (query + output)

## Notes / Anomalies
- (none)
```

---

**End of runbook.**
