# Peak_Trade: Order-Pipeline Integration (Phase 16)

Dokumentation der Execution-Pipeline-Integration in die Backtest-Engine.

---

## Uebersicht

Die Execution-Pipeline (Phase 16) erweitert das Peak_Trade Framework um eine einheitliche
Schnittstelle fuer Signal-to-Order-Transformation und Order-Ausfuehrung im Backtest.

**Workflow:**

```
Strategie → Signale → ExecutionPipeline → OrderExecutor → Fills → PnL-Berechnung
```

**WICHTIG:** Es werden KEINE echten Orders an Boersen gesendet. Die gesamte Pipeline
arbeitet auf Paper-/Sandbox-Level mit simulierten Fills.

---

## Architektur

### Neue Module

```
src/execution/
├── __init__.py              # Package-Exports
└── pipeline.py              # ExecutionPipeline, SignalEvent, Config
```

### Komponenten

| Komponente                | Beschreibung                                              |
|---------------------------|-----------------------------------------------------------|
| `ExecutionPipeline`       | Haupt-Klasse fuer Signal-to-Order-Transformation          |
| `ExecutionPipelineConfig` | Konfiguration (TimeInForce, OrderType, etc.)              |
| `SignalEvent`             | Dataclass fuer Signal-Wechsel-Erkennung                   |

### Integration mit Order-Layer (Phase 15)

Die Execution-Pipeline nutzt den in Phase 15 erstellten Order-Layer:

```
src/orders/
├── base.py     # OrderRequest, OrderFill, OrderExecutionResult
├── paper.py    # PaperOrderExecutor, PaperMarketContext
└── mappers.py  # Konvertierungs-Helfer
```

---

## Verwendung

### 1. Standalone ExecutionPipeline

```python
from src.execution import ExecutionPipeline, SignalEvent
from src.orders import PaperMarketContext, OrderRequest

# Marktkontext erstellen
ctx = PaperMarketContext(
    prices={"BTC/EUR": 50000.0},
    fee_bps=10.0,
    slippage_bps=5.0,
)

# Pipeline erstellen
pipeline = ExecutionPipeline.for_paper(ctx)

# Einzelne Order ausfuehren
order = OrderRequest(
    symbol="BTC/EUR",
    side="buy",
    quantity=0.01,
)
result = pipeline.execute_order(order)

print(f"Status: {result.status}")
if result.fill:
    print(f"Fill: {result.fill.quantity} @ {result.fill.price}")
```

### 2. Signal-to-Order-Transformation

```python
from datetime import datetime
from src.execution import ExecutionPipeline, SignalEvent
from src.orders import PaperMarketContext

ctx = PaperMarketContext(prices={"BTC/EUR": 50000.0}, fee_bps=10.0)
pipeline = ExecutionPipeline.for_paper(ctx)

# SignalEvent erstellen
event = SignalEvent(
    timestamp=datetime.now(),
    symbol="BTC/EUR",
    signal=1,            # Long-Signal
    price=50000.0,
    previous_signal=0,   # Vorher flat
)

# Orders generieren
orders = pipeline.signal_to_orders(
    event=event,
    position_size=0.01,
    current_position=0.0,
)

# Orders ausfuehren
results = pipeline.execute_orders(orders)
```

### 3. Execute from Signal-Serie

```python
import pandas as pd
from src.execution import ExecutionPipeline
from src.orders import PaperMarketContext

# Signal- und Preis-Serien erstellen
dates = pd.date_range(start="2024-01-01", periods=100, freq="h")
signals = pd.Series([...], index=dates)  # -1/0/+1
prices = pd.Series([...], index=dates)   # Close-Preise

ctx = PaperMarketContext(
    prices={"BTC/EUR": prices.iloc[-1]},
    fee_bps=10.0,
)

pipeline = ExecutionPipeline.for_paper(ctx)

# Signale durchlaufen und Orders ausfuehren
results = pipeline.execute_from_signals(
    signals=signals,
    prices=prices,
    symbol="BTC/EUR",
    base_position_size=0.01,
)

# Zusammenfassung
summary = pipeline.get_execution_summary()
print(f"Total Orders: {summary['total_orders']}")
print(f"Filled: {summary['filled_orders']}")
print(f"Total Fees: {summary['total_fees']}")
```

### 4. BacktestEngine mit Order-Layer

```python
import pandas as pd
from src.backtest.engine import BacktestEngine
from src.strategies import load_strategy

# OHLCV-Daten laden (Beispiel)
df = pd.read_csv("data/btc_eur_1h.csv", index_col=0, parse_dates=True)

# Strategie laden
strategy_fn = load_strategy("ma_crossover")

# BacktestEngine mit Order-Layer
engine = BacktestEngine(use_order_layer=True)

result = engine.run_with_order_layer(
    df=df,
    strategy_signal_fn=strategy_fn,
    strategy_params={"fast_period": 10, "slow_period": 30},
    symbol="BTC/EUR",
    fee_bps=10.0,
    slippage_bps=5.0,
)

# Ergebnisse
print(f"Total Return: {result.stats['total_return']:.2%}")
print(f"Total Trades: {result.stats['total_trades']}")
print(f"Total Fees: {result.stats['total_fees']:.2f}")

# Execution-Results abrufen
for exec_result in engine.execution_results[:5]:
    if exec_result.fill:
        print(f"{exec_result.fill.side} {exec_result.fill.quantity} @ {exec_result.fill.price}")
```

---

## Demo-Scripts

### Phase 16C: demo_execution_backtest.py (Empfohlen)

Das neue Demo-Script demonstriert die vollstaendige Phase 16B Integration
mit `use_execution_pipeline` und `log_executions`:

```bash
# ExecutionPipeline-Modus (Default)
python3 -m scripts.demo_execution_backtest

# Mit Parametern
python3 -m scripts.demo_execution_backtest \
    --symbol BTC/EUR \
    --start 2024-01-01 \
    --end 2024-02-01 \
    --strategy ma_crossover \
    --fee-bps 10 \
    --slippage-bps 5

# Legacy-Modus (ohne ExecutionPipeline)
python3 -m scripts.demo_execution_backtest --use-legacy

# Vergleichsmodus: ExecutionPipeline vs. Legacy nebeneinander
python3 -m scripts.demo_execution_backtest --compare

# Ausfuehrliche Ausgabe mit Sample-Trades
python3 -m scripts.demo_execution_backtest --verbose
```

#### CLI-Optionen

| Option              | Default       | Beschreibung                                    |
|---------------------|---------------|-------------------------------------------------|
| `--symbol`          | `BTC&#47;EUR`     | Trading-Symbol                                  |
| `--start`           | (none)        | Start-Datum (YYYY-MM-DD)                        |
| `--end`             | (none)        | End-Datum (YYYY-MM-DD)                          |
| `--bars`            | `200`         | Anzahl Bars (wenn --start nicht gesetzt)        |
| `--timeframe`       | `1h`          | Timeframe (1h, 4h, 1d)                          |
| `--strategy`        | `ma_crossover`| Strategie-Name                                  |
| `--fee-bps`         | `10.0`        | Fees in Basispunkten                            |
| `--slippage-bps`    | `5.0`         | Slippage in Basispunkten                        |
| `--use-legacy`      | `False`       | Legacy-Modus ohne ExecutionPipeline             |
| `--no-log-executions`| `False`      | Execution-Logging deaktivieren                  |
| `--compare`         | `False`       | Vergleiche ExecutionPipeline vs. Legacy         |
| `--verbose`         | `False`       | Ausfuehrliche Ausgabe mit Sample-Trades         |

#### Output-Beispiel

```
======================================================================
Peak_Trade Demo: ExecutionPipeline-Backtest (Phase 16C)
======================================================================

Symbol:     BTC/EUR
Mode:       execution_pipeline_backtest
Zeitraum:   2024-01-01 -> 2024-02-01
Strategy:   ma_crossover
Params:     {'fast_period': 10, 'slow_period': 30, 'stop_pct': 0.02}

----------------------------------------------------------------------
Daten: 200 Bars (1h)
Preis-Range: 48,500.00 - 55,200.00
Fees: 10.0 bps (0.10%)
Slippage: 5.0 bps (0.05%)

----------------------------------------------------------------------
BACKTEST wird ausgefuehrt...
----------------------------------------------------------------------

[Performance]
  Total Return:     +2.35%
  Max Drawdown:     1.87%
  Sharpe Ratio:     1.42
  Calmar Ratio:     1.26

[Trade-Statistiken]
  Total Trades:     12
  Win Rate:         58.3%
  Profit Factor:    1.85
  Blocked Trades:   0

[Execution-Details]
  Total Orders:     24
  Filled Orders:    24
  Rejected Orders:  0
  Total Fees:       45.32 EUR
  Total Slippage:   22.50 EUR

[Execution-Logs] (1 Eintraege)

  Log #1:
    run_id: abc123
    symbol: BTC/EUR
    total_orders: 24
    filled_orders: 24
    total_notional: 125000.0000
    total_fees: 45.3200

======================================================================
Demo abgeschlossen!
======================================================================

WICHTIG: Es wurden KEINE echten Orders gesendet (Paper/Sandbox)
```

#### Execution-Logs abrufen

Im Code koennen die Execution-Logs wie folgt abgerufen werden:

```python
from src.backtest.engine import BacktestEngine

engine = BacktestEngine(
    use_execution_pipeline=True,
    log_executions=True,
)

result = engine.run_realistic(
    df=df,
    strategy_signal_fn=strategy_fn,
    strategy_params=params,
    symbol="BTC/EUR",
    fee_bps=10.0,
    slippage_bps=5.0,
)

# Logs abrufen
logs = engine.get_execution_logs()
for log in logs:
    print(f"Run: {log['run_id']}")
    print(f"  Orders: {log['total_orders']}")
    print(f"  Filled: {log['filled_orders']}")
    print(f"  Fees:   {log['total_fees']:.2f}")

# Logs loeschen (z.B. zwischen Runs)
engine.clear_execution_logs()
```

### Legacy: demo_order_pipeline_backtest.py (Deprecated)

Das aeltere Demo-Script nutzt die deprecated `run_with_order_layer()` API:

```bash
# DEPRECATED - nutze stattdessen demo_execution_backtest.py
python3 scripts/demo_order_pipeline_backtest.py
python3 scripts/demo_order_pipeline_backtest.py --compare-legacy
```

**Hinweis:** Dieses Script funktioniert weiterhin, nutzt aber die veraltete
`use_order_layer` Flag und `run_with_order_layer()` Methode.

---

## SignalEvent Properties

Die `SignalEvent`-Klasse bietet Properties zur Signal-Wechsel-Erkennung:

| Property                  | Beschreibung                                    |
|---------------------------|-------------------------------------------------|
| `is_entry_long`           | True bei Long-Entry (0/-1 → +1)                 |
| `is_exit_long`            | True bei Long-Exit (+1 → 0/-1)                  |
| `is_entry_short`          | True bei Short-Entry (0/+1 → -1)                |
| `is_exit_short`           | True bei Short-Exit (-1 → 0/+1)                 |
| `is_flip_long_to_short`   | True bei Flip (+1 → -1)                         |
| `is_flip_short_to_long`   | True bei Flip (-1 → +1)                         |

### Signal-Wechsel-Beispiele

```
previous_signal → signal | Typ
-----------------------|-----------------------------
        0 → +1          | Entry Long
       +1 → 0           | Exit Long
        0 → -1          | Entry Short
       -1 → 0           | Exit Short
       +1 → -1          | Flip (Exit Long + Entry Short)
       -1 → +1          | Flip (Exit Short + Entry Long)
```

---

## ExecutionPipelineConfig

```python
from src.execution.pipeline import ExecutionPipelineConfig

config = ExecutionPipelineConfig(
    default_time_in_force="GTC",     # Good-Til-Cancelled
    allow_partial_fills=True,         # Teil-Fills erlauben
    default_order_type="market",      # Market-Orders
    generate_client_ids=True,         # Auto-Client-IDs
    log_executions=True,              # Logging aktivieren
)

pipeline = ExecutionPipeline.for_paper(ctx, config=config)
```

---

## Statistiken & Zusammenfassung

```python
summary = pipeline.get_execution_summary()

# Verfuegbare Keys:
{
    "total_orders": 24,
    "filled_orders": 24,
    "rejected_orders": 0,
    "fill_rate": 1.0,
    "total_notional": 12500.00,
    "total_fees": 45.32,
}
```

---

## Tests

```bash
# Smoke-Tests ausfuehren
python3 -m pytest tests/test_execution_pipeline_smoke.py -v

# Mit Coverage
python3 -m pytest tests/test_execution_pipeline_smoke.py -v --cov=src/execution
```

### Test-Abdeckung

| Testklasse                                  | Tests |
|---------------------------------------------|-------|
| `TestSignalEvent`                           | 8     |
| `TestExecutionPipelineConfig`               | 2     |
| `TestExecutionPipeline`                     | 8     |
| `TestExecutionPipelineExecuteFromSignals`   | 2     |
| `TestBacktestEngineOrderLayerIntegration`   | 4     |
| `TestDemoScript`                            | 3     |
| `TestEdgeCases`                             | 3     |
| **Total**                                   | **30** |

---

## BacktestEngine Integration (Phase 16B)

### Neue Flags

| Flag                     | Default | Beschreibung                                         |
|--------------------------|---------|------------------------------------------------------|
| `use_execution_pipeline` | `True`  | ExecutionPipeline fuer Backtests verwenden           |
| `log_executions`         | `False` | Execution-Summaries in `_execution_logs` speichern   |
| `use_order_layer`        | `None`  | **DEPRECATED** - Alias fuer `use_execution_pipeline` |

### Empfohlene Verwendung (Phase 16B)

```python
# ExecutionPipeline-Modus (Default seit Phase 16B)
engine = BacktestEngine(
    use_execution_pipeline=True,   # Default
    log_executions=True,           # Optional: Logging aktivieren
)

result = engine.run_realistic(
    df=df,
    strategy_signal_fn=strategy_fn,
    strategy_params=params,
    symbol="BTC/EUR",
    fee_bps=10.0,
    slippage_bps=5.0,
)

# Legacy-Modus (ohne ExecutionPipeline)
legacy_engine = BacktestEngine(use_execution_pipeline=False)
legacy_result = legacy_engine.run_realistic(df, strategy_fn, params)
```

### Deprecated: use_order_layer (Phase 16A)

```python
# DEPRECATED - funktioniert weiterhin, aber nicht empfohlen
engine = BacktestEngine(use_order_layer=True)
result = engine.run_with_order_layer(df, strategy_fn, params, symbol)
```

### Zusaetzliche Stats im Order-Layer-Modus

Im `result.stats` Dictionary sind zusaetzliche Keys verfuegbar:

| Key                | Beschreibung                      |
|--------------------|-----------------------------------|
| `total_orders`     | Anzahl generierter Orders         |
| `filled_orders`    | Anzahl gefuellter Orders          |
| `rejected_orders`  | Anzahl abgelehnter Orders         |
| `total_fees`       | Summe aller Fees in EUR           |

### Zugriff auf Execution-Results

```python
engine = BacktestEngine(use_order_layer=True)
result = engine.run_with_order_layer(...)

# Alle Execution-Results abrufen
for exec_result in engine.execution_results:
    if exec_result.is_filled and exec_result.fill:
        fill = exec_result.fill
        print(f"{fill.side} {fill.symbol} qty={fill.quantity} @ {fill.price}")
    elif exec_result.is_rejected:
        print(f"REJECTED: {exec_result.reason}")
```

---

## Vergleich: Order-Layer vs Legacy

| Feature                      | Order-Layer                  | Legacy                     |
|------------------------------|------------------------------|----------------------------|
| Signal → Order Tracking      | Ja (OrderRequest/Fill)       | Nein (implizit)            |
| Fee-Simulation               | Explizit in Fill             | Implizit in Return         |
| Slippage-Simulation          | Explizit in Fill             | Implizit in Return         |
| Order-Rejection              | Ja (rejected Orders)         | Nein                       |
| Execution-Historie           | Ja (execution_results)       | Nein                       |
| Partial Fills                | Vorbereitet                  | Nein                       |

---

## Wichtige Hinweise

1. **Keine echten Orders:** Die gesamte Pipeline arbeitet auf Paper-/Sandbox-Level.
   Es werden KEINE echten Orders an Boersen gesendet.

2. **Backward Compatibility:** Der Legacy-Modus (`use_order_layer=False`) bleibt
   unveraendert funktionsfaehig. Bestehende Backtests sind nicht betroffen.

3. **Position Tracking:** Die Pipeline trackt Positionen intern und generiert
   korrekte Exit-Orders bei Signal-Wechseln.

4. **Flip-Orders:** Bei einem Signal-Flip (z.B. Long → Short) werden automatisch
   zwei Orders generiert: Exit der alten Position + Entry der neuen Position.

---

## Siehe auch

- [EXECUTION_REPORTING.md](EXECUTION_REPORTING.md) - Phase 16D Execution-Reporting
- [ORDER_LAYER_SANDBOX.md](ORDER_LAYER_SANDBOX.md) - Phase 15 Order-Layer
- [BACKTEST_ENGINE.md](BACKTEST_ENGINE.md) - BacktestEngine Dokumentation
- [CLI_CHEATSHEET.md](CLI_CHEATSHEET.md) - CLI-Befehle Uebersicht
- [STRATEGY_DEV_GUIDE.md](STRATEGY_DEV_GUIDE.md) - Strategie-Entwicklung
