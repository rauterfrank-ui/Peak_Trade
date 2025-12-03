# Peak_Trade Config Registry - Usage Guide

## 📚 Übersicht

Die neue **Strategien-Registry** bietet:

✅ **Zentrale Verwaltung** aller Strategien in `config.toml`  
✅ **Active/Available-Listen** für Portfolio-Management  
✅ **Default-Parameter** mit Override-Logik  
✅ **Metadata** für intelligente Strategie-Selektion  
✅ **Marktregime-Filtering** (trending/ranging)  

---

## 🚀 Quick Start

### 1. Basic Usage

```python
from src.core.config_registry import get_config, get_active_strategies, get_strategy_config

# Config laden
cfg = get_config()

# Active Strategies
for name in get_active_strategies():
    print(f"🎯 {name}")
```

### 2. Strategie-Config mit Defaults-Merging

```python
from src.core.config_registry import get_strategy_config

cfg = get_strategy_config("ma_crossover")

# Zugriff auf Parameter (mit Fallback auf Defaults)
stop_pct = cfg.get("stop_pct")           # 0.02 (aus strategy.ma_crossover)
take_profit = cfg.get("take_profit_pct") # 0.05 (aus strategies.defaults)
position_frac = cfg.get("position_fraction") # 0.25 (aus defaults)

# Alle Parameter als Dict
all_params = cfg.to_dict()
```

### 3. Backtest-Integration

```python
from src.core.config_registry import get_active_strategies, get_strategy_config
from src.backtest import BacktestEngine

engine = BacktestEngine(initial_cash=10000)

for name in get_active_strategies():
    cfg = get_strategy_config(name)
    
    # Strategie-Instanz erstellen
    strategy = create_strategy(name, **cfg.params)
    
    # Backtest durchführen
    results = engine.run(
        strategy=strategy,
        data=ohlcv_data,
        stop_pct=cfg.get("stop_pct"),
        take_profit_pct=cfg.get("take_profit_pct"),
        position_fraction=cfg.get("position_fraction")
    )
    
    print(f"✅ {name}: Sharpe={results.sharpe:.2f}")
```

---

## 🎯 API-Referenz

### `get_config() -> Dict[str, Any]`

Gibt die komplette Raw-Config zurück.

```python
cfg = get_config()
print(cfg["risk"]["risk_per_trade"])  # 0.01
print(cfg["backtest"]["initial_cash"])  # 10000.0
```

---

### `get_active_strategies() -> List[str]`

Liste der aktuell aktiven Strategien (aus `strategies.active`).

```python
active = get_active_strategies()
# → ["ma_crossover", "momentum_1h", "rsi_strategy"]
```

---

### `get_strategy_config(name: str) -> StrategyConfig`

Lädt Strategie-Config mit Defaults-Merging.

**Returns:** `StrategyConfig` mit:
- `name`: Strategie-Name
- `active`: Bool (ist in active-Liste?)
- `params`: Strategie-spezifische Parameter
- `defaults`: Merged Defaults
- `metadata`: Optional Metadata-Dict

**Methods:**
- `cfg.get(key, default=None)`: Parameter mit Fallback
- `cfg.to_dict()`: Merged Dict aller Parameter

```python
cfg = get_strategy_config("ma_crossover")

print(cfg.name)       # "ma_crossover"
print(cfg.active)     # True
print(cfg.params)     # {"fast_period": 10, "slow_period": 30, ...}
print(cfg.get("stop_pct"))  # 0.02 (aus strategy.ma_crossover)
print(cfg.to_dict())  # Merged: defaults + params
```

---

### `list_strategies() -> List[str]`

Liste ALLER definierten Strategien (aus `[strategy.*]`-Blöcken).

```python
all_strats = list_strategies()
# → ["bollinger_bands", "ecm_cycle", "ma_crossover", ...]
```

---

### `get_strategies_by_regime(regime: str) -> List[str]`

Filtert Strategien nach Marktregime.

**Args:**
- `regime`: "trending", "ranging", oder "any"

**Returns:** Liste von Strategie-Namen passend zum Regime

```python
# Marktregime erkennen (extern implementieren)
current_regime = detect_market_regime(data)  # → "trending"

# Passende Strategien laden
suitable = get_strategies_by_regime(current_regime)
# → ["ma_crossover", "momentum_1h", "macd"]

for name in suitable:
    cfg = get_strategy_config(name)
    # ... backtest
```

---

## 📋 Config-Struktur

### Minimale Registry-Config

```toml
[strategies]
active = ["ma_crossover", "momentum_1h"]
available = ["ma_crossover", "momentum_1h", "rsi_strategy"]

[strategies.defaults]
stop_pct = 0.02
take_profit_pct = 0.05
position_fraction = 0.25
min_hold_bars = 3
max_hold_bars = 100

[strategy.ma_crossover]
fast_period = 10
slow_period = 30
# stop_pct wird von defaults übernommen
```

### Mit Metadata

```toml
[strategies.metadata.ma_crossover]
type = "trend_following"
risk_level = "medium"
best_market_regime = "trending"
recommended_timeframes = ["1h", "4h", "1d"]
```

---

## 🎨 Advanced Use Cases

### 1. Dynamisches Portfolio-Rebalancing

```python
from src.core.config_registry import get_strategies_by_regime, get_strategy_config

def rebalance_portfolio(market_regime: str):
    """Passt Portfolio an Marktregime an."""
    suitable = get_strategies_by_regime(market_regime)
    
    # Nur aktive Strategien
    active_suitable = [
        name for name in suitable
        if get_strategy_config(name).active
    ]
    
    # Capital-Allokation
    weights = {name: 1.0 / len(active_suitable) for name in active_suitable}
    return weights

# Verwendung
regime = detect_market_regime(data)
new_weights = rebalance_portfolio(regime)
# → {"ma_crossover": 0.5, "momentum_1h": 0.5}
```

### 2. Risk-Level-Filtering

```python
def get_low_risk_strategies() -> List[str]:
    """Nur Strategien mit risk_level='low'."""
    result = []
    for name in get_active_strategies():
        cfg = get_strategy_config(name)
        if cfg.metadata and cfg.metadata.get("risk_level") == "low":
            result.append(name)
    return result
```

### 3. Timeframe-Optimierung

```python
def get_strategies_for_timeframe(timeframe: str) -> List[str]:
    """Filtert nach empfohlenem Timeframe."""
    result = []
    for name in get_active_strategies():
        cfg = get_strategy_config(name)
        if cfg.metadata:
            recommended = cfg.metadata.get("recommended_timeframes", [])
            if timeframe in recommended:
                result.append(name)
    return result

# Verwendung
strategies_1h = get_strategies_for_timeframe("1h")
```

---

## 🚨 Best Practices (als Peak_Risk)

### ✅ DO's

1. **Immer Defaults nutzen** für gemeinsame Parameter
2. **Active-Liste klein halten** (max. 3-5 Strategien)
3. **Metadata pflegen** für intelligente Selektion
4. **Vor Live-Trading:** Min. 6 Monate Backtest-Validation
5. **Risk-Limits beachten:**
   - `risk_per_trade <= 0.02` (2%)
   - `max_position_size <= 0.50` (50%)
   - `max_positions` konsistent mit `max_total_exposure`

### ❌ DON'Ts

1. **Niemals** alle Strategien gleichzeitig aktiv
2. **Niemals** `stop_pct > 0.05` (5%) als Default
3. **Niemals** Risk-Limits in Strategy-Config überschreiben
4. **Niemals** Live-Trading ohne Validation-Kennzahlen

---

## 🧪 Testing

```python
from src.core.config_registry import reset_config, get_strategy_config

def test_strategy_defaults_merge():
    """Test: Defaults werden korrekt gemerged."""
    reset_config()  # Cache leeren
    
    cfg = get_strategy_config("ma_crossover")
    
    # Strategie-spezifisch
    assert cfg.get("fast_period") == 10
    
    # Aus defaults
    assert cfg.get("take_profit_pct") == 0.05
    assert cfg.get("position_fraction") == 0.25
```

---

## 🔗 Siehe auch

- **Peak_Trade_OVERVIEW.md** - Projekt-Übersicht
- **Peak_Trade_Data_Layer_Doku.md** - Data-Layer-Dokumentation
- **config/config.toml** - Haupt-Konfigurationsdatei

---

## 📞 Troubleshooting

**Problem:** `KeyError: "Strategie 'XYZ' nicht definiert"`

**Lösung:** Strategie muss in `config.toml` als `[strategy.XYZ]` definiert sein.

---

**Problem:** Defaults werden nicht übernommen

**Lösung:** Prüfe `[strategies.defaults]`-Block in `config.toml`.

---

**Problem:** `FileNotFoundError: Config nicht gefunden`

**Lösung:** 
```bash
# Setze Environment Variable
export PEAK_TRADE_CONFIG=/path/to/config.toml

# Oder: Stelle sicher, dass du im Projekt-Root bist
cd ~/Peak_Trade
```

---

**Stand:** Dezember 2024  
**Autor:** Peak_Trade Core Team
