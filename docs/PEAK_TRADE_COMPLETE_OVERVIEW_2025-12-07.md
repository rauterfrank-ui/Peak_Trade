# Peak_Trade – Vollständige Projektdokumentation

> **Stand:** 2025-12-07  
> **Version:** v1.0 Research + Testnet-ready  
> **Tests:** 1870 Tests (1376+ passed in 39 Phasen)  
> **Code:** ~53.000 Zeilen Python in 149 Modulen

---

## Inhaltsverzeichnis

1. [Executive Summary](#1-executive-summary)
2. [Projektziele & Vision](#2-projektziele--vision)
3. [Architektur-Übersicht](#3-architektur-übersicht)
4. [Modul-Struktur im Detail](#4-modul-struktur-im-detail)
5. [Strategien & Portfolio-Layer](#5-strategien--portfolio-layer)
6. [Backtest-Engine & Research-Pipeline](#6-backtest-engine--research-pipeline)
7. [Risk-Management & Safety](#7-risk-management--safety)
8. [Live/Testnet-Infrastruktur](#8-livetestnet-infrastruktur)
9. [Execution-Pipeline](#9-execution-pipeline)
10. [Reporting & Visualisierung](#10-reporting--visualisierung)
11. [Registry & Experiment-System](#11-registry--experiment-system)
12. [Configuration-Management](#12-configuration-management)
13. [CLI-Tools & Scripts](#13-cli-tools--scripts)
14. [Test-Suite & Qualitätssicherung](#14-test-suite--qualitätssicherung)
15. [Governance & Dokumentation](#15-governance--dokumentation)
16. [Projekt-Status & Roadmap](#16-projekt-status--roadmap)
17. [Quickstart-Guide](#17-quickstart-guide)
18. [Anhang: Dateistruktur](#18-anhang-dateistruktur)

---

## 1. Executive Summary

**Peak_Trade** ist ein modulares, KI-unterstütztes Trading-Framework für Kryptowährungen mit Fokus auf:

- **Robuste Backtests** mit realistischen Annahmen (Fees, Slippage, Stop-Loss)
- **Multi-Strategie-Portfolios** mit intelligenter Gewichtung
- **Strenge Risikokontrolle** auf allen Ebenen (Order, Portfolio, System)
- **Klare Trennung** von Research → Shadow → Testnet → Live
- **Reproduzierbare Experimente** mit vollständiger Protokollierung

### Kernzahlen

| Metrik | Wert |
|--------|------|
| Python-Module | 149 |
| Codezeilen (src/) | ~53.000 |
| Unit-Tests | 1.870 |
| Test-Dateien | 96 |
| Dokumentations-Dateien | 121 |
| Entwicklungsphasen | 74+ |
| Unterstützte Strategien | 15+ |

### Tech-Stack

- **Sprache:** Python 3.9+
- **Daten:** pandas, numpy, pyarrow (Parquet)
- **Exchange:** Kraken API (REST/WebSocket via ccxt)
- **Config:** TOML mit Pydantic-Validierung
- **Testing:** pytest mit ~95% Coverage
- **Reporting:** Matplotlib, HTML-Reports, Markdown

---

## 2. Projektziele & Vision

### 2.1 Kernphilosophie

> **"Ein Trading-Stack, dem Future-Ich vertraut – technisch, risk-seitig und operativ."**

### 2.2 Design-Prinzipien

1. **Safety-First**
   - Mehrere Sicherheitsschichten (Defense-in-Depth)
   - LIVE-Mode standardmäßig blockiert
   - Risk-Limits auf Order- und Portfolio-Level

2. **Research-Driven**
   - Keine Live-Orders ohne validierte Backtests
   - Monte-Carlo & Stress-Tests für Robustheit
   - Walk-Forward-Testing gegen Overfitting

3. **Modulare Architektur**
   - Klare Trennung der Layer (Data, Strategy, Risk, Execution)
   - Plug-and-Play für neue Strategien
   - Configuration-Driven Design

4. **Reproduzierbarkeit**
   - Alle Runs werden in Registry geloggt
   - Versionierte Konfigurationen
   - Vollständige Audit-Trails

### 2.3 Was Peak_Trade NICHT ist

- ❌ Kein "Get-Rich-Quick"-Bot
- ❌ Keine Black-Box ohne Verständnis
- ❌ Kein System für ungeprüftes Live-Trading
- ❌ Keine Finanzberatung oder Anlageempfehlung

---

## 3. Architektur-Übersicht

### 3.1 Layer-Modell

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CLI & Scripts Layer                          │
│  (research_cli.py, live_ops.py, run_backtest.py, ...)              │
└─────────────────────────────────────────────────────────────────────┘
                                   │
┌─────────────────────────────────────────────────────────────────────┐
│                      Reporting & Analytics                          │
│  (HTML Reports, Sweep Visualization, Live Status Reports)           │
└─────────────────────────────────────────────────────────────────────┘
                                   │
┌──────────────────────────┬──────────────────────────────────────────┐
│   Research & Backtest    │         Live/Testnet Layer               │
│  ┌──────────────────┐    │   ┌──────────────────────────────┐       │
│  │ BacktestEngine   │    │   │ ExecutionPipeline            │       │
│  │ Stats & Metrics  │    │   │ SafetyGuard                  │       │
│  │ Registry         │    │   │ LiveRiskLimits               │       │
│  │ Experiments      │    │   │ OrderExecutors               │       │
│  └──────────────────┘    │   │ Portfolio Monitor            │       │
│                          │   └──────────────────────────────┘       │
└──────────────────────────┴──────────────────────────────────────────┘
                                   │
┌─────────────────────────────────────────────────────────────────────┐
│                    Strategy & Portfolio Layer                       │
│  (MA Crossover, RSI, Breakout, Vol-Regime, Portfolio-Recipes)      │
└─────────────────────────────────────────────────────────────────────┘
                                   │
┌─────────────────────────────────────────────────────────────────────┐
│                        Risk & Safety Layer                          │
│  (Position Sizing, Risk Limits, Safety Guards, Governance)         │
└─────────────────────────────────────────────────────────────────────┘
                                   │
┌─────────────────────────────────────────────────────────────────────┐
│                          Data Layer                                 │
│  (Kraken API, CSV Loader, Normalizer, Parquet Cache)               │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.2 Datenfluss

```
Market Data (Kraken API / CSV)
        │
        ▼
┌───────────────┐
│  Data Loader  │ ──▶ Normalisierung ──▶ Parquet Cache
└───────────────┘
        │
        ▼
┌───────────────┐
│  Strategies   │ ──▶ Signale (-1, 0, +1)
└───────────────┘
        │
        ▼
┌───────────────┐
│  Portfolio    │ ──▶ Gewichtete Kombination
└───────────────┘
        │
        ▼
┌───────────────┐
│  Backtest OR  │
│  Execution    │ ──▶ Environment Check ──▶ Safety Check ──▶ Risk Check
└───────────────┘
        │
        ▼
┌───────────────┐
│  Order        │ ──▶ Paper / Testnet / (Live blocked)
│  Executor     │
└───────────────┘
        │
        ▼
┌───────────────┐
│  Reporting    │ ──▶ Stats, Charts, HTML Reports
└───────────────┘
```

---

## 4. Modul-Struktur im Detail

### 4.1 Verzeichnisbaum

```
Peak_Trade/
├── src/                          # Hauptcode (~53.000 Zeilen)
│   ├── analytics/                # Experiment-Analyse, Explorer
│   ├── backtest/                 # BacktestEngine, Stats, Reporting
│   ├── core/                     # Config, Environment, Registry
│   ├── data/                     # Loader, Normalizer, Cache, Kraken
│   ├── exchange/                 # Exchange-Clients (CCXT, Dummy)
│   ├── execution/                # ExecutionPipeline
│   ├── experiments/              # Monte-Carlo, Stress-Tests, Sweeps
│   ├── forward/                  # Forward-Signal-Generierung
│   ├── live/                     # Live-Ops, Safety, Risk-Limits
│   ├── notifications/            # Alert-System (Console, Webhook, Slack)
│   ├── orders/                   # Order-Typen, Executors
│   ├── portfolio/                # Portfolio-Kombination, Weighting
│   ├── regime/                   # Regime-Detection, Switching
│   ├── reporting/                # Reports, Visualisierung
│   ├── risk/                     # Position Sizing, Limits
│   ├── scheduler/                # Job-Scheduling
│   ├── strategies/               # Alle Strategien
│   └── sweeps/                   # Parameter-Sweeps
│
├── scripts/                      # CLI-Tools (~96 Dateien)
├── tests/                        # Unit-Tests (~96 Dateien)
├── docs/                         # Dokumentation (~121 Dateien)
├── config/                       # TOML-Konfiguration
├── reports/                      # Generierte Reports
├── data/                         # Marktdaten & Cache
└── notebooks/                    # Jupyter-Notebooks
```

### 4.2 Kern-Module

| Modul | Pfad | Beschreibung |
|-------|------|--------------|
| **BacktestEngine** | `src/backtest/engine.py` | Haupt-Backtest-Loop mit Fees, Slippage |
| **RegistryEngine** | `src/backtest/registry_engine.py` | Registry-integrierter Backtest |
| **ExecutionPipeline** | `src/execution/pipeline.py` | Order-Orchestrierung mit Safety |
| **SafetyGuard** | `src/live/safety.py` | Environment & Safety-Checks |
| **LiveRiskLimits** | `src/live/risk_limits.py` | Order- & Portfolio-Risk-Limits |
| **EnvironmentConfig** | `src/core/environment.py` | Paper/Testnet/Live-Mode |
| **PeakConfig** | `src/core/peak_config.py` | TOML-Config-Management |
| **ConfigRegistry** | `src/core/config_registry.py` | Strategy-Registry aus TOML |

---

## 5. Strategien & Portfolio-Layer

### 5.1 Verfügbare Strategien

| Strategie | Datei | Typ | Beschreibung |
|-----------|-------|-----|--------------|
| **MA Crossover** | `ma_crossover.py` | Trend | Moving Average Crossover (Fast/Slow) |
| **RSI** | `rsi.py` | Mean-Reversion | RSI Overbought/Oversold |
| **RSI Reversion** | `rsi_reversion.py` | Mean-Reversion | Erweiterte RSI-Strategie |
| **Trend Following** | `trend_following.py` | Trend | Multi-MA Trend-Filter |
| **Mean Reversion** | `mean_reversion.py` | Mean-Reversion | Bollinger-Band basiert |
| **Mean Rev Channel** | `mean_reversion_channel.py` | Mean-Reversion | Keltner Channel |
| **Breakout** | `breakout.py` | Momentum | High/Low Breakout |
| **Breakout Donchian** | `breakout_donchian.py` | Momentum | Donchian Channel Breakout |
| **Momentum** | `momentum.py` | Momentum | Rate-of-Change basiert |
| **Vol Breakout** | `vol_breakout.py` | Volatility | Volatility Breakout |
| **Vol Regime Filter** | `vol_regime_filter.py` | Meta | Regime-Klassifikation |
| **Bollinger** | `bollinger.py` | Mean-Reversion | Bollinger Bands |
| **MACD** | `macd.py` | Trend | MACD Crossover |
| **Regime Aware Portfolio** | `regime_aware_portfolio.py` | Portfolio | Dynamische Regime-Skalierung |
| **Composite** | `composite.py` | Multi | Strategie-Kombination |

### 5.2 Strategy-Interface

```python
class BaseStrategy(ABC):
    """Basis-Interface für alle Strategien."""

    @abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        """
        Generiert Trading-Signale.

        Args:
            df: OHLCV DataFrame mit DatetimeIndex

        Returns:
            pd.Series mit Signalen: -1 (Short), 0 (Flat), +1 (Long)
        """
        pass

    @property
    def name(self) -> str:
        """Strategie-Name für Logging/Reports."""
        return self.__class__.__name__

    @property
    def params(self) -> Dict[str, Any]:
        """Aktuelle Parameter der Strategie."""
        return {}
```

### 5.3 Portfolio-Layer

```python
# Portfolio-Kombination mehrerer Strategien
from src.portfolio import PortfolioManager, EqualWeightCombiner

manager = PortfolioManager(
    strategies=[ma_strategy, rsi_strategy, breakout_strategy],
    combiner=EqualWeightCombiner(),
    weights=[0.4, 0.3, 0.3],
)

combined_signals = manager.generate_signals(df)
```

### 5.4 Portfolio-Recipes (TOML)

```toml
# config/portfolio_recipes.toml

[portfolio_recipes.multi_style_moderate]
description = "Ausgewogenes Multi-Style Portfolio"
risk_profile = "moderate"

[[portfolio_recipes.multi_style_moderate.strategies]]
name = "ma_crossover"
weight = 0.40
params = { fast_window = 20, slow_window = 50 }

[[portfolio_recipes.multi_style_moderate.strategies]]
name = "rsi_reversion"
weight = 0.35
params = { period = 14, oversold = 30, overbought = 70 }

[[portfolio_recipes.multi_style_moderate.strategies]]
name = "breakout_donchian"
weight = 0.25
params = { period = 20 }
```

---

## 6. Backtest-Engine & Research-Pipeline

### 6.1 BacktestEngine

Die BacktestEngine ist das Herzstück für Strategietests:

```python
from src.backtest import BacktestEngine, BacktestConfig

config = BacktestConfig(
    initial_capital=10000.0,
    fee_rate=0.001,           # 0.1% Fees
    slippage_bps=5.0,         # 5 Basispunkte Slippage
    position_size_pct=0.95,   # 95% Kapitalnutzung
    stop_loss_pct=0.05,       # 5% Stop-Loss
)

engine = BacktestEngine(config)
result = engine.run(
    df=ohlcv_data,
    signals=strategy.generate_signals(ohlcv_data),
    symbol="BTC/EUR",
)

print(result.stats)
# {
#   'total_return': 0.234,
#   'sharpe_ratio': 1.45,
#   'max_drawdown': -0.12,
#   'win_rate': 0.58,
#   'profit_factor': 1.82,
#   'total_trades': 47,
#   ...
# }
```

### 6.2 Metriken & Stats

| Metrik | Beschreibung |
|--------|--------------|
| `total_return` | Gesamtrendite |
| `annual_return` | Annualisierte Rendite |
| `sharpe_ratio` | Sharpe Ratio (Risk-adjusted Return) |
| `sortino_ratio` | Sortino Ratio (Downside Deviation) |
| `max_drawdown` | Maximaler Drawdown |
| `calmar_ratio` | Calmar Ratio (Return/MaxDD) |
| `win_rate` | Gewinnquote (% gewinnende Trades) |
| `profit_factor` | Profit Factor (Gewinn/Verlust) |
| `avg_trade_pnl` | Durchschnittlicher Trade-PnL |
| `total_trades` | Anzahl Trades |
| `avg_holding_period` | Durchschnittliche Haltedauer |

### 6.3 Research-Pipeline v2

```bash
# Einzelne Strategie testen
python scripts/research_cli.py run \
  --strategy ma_crossover \
  --symbol BTC/EUR \
  --timeframe 1h \
  --start 2024-01-01 \
  --end 2024-12-01

# Portfolio-Preset testen
python scripts/research_cli.py portfolio \
  --portfolio-preset multi_style_moderate \
  --format both

# Parameter-Sweep durchführen
python scripts/run_strategy_sweep.py \
  --strategy ma_crossover \
  --sweep-config config/sweeps/ma_crossover.toml
```

### 6.4 Robustness-Tests

```python
# Monte-Carlo Simulation
from src.experiments.monte_carlo import MonteCarloSimulator

mc = MonteCarloSimulator(n_simulations=1000)
mc_results = mc.run(equity_curve, returns)

# Walk-Forward Testing
from src.backtest.walkforward import WalkForwardTest

wf = WalkForwardTest(
    train_window=252,  # 1 Jahr Training
    test_window=63,    # 3 Monate Test
    step_size=21,      # 1 Monat Step
)
wf_results = wf.run(strategy, df)

# Stress-Tests
from src.experiments.stress_tests import StressTestRunner

stress = StressTestRunner()
stress_results = stress.run(
    strategy,
    scenarios=["2020_covid_crash", "2022_crypto_winter"]
)
```

---

## 7. Risk-Management & Safety

### 7.1 Defense-in-Depth

```
Layer 1: Environment-Mode
   │      (PAPER / TESTNET / LIVE)
   │
   ▼
Layer 2: SafetyGuard
   │      (ensure_may_place_order)
   │
   ▼
Layer 3: LiveRiskLimits
   │      (Order- & Portfolio-Level)
   │
   ▼
Layer 4: Execution Pipeline
   │      (execute_with_safety)
   │
   ▼
Layer 5: Order Executor
          (Paper / Testnet / Live-blocked)
```

### 7.2 Environment-Konfiguration

```python
from src.core.environment import EnvironmentConfig, TradingEnvironment

# Sichere Defaults
env_config = EnvironmentConfig(
    environment=TradingEnvironment.PAPER,  # PAPER / TESTNET / LIVE
    enable_live_trading=False,             # Zusätzlicher Safety-Switch
    require_confirm_token=True,            # Token für Live erforderlich
    testnet_dry_run=True,                  # Testnet nur Dry-Run
    live_mode_armed=False,                 # Zweistufiges Gating
    live_dry_run_mode=True,                # Live nur als Dry-Run
)
```

### 7.3 SafetyGuard

```python
from src.live.safety import SafetyGuard, create_safety_guard

guard = create_safety_guard(env_config)

# Prüft ob Order-Platzierung erlaubt
try:
    guard.ensure_may_place_order(is_testnet=False)
except SafetyBlockedError as e:
    print(f"Order blockiert: {e}")

# Exceptions:
# - PaperModeOrderError: Im Paper-Modus
# - TestnetDryRunOnlyError: Testnet nur Dry-Run
# - LiveNotImplementedError: Live nicht implementiert
# - LiveTradingDisabledError: Live deaktiviert
# - ConfirmTokenInvalidError: Token ungültig
```

### 7.4 LiveRiskLimits

```python
from src.live.risk_limits import LiveRiskLimits

limits = LiveRiskLimits(
    max_order_notional=5000.0,       # Max 5000€ pro Order
    max_symbol_exposure=10000.0,     # Max 10000€ pro Symbol
    max_total_exposure=50000.0,      # Max 50000€ gesamt
    max_daily_loss_pct=0.05,         # Max 5% Tagesverlust
    max_orders_per_minute=10,        # Rate-Limiting
)

# Risk-Check vor Order
result = limits.check_order(order, portfolio_state)
if not result.allowed:
    print(f"Order blockiert: {result.reasons}")
```

### 7.5 Position Sizing

```python
from src.risk.position_sizer import PositionSizer

sizer = PositionSizer(
    max_position_pct=0.10,     # Max 10% pro Position
    max_risk_per_trade=0.02,  # Max 2% Risk pro Trade
    use_atr_sizing=True,      # ATR-basierte Größe
)

size = sizer.calculate(
    capital=10000.0,
    price=50000.0,
    atr=1500.0,
    stop_distance_pct=0.03,
)
```

---

## 8. Live/Testnet-Infrastruktur

### 8.1 Stufenmodell

```
┌─────────────────────────────────────────────────────────────┐
│                        SHADOW MODE                          │
│  • Keine echten Orders                                      │
│  • Vollständige Simulation                                  │
│  • Paper-Executor mit simulierten Fills                     │
│  • Unbegrenzte Tests möglich                               │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼ (Go/No-Go Entscheidung)
┌─────────────────────────────────────────────────────────────┐
│                       TESTNET MODE                          │
│  • Echte Exchange-Integration (Kraken Testnet)             │
│  • Dry-Run Orders (nur Logging)                            │
│  • Validierung der Order-Logik                             │
│  • Risk-Limits werden getestet                             │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼ (Freigabe nach Checkliste)
┌─────────────────────────────────────────────────────────────┐
│                        LIVE MODE                            │
│  ⚠️ BLOCKIERT in Phase 71                                   │
│  • Zweistufiges Gating (enable + armed)                    │
│  • Confirm-Token erforderlich                              │
│  • Derzeit nur Design/Dry-Run                              │
└─────────────────────────────────────────────────────────────┘
```

### 8.2 Live-Ops CLI

```bash
# Health-Check
python scripts/live_ops.py health --config config/config.toml

# Portfolio-Status
python scripts/live_ops.py portfolio --config config/config.toml --json

# Order-Preview (ohne Ausführung)
python scripts/live_ops.py orders preview --config config/config.toml

# Live-Status-Report generieren
python scripts/generate_live_status_report.py \
  --output-dir reports/live_status \
  --format markdown \
  --tag daily
```

### 8.3 Shadow/Paper Session

```python
from src.live.shadow_session import ShadowPaperSession

session = ShadowPaperSession(
    strategy=strategy,
    symbol="BTC/EUR",
    timeframe="1m",
    initial_capital=10000.0,
)

# Bar-by-Bar Simulation
for bar in live_data_feed:
    session.step(bar)

# Ergebnisse
print(session.get_summary())
```

### 8.4 Exchange-Integration

```python
from src.exchange import build_trading_client_from_config

# Dummy-Client für Tests
from src.exchange.dummy_client import DummyExchangeClient
client = DummyExchangeClient(simulated_prices={"BTC/EUR": 50000})

# Kraken Testnet
from src.exchange.kraken_testnet import KrakenTestnetClient
client = KrakenTestnetClient(api_key="...", api_secret="...")

# CCXT-basierter Client
from src.exchange.ccxt_client import CCXTTradingClient
client = CCXTTradingClient(exchange_id="kraken", config={...})
```

---

## 9. Execution-Pipeline

### 9.1 Architektur (Phase 16A)

```
OrderRequest(s)
      │
      ▼
┌─────────────────────────────────────────┐
│         ExecutionPipeline               │
│  ┌───────────────────────────────────┐  │
│  │ 1. Environment-Check              │  │  ← LIVE blockiert
│  │    (is_live → rejected)           │  │
│  └───────────────────────────────────┘  │
│  ┌───────────────────────────────────┐  │
│  │ 2. SafetyGuard.ensure_may_place   │  │  ← Safety-Exceptions
│  └───────────────────────────────────┘  │
│  ┌───────────────────────────────────┐  │
│  │ 3. LiveRiskLimits.check_orders    │  │  ← Risk-Violations
│  └───────────────────────────────────┘  │
│  ┌───────────────────────────────────┐  │
│  │ 4. OrderExecutor.execute_orders   │  │  ← Paper/Testnet
│  └───────────────────────────────────┘  │
│  ┌───────────────────────────────────┐  │
│  │ 5. RunLogger.log_event            │  │  ← Audit-Trail
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
      │
      ▼
ExecutionResult
  • rejected: bool
  • reason: str
  • risk_check: LiveRiskCheckResult
  • executed_orders: List[OrderExecutionResult]
```

### 9.2 Usage

```python
from src.execution import ExecutionPipeline, ExecutionResult
from src.orders.base import OrderRequest

# Pipeline mit Safety-Komponenten
pipeline = ExecutionPipeline(
    executor=paper_executor,
    env_config=env_config,
    safety_guard=safety_guard,
    risk_limits=risk_limits,
    run_logger=run_logger,
)

# Order erstellen
order = OrderRequest(
    symbol="BTC/EUR",
    side="buy",
    quantity=0.01,
    order_type="market",
)

# Mit Safety-Checks ausführen
result: ExecutionResult = pipeline.execute_with_safety([order])

if result.rejected:
    print(f"Order abgelehnt: {result.reason}")
else:
    for exec_result in result.executed_orders:
        if exec_result.is_filled:
            print(f"Filled: {exec_result.fill.quantity} @ {exec_result.fill.price}")
```

---

## 10. Reporting & Visualisierung

### 10.1 Report-Typen

| Report | Modul | Output |
|--------|-------|--------|
| Backtest-Report | `backtest_report.py` | HTML, Markdown |
| Experiment-Report | `experiment_report.py` | HTML, JSON |
| Live-Status-Report | `live_status_report.py` | Markdown, HTML |
| Sweep-Report | `sweep_visualization.py` | HTML mit Plots |
| Monte-Carlo-Report | `monte_carlo_report.py` | HTML, PNG |
| Stress-Test-Report | `stress_test_report.py` | Markdown |

### 10.2 Backtest-Report Beispiel

```python
from src.reporting.backtest_report import BacktestReportBuilder

builder = BacktestReportBuilder(result)
report = builder.build()

# Als HTML speichern
report.to_html("reports/backtest_report.html")

# Als Markdown
report.to_markdown("reports/backtest_report.md")
```

### 10.3 Visualisierungen

```python
from src.reporting.plots import (
    plot_equity_curve,
    plot_drawdown,
    plot_trade_distribution,
    plot_monthly_returns,
)

# Equity-Kurve
fig = plot_equity_curve(result.equity_curve)
fig.savefig("reports/equity.png")

# Drawdown
fig = plot_drawdown(result.drawdown_series)
fig.savefig("reports/drawdown.png")
```

### 10.4 Sweep-Visualisierung

```python
from src.reporting.sweep_visualization import (
    plot_sharpe_vs_parameter,
    plot_sharpe_heatmap,
    plot_param_sensitivity,
)

# Sharpe vs Parameter
fig = plot_sharpe_vs_parameter(sweep_results, param_name="fast_window")

# Heatmap für 2 Parameter
fig = plot_sharpe_heatmap(
    sweep_results,
    x_param="fast_window",
    y_param="slow_window",
)
```

---

## 11. Registry & Experiment-System

### 11.1 Strategy-Registry

```toml
# config/config.toml

[strategies.ma_crossover]
enabled = true
category = "trend"
timeframes = ["1h", "4h", "1d"]
risk_level = "medium"
description = "Moving Average Crossover Strategy"

[strategies.ma_crossover.defaults]
fast_window = 20
slow_window = 50
```

### 11.2 Experiment-Tracking

```python
from src.core.experiments import ExperimentTracker

tracker = ExperimentTracker(base_dir="reports/experiments")

# Experiment starten
exp_id = tracker.start_experiment(
    name="ma_crossover_sweep",
    strategy="ma_crossover",
    params={"fast_window": [10, 20, 30], "slow_window": [50, 100]},
)

# Ergebnisse loggen
for run_result in sweep_results:
    tracker.log_run(exp_id, run_result)

# Experiment abschließen
tracker.finish_experiment(exp_id)
```

### 11.3 Experiment-Explorer

```bash
# Alle Experimente auflisten
python scripts/experiments_explorer.py list

# Details zu Experiment
python scripts/experiments_explorer.py show --id exp_20241207_123456

# Vergleich mehrerer Experimente
python scripts/experiments_explorer.py compare \
  --ids exp_001 exp_002 exp_003
```

---

## 12. Configuration-Management

### 12.1 Haupt-Config (config/config.toml)

```toml
[general]
project_name = "Peak_Trade"
log_level = "INFO"
default_symbol = "BTC/EUR"
default_timeframe = "1h"

[data]
cache_dir = "data/cache"
default_exchange = "kraken"

[backtest]
initial_capital = 10000.0
fee_rate = 0.001
slippage_bps = 5.0
position_size_pct = 0.95

[environment]
mode = "paper"
enable_live_trading = false
require_confirm_token = true
testnet_dry_run = true

[live_risk]
max_order_notional = 5000.0
max_symbol_exposure = 10000.0
max_total_exposure = 50000.0
max_daily_loss_pct = 0.05

[alerts]
enabled = true
sinks = ["console", "file"]

[alerts.slack]
enabled = false
webhook_url = ""
```

### 12.2 Portfolio-Recipes (config/portfolio_recipes.toml)

```toml
[portfolio_recipes.conservative]
description = "Konservatives Portfolio mit niedrigem Risiko"
risk_profile = "conservative"
max_drawdown_target = 0.10

[[portfolio_recipes.conservative.strategies]]
name = "ma_crossover"
weight = 0.50
params = { fast_window = 50, slow_window = 200 }

[[portfolio_recipes.conservative.strategies]]
name = "rsi_reversion"
weight = 0.50
params = { period = 14, oversold = 25, overbought = 75 }
```

### 12.3 Sweep-Config (config/sweeps/ma_crossover.toml)

```toml
[sweep]
strategy = "ma_crossover"
symbol = "BTC/EUR"
timeframe = "1h"

[sweep.parameters]
fast_window = [10, 20, 30, 40, 50]
slow_window = [50, 100, 150, 200]

[sweep.metrics]
primary = "sharpe_ratio"
secondary = ["total_return", "max_drawdown"]

[sweep.filters]
min_trades = 20
min_sharpe = 0.5
```

---

## 13. CLI-Tools & Scripts

### 13.1 Research & Backtesting

| Script | Beschreibung |
|--------|--------------|
| `research_cli.py` | Haupt-Research-CLI (run, portfolio, pipeline) |
| `run_backtest.py` | Einzelner Backtest |
| `run_strategy_sweep.py` | Parameter-Sweep |
| `run_portfolio_backtest.py` | Portfolio-Backtest |
| `run_monte_carlo_robustness.py` | Monte-Carlo Simulation |
| `run_walkforward_backtest.py` | Walk-Forward Test |
| `run_stress_tests.py` | Stress-Tests |

### 13.2 Live & Operations

| Script | Beschreibung |
|--------|--------------|
| `live_ops.py` | Live-Ops CLI (health, portfolio, orders) |
| `generate_live_status_report.py` | Status-Report generieren |
| `live_monitor_cli.py` | Run-Monitoring |
| `live_alerts_cli.py` | Alert-Management |
| `run_shadow_paper_session.py` | Shadow/Paper Session |
| `run_testnet_session.py` | Testnet Session |

### 13.3 Analysis & Reporting

| Script | Beschreibung |
|--------|--------------|
| `analyze_experiments.py` | Experiment-Analyse |
| `experiments_explorer.py` | Experiment-Browser |
| `generate_backtest_report.py` | Backtest-Report |
| `generate_sweep_html_report.py` | Sweep-HTML-Report |
| `plot_sweep_results.py` | Sweep-Visualisierung |

### 13.4 Beispiel-Aufrufe

```bash
# Research: Strategie testen
python scripts/research_cli.py run \
  --strategy rsi_reversion \
  --symbol BTC/EUR \
  --timeframe 1h \
  --start 2024-01-01 \
  --end 2024-12-01

# Parameter-Sweep
python scripts/run_strategy_sweep.py \
  --strategy ma_crossover \
  --sweep-config config/sweeps/ma_crossover.toml \
  --output-dir reports/sweeps

# Portfolio-Robustness
python scripts/run_portfolio_robustness.py \
  --portfolio-preset multi_style_moderate \
  --mc-simulations 1000 \
  --stress-scenarios all

# Live-Status
python scripts/live_ops.py health
python scripts/live_ops.py portfolio --json

# Report generieren
python scripts/generate_live_status_report.py \
  --output-dir reports/live_status \
  --format both
```

---

## 14. Test-Suite & Qualitätssicherung

### 14.1 Test-Übersicht

| Kategorie | Anzahl Tests | Coverage |
|-----------|--------------|----------|
| Data/Loader | ~50 | ~95% |
| Backtest | ~150 | ~90% |
| Strategies | ~200 | ~85% |
| Risk/Safety | ~100 | ~95% |
| Live/Testnet | ~150 | ~90% |
| Execution | ~50 | ~95% |
| Reporting | ~100 | ~85% |
| Integration | ~200 | ~80% |
| **Gesamt** | **~1870** | **~90%** |

### 14.2 Test-Ausführung

```bash
# Alle Tests
pytest

# Mit Coverage
pytest --cov=src --cov-report=html

# Nur bestimmte Module
pytest tests/test_backtest*.py -v

# Schneller Smoke-Test
pytest -m "not slow" -q

# Nur Integration-Tests
pytest tests/test_*_integration.py -v
```

### 14.3 Test-Kategorien

```python
# tests/test_execution_pipeline.py

class TestExecutionPipelineWithSafety:
    """Tests für execute_with_safety() Methode."""

    def test_execution_pipeline_blocks_live_mode(self):
        """LIVE-Mode wird blockiert."""
        ...

    def test_execution_pipeline_runs_safety_and_blocks_on_violation(self):
        """SafetyGuard blockiert bei Verletzung."""
        ...

    def test_execution_pipeline_executes_orders_when_safe(self):
        """Orders werden ausgeführt wenn alle Checks passieren."""
        ...

    def test_execution_pipeline_blocks_on_risk_violation(self):
        """Risk-Limits blockieren bei Verletzung."""
        ...

    def test_execution_pipeline_logs_events_when_logger_configured(self):
        """Events werden geloggt."""
        ...
```

---

## 15. Governance & Dokumentation

### 15.1 Governance-Prozesse

| Prozess | Dokument | Beschreibung |
|---------|----------|--------------|
| Research → Live | `PLAYBOOK_RESEARCH_TO_LIVE_PORTFOLIOS.md` | Freigabe-Workflow |
| Live-Readiness | `LIVE_READINESS_CHECKLISTS.md` | Checklisten |
| Incident-Handling | `RUNBOOKS_AND_INCIDENT_HANDLING.md` | Runbooks |
| Drills | `INCIDENT_SIMULATION_AND_DRILLS.md` | Übungs-Szenarien |
| Safety-Policy | `GOVERNANCE_AND_SAFETY_OVERVIEW.md` | Safety-Richtlinien |

### 15.2 Go/No-Go Kriterien

```markdown
## Research → Testnet

- [ ] Sharpe Ratio >= 1.0
- [ ] Max Drawdown <= 20%
- [ ] Profit Factor >= 1.3
- [ ] Min. 50 Trades im Backtest
- [ ] Walk-Forward OOS Sharpe >= 0.8
- [ ] Monte-Carlo 5% VaR akzeptabel

## Testnet → Live

- [ ] 30 Tage Shadow-Run ohne kritische Issues
- [ ] Risk-Limits validiert
- [ ] Incident-Drill durchgeführt
- [ ] Zwei-Augen-Prinzip für Freigabe
- [ ] Confirm-Token dokumentiert
```

### 15.3 Dokumentations-Struktur

```
docs/
├── Onboarding/
│   ├── GETTING_STARTED.md
│   ├── PEAK_TRADE_FIRST_7_DAYS.md
│   └── README.md
│
├── Architecture/
│   ├── ARCHITECTURE_OVERVIEW.md
│   ├── ARCHITECTURE.md
│   └── BACKTEST_ENGINE.md
│
├── Research/
│   ├── REGISTRY_BACKTEST_API.md
│   ├── HYPERPARAM_SWEEPS.md
│   └── PORTFOLIO_RECIPES_AND_PRESETS.md
│
├── Live-Operations/
│   ├── LIVE_TESTNET_TRACK_STATUS.md
│   ├── LIVE_OPERATIONAL_RUNBOOKS.md
│   ├── LIVE_STATUS_REPORTS.md
│   └── LIVE_RISK_LIMITS.md
│
├── Governance/
│   ├── GOVERNANCE_AND_SAFETY_OVERVIEW.md
│   ├── INCIDENT_SIMULATION_AND_DRILLS.md
│   └── PLAYBOOK_RESEARCH_TO_LIVE_PORTFOLIOS.md
│
└── Phases/
    ├── PHASE_16A_EXECUTION_PIPELINE.md
    ├── PHASE_71_LIVE_EXECUTION_DESIGN_AND_GATING.md
    └── ...
```

---

## 16. Projekt-Status & Roadmap

### 16.1 Aktueller Status (Stand: 2025-12-07)

| Bereich | Status | Trend |
|---------|--------|-------|
| Data-Layer | **85%** | → |
| Backtest-Engine | **80%** | → |
| Strategy-Layer | **58%** | ↑ |
| Risk-Layer | **75%** | → |
| Registry & Experimente | **85%** | ↑ |
| Reporting | **80%** | ↑ |
| Live/Testnet-Infra | **60%** | → |
| Governance & Safety | **90%** | → |
| Monitoring & Ops | **65%** | → |

**Gesamtstand:** ~75% (v1 Research + Testnet-ready)

### 16.2 Abgeschlossene Phasen (Auswahl)

| Phase | Titel | Status |
|-------|-------|--------|
| 1-15 | Core Framework | ✅ |
| 16A | ExecutionPipeline | ✅ |
| 17-25 | Safety & Environment | ✅ |
| 26-35 | Live-Ops & Monitoring | ✅ |
| 36-40 | Testnet-Integration | ✅ |
| 41-45 | Research-Pipeline v2 | ✅ |
| 46-50 | Portfolio-Robustness | ✅ |
| 51-60 | Live-Alerts & Status | ✅ |
| 61-70 | Governance & Drills | ✅ |
| 71-74 | Live-Execution-Design | ✅ |

### 16.3 Roadmap (Nächste Schritte)

| Prio | Thema | Phase |
|------|-------|-------|
| 1 | Strategie-Bibliothek erweitern | 75+ |
| 2 | Portfolio-Multi-Asset | 76+ |
| 3 | ML-basierte Strategien | 80+ |
| 4 | Live-Execution (echte Orders) | 85+ |
| 5 | Web-Dashboard v1 | 90+ |

---

## 17. Quickstart-Guide

### 17.1 Installation

```bash
# Repository klonen
git clone <repo-url> Peak_Trade
cd Peak_Trade

# Virtuelle Umgebung erstellen
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Dependencies installieren
pip install -r requirements.txt

# Installation prüfen
python -c "from src.backtest import BacktestEngine; print('OK')"
```

### 17.2 Erster Backtest

```bash
# MA Crossover auf BTC/EUR testen
python scripts/research_cli.py run \
  --strategy ma_crossover \
  --symbol BTC/EUR \
  --timeframe 1h \
  --start 2024-01-01 \
  --end 2024-06-01
```

### 17.3 Portfolio-Test

```bash
# Portfolio-Preset testen
python scripts/research_cli.py portfolio \
  --portfolio-preset rsi_reversion_conservative \
  --format both
```

### 17.4 Live-Ops Check

```bash
# System-Health prüfen
python scripts/live_ops.py health --config config/config.toml

# Portfolio-Status (Paper-Mode)
python scripts/live_ops.py portfolio --config config/config.toml
```

### 17.5 Tests ausführen

```bash
# Alle Tests
pytest -v

# Schneller Check
pytest tests/test_execution_pipeline.py -v
```

---

## 18. Anhang: Dateistruktur


### Vollständige Verzeichnisstruktur

```
Peak_Trade/
│
├── 📁 src/                              # Hauptcode (~53.000 Zeilen)
│   │
│   ├── 📁 analytics/                    # Experiment-Analyse
│   │   ├── __init__.py
│   │   ├── experiments_analysis.py      # Experiment-Auswertung
│   │   ├── explorer.py                  # Experiment-Explorer
│   │   ├── filter_flow.py               # Filter-Pipeline
│   │   ├── leaderboard.py               # Leaderboard-Generierung
│   │   ├── notebook_helpers.py          # Jupyter-Helpers
│   │   ├── portfolio_builder.py         # Portfolio-Builder
│   │   ├── regimes.py                   # Regime-Analyse
│   │   └── risk_monitor.py              # Risk-Monitoring
│   │
│   ├── 📁 backtest/                     # Backtest-Engine
│   │   ├── __init__.py
│   │   ├── engine.py                    # ⭐ BacktestEngine
│   │   ├── registry_engine.py           # Registry-Integration
│   │   ├── reporting.py                 # Backtest-Reporting
│   │   ├── result.py                    # Result-Typen
│   │   ├── stats.py                     # Metriken-Berechnung
│   │   └── walkforward.py               # Walk-Forward-Testing
│   │
│   ├── 📁 core/                         # Kern-Module
│   │   ├── __init__.py
│   │   ├── config_pydantic.py           # Pydantic-Validierung
│   │   ├── config_registry.py           # Strategy-Registry
│   │   ├── config_simple.py             # Einfache Config
│   │   ├── environment.py               # ⭐ Environment-Modi
│   │   ├── experiments.py               # Experiment-Tracking
│   │   ├── peak_config.py               # ⭐ TOML-Config
│   │   ├── position_sizing.py           # Position-Sizing
│   │   ├── regime.py                    # Regime-Typen
│   │   └── risk.py                      # Risk-Typen
│   │
│   ├── 📁 data/                         # Daten-Layer
│   │   ├── __init__.py
│   │   ├── cache.py                     # Parquet-Cache
│   │   ├── kraken.py                    # Kraken-API
│   │   ├── kraken_live.py               # Live-Daten
│   │   ├── kraken_pipeline.py           # Daten-Pipeline
│   │   ├── loader.py                    # CSV-Loader
│   │   └── normalizer.py                # Daten-Normalisierung
│   │
│   ├── 📁 exchange/                     # Exchange-Clients
│   │   ├── __init__.py
│   │   ├── base.py                      # Base-Interface
│   │   ├── ccxt_client.py               # CCXT-Integration
│   │   ├── dummy_client.py              # Dummy für Tests
│   │   └── kraken_testnet.py            # Kraken Testnet
│   │
│   ├── 📁 execution/                    # Execution-Pipeline
│   │   ├── __init__.py
│   │   └── pipeline.py                  # ⭐ ExecutionPipeline
│   │
│   ├── 📁 experiments/                  # Experiment-Module
│   │   ├── __init__.py
│   │   ├── base.py                      # Base-Experiment
│   │   ├── monte_carlo.py               # Monte-Carlo
│   │   ├── portfolio_recipes.py         # Portfolio-Recipes
│   │   ├── portfolio_robustness.py      # Portfolio-Robustness
│   │   ├── regime_aware_portfolio_sweeps.py
│   │   ├── regime_sweeps.py             # Regime-Sweeps
│   │   ├── research_playground.py       # Research-Playground
│   │   ├── strategy_sweeps.py           # Strategy-Sweeps
│   │   ├── stress_tests.py              # Stress-Tests
│   │   └── topn_promotion.py            # Top-N Promotion
│   │
│   ├── 📁 forward/                      # Forward-Signals
│   │   ├── __init__.py
│   │   └── signals.py                   # Signal-Generierung
│   │
│   ├── 📁 live/                         # Live/Testnet-Layer
│   │   ├── __init__.py
│   │   ├── alert_manager.py             # Alert-Management
│   │   ├── alert_rules.py               # Alert-Regeln
│   │   ├── alerts.py                    # Alert-System
│   │   ├── audit.py                     # Audit-Export
│   │   ├── broker_base.py               # Broker-Interface
│   │   ├── drills.py                    # Incident-Drills
│   │   ├── monitoring.py                # Live-Monitoring
│   │   ├── orders.py                    # Live-Orders
│   │   ├── portfolio_monitor.py         # Portfolio-Monitor
│   │   ├── risk_limits.py               # ⭐ LiveRiskLimits
│   │   ├── run_logging.py               # Run-Logging
│   │   ├── safety.py                    # ⭐ SafetyGuard
│   │   ├── shadow_session.py            # Shadow-Session
│   │   ├── testnet_limits.py            # Testnet-Limits
│   │   ├── testnet_orchestrator.py      # Testnet-Orchestrator
│   │   ├── testnet_profiles.py          # Testnet-Profile
│   │   └── workflows.py                 # Live-Workflows
│   │
│   ├── 📁 notifications/                # Benachrichtigungen
│   │   ├── __init__.py
│   │   ├── base.py                      # Notifier-Interface
│   │   ├── combined.py                  # Multi-Notifier
│   │   ├── console.py                   # Console-Output
│   │   └── file.py                      # File-Logging
│   │
│   ├── 📁 orders/                       # Order-Layer
│   │   ├── __init__.py
│   │   ├── base.py                      # ⭐ OrderRequest, OrderExecutor
│   │   ├── exchange.py                  # Exchange-Executors
│   │   ├── mappers.py                   # Order-Mapper
│   │   ├── paper.py                     # Paper-Executor
│   │   ├── shadow.py                    # Shadow-Executor
│   │   └── testnet_executor.py          # Testnet-Executor
│   │
│   ├── 📁 portfolio/                    # Portfolio-Layer
│   │   ├── __init__.py
│   │   ├── base.py                      # Portfolio-Interface
│   │   ├── config.py                    # Portfolio-Config
│   │   ├── equal_weight.py              # Equal-Weight
│   │   ├── fixed_weights.py             # Fixed-Weights
│   │   ├── manager.py                   # ⭐ PortfolioManager
│   │   └── vol_target.py                # Vol-Targeting
│   │
│   ├── 📁 regime/                       # Regime-Detection
│   │   ├── __init__.py
│   │   ├── base.py                      # Regime-Interface
│   │   ├── config.py                    # Regime-Config
│   │   ├── detectors.py                 # Regime-Detectors
│   │   └── switching.py                 # Regime-Switching
│   │
│   ├── 📁 reporting/                    # Reporting
│   │   ├── __init__.py
│   │   ├── backtest_report.py           # Backtest-Reports
│   │   ├── base.py                      # Report-Interface
│   │   ├── execution_plots.py           # Execution-Plots
│   │   ├── execution_reports.py         # Execution-Reports
│   │   ├── experiment_report.py         # Experiment-Reports
│   │   ├── html_reports.py              # HTML-Generierung
│   │   ├── live_run_report.py           # Live-Run-Reports
│   │   ├── live_status_report.py        # Live-Status-Reports
│   │   ├── monte_carlo_report.py        # MC-Reports
│   │   ├── plots.py                     # Plot-Funktionen
│   │   ├── portfolio_robustness_report.py
│   │   ├── regime_reporting.py          # Regime-Reports
│   │   ├── stress_test_report.py        # Stress-Test-Reports
│   │   ├── sweep_visualization.py       # Sweep-Visualisierung
│   │   └── walkforward_report.py        # WF-Reports
│   │
│   ├── 📁 risk/                         # Risk-Management
│   │   ├── __init__.py
│   │   ├── limits.py                    # Risk-Limits
│   │   └── position_sizer.py            # ⭐ Position-Sizing
│   │
│   ├── 📁 scheduler/                    # Job-Scheduling
│   │   ├── __init__.py
│   │   ├── config_loader.py             # Config-Loader
│   │   ├── models.py                    # Job-Models
│   │   └── runner.py                    # Job-Runner
│   │
│   ├── 📁 strategies/                   # Strategien
│   │   ├── __init__.py
│   │   ├── base.py                      # ⭐ BaseStrategy
│   │   ├── bollinger.py                 # Bollinger Bands
│   │   ├── breakout.py                  # Breakout
│   │   ├── breakout_donchian.py         # Donchian Breakout
│   │   ├── composite.py                 # Composite-Strategy
│   │   ├── ecm.py                       # ECM-Strategy
│   │   ├── ma_crossover.py              # ⭐ MA Crossover
│   │   ├── macd.py                      # MACD
│   │   ├── mean_reversion.py            # Mean-Reversion
│   │   ├── mean_reversion_channel.py    # Keltner Channel
│   │   ├── momentum.py                  # Momentum
│   │   ├── my_strategy.py               # Custom-Template
│   │   ├── regime_aware_portfolio.py    # Regime-Portfolio
│   │   ├── registry.py                  # Strategy-Registry
│   │   ├── rsi.py                       # RSI
│   │   ├── rsi_reversion.py             # RSI-Reversion
│   │   ├── trend_following.py           # Trend-Following
│   │   ├── vol_breakout.py              # Vol-Breakout
│   │   └── vol_regime_filter.py         # Vol-Regime-Filter
│   │
│   └── 📁 sweeps/                       # Parameter-Sweeps
│       ├── __init__.py
│       └── engine.py                    # Sweep-Engine
│
├── 📁 scripts/                          # CLI-Tools (~96 Dateien)
│   ├── research_cli.py                  # ⭐ Haupt-Research-CLI
│   ├── live_ops.py                      # ⭐ Live-Operations
│   ├── run_backtest.py                  # Backtest
│   ├── run_strategy_sweep.py            # Sweeps
│   ├── run_portfolio_backtest.py        # Portfolio-Backtest
│   ├── run_monte_carlo_robustness.py    # Monte-Carlo
│   ├── run_walkforward_backtest.py      # Walk-Forward
│   ├── run_stress_tests.py              # Stress-Tests
│   ├── generate_live_status_report.py   # Status-Reports
│   ├── experiments_explorer.py          # Experiment-Explorer
│   └── ...                              # Weitere Scripts
│
├── 📁 tests/                            # Unit-Tests (~96 Dateien)
│   ├── conftest.py                      # pytest-Fixtures
│   ├── test_execution_pipeline.py       # Pipeline-Tests
│   ├── test_backtest_smoke.py           # Backtest-Tests
│   ├── test_strategies_smoke.py         # Strategy-Tests
│   ├── test_live_risk_limits*.py        # Risk-Tests
│   └── ...                              # Weitere Tests
│
├── 📁 docs/                             # Dokumentation (~121 Dateien)
│   ├── GETTING_STARTED.md               # Onboarding
│   ├── ARCHITECTURE_OVERVIEW.md         # Architektur
│   ├── PEAK_TRADE_V1_OVERVIEW_FULL.md   # Vollständige Übersicht
│   ├── GOVERNANCE_AND_SAFETY_OVERVIEW.md
│   └── ...                              # Weitere Docs
│
├── 📁 config/                           # Konfiguration
│   ├── config.toml                      # ⭐ Haupt-Config
│   ├── config.test.toml                 # Test-Config
│   ├── portfolio_recipes.toml           # Portfolio-Presets
│   ├── regimes.toml                     # Regime-Config
│   └── 📁 sweeps/                       # Sweep-Configs
│       ├── ma_crossover.toml
│       ├── rsi_reversion.toml
│       └── ...
│
├── 📁 reports/                          # Generierte Reports
│   ├── 📁 experiments/                  # Experiment-Reports
│   ├── 📁 sweeps/                       # Sweep-Reports
│   ├── 📁 portfolio/                    # Portfolio-Reports
│   ├── 📁 live/                         # Live-Reports
│   └── 📁 monte_carlo/                  # MC-Reports
│
├── 📁 data/                             # Marktdaten
│   ├── 📁 cache/                        # Parquet-Cache
│   └── 📁 raw/                          # Rohdaten
│
├── 📁 notebooks/                        # Jupyter-Notebooks
│   ├── Experiments_Overview.ipynb
│   ├── Portfolio_Analysis.ipynb
│   └── Sweep_Analysis.ipynb
│
├── .venv/                               # Virtuelle Umgebung
├── requirements.txt                     # Dependencies
├── pyproject.toml                       # Projekt-Config
├── pytest.ini                           # pytest-Config
└── README.md                            # Landing Page
```

---

## Kontakt & Lizenz

**Projekt:** Peak_Trade  
**Autor:** Franky  
**Stand:** 2025-12-07  
**Lizenz:** Privates Projekt – alle Rechte vorbehalten

---

## Disclaimer

⚠️ **Trading birgt erhebliche Risiken.** Dieses Projekt dient zu Bildungs- und Forschungszwecken. Verwende niemals Kapital, dessen Verlust du dir nicht leisten kannst. Peak_Trade ist kein Finanzberater und gibt keine Anlageempfehlungen.

---

*Dokumentation generiert am 2025-12-07*
