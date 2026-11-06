# Peak_Trade: Execution Reporting (Phase 16D)

Dokumentation des Execution-Reporting-Layers fuer Backtests mit der ExecutionPipeline.

---

## Uebersicht

Das Execution-Reporting-Modul (`src/reporting/`) bietet:

1. **ExecutionStats**: Aggregierte Kennzahlen fuer Order-/Execution-Daten
2. **Konvertierungs-Funktionen**: Erzeugung von Stats aus verschiedenen Quellen
3. **Visualisierungen**: Optionale Matplotlib-Plots fuer Execution-Daten

**WICHTIG:** Paper-only. Alle Daten stammen aus simulierten Backtests.

---

## Module

```
src/reporting/
├── __init__.py              # Package-Exports
├── execution_reports.py     # ExecutionStats, Konvertierungs-Funktionen
└── execution_plots.py       # Visualisierungen (optional)
```

---

## ExecutionStats

Zentrale Dataclass fuer aggregierte Execution-Statistiken.

### Attribute

| Kategorie | Attribut | Beschreibung |
|-----------|----------|--------------|
| **Orders** | `n_orders` | Gesamtzahl Orders |
| | `n_fills` | Anzahl ausgefuehrter Orders |
| | `n_rejected` | Anzahl abgelehnter Orders |
| | `fill_rate` | Anteil ausgefuehrter Orders (0.0 - 1.0) |
| **Fees** | `total_fees` | Summe aller Fees (EUR) |
| | `avg_fee_per_order` | Durchschnittliche Fee pro Order |
| | `avg_fee_per_fill` | Durchschnittliche Fee pro Fill |
| | `fee_rate_bps` | Durchschnittliche Fee-Rate in bps |
| **Volume** | `total_notional` | Gesamtes Handelsvolumen |
| | `avg_trade_notional` | Durchschnittliches Notional pro Trade |
| | `max_trade_notional` | Maximales Notional |
| | `min_trade_notional` | Minimales Notional |
| **Slippage** | `avg_slippage_bps` | Durchschnittliche Slippage in bps |
| | `max_slippage_bps` | Maximale Slippage in bps |
| | `total_slippage` | Gesamte Slippage (absolut, EUR) |
| **Buy/Sell** | `n_buys` | Anzahl Kauf-Orders |
| | `n_sells` | Anzahl Verkauf-Orders |
| | `buy_volume` | Kauf-Volumen |
| | `sell_volume` | Verkauf-Volumen |
| **Performance** | `hit_rate` | Anteil gewinnender Trades |
| | `n_winning_trades` | Anzahl gewinnender Trades |
| | `n_losing_trades` | Anzahl verlierender Trades |
| **Time** | `first_trade_time` | Zeitpunkt des ersten Trades |
| | `last_trade_time` | Zeitpunkt des letzten Trades |
| | `trading_period_days` | Handelsperiode in Tagen |

### Beispiel

```python
from src.reporting import ExecutionStats

stats = ExecutionStats(
    n_orders=100,
    n_fills=95,
    n_rejected=5,
    total_fees=50.0,
    total_notional=10000.0,
    symbol="BTC/EUR",
)

print(f"Fill-Rate: {stats.fill_rate:.1%}")
print(f"Fee-Rate:  {stats.fee_rate_bps:.2f} bps")
```

---

## Konvertierungs-Funktionen

### from_execution_logs()

Erzeugt ExecutionStats aus den Logs der BacktestEngine.

```python
from src.backtest.engine import BacktestEngine
from src.reporting import from_execution_logs

engine = BacktestEngine(use_execution_pipeline=True, log_executions=True)
result = engine.run_realistic(df, strategy_fn, params, symbol="BTC/EUR")

logs = engine.get_execution_logs()
stats = from_execution_logs(logs)

print(f"Orders: {stats.n_orders}")
print(f"Fills:  {stats.n_fills}")
print(f"Fees:   {stats.total_fees:.2f} EUR")
```

### from_execution_results()

Erzeugt ExecutionStats aus OrderExecutionResult-Liste (detaillierter).

```python
from src.reporting import from_execution_results

stats = from_execution_results(engine.execution_results)

print(f"Avg Slippage: {stats.avg_slippage_bps:.2f} bps")
print(f"Buy Volume:   {stats.buy_volume:,.2f} EUR")
print(f"Sell Volume:  {stats.sell_volume:,.2f} EUR")
```

### from_backtest_result()

Erzeugt ExecutionStats aus BacktestResult (kombiniert Stats und Execution-Results).

```python
from src.reporting import from_backtest_result

stats = from_backtest_result(result, engine.execution_results)

print(f"Hit-Rate:      {stats.hit_rate:.1%}")
print(f"Winning Trades: {stats.n_winning_trades}")
```

---

## Formatierung

### format_execution_stats()

Formatiert ExecutionStats als lesbaren String fuer Konsolen-Output.

```python
from src.reporting import format_execution_stats

output = format_execution_stats(stats, title="My Report")
print(output)
```

**Output:**

```
===== My Report =====

[Orders & Fills]
  Orders:              100
  Fills:                95
  Rejected:              5
  Fill-Rate:         95.0%

[Fees]
  Total Fees:          50.00 EUR
  Avg Fee/Order:        0.5000 EUR
  Avg Fee/Fill:         0.5263 EUR
  Fee-Rate:            50.00 bps

[Volume]
  Total Notional:   10000.00 EUR
  Avg Trade Size:     105.26 EUR

[Slippage]
  Avg Slippage:         5.00 bps
  Max Slippage:        12.00 bps
  Total Slippage:      25.00 EUR

[Buy/Sell Split]
  Buys:                  60 (6,000.00 EUR)
  Sells:                 35 (4,000.00 EUR)

[Performance]
  Hit-Rate:           52.0%
  Winning Trades:        26
  Losing Trades:         24

[Symbol: BTC/EUR]
[Run-ID: test_run]
```

---

## Visualisierungen (Optional)

Das Modul `execution_plots.py` bietet optionale Matplotlib-Plots.

### Verfuegbare Plots

| Funktion | Beschreibung |
|----------|--------------|
| `plot_slippage_histogram()` | Histogramm der Slippage-Verteilung |
| `plot_fee_histogram()` | Histogramm der Fee-Verteilung |
| `plot_notional_histogram()` | Histogramm der Trade-Groessen |
| `plot_equity_with_trades()` | Equity-Kurve mit Entry/Exit-Markierungen |
| `plot_buy_sell_breakdown()` | Buy/Sell-Aufschluesselung |
| `plot_execution_summary()` | Zusammenfassende Visualisierung |

### Beispiel

```python
from src.reporting.execution_plots import (
    check_matplotlib,
    plot_slippage_histogram,
    extract_slippages_from_results,
)
from pathlib import Path

if check_matplotlib():
    slippages = extract_slippages_from_results(engine.execution_results)

    plot_slippage_histogram(
        slippages,
        title="Slippage Distribution - BTC/EUR",
        output_path=Path("reports/slippage_hist.png"),
    )
```

---

## Demo-Script Integration

Das Demo-Script (`scripts/demo_execution_backtest.py`) unterstuetzt seit Phase 16D:

```bash
# Detaillierte ExecutionStats ausgeben
python3 -m scripts.demo_execution_backtest --stats

# Plots erstellen
python3 -m scripts.demo_execution_backtest --plot --output-dir reports

# Kombination
python3 -m scripts.demo_execution_backtest --stats --plot --verbose
```

### Neue CLI-Optionen

| Option | Beschreibung |
|--------|--------------|
| `--stats` | Detaillierte ExecutionStats ausgeben |
| `--plot` | Plots speichern (Equity, Slippage, etc.) |
| `--output-dir` | Output-Verzeichnis fuer Plots (default: reports) |

---

## Tests

```bash
# Execution-Reporting Tests ausfuehren
python3 -m pytest tests/test_execution_reporting.py -v

# Mit Coverage
python3 -m pytest tests/test_execution_reporting.py -v --cov=src/reporting
```

### Test-Abdeckung

| Testklasse | Tests |
|------------|-------|
| `TestExecutionStatsDataclass` | 7 |
| `TestFromExecutionLogs` | 5 |
| `TestFromExecutionResults` | 5 |
| `TestFromBacktestResult` | 2 |
| `TestFormatExecutionStats` | 4 |
| `TestExecutionPlotsModule` | 3 |
| `TestReportingModuleImports` | 3 |

---

## Slippage-Berechnung

Slippage wird in Basispunkten (bps) berechnet:

```
Bei Kauf:  slippage_bps = (fill_price - reference_price) / reference_price * 10_000
Bei Verkauf: slippage_bps = (reference_price - fill_price) / reference_price * 10_000
```

- Positiver Wert = schlechtere Ausfuehrung als Referenz
- Referenzpreis kann aus verschiedenen Quellen stammen:
  1. Explizit uebergebener `reference_prices` Dict
  2. `signal_price` aus Request-Metadata
  3. `reference_price` aus Result-Metadata

---

## Siehe auch

- [ORDER_PIPELINE_INTEGRATION.md](ORDER_PIPELINE_INTEGRATION.md) - ExecutionPipeline Integration
- [ORDER_LAYER_SANDBOX.md](ORDER_LAYER_SANDBOX.md) - Order-Layer Grundlagen
- [BACKTEST_ENGINE.md](BACKTEST_ENGINE.md) - BacktestEngine Dokumentation
