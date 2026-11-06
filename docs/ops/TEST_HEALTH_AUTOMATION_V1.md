# Test Health Automation v1

**Stand**: Dezember 2024  
**Status**: ✅ Implementiert  
**Autor**: Peak_Trade Ops Team  
**Version**: v1

---

## Überblick

Die **Test Health Automation v1** erweitert die bestehende v0-Implementierung um:

1. **Strategy-Coverage-Checks**: Prüft, ob für alle aktiven Strategien genügend Backtests und Paper-Runs durchgeführt wurden
2. **Strategy-Switch Sanity Check**: Governance-Prüfung der Live-Strategy-Switch-Konfiguration (KEIN automatisches Switching!)
3. **Erweiterte Slack-Notifications**: Umfasst Strategy-Coverage und Switch-Sanity Violations
4. **Erweiterte CLI-Optionen**: Selektives Deaktivieren einzelner Checks

### Komponenten (v1)

| Komponente | Pfad | Beschreibung |
|------------|------|--------------|
| Config | `config/test_health_profiles.toml` | Erweitert um `[strategy_coverage]` und `[switch_sanity]` |
| Runner | `src/ops/test_health_runner.py` | v1-Datenmodelle und Funktionen |
| Slack | `src/notifications/slack.py` | `send_test_health_slack_notification_v1()` |
| CLI | `scripts/run_test_health_profile.py` | Neue Flags: `--no-strategy-coverage`, `--no-switch-sanity`, `--no-slack` |
| Tests | `tests/ops/test_test_health_v1.py` | Vollständige Test-Suite für v1 |

---

## Quick-Start

### Standard-Aufruf (alle v1-Features)

```bash
python3 scripts/run_test_health_profile.py --profile daily_quick
```

### Ohne Strategy-Coverage (z.B. für lokale Tests)

```bash
python3 scripts/run_test_health_profile.py --no-strategy-coverage
```

### Ohne Switch-Sanity (z.B. für CI ohne Live-Config)

```bash
python3 scripts/run_test_health_profile.py --no-switch-sanity
```

### Ohne Slack (für lokale Entwicklung)

```bash
python3 scripts/run_test_health_profile.py --no-slack
```

### Alles deaktiviert (nur Profile-Checks)

```bash
python3 scripts/run_test_health_profile.py --no-strategy-coverage --no-switch-sanity --no-slack
```

---

## v1-Konfiguration

### 1. Strategy-Coverage

Prüft, ob für alle in `live_profile.strategy_switch.allowed` definierten Strategien genügend Test-Runs durchgeführt wurden.

```toml
[strategy_coverage]
enabled = true
window_days = 7                     # Zeitraum für Run-Zählung
min_backtests_per_strategy = 3      # Mindestanzahl Backtests
min_paper_runs_per_strategy = 1     # Mindestanzahl Paper-Runs
link_to_strategy_switch_allowed = true  # Nur Strategien aus allowed prüfen
runs_directory = "reports/experiments"  # Verzeichnis mit Experiment-Runs
```

#### Wie es funktioniert

1. Lädt die Liste der erlaubten Strategien aus `live_profile.strategy_switch.allowed`
2. Durchsucht `runs_directory` nach JSON-Dateien mit Experiment-Runs
3. Zählt Backtests und Paper-Runs pro Strategie im Zeitfenster
4. Erzeugt Violations wenn Mindestwerte nicht erreicht werden

#### Violation-Beispiele

```
Strategy 'rsi_reversion': only 2/3 backtests in last 7 days
Strategy 'breakout': only 0/1 paper runs in last 7 days
```

### 2. Switch-Sanity Check

Statische Validierung der Strategy-Switch-Konfiguration. **Führt KEIN automatisches Switching durch!**

```toml
[switch_sanity]
enabled = true
config_path = "config/config.toml"  # Pfad zur Live-Config
section_path = "live_profile.strategy_switch"  # TOML-Pfad
allow_r_and_d_in_allowed = false    # R&D-Strategien verboten
require_active_in_allowed = true    # active muss in allowed sein
require_non_empty_allowed = true    # allowed darf nicht leer sein

# R&D-Strategien (dürfen nicht in allowed stehen)
r_and_d_strategy_keys = [
    "armstrong_cycle",
    "el_karoui_vol_model",
    "ehlers_cycle_filter",
    "meta_labeling",
    "bouchaud_microstructure",
    "vol_regime_overlay",
]
```

#### Live-Config-Struktur

Die geprüfte Config-Sektion muss so aussehen:

```toml
[live_profile.strategy_switch]
active_strategy_id = "ma_crossover"
allowed = ["ma_crossover", "rsi_reversion", "breakout"]
auto_switch_enabled = false
require_confirmation = true
```

#### Checks

| Check | Beschreibung | Violation-Beispiel |
|-------|--------------|-------------------|
| `require_non_empty_allowed` | `allowed` darf nicht leer sein | "allowed list must not be empty" |
| `require_active_in_allowed` | `active_strategy_id` muss in `allowed` enthalten sein | "active_strategy_id 'unknown' not in allowed list" |
| `allow_r_and_d_in_allowed` | R&D-Strategien dürfen nicht in `allowed` stehen | "Strategy 'armstrong_cycle' is tier r_and_d but present in allowed list" |

### 3. Erweiterte Slack-Notifications

```toml
[notifications.slack]
enabled = true
webhook_env_var = "PEAK_TRADE_SLACK_WEBHOOK_TESTHEALTH"
min_severity = "warning"
include_profile_name = true
include_violations = true
include_strategy_coverage = true  # v1: Strategy-Coverage in Nachricht
include_switch_sanity = true      # v1: Switch-Sanity in Nachricht
```

#### Beispiel-Slack-Nachricht (v1)

```
[Peak_Trade · TestHealth v1] Status: FAILED

*Profile*: daily_quick
*Health Score*: 65.0/100
*Passed Checks*: 3
*Failed Checks*: 2

*Trigger Violations*: 1
  ❌ Fail-Rate zu hoch: 40.00% > 20.00%

*Strategy Coverage* (3 checked):
  ❌ Strategy 'ma_crossover': only 1/3 backtests in last 7 days
  ❌ Strategy 'ma_crossover': only 0/1 paper runs in last 7 days

*Switch Sanity Violations*:
  ❌ active_strategy_id 'unknown' not in allowed list
  ❌ Strategy 'armstrong_cycle' is tier r_and_d but present in allowed list

*Report*: `reports/test_health/20241210_143000_daily_quick`
```

---

## Operator-Flow

### 1. HTML-Report lesen

Nach jedem Run wird ein HTML-Report generiert:

```
reports/test_health/<timestamp>_<profile>/summary.html
```

Der Report enthält:
- Health-Score mit Ampel-Interpretation
- Trigger-Violations (falls vorhanden)
- **v1: Strategy-Coverage** mit Tabelle pro Strategie
- **v1: Switch-Sanity** Status und Violations
- Check-Details mit Stdout/Stderr bei Fehlern

### 2. Strategy-Coverage interpretieren

| Status | Bedeutung | Aktion |
|--------|-----------|--------|
| ✅ OK | Genügend Backtests und Paper-Runs | Keine |
| ❌ Backtests fehlen | Strategie hat zu wenige Backtests | Backtests für Strategie ausführen |
| ❌ Paper-Runs fehlen | Strategie hat zu wenige Paper-Runs | Paper-Trading-Session starten |

**Typische Ursachen für Coverage-Violations:**

1. Neue Strategie zu `allowed` hinzugefügt, aber noch nicht getestet
2. Experiment-Runs älter als `window_days`
3. Runs im falschen Verzeichnis gespeichert

### 3. Switch-Sanity-Fehler beheben

| Violation | Ursache | Fix |
|-----------|---------|-----|
| "allowed list must not be empty" | Keine Strategien erlaubt | Mindestens eine Strategie zu `allowed` hinzufügen |
| "active_strategy_id not in allowed" | Aktive Strategie nicht freigegeben | Entweder Strategie zu `allowed` hinzufügen ODER `active_strategy_id` ändern |
| "is tier r_and_d but present in allowed" | R&D-Strategie in Produktion | Strategie aus `allowed` entfernen (R&D nur für Research!) |

---

## v1-Datenmodelle

### StrategyCoverageConfig

```python
@dataclass
class StrategyCoverageConfig:
    enabled: bool = True
    window_days: int = 7
    min_backtests_per_strategy: int = 3
    min_paper_runs_per_strategy: int = 1
    link_to_strategy_switch_allowed: bool = True
    runs_directory: str = "reports/experiments"
```

### StrategyCoverageResult

```python
@dataclass
class StrategyCoverageResult:
    enabled: bool
    strategies_checked: int
    strategies_with_violations: int
    coverage_stats: list[StrategyCoverageStats]
    all_violations: list[str]
    is_healthy: bool
```

### SwitchSanityConfig

```python
@dataclass
class SwitchSanityConfig:
    enabled: bool = True
    config_path: str = "config/config.toml"
    section_path: str = "live_profile.strategy_switch"
    allow_r_and_d_in_allowed: bool = False
    require_active_in_allowed: bool = True
    require_non_empty_allowed: bool = True
    r_and_d_strategy_keys: list[str]
```

### SwitchSanityResult

```python
@dataclass
class SwitchSanityResult:
    enabled: bool
    is_ok: bool
    violations: list[str]
    active_strategy_id: str
    allowed: list[str]
    config_path: str
```

---

## API-Referenz (v1)

### `compute_strategy_coverage(config, strategy_ids, now) -> StrategyCoverageResult`

Berechnet Strategy-Coverage für alle gegebenen Strategien.

```python
from src.ops.test_health_runner import (
    StrategyCoverageConfig,
    compute_strategy_coverage,
)

config = StrategyCoverageConfig(
    min_backtests_per_strategy=3,
    min_paper_runs_per_strategy=1,
)
result = compute_strategy_coverage(config, ["ma_crossover", "rsi_reversion"])

if not result.is_healthy:
    print(f"Violations: {result.all_violations}")
```

### `run_switch_sanity_check(cfg) -> SwitchSanityResult`

Führt den Strategy-Switch Sanity Check durch.

```python
from src.ops.test_health_runner import (
    SwitchSanityConfig,
    run_switch_sanity_check,
)

config = SwitchSanityConfig(
    config_path="config/config.toml",
    allow_r_and_d_in_allowed=False,
)
result = run_switch_sanity_check(config)

if not result.is_ok:
    print(f"Violations: {result.violations}")
    print(f"Active: {result.active_strategy_id}")
    print(f"Allowed: {result.allowed}")
```

### `run_test_health_profile(..., skip_strategy_coverage, skip_switch_sanity)`

Erweiterte Signatur für v1:

```python
summary, report_dir = run_test_health_profile(
    profile_name="daily_quick",
    config_path=Path("config/test_health_profiles.toml"),
    report_root=Path("reports/test_health"),
    skip_strategy_coverage=False,  # v1
    skip_switch_sanity=False,      # v1
)
```

---

## Tests

```bash
# Alle v1-Tests ausführen
python3 -m pytest tests/ops/test_test_health_v1.py -v

# Spezifische Test-Klasse
python3 -m pytest tests/ops/test_test_health_v1.py::TestComputeStrategyCoverage -v

# Integration mit bestehenden Tests
python3 -m pytest tests/ops/ -v
```

---

## Migration von v0 zu v1

### Schritt 1: Config erweitern

Füge die neuen Sektionen zu `config/test_health_profiles.toml` hinzu:

```toml
# Existierend...
[notifications.slack]
enabled = true
# ...

# NEU v1:
include_strategy_coverage = true
include_switch_sanity = true

# NEU v1:
[strategy_coverage]
enabled = true
window_days = 7
min_backtests_per_strategy = 3
min_paper_runs_per_strategy = 1
link_to_strategy_switch_allowed = true
runs_directory = "reports/experiments"

# NEU v1:
[switch_sanity]
enabled = true
config_path = "config/config.toml"
section_path = "live_profile.strategy_switch"
allow_r_and_d_in_allowed = false
require_active_in_allowed = true
require_non_empty_allowed = true
```

### Schritt 2: Live-Config erstellen

Falls noch nicht vorhanden, füge `[live_profile.strategy_switch]` zu `config/config.toml` hinzu:

```toml
[live_profile.strategy_switch]
active_strategy_id = "ma_crossover"
allowed = ["ma_crossover", "rsi_reversion", "breakout"]
auto_switch_enabled = false
require_confirmation = true
```

### Schritt 3: Testen

```bash
# Erst ohne v1-Features testen
python3 scripts/run_test_health_profile.py --no-strategy-coverage --no-switch-sanity

# Dann mit v1-Features
python3 scripts/run_test_health_profile.py
```

---

## Siehe auch

- [TEST_HEALTH_AUTOMATION_V0.md](TEST_HEALTH_AUTOMATION_V0.md) – Basis-Dokumentation
- [PHASE_72_LIVE_OPERATOR_CONSOLE.md](../PHASE_72_LIVE_OPERATOR_CONSOLE.md) – Live-Monitoring
- [OBSERVABILITY_AND_MONITORING_PLAN.md](../OBSERVABILITY_AND_MONITORING_PLAN.md) – Monitoring-Plan

---

**Kontakt**: Peak_Trade Ops Team  
**Lizenz**: Intern (Peak_Trade Project)
