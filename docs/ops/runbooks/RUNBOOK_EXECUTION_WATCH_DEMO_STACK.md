# RUNBOOK — Execution Watch Demo-Stack (shadow_mvs + ai_live, STRICT NO-LIVE)

**Status:** READY  
**Owner:** ops  
**Risk:** LOW (watch-only demo telemetry)  
**No-Live:** Keine Broker&#47;Exchange-Verbindungen, keine Orders, keine mutierenden API-Methoden.

---

## Zweck

Lokaler Demo-Stack für das Grafana-Dashboard **„Peak_Trade — Execution Watch Overview“**.

Pfad: **Events → Exporter → Prometheus → Grafana** (STRICT NO-LIVE).

---

## Scope

Nutze dieses Runbook, wenn du:

- schnell ein **nicht-leeres** Execution-Watch Dashboard willst (Demo/Operator-UX),
- dabei **keine** Live-Execution startest,
- und es genügt, dass **AI Live** + **Shadow MVS** Panels „grün“ sind (HTTP/Execution-Watch-API Panels dürfen im Demo leer bleiben).

---

## Voraussetzungen

- Repo ausgecheckt, Python-Env aktiv (uv/venv nach lokalem Standard).
- Docker Desktop läuft.
- Ports frei:
  - Prometheus-local: `localhost:9092`
  - Grafana: `localhost:3000`

---

## Start (Demo-Stack)

Im Terminal (Repo-Root):

```bash
cd ~/Peak_Trade

# 1) Shadow MVS + Prometheus-local + Grafana (Legacy-Stack entfernt)
#    Alternative: docker compose -f docker/docker-compose.obs.yml (Ops Runner, Stage1)
#    Siehe docs/DOCKER_KOMPLETT_UEBERSICHT.md

# 2) AI Live Demo Events (STRICT NO-LIVE; schreibt nur JSONL)
mkdir -p logs/ai
export PEAK_TRADE_AI_EVENTS_JSONL="$PWD/logs/ai/ai_events.jsonl"
python3 scripts/obs/emit_ai_live_sample_events.py --out "$PEAK_TRADE_AI_EVENTS_JSONL"

# 3) (Optional) ai_live exporter starten, falls nicht schon aktiv (Port Contract v1: :9110)
# Hinweis: Der Exporter MUSS auf dieselbe JSONL zeigen (PEAK_TRADE_AI_EVENTS_JSONL), sonst bleibt decisions_total leer.
PEAK_TRADE_AI_EVENTS_JSONL="$PEAK_TRADE_AI_EVENTS_JSONL" \
PEAK_TRADE_AI_RUN_ID="demo" \
PEAK_TRADE_AI_COMPONENT="execution_watch" \
python3 scripts/obs/ai_live_exporter.py --port 9110 >/tmp/ai_live_exporter.log 2>&1 &

# 4) Kurz warten (Prometheus scrape_interval ~5s)
sleep 10
```

---

## Checks (Prometheus)

### A) Targets (müssen UP sein)

Öffne:
- `http://localhost:9092/targets`

Erwartet:
- `job="shadow_mvs"` ist **UP**
- `job="ai_live"` ist **UP**

### B) Minimal-Queries (müssen Resultate liefern)

```bash
curl -sG 'http://localhost:9092/api/v1/query' --data-urlencode 'query=up{job="shadow_mvs"}' && echo
curl -sG 'http://localhost:9092/api/v1/query' --data-urlencode 'query=up{job="ai_live"}' && echo
curl -sG 'http://localhost:9092/api/v1/query' --data-urlencode 'query=peaktrade_ai_decisions_total' && echo
curl -sG 'http://localhost:9092/api/v1/query' --data-urlencode 'query=peaktrade_signals_total' && echo
curl -sG 'http://localhost:9092/api/v1/query' --data-urlencode 'query=peaktrade_orders_approved_total' && echo
curl -sG 'http://localhost:9092/api/v1/query' --data-urlencode 'query=peaktrade_orders_blocked_total' && echo
```

Interpretation:
- `up{job="shadow_mvs"}` → `result != []` ⇒ Shadow-MVS Exporter wird gescraped
- `up{job="ai_live"}` → `result != []` ⇒ ai_live Exporter wird gescraped
- `peaktrade_ai_decisions_total` → **3 Serien** (accept/reject/noop; run_id=demo) ⇒ Events werden gelesen
- `peaktrade_signals_total` / `peaktrade_orders_approved_total` / `peaktrade_orders_blocked_total` → `result != []` ⇒ Trade-Flow Counter sind im Demo-Stack vorhanden (Mock-Exporter liefert deterministische Werte)

---

## Dashboard-Interpretation (Grafana)

Öffne Grafana:
- `http://localhost:3000`

Dashboard:
- **Peak_Trade → execution → Peak_Trade — Execution Watch Overview**

### Demo gesund (erwartet „grün“/Data)

- **AI Live Up (1/0)** = UP
- **UP (job=shadow_mvs)** = UP
- **Exporter (shadow_mvs_up)** = UP
- **Contract: pipeline events metric present** = PRESENT
- **Decisions / min (1m) by decision** zeigt Linien
- **Top reject reasons** zeigt z.B. `none` &#47; `risk_limit`
- **Pipeline events rate (by stage)** zeigt Timeseries

### Darf „No data“ sein im Demo (erwartet im Minimal-Setup)

- Panels mit Execution-Watch API/HTTP:
  - req&#47;s by endpoint
  - latency p95 by endpoint
  - JSONL read errors
- **Contract: execution watch metrics present** = MISSING
- **AI Active (last 30s)**, **last decision age** etc., wenn der Demo-Emitter nicht kontinuierlich läuft

---

## Troubleshooting (mini)

### 1) `up{job="ai_live"}` ist OK, aber `peaktrade_ai_decisions_total` ist leer

Ursache (typisch):
- laufender `ai_live_exporter` zeigt **nicht** auf `PEAK_TRADE_AI_EVENTS_JSONL`

Fix (snapshot-only):
- Exporter neu starten **mit gesetzter Env** (siehe Start-Block)
- Events erneut emittieren

### 2) Dashboard zeigt „No data“, aber Prometheus Queries liefern Daten

Checks:
- Zeitbereich: **Last 15 minutes**
- Refresh (oben rechts)

---

## Stop

```bash
cd ~/Peak_Trade

# Stop: Legacy-Stack (shadow_mvs_local_* entfernt)
#    Bei Ops Runner: docker compose -f docker/docker-compose.obs.yml down

# Falls ai_live_exporter im Foreground läuft: Ctrl-C im entsprechenden Terminal
```

---

## Referenzen

- Stack start/stop: Legacy (entfernt). Alternative: `docker/docker-compose.obs.yml`
- AI Live Exporter: `scripts/obs/ai_live_exporter.py`
- Demo-Events: `scripts/obs/emit_ai_live_sample_events.py`
- Dashboard JSON: Legacy (entfernt). Siehe docs/DOCKER_KOMPLETT_UEBERSICHT.md
