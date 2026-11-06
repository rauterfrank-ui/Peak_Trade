# Backtest Engine – Detaildokumentation

> Realistische Bar-für-Bar-Simulation mit vollständigem Risk-Management

---

## Überblick

Die **BacktestEngine** (`src/backtest/engine.py`) ist das Herzstück des Peak_Trade Systems. Sie simuliert Trading bar-für-bar und integriert alle Risk-Management-Komponenten.

**Hauptfeatures:**
- ✅ Bar-für-Bar-Execution (keine Look-Ahead-Bias)
- ✅ Stop-Loss-Management
- ✅ Position Sizing
- ✅ Risk Management (Drawdown, Equity-Floor)
- ✅ Trade-Tracking mit PnL
- ✅ Performance-Metriken

---

## Architektur

### Komponenten

```text
┌────────────────────────────────────────┐
│         BacktestEngine                 │
├────────────────────────────────────────┤
│                                        │
│  ┌──────────────────────────────────┐ │
│  │  Position Sizer (Legacy)         │ │
│  │  - Risk-based sizing             │ │
│  └──────────────────────────────────┘ │
│                                        │
│  ┌──────────────────────────────────┐ │
│  │  Risk Limits (Legacy)            │ │
│  │  - Max Drawdown Check            │ │
│  │  - Daily Loss Check              │ │
│  └──────────────────────────────────┘ │
│                                        │
│  ┌──────────────────────────────────┐ │
│  │  Core Position Sizer (NEW)       │ │
│  │  - FixedFractionSizer            │ │
│  │  - FixedSizeSizer                │ │
│  │  - NoopPositionSizer             │ │
│  └──────────────────────────────────┘ │
│                                        │
│  ┌──────────────────────────────────┐ │
│  │  Risk Manager (NEW)              │ │
│  │  - MaxDrawdownRiskManager        │ │
│  │  - EquityFloorRiskManager        │ │
│  │  - NoopRiskManager               │ │
│  └──────────────────────────────────┘ │
│                                        │
└────────────────────────────────────────┘
```

---

## Initialisierung

### Constructor

```python
from src.backtest.engine import BacktestEngine
from src.core.position_sizing import build_position_sizer_from_config
from src.core.risk import build_risk_manager_from_config

engine = BacktestEngine(
    position_sizer=None,              # Optional: Legacy PositionSizer
    risk_limits=None,                 # Optional: Legacy RiskLimits
    core_position_sizer=position_sizer,  # NEW: Position Sizing
    risk_manager=risk_manager         # NEW: Risk Management
)
```

**Parameter:**
- `position_sizer` – Legacy Risk-basiertes Position Sizing (optional)
- `risk_limits` – Legacy Risk Limits (optional)
- `core_position_sizer` – Neue OOP Position-Sizing-API (empfohlen)
- `risk_manager` – Neue OOP Risk-Management-API (empfohlen)

---

## Execution Modes

### 1. Realistic Mode (`run_realistic()`)

**Empfohlen für alle Backtests**

```python
result = engine.run_realistic(
    df=df,                          # OHLCV DataFrame
    strategy_signal_fn=signal_fn,   # Strategy Function
    strategy_params=params          # Strategy Parameters
)
```

**Features:**
- Bar-für-Bar-Execution
- Stop-Loss-Checks
- Position-Sizing-Integration
- Risk-Limit-Checks
- Trade-Tracking

**Workflow pro Bar:**
1. Stop-Loss-Check (höchste Priorität)
2. Signal-Handling
3. Position-Sizing
4. Risk-Manager-Check
5. Risk-Limits-Check
6. Trade-Execution
7. Equity-Update

### 2. Vectorized Mode (`run_vectorized()`)

⚠️ **WARNUNG: NUR für schnelle Parameter-Tests!**

```python
result = engine.run_vectorized(
    df=df,
    strategy_signal_fn=signal_fn,
    strategy_params=params
)
```

**Einschränkungen:**
- ❌ Kein Stop-Loss
- ❌ Kein Position Sizing
- ❌ Keine Risk-Limits
- ❌ Synthetische PnL-Berechnung

---

## Bar-für-Bar-Logik (Realistic Mode)

### Execution Flow

```python
for i in range(len(df)):
    bar = df.iloc[i]
    signal = signals.iloc[i]

    # 1. STOP-LOSS CHECK (höchste Priorität!)
    if current_trade is not None:
        if bar["low"] <= current_trade.stop_price:
            # Stop wurde getroffen → Position schließen
            close_trade_at_stop()

    # 2. SIGNAL HANDLING
    if signal == 1 and current_trade is None:
        # LONG ENTRY
        entry_price = bar["close"]
        stop_price = entry_price * (1 - stop_pct)

        # Position Sizing
        target_units = core_position_sizer.get_target_position(
            signal=1,
            price=entry_price,
            equity=current_equity
        )

        # Risk Manager Adjustment
        target_units = risk_manager.adjust_target_position(
            target_units=target_units,
            price=entry_price,
            equity=current_equity,
            timestamp=bar.name
        )

        # Validation
        if target_units == 0:
            # Risk Manager hat Trading gestoppt
            block_trade()
        else:
            # Risk Limits Check
            if check_risk_limits():
                # Trade öffnen
                open_trade()
            else:
                block_trade()

    elif signal == -1 and current_trade is not None:
        # EXIT
        close_trade_at_market()

    # 3. EQUITY UPDATE
    update_equity_curve()
```

---

## Position Sizing Integration

### Workflow

```python
# 1. Strategy generiert Signal
signal = 1  # Long

# 2. Position Sizer berechnet Target Units
target_units = position_sizer.get_target_position(
    signal=signal,
    price=50000.0,
    equity=10000.0
)
# Returns: 0.02 BTC (wenn fraction=0.1 → 1000€ / 50000€)

# 3. Risk Manager kann reduzieren/blockieren
adjusted_units = risk_manager.adjust_target_position(
    target_units=target_units,
    price=50000.0,
    equity=8000.0,  # Drawdown!
    timestamp=None
)
# Returns: 0.0 (wenn max_drawdown erreicht)

# 4. Validation
if adjusted_units == 0:
    # Trade wird blockiert
    blocked_trades += 1
else:
    # Trade wird eröffnet
    current_trade = Trade(
        entry_price=50000.0,
        size=adjusted_units,
        stop_price=49000.0
    )
```

---

## Risk Management Integration

### Max Drawdown Check

```python
class MaxDrawdownRiskManager:
    def adjust_target_position(self, target_units, price, equity, timestamp):
        # Peak-Equity aktualisieren
        if equity > self.peak_equity:
            self.peak_equity = equity

        # Drawdown berechnen
        current_dd = (self.peak_equity - equity) / self.peak_equity

        # Check
        if current_dd >= self.max_drawdown:
            # Trading stoppen!
            self.trading_stopped = True
            return 0.0

        return target_units
```

**Beispiel:**
- Start-Equity: 10.000 €
- Peak erreicht: 12.000 €
- Max-Drawdown: 25%
- Kritische Equity: 9.000 € (12.000 × 0.75)
- Bei Equity <= 9.000 € → alle target_units = 0

### Equity Floor Check

```python
class EquityFloorRiskManager:
    def adjust_target_position(self, target_units, price, equity, timestamp):
        if equity <= self.equity_floor:
            # Equity-Minimum erreicht → Trading stoppen
            self.trading_stopped = True
            return 0.0

        return target_units
```

---

## Stop-Loss-Management

### Stop-Price-Berechnung

```python
entry_price = 50000.0
stop_pct = 0.02  # 2%

stop_price = entry_price * (1 - stop_pct)
# = 50000 * 0.98 = 49000.0
```

### Stop-Check (jede Bar)

```python
if current_trade is not None:
    if bar["low"] <= current_trade.stop_price:
        # Stop wurde getroffen!
        current_trade.exit_time = bar.name
        current_trade.exit_price = current_trade.stop_price
        current_trade.pnl = current_trade.size * (stop_price - entry_price)
        current_trade.exit_reason = "stop_loss"

        # Equity aktualisieren
        equity += current_trade.pnl

        # Trade schließen
        current_trade = None
```

**Wichtig:**
- Stop-Check hat **höchste Priorität** (vor Signal-Handling)
- Exit-Price = Stop-Price (nicht bar["low"])
- Slippage wird NICHT simuliert

---

## Trade-Tracking

### Trade Dataclass

```python
@dataclass
class Trade:
    entry_time: datetime
    entry_price: float
    size: float                 # Units (z.B. BTC)
    stop_price: float
    exit_time: Optional[datetime] = None
    exit_price: Optional[float] = None
    pnl: Optional[float] = None
    pnl_pct: Optional[float] = None
    exit_reason: str = ""       # "stop_loss", "signal", "end_of_data"
```

### Exit-Reasons

- `"stop_loss"` – Stop wurde getroffen
- `"signal"` – Strategy-Exit-Signal (-1)
- `"end_of_data"` – Backtest-Ende (Position noch offen)

---

## Performance-Metriken

### BacktestResult

```python
@dataclass
class BacktestResult:
    equity_curve: pd.Series     # Equity über Zeit
    trades: List[Trade]         # Alle Trades
    stats: Dict[str, float]     # Performance-Metriken
    mode: str                   # "realistic_with_risk_management"
    strategy_name: str
    blocked_trades: int         # Anzahl blockierter Trades
```

### Berechnete Stats

```python
result.stats = {
    "total_return": 0.0578,      # 5.78%
    "max_drawdown": -0.0234,     # -2.34%
    "sharpe": 1.82,
    "total_trades": 12,
    "win_rate": 0.58,            # 58%
    "profit_factor": 1.45
}
```

**Metriken:**
- `total_return` – Gesamtrendite
- `max_drawdown` – Maximaler Drawdown
- `sharpe` – Sharpe Ratio (annualisiert)
- `total_trades` – Anzahl Trades
- `win_rate` – Win Rate (%)
- `profit_factor` – Profit Factor (Gross Profit / Gross Loss)

---

## Heuristische Post-Backtest-Prüfung (Screening, kein operatives Go)

**Authority-Hinweis:** `validate_for_live_trading` wertet **nur** aggregierte **Backtest-`stats`** anhand fester **Schwellwerte** aus — ein Research- bzw. Screening-Hilfsmittel. Das ist **weder** eine Live-Freigabe **noch** Testnet-, Paper- oder Shadow-Autorisierung, **weder** First-Live-**noch** Master-V2- oder Double-Play-Signoff, **weder** Evidence-**noch** operatives Trading. Es entsteht **keine** Order-, Exchange-, Arming- oder Enablement-Autorität. Operative Nutzung verlangt getrennte, Master-V2-kompatible Governance- und Readiness-Pfade, u. a. [STRATEGY_TO_MASTER_V2_INTEGRATION_CONTRACT_V0.md](ops/specs/STRATEGY_TO_MASTER_V2_INTEGRATION_CONTRACT_V0.md), [STRATEGY_REGISTRY_TIERING_DUAL_SOURCE_CONTRACT_V1.md](ops/specs/STRATEGY_REGISTRY_TIERING_DUAL_SOURCE_CONTRACT_V1.md) und (First-Live-Readiness-Rahmen) [MASTER_V2_FIRST_LIVE_PRE_LIVE_READINESS_VERDICT_PACKET_CONTRACT_V1.md](ops/specs/MASTER_V2_FIRST_LIVE_PRE_LIVE_READINESS_VERDICT_PACKET_CONTRACT_V1.md).

```python
from src.backtest.stats import validate_for_live_trading

passed, warnings = validate_for_live_trading(result.stats)

if passed:
    print("Hinweis: Heuristische Mindestkriterien am Backtest erfüllt (kein operatives Go)")
else:
    print("Hinweis: Heuristik am Backtest nicht erfüllt; Details:")
    for warning in warnings:
        print(f"  - {warning}")
```

**Heuristische Mindestfilter (Beispiel-Implementierung, Research-Screening):**
- Sharpe Ratio >= 1.5
- Min. 50 Trades
- Profit Factor >= 1.3
- Max Drawdown < 30%

Diese Werte sind **keine** verbindlichen Produktions- oder Live-Policy-Limits; sie dienen ausschließlich der schnellen Doku-Illustration der Hilfsfunktion.

---

## Best Practices

### Do's

✅ **Immer Stop-Loss** setzen
```python
strategy_params = {"stop_pct": 0.02}  # 2%
```

✅ **Position Sizing** aktivieren
```python
from src.core.position_sizing import build_position_sizer_from_config
position_sizer = build_position_sizer_from_config(cfg)
```

✅ **Risk Manager** nutzen
```python
from src.core.risk import build_risk_manager_from_config
risk_manager = build_risk_manager_from_config(cfg)
```

✅ **Genug Bars** (min. 200+)
```python
df = create_dummy_data(n_bars=500)
```

### Don'ts

❌ **Kein Vectorized Mode** für Live-Decisions
```python
# NUR für schnelle Tests!
result = engine.run_vectorized(...)
```

❌ **Keine zu engen Stops**
```python
# Noise-Trading!
strategy_params = {"stop_pct": 0.001}  # 0.1% ❌
```

❌ **Nicht ohne Risk Management**
```python
# Sehr riskant!
engine = BacktestEngine()  # Kein risk_manager!
```

---

## Beispiel: Kompletter Backtest

```python
from src.core.peak_config import load_config
from src.core.position_sizing import build_position_sizer_from_config
from src.core.risk import build_risk_manager_from_config
from src.strategies.registry import create_strategy_from_config
from src.backtest.engine import BacktestEngine

# 1. Config laden
cfg = load_config()

# 2. Strategie erstellen
strategy = create_strategy_from_config("ma_crossover", cfg)

# 3. Position Sizer & Risk Manager
position_sizer = build_position_sizer_from_config(cfg)
risk_manager = build_risk_manager_from_config(cfg, section="risk_management")

# 4. Daten laden
df = create_dummy_data(n_bars=300)

# 5. Engine initialisieren
engine = BacktestEngine(
    core_position_sizer=position_sizer,
    risk_manager=risk_manager
)

# 6. Backtest durchführen
def strategy_signal_fn(df, params):
    return strategy.generate_signals(df)

result = engine.run_realistic(
    df=df,
    strategy_signal_fn=strategy_signal_fn,
    strategy_params={"stop_pct": 0.02}
)

# 7. Results analysieren
print(f"Total Return: {result.stats['total_return']:.2%}")
print(f"Sharpe Ratio: {result.stats['sharpe']:.2f}")
print(f"Total Trades: {result.stats['total_trades']}")
print(f"Blocked Trades: {result.blocked_trades}")
```

---

## Portfolio-Backtests

Portfolio-Backtests ermöglichen das gleichzeitige Testen mehrerer Symbole/Strategien mit aggregierter Auswertung.

### Konzept

Ein **Portfolio-Backtest** ist eine Kollektion von Einzel-Backtests:
- Mehrere Symbole (z.B. BTC/EUR, ETH/EUR, LTC/EUR)
- Verschiedene Strategien pro Symbol möglich
- Capital Allocation: equal, risk_parity, sharpe_weighted, manual
- Aggregierte Portfolio-Equity und Stats

### Unterschied: Einzel- vs. Portfolio-Backtest

| Aspekt | Einzel-Backtest | Portfolio-Backtest |
|--------|-----------------|-------------------|
| Symbole | 1 | N (mehrere) |
| Run-Type | `backtest` | `portfolio_backtest` |
| Equity | Eine Curve | Aggregierte Curve |
| Logger | `log_backtest_result()` | `log_portfolio_backtest_result()` |

### Quick Start

```bash
# Portfolio-Backtest starten
python3 scripts/run_portfolio_backtest.py

# Mit Tag für Registry
python3 scripts/run_portfolio_backtest.py --tag weekend-research

# Mit spezifischer Allocation
python3 scripts/run_portfolio_backtest.py --allocation risk_parity
```

### CLI-Argumente

| Argument | Beschreibung | Default |
|----------|--------------|---------|
| `--bars` | Anzahl Bars pro Asset | aus config.toml |
| `--allocation` | Capital Allocation | `equal` |
| `--run-name` | Name für Reports | `portfolio` |
| `--tag` | Tag für Registry | - |
| `--dry-run` | Kein Registry-Logging | False |
| `--save-individual` | Speichere Asset-Reports | False |

### Registry-Logging

```python
from src.core.experiments import log_portfolio_backtest_result

run_id = log_portfolio_backtest_result(
    portfolio_name="core_3-strat",
    equity_curve=portfolio_equity,
    component_runs=[
        {"symbol": "BTC/EUR", "strategy_key": "ma_crossover", "weight": 0.33},
        {"symbol": "ETH/EUR", "strategy_key": "rsi_reversion", "weight": 0.33},
    ],
    portfolio_stats={"total_return": 0.12, "sharpe": 1.25},
    tag="weekend-research",
    allocation_method="equal",
)
```

### Ergebnisse ansehen

```bash
# Portfolio-Runs in Registry
python3 scripts/list_experiments.py --run-type portfolio_backtest

# Details eines Runs
python3 scripts/show_experiment.py <run_id>
```

---

## Troubleshooting

### "No trades generated"

**Ursachen:**
- Risk Manager hat Trading gestoppt
- Position Sizing zu klein
- Keine Entry-Signale

**Lösung:**
```python
# 1. Check blocked_trades
print(f"Blocked: {result.blocked_trades}")

# 2. Check Signale
signals = strategy.generate_signals(df)
print(f"Longs: {(signals == 1).sum()}")

# 3. Risk Manager deaktivieren (Test)
from src.core.risk import NoopRiskManager
risk_manager = NoopRiskManager()
```

### "All trades hit stop-loss"

**Ursachen:**
- Stop zu eng
- Strategie-Parameter falsch
- Volatile Daten

**Lösung:**
```python
# 1. Stop lockern
strategy_params = {"stop_pct": 0.03}  # 3% statt 2%

# 2. Strategy-Parameter prüfen
print(strategy.fast_window, strategy.slow_window)
```

---

## Determinismus & No-Lookahead-Garantie

### Prinzipien

Die BacktestEngine garantiert **realistische Simulation** ohne Look-Ahead-Bias:

#### ✅ Was ist garantiert

1. **Bar-für-Bar Execution**
   - Jede Bar wird sequenziell verarbeitet
   - State wird zwischen Bars persistent gehalten
   - Keine Zukunftsinformationen verfügbar

2. **No Lookahead**
   - Signale basieren nur auf Daten bis (inkl.) aktueller Bar
   - Stop-Loss wird erst nach Bar-Close geprüft
   - Position-Sizing nutzt nur bekannte Equity

3. **Realistische Order-Fills**
   - Entry: Next Bar's Open (nach Signal)
   - Stop-Loss: Intrabar-Check mit Bar-Low/High
   - Exit: Next Bar's Open (bei Flat-Signal)

#### ⚠️ Was NICHT garantiert ist

- **Intrabar-Events:** Keine Simulation von Tick-Daten
- **Slippage:** Momentan nicht modelliert (kommt in v2). Für realistische Bewertung: Paper-Trading oder ExecutionPipeline mit Fee/Slippage nutzen; siehe `docs/ops/specs/FEE_SLIPPAGE_CONSERVATIVE_ASSUMPTIONS.md`.
- **Order-Latency:** Instant-Fills angenommen

### Position-Sizing Integration

Die Engine integriert zwei unabhängige Sizing-Systeme:

#### 1. Core Position Sizers (Empfohlen)

```python
from src.core.position_sizing import FixedFractionSizer

sizer = FixedFractionSizer(fraction=0.1)
engine = BacktestEngine(core_position_sizer=sizer)
```

**Verfügbare Sizers:**
- `FixedFractionSizer` – Prozentsatz des Kapitals (z.B. 10%)
- `FixedSizeSizer` – Feste Anzahl Contracts/Units
- `NoopPositionSizer` – Keine Sizing-Logik (für Testing)

#### 2. Vol-Regime Overlay Sizers (Erweitert)

```python
from src.core.position_sizing_overlay import VolRegimeOverlaySizer

overlay = VolRegimeOverlaySizer(
    base_sizer=FixedFractionSizer(fraction=0.1),
    regime_scaling={
        "low": 1.5,    # 150% in niedrig-volatilen Märkten
        "medium": 1.0, # 100% normal
        "high": 0.5    # 50% in hoch-volatilen Märkten
    }
)
engine = BacktestEngine(core_position_sizer=overlay)
```

**Overlay-Typen:**
- `VolRegimeOverlaySizer` – Volatilitäts-adaptiv
- `TrendStrengthOverlaySizer` – Trend-adaptiv
- `CompositeOverlaySizer` – Kombiniert mehrere Overlays

#### 3. Pipeline: Strategy → Sizing → Risk

```text
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│  Strategy   │ ───▶ │   Sizing    │ ───▶ │    Risk     │
│  Signal: 1  │      │  Size: 0.1  │      │  Allowed?   │
└─────────────┘      └─────────────┘      └─────────────┘
       │                    │                     │
       │                    │                     │
       └────────────────────┴─────────────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │   Execute   │
                    │  Position   │
                    └─────────────┘
```

**Wichtig:** Sizing und Risk sind **orthogonal**:
- Sizing bestimmt **wie viel** gehandelt wird
- Risk entscheidet **ob** überhaupt gehandelt wird

### Config-Beispiel mit Sizing

```toml
[backtest]
initial_capital = 10000.0

[sizing]
type = "fixed_fraction"
fraction = 0.1

[sizing.overlay]
type = "vol_regime"
window = 20
thresholds = [0.015, 0.03]  # Low/Medium/High Grenzen
scaling_factors = {low = 1.5, medium = 1.0, high = 0.5}

[risk]
type = "max_drawdown"
max_drawdown = 0.20
```

### Runner-Beispiel mit Sizing

```python
from src.core.peak_config import load_config
from src.core.position_sizing import build_position_sizer_from_config
from src.core.risk import build_risk_manager_from_config
from src.backtest.engine import BacktestEngine

# Config laden
cfg = load_config("config/my_backtest.toml")

# Position Sizer aus Config erstellen
position_sizer = build_position_sizer_from_config(cfg)

# Risk Manager aus Config erstellen
risk_manager = build_risk_manager_from_config(cfg)

# Engine mit Sizing + Risk
engine = BacktestEngine(
    core_position_sizer=position_sizer,
    risk_manager=risk_manager
)

# Backtest ausführen
result = engine.run_realistic(df, strategy.generate_signals, {})

# Position-Sizes im Result
print(result.position_sizes)  # Liste der tatsächlichen Sizes
```

---

## Extension Hooks – Wie erweitere ich die Engine?

Die BacktestEngine ist so gebaut, dass du Komponenten austauschen und erweitern kannst, ohne die Engine selbst ändern zu müssen.

### 1. Custom Position Sizer hinzufügen

**Schritt 1: Sizer implementieren**

```python
# src/core/position_sizing.py
from typing import Optional

class MyCustomSizer(BasePositionSizer):
    """
    Beispiel: Kelly-Criterion-basiertes Position Sizing
    """

    def __init__(self, win_rate: float = 0.55, avg_win_loss_ratio: float = 1.5):
        self.win_rate = win_rate
        self.ratio = avg_win_loss_ratio

    def get_target_position(
        self,
        signal: int,
        price: float,
        equity: float,
        context: Optional[dict] = None
    ) -> float:
        """Kelly-Criterion Sizing."""
        if signal == 0:
            return 0.0

        # Kelly = (win_rate * ratio - (1 - win_rate)) / ratio
        kelly_fraction = (
            self.win_rate * self.ratio - (1 - self.win_rate)
        ) / self.ratio

        # Konservativ: Halber Kelly
        fraction = kelly_fraction * 0.5

        # Units berechnen
        position_value = equity * fraction
        target_units = position_value / price

        return target_units
```

**Schritt 2: In Config-Builder registrieren**

```python
# src/core/position_sizing.py (in build_position_sizer_from_config)

def build_position_sizer_from_config(cfg, section="sizing"):
    sizer_type = cfg.get(f"{section}.type", "fixed_fraction")

    if sizer_type == "my_custom":
        win_rate = cfg.get(f"{section}.win_rate", 0.55)
        ratio = cfg.get(f"{section}.avg_win_loss_ratio", 1.5)
        return MyCustomSizer(win_rate=win_rate, ratio=ratio)

    # ... rest of code
```

**Schritt 3: In Config nutzen**

```toml
[sizing]
type = "my_custom"
win_rate = 0.58
avg_win_loss_ratio = 1.6
```

### 2. Custom Risk Manager hinzufügen

**Schritt 1: Risk Manager implementieren**

```python
# src/core/risk.py

class VolatilityRiskManager(BaseRiskManager):
    """
    Beispiel: Reduziert Position-Size bei hoher Volatilität
    """

    def __init__(self, window: int = 20, vol_threshold: float = 0.03):
        self.window = window
        self.vol_threshold = vol_threshold
        self.price_history = []

    def adjust_target_position(
        self,
        target_units: float,
        price: float,
        equity: float,
        timestamp
    ) -> float:
        # Preis-Historie aktualisieren
        self.price_history.append(price)
        if len(self.price_history) > self.window:
            self.price_history.pop(0)

        # Volatilität berechnen
        if len(self.price_history) < 2:
            return target_units

        import numpy as np
        returns = np.diff(self.price_history) / self.price_history[:-1]
        volatility = np.std(returns)

        # Position reduzieren bei hoher Volatilität
        if volatility > self.vol_threshold:
            scaling = 0.5  # Halbe Position
            return target_units * scaling

        return target_units
```

**Schritt 2: In Config-Builder registrieren**

```python
# src/core/risk.py (in build_risk_manager_from_config)

def build_risk_manager_from_config(cfg, section="risk"):
    risk_type = cfg.get(f"{section}.type", "noop")

    if risk_type == "volatility":
        window = cfg.get(f"{section}.window", 20)
        threshold = cfg.get(f"{section}.vol_threshold", 0.03)
        return VolatilityRiskManager(window=window, vol_threshold=threshold)

    # ... rest of code
```

**Schritt 3: In Config nutzen**

```toml
[risk]
type = "volatility"
window = 30
vol_threshold = 0.025
```

### 3. Custom Backtest-Mode hinzufügen

Wenn du einen komplett neuen Execution-Mode brauchst (z.B. Intrabar-Simulation):

**Option A: Neue Methode in Engine**

```python
# src/backtest/engine.py

class BacktestEngine:
    # ... existing methods ...

    def run_intrabar(
        self,
        df: pd.DataFrame,
        tick_data: pd.DataFrame,  # Zusätzliche Tick-Daten
        strategy_signal_fn,
        strategy_params: dict
    ):
        """
        Neuer Mode mit Intrabar-Tick-Simulation.
        """
        # Deine Custom-Logik hier
        pass
```

**Option B: Engine-Wrapper**

```python
# scripts/run_intrabar_backtest.py

from src.backtest.engine import BacktestEngine

class IntrabarBacktestEngine:
    """
    Wrapper um BacktestEngine für Intrabar-Simulation.
    """

    def __init__(self, base_engine: BacktestEngine):
        self.engine = base_engine

    def run_with_ticks(self, df, tick_data, strategy_signal_fn, params):
        # Deine Custom-Logik hier
        # Nutzt self.engine.run_realistic() intern
        pass
```

### 4. Custom Stats/Metriken hinzufügen

```python
# src/backtest/stats.py

def compute_additional_metrics(result: BacktestResult) -> dict:
    """
    Berechnet zusätzliche Custom-Metriken.
    """
    trades = result.trades

    # Beispiel: Longest Drawdown Duration
    equity = result.equity_curve
    rolling_max = equity.expanding().max()
    drawdown = (equity - rolling_max) / rolling_max

    in_drawdown = drawdown < 0
    drawdown_periods = in_drawdown.astype(int).groupby(
        (in_drawdown != in_drawdown.shift()).cumsum()
    ).sum()

    longest_dd_duration = drawdown_periods.max() if len(drawdown_periods) > 0 else 0

    # Beispiel: Average Trade Duration
    if trades:
        durations = [
            (t.exit_time - t.entry_time).total_seconds() / 3600  # Hours
            for t in trades if t.exit_time
        ]
        avg_duration_hours = np.mean(durations) if durations else 0
    else:
        avg_duration_hours = 0

    return {
        "longest_drawdown_duration_bars": int(longest_dd_duration),
        "avg_trade_duration_hours": avg_duration_hours,
    }

# Usage in runner:
result = engine.run_realistic(...)
custom_stats = compute_additional_metrics(result)
result.stats.update(custom_stats)
```

### 5. Custom Trade-Exit-Logic

Wenn du komplexere Exit-Logik brauchst (z.B. Trailing-Stop):

```python
# In deinem Runner-Script

def run_with_trailing_stop(engine, df, strategy, params):
    """
    Wrapper für Trailing-Stop-Logik.
    """

    # Pre-Compute Trailing-Stops
    signals = strategy.generate_signals(df)
    df_with_stops = df.copy()

    # Trailing-Stop berechnen (z.B. 10% vom Peak)
    for i in range(len(df)):
        if signals.iloc[i] == 1:
            # Entry → Track Peak
            peak = df["close"].iloc[i]
            trailing_stop = peak * 0.9
            df_with_stops.loc[df.index[i], "trailing_stop"] = trailing_stop

    # Backtest mit modifizierten Stops
    result = engine.run_realistic(
        df=df_with_stops,
        strategy_signal_fn=lambda d, p: signals,
        strategy_params=params
    )

    return result
```

### 6. Integration mit externen Tools

**MLflow-Integration:**

```python
# scripts/run_with_mlflow.py
import mlflow

cfg = load_config()
strategy = create_strategy_from_config("ma_crossover", cfg)
engine = BacktestEngine.from_config(cfg)

with mlflow.start_run():
    # Log Config
    mlflow.log_params(cfg.to_dict())

    # Run Backtest
    result = engine.run_realistic(df, strategy.generate_signals, {})

    # Log Metrics
    mlflow.log_metrics(result.stats)

    # Log Artifacts
    mlflow.log_artifact("reports/backtest_report.html")
```

**Optuna-Integration (Hyperparameter-Tuning):**

```python
# scripts/run_optuna_sweep.py
import optuna

def objective(trial):
    # Suggest Parameters
    fast = trial.suggest_int("fast", 10, 50)
    slow = trial.suggest_int("slow", 50, 200)

    # Run Backtest
    strategy = MACrossoverStrategy(fast_window=fast, slow_window=slow)
    result = engine.run_realistic(df, strategy.generate_signals, {})

    # Optimize Sharpe
    return result.stats["sharpe"]

study = optuna.create_study(direction="maximize")
study.optimize(objective, n_trials=100)

print(f"Best Params: {study.best_params}")
```

---

## Further Reading

### Core Documentation
- 🚪 **[Documentation Frontdoor](README.md)** – Navigate all docs by audience & topic
- 📖 **[Peak Trade Overview](PEAK_TRADE_OVERVIEW.md)** – Architecture map, modules, data flow, extensibility
- 🎯 **[Strategy Developer Guide](STRATEGY_DEV_GUIDE.md)** – Develop custom strategies

### Operations & Governance
- 🛰️ **[Live Operational Runbooks](LIVE_OPERATIONAL_RUNBOOKS.md)** – Live ops procedures
- 🛰️ **[Ops Hub](ops/README.md)** – Operator center
- 🛡️ **[Governance & Safety Overview](GOVERNANCE_AND_SAFETY_OVERVIEW.md)** – Safety-first approach

### Technical References
- Position Sizing & Overlays: `src/core/position_sizing.py` – Source code
- [Vol Regime Overlay Sizer Tests](../tests/test_vol_regime_overlay_sizer.py) – Test examples
- [Config Reference](../config.toml) – Configuration schema

### Recent Updates
- 🆕 **[Documentation Update Summary](DOCUMENTATION_UPDATE_SUMMARY.md)** – Extension hooks added (2026-01-13)

---

**Letzte Aktualisierung:** Januar 2026
