# Test Health Automation v0

**Stand**: Dezember 2024  
**Status**: ✅ Implementiert  
**Autor**: Peak_Trade Ops Team

---

## Überblick

Die **Test Health Automation** ist eine Meta-Schicht für automatisierte Qualitätsprüfungen im Peak_Trade-Projekt. Sie führt definierte Check-Profile aus, bewertet die Ergebnisse mit einem gewichteten Health-Score (0-100) und erzeugt strukturierte Reports für KI-Testdatenspezialisten und Ops-Teams.

### Zweck

- **Automatisierte Test-Health-Checks**: Pytest-Suites, Offline-Drills, Trigger-Training-Sessions
- **Strukturierte Reports**: JSON (maschinenlesbar), Markdown (human-readable), HTML (visualisiert)
- **Health-Score-Metriken**: Gewichtete Bewertung (0-100) mit Ampel-System (🟢 Grün / 🟡 Gelb / 🔴 Rot)
- **CI/CD-Integration**: Exit-Codes, strukturierte Logs, zeitbasierte Report-Ordner

### Komponenten

1. **Config**: `config/test_health_profiles.toml` – Definition von Check-Profilen
2. **Runner**: `src/ops/test_health_runner.py` – Core-Logik für Check-Ausführung und Report-Generierung
3. **CLI**: `scripts/run_test_health_profile.py` – Command-Line-Interface
4. **Smoke-Scripts**: z.B. `scripts/run_offline_synth_session_smoke.py` – Minimal-Tests für schnelle Checks
5. **Reports**: `reports/test_health/<timestamp>_<profile>/` – JSON/MD/HTML

---

## Quick-Start

### Einfacher Aufruf (Default-Profil)

```bash
python scripts/run_test_health_profile.py
```

Verwendet automatisch das `default_profile` aus der TOML-Config (z.B. `weekly_core`).

### Spezifisches Profil ausführen

```bash
python scripts/run_test_health_profile.py --profile daily_quick
```

### Custom-Config und Report-Root

```bash
python scripts/run_test_health_profile.py \
    --profile full_suite \
    --config config/test_health_profiles.toml \
    --report-root reports/test_health
```

### Exit-Codes

- **0**: Alle Checks erfolgreich (`failed_checks == 0`)
- **1**: Mindestens ein Check fehlgeschlagen

---

## Profile-Konfiguration

Die Profile werden in `config/test_health_profiles.toml` definiert.

### Struktur

```toml
version = "0.1"
default_profile = "weekly_core"

[profiles.<profile_name>]
description = "Beschreibung des Profils"
time_window_days = 7  # optional, für spätere Heatmaps

[[profiles.<profile_name>.checks]]
id = "unique_check_id"
name = "Human-Readable Name"
cmd = "bash command to execute"
weight = 3  # Gewichtung (integer > 0)
category = "tests"  # Kategorie (z.B. tests, offline_synth, trigger_training)
```

### Beispiel: `weekly_core`

```toml
[profiles.weekly_core]
description = "Wöchentlicher Kern-Gesundheitscheck (Research & Offline)"
time_window_days = 7

[[profiles.weekly_core.checks]]
id = "pytest_core_offline"
name = "Pytest Core & Offline"
cmd = "pytest -q tests/core tests/offline --maxfail=1 -x"
weight = 3
category = "tests"

[[profiles.weekly_core.checks]]
id = "offline_synth_smoke"
name = "OfflineSynthSession Smoke"
cmd = "python scripts/run_offline_synth_session_smoke.py"
weight = 2
category = "offline_synth"

[[profiles.weekly_core.checks]]
id = "trigger_training_demo"
name = "TriggerTraining Drill Demo"
cmd = "python scripts/run_offline_trigger_training_drill_example.py --session-id TEST_HEALTH_SMOKE"
weight = 2
category = "trigger_training"
```

### Verfügbare Profile (v0)

| Profil | Beschreibung | Checks | Dauer (ca.) |
|--------|--------------|--------|-------------|
| `weekly_core` | Wöchentlicher Kern-Check (Research & Offline) | 5 | 2-5 Min |
| `daily_quick` | Tägliche Quick-Checks (nur kritische Tests) | 2 | <1 Min |
| `full_suite` | Vollständiger Check (alle Module) | 4 | 5-15 Min |

---

## Health-Score-System

### Berechnung

Der Health-Score wird gewichtet berechnet:

```
health_score = (passed_weight / total_weight) * 100.0
```

- `passed_weight`: Summe der Gewichte aller erfolgreich bestandenen Checks
- `total_weight`: Summe aller Check-Gewichte

### Ampel-Interpretation

| Score-Range | Ampel | Bedeutung |
|-------------|-------|-----------|
| **80-100** | 🟢 Grün | **Gesund** – Alle kritischen Systeme laufen einwandfrei |
| **50-80** | 🟡 Gelb | **Teilweise gesund** – Genauer hinsehen, einige Checks fehlgeschlagen |
| **<50** | 🔴 Rot | **Kritisch** – Sofortiges Handeln erforderlich |

### Beispiel

Profil `weekly_core` hat 5 Checks:

| Check | Weight | Status |
|-------|--------|--------|
| Check 1 | 3 | ✅ PASS |
| Check 2 | 2 | ✅ PASS |
| Check 3 | 2 | ❌ FAIL |
| Check 4 | 2 | ✅ PASS |
| Check 5 | 1 | ✅ PASS |

**Berechnung**:
- `passed_weight = 3 + 2 + 2 + 1 = 8`
- `total_weight = 3 + 2 + 2 + 2 + 1 = 10`
- `health_score = (8 / 10) * 100.0 = 80.0` → 🟢 Grün

---

## Report-Struktur

Nach jedem Profil-Lauf wird ein timestamp-basierter Report-Ordner erstellt:

```
reports/test_health/
├── 20251210_143012_weekly_core/
│   ├── summary.json        # Maschinenlesbar (JSON)
│   ├── summary.md          # Human-Readable (Markdown)
│   └── summary.html        # Visualisiert (HTML)
```

### `summary.json`

Vollständiges Summary-Objekt mit allen Check-Resultaten, Timestamps, Health-Score.

```json
{
  "profile_name": "weekly_core",
  "started_at": "2025-12-10T14:30:12.123456",
  "finished_at": "2025-12-10T14:35:45.678901",
  "health_score": 80.0,
  "passed_checks": 4,
  "failed_checks": 1,
  "skipped_checks": 0,
  "total_weight": 10,
  "passed_weight": 8,
  "checks": [
    {
      "id": "pytest_core_offline",
      "name": "Pytest Core & Offline",
      "status": "PASS",
      "duration_seconds": 12.34,
      "weight": 3,
      ...
    },
    ...
  ]
}
```

### `summary.md`

Markdown-Report mit Tabelle, Ampel-Interpretation, Check-Details.

### `summary.html`

Self-contained HTML-Report mit inline CSS, farblichen Markierungen, responsive Design.

---

## Erweiterungen (v1+)

Die v0-Implementierung ist bewusst minimalistisch. Geplante Erweiterungen:

- **Scheduling**: Cron/GitHub-Actions-Integration für tägliche/wöchentliche Runs
- **Historische Trends**: Health-Score-Verlauf über Zeit (Heatmaps)
- **Alerting**: Slack/Email-Benachrichtigung bei Rot/Gelb-Status
- **Parallel-Execution**: Checks parallel statt sequenziell ausführen
- **Check-Retries**: Automatische Retries bei flaky Tests
- **Diff-Reports**: Vergleich zwischen zwei Profil-Runs
- **KI-Datenexport**: Strukturierte Daten für KI-Testdatenspezialist

---

## API-Referenz

### `load_test_health_profile(config_path, profile_name) -> list[TestCheckConfig]`

Lädt ein Profil aus der TOML-Config.

### `run_single_check(check) -> TestCheckResult`

Führt einen einzelnen Check aus.

### `aggregate_health(profile_name, results) -> TestHealthSummary`

Aggregiert Check-Resultate zu einem Summary.

### `run_test_health_profile(profile_name, config_path, report_root) -> tuple[TestHealthSummary, Path]`

Main-Entry-Point: Führt ein Profil aus, erzeugt Reports.

---

## Entwickler-Hinweise

### Neues Profil hinzufügen

1. Öffne `config/test_health_profiles.toml`
2. Füge neue Profil-Sektion hinzu:

```toml
[profiles.my_custom_profile]
description = "Mein Custom-Profil"
time_window_days = 3

[[profiles.my_custom_profile.checks]]
id = "my_check_1"
name = "My Check 1"
cmd = "pytest -q tests/my_module"
weight = 2
category = "tests"
```

3. Ausführen:

```bash
python scripts/run_test_health_profile.py --profile my_custom_profile
```

### Neuen Check hinzufügen

Checks können beliebige Shell-Commands sein:

- **Pytest**: `pytest -q tests/my_module`
- **Python-Script**: `python scripts/my_smoke_test.py`
- **Shell-Script**: `bash scripts/check_db_connection.sh`
- **Custom-Command**: `curl -f https://api.example.com/health`

**Wichtig**: Command muss Exit-Code 0 bei Erfolg zurückgeben!

### Tests erweitern

Siehe `tests/ops/test_test_health_runner.py` für Beispiele.

---

## FAQ

### Warum gewichtete Health-Scores?

Nicht alle Checks sind gleich wichtig. Core-Tests (z.B. `pytest tests/core`) haben höheres Gewicht als Smoke-Tests.

### Wie lange dauert ein Profil-Lauf?

- `daily_quick`: <1 Min
- `weekly_core`: 2-5 Min
- `full_suite`: 5-15 Min (abhängig von Test-Suite-Größe)

### Kann ich Checks parallel ausführen?

In v0: Nein (sequenziell). Geplant für v1.

### Wie integriere ich das in CI/CD?

Beispiel GitHub Actions:

```yaml
name: Test Health Check

on:
  schedule:
    - cron: '0 6 * * 1'  # Jeden Montag um 6:00 UTC

jobs:
  test-health:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: python scripts/run_test_health_profile.py --profile weekly_core
```

---

## Trigger-Bedingungen & Alerting (Neu)

**Stand**: Dezember 2024

### Trigger-Config

Seit v0.2 unterstützt die Test Health Automation **erweiterte Trigger-Bedingungen** pro Profil, die automatisch bei jedem Run evaluiert werden:

```toml
[profiles.weekly_core]
description = "Wöchentlicher Kern-Gesundheitscheck"
time_window_days = 7

  [profiles.weekly_core.triggers]
  min_total_runs = 5               # Mindestanzahl Runs im Zeitfenster
  max_fail_rate = 0.20             # Max. 20% Fails erlaubt
  max_consecutive_failures = 3     # Max. 3 Fails in Folge
  max_hours_since_last_run = 168   # Max. 7 Tage ohne Run
  require_critical_green = true    # Kritische Testgruppen müssen grün sein

[[profiles.weekly_core.checks]]
id = "pytest_smoke_core"
name = "Pytest Smoke & Core"
cmd = "pytest tests/..."
weight = 3
category = "tests"
```

#### Verfügbare Trigger

| Trigger                      | Beschreibung                                  | Severity | Beispiel |
|------------------------------|-----------------------------------------------|----------|----------|
| `min_total_runs`             | Mindestanzahl Runs im Zeitfenster             | warning  | `5`      |
| `max_fail_rate`              | Maximale Fail-Rate (0.0 - 1.0)                | error    | `0.20`   |
| `max_consecutive_failures`   | Max. aufeinanderfolgende Failures             | error    | `3`      |
| `max_hours_since_last_run`   | Max. Stunden seit letztem Run                 | warning  | `168`    |
| `require_critical_green`     | Kritische Testgruppen müssen grün sein        | error    | `true`   |

#### Trigger-Evaluierung

- Trigger werden **automatisch** bei jedem Run evaluiert
- Violations werden im Report ausgegeben (JSON/MD/HTML)
- Exit-Code bleibt unverändert (nur Failed Checks triggern Exit 1)
- Violations sind **additiv** zum Health-Score (informativ, nicht blockierend)

### Slack-Notifications

Die Test Health Automation kann **automatisch Slack-Notifications** versenden bei:

- Fehlgeschlagenen Checks (`failed_checks > 0`)
- Trigger-Violations (konfigurierbare `min_severity`)

#### Konfiguration

```toml
[notifications.slack]
enabled = true
webhook_env_var = "PEAK_TRADE_SLACK_WEBHOOK_TESTHEALTH"
min_severity = "warning"    # "info" | "warning" | "error"
include_profile_name = true
include_violations = true
```

#### Setup

1. **Webhook erstellen** in Slack:
   - Gehe zu Slack App Directory → Incoming Webhooks
   - Erstelle einen neuen Webhook für den gewünschten Channel (z.B. `#test-health`)
   - Kopiere die Webhook-URL

2. **ENV-Variable setzen**:
   ```bash
   export PEAK_TRADE_SLACK_WEBHOOK_TESTHEALTH="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
   ```

3. **In CI/CD** (GitHub Actions):
   ```yaml
   - name: Run Test Health
     env:
       PEAK_TRADE_SLACK_WEBHOOK_TESTHEALTH: ${{ secrets.SLACK_WEBHOOK_TESTHEALTH }}
     run: |
       python scripts/run_test_health_profile.py --profile weekly_core
   ```

#### Beispiel-Notification

```
🔴 Test Health Report: weekly_core

Health Score: 65.0 / 100.0
Passed Checks: 3
Failed Checks: 2

Trigger Violations: 2
  ❌ Fail-Rate zu hoch: 40.00% > 20.00%
  ⚠️ Zu wenige Runs im Zeitfenster: 3 < 5

Report: reports/test_health/20241210_150342_weekly_core/
```

#### Fail-Safe

- Slack-Fehler **killen nicht die Pipeline** (try/catch)
- Bei fehlendem Webhook: leise deaktiviert (kein Fehler)
- Bei API-Fehlern: Warning im Log, aber Exit-Code unverändert

---

## Siehe auch

- [PHASE_72_LIVE_OPERATOR_CONSOLE.md](../PHASE_72_LIVE_OPERATOR_CONSOLE.md) – Live-Monitoring
- [PHASE_73_LIVE_DRY_RUN_DRILLS.md](../PHASE_73_LIVE_DRY_RUN_DRILLS.md) – Dry-Run-Drills
- [OBSERVABILITY_AND_MONITORING_PLAN.md](../OBSERVABILITY_AND_MONITORING_PLAN.md) – Monitoring-Plan

---

**Kontakt**: Peak_Trade Ops Team  
**Lizenz**: Intern (Peak_Trade Project)
