# Peak_Trade

Ein modularer Trading- und Backtest-Stack mit Fokus auf:

- saubere Daten-Pipeline (Kraken & Co.),
- robuste Backtest-Engine,
- klar definierte Risk Management,
- gut strukturierte, wartbare Dokumentation.

Aktueller Stand: **Phase 1 + Phase 2 abgeschlossen**
– Data Layer, Backtest Engine und Risk Layer sind implementiert und produktionsreif vorbereitet.

---

## ⚠️ Disclaimer

**WICHTIG:** Dieses Projekt dient ausschließlich zu Bildungs- und Forschungszwecken.

Trading birgt erhebliche Risiken. Es gibt keine Garantie für Profitabilität.

**Verwende niemals Kapital, dessen Verlust du dir nicht leisten kannst.**

Alle Trading-Entscheidungen erfolgen auf eigene Verantwortung.

---

## 1. Features & Architektur

Peak_Trade ist in mehrere klar getrennte Bereiche gegliedert:

### Data Layer
- Laden von Marktdaten (z.B. über Kraken-API oder CSV)
- Normalisierung & Caching (Parquet, Wiederverwendbarkeit)
- Einstiegspunkte: `src/data/…`, Demos in `scripts/`

### Strategy Layer
- Strategien greifen auf normalisierte Daten zu
- 6 professionelle Strategien implementiert (MA Crossover, Momentum, MACD, RSI, Bollinger Bands, ECM)
- Beispielstrategien und Backtest-Szenarien (erweiterbar)

### Risk Layer
- Zentrale Risikoparameter in `config/config.toml` (`[risk]`)
- Globale Limits (Daily Loss, Drawdown, Exposure, Kill-Switch)
- Position Sizing inkl. optionaler Kelly-Logik
- Kernmodule:
  - `src/risk/limits.py`
  - `src/risk/position_sizer.py`

### Backtest Engine
- Simuliert Strategien auf Historien-Daten
- Berücksichtigt Fees, Slippage, Positionslogik, Risk-Limits
- Realistic Mode (produktionsreif) vs. Vectorized Mode (schnelle Tests)
- Kernmodul: `src/backtest/engine.py`

### Dokumentation & Projektorganisation
- Zentrale Doku in `docs/project_docs/`
- Technische Reports & Dashboards in `docs/reports/`
- Archivierte Stände & Imports in `archive/`

**Ausführliche Dokumentation:**
- `docs/project_docs/IMPLEMENTATION_SUMMARY.md`
- `docs/project_docs/CONFIG_SYSTEM.md`
- `docs/project_docs/RISK_MANAGEMENT.md`

---

## 2. Projektstruktur

Die wichtigsten Teile der Projektstruktur:

```text
Peak_Trade/
├─ README.md
├─ pyproject.toml
├─ requirements.txt
├─ .gitignore
├─ config/
│  └─ config.toml
├─ src/
│  ├─ core/              # Config-System (Pydantic)
│  ├─ data/              # Datenbeschaffung & Caching
│  ├─ risk/              # Risk-Management
│  ├─ backtest/          # Backtest-Engine
│  ├─ strategies/        # Trading-Strategien
│  ├─ portfolio/         # Portfolio-Manager
│  └─ theory/            # Quant-Finance-Modelle
├─ scripts/
│  ├─ demo_complete_pipeline.py
│  ├─ demo_risk_limits.py
│  ├─ demo_kraken_simple.py
│  ├─ run_ma_realistic.py
│  └─ debug_signals.py
├─ tests/
├─ data/                 # NICHT ins Repo!
├─ results/              # NICHT ins Repo!
├─ docs/
│  ├─ architecture/
│  │  └─ architecture_diagram.png
│  ├─ reports/
│  │  ├─ peak_trade_documentation.pdf
│  │  ├─ PeakTrade_enhanced.pdf
│  │  └─ dashboard.html
│  └─ project_docs/
│     ├─ CHANGELOG.md
│     ├─ RISK_MANAGEMENT.md
│     ├─ CLAUDE_NOTES.md
│     ├─ FINAL_SUMMARY.md
│     ├─ IMPLEMENTATION_SUMMARY.md
│     ├─ CONFIG_SYSTEM.md
│     ├─ RISK_LIMITS_UPDATE.md
│     └─ NEXT_STEPS.md
└─ archive/
   ├─ PeakTradeRepo/
   ├─ noch_einordnen/
   └─ full_files_stand_02.12.2025
```

---

## 3. Quick Start

### Installation

```bash
cd ~/Peak_Trade

# Virtual Environment anlegen
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Dependencies installieren
pip install -r requirements.txt
```

### Konfiguration testen

```bash
# Config-System validieren
python -c "from src.core import get_config; cfg = get_config(); print(f'Risk per Trade: {cfg.risk.risk_per_trade}')"
```

**Erwartete Ausgabe:** `Risk per Trade: 0.01`

### Demo-Scripts ausführen

```bash
# Komplette Pipeline (Data + Risk + Backtest)
python scripts/demo_complete_pipeline.py

# Risk-Limits Demo
python scripts/demo_risk_limits.py

# Kraken-Datenpipeline Demo
python scripts/demo_kraken_simple.py

# Single Strategy Backtest
python scripts/run_ma_realistic.py
```

---

## 4. Konfiguration (config/config.toml)

### Risk-Management (KRITISCH!)

```toml
[risk]
# Position Sizing
position_sizing_method = "fixed_fractional"  # oder "kelly"
risk_per_trade = 0.01                        # 1% Risiko pro Trade
max_position_size = 0.25                     # 25% max. Position
min_position_value = 50.0                    # Min. $50 Position
min_stop_distance = 0.005                    # Min. 0.5% Stop
kelly_scaling = 0.5                          # Half-Kelly (konservativ)

# Portfolio Risk Limits
max_daily_loss = 0.03        # 3% Kill-Switch
max_drawdown = 0.20          # 20% Max. Drawdown
max_positions = 2            # Max. 2 parallele Positionen
max_total_exposure = 0.75    # 75% Max. Exposure
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

**Mehr Details:** `docs/project_docs/CONFIG_SYSTEM.md`

---

## 5. Risk-Management-Philosophie

### Mindestanforderungen für Live-Trading

**OHNE diese Werte: KEIN Live-Trading!**

```toml
[validation]
min_sharpe = 1.5              # Sharpe Ratio >= 1.5
max_drawdown = -0.15          # Max DD <= 15%
min_trades = 50               # Mind. 50 Trades im Backtest
min_profit_factor = 1.3       # PF >= 1.3
min_backtest_months = 6       # Mind. 6 Monate Backtest
```

### Position-Sizing-Formel (Fixed Fractional)

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

**Mehr Details:** `docs/project_docs/RISK_MANAGEMENT.md`

---

## 6. Verfügbare Strategien

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
python -c "from src.strategies import list_strategies; print(list_strategies())"
```

---

## 7. Testing

```bash
# Alle Tests
pytest tests/

# Mit Coverage
pytest --cov=src tests/

# Einzelner Test
pytest tests/test_basics.py -v
```

---

## 8. Typischer Workflow

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

## 9. Wichtige Konzepte

### Realistic vs. Vectorized Backtest

| Feature | Realistic | Vectorized |
|---------|-----------|------------|
| **Risk-Management** | ✅ Position Sizing | ❌ Immer 100% |
| **Stop-Loss** | ✅ Bar-für-Bar | ❌ Kein Stop |
| **Trade-Objekte** | ✅ Echte Trades | ❌ Synthetisch |
| **Use Case** | **Live-Entscheidungen** | Schnelle Tests |
| **Geschwindigkeit** | Langsam | Schnell |

**REGEL: Für Live-Trading-Entscheidungen IMMER Realistic Mode verwenden!**

### Risk Profiles

Peak_Trade bietet drei vordefinierte Risk-Profile:

- **Conservative**: Anfänger, kleine Accounts (< $5k)
- **Moderate**: Intermediate, Accounts > $5k
- **Aggressive**: Profis, große Accounts (> $50k)

Details: `docs/project_docs/RISK_MANAGEMENT.md` Abschnitt 9

---

## 10. Dokumentation

### Projekt-Dokumentation
- `docs/project_docs/CHANGELOG.md` - Änderungshistorie
- `docs/project_docs/RISK_MANAGEMENT.md` - Risk-Management-System
- `docs/project_docs/IMPLEMENTATION_SUMMARY.md` - Implementierungsdetails
- `docs/project_docs/CONFIG_SYSTEM.md` - Konfigurationssystem
- `docs/project_docs/CLAUDE_NOTES.md` - AI Session Log

### Reports & Visualisierungen
- `docs/reports/peak_trade_documentation.pdf` - Vollständige Doku
- `docs/reports/dashboard.html` - Interaktives Dashboard
- `docs/architecture/architecture_diagram.png` - Architektur-Diagramm

---

## 11. Sicherheit

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

## 12. Roadmap

### ✅ Phase 1 + 2 (Abgeschlossen)
- Config-System (Pydantic)
- Risk-Management (Position Sizing + Kelly)
- Backtest-Engine (Realistic + Vectorized)
- Kraken-Integration
- 6 Trading-Strategien
- Portfolio-Manager
- Umfassende Dokumentation

### 🚧 Phase 3 (In Planung)
- Erweiterte Portfolio-Metriken (Sharpe, Sortino, Calmar)
- Dynamische Risk-Adjustierung basierend auf Volatilität
- Multi-Asset Position Sizing mit Korrelation
- Alert-System (E-Mail, Slack) bei Limit-Verletzungen

### 📅 Langfristig
- Parameter-Optimization (Walk-Forward)
- Machine-Learning-basierte Risk-Modelle
- Real-time Risk Dashboard
- Paper-Trading (Testnet)
- Live-Execution (nach 6+ Monaten Paper-Trading!)

**Details:** `docs/project_docs/NEXT_STEPS.md`

---

## 13. Tech-Stack

- **Python 3.11+** – Basis
- **Pandas & NumPy** – Datenverarbeitung
- **Pydantic** – Config-Validierung
- **ccxt** – Exchange-APIs (Kraken)
- **PyArrow** – Parquet-Caching
- **pytest** – Testing

---

## 14. Support & Entwicklung

### Bei Problemen:
1. Prüfe `docs/project_docs/IMPLEMENTATION_SUMMARY.md`
2. Führe Tests aus: `pytest tests/ -v`
3. Nutze Demo-Scripts zum Debugging

### Entwicklung:
- Python >= 3.11
- Type Hints in allen Modulen
- Docstrings (Deutsch bevorzugt)
- Tests für neue Features

---

**Built with ❤️ and strict risk management**

**Erstellt:** Dezember 2024
**Letztes Update:** 2025-12-02
**Status:** Phase 1 + 2 abgeschlossen, produktionsreif für Backtesting
