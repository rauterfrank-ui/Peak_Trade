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

## Live-Trading-Validierung

```python
from src.backtest.stats import validate_for_live_trading

passed, warnings = validate_for_live_trading(result.stats)

if passed:
    print("✅ Strategie für Live-Trading freigegeben")
else:
    print("❌ Nicht freigegeben:")
    for warning in warnings:
        print(f"  - {warning}")
```

**Kriterien:**
- Sharpe Ratio >= 1.5
- Min. 50 Trades
- Profit Factor >= 1.3
- Max Drawdown < 30%

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
python scripts/run_portfolio_backtest.py

# Mit Tag für Registry
python scripts/run_portfolio_backtest.py --tag weekend-research

# Mit spezifischer Allocation
python scripts/run_portfolio_backtest.py --allocation risk_parity
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
python scripts/list_experiments.py --run-type portfolio_backtest

# Details eines Runs
python scripts/show_experiment.py <run_id>
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
- **Slippage:** Momentan nicht modelliert (kommt in v2)
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

## Weiterführende Dokumentation

- [Architektur-Übersicht](PEAK_TRADE_OVERVIEW.md)
- [Strategy Developer Guide](STRATEGY_DEV_GUIDE.md)
- [Position Sizing & Overlays](../src/core/position_sizing.py)
- [Vol Regime Overlay Sizer Tests](../tests/test_vol_regime_overlay_sizer.py)
- [Config Reference](../config.toml)

---

**Letzte Aktualisierung:** Dezember 2024
