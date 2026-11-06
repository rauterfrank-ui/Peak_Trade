# Phase 24: Shadow-/Dry-Run-Execution

## Einführung

### Was ist Shadow-/Dry-Run-Execution?

Shadow-Execution (auch "Dry-Run" genannt) ist ein Modus, der die **bestehende Execution-Pipeline** nutzt, aber **keine echten API-Calls** an Exchanges macht. Orders werden nur simuliert und geloggt.

Dies ermöglicht:
- **Quasi-realistische Ausführungssimulation** mit Fee- und Slippage-Modellierung
- **Shadow-Live**: Strategien können "so tun, als ob" sie live traden
- **Dry-Run vor echtem Testnet/Live**: Letzte Validierung vor dem Echtbetrieb

### Abgrenzung zu anderen Modi

| Modus | Beschreibung | API-Calls | Phase |
|-------|--------------|-----------|-------|
| **Paper** | Klassischer Backtest mit `PaperOrderExecutor` | Keine | 15+ |
| **Shadow** | Execution-Pipeline mit `ShadowOrderExecutor` | Keine | 24 |
| **Testnet Dry-Run** | Testnet-Simulation ohne echte Orders | Keine | 17 |
| **Testnet Real** | Echte Testnet-Orders | Ja (Testnet) | Zukünftig |
| **Live** | Echte Production-Orders | Ja (Live) | Nicht implementiert |

### WICHTIG: Safety

**Shadow-Execution ist zu 100% simulativ!**

- Keine echten API-Calls an Exchanges
- Keine API-Keys erforderlich
- Keine Verbindung zu Broker/Exchange
- Alle "Orders" bleiben im System (Registry, Logs)

Die Safety-Layer (`SafetyGuard`, `LiveRiskLimits`) bleiben unverändert und blockieren weiterhin echte Orders.

---

## Architektur

### ShadowOrderExecutor

```
src/orders/shadow.py
├── ShadowMarketContext     # Marktkontext (Preise, Fees, Slippage)
├── ShadowOrderLog          # Log-Eintrag für Shadow-Orders
└── ShadowOrderExecutor     # Hauptklasse für Shadow-Execution
```

Der `ShadowOrderExecutor`:
- Implementiert das `OrderExecutor`-Protocol
- Simuliert Market- und Limit-Orders
- Berechnet Fees und Slippage
- Führt ein detailliertes Order-Log

### Integration in ExecutionPipeline

```python
from src.execution.pipeline import ExecutionPipeline

# Einfachste Verwendung
pipeline = ExecutionPipeline.for_shadow()

# Mit benutzerdefinierten Parametern
pipeline = ExecutionPipeline.for_shadow(
    fee_rate=0.001,      # 10 bps
    slippage_bps=5.0,    # 5 bps
)

# Mit explizitem Context
from src.orders.shadow import ShadowMarketContext

ctx = ShadowMarketContext(
    prices={"BTC/EUR": 50000.0},
    fee_rate=0.0005,
)
pipeline = ExecutionPipeline.for_shadow(market_context=ctx)
```

### RunType in Registry

Shadow-Runs werden in der Experiments-Registry mit `run_type="shadow_run"` geloggt:

```python
from src.core.experiments import log_shadow_run

run_id = log_shadow_run(
    strategy_key="ma_crossover",
    symbol="BTC/EUR",
    timeframe="1h",
    stats={"total_return": 0.08, "sharpe": 1.1},
    execution_summary={
        "total_orders": 42,
        "filled_orders": 40,
        "total_notional": 125000.0,
    },
    tag="shadow_test_v1",
)
```

---

## Quickstart

### 1. CLI-Aufruf

```bash
# Einfachster Aufruf (defaults aus config/config.toml)
python3 scripts/run_shadow_execution.py

# Mit Strategie und Tag
python3 scripts/run_shadow_execution.py --strategy ma_crossover --tag shadow_test_v1

# Mit CSV-Daten und Datumsbeschränkung
python3 scripts/run_shadow_execution.py \
    --strategy rsi_strategy \
    --data-file data/btc_eur_1h.csv \
    --start 2023-01-01 \
    --end 2023-12-31

# Mit Fee- und Slippage-Überschreibung
python3 scripts/run_shadow_execution.py \
    --fee-rate 0.001 \
    --slippage-bps 10 \
    --verbose
```

### 2. Output-Beispiel

```
======================================================================
  Peak_Trade Shadow-/Dry-Run-Execution (Phase 24)
  WICHTIG: KEINE echten Orders werden gesendet!
======================================================================

[1/5] Config laden...
[2/5] Strategie bestimmen...
[3/5] Daten laden...
  500 Bars geladen
  Zeitraum: 2024-01-01 - 2024-01-21
[4/5] Shadow-Execution ausführen...
[5/5] Ergebnis ausgeben...

======================================================================
SHADOW-RUN ABGESCHLOSSEN
======================================================================

Zeitraum:   2024-01-01 bis 2024-01-21
Strategie:  ma_crossover
Symbol:     BTC/EUR
Bars:       500
Modus:      SHADOW (keine echten Orders)

--- PERFORMANCE ---
  Total Return:         8.25%
  Max Drawdown:        -3.12%
  Sharpe Ratio:         1.42
  CAGR:               142.50%

--- EXECUTION (SHADOW) ---
  Total Orders:           42
  Filled Orders:          40
  Rejected Orders:         2
  Fill Rate:           95.24%
  Total Notional:   125,432.00
  Total Fees:            62.72

--- SHADOW-PARAMETER ---
  Fee Rate:             5.0 bps
  Slippage:             0.0 bps

======================================================================

Registry-Run-ID: a1b2c3d4-e5f6-7890-abcd-ef1234567890
Run-Type: shadow_run
Tag: shadow_test_v1

HINWEIS: Dies war ein SHADOW-RUN. Keine echten Orders wurden gesendet.
```

### 3. Programmatische Verwendung

```python
from src.execution.pipeline import ExecutionPipeline
from src.orders.base import OrderRequest
import pandas as pd

# Pipeline erstellen
pipeline = ExecutionPipeline.for_shadow(
    fee_rate=0.0005,   # 5 bps
    slippage_bps=5.0,  # 5 bps
)

# Preise setzen (z.B. aus DataFrame)
pipeline.executor.set_price("BTC/EUR", 50000.0)

# Einzelne Order ausführen
order = OrderRequest(
    symbol="BTC/EUR",
    side="buy",
    quantity=0.1,
)
result = pipeline.execute_orders([order])[0]

print(f"Status: {result.status}")  # "filled"
print(f"Mode: {result.metadata['mode']}")  # "shadow_run"

# Oder: Execution aus Signalen
signals = pd.Series([0, 1, 1, 0, -1, 0])
prices = pd.Series([50000, 50100, 50200, 50150, 50000, 49900])

results = pipeline.execute_from_signals(
    signals=signals,
    prices=prices,
    symbol="BTC/EUR",
)

# Execution-Summary
summary = pipeline.executor.get_execution_summary()
print(f"Total Orders: {summary['total_orders']}")
print(f"Total Notional: {summary['total_notional']:.2f}")
```

---

## Konfiguration

### config/config.toml

```toml
[shadow]
enabled = true
run_type = "shadow_run"
fee_rate = 0.0005              # 5 bps = 0.05%
slippage_bps = 0.0             # 0 bps (konservativ)
base_currency = "EUR"
log_all_orders = true
```

### Parameter

| Parameter | Typ | Default | Beschreibung |
|-----------|-----|---------|--------------|
| `enabled` | bool | `true` | Shadow-Modus aktiviert |
| `run_type` | str | `"shadow_run"` | Registry run_type |
| `fee_rate` | float | `0.0005` | Fee als Dezimalzahl (5 bps) |
| `slippage_bps` | float | `0.0` | Slippage in Basispunkten |
| `base_currency` | str | `"EUR"` | Währung für Fees |
| `log_all_orders` | bool | `true` | Alle Orders loggen |

---

## Limitierungen

1. **Keine echten API-Calls**: Shadow-Execution macht niemals echte Calls an Exchanges.

2. **Vereinfachte Fill-Simulation**:
   - Market-Orders werden sofort zum aktuellen Preis gefüllt (+ Slippage)
   - Limit-Orders werden gefüllt wenn `market_price` die Bedingung erfüllt
   - Keine Partial Fills (alles-oder-nichts)
   - Keine Order-Book-Simulation

3. **Kein Order-Book / Liquidität**:
   - Orders werden immer gefüllt (wenn Preis bekannt)
   - Keine Simulation von Liquiditätsengpässen
   - Keine Market-Impact-Modellierung

4. **Kein Ersatz für echtes Testnet/Live**:
   - Shadow-Runs sind eine Vorstufe, kein Ersatz
   - Vor echtem Live-Trading sollte immer ein echter Testnet-Test erfolgen

---

## Kombination mit anderen Phasen

### Phase 19: Regime-Analyse

Shadow-Runs können mit der Regime-Analyse kombiniert werden:

```python
from src.core.regime import SimpleRegimeDetector

# Regime erkennen
detector = SimpleRegimeDetector()
regime = detector.detect(df)

# Shadow-Run mit Regime-Info
run_id = log_shadow_run(
    strategy_key="ma_crossover",
    symbol="BTC/EUR",
    timeframe="1h",
    stats=stats,
    extra_metadata={"regime": regime},
)
```

### Phase 20: Sweeps

Shadow-Runs können für schnelle Parameter-Tests verwendet werden:

```python
# Sweep mit Shadow-Execution statt normalem Backtest
for params in parameter_grid:
    result = run_shadow_execution(strategy, params)
    log_sweep_run(..., extra_metadata={"mode": "shadow"})
```

### Phase 21: Reporting v2

Shadow-Runs sind kompatibel mit dem HTML-Reporting:

```python
from src.reporting.html_reports import HtmlReportBuilder

builder = HtmlReportBuilder()
# ... Report aus Shadow-Run-Ergebnissen bauen
```

### Phase 22: Experiment Explorer

Shadow-Runs erscheinen im Explorer mit `run_type="shadow_run"`:

```python
from src.core.experiments import list_experiments

shadow_runs = list_experiments(run_type="shadow_run", limit=10)
```

---

## FAQ

### Wann Shadow-Execution verwenden?

1. **Vor Testnet/Live**: Als letzter Validierungsschritt
2. **Shadow-Live**: Strategie parallel zum Markt simulieren
3. **Schnelle Tests**: Fee-/Slippage-Auswirkungen testen

### Unterschied zu Paper-Backtest?

| Aspekt | Paper-Backtest | Shadow-Execution |
|--------|----------------|------------------|
| **Executor** | `PaperOrderExecutor` | `ShadowOrderExecutor` |
| **Pipeline** | Optional | Immer `ExecutionPipeline` |
| **Order-Log** | In Engine | In Executor + Registry |
| **Fokus** | Backtest-Stats | Execution-Simulation |

### Kann ich Shadow-Mode mit echtem Live kombinieren?

Nein. Shadow-Mode ist zu 100% simulativ. Der `LiveOrderExecutor` ist weiterhin ein Stub und blockiert alle echten Orders.

---

## Dateien

### Neue Dateien (Phase 24)

| Datei | Beschreibung |
|-------|--------------|
| `src/orders/shadow.py` | ShadowOrderExecutor, ShadowMarketContext |
| `scripts/run_shadow_execution.py` | CLI-Script für Shadow-Runs |
| `tests/test_shadow_execution.py` | 33 Unit-/Integrationstests |
| `docs/PHASE_24_SHADOW_EXECUTION.md` | Diese Dokumentation |

### Geänderte Dateien

| Datei | Änderung |
|-------|----------|
| `src/orders/__init__.py` | Export von Shadow-Klassen |
| `src/execution/pipeline.py` | Factory-Methode `for_shadow()` |
| `src/core/experiments.py` | `RUN_TYPE_SHADOW_RUN`, `log_shadow_run()` |
| `config/config.toml` | `[shadow]`-Sektion |
