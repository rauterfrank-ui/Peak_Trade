# Registry-Backtest Integration – Implementierungs-Summary

**Datum:** Dezember 2024  
**Status:** ✅ Implementiert & Getestet  
**Branch:** (aktuelle Branch)

---

## Übersicht

Integration der **Strategien-Registry** in die **BacktestEngine**, um Config-basierte Backtests zu ermöglichen.

**Neue Features:**
1. `run_single_strategy_from_registry()` – Single-Strategy aus Config
2. `run_portfolio_from_config()` – Multi-Strategy-Portfolio
3. Regime-basiertes Filtering (`regime_filter="trending"`)
4. Flexible Capital-Allocation (equal/manual/risk_parity/sharpe_weighted)

---

## Geänderte/Neue Dateien

### 1. `src/backtest/engine.py` ⭐

**Änderungen:**
- Import von `get_config()` aus `config_registry` statt `core`
- Dict-Zugriff auf Config (`config["backtest"]["initial_cash"]`) statt Pydantic
- Neue Entry-Points hinzugefügt (am Ende der Datei)

**Neue Funktionen:**
- `run_single_strategy_from_registry()` – Registry-basierter Single-Backtest
- `run_portfolio_from_config()` – Portfolio-Backtest mit mehreren Strategien

**Neue Klassen:**
- `PortfolioResult` – Return-Typ für Portfolio-Backtests

**Helper-Funktionen:**
- `_calculate_allocation()` – Capital-Allocation-Logik
- `_combine_equity_curves()` – Equity-Curves kombinieren
- `_create_dummy_result()` – Dummy-Result bei Fehler

**Wichtig:**
- Bestehende API (`run_realistic()`, `run_vectorized()`) **unverändert**
- Risk-Layer-Integration bleibt erhalten

---

### 2. `src/strategies/__init__.py` 🔧

**Änderung:**
- `STRATEGY_REGISTRY` erweitert mit TOML-kompatiblen Namen:
  ```python
  "momentum_1h": "momentum",      # Strategie-Name != Modul-Name
  "rsi_strategy": "rsi",
  "bollinger_bands": "bollinger",
  "ecm_cycle": "ecm",
  ```

**Grund:**
- Namen in Registry müssen mit `[strategy.*]` in `config.toml` übereinstimmen

---

### 3. `scripts/demo_registry_backtest.py` 🆕

**Neu:** Vollständiges Demo-Script für Registry-Backtest-API

**Features:**
- Fake-OHLCV-Generator für Tests
- Demo 1: Single-Strategy (MA-Crossover, Momentum)
- Demo 2: Portfolio All Active (Equal Weight)
- Demo 3: Portfolio Regime-Filter (Trending)
- Demo 4: Portfolio Custom-Liste

**Usage:**
```bash
cd ~/Peak_Trade
source .venv/bin/activate
python scripts/demo_registry_backtest.py
```

---

### 4. `docs/REGISTRY_BACKTEST_API.md` 📚

**Neu:** Umfassende API-Dokumentation

**Inhalte:**
- API-Referenz (Single-Strategy, Portfolio)
- Workflow-Diagramme
- Code-Beispiele
- Config-Referenz
- Best Practices
- Fehlerbehebung
- Erweiterungspunkte (TODO-Liste)

---

## Testing

### Manuelle Tests

✅ **Demo ausgeführt:**
```bash
python scripts/demo_registry_backtest.py
```

**Ergebnis:**
- Alle 4 Demos laufen erfolgreich durch
- Single-Strategy-Backtests funktionieren
- Portfolio-Backtests funktionieren
- Regime-Filtering funktioniert
- Custom-Strategie-Listen funktionieren

**Bekannte Warnungen:**
- FutureWarning in `ma_crossover.py` (Pandas Downcast) – harmlos, keine Auswirkung

### Unit-Tests (TODO)

Noch keine automatisierten Tests geschrieben. Empfehlung:

```bash
# In tests/backtest/test_registry_backtest.py
pytest tests/backtest/test_registry_backtest.py -v
```

**Test-Cases:**
- Single-Strategy mit verschiedenen Configs
- Portfolio mit Equal/Manual Allocation
- Regime-Filtering
- Error-Handling (fehlende Strategien, falsche Config)

---

## Migration Guide

### Für bestehende Backtest-Scripts

**Alt:**
```python
from src.backtest.engine import BacktestEngine
from src.strategies.ma_crossover import generate_signals

engine = BacktestEngine()
result = engine.run_realistic(
    df=df,
    strategy_signal_fn=generate_signals,
    strategy_params={"fast_period": 10, "slow_period": 30, "stop_pct": 0.02}
)
```

**Neu:**
```python
from src.backtest.engine import run_single_strategy_from_registry

result = run_single_strategy_from_registry(
    df=df,
    strategy_name="ma_crossover",
    custom_params={"fast_period": 10, "slow_period": 30}
)
```

**Vorteile:**
- Defaults aus Config werden automatisch gemerged
- Kein manueller Import der Strategie-Funktion
- Konsistent mit Registry-Konzept

**Backward-Kompatibilität:**
- Alte API bleibt vollständig erhalten
- Bestehende Scripts funktionieren unverändert

---

## Offene Punkte / TODOs

### 5.1 Risk-Parity Allocation

**Status:** Stub implementiert, gibt Warning + fallback auf equal

**Implementierung:**
```python
# In _calculate_allocation():
elif method == "risk_parity":
    # Basierend auf Volatility -> gleiche Risk-Exposure
    # Benötigt historische Returns für jede Strategie
    pass
```

**Benötigt:**
- Rolling-Window-Volatility-Berechnung
- Sharpe-Ratio-basierte Weights

---

### 5.2 Sharpe-Weighted Allocation

**Status:** Stub implementiert, gibt Warning + fallback auf equal

**Implementierung:**
```python
elif method == "sharpe_weighted":
    # Höhere Sharpe -> mehr Kapital
    # Benötigt historische Backtests
    pass
```

**Benötigt:**
- Historische Backtest-Results pro Strategie
- Sharpe-Normalisierung

---

### 5.3 Dynamic Rebalancing

**Status:** Nicht implementiert

**Idee:**
- Portfolio periodisch rebalancen (z.B. alle 24h)
- Basierend auf aktueller Performance

**Config:**
```toml
[portfolio]
rebalance_frequency = 24  # Bars
dynamic_allocation = true
```

---

### 5.4 Unit-Tests

**Priorität:** Hoch

**Test-Dateien:**
- `tests/backtest/test_registry_backtest.py`
- `tests/backtest/test_portfolio_allocation.py`

**Coverage:**
- Single-Strategy-Backtest mit verschiedenen Configs
- Portfolio mit Equal/Manual Allocation
- Regime-Filtering
- Error-Handling

---

### 5.5 Multi-Portfolio-Support

**Status:** Partial (Profile-Overrides implementiert)

**Aktuell implementiert (Profile-Overrides):**
```toml
[portfolio.conservative]
allocation_method = "equal"
strategy_filter = ["ma_crossover"]

[portfolio.aggressive]
allocation_method = "risk_parity"
strategy_filter = ["momentum_1h", "rsi_strategy"]
```

```python
result = run_portfolio_from_config(df=df, portfolio_name="aggressive")
```

---

## Performance-Notizen

**Aktuelle Implementierung:**
- Portfolio-Backtests: **Sequential** (nacheinander)
- Potenzial für Parallelisierung (multiprocessing)

**Benchmark (Demo):**
- 1000 Bars, 3 Strategien: ~2-3 Sekunden
- 2000 Bars, 3 Strategien: ~4-5 Sekunden

**Optimierungspotenzial:**
```python
from multiprocessing import Pool

# In run_portfolio_from_config():
with Pool(processes=len(strategies)) as pool:
    results = pool.map(run_single_backtest, strategies)
```

---

## Git Commit

**Commit-Message:**
```
feat: Registry-basierte Backtest-Integration

- Neue Entry-Points: run_single_strategy_from_registry(), run_portfolio_from_config()
- Portfolio-Backtest mit Equal/Manual Allocation
- Regime-basiertes Strategie-Filtering
- Demo-Script + ausführliche Dokumentation

BREAKING: BacktestEngine nutzt jetzt config_registry statt core.config
→ Alte API (run_realistic) bleibt kompatibel

Files:
- src/backtest/engine.py (erweitert)
- src/strategies/__init__.py (Registry-Namen angepasst)
- scripts/demo_registry_backtest.py (neu)
- docs/REGISTRY_BACKTEST_API.md (neu)

Tested: Manuelle Demo erfolgreich
TODO: Unit-Tests, Risk-Parity, Sharpe-Weighted
```

**Dateien zum Commit:**
```bash
git add src/backtest/engine.py
git add src/strategies/__init__.py
git add scripts/demo_registry_backtest.py
git add docs/REGISTRY_BACKTEST_API.md
git commit -m "feat: Registry-basierte Backtest-Integration"
```

---

## Nächste Schritte

### Sofort

1. ✅ **Demo testen** (bereits erfolgt)
2. ✅ **Dokumentation schreiben** (bereits erfolgt)
3. ⬜ **Git-Commit** (vom User durchführen)

### Kurzfristig

4. ⬜ **Unit-Tests schreiben**
5. ⬜ **Risk-Parity Allocation implementieren**
6. ⬜ **End-to-End-Backtest-Script erstellen:**
   ```bash
   python scripts/run_backtest.py --strategy ma_crossover --timeframe 1h
   python scripts/run_backtest.py --portfolio --regime trending
   ```

### Mittelfristig

7. ⬜ **Sharpe-Weighted Allocation**
8. ⬜ **Dynamic Rebalancing**
9. ⬜ **Multi-Portfolio-Support**
10. ⬜ **Performance-Optimierung (Parallelisierung)**

---

## Zusammenfassung

**Was funktioniert:**
✅ Registry-basierter Single-Strategy-Backtest  
✅ Portfolio-Backtest (Equal/Manual Allocation)  
✅ Regime-Filtering  
✅ Custom Strategie-Listen  
✅ Risk-Layer-Integration (unverändert)  
✅ Vollständige Dokumentation  
✅ Demo-Script  

**Was noch fehlt:**
⬜ Unit-Tests  
⬜ Risk-Parity Allocation  
⬜ Sharpe-Weighted Allocation  
⬜ Dynamic Rebalancing  
⬜ Multi-Portfolio-Support  

**Breaking Changes:**
- BacktestEngine nutzt `config_registry.get_config()` (Returns Dict)
- Bestehende API bleibt kompatibel (kein Impact auf User-Code)

---

**Stand:** Dezember 2024  
**Autor:** Peak_Trade Team  
**Review:** Pending
