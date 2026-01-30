# Phase 37: Testnet-Orchestrierung & Limits

## Zusammenfassung

Phase 37 implementiert einen **kontrollierten Testnet-Desk** mit:
- Zentralen **Testnet-Limits** (pro Run, pro Tag, pro Symbol)
- Vordefinierten **Session-Profilen** (z.B. `ma_crossover_small`, `btc_momentum`)
- Einer **Orchestrierungs-CLI** zum standardisierten Starten von Sessions
- Optionaler **Auto-Report-Generierung** nach Session-Ende

**Status**: Implementiert
**Neue Tests**: ~50+ Tests in 3 neuen Test-Dateien

## Motivation

Vor Phase 37 waren Testnet-Sessions ad-hoc und unkontrolliert:
- Keine einheitliche Konfiguration
- Keine Tages-Budgets oder Run-Limits
- Keine standardisierten Test-Setups

Phase 37 macht Testnet-Betrieb **planbar & kontrolliert** - wie ein kleiner
Testnet-Desk mit Budget und Gameplan.

## Architektur

```
┌─────────────────────────────────────────────────────────────────┐
│                  Orchestrator CLI                               │
│         scripts/orchestrate_testnet_runs.py                     │
└─────────────────────┬───────────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
        ▼             ▼             ▼
┌───────────┐  ┌───────────┐  ┌───────────┐
│  Profile  │  │  Limits   │  │  Config   │
│  Loader   │  │Controller │  │  Loader   │
└─────┬─────┘  └─────┬─────┘  └───────────┘
      │              │
      │              ▼
      │        ┌───────────┐
      │        │  Usage    │
      │        │  Store    │
      │        └───────────┘
      │
      ▼
┌─────────────────────────────────────────────────────────────────┐
│              Testnet Session (Phase 35)                         │
│           scripts/run_testnet_session.py                        │
└─────────────────────────────────────────────────────────────────┘
```

### Komponenten

#### 1. TestnetLimitsController (`src/live/testnet_limits.py`)

Kontrolliert alle Testnet-Limits:

```python
from src.live.testnet_limits import (
    TestnetLimitsController,
    load_testnet_limits_from_config,
)

controller = load_testnet_limits_from_config(cfg)

# Alle Checks in einem Aufruf
result = controller.check_run_allowed(
    symbol="BTC/EUR",
    planned_notional=500.0,
    planned_trades=20,
    planned_duration_minutes=60,
)

if result.allowed:
    # Run starten...
    controller.register_run_consumption(notional=480.0, trades=18)
else:
    print(f"Geblockt: {result.reasons}")
```

**Limit-Typen**:
- `TestnetRunLimits`: Max Notional/Trades/Duration pro Run
- `TestnetDailyLimits`: Max Notional/Trades pro Tag
- `TestnetSymbolPolicy`: Symbol-Whitelist

#### 2. TestnetUsageStore (`src/live/testnet_limits.py`)

Persistiert die taegliche Testnet-Nutzung:

```python
from src.live.testnet_limits import TestnetUsageStore

store = TestnetUsageStore(base_dir=Path("test_results"))

# Heutigen Stand laden
state = store.load_for_today()
print(f"Notional heute: {state.notional_used}")
print(f"Trades heute: {state.trades_executed}")

# Nach Run aktualisieren
state.notional_used += 500.0
state.trades_executed += 15
store.save_for_today(state)
```

**Speicherformat**: JSON-Dateien unter `{base_dir}/usage/usage_YYYY-MM-DD.json`

#### 3. TestnetSessionProfile (`src/live/testnet_profiles.py`)

Vordefinierte Test-Konfigurationen:

```python
from src.live.testnet_profiles import (
    load_testnet_profiles,
    get_testnet_profile,
)

profiles = load_testnet_profiles(cfg)
profile = profiles["ma_crossover_small"]

print(f"Strategie: {profile.strategy}")
print(f"Symbol: {profile.symbol}")
print(f"Laufzeit: {profile.duration_minutes} Minuten")
```

#### 4. TestnetOrchestrator (`scripts/orchestrate_testnet_runs.py`)

Kombiniert Profile, Limits und Sessions:

```python
from scripts.orchestrate_testnet_runs import TestnetOrchestrator

orchestrator = TestnetOrchestrator(
    cfg=cfg,
    limits_controller=limits_controller,
    orch_config=orch_config,
)

# Dry-Run (nur Checks)
result = orchestrator.run_profile("ma_crossover_small", dry_run=True)

# Echter Run
result = orchestrator.run_profile("ma_crossover_small", dry_run=False)
```

## Config-Referenz

### [testnet_limits.run]

```toml
[testnet_limits.run]
max_notional_per_run = 1000.0    # Max. Handelsvolumen pro Run (EUR)
max_trades_per_run = 50         # Max. Anzahl Trades pro Run
max_duration_minutes = 240      # Max. Laufzeit pro Run (4 Stunden)
```

### [testnet_limits.daily]

```toml
[testnet_limits.daily]
max_notional_per_day = 5000.0   # Max. Gesamt-Notional pro Tag (EUR)
max_trades_per_day = 200        # Max. Anzahl Trades pro Tag
```

### [testnet_limits.symbols]

```toml
[testnet_limits.symbols]
allowed = ["BTC/EUR", "ETH/EUR"]  # Symbol-Whitelist
```

### [testnet_profiles.*]

```toml
[testnet_profiles.ma_crossover_small]
strategy = "ma_crossover"
symbol = "BTC/EUR"
timeframe = "1m"
duration_minutes = 60
max_notional = 500.0
max_trades = 20
description = "Kleiner BTC/EUR Intraday-Test"

[testnet_profiles.btc_momentum]
strategy = "momentum_1h"
symbol = "BTC/EUR"
timeframe = "5m"
duration_minutes = 120
max_notional = 1000.0
max_trades = 30
description = "BTC Momentum-Test"
```

### [testnet_orchestration]

```toml
[testnet_orchestration]
runs_base_dir = "test_runs/"            # Verzeichnis fuer Run-Logs
reports_dir = "test_results/reports/"   # Verzeichnis fuer Reports
auto_generate_report = true             # Auto-Report nach Run
report_format = "markdown"              # Report-Format
usage_retention_days = 30               # Aufbewahrungszeit Usage-Daten
```

## CLI-Verwendung

### Profile auflisten

```bash
python3 -m scripts.orchestrate_testnet_runs --list
```

Output:
```
Verfuegbare Testnet-Profile:
==================================================

[ma_crossover_small]
  Strategie:    ma_crossover
  Symbol:       BTC/EUR
  Timeframe:    1m
  Laufzeit:     60 Minuten
  Max Notional: 500.00
  Max Trades:   20
  Beschreibung: Kleiner BTC/EUR Intraday-Test
...
```

### Tages-Budget anzeigen

```bash
python3 -m scripts.orchestrate_testnet_runs --budget
```

Output:
```
=== Testnet Tages-Budget ===
Datum: 2024-12-04

Verbraucht heute:
  Notional:  1500.00
  Trades:    45
  Runs:      3

Verbleibend:
  Notional:  3500.00
  Trades:    155

Limits:
  Max Notional/Tag:  5000.0
  Max Trades/Tag:    200
==============================
```

### Profil starten (Dry-Run)

```bash
python3 -m scripts.orchestrate_testnet_runs --profile ma_crossover_small --dry-run
```

Prueft alle Limits ohne Session zu starten.

### Profil starten (Echt)

```bash
python3 -m scripts.orchestrate_testnet_runs --profile ma_crossover_small
```

**Voraussetzungen**:
- `KRAKEN_TESTNET_API_KEY` gesetzt
- `KRAKEN_TESTNET_API_SECRET` gesetzt
- `[environment] mode = "testnet"` in config.toml

### Mit Overrides

```bash
python3 -m scripts.orchestrate_testnet_runs --profile ma_crossover_small \
    --override-duration 30 \
    --override-max-notional 300.0
```

## Beispiel-Workflows

### Workflow 1: Taeglicher Smoke-Test

```bash
# Morgens: Budget pruefen
python3 -m scripts.orchestrate_testnet_runs --budget

# Quick-Smoke starten
python3 -m scripts.orchestrate_testnet_runs --profile quick_smoke

# Budget nach Run
python3 -m scripts.orchestrate_testnet_runs --budget
```

### Workflow 2: Strategie-Validierung

```bash
# Dry-Run zuerst
python3 -m scripts.orchestrate_testnet_runs --profile btc_momentum --dry-run

# Bei OK: Echter Run
python3 -m scripts.orchestrate_testnet_runs --profile btc_momentum

# Report im reports_dir pruefen
```

### Workflow 3: Mehrere Profile pro Tag

```bash
# Erstes Profil
python3 -m scripts.orchestrate_testnet_runs --profile ma_crossover_small

# Zweites Profil (wird gegen Daily-Limits geprueft)
python3 -m scripts.orchestrate_testnet_runs --profile eth_swing

# Drittes Profil koennte geblockt werden wenn Daily-Limits erreicht
```

## Safety-Hinweise

1. **Nur Testnet**: Phase 37 ist fuer `TradingEnvironment.TESTNET` konzipiert
2. **Limits ergaenzen LiveRiskLimits**: TestnetLimits ersetzen nicht die
   bestehenden LiveRiskLimits, sondern ergaenzen sie als zusaetzliche Schicht
3. **Usage-Persistenz**: Tages-Nutzung wird in JSON-Dateien gespeichert und
   ist von Neustart unabhaengig
4. **validate_only=true**: Default-Verhalten von KrakenTestnetClient - Orders
   werden validiert, aber nicht ausgefuehrt

## Dateien

| Datei | Beschreibung |
|-------|--------------|
| `src/live/testnet_limits.py` | Limits, Controller, UsageStore |
| `src/live/testnet_profiles.py` | Profile-Dataclass und Loader |
| `scripts/orchestrate_testnet_runs.py` | Orchestrator-CLI |
| `config/config.toml` | Produktions-Config mit Phase-37-Bloecken |
| `config/config.test.toml` | Test-Config mit Phase-37-Bloecken |
| `tests/test_testnet_limits.py` | Tests fuer Limits |
| `tests/test_testnet_profiles.py` | Tests fuer Profile |
| `tests/test_testnet_orchestration.py` | Tests fuer Orchestrator |

## Naechste Schritte

- [ ] Erweiterte Reporting-Integration (Phase-30-Reports)
- [ ] Scheduling-Integration (Cron-Jobs fuer regelmaessige Tests)
- [ ] Multi-Profil-Runs (sequenziell oder parallel)
- [ ] Dashboard-Integration (Web-UI fuer Budget-Monitoring)
