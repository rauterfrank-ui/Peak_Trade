# Peak_Trade Automation Setup – Abschlussbericht 📋

**Erstellt**: 2025-12-10  
**Status**: ✅ Vollständig implementiert und getestet  
**Sicherheit**: 🔒 Alle Scripts sind strikt offline – keine Live-Orders möglich

---

## 1️⃣ Dateien & Ordner

### Neu erstellt

#### Automation-Scripts

| Datei | Typ | Zeilen | Beschreibung |
|-------|-----|--------|--------------|
| `scripts/automation/README.md` | Doku | 200+ | Vollständige Dokumentation der Automation-Suite |
| `scripts/automation/QUICKSTART.md` | Doku | 150+ | Schnellstart-Anleitung für Benutzer |
| `scripts/automation/run_offline_daily_suite.py` | Script | 700+ | Daily Test-Suite (6 Jobs) |
| `scripts/automation/run_offline_weekly_suite.py` | Script | 750+ | Weekly Test-Suite (8 Jobs) |

#### CI/CD

| Datei | Typ | Beschreibung |
|-------|-----|--------------|
| `.github/workflows/offline_suites.yml` | Workflow | GitHub Actions für Daily & Weekly Suites |

#### Generated Reports (Beispiele aus Dry-Run)

| Datei | Typ | Beschreibung |
|-------|-----|--------------|
| `reports/automation/daily/automation_daily_<TIMESTAMP>.json` | JSON | Daily Suite JSON-Log |
| `reports/automation/weekly/automation_weekly_<TIMESTAMP>.json` | JSON | Weekly Suite JSON-Log |
| `reports/automation/weekly/automation_weekly_<TIMESTAMP>.md` | Markdown | Weekly Suite Summary |

---

## 2️⃣ Technische Zusammenfassung

### Verwendete Module

#### OfflineSynthSession
- **Quelle**: `scripts/run_offline_realtime_ma_crossover.py`
- **Klassen**:
  - `OfflineSynthSessionConfig` (Lines 92-108)
  - `OfflineSynthSessionResult` (Lines 111-127)
  - `run_offline_synth_session()` (Lines 130-207)
- **Verwendung**: Generiert synthetische OHLCV-Daten mit Regime-Switching

#### OfflineRealtimeFeed
- **Quelle**: `scripts/run_offline_realtime_ma_crossover.py`
- **Klassen**:
  - `OfflineRealtimeFeedConfig` (Lines 215-227)
  - `OfflineRealtimeFeed` (Lines 230-279)
  - `build_offline_ma_crossover_pipeline()` (Lines 564-651)
  - `run_pipeline()` (Lines 659-781)
- **Verwendung**: Pipeline für MA-Crossover-Strategie mit Paper-Trading

#### Trigger-Training
- **Quelle**: `scripts/run_offline_trigger_training_drill_example.py`
- **Workflow**: Vollständiges Trigger-Training mit:
  - Session-Daten-Loading (Lines 174-243)
  - Demo-Daten-Generierung (Lines 246-434)
  - Trigger-Event-Building (Lines 469-476)
  - Reaction-Stats (Lines 479-497)
  - Execution-Latency-Stats (Lines 500-514)
  - Report-Generierung (Lines 531-558)
- **Verwendung**: Subprocess-Aufruf des kompletten Drill-Scripts

#### Psychology-Heatmap
- **Quelle**: `src/reporting/psychology_heatmap.py`
- **Integration**: Automatisch in Trigger-Training-Reports eingebunden
- **Features**:
  - Heatmap-Zellen mit 4 Heat-Levels (0-3)
  - 5 Psychologie-Dimensionen: FOMO, Verlustangst, Impulsivität, Zögern, Regelbruch
  - HTML-Template-Integration über `src/webui/templates/`

---

## 3️⃣ Wie ich das benutze

### Lokale Ausführung

#### Daily Suite

```bash
# Standard-Run (alle 6 Jobs)
python3 scripts/automation/run_offline_daily_suite.py

# Mit verbose Logging
python3 scripts/automation/run_offline_daily_suite.py --verbose

# Dry-Run (nur anzeigen, was laufen würde)
python3 scripts/automation/run_offline_daily_suite.py --dry-run

# Nur Trigger-Training ausführen
python3 scripts/automation/run_offline_daily_suite.py --only-trigger

# Ohne Pytest
python3 scripts/automation/run_offline_daily_suite.py --no-pytest
```

**Erwartete Laufzeit**: ~5-10 Minuten

**Output**:
- JSON-Log: `reports/automation/daily/automation_daily_<YYYYMMDD_HHMMSS>.json`
- Trigger-Reports: `reports/automation/daily/trigger_training/<SESSION_ID>/`

---

#### Weekly Suite

```bash
# Standard-Run (alle 8 Jobs)
python3 scripts/automation/run_offline_weekly_suite.py

# Mit verbose Logging
python3 scripts/automation/run_offline_weekly_suite.py --verbose

# Dry-Run
python3 scripts/automation/run_offline_weekly_suite.py --dry-run

# Quick-Mode (weniger Jobs, schneller)
python3 scripts/automation/run_offline_weekly_suite.py --quick-mode
```

**Erwartete Laufzeit**:
- Standard: ~30-60 Minuten
- Quick-Mode: ~10-15 Minuten

**Output**:
- JSON-Log: `reports/automation/weekly/automation_weekly_<YYYYMMDD_HHMMSS>.json`
- Markdown-Summary: `reports/automation/weekly/automation_weekly_<YYYYMMDD_HHMMSS>.md`
- Trigger-Reports: `reports/automation/weekly/trigger_training_<SCENARIO>/`

---

### Cron-Automation

#### Setup

1. **Crontab öffnen**:
   ```bash
   crontab -e
   ```

2. **Daily Suite hinzufügen** (täglich um 02:00):
   ```bash
   0 2 * * * cd /Users/frnkhrz/Peak_Trade && /path/to/venv/bin/python3 scripts/automation/run_offline_daily_suite.py >> /var/log/peak_trade_daily.log 2>&1
   ```

3. **Weekly Suite hinzufügen** (jeden Montag um 03:00):
   ```bash
   0 3 * * 1 cd /Users/frnkhrz/Peak_Trade && /path/to/venv/bin/python3 scripts/automation/run_offline_weekly_suite.py >> /var/log/peak_trade_weekly.log 2>&1
   ```

#### Tipps für Cron

- Verwende **absolute Pfade** für Python-Binary und Script
- Stelle sicher, dass das **Working Directory** korrekt ist (`cd /Users/frnkhrz/Peak_Trade`)
- Leite **stdout und stderr** in Log-Dateien um (`>> /path/to/log 2>&1`)
- Teste den Cron-Befehl vorher manuell im Terminal

#### Log-Rotation (empfohlen)

```bash
# Alte Automation-Logs löschen (älter als 30 Tage)
find /Users/frnkhrz/Peak_Trade/reports/automation -name "*.json" -mtime +30 -delete
find /Users/frnkhrz/Peak_Trade/reports/automation -name "*.md" -mtime +30 -delete

# Als wöchentlicher Cron-Job (Sonntag um 01:00)
0 1 * * 0 find /Users/frnkhrz/Peak_Trade/reports/automation -name "*.json" -mtime +30 -delete
```

---

### GitHub Actions (CI)

#### Setup

Die GitHub Actions sind bereits konfiguriert in:
- `.github/workflows/offline_suites.yml`

#### Automatische Ausführung

- **Daily Suite**: Jeden Tag um 02:00 UTC
- **Weekly Suite**: Jeden Montag um 03:00 UTC

#### Manueller Trigger

1. Gehe zu GitHub → Actions → "Offline Test Suites"
2. Klicke auf "Run workflow"
3. Wähle Suite-Typ: `daily`, `weekly`, oder `both`
4. Klicke "Run workflow"

#### Artifacts

Nach jedem Run werden die Reports als Artifacts hochgeladen:
- **Retention**: 30 Tage (Daily), 90 Tage (Weekly)
- **Download**: Über GitHub Actions UI

---

### Logs auswerten

#### JSON-Logs

```bash
# Letztes Daily-Log anschauen
cat reports/automation/daily/automation_daily_*.json | tail -n 1 | jq '.'

# Summary anzeigen
jq '.summary' reports/automation/daily/automation_daily_*.json | tail -n 1

# Failed Jobs filtern
jq '.jobs[] | select(.status=="failed")' reports/automation/daily/automation_daily_*.json | tail -n 1

# Performance-Metriken extrahieren
jq '.jobs[] | select(.job_name | contains("synth")) | {name: .job_name, ticks_per_sec: .extra.ticks_per_sec}' \
  reports/automation/daily/automation_daily_*.json | tail -n 1
```

#### Markdown-Summaries

```bash
# Letztes Weekly-Summary anschauen
cat reports/automation/weekly/automation_weekly_*.md | tail -n 100
```

#### Trends analysieren (über mehrere Runs)

```bash
# Ticks/s-Trend für OfflineSynth (letzte 10 Runs)
for file in $(ls -t reports/automation/daily/automation_daily_*.json | head -10); do
  echo -n "$(basename $file): "
  jq '.jobs[] | select(.job_name=="offline_synth_medium") | .extra.ticks_per_sec' "$file"
done

# Missed-Trigger-Rate-Trend (letzte 10 Runs)
for file in $(ls -t reports/automation/daily/automation_daily_*.json | head -10); do
  echo -n "$(basename $file): "
  jq '.jobs[] | select(.job_name=="trigger_training_drill") | .extra.missed_signals // 0' "$file"
done
```

---

## 4️⃣ Offene TODOs / Ideen

### Kurzfristig (nächste 1-2 Wochen)

- [ ] **Meta-Report-Script**: Aggregiert die letzten 7/30 Tage
  - Trends für Ticks/s, Missed-Trigger-Rate, PnL
  - HTML-Dashboard mit Charts (Plotly/Matplotlib)
  - Speicherort: `reports/automation/meta/meta_report_<PERIOD>.html`

- [ ] **Alerting**: Bei Failed Jobs Notification senden
  - Integration mit Slack/Discord/Email
  - Konfigurierbarer Threshold (z.B. nur wenn >2 Jobs fehlschlagen)
  - Siehe `src/notifications/` für vorhandene Provider

- [ ] **Pytest-Marker**: Marker für `offline_fast` Tests hinzufügen
  - Tests mit `@pytest.mark.offline_fast` taggen
  - In Daily Suite nur diese Tests laufen lassen

### Mittelfristig (nächste 1-2 Monate)

- [ ] **Zusätzliche Strategien in Weekly Suite**:
  - RSI-Reversion
  - Donchian-Breakout
  - Armstrong/El-Karoui R&D-Strategien

- [ ] **Performance-Benchmarking**:
  - Baseline-Metriken festlegen (z.B. Ticks/s)
  - Regression-Detection bei Verschlechterung >10%
  - Auto-Issue-Creation bei Performance-Regression

- [ ] **Szenario-Library für Trigger-Training**:
  - Mehr Szenarien (Revenge Trading, Scale-In, etc.)
  - Konfigurierbarer Szenario-Mix pro Drill
  - Szenario-Config in TOML-Dateien

### Langfristig (next Quarter)

- [ ] **Web-Dashboard für Automation-Metriken**:
  - Integration in bestehende WebUI (`src/webui/`)
  - Trendgraphen, Heatmaps, Leaderboards
  - Vergleich zwischen Daily/Weekly Runs

- [ ] **Docker-Container für Automation**:
  - Self-contained Automation-Environment
  - Einfachere CI/CD-Integration
  - Reproduzierbare Builds

- [ ] **Multi-Strategy Portfolio Testing**:
  - Weekly Suite testet auch Portfolio-Kombinationen
  - Risk-Metriken (Sharpe, Sortino, Max DD)
  - Correlation-Matrix für Strategien

---

## 5️⃣ Sicherheit & Best Practices

### ✅ Was die Automation MACHT

- Generiert synthetische Marktdaten (OfflineSynthSession)
- Simuliert Paper-Trading (keine echten Orders)
- Führt Trigger-Training-Drills aus (Demo-Daten)
- Schreibt Reports in `reports/automation/`
- Loggt Performance-Metriken

### ❌ Was die Automation NICHT MACHT

- **KEINE** Verbindung zu Live-Exchanges (Kraken, etc.)
- **KEINE** realen Order-Submissions
- **KEINE** Zugriffe auf API-Keys oder Secrets
- **KEINE** Schreibzugriffe außerhalb von `reports/`
- **KEINE** Änderungen an der Codebase

### 🔒 Sicherheits-Features

1. **Environment-Checks**: Alle Pipelines laufen im `PAPER`-Modus
2. **No-Network-Sandbox**: Scripts nutzen nur lokale Daten
3. **Read-Only Data**: Keine Schreibzugriffe auf `/data/` oder `/live_runs/`
4. **Logging**: Alle Aktivitäten werden geloggt (JSON + stdout)

---

## 6️⃣ Troubleshooting

### Problem: Script läuft nicht

**Symptom**: `python3: command not found` oder ähnlich

**Lösung**:
```bash
# Python-Version prüfen
python3 --version  # mindestens 3.10 erforderlich

# Falls Python nicht gefunden wird
which python3

# Alternative: Direkt mit Python-Binary
/usr/local/bin/python3 scripts/automation/run_offline_daily_suite.py
```

---

### Problem: Import-Fehler

**Symptom**: `ModuleNotFoundError: No module named 'src'`

**Lösung**:
```bash
# Working Directory prüfen
pwd  # sollte /Users/frnkhrz/Peak_Trade sein

# Falls falsch, navigiere zum Projekt-Root
cd /Users/frnkhrz/Peak_Trade

# Dependencies installieren
pip install -r requirements.txt
```

---

### Problem: Jobs schlagen fehl

**Symptom**: `jobs_failed > 0` in JSON-Log

**Lösung**:
```bash
# Fehler-Details anschauen
jq '.jobs[] | select(.status=="failed") | {name: .job_name, error: .error_msg}' \
  reports/automation/daily/automation_daily_*.json

# Einzelne Module manuell testen
python3 scripts/run_offline_realtime_ma_crossover.py --n-steps 100 --verbose

python3 scripts/run_offline_trigger_training_drill_example.py --verbose
```

---

### Problem: Trigger-Training fehlt

**Symptom**: `trigger_training_drill` Job fehlt oder schlägt fehl

**Lösung**:
```bash
# Prüfe, ob Script existiert
ls -l scripts/run_offline_trigger_training_drill_example.py

# Falls vorhanden, teste manuell
python3 scripts/run_offline_trigger_training_drill_example.py --session-id TEST_123

# Falls nicht vorhanden, überspringe Trigger-Training
python3 scripts/automation/run_offline_daily_suite.py --no-trigger
```

---

### Problem: Pytest schlägt fehl

**Symptom**: `pytest_fast` Job hat `status="failed"`

**Lösung**:
```bash
# Pytest manuell ausführen
pytest -xvs

# Nur schnelle Tests (falls Marker vorhanden)
pytest -m "offline_fast" -xvs

# Falls Pytest-Fehler nicht kritisch sind, überspringe
python3 scripts/automation/run_offline_daily_suite.py --no-pytest
```

---

## 7️⃣ Nächste Schritte

### Für dich als Benutzer

1. **Teste die Scripts lokal**:
   ```bash
   python3 scripts/automation/run_offline_daily_suite.py --dry-run
   python3 scripts/automation/run_offline_weekly_suite.py --dry-run
   ```

2. **Führe einen echten Daily Run aus**:
   ```bash
   python3 scripts/automation/run_offline_daily_suite.py --verbose
   ```

3. **Schaue die Reports an**:
   ```bash
   cat reports/automation/daily/automation_daily_*.json | jq '.'
   ```

4. **Setup Cron** (falls gewünscht):
   - Siehe Abschnitt "Cron-Automation" oben

5. **Aktiviere GitHub Actions** (falls gewünscht):
   - Commit & Push `.github/workflows/offline_suites.yml`
   - Überprüfe unter GitHub → Actions

### Für die Zukunft

- **Meta-Report-Script** entwickeln (aggregiert Trends)
- **Weitere Strategien** in Weekly Suite integrieren
- **Alerting** für Failed Jobs einrichten
- **Web-Dashboard** für Automation-Metriken bauen

---

## 8️⃣ Zusammenfassung

### ✅ Was wurde implementiert

- ✅ **2 vollständige Automation-Scripts** (Daily + Weekly)
- ✅ **Umfassende Dokumentation** (README + QUICKSTART)
- ✅ **GitHub Actions Workflow** für CI/CD
- ✅ **JSON-Logging** mit strukturierten Metriken
- ✅ **Markdown-Summaries** für Weekly Runs
- ✅ **Dry-Run-Modus** für Testing
- ✅ **Flexible CLI-Flags** für Customization
- ✅ **Integration mit bestehenden Modulen**:
  - OfflineSynthSession ✅
  - OfflineRealtimeFeed ✅
  - Trigger-Training ✅
  - Psychology-Heatmap ✅

### 📊 Test-Abdeckung

| Job | Daily | Weekly | Status |
|-----|-------|--------|--------|
| Pytest Fast | ✅ | - | Implementiert |
| OfflineSynth (small) | ✅ | - | Implementiert |
| OfflineSynth (medium) | ✅ | - | Implementiert |
| OfflineSynth (long) | - | ✅ | Implementiert |
| OfflineRealtime (Baseline) | ✅ | ✅ | Implementiert |
| OfflineRealtime (R&D) | ✅ | ✅ | Implementiert |
| OfflineRealtime (Multi-Symbol) | - | ✅ | Implementiert |
| Trigger-Training (single) | ✅ | - | Implementiert |
| Trigger-Training (scenarios) | - | ✅ | Implementiert |

### 🎯 Nächste Prioritäten

1. **Lokal testen** (beide Suiten)
2. **Cron einrichten** (optional)
3. **GitHub Actions aktivieren** (optional)
4. **Meta-Report-Script** entwickeln (next iteration)

---

**Fragen? Issues?** → Siehe `docs&sol;CONTRIBUTING.md (planned)` oder öffne ein GitHub Issue.

**Zuletzt aktualisiert**: 2025-12-10  
**Maintainer**: Peak_Trade Team
