# Quickstart: Peak_Trade Automation 🚀

## 🎯 Übersicht

Diese Automation-Suite führt **offline Tests** durch – **keine Live-Orders, kein Real-Trading**.

## ⚡ Schnellstart

### 1. Daily Suite (lokal ausführen)

```bash
# Alle Jobs ausführen
python3 scripts/automation/run_offline_daily_suite.py

# Nur Trigger-Training
python3 scripts/automation/run_offline_daily_suite.py --only-trigger

# Ohne Pytest
python3 scripts/automation/run_offline_daily_suite.py --no-pytest

# Dry-Run (zeigt nur, was laufen würde)
python3 scripts/automation/run_offline_daily_suite.py --dry-run
```

**Erwartete Laufzeit**: ~5-10 Minuten

**Output**: `reports&#47;automation&#47;daily&#47;automation_daily_<TIMESTAMP>.json`

---

### 2. Weekly Suite (lokal ausführen)

```bash
# Alle Jobs ausführen
python3 scripts/automation/run_offline_weekly_suite.py

# Quick-Mode (weniger Jobs, schneller)
python3 scripts/automation/run_offline_weekly_suite.py --quick-mode

# Dry-Run
python3 scripts/automation/run_offline_weekly_suite.py --dry-run
```

**Erwartete Laufzeit**:
- Standard: ~30-60 Minuten
- Quick-Mode: ~10-15 Minuten

**Output**:
- JSON: `reports&#47;automation&#47;weekly&#47;automation_weekly_<TIMESTAMP>.json`
- Markdown: `reports&#47;automation&#47;weekly&#47;automation_weekly_<TIMESTAMP>.md`

---

## 📅 Automation via Cron

### Daily Suite

```bash
# Crontab öffnen
crontab -e

# Daily Suite jeden Tag um 02:00
0 2 * * * cd /path/to/Peak_Trade && /path/to/venv/bin/python3 scripts/automation/run_offline_daily_suite.py >> /path/to/logs/daily_suite.log 2>&1
```

### Weekly Suite

```bash
# Weekly Suite jeden Montag um 03:00
0 3 * * 1 cd /path/to/Peak_Trade && /path/to/venv/bin/python3 scripts/automation/run_offline_weekly_suite.py >> /path/to/logs/weekly_suite.log 2>&1
```

**Tipps**:
- Ersetze `/path/to/Peak_Trade` mit deinem tatsächlichen Pfad
- Ersetze `/path/to/venv` mit deinem Python-Venv-Pfad
- Stelle sicher, dass die Logs in einem beschreibbaren Verzeichnis landen

---

## 🔍 Logs & Reports auswerten

### JSON-Logs

```bash
# Letztes Daily-Log anschauen
cat reports/automation/daily/automation_daily_*.json | jq '.'

# Letztes Weekly-Log anschauen
cat reports/automation/weekly/automation_weekly_*.json | jq '.'

# Nur Summary anzeigen
cat reports/automation/daily/automation_daily_*.json | jq '.summary'

# Failed Jobs anzeigen
cat reports/automation/daily/automation_daily_*.json | jq '.jobs[] | select(.status=="failed")'
```

### Markdown-Summaries

```bash
# Letztes Weekly-Summary anschauen
cat reports/automation/weekly/automation_weekly_*.md
```

---

## 🐛 Troubleshooting

### Problem: Script läuft nicht

**Lösung**:
1. Prüfe Python-Version: `python3 --version` (mindestens 3.10)
2. Prüfe Dependencies: `pip install -r requirements.txt`
3. Teste mit `--dry-run` Flag

### Problem: Jobs schlagen fehl

**Lösung**:
1. Schaue ins JSON-Log: `error_msg` Feld
2. Laufe einzelne Module manuell:
   ```bash
   # Test OfflineSynthSession
   python3 scripts/run_offline_realtime_ma_crossover.py --n-steps 100

   # Test Trigger-Training
   python3 scripts/run_offline_trigger_training_drill_example.py
   ```

### Problem: Trigger-Training-Drill fehlt

**Lösung**:
- Stelle sicher, dass `scripts/run_offline_trigger_training_drill_example.py` existiert
- Falls nicht vorhanden, überspringe mit `--no-trigger` Flag

---

## 📊 Was wird getestet?

### Daily Suite (6 Jobs)

1. **Pytest Fast**: Schnelle Unit-Tests
2. **OfflineSynth Small**: 1.000 Synth-Steps
3. **OfflineSynth Medium**: 5.000 Synth-Steps
4. **OfflineRealtime Baseline**: MA-Crossover (BTC/EUR)
5. **OfflineRealtime R&D**: MA-Crossover mit anderen Parametern
6. **Trigger-Training Drill**: Psychology-Heatmap + Reaktionszeit-Stats

### Weekly Suite (8 Jobs)

1. **OfflineSynth Long**: 20.000 Synth-Steps
2. **OfflineRealtime BTC/EUR Baseline**: MA-Crossover
3. **OfflineRealtime BTC/EUR R&D**: MA-Crossover (custom params)
4. **OfflineRealtime BTC/USD Baseline**: MA-Crossover
5. **OfflineRealtime ETH/EUR Baseline**: MA-Crossover
6. **Trigger-Training FOMO**: FOMO-Szenario
7. **Trigger-Training Overtrading**: Overtrading-Szenario
8. **Trigger-Training Freeze**: Freeze-Szenario

---

## 🚨 Wichtig: Keine Live-Orders!

**Alle Scripts laufen strikt offline**:
- ✅ Synthetic Data
- ✅ Paper Trading
- ✅ Offline Drills
- ❌ **KEINE** Live-Exchange-Verbindungen
- ❌ **KEINE** realen Orders

---

## 📚 Weitere Infos

- **Vollständige Doku**: [README.md](./README.md)
- **GitHub Actions**: [.github/workflows/offline_suites.yml](../../.github/workflows/offline_suites.yml)
- **Projekt-Doku**: [docs/](../../docs/)

---

**Zuletzt aktualisiert**: 2025-12-10
