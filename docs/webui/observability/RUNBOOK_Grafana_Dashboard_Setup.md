# Peak_Trade Observability Runbook (stabile Datenflüsse, alles im Grafana)

**Scope:** Betrieb/Verifikation der Observability-Kette **ohne Änderungen an Docker/Compose-Konfigurationen** (nur Start/Restart, Read-only Checks, Grafana-Dashboards/Queries).  
**Zielbild:** Ein *Unified Operator Dashboard* zeigt **AI Live** + **Shadow/Health** + **System/Ports** konsistent, mit klaren Datasource-Regeln.

---

## 0. Architektur in einem Bild

### Komponenten & Ports
| Domain | Producer (Quelle) | Endpoint | Scraped by | Prom Port | Grafana DS (UID) |
|---|---|---:|---|---:|---|
| Grafana UI | grafana container | `:3000` | — | — | — |
| Prom (Shadow stack) | prometheus-local | `:9092` | — | 9092 | `prom_local_9092` |
| Prom (AI Live ops) | prometheus-local | `:9094` | — | 9094 | `prom_ai_live_9094` |
| Prom (Observability) | prometheus-local | `:9095` | — | 9095 | `prom_observability_9095` |
| AI Live Exporter | host python proc (ai_live_restart) | `:9110/metrics` | job=`ai_live` | 9094 *(typisch)* | `prom_ai_live_9094` |
| Shadow MVS Exporter | host/stack proc | `:9109/metrics` | job=`shadow_mvs` | 9092 | `prom_local_9092` |
| peak_trade_web | web service | `:8000/metrics` | job=`peak_trade_web` | 9092 | `prom_local_9092` |
| peak_trade_metricsd | metrics daemon | `:9111/metrics` | job=`peak_trade_metricsd` | 9092 | `prom_local_9092` |

> **Wichtig:** „Grafana/Prometheus laufen“ ≠ „Telemetry-Produzenten laufen“.  
> Health/Shadow-Panels sind *korrekt leer*, wenn `9109/8000/9111` nicht laufen oder nicht gescraped werden.

---

## 1. Datasource-Regeln (damit alles in EINEM Dashboard funktioniert)

### 1.1 Unified Dashboard Grundregel
- **AI Live Panels** (peaktrade_ai_*) → **Default** `prom_ai_live_9094` (Variable `$ds`).
- **Shadow/Health/Pipeline Panels** (shadow_mvs, pipeline, contracts) → **hart gepinnt** auf `prom_local_9092`.
- **Stack Fingerprint Panels** → **prom_local_9092** und **ohne stack-label-Abhängigkeit** (Queries nutzen `up`, `count(up)`, `count by(job) (up)`).

Diese Regeln vermeiden, dass ein `$ds=9094` die Shadow/Health-Kacheln „wegfiltert“.

---

## 2. Start/Restart (deterministisch, ohne „no configuration file provided“)

### 2.1 Shadow MVS Grafana+Prom (9092 + 3000)
**Helper:** `scripts/obs/shadow_mvs_up.sh` (auto-resolve compose files)

```bash
./scripts/obs/shadow_mvs_up.sh ps
./scripts/obs/shadow_mvs_up.sh up
# optional:
./scripts/obs/shadow_mvs_up.sh restart
./scripts/obs/shadow_mvs_up.sh logs
```

### 2.2 Prometheus 9094/9095 (AI-Live-ops + Observability)
**Helpers:**
- `scripts/obs/prom_9094_9095_up_and_verify.sh`
- `scripts/obs/prom_9094_9095_restart.sh`
- Resolver: `scripts/obs/resolve_obse_ailive_compose.py` (funktioniert auch nach `down`, via lokale Overrides)

```bash
./scripts/obs/prom_9094_9095_up_and_verify.sh
# bei "stuck" / Restart-loop:
./scripts/obs/prom_9094_9095_restart.sh
```

> **Lokale Overrides (Ports 9094/9095):** liegen bei dir unter `.ops_local/compose_overrides/*` (gitignored).  
> Diese sind bewusst *lokal* und ändern keine repo/Docker-Defaults.

### 2.3 AI Live Exporter (9110) – deterministisch via repo-lokalem venv
**Helper:** `scripts/obs/ai_live_restart.sh` (nutzt `.venv_obs` fallback)

Einmalig (falls venv noch nicht existiert):
```bash
python3 -m venv .venv_obs
. .venv_obs/bin/activate
pip install -U pip wheel
pip install prometheus-client
```

Start/Restart:
```bash
./scripts/obs/ai_live_restart.sh 9110
curl -fsS http://localhost:9110/metrics | head
```

**Echte Events-Datei** (statt Demo):
```bash
export PEAK_TRADE_AI_EVENTS_JSONL="/ABSOLUTER/PFAD/ZU/ai_events.jsonl"
./scripts/obs/ai_live_restart.sh 9110
```

> **No data bei AI decisions:** Wenn der Exporter nur Heartbeat ausgibt, fehlen Samples → keine Serien in Prometheus. Ursache: Events-JSONL leer/keine Events.

---

## 3. Minimaler „Sanity Gate“ (5 Minuten, stabiler Datenfluss)

### 3.1 Container + Health
```bash
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E 'grafana|prometheus|:3000|:9092|:9094|:9095' || true

curl -fsS http://localhost:3000/api/health
curl -fsS http://localhost:9092/-/ready
curl -fsS http://localhost:9094/-/ready
curl -fsS http://localhost:9095/-/ready
```

### 3.2 Prom Targets (UP/Down)
```bash
# 9092: shadow/web/metricsd (und evtl ai_live)
curl -fsS "http://localhost:9092/api/v1/query?query=up" | python3 -m json.tool | head -n 80

# 9094: ai_live
curl -fsS "http://localhost:9094/api/v1/query?query=up%7Bjob%3D%22ai_live%22%7D" | python3 -m json.tool
```

### 3.3 AI Live: Serien existieren wirklich?
```bash
curl -fsS http://localhost:9110/metrics | grep -E '^peaktrade_ai_' | head -n 30 || true
curl -fsS "http://localhost:9094/api/v1/series?match[]=peaktrade_ai_decisions_total" | python3 -m json.tool | head -n 60
```

---

## 4. Grafana: Unified Dashboard Betrieb

### 4.1 URL + Login
- URL: `http://localhost:3000`
- User/Pass: `admin / admin`
- Unified: `Dashboards → Peak_Trade — Operator Unified`

### 4.2 Wenn Panels „nicht aktualisieren“ (Provisioning/Caching)
Read-only/low-risk Vorgehen:
1) Hard refresh im Browser (`Cmd+Shift+R`)
2) Zeitbereich auf „Last 6h“ stellen, dann zurück auf „Last 15m“
3) Grafana Container restart (nur Grafana):
```bash
docker restart peaktrade-shadow-mvs-grafana-1
```

### 4.3 Wenn trotz Prom-Daten weiterhin „No data“
**Prinzip:** Panel kann nur anzeigen, was in der *verwendeten Datasource* existiert.

**Read-only Diagnose:**
- Panel (⋯) → **Inspect → Query** → PromQL kopieren
- Dann dieselbe PromQL direkt gegen den passenden Prom ausführen:
```bash
# Beispiel: Query aus Panel einfügen (URL-encoden über --data-urlencode)
curl -fsS -G "http://localhost:9092/api/v1/query" --data-urlencode 'query=<PROMQL>' | python3 -m json.tool
curl -fsS -G "http://localhost:9094/api/v1/query" --data-urlencode 'query=<PROMQL>' | python3 -m json.tool
```

---

## 5. Typische „No data / 0“-Ursachen (Mapping)

### 5.1 AI Live Panels (Decisions/Latency/Actions) leer
**Ursache:** Exporter liefert HELP/TYPE aber keine Samples → keine Serien in Prom.  
**Check:**
- `curl :9110/metrics | rg peaktrade_ai_decisions_total` (muss Sample-Zeilen zeigen)
- `series?match[]=peaktrade_ai_decisions_total` auf 9094

### 5.2 Signals / Orders Approved/Blocked / Signals per min leer
**Ursache:** Diese Metriken kommen **nicht** aus AI Live, sondern aus `metricsd` oder Shadow/Web.  
**Check:**
- `up{job="peak_trade_metricsd"}` auf 9092
- Metrikfamilien im 9092 Prom vorhanden? (`/api/v1/label/__name__/values` + grep)

### 5.3 Shadow Health / Pipeline leer
**Ursache:** `shadow_mvs` Exporter (9109) nicht aktiv oder nicht gescraped.  
**Check:**
- `up{job="shadow_mvs"}` auf 9092
- Wenn `up=0`: Shadow runner/exporter starten (je nach Setup) – sonst bleiben die invariants korrekt „MISSING“.

### 5.4 Stack Fingerprint leer
**Ursache:** Früher stack-label filterte weg; aktuell muss `知道` sein:
- Queries nutzen `count(up)`, `count by(job)(up)`, `up==1`.
**Check:** direkt auf 9092:
```bash
curl -fsS -G "http://localhost:9092/api/v1/query" --data-urlencode 'query=count(up)' | python3 -m json.tool
```

---

## 6. Stabilitätsregeln (damit es nicht wieder „driftet“)

1) **Docker/Compose bleibt wie es ist**. Anpassungen sind *nur*:
   - Start/Restart über Helper-Skripte
   - Grafana Dashboard Queries / Generator
2) **Datasource Ownership** ist fix:
   - AI → 9094
   - Shadow/Health → 9092
3) **Producer müssen laufen**, sonst bleibt Dashboard leer (kein „Grafana Bug“).
4) **Rebuild bleibt Zero-Diff**:
   - `python3 scripts/obs/build_operator_unified_dashboard.py`
   - `git diff --exit-code docs/webui/observability/grafana/dashboards/overview/peaktrade-operator-unified.json`

---

## 7. Operator-Checkliste (Read-only, kurz)

1) `curl :3000/api/health`
2) `curl :9092/-/ready ; :9094/-/ready ; :9095/-/ready`
3) `curl :9094/api/v1/query?query=up{job="ai_live"}`
4) `curl :9110/metrics | head`
5) `curl :9092/api/v1/query?query=up` → sind `shadow_mvs/web/metricsd` up?
6) Unified Dashboard öffnen → Zeitfenster 6h → 15m → Hard refresh
7) Bei No data: Panel Inspect Query → PromQL gegen richtigen Prom curl'n

---

## 8. Links (lokal)
- Grafana: `http://localhost:3000`
- Unified Dashboard: `http://localhost:3000/d/peaktrade-operator-unified/peak-trade-operator-unified`
- Prometheus 9092: `http://localhost:9092`
- Prometheus 9094 Targets: `http://localhost:9094/targets`
- Prometheus 9095: `http://localhost:9095`
- AI Live Exporter: `http://localhost:9110/metrics`
