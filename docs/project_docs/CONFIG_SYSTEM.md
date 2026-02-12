# Peak_Trade Config-System

**Stand:** 2025-12-02
**Komponenten:** Simple TOML Loader + BacktestEngine + Risk-Layer

---

## Übersicht

Das Config-System nutzt einfache TOML-Dateien ohne Pydantic-Validierung.

### Komponenten

1. **Config-Datei:** `config/default.toml`
2. **TOML-Loader:** `src/core/config_simple.py`
3. **BacktestEngine:** `src/backtest/engine.py`
4. **Risk-Layer:** `src/risk/` (PositionSizer + RiskLimits)

---

## Quick Start

### 1. Config laden

```python
from src.core.config_simple import load_config

# Default: config/default.toml
cfg = load_config()

# Custom Pfad
cfg = load_config('my_config.toml')

# Via Environment Variable
import os
os.environ['PEAK_TRADE_CONFIG'] = 'custom.toml'
cfg = load_config()
```

### 2. Strategie-Config holen

```python
from src.core.config_simple import get_strategy_config, list_strategies

# Alle verfügbaren Strategien
strategies = list_strategies(cfg)
# => ['ma_crossover', 'momentum_1h', 'rsi_strategy']

# Spezifische Strategie
strat_cfg = get_strategy_config(cfg, 'ma_crossover')
# => {'fast_period': 10, 'slow_period': 30, 'stop_pct': 0.02}
```

### 3. Risk-Layer initialisieren

```python
from src.risk import PositionSizer, PositionSizerConfig, RiskLimits, RiskLimitsConfig

# PositionSizer aus Config
position_sizer = PositionSizer(
    PositionSizerConfig(
        method=cfg['risk']['position_sizing_method'],
        risk_pct=cfg['risk']['risk_per_trade'] * 100,  # Dezimal -> Prozent
        max_position_pct=cfg['risk']['max_position_size'] * 100,
    )
)

# RiskLimits aus Config
risk_limits = RiskLimits(
    RiskLimitsConfig(
        max_drawdown_pct=cfg['risk']['max_drawdown_pct'],
        max_position_pct=cfg['risk']['max_position_pct'],
        daily_loss_limit_pct=cfg['risk']['daily_loss_limit_pct'],
    )
)
```

### 4. Backtest durchführen

```python
from src.backtest.engine import BacktestEngine
from src.strategies.ma_crossover import generate_signals

# Engine mit Risk-Layer
engine = BacktestEngine(
    position_sizer=position_sizer,
    risk_limits=risk_limits
)

# Backtest ausführen
result = engine.run_realistic(
    df=df,  # OHLCV DataFrame
    strategy_signal_fn=generate_signals,
    strategy_params=strat_cfg
)

# Ergebnisse
print(f"Total Return: {result.stats['total_return']:.2%}")
print(f"Sharpe Ratio: {result.stats['sharpe']:.2f}")
print(f"Total Trades: {result.stats['total_trades']}")
print(f"Blocked Trades: {result.blocked_trades}")
```

---

## Config-Datei: config/default.toml

### Struktur

```toml
[backtest]
initial_cash = 10000.0
results_dir = "results"

[risk]
# Position Sizing
position_sizing_method = "fixed_fractional"
risk_per_trade = 0.01          # 1% Risiko pro Trade
max_position_size = 0.25       # Max 25% des Kapitals
min_position_value = 50.0      # Min $50 Position
min_stop_distance = 0.005      # Min 0.5% Stop-Distanz

# Portfolio Risk Limits
max_drawdown_pct = 20.0        # Max 20% Drawdown
max_position_pct = 10.0        # Max 10% Position
daily_loss_limit_pct = 5.0     # Max 5% Daily Loss

# Kelly (falls verwendet)
kelly_scaling = 0.5

[data]
default_timeframe = "1h"
data_dir = "data"
use_cache = true
cache_format = "parquet"

[strategy.ma_crossover]
fast_period = 10
slow_period = 30
stop_pct = 0.02

[strategy.momentum_1h]
lookback_period = 20
entry_threshold = 0.02
exit_threshold = -0.01
stop_pct = 0.025

[strategy.rsi_strategy]
rsi_period = 14
oversold = 30
overbought = 70
stop_pct = 0.02
```

### Wichtige Parameter

#### Backtest

- `initial_cash`: Startkapital in USD
- `results_dir`: Verzeichnis für Backtest-Ergebnisse

#### Risk

**Position Sizing:**
- `position_sizing_method`: "fixed_fractional" oder "kelly"
- `risk_per_trade`: Risiko pro Trade (Dezimal: 0.01 = 1%)
- `max_position_size`: Max Position (Dezimal: 0.25 = 25%)
- `min_position_value`: Minimaler Positionswert in USD
- `min_stop_distance`: Minimale Stop-Distanz (Dezimal)

**Risk Limits:**
- `max_drawdown_pct`: Max Drawdown in Prozent (20.0 = 20%)
- `max_position_pct`: Max Position in Prozent (10.0 = 10%)
- `daily_loss_limit_pct`: Daily Loss Limit in Prozent (5.0 = 5%)

⚠️ **WICHTIG:**
- `risk_per_trade`, `max_position_size` sind **Dezimalwerte** (0.01 = 1%)
- `*_pct` Parameter sind **Prozentwerte** (20.0 = 20%)

#### Data

- `default_timeframe`: Standard-Timeframe ("1h", "4h", "1d")
- `data_dir`: Daten-Verzeichnis
- `use_cache`: Caching aktivieren
- `cache_format`: Cache-Format ("parquet")

#### Strategy

Jede Strategie hat eigene Parameter unter `[strategy.NAME]`.

**Beispiel:**
```toml
[strategy.ma_crossover]
fast_period = 10
slow_period = 30
stop_pct = 0.02
```

---

## Demo-Script

### Ausführen

```bash
# Mit default config
python3 scripts/run_simple_backtest.py

# Mit custom config
PEAK_TRADE_CONFIG=my_config.toml python3 scripts/run_simple_backtest.py
```

### Was macht das Script?

1. ✅ Lädt Config aus `config/default.toml`
2. ✅ Initialisiert Risk-Layer mit Config-Parametern
3. ✅ Lädt Strategie-Parameter aus Config
4. ✅ Führt Backtest mit vollständigem Risk-Management durch
5. ✅ Zeigt Ergebnisse (Performance, Trades, Risk-Stats)

### Erwartete Ausgabe

```
======================================================================
PEAK_TRADE SIMPLE BACKTEST
======================================================================

Zeigt vollständige Config-Integration:

  ✅ TOML Config Loader (ohne Pydantic)
  ✅ BacktestEngine mit Risk-Layer
  ✅ Strategie-Parameter aus Config
  ✅ Risk-Parameter aus Config

----------------------------------------------------------------------
1. Config laden
----------------------------------------------------------------------
✅ Config geladen: config/default.toml

📋 Backtest-Config:
  Initial Cash:      $10,000.00
  Results Dir:       results

📋 Risk-Config:
  Risk per Trade:    1.0%
  Max Position:      25%
  Max Drawdown:      20.0%
  Daily Loss Limit:  5.0%

📋 Verfügbare Strategien: ma_crossover, momentum_1h, rsi_strategy

----------------------------------------------------------------------
2. Strategie-Config laden
----------------------------------------------------------------------
✅ Strategie 'ma_crossover' geladen

📋 Parameter:
  fast_period         : 10
  slow_period         : 30
  stop_pct            : 0.02

... (weitere Schritte)

======================================================================
BACKTEST ERGEBNISSE
======================================================================

📊 Performance:
  Total Return:           0.00%
  Max Drawdown:           0.00%
  Sharpe Ratio:            0.00

📊 Trades:
  Total Trades:               0
  Blocked Trades:           115
  Win Rate:                0.0%
  Profit Factor:           0.00
```

---

## Custom Config erstellen

### 1. Neue Config-Datei

```bash
cp config/default.toml config/my_aggressive.toml
vim config/my_aggressive.toml
```

### 2. Anpassen

```toml
[risk]
# Aggressiver
risk_per_trade = 0.02          # 2% statt 1%
max_position_size = 0.50       # 50% statt 25%
max_drawdown_pct = 30.0        # 30% statt 20%
daily_loss_limit_pct = 10.0    # 10% statt 5%
```

### 3. Nutzen

```bash
PEAK_TRADE_CONFIG=config/my_aggressive.toml python scripts/run_simple_backtest.py
```

---

## API-Referenz

### load_config()

```python
from src.core.config_simple import load_config

cfg = load_config(config_path=None)
# -> dict[str, Any]
```

**Args:**
- `config_path`: Optional - Pfad zur TOML-Datei

**Returns:**
- `dict` mit Config-Daten

**Raises:**
- `FileNotFoundError`: Wenn Config-Datei nicht existiert

**Pfad-Resolution:**
1. Explizit übergebener `config_path`
2. Environment Variable `PEAK_TRADE_CONFIG`
3. Default: `config/default.toml`

### get_strategy_config()

```python
from src.core.config_simple import get_strategy_config

strat_cfg = get_strategy_config(cfg, strategy_name)
# -> dict[str, Any]
```

**Args:**
- `cfg`: Config-Dict von `load_config()`
- `strategy_name`: Name der Strategie (z.B. "ma_crossover")

**Returns:**
- `dict` mit Strategie-Parametern

**Raises:**
- `KeyError`: Wenn Strategie nicht definiert

### list_strategies()

```python
from src.core.config_simple import list_strategies

strategies = list_strategies(cfg)
# -> list[str]
```

**Args:**
- `cfg`: Config-Dict von `load_config()`

**Returns:**
- Sortierte Liste von Strategie-Namen

---

## Integration mit BacktestEngine

### Vollständiges Beispiel

```python
from src.core.config_simple import load_config, get_strategy_config
from src.backtest.engine import BacktestEngine
from src.risk import PositionSizer, PositionSizerConfig, RiskLimits, RiskLimitsConfig
from src.strategies.ma_crossover import generate_signals

# 1. Config laden
cfg = load_config()

# 2. Risk-Layer initialisieren
position_sizer = PositionSizer(
    PositionSizerConfig(
        method=cfg['risk']['position_sizing_method'],
        risk_pct=cfg['risk']['risk_per_trade'] * 100,
        max_position_pct=cfg['risk']['max_position_size'] * 100,
    )
)

risk_limits = RiskLimits(
    RiskLimitsConfig(
        max_drawdown_pct=cfg['risk']['max_drawdown_pct'],
        max_position_pct=cfg['risk']['max_position_pct'],
        daily_loss_limit_pct=cfg['risk']['daily_loss_limit_pct'],
    )
)

# 3. BacktestEngine erstellen
engine = BacktestEngine(
    position_sizer=position_sizer,
    risk_limits=risk_limits
)

# 4. Strategie-Config holen
strat_cfg = get_strategy_config(cfg, 'ma_crossover')

# 5. Backtest durchführen
result = engine.run_realistic(
    df=df,
    strategy_signal_fn=generate_signals,
    strategy_params=strat_cfg
)

# 6. Ergebnisse
print(f"Return: {result.stats['total_return']:.2%}")
print(f"Sharpe: {result.stats['sharpe']:.2f}")
print(f"Trades: {result.stats['total_trades']}")
print(f"Blocked: {result.blocked_trades}")
```

---

## Troubleshooting

### Problem: Config nicht gefunden

**Fehler:**
```
FileNotFoundError: Config file not found: config/default.toml
```

**Lösung:**
```bash
# Prüfen ob Datei existiert
ls -la config/default.toml

# Wenn nicht: Von Root-Config kopieren
cp config.toml config/default.toml

# Oder: Environment Variable setzen
export PEAK_TRADE_CONFIG=config.toml
```

### Problem: Strategie nicht gefunden

**Fehler:**
```
KeyError: Strategie 'xyz' nicht in Config gefunden
```

**Lösung:**
```python
# Verfügbare Strategien anzeigen
from src.core.config_simple import list_strategies, load_config

cfg = load_config()
print(list_strategies(cfg))
# => ['ma_crossover', 'momentum_1h', 'rsi_strategy']

# Strategie in config/default.toml hinzufügen:
# [strategy.xyz]
# param1 = value1
```

### Problem: Alle Trades blockiert

**Symptom:**
```
Total Trades: 0
Blocked Trades: 115
```

**Mögliche Ursachen:**

1. **Position zu klein:**
```toml
[risk]
min_position_value = 50.0  # Zu hoch?
```

2. **Max Position zu niedrig:**
```toml
[risk]
max_position_pct = 10.0  # 10% - erhöhen auf 25%?
```

3. **Stop-Distanz zu eng:**
```toml
[risk]
min_stop_distance = 0.005  # 0.5% - evtl. zu streng

[strategy.ma_crossover]
stop_pct = 0.02  # 2% - sollte OK sein
```

**Lösung:**
```toml
[risk]
max_position_pct = 25.0  # Erhöhen
min_position_value = 25.0  # Reduzieren
```

---

## Vergleich: Alte vs Neue Config

### Alte Config (Pydantic)

```python
from src.core import get_config

cfg = get_config()
print(cfg.risk.risk_per_trade)  # Attribute-Access
print(cfg.backtest.initial_cash)
```

### Neue Config (Simple TOML)

```python
from src.core.config_simple import load_config

cfg = load_config()
print(cfg['risk']['risk_per_trade'])  # Dict-Access
print(cfg['backtest']['initial_cash'])
```

**Vorteile Simple:**
- ✅ Keine Pydantic-Dependency
- ✅ Einfacher dict-basiert
- ✅ Flexible Struktur

**Nachteile Simple:**
- ❌ Keine automatische Validierung
- ❌ Keine Type-Hints im Config-Objekt

---

## Zusammenfassung

1. ✅ **Config-Datei:** `config/default.toml` - Zentrale Config für alle Parameter
2. ✅ **TOML-Loader:** `src/core/config_simple.py` - Einfacher Loader ohne Pydantic
3. ✅ **Risk-Integration:** Risk-Parameter direkt aus Config
4. ✅ **Backtest-Script:** `scripts/run_simple_backtest.py` - Vollständiges Beispiel
5. ✅ **Flexibel:** Environment Variable für Custom Configs

**Workflow:**
1. Config laden mit `load_config()`
2. Strategie-Config holen mit `get_strategy_config()`
3. Risk-Layer initialisieren aus Config
4. Backtest durchführen mit `engine.run_realistic()`

**Status:** Produktionsreif ✅

---

**Stand:** 2025-12-02
**Dateien:**
- `config/default.toml`
- `src/core/config_simple.py`
- `scripts/run_simple_backtest.py`
