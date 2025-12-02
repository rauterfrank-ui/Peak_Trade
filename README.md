# Peak_Trade

**KI-unterstütztes, risikokontrolliertes Trading-Framework**

Peak_Trade ist ein Research- und Trading-Framework mit Fokus auf:
- Systematische Backtests auf OHLCV-Daten
- Sauberes Risk-Management (Risk-per-Trade, Stops, Drawdowns)
- Klare Trennung von Daten, Strategien, Backtest, Theorie (Quant-Finance)
- Erweiterbarkeit für Makro-/ECM-Overlay und Modellwelt (à la El Karoui)

---

## ⚠️ Disclaimer

**WICHTIG:** Dieses Projekt dient ausschließlich zu Bildungs- und Forschungszwecken.

Trading birgt erhebliche Risiken. Es gibt keine Garantie für Profitabilität.

**Verwende niemals Kapital, dessen Verlust du dir nicht leisten kannst.**

Alle Trading-Entscheidungen erfolgen auf eigene Verantwortung.

---

## 🚀 Quick Start

### 1. Installation

```bash
cd ~/Peak_Trade

# Virtual Environment anlegen
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Dependencies installieren
pip install -r requirements.txt
```

### 2. Konfiguration testen

```bash
# Config-System validieren
python -c "from src.core import get_config; cfg = get_config(); print(f'Risk per Trade: {cfg.risk.risk_per_trade}')"
```

**Erwartete Ausgabe:** `Risk per Trade: 0.01`

### 3. Backtest durchführen

```bash
# Single Strategy
python scripts/run_ma_realistic.py

# Multi-Strategy Portfolio (6 Strategien)
python scripts/run_full_portfolio.py
```

---

## 📁 Projektstruktur

```
Peak_Trade/
├── config.toml                    # Zentrale Konfiguration
├── requirements.txt               # Python-Dependencies
├── .gitignore                     # Schützt Secrets & Daten
├── README.md
│
├── src/
│   ├── core/                      # Config-System (Pydantic)
│   │   ├── __init__.py
│   │   └── config.py
│   │
│   ├── data/                      # Datenbeschaffung & Caching
│   │   ├── __init__.py
│   │   └── kraken.py              # OHLCV von Kraken
│   │
│   ├── strategies/                # Trading-Strategien
│   │   ├── __init__.py
│   │   └── ma_crossover.py        # Moving Average Crossover
│   │
│   ├── risk/                      # Risk-Management
│   │   ├── __init__.py
│   │   └── position_sizer.py      # Position Sizing
│   │
│   ├── backtest/                  # Backtest-Engine
│   │   ├── __init__.py
│   │   ├── engine.py              # Realistic & Vectorized
│   │   └── stats.py               # Performance-Metriken
│   │
│   ├── features/                  # Feature-Engineering (ECM)
│   │   └── __init__.py
│   │
│   └── theory/                    # Quant-Finance-Modelle
│       └── __init__.py
│
├── scripts/                       # Backtest-Runner
│   ├── run_ma_realistic.py
│   └── run_ma_vectorized.py
│
├── tests/                         # Unit & Integration Tests
│   ├── test_backtest_dummy.py
│   └── test_stats_dummy.py
│
├── data/                          # NICHT ins Repo!
│   └── raw/
│
└── results/                       # NICHT ins Repo!
    ├── backtests/
    └── reports/
```

---

## ⚙️ Konfiguration (config.toml)

### Risk-Management (KRITISCH!)

```toml
[risk]
risk_per_trade = 0.01          # Max. 1% Risiko pro Trade
max_daily_loss = 0.03          # 3% Kill-Switch
max_positions = 2              # Max. parallele Positionen
max_position_size = 0.25       # Max. 25% in einer Position
min_position_value = 50.0      # Min. 50 USD pro Trade
min_stop_distance = 0.005      # Min. 0.5% Stop-Distanz
```

**NIEMALS diese Werte erhöhen ohne gründliche Backtests!**

### Backtest-Einstellungen

```toml
[backtest]
initial_cash = 10000.0         # Startkapital
results_dir = "results"        # Output-Verzeichnis
```

### Strategie-Parameter

```toml
[strategy.ma_crossover]
fast_period = 10               # Schneller Moving Average
slow_period = 30               # Langsamer Moving Average
stop_pct = 0.02                # 2% Stop-Loss
```

---

## 🔒 Risk-Management-Philosophie

### Mindestanforderungen für Live-Trading

**OHNE diese Werte: KEIN Live-Trading!**

```python
MIN_SHARPE = 1.5              # Sharpe Ratio >= 1.5
MAX_DRAWDOWN = -15.0%         # Max DD <= 15%
MIN_TRADES = 50               # Mind. 50 Trades im Backtest
MIN_PROFIT_FACTOR = 1.3       # PF >= 1.3
MIN_BACKTEST_PERIOD = 6 Monate
```

### Position-Sizing-Formel

```python
# Maximales Risiko pro Trade
risk_amount = equity * risk_per_trade  # z.B. 10000 * 0.01 = 100 USD

# Stop-Distanz
stop_distance = entry_price - stop_price  # z.B. 50000 - 49000 = 1000

# Position Size
size = risk_amount / stop_distance  # 100 / 1000 = 0.1 BTC
```

**Constraints:**
- Position <= 25% des Kontos
- Position >= 50 USD
- Stop-Distanz >= 0.5%

---

## 📊 Verfügbare Strategien

Peak_Trade enthält **6 professionelle Trading-Strategien**:

### Trend-Following
1. **MA Crossover** - Moving Average Crossover (klassisch)
2. **Momentum** - Momentum-basiert (Kursänderung über N Perioden)
3. **MACD** - Moving Average Convergence Divergence

### Mean-Reversion
4. **RSI** - Relative Strength Index (Oversold/Overbought)
5. **Bollinger Bands** - Volatilitäts-basierte Mean-Reversion

### Cycle-Based
6. **ECM** - Economic Confidence Model (Armstrong's 8.6-Jahr-Zyklus)

**Portfolio-Mode:** Alle Strategien können parallel in einem Portfolio laufen!

```bash
# Alle Strategien auflisten
python -c "from src.core import list_strategies; print(list_strategies())"
```

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
import pandas as pd

def generate_signals(df: pd.DataFrame, params: dict) -> pd.Series:
    """
    Generiert Trading-Signale.
    
    Args:
        df: OHLCV-DataFrame mit DatetimeIndex
        params: Strategy-Parameter aus config.toml
        
    Returns:
        Series mit Werten: 1 (Long), 0 (Neutral), -1 (Short)
    """
    # Implementierung hier
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

---

## 🎯 Wichtige Konzepte

### Realistic vs. Vectorized Backtest

| Feature | Realistic | Vectorized |
|---------|-----------|------------|
| **Risk-Management** | ✅ Position Sizing | ❌ Immer 100% |
| **Stop-Loss** | ✅ Bar-für-Bar | ❌ Kein Stop |
| **Trade-Objekte** | ✅ Echte Trades | ❌ Synthetisch |
| **Use Case** | **Live-Entscheidungen** | Schnelle Tests |
| **Geschwindigkeit** | Langsam | Schnell |

**REGEL: Für Live-Trading-Entscheidungen IMMER Realistic Mode verwenden!**

---

## 🚧 Roadmap

### ✅ Implementiert
- Config-System (Pydantic)
- Risk-Management (Position Sizing)
- Projektstruktur

### 🚧 In Entwicklung
- Backtest-Engine (Realistic + Vectorized)
- Kraken-Integration
- MA-Crossover-Strategie
- Performance-Stats (Sharpe, MaxDD, etc.)

### 📅 Geplant
- Daily-Loss-Tracker (Kill-Switch)
- Parameter-Optimization
- Visualisierung (Equity-Curve, Drawdown-Charts)
- Armstrong-ECM-Integration
- Multi-Strategy-Portfolio
- Walk-Forward-Analysis
- Paper-Trading (Testnet)
- Live-Execution (nach 6+ Monaten Paper-Trading!)

---

## 📚 Dokumentation

- **`docs/architecture.md`** – Detaillierte Architektur
- **`docs/llm_workflows.md`** – LLM-Prompts für Tasks
- **`docs/armstrong_notes.md`** – Economic Confidence Model
- **`PEAK_TRADE_PROJECT_SUMMARY.md`** – Vollständige Projekt-Übersicht

---

## 🔐 Sicherheit

### API-Keys NIEMALS ins Repo!

```bash
# Erstelle .env-Datei (wird von .gitignore ausgeschlossen)
echo "KRAKEN_API_KEY=your_key_here" >> .env
echo "KRAKEN_API_SECRET=your_secret_here" >> .env
```

Die `.gitignore` schützt automatisch:
- `.env`-Dateien
- `data/`-Verzeichnis
- `results/`-Verzeichnis
- Alle `*_secret*` und `*_key*` Dateien

---

## 📞 Support & Entwicklung

### Bei Problemen:
1. Prüfe `docs/architecture.md`
2. Verwende `docs/llm_workflows.md` für LLM-Prompts
3. Führe Tests aus: `pytest tests/ -v`

### Entwicklung:
- Python >= 3.11
- Type Hints in allen Modulen
- Docstrings auf Deutsch
- Tests für neue Features

---

## 🛠️ Tech-Stack

- **Python 3.11+** – Basis
- **Pandas & NumPy** – Datenverarbeitung
- **Pydantic** – Config-Validierung
- **ccxt** – Exchange-APIs (Kraken)
- **PyArrow** – Parquet-Caching
- **pytest** – Testing

---

**Built with ❤️ and strict risk management**

**Erstellt:** Dezember 2024  
**Status:** In aktiver Entwicklung (Backtest-Phase)
