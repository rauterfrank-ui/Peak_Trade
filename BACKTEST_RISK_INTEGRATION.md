# BacktestEngine - Risk-Layer Integration

**Datum:** 2024-12-02
**Status:** ✅ Vollständig implementiert und getestet

---

## Übersicht

Die `BacktestEngine` wurde vollständig mit dem Risk-Layer integriert. Vor jedem Trade findet ein umfassender Risk-Check statt.

---

## Was wurde geändert?

### Datei: `src/backtest/engine.py`

**Vollständig neu geschrieben** mit:

1. **Risk-Layer-Integration im `__init__`:**
   ```python
   def __init__(
       self,
       position_sizer: Optional[PositionSizer] = None,
       risk_limits: Optional[RiskLimits] = None,
   ):
   ```

2. **Tracking-Strukturen:**
   - `self.equity_curve` - Vollständige Equity-Historie
   - `self.daily_returns_pct` - Tägliche Returns für Daily-Loss-Check

3. **Risk-Check vor jedem Trade:**
   - Position Sizing via `calc_position_size()`
   - Risk Limits via `risk_limits.check_all()`
   - Drawdown-Check
   - Daily Loss-Check
   - Position Size-Check

4. **Trade-Tracking:**
   - PnL in USD und Prozent
   - Exit-Reasons (stop_loss, signal, end_of_data)
   - Blockierte Trades werden gezählt

---

## API

### Verwendung

```python
from src.backtest.engine import BacktestEngine
from src.risk import PositionSizer, PositionSizerConfig, RiskLimits, RiskLimitsConfig
from src.strategies.ma_crossover import generate_signals

# Default-Config
engine = BacktestEngine()

# Custom Risk-Config
position_sizer = PositionSizer(
    PositionSizerConfig(risk_pct=1.0, max_position_pct=25.0)
)

risk_limits = RiskLimits(
    RiskLimitsConfig(
        max_drawdown_pct=20.0,
        max_position_pct=10.0,
        daily_loss_limit_pct=5.0,
    )
)

engine = BacktestEngine(position_sizer=position_sizer, risk_limits=risk_limits)

# Backtest durchführen
result = engine.run_realistic(
    df=df,
    strategy_signal_fn=generate_signals,
    strategy_params={"fast_period": 10, "slow_period": 30, "stop_pct": 0.02},
)

# Ergebnisse
print(f"Total Trades: {result.stats['total_trades']}")
print(f"Blocked Trades: {result.blocked_trades}")
print(f"Total Return: {result.stats['total_return']:.2%}")
```

---

## Workflow

### 1. Initialisierung

```python
equity = initial_cash
equity_curve = [equity]
daily_returns_pct = {}
trades = []
blocked_trades = 0
```

### 2. Bar-für-Bar-Loop

Für jeden Bar:

#### A. Stop-Loss-Check (Höchste Priorität)
```python
if current_trade and bar['low'] <= current_trade.stop_price:
    # Stop getroffen -> Position schließen
    equity += trade.pnl
    trades.append(trade)
    _register_trade_pnl(trade_dt, pnl_pct)
```

#### B. Signal-Handling

Bei Buy-Signal (1):

1. **Position Sizing**
   ```python
   req = PositionRequest(equity, entry_price, stop_price, risk_per_trade)
   pos_result = calc_position_size(req, max_position_pct, min_position_value, min_stop_distance)
   ```

2. **Position-Size-Check**
   ```python
   if pos_result.rejected:
       blocked_trades += 1
       continue
   ```

3. **Risk-Limits-Check**
   ```python
   risk_ok = risk_limits.check_all(
       equity_curve=equity_curve,
       returns_today_pct=get_today_returns(current_dt),
       new_position_nominal=pos_result.value,
       capital=equity,
   )
   ```

4. **Trade-Eröffnung**
   ```python
   if risk_ok:
       current_trade = Trade(...)
   else:
       blocked_trades += 1
   ```

Bei Sell-Signal (-1):

1. **Position schließen**
   ```python
   trade.pnl = size * (exit_price - entry_price)
   equity += trade.pnl
   trades.append(trade)
   _register_trade_pnl(trade_dt, pnl_pct)
   ```

#### C. Equity-Update
```python
equity_curve.append(equity)
```

### 3. Stats berechnen

```python
equity_series = pd.Series(equity_curve, index=...)
basic_stats = compute_basic_stats(equity_series)
sharpe = compute_sharpe_ratio(equity_series)
trade_stats = compute_trade_stats(trades)
```

---

## Neue Features

### 1. BacktestResult erweitert

```python
@dataclass
class BacktestResult:
    equity_curve: pd.Series
    trades: List[Trade]
    stats: Dict[str, float]
    mode: str
    strategy_name: str = ""
    blocked_trades: int = 0  # NEU!
```

### 2. Trade erweitert

```python
@dataclass
class Trade:
    entry_time: datetime
    entry_price: float
    size: float
    stop_price: float
    exit_time: Optional[datetime] = None
    exit_price: Optional[float] = None
    pnl: Optional[float] = None
    pnl_pct: Optional[float] = None  # NEU!
    exit_reason: str = ""
```

### 3. Risk-Tracking

**Daily Returns:**
```python
self.daily_returns_pct: Dict[pd.Timestamp, List[float]] = {}

def _register_trade_pnl(self, trade_dt, pnl_pct):
    day = trade_dt.normalize()
    self.daily_returns_pct.setdefault(day, []).append(pnl_pct)
```

**Equity-Curve:**
```python
self.equity_curve: List[float] = [initial_cash]

# Nach jedem Bar
self.equity_curve.append(current_equity)
```

---

## Demo-Script

**Datei:** `scripts/demo_backtest_with_risk.py`

**Ausführen:**
```bash
python scripts/demo_backtest_with_risk.py
```

**Zeigt:**
1. Backtest mit Default Risk-Config
2. Backtest mit strengen Risk-Limits
3. Backtest mit aggressiven Risk-Limits
4. Trade-Details

---

## Beispiele

### Beispiel 1: Default-Config

```python
engine = BacktestEngine()

result = engine.run_realistic(df, generate_signals, {
    "fast_period": 10,
    "slow_period": 30,
    "stop_pct": 0.02,
})

print(f"Trades: {result.stats['total_trades']}")
print(f"Blocked: {result.blocked_trades}")
```

### Beispiel 2: Conservative Config

```python
from src.risk import RiskLimits, RiskLimitsConfig

risk_limits = RiskLimits(
    RiskLimitsConfig(
        max_drawdown_pct=10.0,  # Streng
        max_position_pct=5.0,   # Streng
        daily_loss_limit_pct=2.0,  # Streng
    )
)

engine = BacktestEngine(risk_limits=risk_limits)

result = engine.run_realistic(df, generate_signals, strategy_params)

# Viele Trades werden blockiert
print(f"Blocked: {result.blocked_trades}")
```

### Beispiel 3: Aggressive Config

```python
position_sizer = PositionSizer(
    PositionSizerConfig(
        risk_pct=2.0,  # 2% Risk
        max_position_pct=50.0,  # 50% Position erlaubt
    )
)

risk_limits = RiskLimits(
    RiskLimitsConfig(
        max_drawdown_pct=30.0,
        daily_loss_limit_pct=10.0,
    )
)

engine = BacktestEngine(position_sizer=position_sizer, risk_limits=risk_limits)

result = engine.run_realistic(df, generate_signals, strategy_params)

# Weniger Trades werden blockiert
print(f"Blocked: {result.blocked_trades}")
```

---

## Risk-Checks im Detail

### 1. Position-Size-Check

**In `calc_position_size()`:**

```python
# 1. Stop unter Entry?
if stop_price >= entry_price:
    return rejected

# 2. Stop-Distanz ausreichend?
if stop_distance_pct < min_stop_distance:
    return rejected

# 3. Position zu groß?
if position_value > equity * max_position_pct:
    return rejected

# 4. Position zu klein?
if position_value < min_position_value:
    return rejected
```

### 2. Risk-Limits-Check

**In `risk_limits.check_all()`:**

```python
# 1. Drawdown-Check
if not check_drawdown(equity_curve, max_drawdown_pct):
    return False

# 2. Daily Loss-Check
if not check_daily_loss(returns_today_pct, daily_loss_limit_pct):
    return False

# 3. Position Size-Check
if not check_position_size(position_nominal, capital, max_position_pct):
    return False

return True
```

---

## Logging

Die Engine loggt wichtige Events:

```python
import logging

logger = logging.getLogger(__name__)

# Bei blockiertem Trade
logger.debug(f"Trade blockiert bei {current_dt}: Equity={equity:.2f}")

# Bei Abschluss
logger.info(f"Backtest abgeschlossen: {len(trades)} Trades, {blocked_trades} blockiert")
```

**Logging aktivieren:**
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## Troubleshooting

### Problem: Alle Trades werden blockiert

**Symptom:**
```
Total Trades: 0
Blocked Trades: 115
```

**Mögliche Ursachen:**

1. **Position zu klein:**
   ```python
   # config.toml
   [risk]
   min_position_value = 50.0  # Zu hoch?
   ```

2. **Max Position zu klein:**
   ```python
   [risk]
   max_position_size = 0.25  # 25% OK
   max_position_pct = 10.0    # 10% zu niedrig?
   ```

3. **Stop-Distanz zu eng:**
   ```python
   [risk]
   min_stop_distance = 0.005  # 0.5% min

   # In Strategie
   stop_pct = 0.02  # 2% sollte OK sein
   ```

**Lösung:**
```python
# Anpassen in config.toml oder Custom-Config

position_sizer = PositionSizer(
    PositionSizerConfig(
        risk_pct=1.0,
        max_position_pct=25.0,  # Erhöhen
    )
)

risk_limits = RiskLimits(
    RiskLimitsConfig(
        max_position_pct=25.0,  # Erhöhen
    )
)
```

---

## Integration-Status

✅ **Vollständig implementiert:**
- Position Sizing vor jedem Trade
- Risk Limits (Drawdown, Daily Loss, Position Size)
- Stop-Loss-Management
- Trade-Tracking mit PnL
- Blocked-Trades-Counter

✅ **Rückwärtskompatibel:**
- Alte API-Aufrufe funktionieren weiter
- Default-Configs werden verwendet wenn keine übergeben

✅ **Getestet:**
- Demo-Script läuft durch
- Alle Risk-Checks funktionieren
- Trades werden korrekt blockiert

---

## Nächste Schritte

1. **Mit echten Daten testen:**
   ```bash
   python scripts/demo_backtest_with_risk.py
   ```

2. **Config optimieren:**
   - `config.toml` anpassen
   - Limits testen mit verschiedenen Strategien

3. **Parameter-Optimierung:**
   - Risk-Parameter tunen
   - Backtests mit verschiedenen Configs

4. **Multi-Strategy:**
   - Mehrere Strategien parallel
   - Portfolio-weite Risk-Limits

---

## Zusammenfassung

Die BacktestEngine ist jetzt vollständig mit dem Risk-Layer integriert:

- ✅ Position Sizing aktiv
- ✅ Risk Limits (Drawdown, Daily Loss, Position Size)
- ✅ Stop-Loss-Management
- ✅ Trade-Tracking mit PnL
- ✅ Blocked-Trades werden gezählt
- ✅ Rückwärtskompatibel
- ✅ Demo-Script vorhanden

**Status:** Produktionsreif für Backtesting! 🚀

---

**Stand:** 2024-12-02
**Dateien:**
- `src/backtest/engine.py` - Vollständig neu
- `src/risk/__init__.py` - Exports erweitert
- `scripts/demo_backtest_with_risk.py` - NEU
