# Peak_Trade – Architektur & Entwicklung (Phasen 1–17)

**Stand:** Dezember 2024
**Version:** Phase 17 abgeschlossen

---

## 1. Einleitung

### 1.1 Was ist Peak_Trade?

Peak_Trade ist ein modulares **Python-Trading-Framework** für systematisches Research, Backtesting und (zukünftig) automatisiertes Trading von Kryptowährungen und anderen Asset-Klassen.

Das Framework ist als **`src`-Layout** organisiert (Paket `peak_trade`) und folgt dem Prinzip der strikten Trennung von:

- Datenakquisition
- Strategielogik
- Risikomanagement
- Order-Execution
- Reporting & Analytics

### 1.2 Projektziele

| Ziel | Beschreibung |
|------|--------------|
| **Research-Framework** | Schnelles Prototyping und Backtesting von Trading-Strategien |
| **Risk-First-Ansatz** | Integriertes Risikomanagement auf allen Ebenen |
| **Nachvollziehbarkeit** | Experiment-Registry, Audit-Logs, reproduzierbare Ergebnisse |
| **Modularität** | Austauschbare Komponenten (Strategien, Executors, Risk-Layer) |
| **Safety-by-Design** | Mehrstufige Absicherung für zukünftiges Live-Trading |

### 1.3 Aktueller Stand

**Paper-Only-Betrieb:** Peak_Trade sendet aktuell **keine echten Orders** an Börsen. Alle Funktionen arbeiten im Paper-/Backtest-/Dry-Run-Modus. Die Architektur ist jedoch so aufgebaut, dass ein kontrollierter Übergang zu Testnet/Live möglich ist.

---

## 2. High-Level Architektur

### 2.1 Schichtenmodell

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CONFIG & REGISTRY                              │
│         config.toml  |  PeakConfig  |  StrategyRegistry  |  Experiments     │
└─────────────────────────────────────────────────────────────────────────────┘
                                       │
         ┌─────────────────────────────┼─────────────────────────────┐
         ▼                             ▼                             ▼
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│   DATA-LAYER    │         │ STRATEGY-LAYER  │         │   RISK-LAYER    │
│                 │         │                 │         │                 │
│ • Loader        │ ──────▶ │ • BaseStrategy  │ ──────▶ │ • PositionSizer │
│ • Cache         │         │ • MA Crossover  │         │ • RiskManager   │
│ • Normalizer    │         │ • MACD, RSI ... │         │ • LiveRiskLimits│
│ • Kraken API    │         │ • Registry      │         │                 │
└─────────────────┘         └─────────────────┘         └─────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           EXECUTION-LAYER (Phase 16)                        │
│                                                                             │
│   Signals (-1/0/+1)  ──▶  ExecutionPipeline  ──▶  OrderRequests  ──▶  Fills│
└─────────────────────────────────────────────────────────────────────────────┘
                                       │
         ┌─────────────────────────────┼─────────────────────────────┐
         ▼                             ▼                             ▼
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│  ORDER-LAYER    │         │ BACKTEST-ENGINE │         │ SAFETY-LAYER    │
│                 │         │                 │         │   (Phase 17)    │
│ • OrderRequest  │         │ • Bar-für-Bar   │         │                 │
│ • PaperExecutor │         │ • Trade-Logging │         │ • SafetyGuard   │
│ • TestnetExec   │         │ • Equity-Kurve  │         │ • Environment   │
│   (Dry-Run)     │         │ • Statistics    │         │ • Dry-Run-Stubs │
└─────────────────┘         └─────────────────┘         └─────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         REPORTING & ANALYTICS                               │
│                                                                             │
│  BacktestResult  |  ExecutionStats  |  Leaderboard  |  Portfolio-Builder   │
└─────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      SCHEDULER & NOTIFICATIONS                              │
│                                                                             │
│         JobScheduler  |  AlertNotifier  |  Experiment-Registry              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Hauptkomponenten

| Layer | Module | Zweck |
|-------|--------|-------|
| **Data** | `src/data/` | OHLCV-Daten laden, normalisieren, cachen |
| **Strategies** | `src/strategies/` | Strategie-Implementierungen, Registry |
| **Backtest** | `src/backtest/` | BacktestEngine, Statistiken, Portfolio-Backtests |
| **Risk** | `src/core/risk.py`, `src/core/position_sizing.py` | Position Sizing, Drawdown-Management |
| **Live-Risk** | `src/live/risk_limits.py` | Order-Batch-Limits, Daily-Loss-Limits |
| **Orders** | `src/orders/` | OrderRequest, Executors, Mappers |
| **Execution** | `src/execution/` | ExecutionPipeline, Signal-zu-Order-Transformation |
| **Reporting** | `src/reporting/` | ExecutionStats, Plots, Reports |
| **Analytics** | `src/analytics/` | Experiment-Analyse, Leaderboard, Portfolio-Builder |
| **Scheduler** | `src/scheduler/` | Job-Scheduling, periodische Ausführung |
| **Notifications** | `src/notifications/` | Alert-System (Console, File) |
| **Environment** | `src/core/environment.py` | Trading-Umgebungen (paper/testnet/live) |
| **Safety** | `src/live/safety.py` | SafetyGuard, Absicherung |

---

## 3. Phasenübersicht (1–17)

### 3.1 Übersichtstabelle

| Phase | Titel | Kernziel | Wichtige Module |
|-------|-------|----------|-----------------|
| 1 | Projekt-Setup | Grundstruktur, Dependencies | `pyproject.toml`, `src/` |
| 2 | Data-Layer Basis | CSV-Loader, Normalizer | `src/data/loader.py`, `normalizer.py` |
| 3 | Cache & Kraken | Parquet-Cache, Kraken-API | `src/data/cache.py`, `kraken.py` |
| 4 | Erste Strategie | MA-Crossover, Signal-Format | `src/strategies/ma_crossover.py` |
| 5 | BacktestEngine v1 | Erste Backtest-Implementierung | `src/backtest/engine.py` |
| 6 | Statistiken | Sharpe, Drawdown, Win-Rate | `src/backtest/stats.py` |
| 7 | Weitere Strategien | MACD, RSI, Bollinger, Donchian | `src/strategies/*.py` |
| 8 | Strategy-Registry | Zentrale Strategie-Verwaltung | `src/strategies/registry.py` |
| 9 | Risk-Layer Basis | Position Sizing, Risk Management | `src/core/position_sizing.py`, `risk.py` |
| 10 | Portfolio-Backtests | Multi-Asset, Multi-Strategy | `src/backtest/registry_engine.py` |
| 11 | Experiments-Registry | Run-Tracking, CSV-Persistenz | `src/core/experiments.py` |
| 12 | Scheduler | Job-Scheduling, Daemon | `src/scheduler/` |
| 13 | Notifications | Alert-System | `src/notifications/` |
| 14 | Live-Risk-Limits | Order-Batch-Limits | `src/live/risk_limits.py` |
| 15 | Order-Layer | OrderRequest, PaperExecutor | `src/orders/` |
| 16 | Execution-Layer | ExecutionPipeline, Reporting | `src/execution/`, `src/reporting/` |
| 17 | Environment & Safety | SafetyGuard, Dry-Run-Executors | `src/core/environment.py`, `src/live/safety.py` |

### 3.2 Detaillierte Phasenbeschreibungen

#### Phasen 1–5: Foundation

**Phase 1–3 (Data-Layer):**
- Projekt-Setup mit `pyproject.toml` und `src`-Layout
- `CsvLoader` für flexible CSV-Imports
- `KrakenCsvLoader` für Kraken-spezifische OHLC-Exporte
- `ParquetCache` für schnelles Laden großer Datensätze
- `Normalizer` für einheitliches OHLCV-Format (DatetimeIndex, UTC)
- `fetch_ohlcv_df()` für ccxt-basierte Kraken-Abfragen

**Phase 4–5 (Erste Strategie & Backtest):**
- Etablierung des Signal-Formats: `-1` (Short), `0` (Flat), `+1` (Long)
- `BaseStrategy` als abstrakte Basisklasse
- MA-Crossover als erste vollständige Strategie
- `BacktestEngine` mit Bar-für-Bar-Simulation
- `Trade`-Dataclass für Entry/Exit-Tracking

#### Phasen 6–10: Erweiterung

**Phase 6–7 (Statistiken & Strategien):**
- `calculate_backtest_stats()` mit Sharpe, Sortino, Max Drawdown, etc.
- Zusätzliche Strategien: MACD, RSI Reversion, Bollinger Bands, Momentum, Donchian Breakout
- Einheitliches Interface via `BaseStrategy.from_config()`

**Phase 8 (Strategy-Registry):**
- `StrategySpec` Dataclass mit Metadaten
- Zentrale Registry mit `get_strategy_spec()`, `create_strategy_from_config()`
- Automatische Erkennung verfügbarer Strategien

**Phase 9–10 (Risk & Portfolio):**
- `PositionSizer` Hierarchie: Noop, FixedSize, FixedFraction
- `RiskManager` mit Drawdown-Monitoring
- `RegistryBacktestEngine` für Portfolio-Backtests
- Multi-Asset-Unterstützung mit konfigurierbaren Gewichten

#### Phasen 11–14: Infrastructure

**Phase 11 (Experiments-Registry):**
- `ExperimentRecord` Dataclass für Run-Ergebnisse
- Run-Types: `backtest`, `portfolio_backtest`, `forward_signal`, `live_risk_check`, `paper_trade`, `sweep`, `market_scan`, `scheduler_job`
- CSV-Persistenz in `reports/experiments/experiments.csv`

**Phase 12 (Scheduler):**
- `JobDefinition` und `JobSchedule` Dataclasses
- Schedule-Typen: `once`, `interval`, `daily`, `cron`
- `run_scheduler.py` als Daemon-Script

**Phase 13 (Notifications):**
- `Alert` Dataclass mit Levels (info, warning, critical)
- `Notifier` Protocol für erweiterbare Ziele
- `ConsoleNotifier`, `FileNotifier`, `CombinedNotifier`

**Phase 14 (Live-Risk-Limits):**
- `LiveRiskConfig` mit Exposure-/Loss-Limits
- `LiveRiskLimits` Klasse für Order-Batch-Validation
- Integration mit Experiments-Registry für Daily PnL

#### Phase 15: Order-Layer

- `OrderRequest`: symbol, side, quantity, order_type, limit_price, metadata
- `OrderFill`: Ausgeführte Order mit Preis, Timestamp, Fee
- `OrderExecutionResult`: Status (filled/rejected), Fill, Reason
- `PaperOrderExecutor`: Simulation mit Slippage und Fees
- `PaperMarketContext`: Preise für Paper-Trading
- Mappers zwischen `LiveOrderRequest` und `OrderRequest`

#### Phase 16: Execution-Layer (A–D)

Siehe Abschnitt 4 für Details.

#### Phase 17: Environment & Safety

Siehe Abschnitt 5 für Details.

---

## 4. Fokus: Phase 16 – Execution-Layer

Phase 16 implementiert die vollständige Pipeline von Strategy-Signalen zu ausgeführten Orders.

### 4.1 Phase 16A – ExecutionPipeline Core

**Modul:** `src/execution/pipeline.py`

**Kernkomponenten:**

```python
@dataclass
class SignalEvent:
    timestamp: datetime
    symbol: str
    signal: int  # -1, 0, +1
    price: float
    prev_signal: int
```

```python
class ExecutionPipeline:
    def signal_to_orders(self, event: SignalEvent) -> List[OrderRequest]
    def execute_orders(self, orders: Sequence[OrderRequest]) -> List[OrderExecutionResult]
    def execute_from_signals(self, signals: pd.Series, prices: pd.Series) -> List[OrderExecutionResult]
```

**Workflow:**
1. Strategy erzeugt Signal-Serie (`-1/0/+1`)
2. `SignalEvent` erkennt Signalwechsel (Entry/Exit/Flip)
3. `signal_to_orders()` transformiert zu `OrderRequest`
4. `OrderExecutor` (Paper/Testnet) führt aus
5. `OrderExecutionResult` mit Fill-Details zurück

### 4.2 Phase 16B – BacktestEngine-Integration

**Neue Flags:**

```python
BacktestEngine(
    strategy=strategy,
    use_execution_pipeline=True,  # Aktiviert neuen Execution-Flow
    log_executions=True,          # Speichert alle Fills
)
```

**Methoden:**

- `_run_with_execution_pipeline()`: Verwendet ExecutionPipeline statt direkter Signal-Verarbeitung
- `get_execution_logs()`: Gibt alle `OrderExecutionResult`-Objekte zurück

### 4.3 Phase 16C – Demo-Script

**Script:** `scripts/demo_execution_backtest.py`

**Modi:**

| Modus | Beschreibung |
|-------|--------------|
| `--mode execution` | Nur ExecutionPipeline |
| `--mode legacy` | Traditioneller Backtest |
| `--mode compare` | Beide Modi vergleichen |

**Beispiel:**

```bash
python scripts/demo_execution_backtest.py \
    --symbol BTC/EUR \
    --mode compare \
    --stats \
    --plot
```

### 4.4 Phase 16D – Execution-Reporting

**Modul:** `src/reporting/execution_reports.py`

**`ExecutionStats` Dataclass:**

| Feld | Beschreibung |
|------|--------------|
| `total_orders` | Anzahl generierter Orders |
| `filled_orders` | Anzahl ausgeführter Orders |
| `rejected_orders` | Anzahl abgelehnter Orders |
| `fill_rate` | Ausführungsquote (0–1) |
| `total_fees` | Summe aller Gebühren |
| `total_notional` | Gesamtvolumen |
| `avg_slippage_bps` | Durchschnittliche Slippage |
| `winning_trades` | Gewinn-Trades |
| `losing_trades` | Verlust-Trades |
| `win_rate` | Gewinnquote |
| `avg_hold_bars` | Durchschnittliche Haltedauer |

**Modul:** `src/reporting/execution_plots.py`

- Equity-Kurve mit Trades
- Fill-Histogramm
- Slippage-Verteilung
- Gebühren-Analyse

### 4.5 Order-Flow Diagramm

```text
Strategy.generate_signals(df)
         │
         ▼
    pd.Series [-1, 0, +1, +1, 0, -1, ...]
         │
         ▼
ExecutionPipeline.execute_from_signals()
         │
         ├──▶ SignalEvent(signal=+1, prev=0) ──▶ Entry Long
         │
         ├──▶ signal_to_orders() ──▶ OrderRequest(side="buy")
         │
         ├──▶ OrderExecutor.execute_order()
         │
         └──▶ OrderExecutionResult(status="filled", fill=OrderFill(...))
```

---

## 5. Fokus: Phase 17 – Environment & Safety

Phase 17 etabliert eine robuste Safety-Architektur für zukünftiges Live-Trading, **ohne** echte Orders zu implementieren.

### 5.1 Environment-Modell

**Modul:** `src/core/environment.py`

**TradingEnvironment Enum:**

```python
class TradingEnvironment(str, Enum):
    PAPER = "paper"      # Simulation / Backtest
    TESTNET = "testnet"  # Börsen-Testnet (Dry-Run in Phase 17)
    LIVE = "live"        # Echte Orders (NICHT implementiert)
```

**EnvironmentConfig Dataclass:**

```python
@dataclass
class EnvironmentConfig:
    environment: TradingEnvironment = TradingEnvironment.PAPER
    enable_live_trading: bool = False
    require_confirm_token: bool = True
    confirm_token: str | None = None
    testnet_dry_run: bool = True
    log_all_orders: bool = True
```

**Konfiguration in `config.toml`:**

```toml
[environment]
mode = "paper"              # "paper" | "testnet" | "live"
enable_live_trading = false
require_confirm_token = true
confirm_token = ""          # Muss "I_KNOW_WHAT_I_AM_DOING" sein
testnet_dry_run = true
log_all_orders = true
```

### 5.2 SafetyGuard

**Modul:** `src/live/safety.py`

**Zweck:** Zentraler Wächter für alle potenziell kritischen Operationen.

**Exceptions:**

| Exception | Auslöser |
|-----------|----------|
| `PaperModeOrderError` | Order-Versuch im Paper-Modus |
| `TestnetDryRunOnlyError` | Testnet ist nur als Dry-Run verfügbar |
| `LiveNotImplementedError` | Live-Trading nicht implementiert |
| `LiveTradingDisabledError` | `enable_live_trading = False` |
| `ConfirmTokenInvalidError` | Token fehlt oder falsch |

**Kernmethoden:**

```python
class SafetyGuard:
    def ensure_may_place_order(self, *, is_testnet: bool = False) -> None
    def ensure_not_live(self) -> None
    def ensure_confirm_token(self) -> None
    def may_use_dry_run(self) -> bool
    def get_effective_mode(self) -> str  # "paper", "dry_run", "blocked"
```

### 5.3 Mehrstufige Absicherung

```text
┌─────────────────────────────────────────────────────────────┐
│                     SAFETY-LAYER                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Environment-Modus (paper/testnet/live)                  │
│         │                                                   │
│         ▼                                                   │
│  2. enable_live_trading Flag (muss true sein)               │
│         │                                                   │
│         ▼                                                   │
│  3. Confirm-Token ("I_KNOW_WHAT_I_AM_DOING")                │
│         │                                                   │
│         ▼                                                   │
│  4. testnet_dry_run Flag (blockt echte Testnet-Orders)      │
│         │                                                   │
│         ▼                                                   │
│  5. LiveNotImplementedError (finale Barriere in Phase 17)   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 5.4 Exchange-Executors

**Modul:** `src/orders/exchange.py`

| Executor | Verhalten in Phase 17 |
|----------|----------------------|
| `TestnetOrderExecutor` | Dry-Run mit Logging, simulierte Fills |
| `LiveOrderExecutor` | Stub – wirft `LiveNotImplementedError` |
| `ExchangeOrderExecutor` | Fassade, delegiert je nach Environment |

**TestnetOrderExecutor Dry-Run:**

```python
result = executor.execute_order(order)
# result.metadata["mode"] == "testnet_dry_run"
# result.metadata["dry_run"] == True
# result.metadata["note"] == "KEIN echter API-Call - nur Dry-Run-Simulation"
```

### 5.5 Safety-Statement

| Prüfung | Status |
|---------|--------|
| Echte Orders möglich? | **Nein** |
| Testnet-API-Calls? | **Nein** (nur Dry-Run) |
| Live-API-Calls? | **Nein** (NotImplemented) |
| Alle Pfade durch SafetyGuard? | **Ja** |
| Audit-Logging aktiv? | **Ja** |

---

## 6. Tests & Qualität

### 6.1 Test-Übersicht

| Bereich | Anzahl Tests | Status |
|---------|--------------|--------|
| Data/Loader/Cache | ~30 | ✅ |
| Strategies | ~40 | ✅ |
| Backtest/Engine | ~50 | ✅ |
| Orders/Execution | ~60 | ✅ |
| Reporting | ~20 | ✅ |
| Analytics | ~30 | ✅ |
| Live-Risk | ~25 | ✅ |
| Scheduler/Notifications | ~30 | ✅ |
| Environment/Safety (Phase 17) | 53 | ✅ |
| **Gesamt** | **~400** | ✅ |

### 6.2 Phase 16 Tests

- 141 Tests für Execution-Layer
- Abdeckung: SignalEvent, ExecutionPipeline, BacktestEngine-Integration, Demo-Script, Reporting

### 6.3 Phase 17 Tests

**Datei:** `tests/test_environment_and_safety.py`

| Testklasse | Tests | Fokus |
|------------|-------|-------|
| `TestTradingEnvironment` | 3 | Enum-Werte, String-Konvertierung |
| `TestEnvironmentConfig` | 10 | Defaults, Safety-Flags, allows_real_orders |
| `TestEnvironmentHelpers` | 6 | is_paper, is_testnet, is_live, Config-Parsing |
| `TestSafetyGuard` | 15 | ensure_may_place_order in allen Modi |
| `TestCreateSafetyGuard` | 2 | Factory-Funktion |
| `TestTestnetOrderExecutor` | 9 | Dry-Run-Verhalten, Order-Logging |
| `TestLiveOrderExecutor` | 3 | Stub-Verhalten, Exception |
| `TestExchangeOrderExecutor` | 3 | Environment-Routing |
| `TestSafetyIntegration` | 3 | End-to-End Safety-Checks |

### 6.4 Test-Philosophie

1. **Safety First:** Alle kritischen Pfade sind getestet
2. **Paper vor Live:** Kein Live-Code ohne umfangreiche Paper-Tests
3. **Regression Prevention:** Tests für alle Phasen bleiben grün
4. **Edge Cases:** Fehlkonfiguration, ungültige Token, etc.

---

## 7. Konfiguration

### 7.1 config.toml Struktur

```toml
# ============================================================================
# ENVIRONMENT & SAFETY (Phase 17)
# ============================================================================
[environment]
mode = "paper"
enable_live_trading = false
require_confirm_token = true
confirm_token = ""
testnet_dry_run = true
log_all_orders = true

# ============================================================================
# BACKTEST
# ============================================================================
[backtest]
initial_cash = 10_000.0
results_dir = "results"

# ============================================================================
# RISK MANAGEMENT
# ============================================================================
[risk]
risk_per_trade = 0.01
max_position_size = 0.25
max_daily_loss = 0.03
max_drawdown = 0.20

# ============================================================================
# STRATEGIE-KONFIGURATIONEN
# ============================================================================
[strategy.ma_crossover]
fast_window = 20
slow_window = 50
stop_pct = 0.02

[strategy.rsi_reversion]
rsi_window = 14
lower = 30.0
upper = 70.0

# ... weitere Strategien

# ============================================================================
# LIVE-RISK-LIMITS
# ============================================================================
[live_risk]
enabled = true
max_daily_loss_abs = 500.0
max_order_notional = 1000.0
max_open_positions = 10
```

### 7.2 Config-Zugriff

```python
# TOML-basiert (empfohlen)
from src.core.peak_config import load_config
cfg = load_config("config.toml")
fast = cfg.get("strategy.ma_crossover.fast_window", 20)

# Mit Overrides
new_cfg = cfg.with_overrides({"strategy.ma_crossover.fast_window": 10})

# Environment-Config
from src.core.environment import get_environment_from_config
env_config = get_environment_from_config(cfg)
```

---

## 8. Scripts & CLI

### 8.1 Wichtige Scripts

| Script | Zweck |
|--------|-------|
| `scripts/run_backtest.py` | Einzelner Strategie-Backtest |
| `scripts/run_portfolio_backtest.py` | Multi-Asset/Multi-Strategy Backtest |
| `scripts/demo_execution_backtest.py` | ExecutionPipeline Demo |
| `scripts/run_sweep.py` | Parameter-Sweep |
| `scripts/run_market_scan.py` | Markt-Screening |
| `scripts/run_scheduler.py` | Scheduler-Daemon |
| `scripts/generate_forward_signals.py` | Out-of-Sample Signale |
| `scripts/select_live_candidates.py` | Strategie-Auswahl |

### 8.2 Demo-Script Beispiel

```bash
# ExecutionPipeline Demo mit Stats und Plot
python scripts/demo_execution_backtest.py \
    --symbol BTC/EUR \
    --bars 500 \
    --mode compare \
    --stats \
    --plot \
    --output-dir reports/execution/
```

---

## 9. Aktueller Status & Ausblick

### 9.1 Aktueller Stand

**Peak_Trade ist ein voll funktionsfähiges Research- und Backtest-Framework:**

- ✅ 6+ Strategien mit einheitlichem Interface
- ✅ Vollständige BacktestEngine mit Risk-Management
- ✅ ExecutionPipeline für Signal-zu-Order-Transformation
- ✅ Execution-Reporting mit detaillierten Statistiken
- ✅ Experiment-Registry für Run-Tracking
- ✅ Scheduler für automatisierte Jobs
- ✅ Safety-Layer mit mehrstufiger Absicherung
- ✅ ~400 Tests grün

**Paper-Only:** Es werden keine echten Orders gesendet.

### 9.2 Mögliche nächste Phasen

| Phase | Titel | Beschreibung |
|-------|-------|--------------|
| 18 | Testnet-Integration | Echte Testnet-API-Calls mit harten Limits |
| 19 | UI/Dashboard | Web-basiertes Reporting-Dashboard |
| 20 | Portfolio-Execution | Multi-Account, Rebalancing |
| 21+ | Live-Trading | Streng limitiertes Live-Trading |

> **Hinweis:** Diese Phasen sind nicht geplant oder implementiert.
> Sie dienen nur als möglicher Ausblick.

---

## 10. Glossar

| Begriff | Definition |
|---------|------------|
| **Signal** | Strategieausgabe: -1 (Short), 0 (Flat), +1 (Long) |
| **SignalEvent** | Einzelnes Signal mit Timestamp und Preiskontext |
| **OrderRequest** | Anfrage für eine Order (symbol, side, quantity) |
| **OrderFill** | Ausgeführte Order mit Preis und Fees |
| **ExecutionPipeline** | Transformiert Signale zu Orders und Fills |
| **SafetyGuard** | Zentrale Absicherung gegen unbeabsichtigte Orders |
| **Dry-Run** | Simulation ohne echte API-Calls |
| **Paper-Trading** | Backtest mit realistischer Order-Simulation |
| **Environment** | Trading-Kontext (paper/testnet/live) |

---

## 11. Dateien & Module

### 11.1 Verzeichnisstruktur

```
Peak_Trade/
├── config.toml                 # Hauptkonfiguration
├── pyproject.toml              # Python-Package-Definition
├── src/
│   ├── __init__.py
│   ├── analytics/              # Experiment-Analyse, Portfolio-Builder
│   ├── backtest/               # BacktestEngine, Stats
│   ├── core/                   # Config, Risk, Environment
│   ├── data/                   # Loader, Cache, Kraken
│   ├── execution/              # ExecutionPipeline
│   ├── exchange/               # Exchange-Abstraktion
│   ├── forward/                # Forward-Signale
│   ├── live/                   # Live-Risk, Safety
│   ├── notifications/          # Alert-System
│   ├── orders/                 # Order-Layer
│   ├── reporting/              # Execution-Reports, Plots
│   ├── scheduler/              # Job-Scheduler
│   └── strategies/             # Strategie-Implementierungen
├── scripts/                    # CLI-Scripts
├── tests/                      # Pytest-Tests
├── docs/                       # Dokumentation
└── reports/                    # Generierte Reports
```

### 11.2 Wichtige Module (Phase 16 & 17)

| Modul | Beschreibung |
|-------|--------------|
| `src/execution/pipeline.py` | ExecutionPipeline, SignalEvent |
| `src/orders/base.py` | OrderRequest, OrderFill, OrderExecutionResult |
| `src/orders/paper.py` | PaperOrderExecutor, PaperMarketContext |
| `src/orders/exchange.py` | Testnet/Live Executors (Dry-Run/Stubs) |
| `src/reporting/execution_reports.py` | ExecutionStats |
| `src/reporting/execution_plots.py` | Visualisierungen |
| `src/core/environment.py` | TradingEnvironment, EnvironmentConfig |
| `src/live/safety.py` | SafetyGuard, Safety-Exceptions |

---

## 12. Kontakt & Lizenz

**Projekt:** Peak_Trade
**Status:** Aktive Entwicklung (Phase 17 abgeschlossen)
**Lizenz:** Proprietär / Nicht öffentlich

---

*Dieses Dokument wurde automatisch generiert und fasst die Architektur und Entwicklung von Peak_Trade bis einschließlich Phase 17 zusammen.*
