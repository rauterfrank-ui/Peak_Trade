# Peak_Trade – AI Assistant Guide (Claude/Cursor)

> **Hinweis:** Dieser Guide ist die technische Referenz für Claude/Cursor (Projekt-Übersicht, Module, Commands).
> Bevor du mit AI-Tools aktiv am Peak_Trade-Repo arbeitest, lies bitte zuerst den **AI-Helper-Guide** (Working Agreements & Best Practices):
> [`PEAK_TRADE_AI_HELPER_GUIDE.md`](PEAK_TRADE_AI_HELPER_GUIDE.md)

> **Zweck:** Zentrale Anleitung für die Nutzung von AI-Assistenz (Claude, Cursor, ChatGPT) im Peak_Trade-Projekt
>
> **Zielgruppe:** Entwickler, die mit AI-Tools arbeiten, um Code zu schreiben, Dokumentation zu erstellen oder das Projekt zu verstehen

---

## 1. Projekt-Übersicht

**Peak_Trade** ist ein modulares Kryptowährungs-Trading- und Backtesting-Framework in Python 3.9+. Es bietet Strategie-Entwicklung, Backtesting mit realistischen Marktbedingungen, Risk-Management und Live-/Paper-Trading-Funktionalität.

---

## 2. Quick Commands

```bash
# Setup
source .venv/bin/activate
pip install -e ".[dev]"

# Testing
pytest tests/ -v                              # All tests
pytest tests/test_backtest_smoke.py -v        # Specific file
pytest tests/ --cov=src --cov-report=html     # With coverage

# Linting & Formatting
ruff check src/ tests/
black src/ tests/

# Run Backtest
python scripts/run_backtest.py
python scripts/run_backtest.py --strategy rsi_reversion
python scripts/run_backtest.py --config custom_config.toml

# Sweeps & Analytics
python scripts/sweep_parameters.py --strategy ma_crossover
python scripts/list_experiments.py --sort-by sharpe
python scripts/generate_leaderboards.py

# Forward/Paper Trading
python scripts/generate_forward_signals.py --strategy ma_crossover
python scripts/check_live_risk_limits.py
python scripts/paper_trade_from_orders.py
```

---

## 3. Portfolio Research to Live Playbook

Wenn du mit AI-Assistenz neue Portfolios/Presets evaluierst oder Richtung Live bringen willst, nutze [`PLAYBOOK_RESEARCH_TO_LIVE_PORTFOLIOS.md`](../PLAYBOOK_RESEARCH_TO_LIVE_PORTFOLIOS.md) als Kontext-Prompt.

Dieses Playbook beschreibt:
- Den kompletten Weg von Portfolio-Presets in der Research-Welt bis zur Live-/Testnet-Aktivierung
- Klare Go/No-Go-Kriterien basierend auf Metriken
- Mapping von Research-Konfigurationen auf Live-/Testnet-Setups
- Governance & Safety-Anbindung bei jedem Schritt

**Verwendung als AI-Kontext:**
- Füge das Playbook als Kontext hinzu, wenn du Portfolios evaluieren oder aktivieren willst
- Der AI-Assistent kennt dann die Gatekeeping-Logik und Governance-Kriterien
- Alle CLI-Commands und Workflows sind dokumentiert

---

## 4. Verzeichnis-Struktur

```
Peak_Trade/
├── config.toml              # Central configuration (TOML)
├── config/                  # Regime/sweep configurations
├── pyproject.toml           # Dependencies & tooling
├── src/
│   ├── core/                # Config, position sizing, risk, experiments
│   ├── data/                # Data loading, caching, Kraken API
│   ├── strategies/          # Trading strategies (BaseStrategy ABC)
│   ├── backtest/            # BacktestEngine, stats, reporting
│   ├── live/                # Risk limits, orders, safety
│   ├── forward/             # Signal generation/evaluation
│   ├── orders/              # Order execution layer
│   ├── exchange/            # CCXT integration
│   ├── analytics/           # Experiment analysis, leaderboards
│   └── notifications/       # Alert system
├── scripts/                 # CLI runners (run_backtest.py, etc.)
├── tests/                   # pytest test suite
├── docs/                    # Comprehensive documentation
└── reports/                 # Generated outputs (experiments, results)
```

---

## 5. Wichtige Module

| Module | Purpose |
|--------|---------|
| `src/core/peak_config.py` | TOML config loading with dot-notation access |
| `src/core/position_sizing.py` | Position sizing (NoopSizer, FixedFraction, FixedSize) |
| `src/core/risk.py` | Risk management (MaxDrawdown, EquityFloor) |
| `src/core/experiments.py` | Experiment registry tracking |
| `src/strategies/base.py` | BaseStrategy ABC - all strategies inherit this |
| `src/strategies/registry.py` | Strategy lookup by key |
| `src/backtest/engine.py` | BacktestEngine - bar-by-bar simulation |
| `src/backtest/stats.py` | Performance metrics (Sharpe, Drawdown, etc.) |
| `src/live/risk_limits.py` | Pre-trade risk checks |

---

## 6. Verfügbare Strategien

| Key | Type | Description |
|-----|------|-------------|
| `ma_crossover` | Trend | Moving Average Crossover |
| `rsi_reversion` | Reversion | RSI Mean-Reversion |
| `breakout_donchian` | Trend | Donchian Channel Breakout |
| `momentum_1h` | Trend | Momentum-based |
| `bollinger_bands` | Reversion | Bollinger Bands |
| `macd` | Trend | MACD Crossover |
| `trend_following` | Trend | ADX-based |
| `mean_reversion` | Reversion | Z-Score |

---

## 7. Architektur-Patterns

1. **Abstract Base Classes**: `BaseStrategy`, `BasePositionSizer`, `BaseRiskManager`
2. **Factory Methods**: `Strategy.from_config(cfg, section)`
3. **Dataclasses**: Type-safe data containers (`BacktestResult`, `Trade`)
4. **Registry Pattern**: Strategy and experiment registries
5. **Configuration-Driven**: All behaviors via `config.toml`

---

## 8. Neue Strategie erstellen

```python
# src/strategies/my_strategy.py
from .base import BaseStrategy
import pandas as pd

class MyStrategy(BaseStrategy):
    KEY = "my_strategy"

    def __init__(self, param1: int = 20):
        self.param1 = param1

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        # Return pd.Series with values in {-1, 0, 1}
        return pd.Series(0, index=data.index)

    @classmethod
    def from_config(cls, cfg, section: str):
        return cls(param1=cfg.get(f"{section}.param1", 20))
```

Register in `src/strategies/registry.py` and add config to `config.toml`.

---

## 9. Config-Struktur (config.toml)

```toml
[environment]
mode = "paper"                    # paper | testnet | live

[general]
base_currency = "EUR"
starting_capital = 10_000.0
active_strategy = "ma_crossover"

[position_sizing]
type = "fixed_fraction"           # noop | fixed_size | fixed_fraction
fraction = 0.1

[risk_management]
type = "max_drawdown"
max_drawdown = 0.25

[strategy.ma_crossover]
fast_window = 20
slow_window = 50

[live_risk]
enabled = true
max_daily_loss_abs = 500.0
block_on_violation = true
```

---

## 10. Risk-Management-Layer

1. **Position Sizing** (`src/core/position_sizing.py`): signal → units
2. **Risk Management** (`src/core/risk.py`): adjusts units based on equity/drawdown
3. **Live Risk Limits** (`src/live/risk_limits.py`): pre-trade checks

---

## 11. Code-Style

- **Python**: 3.9+, type hints, dataclasses
- **Line length**: 100 characters
- **Formatter**: Black
- **Linter**: Ruff
- **Tests**: pytest with fixtures

---

## 12. Wichtige Hinweise

- Strategies return **states** (persistent positions), not events
- CLI args override `config.toml` settings
- All runs logged to `reports/experiments/experiments.csv`
- Documentation in German and English

---

## 13. Wichtige Dateien zum Einstieg

1. `config.toml` - Central configuration
2. `src/backtest/engine.py` - Backtest engine
3. `src/strategies/base.py` - Strategy base class
4. `scripts/run_backtest.py` - Main entry point
5. `docs/ARCHITECTURE_OVERVIEW.md` - Architecture overview (Phase 52)

---

## 14. Developer-Guides (Phase 52)

**Wie nutze ich die Developer-Guides mit AI-Assistenz?**

Die Developer-Guides (`DEV_GUIDE_*.md`) können als Kontext für AI-Tools verwendet werden:

1. **Neue Strategie hinzufügen:**
   - Öffne `docs/DEV_GUIDE_ADD_STRATEGY.md` als Kontext
   - AI-Tool kann die Schritt-für-Schritt-Anleitung befolgen

2. **Neuen Exchange-Adapter hinzufügen:**
   - Öffne `docs/DEV_GUIDE_ADD_EXCHANGE.md` als Kontext
   - AI-Tool kann die Integration-Schritte befolgen

3. **Neues Live-Risk-Limit hinzufügen:**
   - Öffne `docs/DEV_GUIDE_ADD_LIVE_RISK_LIMIT.md` als Kontext
   - AI-Tool kann die Implementierung-Schritte befolgen

4. **Neues Portfolio-Rezept hinzufügen:**
   - Öffne `docs/DEV_GUIDE_ADD_PORTFOLIO_RECIPE.md` als Kontext
   - AI-Tool kann die Rezept-Definition befolgen

**Beispiel-Prompt für AI-Tools:**

```
Ich möchte eine neue Strategie hinzufügen. Bitte nutze 
docs/DEV_GUIDE_ADD_STRATEGY.md als Referenz und folge 
den Schritt-für-Schritt-Anweisungen.
```

**Verfügbare Developer-Guides:**

- `docs/DEV_GUIDE_ADD_STRATEGY.md` – Neue Strategie hinzufügen
- `docs/DEV_GUIDE_ADD_EXCHANGE.md` – Neuen Exchange-Adapter hinzufügen
- `docs/DEV_GUIDE_ADD_LIVE_RISK_LIMIT.md` – Neues Live-Risk-Limit hinzufügen
- `docs/DEV_GUIDE_ADD_PORTFOLIO_RECIPE.md` – Neues Portfolio-Rezept hinzufügen

---

## 15. Architektur-Übersicht

- `docs/ARCHITECTURE_OVERVIEW.md` – High-Level-Architektur mit Diagramm und Layer-Beschreibung

---

## 16. Weitere wichtige Dokumente

- `docs/PEAK_TRADE_STATUS_OVERVIEW.md` – Gesamtstatus des Projekts
- `docs/PLAYBOOK_RESEARCH_TO_LIVE_PORTFOLIOS.md` – End-to-End-Prozess für Portfolio-Promotion
- `docs/PORTFOLIO_RECIPES_AND_PRESETS.md` – Portfolio-Rezepte & Presets
- `docs/CLI_CHEATSHEET.md` – CLI-Referenz & Quick Commands

---

**Built with ❤️ and AI-assistance**








