# RUNBOOK — Dashboard Watch-Only v0 — Start → Finish (Snapshot-only)

**Status:** READY  
**Owner:** ops  
**Risk:** LOW (read-only, watch-only)  
**No-Live:** Keine Trading-/Execution-Aktionen; keine mutierenden Web-API-Methoden.

---

## 1) Zweck
Dieses Runbook beschreibt den **lokalen** Start → Betrieb → Shutdown des Watch-Only Dashboards.

---

## 2) Preconditions (Artefakte)
- Runs Directory (Default im Start-Script: `live_runs`)
- Pro Run (minimal):
  - `meta.json`
  - `events.csv` oder `events.parquet`

Hinweis (Docs Token Policy):
- Für **illustrative** Inline-Code Pfad-Tokens mit Slash gilt Encoding `&#47;` (z.B. `live_runs&#47;`), siehe `docs/ops/runbooks/RUNBOOK_DASHBOARD_WATCH_ONLY_V01B.md`.

---

## 3) Pre-Flight (Repo + Continuation Guard)
Wenn dein Terminal Prompt `>` / `dquote>` / heredoc anzeigt: **Ctrl-C**.

```bash
cd /Users/frnkhrz/Peak_Trade
pwd
git rev-parse --show-toplevel
git status -sb
```

---

## 4) Start Server (Local)
Start Script:
- `scripts/live_web_server.py`

Minimal:

```bash
python scripts/live_web_server.py --host 127.0.0.1 --port 8000
```

Optional: Runs Directory Override (wenn deine Artefakte nicht im Default liegen):

```bash
python scripts/live_web_server.py --host 127.0.0.1 --port 8000 --base-runs-dir live_runs --auto-refresh-seconds 5
```

---

## 5) Open UI (Watch-Only)
Browser:
- `http://127.0.0.1:8000/watch`
- `http://127.0.0.1:8000/watch/runs/{run_id}`
- `http://127.0.0.1:8000/sessions/{run_id}` (Alias)

---

## 6) API (Read-only) — Quick Checks
One-shot Snapshots (ohne watch):

```bash
python -c "import requests; print(requests.get('http://127.0.0.1:8000/api/v0/health').status_code)"
```

Alternativ via Browser/HTTP Client:
- `&#47;api&#47;v0&#47;health`
- `&#47;api&#47;v0&#47;runs`

---

## 6.1) Optional: Prometheus Observability (watch-only)

**Ziel:** Service-Health/HTTP-Metriken via Prometheus (und optional Grafana) sichtbar machen.  
**Wichtig:** `&#47;metrics` existiert nur, wenn `PEAK_TRADE_PROMETHEUS_ENABLED=1` gesetzt ist **und** `prometheus_client` im Environment verfügbar ist.

### A) Server mit Env-Flag starten

Beim Start des Watch-Only Servers das Env-Flag setzen (Beispiel):

```bash
PEAK_TRADE_PROMETHEUS_ENABLED=1 python scripts/live_web_server.py --host 127.0.0.1 --port 8000
```

### B) Prometheus/Grafana lokal starten (Docker Compose, optional)

Compose-Datei (repo target): `docs/webui/observability/DOCKER_COMPOSE_PROM_GRAFANA.yml`  
Scrape Config (repo target): `docs/webui/observability/PROMETHEUS_SCRAPE_EXAMPLE.yml`

Hinweis: In `PROMETHEUS_SCRAPE_EXAMPLE.yml` ggf. `targets` an deinen Host/Port anpassen.

### C) Quick Verify

- Metrics Endpoint (nur wenn enabled): `&#47;metrics`
- Prometheus UI: `http://127.0.0.1:9090/`
- Grafana UI: `http://127.0.0.1:3000/`
  - Dashboard JSON Import: `docs/webui/observability/GRAFANA_DASHBOARD_PEAK_TRADE_WATCH_ONLY.json`

---

## 7) Troubleshooting (Snapshot-only)
- Runs-Liste leer:
  - Prüfe, ob `--base-runs-dir` auf das richtige Verzeichnis zeigt.
  - Prüfe pro Run: `meta.json` vorhanden.
- Run Detail 404:
  - Run-ID existiert nicht als Directory unter base-runs-dir.
- API mutating method:
  - Erwartet: `POST` auf `&#47;api&#47;...` → **405** (“read-only api”)

---

## 8) Shutdown
Server Prozess im Terminal beenden (Ctrl-C).

---

## 9) Referenzen
- Implementation: `src/live/web/app.py`
- Start Script: `scripts/live_web_server.py`
- API Contract: `docs/webui/DASHBOARD_API_CONTRACT_v0.md`
- Operator Runbook (v0.1B): `docs/ops/runbooks/RUNBOOK_DASHBOARD_WATCH_ONLY_V01B.md`
