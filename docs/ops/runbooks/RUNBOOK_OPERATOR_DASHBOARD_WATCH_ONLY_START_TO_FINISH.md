# RUNBOOK — Operator Dashboard (Watch-Only) — Start → Finish (Peak_Trade)

**Status:** READY FOR IMPLEMENTATION (v1.0)  
**Maintainer:** ops / aiops  
**Risk:** LOW (read-only, observe-only)  
**Scope:** Operator möchte **nur zuschauen** (Monitoring), keine Execution-Controls

---

## 0) Ziel & Nicht-Ziele

### Ziel
Ein lokales Operator-Dashboard starten, um **der AI beim Arbeiten zuzuschauen** (read-only):

- Session/Run-Status
- AI Activity Feed (Events)
- Health / Alerts
- deterministische Snapshots (HTML/JSON) exportieren

### Nicht-Ziele (Governance)
- **Keine** Start/Stop/Switch/Order-Aktionen im UI
- **Keine** Secrets/Execution-Keys im Dashboard-Prozess
- **Keine** UI-Controls, die die Trading-Pipeline beeinflussen könnten

---

## 1) Voraussetzungen

### 1.1 System
- macOS / Linux
- Python (Repo-Setup via `.venv`)
- Browser lokal

### 1.2 Datenquellen (Watch-Only)
Mindestens eine Quelle muss existieren:
- **Live Sessions Registry Artefakte** (z.B. `reports&#47;experiments&#47;live_sessions&#47;*.json`)
- **Live Runs Artefakte** (z.B. `live_runs&#47;<run_id>&#47;...`)
- oder ein laufender Prozess, der diese Artefakte schreibt (separater Runner)

> Das Dashboard ist **read-only** und liest nur Artefakte/Status aus Dateien.

---

## 2) Pre-Flight (Repo + Continuation-Guard)

> Wenn du im Terminal gerade einen Prompt wie `>`, `dquote>`, `heredoc>` siehst: **Ctrl-C**.

### Step 2.1 — In Repo wechseln (1 Befehl)
```bash
cd /Users/frnkhrz/Peak_Trade
```

### Step 2.2 — Virtuelle Umgebung aktivieren + Dependencies
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Step 2.3 — Datenquelle kurz prüfen (read-only)
```bash
# Sessions Registry (falls vorhanden)
ls -la reports/experiments/live_sessions 2>/dev/null | head -20 || true

# Live Runs (falls vorhanden)
ls -la live_runs 2>/dev/null | head -50 || true
```

---

## 3) Dashboard auswählen (zwei Optionen)

### Option A (empfohlen für “AI zuschauen”): WebUI Dashboard v1.x
**Wenn du** Sessions/Live-Track/Telemetry/Alerts + deterministische Status-Snapshots willst.

**Start (stabil, ohne reload):**
```bash
uvicorn src.webui.app:app --host 127.0.0.1 --port 8000
```

**Start (Dev, auto-reload):**
```bash
python3 scripts/run_web_dashboard.py
```

**Aufrufen:**
- Home: `http://127.0.0.1:8000/`
- OpenAPI: `http://127.0.0.1:8000/docs`

### Option B (empfohlen für “Run Monitoring”): Live Web Dashboard v0 (Phase 67)
**Wenn du** `live_runs&#47;`-basierte Runs mit Auto-Refresh HTML + Run-Snapshot/Tail/Alerts willst.

**Start:**
```bash
python3 scripts/live_web_server.py --host 127.0.0.1 --port 8000
```

**Mit Run-Verzeichnis Override (falls du nicht `live_runs&#47;` nutzt):**
```bash
python3 scripts/live_web_server.py \
  --host 127.0.0.1 \
  --port 8000 \
  --base-runs-dir live_runs \
  --auto-refresh-seconds 5
```

**Aufrufen:**
- Dashboard: `http://127.0.0.1:8000/` (alias auch `/dashboard`)
- Health: `http://127.0.0.1:8000/health`

---

## 4) Verification (schnelle “läuft & ist read-only” Checks)

### 4.1 WebUI v1.x
- Browser öffnet `http://127.0.0.1:8000/`
- `http://127.0.0.1:8000/docs` zeigt nur **read-only** (GET) APIs für Monitoring (keine Start/Stop/Order-Endpunkte)
- Snapshot-Endpunkte liefern Daten:
  - `http://127.0.0.1:8000/api/live/status/snapshot.json`
  - `http://127.0.0.1:8000/api/live/status/snapshot.html`

### 4.2 Live Web Dashboard v0
- `http://127.0.0.1:8000/health` liefert `{"status":"ok"}` (HTTP 200)
- `http://127.0.0.1:8000/runs` liefert eine Liste (JSON; ggf. leer, wenn keine Runs da sind)

---

## 5) Deterministische Snapshot-Exports (HTML/JSON)

> “Deterministisch” heißt hier: **gleicher Endpoint → gleiche Dateinamen** (kein Timestamp im Filename). Wenn du archivieren willst, kopiere danach separat in ein datiertes Verzeichnis.

### 5.1 Export: WebUI v1.x (Status Snapshot)
```bash
mkdir -p out/operator_dashboard

curl -fsS "http://127.0.0.1:8000/api/live/status/snapshot.json" \
  -o "out/operator_dashboard/status_snapshot.json"

curl -fsS "http://127.0.0.1:8000/api/live/status/snapshot.html" \
  -o "out/operator_dashboard/status_snapshot.html"
```

**Optional (Sessions Registry als JSON):**
```bash
curl -fsS "http://127.0.0.1:8000/api/live_sessions?limit=50" \
  -o "out/operator_dashboard/live_sessions.json"
```

### 5.2 Export: Live Web Dashboard v0 (Runs + Run Snapshot/Tail/Alerts)
```bash
mkdir -p out/operator_dashboard

# Runs-Liste (JSON)
curl -fsS "http://127.0.0.1:8000/runs" \
  -o "out/operator_dashboard/runs.json"
```

**Run-spezifisch (Run-ID einsetzen):**
```bash
RUN_ID="<run_id>"

curl -fsS "http://127.0.0.1:8000/runs/${RUN_ID}/snapshot" \
  -o "out/operator_dashboard/run_snapshot.json"

curl -fsS "http://127.0.0.1:8000/runs/${RUN_ID}/tail?limit=200" \
  -o "out/operator_dashboard/run_tail.json"

curl -fsS "http://127.0.0.1:8000/runs/${RUN_ID}/alerts?limit=50" \
  -o "out/operator_dashboard/run_alerts.json"
```

---

## 6) (Optional) Safety Proof Snapshot (Phase 74, read-only)

Wenn du zusätzlich einen Governance-freundlichen Snapshot willst (“Live bleibt locked”):
```bash
mkdir -p out/operator_dashboard

python3 scripts/export_live_audit_snapshot.py \
  --output-json out/operator_dashboard/live_audit_snapshot.json \
  --output-markdown out/operator_dashboard/live_audit_snapshot.md
```

---

## 7) Shutdown

### Step 7.1 — Dashboard stoppen
- Im Terminal mit dem laufenden Server: **Ctrl-C**

### Step 7.2 — Port belegt? (häufigster Fehler)
```bash
# macOS / Linux:
lsof -nP -iTCP:8000 -sTCP:LISTEN || true
```

---

## 8) Troubleshooting (Operator-FAQ)

### Problem: “No runs found” / leere Liste
- Prüfe, ob `live_runs&#47;` existiert und ob dort Run-Verzeichnisse liegen.
- Prüfe, ob `--base-runs-dir` korrekt gesetzt ist.
- Hinweis: Das Dashboard **erzeugt keine Runs**. Es zeigt nur existierende Artefakte an.

### Problem: “Run not found”
- Run-ID stimmt nicht oder liegt nicht unter dem konfigurierten `base_runs_dir`.

### Problem: ImportError / Module not found (uvicorn, fastapi, etc.)
- Stelle sicher, dass `.venv` aktiv ist und `pip install -r requirements.txt` erfolgreich lief.

### Problem: Port 8000 already in use
- Starte auf anderem Port, z.B. `--port 8080`, oder stoppe den Prozess, der auf 8000 lauscht (siehe Step 7.2).

### Problem: “Ich will zuschauen, aber es passiert nichts”
- Du brauchst einen separaten Prozess, der Artefakte schreibt (Session Runner / Orchestrator / Workflow).  
  Dieses Runbook deckt **nur** das watch-only Dashboard ab.

---

## 9) Referenzen

- `docs/webui/DASHBOARD_OVERVIEW.md` — Dashboard-Übersicht (URLs, Datenfluss, read-only)
- `docs/webui/DASHBOARD_DATA_CONTRACT_v0.md` — Data Contract (Artifacts) für Dashboard v0
- `docs/webui/DASHBOARD_API_CONTRACT_v0.md` — API Contract (Read-only) für Dashboard v0
- `docs/CLI_CHEATSHEET.md` — “Live Web Dashboard (Phase 67)” Quick Commands
- `docs/LIVE_OPERATIONAL_RUNBOOKS.md` — Abschnitt “10d Live Web Dashboard v0”
- `scripts&#47;run_web_dashboard.py` — WebUI dev runner (reload)
- `scripts&#47;live_web_server.py` — Live Dashboard server (Phase 67)
- `scripts&#47;export_live_audit_snapshot.py` — Read-only Audit Snapshot (Phase 74)
