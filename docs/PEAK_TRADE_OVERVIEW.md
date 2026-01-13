# PEAK_TRADE – Architektur & Schnelleinstieg

> **Modulares Trading-Framework mit Safety-First-Ansatz**

---

## Architektur-Map

Peak_Trade folgt einer klaren Pipeline-Architektur mit strikter Separation of Concerns:

```text
┌─────────────────────────────────────────────────────────────┐
│                       PEAK_TRADE PIPELINE                    │
└─────────────────────────────────────────────────────────────┘

┌──────────┐      ┌──────────┐      ┌──────────┐      ┌──────────┐
│   DATA   │ ───▶ │ STRATEGY │ ───▶ │  SIZING  │ ───▶ │   RISK   │
│  FEEDS   │      │ SIGNALS  │      │ OVERLAY  │      │  LIMITS  │
└──────────┘      └──────────┘      └──────────┘      └──────────┘
     │                  │                  │                  │
     │                  │                  │                  │
     ▼                  ▼                  ▼                  ▼
┌──────────────────────────────────────────────────────────────┐
│                     BACKTEST ENGINE                          │
│  • Bar-für-Bar Execution (No Look-Ahead)                    │
│  • Portfolio State Management                               │
│  • Trade Tracking & PnL                                     │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│                        REPORTING                             │
│  • Performance-Metriken (Sharpe, Drawdown, ...)            │
│  • Equity Curves & Visualisierung                          │
│  • Research Reports (Walk-Forward, Monte-Carlo, ...)       │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│                   GOVERNANCE & LIVE TRACK                    │
│  • Go/No-Go-Decisions (Research-Pipeline)                  │
│  • Live-Session-Runner (Testnet & Production)              │
│  • Alerts, Monitoring, Operator-Console                    │
└──────────────────────────────────────────────────────────────┘
```

---

## Wie starte ich schnell einen Backtest?

### 1. Minimaler Backtest (Command-Line)

```bash
# Mit vorhandener Config
python scripts/run_strategy_from_config.py --strategy ma_crossover --symbol BTC/USDT

# Mit Custom-Config
python scripts/run_strategy_from_config.py --config config&#47;my_backtest.toml
```

### 2. Programmatischer Backtest (Python)

```python
from src.core.peak_config import load_config
from src.strategies.registry import create_strategy_from_config
from src.backtest.engine import BacktestEngine
from src.data.data_loader import load_ohlcv_data

# 1. Load Config
cfg = load_config("config/backtest_ma_crossover.toml")

# 2. Load Data
df = load_ohlcv_data(
    symbol=cfg.get("data.symbol", "BTC/USDT"),
    timeframe=cfg.get("data.timeframe", "1h"),
    start_date=cfg.get("data.start_date"),
    end_date=cfg.get("data.end_date")
)

# 3. Create Strategy from Registry
strategy = create_strategy_from_config("ma_crossover", cfg)

# 4. Run Backtest
engine = BacktestEngine.from_config(cfg)
result = engine.run_realistic(
    df=df,
    strategy_signal_fn=strategy.generate_signals,
    strategy_params={}
)

# 5. Analyze Results
print(f"Total Return: {result.total_return:.2%}")
print(f"Sharpe Ratio: {result.sharpe_ratio:.2f}")
print(f"Max Drawdown: {result.max_drawdown:.2%}")
```

### 3. Minimal Config-Beispiel

**`config&#47;my_backtest.toml`:**

```toml
[data]
symbol = "BTC/USDT"
timeframe = "1h"
start_date = "2024-01-01"
end_date = "2024-12-31"
exchange = "kraken"

[backtest]
initial_capital = 10000.0
position_fraction = 0.1  # 10% pro Trade

[strategy.ma_crossover]
fast_window = 20
slow_window = 50

[risk]
max_drawdown = 0.20
daily_loss_limit = 0.05
```

---

## Strategy Registry Keys

Alle verfügbaren Strategien sind in der **Strategy Registry** registriert (`src/strategies/registry.py`).

### Production-Ready Strategien

| Key | Beschreibung | Config Section |
|-----|-------------|----------------|
| `ma_crossover` | Moving Average Crossover | `strategy.ma_crossover` |
| `rsi_reversion` | RSI Mean-Reversion | `strategy.rsi_reversion` |
| `breakout_donchian` | Donchian Channel Breakout | `strategy.breakout_donchian` |
| `macd` | MACD Trend-Following | `strategy.macd` |
| `bollinger_bands` | Bollinger Bands Reversion | `strategy.bollinger_bands` |
| `momentum_1h` | Momentum-basierte Strategie | `strategy.momentum_1h` |
| `trend_following` | ADX Trend-Following | `strategy.trend_following` |
| `mean_reversion` | Z-Score Mean-Reversion | `strategy.mean_reversion` |

### Research-Track Strategien (R&D)

| Key | Beschreibung | Status |
|-----|-------------|--------|
| `armstrong_cycle` | Armstrong ECM Cycle Model | ✅ Live-Ready |
| `el_karoui_vol_model` | El Karoui Stochastic Vol | ✅ Live-Ready |
| `ehlers_cycle_filter` | Ehlers DSP Cycle Filter | 🔬 R&D-Only |
| `meta_labeling` | López de Prado Meta-Labeling | 🔬 R&D-Only |
| `bouchaud_microstructure` | Bouchaud Microstructure | 🔬 Skeleton |
| `vol_regime_overlay` | Gatheral/Cont Vol Overlay | 🔬 Skeleton |

**Hinweis:** R&D-Strategien benötigen `research.allow_r_and_d_strategies = true` in der Config.

---

## Sizing & Risk Config Sections

### Position Sizing

**`[sizing]` Section:**

```toml
[sizing]
type = "fixed_fraction"  # oder "fixed_size", "noop"
fraction = 0.1           # 10% des Kapitals pro Position
```

**Overlay Sizing (Erweitert):**

```toml
[sizing.overlay]
type = "vol_regime"
scaling_factors = {low = 1.5, medium = 1.0, high = 0.5}
```

### Risk Management

**`[risk]` Section:**

```toml
[risk]
type = "max_drawdown"      # oder "equity_floor", "noop"
max_drawdown = 0.20        # 20% Max Drawdown
equity_floor = 8000.0      # Absoluter Equity-Floor

# Erweitertes Risk Management
daily_loss_limit = 0.05    # 5% Tagesverlust-Limit
max_open_positions = 3     # Max 3 gleichzeitige Positionen
max_position_notional_pct = 0.3  # Max 30% Kapital pro Position
```

---

## Live-Track & Governance

### Go/No-Go Research-Pipeline

Vor einem Live-Deployment durchläuft jede Strategie eine systematische Prüfung:

1. **Backtest** – Historische Performance
2. **Walk-Forward** – Out-of-Sample-Validierung
3. **Monte-Carlo** – Robustheit gegen Zufall
4. **Stress-Tests** – Verhalten in Extremszenarien
5. **Shadow-Run** – Testnet-Monitoring (papier-basiert)
6. **Testnet-Run** – Echte Orders mit Testnet-Geld
7. **Production** – Live-Deployment mit Risk-Limits

**Dokumentation:**
- 📖 **Playbook:** [`docs/PLAYBOOK_RESEARCH_TO_LIVE_PORTFOLIOS.md`](PLAYBOOK_RESEARCH_TO_LIVE_PORTFOLIOS.md)
- 🎯 **Live-Track Demo:** [`docs/PHASE_84_LIVE_TRACK_DEMO_WALKTHROUGH.md`](PHASE_84_LIVE_TRACK_DEMO_WALKTHROUGH.md)

### Live-Ops Tools

```bash
# Live-Status abrufen
python -m src.cli.live_ops status

# Portfolio-Snapshot
python -m src.cli.live_ops portfolio

# Offene Orders
python -m src.cli.live_ops orders

# Health-Check
python -m src.cli.live_ops health
```

---

## Weitere Dokumentation

### Schnelleinstieg

- 🚀 **First 7 Days:** [`PEAK_TRADE_FIRST_7_DAYS.md`](PEAK_TRADE_FIRST_7_DAYS.md)
- 📖 **v1.0 Overview:** [`PEAK_TRADE_V1_OVERVIEW_FULL.md`](PEAK_TRADE_V1_OVERVIEW_FULL.md)

### Technische Guides

- 🏗️ **Architektur:** [`ARCHITECTURE.md`](ARCHITECTURE.md)
- 🔬 **Backtest Engine:** [`BACKTEST_ENGINE.md`](BACKTEST_ENGINE.md)
- 🎯 **Strategy Development:** [`STRATEGY_DEV_GUIDE.md`](STRATEGY_DEV_GUIDE.md)
- 🧪 **Research-Pipeline:** [`RESEARCH_PIPELINE_V2.md`](RESEARCH_PIPELINE_V2.md)

### Developer Guides

- ⚡ **Developer Workflow:** [`DEVELOPER_WORKFLOW_GUIDE.md`](DEVELOPER_WORKFLOW_GUIDE.md)
- 🤖 **AI-Helper Guide:** [`ai/PEAK_TRADE_AI_HELPER_GUIDE.md`](ai/PEAK_TRADE_AI_HELPER_GUIDE.md)
- 📚 **Knowledge Base Index:** [`KNOWLEDGE_BASE_INDEX.md`](KNOWLEDGE_BASE_INDEX.md)

### Operations & Safety

- 🛡️ **Risk Management:** [`RISK_MANAGEMENT_V1.md`](RISK_MANAGEMENT_V1.md)
- 🚨 **Incident Drills:** [`INCIDENT_SIMULATION_AND_DRILLS.md`](INCIDENT_SIMULATION_AND_DRILLS.md)
- 📊 **Monitoring & Alerts:** [`OBSERVABILITY_AND_MONITORING_PLAN.md`](OBSERVABILITY_AND_MONITORING_PLAN.md)
- 🔐 **Resilience Guide:** [`resilience_guide.md`](resilience_guide.md)

---

## Repository-Struktur

```text
Peak_Trade/
├── src/
│   ├── strategies/       # Strategy-Implementierungen
│   │   ├── registry.py   # Zentrale Strategy-Registry
│   │   ├── base.py       # BaseStrategy-Contract
│   │   └── ...
│   ├── backtest/         # Backtest-Engine
│   ├── data/             # Data-Loading & Caching
│   ├── core/             # Core-Module (Config, Sizing, Risk)
│   ├── live/             # Live-Trading-Components
│   ├── reporting/        # Reports & Visualisierung
│   └── governance/       # Go/No-Go-Logic
├── config/               # TOML-Configs für Backtests
├── scripts/              # CLI-Tools & Utilities
├── tests/                # Pytest Test-Suite
└── docs/                 # Dokumentation
```

---

## Quick Commands

```bash
# Tests ausführen
pytest -q

# Targeted Tests (Position-Sizing)
pytest tests/test_vol_regime_overlay_sizer.py -q

# Linting
python3 -m ruff check src tests scripts

# Backtest ausführen
python scripts/run_strategy_from_config.py --strategy ma_crossover

# Research-Pipeline
python scripts&#47;run_walkforward.py --strategy ma_crossover
python scripts&#47;run_monte_carlo.py --strategy ma_crossover
python scripts/run_stress_tests.py --portfolio moderate

# Live-Status
python -m src.cli.live_ops status
```

---

## Extensibility Points

Peak_Trade ist so gebaut, dass alle zentralen Komponenten austauschbar sind. Hier sind die wichtigsten Erweiterungspunkte:

### 1. Neue Strategy hinzufügen

```python
# src/strategies/my_strategy.py
from .base import BaseStrategy

class MyStrategy(BaseStrategy):
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        # Deine Logik hier
        return signals

# In registry.py registrieren
from .my_strategy import MyStrategy

_STRATEGY_REGISTRY["my_strategy"] = StrategySpec(
    key="my_strategy",
    cls=MyStrategy,
    config_section="strategy.my_strategy"
)
```

**→ Siehe:** [STRATEGY_DEV_GUIDE.md](STRATEGY_DEV_GUIDE.md)

### 2. Neuen Position Sizer hinzufügen

```python
# src/core/position_sizing.py
class MyCustomSizer(BasePositionSizer):
    def get_target_position(self, signal, price, equity):
        # Deine Sizing-Logik hier
        return target_units
```

**Config:**
```toml
[sizing]
type = "my_custom"  # Registrierung in build_position_sizer_from_config()
```

### 3. Neuen Risk Manager hinzufügen

```python
# src/core/risk.py
class MyRiskManager(BaseRiskManager):
    def adjust_target_position(self, target_units, price, equity, timestamp):
        # Deine Risk-Logik hier
        return adjusted_units
```

**Config:**
```toml
[risk]
type = "my_risk"  # Registrierung in build_risk_manager_from_config()
```

### 4. Neuen Runner hinzufügen

```bash
# scripts/run_my_custom_backtest.py
from src.backtest.engine import BacktestEngine
from src.core.peak_config import load_config

cfg = load_config()
# Deine Runner-Logik hier
```

**Beispiele:**
- `scripts&#47;run_strategy_from_config.py` – Einzel-Backtest
- `scripts&#47;run_portfolio_backtest.py` – Portfolio-Backtest
- `scripts&#47;run_walkforward.py` – Walk-Forward-Validation

### 5. Neue Datenquelle hinzufügen

```python
# src/data/loaders/my_provider.py
def load_data_from_my_provider(symbol, start, end):
    # Deine Data-Loading-Logik hier
    return df  # Must return OHLCV DataFrame
```

**Integration in `src&#47;data&#47;data_loader.py`:**
```python
def load_ohlcv_data(..., provider="my_provider"):
    if provider == "my_provider":
        return load_data_from_my_provider(...)
```

---

## Operational Notes

### Determinism & Reproduzierbarkeit

Peak_Trade garantiert **deterministische Backtests**:

- ✅ Gleiche Config + gleiche Daten = gleiche Ergebnisse
- ✅ Bar-für-Bar-Execution ohne Look-Ahead
- ✅ Seed-basierte Randomness (für Monte-Carlo-Simulationen)

**Best Practice:**
```toml
[backtest]
seed = 42  # Für reproduzierbare Random-Samples
```

### Wie starte ich einen lokalen Backtest?

**Variante A: Config-basiert (Empfohlen)**
```bash
# Mit Standard-Config
python scripts/run_strategy_from_config.py --strategy ma_crossover

# Mit Custom-Config
python scripts/run_strategy_from_config.py --config config&#47;my_backtest.toml
```

**Variante B: Portfolio-Backtest**
```bash
python scripts/run_portfolio_backtest.py --allocation equal
```

**Variante C: Research-Pipeline**
```bash
# Walk-Forward
python scripts&#47;run_walkforward.py --strategy ma_crossover

# Monte-Carlo
python scripts&#47;run_monte_carlo.py --strategy rsi_reversion --runs 1000
```

### Logging & Registry

Alle Backtest-Ergebnisse werden automatisch in der **Experiment-Registry** geloggt:

```bash
# Alle Runs anzeigen
python scripts/list_experiments.py

# Details eines Runs
python scripts/show_experiment.py <run_id>

# Nur Portfolio-Runs
python scripts/list_experiments.py --run-type portfolio_backtest
```

**Registry-Location:**
- SQLite-DB: `data/experiments.db`
- Equity-Curves: `data/equity_curves/<run_id>.parquet`

---

## Nächste Schritte

1. **Ersten Backtest laufen lassen:** Folge dem [Quickstart](#wie-starte-ich-schnell-einen-backtest) oben
2. **Eigene Strategie entwickeln:** Siehe [STRATEGY_DEV_GUIDE.md](STRATEGY_DEV_GUIDE.md)
3. **Research-Pipeline testen:** Siehe [RESEARCH_PIPELINE_V2.md](RESEARCH_PIPELINE_V2.md)
4. **Live-Track kennenlernen:** Siehe [PHASE_84_LIVE_TRACK_DEMO_WALKTHROUGH.md](PHASE_84_LIVE_TRACK_DEMO_WALKTHROUGH.md)

---

## Further Reading / Related Docs

### Core Documentation
- 🚪 **[Documentation Frontdoor](README.md)** – Navigate all docs by audience & topic
- 🔬 **[Backtest Engine](BACKTEST_ENGINE.md)** – Detailed engine contract, execution modes, extension hooks
- 🎯 **[Strategy Dev Guide](STRATEGY_DEV_GUIDE.md)** – Step-by-step strategy development

### Architecture Deep Dives
- 🏗️ **[Architecture Overview](ARCHITECTURE_OVERVIEW.md)** – **Deep dive:** System design, layer diagrams, component interactions
- 📐 **[Architecture Details](ARCHITECTURE.md)** – Technical architecture specifications

**Note:** This document (PEAK_TRADE_OVERVIEW) is the **entry point** with architecture map and extensibility points. For detailed system design, see ARCHITECTURE_OVERVIEW.md.

### Developer & Operations
- ⚡ **[Developer Workflow Guide](DEVELOPER_WORKFLOW_GUIDE.md)** – Workflows, automation, productivity
- 🛰️ **[Live Operational Runbooks](LIVE_OPERATIONAL_RUNBOOKS.md)** – Live ops procedures
- 🛰️ **[Ops Hub](ops/README.md)** – Operator center with runbooks, merge logs, CI docs

### Research & Portfolio
- 📊 **[Research → Live Playbook](PLAYBOOK_RESEARCH_TO_LIVE_PORTFOLIOS.md)** – End-to-end research-to-production workflow
- 🎯 **[Portfolio Recipes](PORTFOLIO_RECIPES_AND_PRESETS.md)** – Predefined portfolio configurations

### Governance & Safety
- 🛡️ **[Governance & Safety Overview](GOVERNANCE_AND_SAFETY_OVERVIEW.md)** – Safety-first approach, go/no-go decisions
- 🔐 **[Governance Hub](governance/README.md)** – AI autonomy, policy critic, evidence packs
- 🔒 **[Safety Policies](SAFETY_POLICY_TESTNET_AND_LIVE.md)** – Testnet & live safety rules

### Recent Updates
- 🆕 **[Documentation Update Summary](DOCUMENTATION_UPDATE_SUMMARY.md)** – Recent docs changes (2026-01-13)

---

**📌 Wichtig:** Peak_Trade ist ein Safety-First-Framework. Lies immer die Docs, bevor du etwas in Production deployest!
