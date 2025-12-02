# Peak_Trade: Projekt-Zusammenfassung für neuen Chat

> **KI-unterstütztes, risikokontrolliertes Trading-Framework**  
> Stand: Dezember 2024  
> Zweck: Backtests, Strategieentwicklung, Risk-Management  
> **KEIN Live-Trading ohne ausgiebige Validierung!**

---

## 📋 Projekt-Übersicht

### Ziele
- **Risk-First-Ansatz**: Jeder Trade durch Position Sizing + Stop-Loss abgesichert
- **Realistische Backtests**: Bar-für-Bar-Simulation mit echtem Risk-Management
- **Modulare Architektur**: Klare Trennung Data/Strategy/Risk/Backtest
- **Nachvollziehbarkeit**: Logging + Performance-Metriken

### Tech-Stack
```
Python 3.11+
├─ pandas, numpy          # Datenverarbeitung
├─ pydantic              # Config-Validierung
├─ ccxt                  # Kraken-API
├─ pyarrow               # Parquet-Caching
└─ pytest                # Testing
```

---

## 🏗️ Projektstruktur

```
Peak_Trade/
├─ config.toml                         # Zentrale Konfiguration
├─ README.md
├─ requirements.txt
├─ .gitignore
│
├─ docs/
│  ├─ architecture.md                  # Architektur-Details
│  ├─ llm_workflows.md                 # LLM-Prompts für neue Chats
│  ├─ armstrong_notes.md               # Economic Confidence Model
│  ├─ trading_bot_notes.md
│  └─ Peak_Trade_setup_notes.md
│
├─ data/                               # Nicht ins Repo!
│  └─ raw/
│
├─ results/                            # Nicht ins Repo!
│  ├─ backtests/
│  └─ reports/
│
├─ src/
│  ├─ core/
│  │  ├─ __init__.py
│  │  └─ config.py                     # Pydantic-Config-System
│  │
│  ├─ data/
│  │  ├─ __init__.py
│  │  └─ kraken.py                     # OHLCV-Fetch + Parquet-Cache
│  │
│  ├─ strategies/
│  │  ├─ __init__.py
│  │  └─ ma_crossover.py               # Moving-Average-Crossover
│  │
│  ├─ risk/
│  │  ├─ __init__.py
│  │  └─ position_sizer.py             # Position Sizing (Risk-per-Trade)
│  │
│  ├─ backtest/
│  │  ├─ __init__.py
│  │  ├─ engine.py                     # Backtest-Engine (2 Modi)
│  │  └─ stats.py                      # Sharpe, MaxDD, Trade-Stats
│  │
│  ├─ features/                        # Future: ECM-Indikatoren
│  │  └─ __init__.py
│  │
│  └─ theory/                          # Future: GBM, Heston, etc.
│     └─ __init__.py
│
├─ scripts/
│  ├─ run_ma_realistic.py              # Realistic-Backtest-Runner
│  └─ run_ma_vectorized.py             # Vectorized (schnell, ungenau)
│
└─ tests/
   ├─ test_backtest_dummy.py
   └─ test_stats_dummy.py
```

---

## ⚙️ Zentrale Konfiguration (config.toml)

```toml
[backtest]
initial_cash = 10000.0
results_dir = "results"

[risk]
risk_per_trade = 0.01          # 1% pro Trade
max_daily_loss = 0.03          # 3% Kill-Switch
max_positions = 2              # Max. parallele Positionen
max_position_size = 0.25       # Max. 25% in einer Position
min_position_value = 50.0      # Min. 50 USD pro Position

[data]
default_timeframe = "1h"
data_dir = "data"

[strategy.ma_crossover]
fast_period = 10
slow_period = 30
stop_pct = 0.02                # 2% Stop-Loss
```

---

## 🔧 Kern-Module im Detail

### 1. src/core/config.py

**Pydantic-basiertes Config-System**

```python
from pydantic import BaseModel, Field
from pathlib import Path
import toml

class BacktestConfig(BaseModel):
    initial_cash: float = Field(gt=0)
    results_dir: Path

class RiskConfig(BaseModel):
    risk_per_trade: float = Field(default=0.01, gt=0, le=0.05)
    max_daily_loss: float = Field(default=0.03, gt=0, le=0.10)
    max_positions: int = Field(default=2, ge=1)
    max_position_size: float = Field(default=0.25, gt=0, le=0.50)
    min_position_value: float = Field(default=50.0, gt=0)

class DataConfig(BaseModel):
    default_timeframe: str = "1h"
    data_dir: Path = Path("data")

class Settings(BaseModel):
    backtest: BacktestConfig
    risk: RiskConfig
    data: DataConfig
    strategy: dict = {}

def load_config(path: Path = Path("config.toml")) -> Settings:
    raw = toml.load(path)
    return Settings(**raw)

def get_config() -> Settings:
    """Singleton-Pattern für globale Config."""
    global _config
    if _config is None:
        _config = load_config()
    return _config
```

**Key Features:**
- Automatische Validierung (Pydantic)
- Immutable (frozen=True möglich)
- Type-Safe
- Zentrale Parameter-Verwaltung

---

### 2. src/risk/position_sizer.py

**Position Sizing basierend auf Risk-per-Trade**

```python
from dataclasses import dataclass

@dataclass
class PositionRequest:
    equity: float           # Aktuelles Kontovermögen
    entry_price: float      # Geplanter Entry
    stop_price: float       # Stop-Loss-Preis
    risk_per_trade: float   # z.B. 0.01 = 1%

@dataclass
class PositionResult:
    size: float                    # Anzahl Units (z.B. BTC)
    value: float                   # Positionswert USD
    risk_amount: float             # Risikobetrag USD
    risk_percent: float            # Risiko in %
    stop_distance_percent: float   # Stop-Distanz %
    rejected: bool = False
    reason: str = ""

def calc_position_size(
    req: PositionRequest,
    max_position_pct: float = 0.25,
    min_position_value: float = 50.0,
    min_stop_distance: float = 0.005
) -> PositionResult:
    """
    Berechnet Positionsgröße so, dass maximal
    risk_per_trade * equity bis zum Stop verloren wird.
    
    Formel:
        risk_amount = equity * risk_per_trade
        size = risk_amount / |entry_price - stop_price|
    
    Validierungen:
    - Stop muss unter Entry liegen (Long)
    - Stop-Distanz >= 0.5%
    - Position <= max_position_pct
    - Position >= min_position_value
    """
    # Implementierung siehe vorherige Messages
```

**Key Features:**
- Risk-basierte Berechnung
- Multiple Safety-Checks
- Klare Rejection-Gründe
- Konfigurierbare Limits

---

### 3. src/data/kraken.py

**Kraken-OHLCV-Integration mit Caching**

```python
import ccxt
import pandas as pd
from pathlib import Path

def get_kraken_client() -> ccxt.kraken:
    """Erstellt Kraken-Client mit Config-Parametern."""
    cfg = load_config()
    return ccxt.kraken({
        "enableRateLimit": True,
        "rateLimit": 1000,
        "options": {"defaultType": "spot"}
    })

def fetch_ohlcv_df(
    symbol: str,
    timeframe: str = "1h",
    limit: int = 720,
    since_ms: Optional[int] = None,
    use_cache: bool = True
) -> pd.DataFrame:
    """
    Holt OHLCV-Daten von Kraken.
    
    Returns:
        DataFrame mit UTC-DatetimeIndex
        Spalten: [open, high, low, close, volume]
    
    Features:
    - Parquet-Caching für schnellere Wiederholungen
    - Automatisches Error-Handling
    - Logging
    """
    # Implementierung siehe vorherige Messages

def clear_cache(symbol: Optional[str] = None, timeframe: Optional[str] = None):
    """Löscht Cache-Dateien."""
```

**Key Features:**
- Parquet-Caching (schnell!)
- Kraken-API-Integration (ccxt)
- UTC-DatetimeIndex
- Error-Handling

---

### 4. src/backtest/engine.py

**Backtest-Engine mit 2 Modi**

#### Mode 1: Realistic (FÜR LIVE-TRADING-ENTSCHEIDUNGEN!)

```python
class BacktestEngine:
    def run_realistic(
        self,
        df: pd.DataFrame,
        strategy_name: str = "ma_crossover",
        save_results: bool = True
    ) -> BacktestResult:
        """
        Bar-für-Bar mit echtem Risk-Management.
        
        Execution-Loop:
        1. STOP-LOSS CHECK (vor allem!)
        2. Mark-to-Market (Unrealized PnL)
        3. Signal-Handling (Entry/Exit)
        4. Position Size Calculation (Risk-Layer)
        5. Equity-Tracking
        """
        # Implementierung siehe vorherige Messages
```

**Features:**
- Position Sizing (Risk-basiert)
- Stop-Loss-Überwachung (Bar-für-Bar)
- Echte Trade-Objekte
- Realistische PnL-Berechnung

#### Mode 2: Vectorized (NUR FÜR SCHNELLE TESTS!)

```python
def run_vectorized(self, df: pd.DataFrame) -> BacktestResult:
    """
    ⚠️ WARNUNG: Kein Risk-Management! Immer 100% investiert!
    
    Nur für:
    - Schnelle Experimente
    - Parameter-Grids
    - NICHT für Live-Trading-Entscheidungen!
    """
```

---

### 5. src/backtest/stats.py

**Performance-Metriken**

```python
def compute_basic_stats(equity: pd.Series) -> dict:
    """Total Return + Max Drawdown."""
    return {
        "total_return": float(end / start - 1),
        "max_drawdown": float((equity / equity.cummax() - 1).min())
    }

def compute_sharpe_ratio(equity: pd.Series, periods_per_year: int) -> float:
    """Annualisierte Sharpe Ratio."""
    returns = equity.pct_change().dropna()
    mean_return = returns.mean() * periods_per_year
    std_return = returns.std() * sqrt(periods_per_year)
    return (mean_return - risk_free_rate) / std_return

def compute_trade_stats(trades_df: pd.DataFrame) -> dict:
    """Win Rate, Profit Factor, Avg Win/Loss, etc."""
    wins = trades_df[trades_df["pnl"] > 0]
    losses = trades_df[trades_df["pnl"] < 0]
    
    return {
        "total_trades": len(trades_df),
        "win_rate": len(wins) / len(trades_df),
        "profit_factor": wins["pnl"].sum() / abs(losses["pnl"].sum()),
        "avg_win": wins["pnl"].mean(),
        "avg_loss": losses["pnl"].mean(),
        # ...
    }

def validate_for_live_trading(stats: dict) -> tuple[bool, list[str]]:
    """
    Prüft, ob Strategie für Live-Trading bereit ist.
    
    Mindestanforderungen:
    - Sharpe Ratio >= 1.5
    - Max Drawdown <= -15%
    - Min. 50 Trades
    - Profit Factor >= 1.3
    """
```

**Metriken:**
- **Equity-basiert:** Total Return, Max Drawdown, Sharpe, Sortino, Calmar
- **Trade-basiert:** Win Rate, Profit Factor, Expectancy, Avg Win/Loss

---

### 6. src/strategies/ma_crossover.py

**Beispiel-Strategie: Moving-Average-Crossover**

```python
def generate_signals(df: pd.DataFrame, params: dict) -> pd.Series:
    """
    Generiert Handelssignale basierend auf MA-Crossover.
    
    Returns:
        Series mit Werten:
        - 0 = neutral/flat
        - 1 = long
        - -1 = short (future)
    """
    fast = df["close"].rolling(params["fast_period"]).mean()
    slow = df["close"].rolling(params["slow_period"]).mean()
    
    signals = pd.Series(0, index=df.index)
    signals[fast > slow] = 1
    
    return signals
```

---

## 🚀 Quick Start

### 1. Setup

```bash
cd ~/Peak_Trade

# Virtual Environment
source .venv/bin/activate

# Dependencies
pip install -r requirements.txt
```

### 2. Erster Backtest (Dummy-Daten)

```bash
python scripts/run_ma_realistic.py
```

**Ausgabe:**

```
======================================================================
BACKTEST PERFORMANCE REPORT
======================================================================

📊 EQUITY METRIKEN
----------------------------------------------------------------------
Start Equity:      $10,000.00
End Equity:        $10,543.21
Total Return:         5.43%
Max Drawdown:        -8.23%

📈 RISK-ADJUSTED METRIKEN
----------------------------------------------------------------------
Sharpe Ratio:         1.23
Calmar Ratio:         0.66

🎯 TRADE STATISTIKEN
----------------------------------------------------------------------
Total Trades:           23
Winning Trades:         14
Win Rate:            60.87%
Profit Factor:        2.34

🔒 LIVE-TRADING-VALIDIERUNG
----------------------------------------------------------------------
❌ STRATEGIE NICHT FREIGEGEBEN:
  1. Nur 23 Trades < 50 (zu wenig statistische Signifikanz)
```

### 3. Mit echten Kraken-Daten

```bash
python scripts/run_ma_realistic.py --source kraken:BTC/USD:1h:720
```

---

## 🔒 Risk-Management-Philosophie

### Mindestanforderungen für Live-Trading

```python
MIN_SHARPE = 1.5              # Sharpe Ratio >= 1.5
MAX_DRAWDOWN = -15.0%         # Max DD <= 15%
MIN_TRADES = 50               # Mind. 50 Trades
MIN_PROFIT_FACTOR = 1.3       # PF >= 1.3
MIN_BACKTEST_PERIOD = 6 Monate
```

**Ohne diese Werte: KEIN Live-Trading!**

### Position-Sizing-Formel

```python
# Maximales Risiko pro Trade
risk_amount = equity * risk_per_trade  # z.B. 10000 * 0.01 = 100 USD

# Stop-Distanz
stop_distance = entry_price - stop_price  # z.B. 50000 - 48000 = 2000

# Position Size
size = risk_amount / stop_distance  # 100 / 2000 = 0.05 BTC
```

**Constraints:**
- Position <= 25% des Kontos
- Position >= 50 USD
- Stop-Distanz >= 0.5%

---

## 🧪 Testing

```bash
# Alle Tests
pytest tests/

# Mit Coverage
pytest --cov=src tests/

# Einzelner Test
pytest tests/test_backtest_dummy.py -v
```

---

## 📊 Typischer Workflow

### 1. Strategie entwickeln

```python
# src/strategies/my_strategy.py
def generate_signals(df: pd.DataFrame, params: dict) -> pd.Series:
    # Implementierung
    return signals
```

### 2. Config ergänzen

```toml
[strategy.my_strategy]
param1 = 10
param2 = 20
stop_pct = 0.02
```

### 3. Backtest durchführen

```bash
python scripts/run_ma_realistic.py --strategy my_strategy
```

### 4. Performance analysieren

```python
from src.backtest.stats import validate_for_live_trading

passed, warnings = validate_for_live_trading(result.stats)

if not passed:
    print("Strategie noch nicht bereit:")
    for w in warnings:
        print(f"  - {w}")
```

### 5. Iterieren

- Parameter anpassen
- Stop-Loss optimieren
- Mehr Daten testen
- Wiederhole Backtest

---

## 🎯 Wichtige Konzepte

### 1. Realistic vs. Vectorized

| Feature | Realistic | Vectorized |
|---------|-----------|------------|
| **Risk-Management** | ✅ Position Sizing | ❌ Immer 100% |
| **Stop-Loss** | ✅ Bar-für-Bar | ❌ Kein Stop |
| **Trade-Objekte** | ✅ Echte Trades | ❌ Synthetisch |
| **Use Case** | **Live-Entscheidungen** | Schnelle Tests |
| **Geschwindigkeit** | Langsam | Schnell |

**REGEL: Für Live-Trading-Entscheidungen IMMER Realistic Mode verwenden!**

### 2. Position Sizing Flow

```
Entry-Signal erkannt
        ↓
Risk berechnen: equity * risk_per_trade (z.B. 100 USD)
        ↓
Stop-Distanz: entry - stop (z.B. 2000 USD)
        ↓
Size berechnen: risk / distance (z.B. 0.05 BTC)
        ↓
Validierung:
├─ Size <= 25% des Kontos? ✓
├─ Value >= 50 USD? ✓
└─ Stop-Distanz >= 0.5%? ✓
        ↓
Position wird eröffnet
```

### 3. Stop-Loss-Überwachung

```python
# In jedem Bar:
if position_size > 0 and bar["low"] <= stop_price:
    # Exit zu Stop-Preis (konservativ!)
    pnl = position_size * (stop_price - entry_price)
    equity += pnl
    position_size = 0
```

---

## 🤖 LLM-Prompt für neue Chats

**Verwende diesen Prompt, wenn du einen neuen Chat startest:**

```
Du bist mein Lead Engineer für das Projekt „Peak_Trade": 
ein KI-unterstütztes, risikokontrolliertes Trading-Framework.

WICHTIGE REGELN:
- Antworte IMMER auf Deutsch
- Risk-First-Ansatz: Erst Sicherheit, dann Performance
- Nutze bestehendes Config-System (Pydantic, config.toml)
- Code mit Type Hints + Docstrings
- Bei Trading-Code: Klar markieren ob Backtest oder Live

PROJEKTSTRUKTUR:
- src/core/config.py – Pydantic-Config
- src/data/kraken.py – OHLCV-Daten + Caching
- src/risk/position_sizer.py – Position Sizing
- src/backtest/engine.py – Backtest-Engine (Realistic/Vectorized)
- src/backtest/stats.py – Performance-Metriken
- src/strategies/ma_crossover.py – Beispiel-Strategie

TECH-STACK:
Python, Pandas, ccxt, Pydantic, Parquet-Caching

RISK-MANAGEMENT-PHILOSOPHIE:
- Max 1% Risk pro Trade
- Stop-Loss immer gesetzt
- Position Size niemals > 25% des Kontos
- Min. 50 Trades im Backtest vor Live-Trading
- Sharpe >= 1.5, Max DD <= -15% für Live-Freigabe

Lies bitte die Zusammenfassung in dieser Datei für Details.
```

---

## 📚 Wichtige Dateien

### Existierende Docs
- `docs/architecture.md` – Detaillierte Architektur
- `docs/llm_workflows.md` – LLM-Prompts für verschiedene Tasks
- `docs/armstrong_notes.md` – Economic Confidence Model
- `docs/trading_bot_notes.md` – Trading-Konzepte
- `docs/Peak_Trade_setup_notes.md` – Setup-Notizen

### Code-Hauptdateien
- `src/core/config.py` – Config-System
- `src/risk/position_sizer.py` – Position Sizing
- `src/backtest/engine.py` – Backtest-Engine
- `src/backtest/stats.py` – Performance-Stats
- `src/data/kraken.py` – Daten-Integration

---

## 🚧 Roadmap

### ✅ Implementiert
- Config-System (Pydantic)
- Risk-Management (Position Sizing)
- Backtest-Engine (Realistic + Vectorized)
- Performance-Stats (Sharpe, MaxDD, etc.)
- Kraken-Integration
- MA-Crossover-Strategie

### 🚧 In Entwicklung
- Daily-Loss-Tracker (Kill-Switch)
- Parameter-Optimization
- Visualisierung (Equity-Curve, Drawdown-Charts)

### 📅 Geplant
- Armstrong-ECM-Integration
- Multi-Strategy-Portfolio
- Walk-Forward-Analysis
- Paper-Trading (Testnet)
- Live-Execution (nach 6+ Monaten Paper-Trading!)

---

## ⚠️ Kritische Erinnerungen

1. **NIEMALS Live-Trading ohne:**
   - Min. 6 Monate Backtests
   - Sharpe >= 1.5
   - Max DD <= -15%
   - Min. 50 Trades
   - Profit Factor >= 1.3

2. **Position Sizing ist NICHT optional**
   - Immer calc_position_size() verwenden
   - Niemals manuell "all-in" gehen

3. **Stop-Loss ist PFLICHT**
   - Jeder Trade braucht Stop-Loss
   - Stop wird Bar-für-Bar gecheckt

4. **Realistic Mode für finale Entscheidungen**
   - Vectorized nur für schnelle Tests
   - Niemals Vectorized-Stats für Live-Entscheidungen verwenden

5. **Secrets NIEMALS ins Repo**
   - API-Keys nur in .env oder Umgebungsvariablen
   - .gitignore ist aktiv

---

## 📞 Support

Bei Problemen:
1. Prüfe `docs/architecture.md`
2. Verwende `docs/llm_workflows.md` für LLM-Prompts
3. Führe Tests aus: `pytest tests/ -v`

---

**Erstellt:** Dezember 2024  
**Maintainer:** Peak_Trade Team  
**Status:** In aktiver Entwicklung (Backtest-Phase)

---

## ⚖️ Disclaimer

**WICHTIG:** Dieses Projekt dient ausschließlich zu Bildungs- und Forschungszwecken.

Trading birgt erhebliche Risiken. Es gibt keine Garantie für Profitabilität.

**Verwende niemals Kapital, dessen Verlust du dir nicht leisten kannst.**

Alle Trading-Entscheidungen erfolgen auf eigene Verantwortung.

---

**Built with ❤️ and strict risk management**
