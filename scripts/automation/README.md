# Peak_Trade – Offline Test-/Drill-Automation 🤖

## 📋 Überblick

Dieses Verzeichnis enthält automatisierte Test-/Drill-Suiten für Peak_Trade, die **komplett offline** laufen – **keine realen Orders, kein Live-Trading**.

Die Automation-Scripts führen regelmäßig verschiedene Tests und Drills durch, um die Codebase gesund zu halten und Performance-Metriken zu tracken.

## 🎯 Zweck

- **Regelmäßige Qualitätssicherung**: Automatisierte Tests für Core-Funktionalität
- **Performance-Tracking**: Speed-Metriken für Synth-Sessions und Realtime-Feeds
- **Trigger-Training**: Psychologie-Heatmaps und Reaktionszeit-Statistiken
- **Strategie-Validierung**: Offline-Tests für verschiedene Strategien und Märkte

## 📁 Enthaltene Scripts

### 1. `run_offline_daily_suite.py` – Tägliche Test-Suite

**Zweck**: Schnelle, tägliche Validierung der Core-Funktionalität.

**Umfang**:
- ✅ **Pytest-Run** (schnelle Tests)
- 🎲 **2 OfflineSynthSession-Runs** (unterschiedliche Größen: 1000 / 5000 Steps)
- 📊 **2 OfflineRealtimeFeed-Runs** (Baseline + R&D-Strategie)
- 🎯 **1 Trigger-Training Drill** mit Psychology-Heatmap

**Laufzeit**: ~5-10 Minuten (je nach Hardware)

**Logging**: JSON-Log unter `reports&#47;automation&#47;daily&#47;automation_daily_<TIMESTAMP>.json`

**Usage**:
```bash
# Standard-Run (alle Jobs)
python scripts/automation/run_offline_daily_suite.py

# Dry-Run (nur anzeigen, was laufen würde)
python scripts/automation/run_offline_daily_suite.py --dry-run

# Nur bestimmte Jobs
python scripts/automation/run_offline_daily_suite.py --no-pytest
python scripts/automation/run_offline_daily_suite.py --only-trigger
```

**Empfohlene Cron-Schedule**:
```bash
# Jeden Tag um 02:00 Uhr
0 2 * * * /path/to/venv/bin/python /path/to/Peak_Trade/scripts/automation/run_offline_daily_suite.py >> /path/to/logs/daily_suite.log 2>&1
```

---

### 2. `run_offline_weekly_suite.py` – Wöchentliche Test-Suite

**Zweck**: Umfassende Tests über verschiedene Strategien und Märkte hinweg.

**Umfang**:
- 🎲 **Lange OfflineSynthSession** (20.000 Steps)
- 📊 **Multi-Symbol OfflineRealtimeFeed-Runs**:
  - BTCEUR, BTCUSD, ETHEUR (je mit Baseline + R&D-Strategien)
- 🎯 **Szenario-Matrix für Trigger-Training**:
  - Mehrere Drills mit unterschiedlichen Schwerpunkten (FOMO, Overtrading, Freeze)
  - Psychologie-Heatmaps für jedes Szenario

**Laufzeit**: ~30-60 Minuten (je nach Hardware)

**Logging**:
- JSON-Log: `reports&#47;automation&#47;weekly&#47;automation_weekly_<TIMESTAMP>.json`
- Markdown-Summary: `reports&#47;automation&#47;weekly&#47;automation_weekly_<TIMESTAMP>.md`

**Usage**:
```bash
# Standard-Run (alle Jobs)
python scripts/automation/run_offline_weekly_suite.py

# Dry-Run
python scripts/automation/run_offline_weekly_suite.py --dry-run

# Custom Output-Verzeichnis
python scripts/automation/run_offline_weekly_suite.py --output-dir reports/custom_weekly
```

**Empfohlene Cron-Schedule**:
```bash
# Jeden Montag um 03:00 Uhr
0 3 * * 1 /path/to/venv/bin/python /path/to/Peak_Trade/scripts/automation/run_offline_weekly_suite.py >> /path/to/logs/weekly_suite.log 2>&1
```

---

## 🔒 Sicherheit

**WICHTIG**: Alle Scripts in diesem Verzeichnis sind **strikt offline**:

- ✅ Keine Verbindung zu Live-Exchanges
- ✅ Keine realen Order-Submissions
- ✅ Nur Paper-/Synthetic-/Demo-Modus
- ✅ Alle Daten werden lokal unter `reports&#47;automation&#47;` gespeichert

## 📊 Output-Struktur

```
reports/
└── automation/
    ├── daily/
    │   ├── automation_daily_20251210_020000.json
    │   ├── automation_daily_20251211_020000.json
    │   └── ...
    └── weekly/
        ├── automation_weekly_20251209_030000.json
        ├── automation_weekly_20251209_030000.md
        ├── automation_weekly_20251216_030000.json
        ├── automation_weekly_20251216_030000.md
        └── ...
```

## 🚀 GitHub Actions / CI-Integration

Wenn du GitHub Actions verwendest, kannst du die Suiten auch in CI laufen lassen:

```yaml
# .github/workflows/offline_suites.yml
name: Offline Test Suites

on:
  schedule:
    # Daily Suite: Jeden Tag um 02:00 UTC
    - cron: '0 2 * * *'
    # Weekly Suite: Jeden Montag um 03:00 UTC
    - cron: '0 3 * * 1'
  workflow_dispatch:  # Manueller Trigger

jobs:
  daily-suite:
    if: github.event.schedule == '0 2 * * *'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: python scripts/automation/run_offline_daily_suite.py

  weekly-suite:
    if: github.event.schedule == '0 3 * * 1'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: python scripts/automation/run_offline_weekly_suite.py
```

## 📈 Metriken & Monitoring

Die JSON-Logs enthalten folgende Metriken:

**Performance**:
- `ticks_per_sec`: Verarbeitungsgeschwindigkeit (OfflineSynthSession)
- `duration_sec`: Laufzeit pro Job
- `n_orders`, `n_trades`: Trading-Aktivität

**Trigger-Training**:
- `missed_trigger_rate`: Anteil verpasster Signale
- `false_trigger_rate`: Anteil falscher Signale
- `avg_reaction_time_ms`: Durchschnittliche Reaktionszeit
- `reaction_buckets`: Verteilung nach Reaktionszeit (0-2s, 2-5s, >5s)

**Execution-Latency**:
- `mean_trigger_delay_ms`: Verzögerung zwischen Signal und Order
- `mean_send_to_fill_ms`: Verzögerung zwischen Order-Send und Fill
- `mean_slippage`: Durchschnittlicher Slippage

## 🛠️ Entwicklung

**Neue Jobs hinzufügen**:
1. Job-Funktion in `run_offline_daily_suite.py` oder `run_offline_weekly_suite.py` definieren
2. Job zur `JOBS`-Liste hinzufügen
3. Optional: CLI-Flag für Selective Execution hinzufügen

**Logging erweitern**:
- JSON-Logs können beliebige Metriken enthalten (siehe `JobResult.extra`)
- Markdown-Summaries werden automatisch aus JSON generiert

## 📝 Maintenance

**Logs aufräumen**:
```bash
# Alte Logs löschen (älter als 30 Tage)
find reports/automation -name "*.json" -mtime +30 -delete
find reports/automation -name "*.md" -mtime +30 -delete
```

**Fehlersuche**:
- Logs in `reports&#47;automation&#47;` prüfen
- Einzelne Jobs manuell laufen lassen (z.B. `run_offline_realtime_ma_crossover.py`)
- Mit `--dry-run` testen, ohne Jobs auszuführen

## 🤝 Beiträge

Bei Fragen oder Verbesserungsvorschlägen: siehe `docs&sol;CONTRIBUTING.md (planned)`

---

**Zuletzt aktualisiert**: 2025-12-10
**Maintainer**: Peak_Trade Team
