# Peak_Trade – Registry-Backtest API

**Stand:** Dezember 2024  
**Status:** ✅ Implementiert & Getestet

---

## Dokumentgrenzen

Die Angabe **„implementiert & getestet“** am Dokumentkopf bezieht sich auf die **vorhandene Registry-/Backtest-API-Oberfläche** und die in diesem Dokument als **lauffähig beschriebenen** Pfade (**Single-Strategy** aus der Registry sowie **Portfolio-Backtests** mit den hier dokumentierten **Capital-Allocation-Modi `equal` und `manual`**, inklusive der beschriebenen Filter/Workflow-Schritte). **Nicht** jede spätere oder in Konfigurationsbeispielen genannte Allocator-Variante ist damit bereits als produktiv gelieferte Semantik zu lesen.

**Offene Erweiterungspunkte:** Allocator-Kennzeichnungen wie **`risk_parity`** und **`sharpe_weighted`** sowie **Dynamic Rebalancing** sind in diesem Dokument im **Portfolio-Workflow** (Schritt **Capital Allocation** unter **„2. Portfolio-Backtest“ → Workflow**) sowie in **„5. Erweiterungspunkte“** ausdrücklich als **TODO** bzw. **Roadmap** geführt — solange dort **`TODO`**-/Stub-Inhalt dokumentiert ist, handelt es sich nicht um einen abgeschlossenen, produktreifen Lieferpfad. Daraus **keine** Live-, Trading-, Strategy-Readiness oder Gate-/Freigabe-Claims ableiten.

## Überblick

Die **Registry-Backtest-Integration** erweitert die bestehende `BacktestEngine` um zwei neue, konfigurationsbasierte Entry-Points:

1. **`run_single_strategy_from_registry()`** – Backtest EINER Strategie aus der Registry
2. **`run_portfolio_from_config()`** – Portfolio-Backtest mit MEHREREN Strategien

**Vorteil gegenüber bisheriger API:**
- ❌ Alt: Strategie-Funktion manuell importieren, Parameter hardcoded
- ✅ Neu: Strategie-Name angeben → Registry lädt automatisch + merged Defaults

---

## 1. Single-Strategy-Backtest

### API

```python
from src.backtest.engine import run_single_strategy_from_registry

result = run_single_strategy_from_registry(
    df=df,                          # OHLCV-DataFrame
    strategy_name="ma_crossover",   # Name aus config.toml
    custom_params=None,             # Optional: Override-Parameter
    position_sizer=None,            # Optional: Custom PositionSizer
    risk_limits=None,               # Optional: Custom RiskLimits
)
```

### Workflow

1. **Config laden:** Holt `[strategy.{name}]` + `[strategies.defaults]` aus `config.toml`
2. **Merging:** Kombiniert Defaults + Strategie-spezifische Parameter
3. **Override:** `custom_params` überschreiben merged Config
4. **Strategie laden:** `load_strategy(name)` holt Funktion aus `src/strategies/`
5. **Backtest:** Führt `BacktestEngine.run_realistic()` aus

### Beispiel

```python
import pandas as pd
from src.backtest.engine import run_single_strategy_from_registry

# OHLCV-Daten (z.B. aus Data-Layer)
df = pd.read_parquet("data/BTC_USD_1h.parquet")

# Backtest mit Config aus Registry
result = run_single_strategy_from_registry(
    df=df,
    strategy_name="ma_crossover",
    custom_params={
        "fast_period": 20,  # überschreibt Config-Wert
        "slow_period": 50,
    }
)

# Ergebnisse
print(f"Return: {result.stats['total_return']:.2%}")
print(f"Sharpe: {result.stats['sharpe']:.2f}")
print(f"Trades: {result.stats['total_trades']}")
```

### Return-Wert

`BacktestResult` mit:
- `equity_curve: pd.Series` – Equity-Verlauf
- `trades: List[Trade]` – Alle ausgeführten Trades
- `stats: Dict[str, float]` – Kennzahlen (Return, Sharpe, DD, etc.)
- `strategy_name: str` – Name der Strategie
- `blocked_trades: int` – Anzahl blockierter Trades durch Risk-Limits

---

## 2. Portfolio-Backtest

### API

```python
from src.backtest.engine import run_portfolio_from_config

result = run_portfolio_from_config(
    df=df,
    cfg=None,                    # Optional: Custom Config-Dict (default: lädt config.toml)
    portfolio_name="default",    # Portfolio-Name (für spätere Multi-Portfolio-Unterstützung)
    strategy_filter=None,        # Optional: Liste von Strategie-Namen
    regime_filter=None,          # Optional: "trending", "ranging", "any"
    position_sizer=None,
    risk_limits=None,
)
```

### Workflow

1. **Strategien bestimmen:**
   - Ohne Filter: nutzt `strategies.active` aus Config
   - Mit `strategy_filter`: explizite Liste
   - Mit `regime_filter`: filtert nach `metadata.best_market_regime`

2. **Limit prüfen:** Max. `portfolio.max_strategies_active` Strategien

3. **Capital Allocation:**
   - `"equal"`: Gleichverteilung (1/N)
   - `"manual"`: Nutzt `portfolio.weights` aus Config
   - `"risk_parity"`: TODO (gleiches Risk-Level)
   - `"sharpe_weighted"`: TODO (historische Sharpe)

4. **Backtests ausführen:**
   - Jede Strategie erhält anteiliges Kapital
   - Parallele Ausführung (unabhängige Equity-Curves)

5. **Equity kombinieren:**
   - Gewichtete Summe der einzelnen Equity-Curves

6. **Portfolio-Stats:** Aggregierte Kennzahlen

### Beispiele

#### Alle aktiven Strategien (Equal Weight)

```python
result = run_portfolio_from_config(df=df)

print(f"Portfolio Return: {result.portfolio_stats['total_return']:.2%}")
print(f"Portfolio Sharpe: {result.portfolio_stats['sharpe']:.2f}")
print(f"Strategien: {list(result.strategy_results.keys())}")
```

#### Nur Trending-Strategien

```python
result = run_portfolio_from_config(
    df=df,
    regime_filter="trending",
)
```

Dies nutzt nur Strategien mit `metadata.best_market_regime = "trending"` oder `"any"`.

#### Custom Strategie-Liste

```python
result = run_portfolio_from_config(
    df=df,
    strategy_filter=["ma_crossover", "momentum_1h"],
)
```

#### Manual Allocation (aus Config)

In `config.toml`:
```toml
[portfolio]
allocation_method = "manual"

[portfolio.weights]
ma_crossover = 0.40
momentum_1h = 0.30
rsi_strategy = 0.30
```

```python
result = run_portfolio_from_config(df=df)
# Nutzt automatisch manual weights
```

### Return-Wert

`PortfolioResult` mit:
- `combined_equity: pd.Series` – Kombinierte Portfolio-Equity
- `strategy_results: Dict[str, BacktestResult]` – Individual-Results pro Strategie
- `portfolio_stats: Dict[str, float]` – Aggregierte Stats
- `allocation: Dict[str, float]` – Capital-Allocation pro Strategie

---

## 3. Konfiguration

### Strategie-Registry

**File:** `config/config.toml`

```toml
# ============================================================================
# STRATEGIEN-REGISTRY
# ============================================================================

[strategies]
# Aktive Strategien (für Portfolio-Backtests)
active = ["ma_crossover", "momentum_1h", "rsi_strategy"]

# Verfügbare Strategien (Dokumentation)
available = [
    "ma_crossover",
    "momentum_1h",
    "rsi_strategy",
    "bollinger_bands",
    "macd",
    "ecm_cycle"
]

# Default-Parameter für ALLE Strategien
[strategies.defaults]
stop_pct = 0.02
take_profit_pct = 0.05
position_fraction = 0.25
min_hold_bars = 3
max_hold_bars = 100
# ... weitere Defaults

# Strategie-Metadaten (für Filtering)
[strategies.metadata.ma_crossover]
type = "trend_following"
risk_level = "medium"
best_market_regime = "trending"
recommended_timeframes = ["1h", "4h", "1d"]

# ============================================================================
# STRATEGIE-SPEZIFISCHE PARAMETER
# ============================================================================

[strategy.ma_crossover]
fast_period = 10
slow_period = 30
stop_pct = 0.02  # überschreibt strategies.defaults.stop_pct

[strategy.momentum_1h]
lookback_period = 20
entry_threshold = 0.02
exit_threshold = -0.01
stop_pct = 0.025
```

### Portfolio-Config

```toml
[portfolio]
enabled = true
max_strategies_active = 3
min_correlation = -0.3
rebalance_frequency = 24

# Capital Allocation
allocation_method = "equal"  # "equal", "manual", "risk_parity", "sharpe_weighted"
total_capital = 10000.0

# Portfolio-Level Risk
portfolio_max_dd = -0.20
portfolio_stop_loss = -0.05

# Manual Weights (nur bei allocation_method="manual")
[portfolio.weights]
ma_crossover = 0.33
momentum_1h = 0.33
rsi_strategy = 0.34
```

### Strategie-Modul-Mapping

Das folgende Snippet ist ein **Auszug** (häufig genutzte Kern-Keys); die **vollständige** Zuordnung Strategie-Name → Modulpfad steht im Quellcode in `src/strategies/__init__.py`. Für den **klassenbasierten**, konfigurationsgetriebenen Einstieg (`StrategySpec`, z. B. `create_strategy_from_config`) siehe `src/strategies/registry.py`.

**File:** `src/strategies/__init__.py`

```python
STRATEGY_REGISTRY = {
    "ma_crossover": "ma_crossover",
    "momentum_1h": "momentum",      # Strategie-Name != Modul-Name
    "rsi_strategy": "rsi",
    "bollinger_bands": "bollinger",
    "macd": "macd",
    "ecm_cycle": "ecm",
}
```

**WICHTIG:** Die Keys müssen mit `[strategy.*]`-Namen in `config.toml` übereinstimmen!

---

## 4. Abgrenzung zur alten API

### Alte API (weiterhin verfügbar)

```python
from src.backtest.engine import BacktestEngine
from src.strategies.ma_crossover import generate_signals

engine = BacktestEngine()
result = engine.run_realistic(
    df=df,
    strategy_signal_fn=generate_signals,
    strategy_params={
        "fast_period": 10,
        "slow_period": 30,
        "stop_pct": 0.02,
    }
)
```

**Nachteile:**
- Strategie-Funktion muss manuell importiert werden
- Parameter hardcoded
- Kein Defaults-Merging
- Keine Portfolio-Unterstützung

### Neue API (empfohlen)

```python
from src.backtest.engine import run_single_strategy_from_registry

result = run_single_strategy_from_registry(
    df=df,
    strategy_name="ma_crossover",
    custom_params={"fast_period": 20}  # nur Overrides nötig
)
```

**Vorteile:**
- Config-basiert (DRY-Prinzip)
- Defaults-Merging automatisch
- Strategie-Loader dynamisch
- Portfolio-Support out-of-the-box
- Konsistent mit Registry-Konzept

---

## 5. Erweiterungspunkte

### 5.1 Risk-Parity Allocation (TODO)

```python
def _calculate_allocation(...):
    # ...
    elif method == "risk_parity":
        # Basierend auf Volatility/Sharpe gleiche Risk-Exposure
        # Benötigt historische Backtests oder Rolling-Window-Analyse
        pass
```

### 5.2 Sharpe-Weighted Allocation (TODO)

```python
elif method == "sharpe_weighted":
    # Basierend auf historischer Sharpe-Ratio
    # Höhere Sharpe → mehr Kapital
    pass
```

### 5.3 Dynamic Rebalancing (TODO)

Aktuell: Statische Allocation für gesamten Backtest-Zeitraum  
Zukünftig: Periodisches Rebalancing (z.B. alle 24h)

```python
# In run_portfolio_from_config():
rebalance_freq = portfolio_cfg.get("rebalance_frequency", 24)
# Implementierung: Rolling-Allocation basierend auf Performance
```

### 5.4 Multi-Portfolio-Support (Partial)

**Status:** Basis-Implementierung vorhanden (Profile-Overrides via Subtables).

Aktuell unterstützt Peak_Trade **Portfolio-Profile-Overrides** via TOML-Subtables:

```toml
[portfolio]
enabled = true
allocation_method = "equal"
total_capital = 10000.0

[portfolio.aggressive]
allocation_method = "manual"
total_capital = 20000.0
```

```python
result = run_portfolio_from_config(
    df=df,
    portfolio_name="aggressive",
)
```

---

## 6. Best Practices

### 6.1 Strategie-Entwicklung

1. **Strategie-Modul erstellen:** `src/strategies/my_strategy.py`
2. **`generate_signals()` implementieren:** `(df, params) → pd.Series`
3. **Registry-Eintrag:** `STRATEGY_REGISTRY["my_strategy"] = "my_strategy"`
4. **Config-Block:** `[strategy.my_strategy]` in `config.toml`
5. **Metadata:** `[strategies.metadata.my_strategy]` für Filtering

### 6.2 Backtest-Workflow

1. **Single-Strategy-Tests:**
   - Erst mit `run_single_strategy_from_registry()` einzeln testen
   - Parameter-Tuning via `custom_params`
   - Validierung: Sharpe > 1.5, MaxDD < -15%

2. **Portfolio-Tests:**
   - Erst Trending-Strategien, dann Ranging-Strategien isoliert testen
   - Korrelations-Analyse zwischen Strategien
   - Portfolio-Backtest mit Equal Weight
   - Später: Risk-Parity oder Sharpe-Weighted

3. **Live-Freigabe:**
   - Min. 6 Monate Backtest-Historie
   - Mehrere Marktregimes abgedeckt
   - Siehe `[validation]` in Config

### 6.3 Config-Management

- **Keine Secrets in `config.toml`!** → Nutze `.env` oder Umgebungsvariablen
- **Versionierung:** `config.toml` sollte ins Repo (ohne Keys)
- **Dev/Prod:** Nutze `PEAK_TRADE_CONFIG=&#47;path&#47;to&#47;prod.toml`

---

## 7. Fehlerbehebung

### Error: "Strategie 'X' nicht in config.toml definiert"

**Lösung:** Füge `[strategy.X]`-Block in `config.toml` hinzu.

### Error: "Unbekannte Strategie 'X'"

**Lösung:** Füge Eintrag in `STRATEGY_REGISTRY` in `src/strategies/__init__.py` hinzu.

### Warning: "Portfolio limitiert auf N Strategien"

**Info:** `portfolio.max_strategies_active` ist erreicht. Erhöhe Limit oder reduziere `strategies.active`.

### Trades = 0 / Blocked Trades hoch

**Mögliche Ursachen:**
1. **Risk-Limits zu streng:** Stop-Distance zu gering, Max-Position-Size zu klein
2. **Strategie-Signale:** Keine Entry-Signale generiert
3. **Daten-Qualität:** Zu wenig Bars, ungültige OHLCV

**Debug:**
```python
import logging
logging.basicConfig(level=logging.DEBUG)
# Re-run Backtest mit DEBUG-Logs
```

---

## 8. Demo

**File:** `scripts/demo_registry_backtest.py`

```bash
cd ~/Peak_Trade
source .venv/bin/activate
python3 scripts/demo_registry_backtest.py
```

**Output:**
- Demo 1: Single-Strategy (MA-Crossover, Momentum)
- Demo 2: Portfolio All Active (Equal Weight)
- Demo 3: Portfolio Regime-Filter (Trending)
- Demo 4: Portfolio Custom-List (MA + Momentum)

---

## 9. Zusammenfassung

✅ **Was funktioniert:**
- Registry-basierter Single-Strategy-Backtest
- Portfolio-Backtest mit Equal/Manual Allocation
- Regime-basiertes Filtering
- Custom Strategie-Listen
- Defaults-Merging aus Config
- Risk-Layer-Integration (unverändert)

🚧 **Noch nicht implementiert:**
- Risk-Parity Allocation
- Sharpe-Weighted Allocation
- Dynamic Rebalancing
- Multi-Portfolio-Support

📚 **Siehe auch:**
- `README_REGISTRY.md` – Allgemeine Registry-Konzepte
- `docs/CONFIG_REGISTRY_USAGE.md` – Config-API-Referenz
- `scripts/demo_config_registry.py` – Registry-Basics
- `scripts/demo_registry_backtest.py` – Backtest-Demos

---

**Stand:** Dezember 2024  
**Autor:** Peak_Trade Team  
**Lizenz:** Proprietary
