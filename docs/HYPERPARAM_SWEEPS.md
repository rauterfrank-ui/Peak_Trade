# Hyperparameter-Sweeps (Phase 20)

Dokumentation für die Hyperparameter-Sweep-Infrastruktur in Peak_Trade.

---

## Einführung

### Was ist ein Hyperparameter-Sweep?

Ein Hyperparameter-Sweep ist eine systematische Suche über verschiedene Parameter-Kombinationen einer Trading-Strategie, um die optimale Konfiguration zu finden.

**Beispiel:** Für eine Moving-Average-Crossover-Strategie könnten wir testen:
- `fast_window` ∈ {10, 20, 30}
- `slow_window` ∈ {50, 100, 150}

Das ergibt 3 × 3 = 9 Kombinationen, die jeweils als Backtest ausgeführt werden.

### Motivation

- **Optimierung**: Finde die besten Parameter für eine Strategie
- **Robustheit**: Prüfe, ob Performance bei Parametervariation stabil bleibt
- **Vergleichbarkeit**: Alle Runs werden in der Registry gespeichert und sind reproduzierbar

### Scope

- **Nur Backtests**: Keine Live- oder Testnet-Orders
- **Registry-Integration**: Volle Reproduzierbarkeit
- **Safety**: SafetyGuard und TradingEnvironment bleiben unverändert

---

## Architektur

### Komponenten

```
┌──────────────────────────────────────────────────────────────────┐
│                    Sweep Infrastructure (Phase 20)                │
├──────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌─────────────────────┐    ┌─────────────────────────────────┐  │
│  │  src/sweeps/        │    │  scripts/run_sweep_strategy.py  │  │
│  │  - engine.py        │◀───│  (CLI Interface)                │  │
│  │  - __init__.py      │    └─────────────────────────────────┘  │
│  └─────────────────────┘                                          │
│           │                                                       │
│           ▼                                                       │
│  ┌─────────────────────┐    ┌─────────────────────────────────┐  │
│  │  Strategy Registry  │    │  Experiments Registry           │  │
│  │  (src/strategies)   │    │  (src/core/experiments.py)      │  │
│  └─────────────────────┘    └─────────────────────────────────┘  │
│           │                          │                            │
│           ▼                          ▼                            │
│  ┌─────────────────────┐    ┌─────────────────────────────────┐  │
│  │  Backtest Engine    │    │  experiments.csv                │  │
│  │  (src/backtest)     │    │  (reports/experiments/)         │  │
│  └─────────────────────┘    └─────────────────────────────────┘  │
│                                                                    │
└──────────────────────────────────────────────────────────────────┘
```

### Dateien

| Datei | Beschreibung |
|-------|--------------|
| `src/sweeps/engine.py` | Sweep-Engine mit SweepConfig, SweepResult, SweepSummary |
| `src/sweeps/__init__.py` | Modul-Exports |
| `scripts/run_sweep_strategy.py` | CLI-Script für Sweeps |
| `config/sweeps/*.toml` | Vordefinierte Parameter-Grids |

### Registry-Integration

Jeder Sweep-Run wird als `run_type="sweep"` in der Registry gespeichert:

- **sweep_name**: Gruppiert alle Runs eines Sweeps
- **sweep_id**: Eindeutige ID für den gesamten Sweep
- **params**: Die getestete Parameterkombination
- **stats**: Backtest-Metriken (total_return, sharpe, max_drawdown, ...)
- **tag**: Optionaler User-Tag

---

## Quickstart

### Beispiel 1: Sweep für `trend_following`

```bash
# Mit vordefiniertem Grid
python3 scripts/run_sweep_strategy.py --strategy trend_following \
    --grid config/sweeps/trend_following.toml \
    --tag optimization

# Mit Limit und Top-5 Ausgabe
python3 scripts/run_sweep_strategy.py --strategy trend_following \
    --grid config/sweeps/trend_following.toml \
    --max-runs 20 --top-n 5
```

### Beispiel 2: Sweep für `my_strategy`

```bash
# Mit vordefiniertem Grid
python3 scripts/run_sweep_strategy.py --strategy my_strategy \
    --grid config/sweeps/my_strategy.toml \
    --symbol BTC/EUR --tag volatility-test

# Mit CLI-Parametern (ohne Grid-Datei)
python3 scripts/run_sweep_strategy.py --strategy my_strategy \
    --param lookback_window=15,20,25 \
    --param entry_multiplier=1.2,1.5,2.0 \
    --param exit_multiplier=0.3,0.5
```

### Beispiel 3: Sweep für `mean_reversion`

```bash
# Mit echten Daten
python3 scripts/run_sweep_strategy.py --strategy mean_reversion \
    --grid config/sweeps/mean_reversion.toml \
    --data-file data/btc_eur_1h.csv \
    --tag production-test
```

### Beispiel 4: Dry-Run (nur Kombinationen anzeigen)

```bash
python3 scripts/run_sweep_strategy.py --strategy ma_crossover \
    --grid config/sweeps/ma_crossover.toml \
    --dry-run
```

### Beispiel 5: Export nach CSV

```bash
python3 scripts/run_sweep_strategy.py --strategy my_strategy \
    --grid config/sweeps/my_strategy.toml \
    --export results/my_strategy_sweep.csv
```

---

## CLI-Referenz

### `scripts/run_sweep_strategy.py`

```
usage: run_sweep_strategy.py [-h] [--strategy STRATEGY] [--list-strategies]
                              [--grid GRID] [--param KEY=VALUES]
                              [--data-file DATA_FILE] [--symbol SYMBOL]
                              [--timeframe TIMEFRAME] [--bars BARS]
                              [--sweep-name SWEEP_NAME] [--tag TAG]
                              [--max-runs MAX_RUNS]
                              [--sort-by {sharpe,total_return,max_drawdown,profit_factor,total_trades}]
                              [--sort-asc] [--top-n TOP_N] [--export PATH]
                              [--no-registry] [--dry-run] [--verbose]
                              [--config CONFIG]

Argumente:
  --strategy STRATEGY   Strategie-Key (z.B. ma_crossover, my_strategy)
  --list-strategies     Zeigt alle verfügbaren Strategien

Parameter-Grid:
  --grid GRID           Pfad zu TOML/JSON-Datei oder JSON-String
  --param KEY=VALUES    Parameter mit Werten (komma-separiert)

Daten:
  --data-file FILE      CSV-Datei mit OHLCV-Daten (sonst Dummy-Daten)
  --symbol SYMBOL       Trading-Pair (Default: BTC/EUR)
  --timeframe TF        Timeframe (Default: 1h)
  --bars N              Anzahl Dummy-Bars (Default: 500)

Sweep-Optionen:
  --sweep-name NAME     Name für Gruppierung
  --tag TAG             Tag für Registry-Filterung
  --max-runs N          Max. Anzahl Kombinationen
  --sort-by METRIC      Sortier-Metrik (Default: sharpe)
  --sort-asc            Aufsteigend sortieren
  --top-n N             Top-N in Ausgabe (Default: 10)

Output:
  --export PATH         CSV-Export der Ergebnisse
  --no-registry         Kein Registry-Logging
  --dry-run             Nur Kombinationen anzeigen
  --verbose, -v         Ausführliche Ausgabe
  --config PATH         Basis-Config (Default: config.toml)
```

---

## Vordefinierte Grids

### `config/sweeps/ma_crossover.toml`

```toml
[grid]
short_window = [5, 10, 20, 30]
long_window = [50, 100, 150, 200]
# 16 Kombinationen
```

### `config/sweeps/trend_following.toml`

```toml
[grid]
adx_period = [10, 14, 20]
adx_threshold = [20.0, 25.0, 30.0]
exit_threshold = [15.0, 20.0]
ma_period = [20, 50, 100]
use_ma_filter = [true, false]
# 108 Kombinationen (manche werden bei Validierung übersprungen)
```

### `config/sweeps/mean_reversion.toml`

```toml
[grid]
lookback = [10, 15, 20, 30]
entry_threshold = [-3.0, -2.5, -2.0, -1.5]
exit_threshold = [-0.5, 0.0, 0.5]
use_vol_filter = [true, false]
# 96 Kombinationen
```

### `config/sweeps/my_strategy.toml`

```toml
[grid]
lookback_window = [10, 15, 20, 25, 30]
entry_multiplier = [1.0, 1.5, 2.0, 2.5]
exit_multiplier = [0.25, 0.5, 0.75]
use_close_only = [false]
# 60 Kombinationen
```

---

## Best Practices

### 1. Laufzeit kontrollieren

Nutze `--max-runs` um bei großen Grids die Laufzeit zu begrenzen:

```bash
python3 scripts/run_sweep_strategy.py --strategy my_strategy \
    --grid config/sweeps/my_strategy.toml \
    --max-runs 30
```

### 2. Dry-Run zuerst

Prüfe immer erst die Kombinationen mit `--dry-run`:

```bash
python3 scripts/run_sweep_strategy.py --strategy trend_following \
    --grid config/sweeps/trend_following.toml \
    --dry-run
```

### 3. Tags für Filterung

Verwende aussagekräftige Tags:

```bash
# Für Optimierungs-Experimente
--tag optimization-v1

# Für verschiedene Datensets
--tag btc-2024

# Für Robustheitstests
--tag robustness-check
```

### 4. Overfitting vermeiden

- **In-Sample / Out-of-Sample**: Führe Sweeps auf einem Teil der Daten aus, validiere auf dem Rest
- **Nicht zu viele Parameter**: Beschränke das Grid auf die wichtigsten Parameter
- **Mehrere Zeiträume**: Teste die besten Konfigurationen auf verschiedenen Zeiträumen

```bash
# Training-Daten (2022-2023)
python3 scripts/run_sweep_strategy.py --strategy my_strategy \
    --grid config/sweeps/my_strategy.toml \
    --data-file data/btc_2022_2023.csv \
    --tag training

# Dann manuell die beste Konfiguration auf 2024 validieren
```

### 5. Ergebnisse analysieren

Nach dem Sweep:

```bash
# Alle Sweep-Runs anzeigen
python3 scripts/list_experiments.py --run-type sweep

# Top-Runs nach Sharpe
python3 scripts/analyze_experiments.py --mode top-runs --run-type sweep --metric sharpe
```

---

## Programmatische Nutzung

### Basic Usage

```python
from src.sweeps import SweepConfig, SweepEngine, run_strategy_sweep
import pandas as pd

# Daten laden
df = pd.read_csv("data/btc_eur_1h.csv", parse_dates=True, index_col=0)

# Convenience-Funktion
summary = run_strategy_sweep(
    strategy_key="my_strategy",
    param_grid={
        "lookback_window": [15, 20, 25],
        "entry_multiplier": [1.2, 1.5, 2.0],
    },
    data=df,
    tag="research",
    verbose=True,
)

# Beste Parameter
print(f"Best params: {summary.best_result.params}")
print(f"Best Sharpe: {summary.best_result.sharpe:.2f}")
```

### Advanced Usage

```python
from src.sweeps import SweepConfig, SweepEngine

# Konfiguration
config = SweepConfig(
    strategy_key="trend_following",
    param_grid={
        "adx_threshold": [20, 25, 30],
        "ma_period": [50, 100],
    },
    symbol="ETH/EUR",
    timeframe="4h",
    max_runs=10,
    sort_by="total_return",
    tag="eth-test",
)

# Engine mit Progress-Callback
def progress(current, total, params):
    print(f"Progress: {current}/{total}")

engine = SweepEngine(verbose=False, progress_callback=progress)
summary = engine.run_sweep(config, data=df)

# Ergebnisse als DataFrame
results_df = summary.to_dataframe()
print(results_df.sort_values("sharpe", ascending=False).head(5))
```

---

## Integration mit späteren Phasen

### Phase 22: Experiment- & Metrics-Explorer

Die Sweep-Ergebnisse werden in der Registry gespeichert und können mit dem zukünftigen Explorer visualisiert werden:

- Filterung nach `sweep_name`, `tag`, `strategy_key`
- Vergleich verschiedener Sweeps
- Parameter-Heatmaps
- Robustheit-Analysen

### Geplante Erweiterungen

- **Random Search**: Statt Grid-Search zufällige Kombinationen
- **Bayesian Optimization**: Intelligentere Parametersuche
- **Walk-Forward Analysis**: Automatische Train/Test-Splits
- **Multi-Symbol Sweeps**: Gleichzeitige Optimierung über mehrere Märkte

---

## Troubleshooting

### Problem: "Unbekannte Strategie"

**Lösung**: Prüfe verfügbare Strategien mit `--list-strategies`:

```bash
python3 scripts/run_sweep_strategy.py --list-strategies
```

### Problem: Zu viele Kombinationen

**Lösung**: Reduziere das Grid oder nutze `--max-runs`:

```bash
python3 scripts/run_sweep_strategy.py --strategy my_strategy \
    --grid config/sweeps/my_strategy.toml \
    --max-runs 20
```

### Problem: Validierungsfehler bei bestimmten Kombinationen

**Erklärung**: Manche Parameter-Kombinationen sind ungültig (z.B. `exit_threshold >= entry_threshold`). Diese werden automatisch übersprungen.

**Lösung**: Prüfe die Strategie-Dokumentation für gültige Parameterbereiche.

### Problem: Keine Ergebnisse in Registry

**Prüfen**: Wurde `--no-registry` verwendet?

```bash
# Mit Registry (Standard)
python3 scripts/run_sweep_strategy.py --strategy my_strategy --grid ...

# Ohne Registry (nur für Tests)
python3 scripts/run_sweep_strategy.py --strategy my_strategy --grid ... --no-registry
```

---

## Changelog

### Phase 20 (Initial Release)

- Neues Modul `src/sweeps/` mit SweepEngine
- CLI-Script `scripts/run_sweep_strategy.py`
- Vordefinierte Grids für trend_following, mean_reversion, my_strategy
- Volle Registry-Integration
- CSV-Export
- Dokumentation und Tests
