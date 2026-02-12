# Peak_Trade: Strategy-Sweeps & Market-Scans

Diese Dokumentation beschreibt die Parameter-Sweep- und Market-Scan-Funktionalität.

---

## Konzepte

### Strategy-Sweeps

Ein **Strategy-Sweep** testet systematisch verschiedene Parameter-Kombinationen einer Strategie.
Das Ziel ist, optimale Parameter zu finden, die historisch gut performt haben.

- **Parameter-Grid**: Definiert Wertebereiche für jeden Parameter
- **Kartesisches Produkt**: Alle Kombinationen werden getestet
- **Registry-Logging**: Jeder Run wird als `RUN_TYPE_SWEEP` gespeichert
- **Analyse**: Best-Params, Sharpe-Ranking, Return-Vergleich

### Market-Scans

Ein **Market-Scan** analysiert mehrere Symbole gleichzeitig mit einer Strategie.
Das Ziel ist, aktuelle Trading-Opportunities zu identifizieren.

- **Forward-Mode**: Echte Exchange-Daten, aktuelles Signal
- **Backtest-Lite-Mode**: Schneller Backtest mit Dummy-Daten
- **Registry-Logging**: Jeder Run wird als `RUN_TYPE_MARKET_SCAN` gespeichert
- **Analyse**: Signal-Aggregation, Top-Symbole, Trend-Übersicht

---

## CLI-Tools

### scripts/run_sweep.py

Führt Parameter-Sweeps für eine Strategie durch.

#### Argumente

| Argument | Beschreibung | Default |
|----------|--------------|---------|
| `--strategy` | Strategie-Key (erforderlich) | - |
| `--symbol` | Trading-Pair | `BTC&#47;EUR` |
| `--timeframe` | Timeframe | `1h` |
| `--grid` | Parameter-Grid (JSON&#47;TOML-Datei oder JSON-String) | erforderlich |
| `--max-runs` | Maximale Anzahl Runs (0 = unbegrenzt) | `0` |
| `--sweep-name` | Optionaler Name für den Sweep | auto |
| `--tag` | Optionaler Tag für Registry | - |
| `--config` | Pfad zur TOML-Config | `config/config.toml` |
| `--dry-run` | Nur Parameter anzeigen, keine Runs | False |

#### Beispiele

```bash
# Sweep mit JSON-Grid
python3 scripts/run_sweep.py \
    --config config/config.toml \
    --strategy ma_crossover \
    --symbol BTC/EUR \
    --grid '{"short_window": [5, 10, 20], "long_window": [50, 100]}'

# Sweep mit TOML-Datei
python3 scripts/run_sweep.py \
    --config config/config.toml \
    --strategy ma_crossover \
    --grid config/sweeps/ma_crossover.toml \
    --tag optimization-v1

# Limitierter Sweep (max 10 Kombinationen)
python3 scripts/run_sweep.py \
    --config config/config.toml \
    --strategy rsi_reversion \
    --grid config/sweeps/rsi_reversion.toml \
    --max-runs 10

# Dry-Run (nur Kombinationen anzeigen)
python3 scripts/run_sweep.py \
    --config config/config.toml \
    --strategy ma_crossover \
    --grid '{"short_window": [5, 10], "long_window": [50, 100]}' \
    --dry-run
```

#### Grid-Dateiformate

**TOML-Format** (`config/sweeps/ma_crossover.toml`):
```toml
[grid]
short_window = [5, 10, 20, 30]
long_window = [50, 100, 150, 200]
```

**JSON-Format** (`config&#47;sweeps&#47;ma_crossover.json`, illustrative):
```json
{
  "short_window": [5, 10, 20, 30],
  "long_window": [50, 100, 150, 200]
}
```

**Inline-JSON**:
```bash
--grid '{"short_window": [5, 10], "long_window": [50, 100]}'
```

---

### scripts/run_market_scan.py

Scannt mehrere Symbole mit einer Strategie.

#### Argumente

| Argument | Beschreibung | Default |
|----------|--------------|---------|
| `--strategy` | Strategie-Key (erforderlich) | - |
| `--symbols` | Komma-separierte Symbol-Liste (erforderlich) | - |
| `--timeframe` | Timeframe | `1h` |
| `--bars` | Anzahl Bars für Daten | `200` |
| `--mode` | Scan-Modus: `forward` oder `backtest-lite` | `forward` |
| `--scan-name` | Optionaler Name für den Scan | auto |
| `--tag` | Optionaler Tag für Registry | - |
| `--config` | Pfad zur TOML-Config | `config/config.toml` |
| `--dry-run` | Nur Symbole anzeigen, keine Runs | False |

#### Beispiele

```bash
# Forward-Scan (echte Exchange-Daten)
python3 scripts/run_market_scan.py \
    --config config/config.toml \
    --strategy ma_crossover \
    --symbols "BTC/EUR,ETH/EUR,LTC/EUR,XRP/EUR" \
    --mode forward \
    --tag morning-scan

# Backtest-Lite-Scan (schnell, Dummy-Daten)
python3 scripts/run_market_scan.py \
    --config config/config.toml \
    --strategy rsi_reversion \
    --symbols "BTC/EUR,ETH/EUR,SOL/EUR" \
    --mode backtest-lite \
    --timeframe 4h

# Dry-Run
python3 scripts/run_market_scan.py \
    --config config/config.toml \
    --strategy ma_crossover \
    --symbols "BTC/EUR,ETH/EUR" \
    --dry-run
```

---

## Registry-Logging

### log_sweep_run()

Loggt einen einzelnen Sweep-Run in die Experiments-Registry.

```python
from src.core.experiments import log_sweep_run

run_id = log_sweep_run(
    strategy_key="ma_crossover",
    symbol="BTC/EUR",
    timeframe="1h",
    params={"short_window": 10, "long_window": 50},
    stats={"total_return": 0.15, "sharpe": 1.2, "max_drawdown": -0.08},
    sweep_name="ma_optimization",
    tag="v1",
)
```

**Gespeicherte Felder:**
- `run_type`: `sweep`
- `strategy_key`: Strategie-Name
- `symbol`, `timeframe`: Trading-Kontext
- `params_json`: Parameter als JSON
- `stats_json`: Backtest-Statistiken als JSON
- `metadata_json`: sweep_name, backtest_run_id, etc.

### log_market_scan_result()

Loggt ein Market-Scan-Ergebnis in die Experiments-Registry.

```python
from src.core.experiments import log_market_scan_result

# Forward-Mode (Signal)
run_id = log_market_scan_result(
    strategy_key="ma_crossover",
    symbol="BTC/EUR",
    timeframe="1h",
    mode="forward",
    signal=1.0,  # +1 = LONG, -1 = SHORT, 0 = FLAT
    scan_name="morning_scan",
    tag="daily",
)

# Backtest-Lite-Mode (Stats)
run_id = log_market_scan_result(
    strategy_key="rsi_reversion",
    symbol="ETH/EUR",
    timeframe="4h",
    mode="backtest-lite",
    stats={"total_return": 0.08, "sharpe": 0.9},
    scan_name="weekly_scan",
)
```

**Gespeicherte Felder:**
- `run_type`: `market_scan`
- `strategy_key`: Strategie-Name
- `symbol`, `timeframe`: Trading-Kontext
- `stats_json`: Signal (forward) oder Backtest-Stats
- `metadata_json`: mode, scan_name, bars_fetched, etc.

---

## Analytics-Layer

### Filter-Funktionen

```python
import pandas as pd
from src.analytics.experiments_analysis import (
    load_experiments,
    filter_sweeps,
    filter_market_scans,
)

# Alle Experiments laden
df = load_experiments()

# Nur Sweeps filtern
sweeps_df = filter_sweeps(df)

# Nur Market-Scans filtern
scans_df = filter_market_scans(df)
```

### Sweep-Zusammenfassung

```python
from src.analytics.experiments_analysis import summarize_sweeps, SweepSummary

summaries = summarize_sweeps(sweeps_df)

for s in summaries:
    print(f"Sweep: {s.sweep_name}")
    print(f"  Runs: {s.run_count}")
    print(f"  Best Sharpe: {s.best_sharpe:.2f}")
    print(f"  Best Return: {s.best_return:.1%}")
    print(f"  Best Params: {s.best_params}")
```

**SweepSummary Felder:**
| Feld | Beschreibung |
|------|--------------|
| `sweep_name` | Name des Sweeps |
| `strategy_key` | Strategie |
| `run_count` | Anzahl Kombinationen |
| `best_sharpe` | Höchster Sharpe-Ratio |
| `best_return` | Höchster Total-Return |
| `best_params` | Beste Parameter |
| `best_run_id` | Run-ID des besten Runs |

### Market-Scan-Zusammenfassung

```python
from src.analytics.experiments_analysis import summarize_market_scans, MarketScanSummary

summaries = summarize_market_scans(scans_df)

for s in summaries:
    print(f"Scan: {s.scan_name}")
    print(f"  Symbole gescannt: {s.run_count}")
    print(f"  LONG-Signale: {s.long_signals}")
    print(f"  SHORT-Signale: {s.short_signals}")
    print(f"  FLAT-Signale: {s.flat_signals}")
    print(f"  Top-Symbol: {s.top_symbol} ({s.top_signal:+.1f})")
```

**MarketScanSummary Felder:**
| Feld | Beschreibung |
|------|--------------|
| `scan_name` | Name des Scans |
| `strategy_key` | Strategie |
| `run_count` | Anzahl gescannter Symbole |
| `long_signals` | Anzahl LONG-Signale |
| `short_signals` | Anzahl SHORT-Signale |
| `flat_signals` | Anzahl FLAT-Signale |
| `top_symbol` | Symbol mit stärkstem Signal |
| `top_signal` | Stärkstes Signal |

---

## Kombination mit analyze_experiments.py

```bash
# Alle Sweep-Runs auflisten
python3 scripts/analyze_experiments.py --run-type sweep

# Alle Market-Scans auflisten
python3 scripts/analyze_experiments.py --run-type market_scan

# Sweeps für eine Strategie filtern
python3 scripts/analyze_experiments.py --run-type sweep --strategy ma_crossover

# Scans mit Tag filtern
python3 scripts/analyze_experiments.py --run-type market_scan --tag morning-scan
```

---

## Typische Workflows

### Workflow 1: Parameter-Optimierung

```bash
# 1. Sweep durchführen
python3 scripts/run_sweep.py \
    --strategy ma_crossover \
    --symbol BTC/EUR \
    --grid config/sweeps/ma_crossover.toml \
    --tag optimization-v1

# 2. Ergebnisse analysieren
python3 scripts/analyze_experiments.py \
    --run-type sweep \
    --tag optimization-v1

# 3. Beste Parameter für Backtest verwenden
python3 scripts/run_backtest.py \
    --strategy ma_crossover \
    --symbol BTC/EUR \
    --params '{"short_window": 10, "long_window": 100}'
```

### Workflow 2: Morning-Scan

```bash
# 1. Alle Symbole scannen
python3 scripts/run_market_scan.py \
    --strategy ma_crossover \
    --symbols "BTC/EUR,ETH/EUR,LTC/EUR,XRP/EUR,SOL/EUR" \
    --mode forward \
    --tag morning-scan

# 2. Signale analysieren
python3 scripts/analyze_experiments.py \
    --run-type market_scan \
    --tag morning-scan

# 3. Bei starkem Signal: Order-Preview
python3 scripts/preview_live_orders.py \
    --signals reports/forward/... \
    --notional 500
```

### Workflow 3: Multi-Strategie-Scan

```bash
# Mehrere Strategien scannen
for strategy in ma_crossover rsi_reversion breakout_donchian; do
    python3 scripts/run_market_scan.py \
        --strategy $strategy \
        --symbols "BTC/EUR,ETH/EUR" \
        --mode forward \
        --tag multi-scan
done

# Aggregierte Analyse
python3 scripts/analyze_experiments.py \
    --run-type market_scan \
    --tag multi-scan
```

---

## Grid-Beispiele

### MA-Crossover Grid

```toml
# config/sweeps/ma_crossover.toml
[grid]
short_window = [5, 10, 20, 30]
long_window = [50, 100, 150, 200]
```
→ 16 Kombinationen

### RSI-Reversion Grid

```toml
# config/sweeps/rsi_reversion.toml
[grid]
rsi_period = [7, 14, 21]
entry_threshold = [20, 25, 30, 35]
exit_threshold = [45, 50, 55]
```
→ 36 Kombinationen

### Bollinger-Breakout Grid

```toml
# config/sweeps/bollinger_breakout.toml
[grid]
window = [10, 20, 30]
num_std = [1.5, 2.0, 2.5, 3.0]
```
→ 12 Kombinationen

---

## Troubleshooting

### "Strategie nicht gefunden"

```bash
# Verfügbare Strategien auflisten
python3 -c "from src.strategies.registry import list_strategies; print(list_strategies())"
```

### "Grid konnte nicht geladen werden"

- Prüfe Dateiformat (.toml oder .json)
- Bei JSON: Gültige Syntax mit doppelten Anführungszeichen
- Bei TOML: Listen in eckigen Klammern `[1, 2, 3]`

### "Zu viele Kombinationen"

Verwende `--max-runs` um die Anzahl zu begrenzen:
```bash
python3 scripts/run_sweep.py ... --max-runs 20
```

### "Exchange-Fehler im Forward-Mode"

- Prüfe API-Keys in `config/config.toml`
- Verwende `--mode backtest-lite` für Tests ohne Exchange

---

## Siehe auch

- [LIVE_WORKFLOWS.md](LIVE_WORKFLOWS.md) - Order-Preview, Paper-Trading
- [NOTIFICATIONS.md](NOTIFICATIONS.md) - Alert-Integration
- [STRATEGY_DEV_GUIDE.md](STRATEGY_DEV_GUIDE.md) - Eigene Strategien entwickeln
