# Registry-Backtest Integration

**Quick-Start für die neuen Registry-basierten Backtest-Entry-Points**

---

## Was ist neu?

Statt Strategie-Funktionen manuell zu importieren und Parameter hardcoded zu übergeben, kannst du jetzt **Config-basierte Backtests** durchführen:

```python
# ❌ Alt (funktioniert weiterhin)
from src.backtest.engine import BacktestEngine
from src.strategies.ma_crossover import generate_signals

engine = BacktestEngine()
result = engine.run_realistic(
    df=df,
    strategy_signal_fn=generate_signals,
    strategy_params={"fast_period": 10, "slow_period": 30, "stop_pct": 0.02}
)

# ✅ Neu (empfohlen)
from src.backtest.engine import run_single_strategy_from_registry

result = run_single_strategy_from_registry(
    df=df,
    strategy_name="ma_crossover",
    custom_params={"fast_period": 20}  # nur Overrides nötig
)
```

**Vorteile:**
- ✅ Defaults aus Config werden automatisch gemerged
- ✅ Kein manueller Import der Strategie-Funktion
- ✅ Portfolio-Support out-of-the-box
- ✅ Konsistent mit Registry-Konzept

---

## Quick Examples

### Single-Strategy-Backtest

```python
from src.backtest.engine import run_single_strategy_from_registry

result = run_single_strategy_from_registry(
    df=df,
    strategy_name="ma_crossover",
)

print(f"Return: {result.stats['total_return']:.2%}")
print(f"Sharpe: {result.stats['sharpe']:.2f}")
```

### Portfolio-Backtest (Alle aktiven Strategien)

```python
from src.backtest.engine import run_portfolio_from_config

result = run_portfolio_from_config(df=df)

print(f"Portfolio Return: {result.portfolio_stats['total_return']:.2%}")
print(f"Strategien: {list(result.strategy_results.keys())}")
```

### Portfolio-Backtest (Nur Trending-Strategien)

```python
result = run_portfolio_from_config(
    df=df,
    regime_filter="trending",
)
```

---

## Demo ausführen

```bash
cd ~/Peak_Trade
source .venv/bin/activate
python3 scripts/demo_registry_backtest.py
```

---

## Dokumentation

📚 **Ausführliche API-Referenz:**  
`docs/REGISTRY_BACKTEST_API.md`

🔧 **Implementierungs-Details:**  
`docs/REGISTRY_BACKTEST_IMPLEMENTATION.md`

📖 **Config-Registry-Basics:**  
`docs/CONFIG_REGISTRY_USAGE.md`

---

## Config-Struktur

Die Strategie-Config befindet sich in `config/config.toml`:

```toml
# Aktive Strategien (für Portfolio)
[strategies]
active = ["ma_crossover", "momentum_1h", "rsi_strategy"]

# Default-Parameter für ALLE Strategien
[strategies.defaults]
stop_pct = 0.02
position_fraction = 0.25
min_hold_bars = 3

# Strategie-spezifische Parameter
[strategy.ma_crossover]
fast_period = 10
slow_period = 30
stop_pct = 0.02  # überschreibt defaults

# Portfolio-Config
[portfolio]
enabled = true
max_strategies_active = 3
allocation_method = "equal"  # "equal", "manual", "risk_parity", "sharpe_weighted"
```

---

## Features

✅ **Implementiert:**
- Single-Strategy-Backtest aus Registry
- Portfolio-Backtest mit mehreren Strategien
- Regime-basiertes Filtering (`regime_filter="trending"`)
- Capital-Allocation: Equal, Manual
- Risk-Layer-Integration (PositionSizer, RiskLimits)

🚧 **TODO:**
- Risk-Parity Allocation
- Sharpe-Weighted Allocation
- Dynamic Rebalancing
- Unit-Tests

---

## Nächste Schritte

1. **Demo testen:**
   ```bash
   python3 scripts/demo_registry_backtest.py
   ```

2. **API-Dokumentation lesen:**  
   `docs/REGISTRY_BACKTEST_API.md`

3. **Eigene Strategien hinzufügen:**
   - Modul in `src/strategies/` erstellen
   - `generate_signals()` implementieren
   - Registry-Eintrag in `__init__.py`
   - Config-Block in `config.toml`

4. **Portfolio testen:**
   - `strategies.active` in Config anpassen
   - `run_portfolio_from_config()` aufrufen

---

**Stand:** Dezember 2024  
**Status:** ✅ Implementiert & Getestet
