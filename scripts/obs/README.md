# Peak_Trade Observability Scripts - Stage 1 Monitoring

## 📁 Struktur

```
scripts/obs/
├── README.md                      ← Diese Datei
├── stage1_daily_snapshot.py       ← Täglicher Report-Generator
├── stage1_trend_report.py         ← Trend-Analyse über N Tage
└── run_stage1_monitoring.sh       ← Convenience Wrapper (täglich ausführen)

reports&#47;obs&#47;stage1&#47;
├── 2025-12-20_snapshot.md         ← Daily Snapshots (automatisch erstellt)
├── 2025-12-21_snapshot.md
└── ...
```

---

## 🚀 Quick Start

### Tägliche Monitoring-Routine

```bash
# Option 1: Convenience Wrapper (empfohlen)
bash scripts/obs/run_stage1_monitoring.sh

# Option 2: Manuell
python3 scripts/obs/stage1_daily_snapshot.py
python3 scripts/obs/stage1_trend_report.py
```

## Stage1 report index (deterministic)
After Stage1 runs, a deterministic index is generated:
- Path: `reports&#47;stage1&#47;index.json`
- Schema: `stage1_index.v1`
- Purpose: stable discovery for WebUI/ops; includes sha256 + size for artifacts.

You can regenerate manually:
`python3 scripts/obs/stage1_report_index.py --root reports/obs/stage1 --out reports/obs/stage1/index.json --run-date YYYY-MM-DD` <!-- pt:ref-target-ignore -->

## Stage1 validation (fail-fast)
After index generation, Stage1 runners validate artifacts and write:
- `reports&#47;obs&#47;stage1&#47;validation.json` (schema: `stage1_validation.v1`)

Manual run:
`python3 scripts/obs/validate_stage1_index.py --root reports/obs/stage1 --index reports/obs/stage1/index.json --out reports/obs/stage1/validation.json --require data.json --require report.md` <!-- pt:ref-target-ignore -->

---

## Observability Stack (Ops Runner)

Grafana/Dashboard-Skripte wurden entfernt. Für lokale Observability nutze den Ops Runner:

```bash
# Compose prüfen
docker compose -f docker/docker-compose.obs.yml config

# Stage1 Snapshot (siehe run_stage1_snapshot_docker.sh)
docker compose -f docker/docker-compose.obs.yml run --rm peaktrade-ops stage1-snapshot
```

Siehe `docs/DOCKER_KOMPLETT_UEBERSICHT.md` für die kanonische Docker-Dokumentation.

---

## 📊 Script 1: Daily Snapshot

**Zweck:** Analysiert Telemetry/Alert-JSONL-Dateien der letzten 24h und erstellt einen Markdown-Report.

### Basic Usage

```bash
# Standard-Run (verwendet defaults)
python3 scripts/obs/stage1_daily_snapshot.py

# Mit custom Optionen
python3 scripts/obs/stage1_daily_snapshot.py \
  --repo ~/Peak_Trade \
  --out-dir reports&#47;obs&#47;stage1 \
  --max-files 10 \
  --max-depth 12
```

### Erweiterte Optionen

| Option | Default | Beschreibung |
|--------|---------|--------------|
| `--repo` | `.` | Repo root (Ausgangspunkt für Dateisuche) |
| `--out-dir` | `reports&#47;obs&#47;stage1` | Output-Verzeichnis für Reports |
| `--max-depth` | `10` | Maximale Suchtiefe für JSONL-Dateien |
| `--max-files` | `8` | Parse nur die N neuesten Dateien |
| `--legacy-regex` | `(legacy\|risk[_ -]?limit...)` | Regex für Legacy-Detection |
| `--fail-on-new-alerts` | `false` | Exit Code 2 wenn neue Alerts detektiert |

### Exit Codes

- **0:** OK (keine neuen Alerts)
- **2:** Warnung (neue Alerts detektiert, nur mit `--fail-on-new-alerts`)

### Output

Erstellt `reports&#47;obs&#47;stage1&#47;YYYY-MM-DD_snapshot.md` mit:
- Candidate JSONL files (Top 8, neueste zuerst)
- Summary (Zeilen, Timestamps, Legacy-Hits)
- Last 24h breakdown (Severity, Event Types, Rules)
- Operator actions (ACK/SNOOZE/RESOLVE)
- **New-alerts heuristic:** Anzahl neuer Alerts (event_type enthält "alert")

---

## 📈 Script 2: Trend Report

**Zweck:** Aggregiert mehrere Daily Snapshots zu einem Trend-Report (Go/No-Go Signal).

### Basic Usage

```bash
# Letzte 14 Tage (default)
python3 scripts/obs/stage1_trend_report.py

# Letzte 7 Tage
python3 scripts/obs/stage1_trend_report.py --days 7

# Custom Snapshot-Directory
python3 scripts/obs/stage1_trend_report.py --dir reports&#47;obs&#47;stage1
```

### Optionen

| Option | Default | Beschreibung |
|--------|---------|--------------|
| `--dir` | `reports&#47;obs&#47;stage1` | Snapshot-Verzeichnis |
| `--days` | `14` | Anzahl der letzten Tage (max) |

### Output

Erzeugt Markdown-Tabelle mit:
- **Day:** Datum
- **New alerts (24h):** Neue Alerts pro Tag
- **Legacy hits:** Legacy-System-Aktivität
- **Operator actions:** ACK/SNOOZE/RESOLVE pro Tag

**Quick Signal:**
- ✅ Keine neuen Alerts → Stage 2 (Webhook) ready
- ⚠️ Neue Alerts detektiert → Ursachenanalyse empfohlen

---

## 🔄 Automation (Empfohlen)

### Täglicher Cron Job

```bash
# Crontab editieren
crontab -e

# Eintrag hinzufügen (täglich um 08:00 UTC)
0 8 * * * cd /path/to/Peak_Trade && bash scripts/obs/run_stage1_monitoring.sh >> logs/stage1_cron.log 2>&1
```

### Alternative: GitHub Actions

Siehe `.github&#47;workflows&#47;stage1_monitoring.yml` (falls vorhanden).

---

## 📋 Erwartete Werte (Healthy Stage 1)

### Baseline (erste 1-2 Wochen):

| Metrik | Erwarteter Wert | Schwelle |
|--------|-----------------|----------|
| **New alerts (24h)** | 0-5 | > 10 → Review |
| **Legacy hits** | 100-600 | Ignorieren (separates System) |
| **Operator actions** | 0 | > 0 → Prüfen warum |
| **CRITICAL alerts** | 0 | > 5 → Urgent Review |

### Warnsignale:

- 🚨 **New alerts > 10/Tag:** Noise-Problem, Thresholds anpassen
- 🚨 **Operator actions > 5/Tag:** Alert-Fatigue, Rules überprüfen
- 🚨 **CRITICAL > 5:** System-Issue, Incident-Response

---

## 🔍 Troubleshooting

### Problem: Keine JSONL-Dateien gefunden

**Symptom:** Report zeigt "(none found)"

**Lösungen:**
1. `--max-depth` erhöhen (z.B. `--max-depth 15`)
2. Prüfen: Existieren Telemetry-Logs? `ls -lh logs/execution`
3. Prüfen: Alert-History enabled? `grep enabled config/telemetry_alerting.toml`

### Problem: Nur Legacy-Alerts, keine neuen Alerts

**Symptom:** New-alerts heuristic = 0, aber viele CRITICAL/WARN

**Erklärung:**
- Legacy-System (`live_runs&#47;alerts&#47;`) ist ein **separates System**
- Neues System (`data&#47;telemetry&#47;alerts&#47;`) emitted nur bei tatsächlichen Issues
- **Erwartetes Verhalten** für healthy Stage 1 ✅

### Problem: Parse errors

**Symptom:** Wenige Events trotz großer JSONL-Dateien

**Lösungen:**
1. Timestamp-Schema prüfen: `head -1 file.jsonl | jq .`
2. Legacy-Regex anpassen: `--legacy-regex "..."` (Custom Pattern)

---

## 🧪 Testing

### Smoke Test

```bash
# 1) Daily Snapshot (soll 0 neue Alerts zeigen)
python3 scripts/obs/stage1_daily_snapshot.py
echo "Exit code: $?"  # Soll 0 sein

# 2) Trend Report (soll ✅ signal zeigen)
python3 scripts/obs/stage1_trend_report.py
```

### Fail-on-new-alerts Test

```bash
# Soll Exit Code 2 zurückgeben wenn neue Alerts detektiert werden
python3 scripts/obs/stage1_daily_snapshot.py --fail-on-new-alerts
if [ $? -eq 2 ]; then
  echo "⚠️ Neue Alerts detektiert!"
fi
```

---

## 📖 Related Documentation

- **Phase 16I:** `docs/ops/TELEMETRY_ALERTING_RUNBOOK.md`
- **Phase 16J:** `docs/ops/TELEMETRY_ALERTING_LIFECYCLE_RUNBOOK.md`
- **Health Monitoring:** `docs/ops/TELEMETRY_HEALTH_RUNBOOK.md`
- **Trend Analysis:** `docs/ops/TELEMETRY_HEALTH_TRENDS_RUNBOOK.md`

---

## ✅ Checklist: Ready for Stage 2 (Webhook Enablement)

Vor dem Aktivieren von Webhook-Delivery prüfen:

- [ ] 1-2 Wochen tägliche Snapshots erstellt
- [ ] Trend Report zeigt ✅ "Keine neuen Alerts"
- [ ] Operator Actions = 0 (keine manuellen Suppressions nötig)
- [ ] Legacy-Alerts verstanden (separates System, ignorieren OK)
- [ ] Webhook-Endpoint konfiguriert & getestet
- [ ] Alert-Thresholds angepasst (falls Noise detektiert)
- [ ] Runbooks reviewed & Team informiert

**Next:** `config/telemetry_alerting.toml` → `dry_run = false` + `webhook.enabled = true`

---

**Erstellt:** 2025-12-20  
**Version:** 1.0 (Stage 1 DRY-RUN)
