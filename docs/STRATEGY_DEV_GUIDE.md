# Strategie-Entwicklung mit Peak_Trade 🎯

> **Schritt-für-Schritt-Anleitung zum Entwickeln eigener Trading-Strategien**

---

## 1. Grundprinzip

Peak_Trade-Strategien folgen einem klaren Contract:

```python
Input:  OHLCV-DataFrame (mindestens 'close'-Spalte)
Output: pd.Series mit diskreten Signalen/States:
        - 1  = long
        - -1 = short
        - 0  = flat
```

### Signal vs. State

- **Signal:** Diskrete Events (z.B. MA-Crossover)
- **State:** Kontinuierliche Position (z.B. "im long-Trade")

Die meisten Strategien geben **States** zurück, die über die Zeit persistent sind:

```python
# Beispiel MA Crossover
Bar 100: Fast MA kreuzt über Slow MA  → Signal = 1  → State = 1 (long)
Bar 101: Kein neues Event             → Signal = 0  → State = 1 (bleibe long!)
Bar 102: Kein neues Event             → Signal = 0  → State = 1
Bar 103: Fast MA kreuzt unter Slow MA → Signal = -1 → State = 0 (flat)
```

**Wichtig:** Die Engine erwartet **States**, nicht Events!

---

## 2. BaseStrategy-API

Alle Strategien erben von `BaseStrategy` (`src/strategies/base.py`):

### 2.1 BaseStrategy-Contract

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional
import pandas as pd

@dataclass
class StrategyMetadata:
    """Metadaten für Logging, Doku, UI."""
    name: str
    description: str = ""
    version: str = "0.1.0"
    author: str = "Peak_Trade"

class BaseStrategy(ABC):
    """
    Abstrakte Basis-Strategie.

    Contract:
    - Input: DataFrame mit OHLCV (mindestens 'close')
    - Output: pd.Series mit Ziel-Position (1, -1, 0)
    """

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        metadata: Optional[StrategyMetadata] = None,
    ) -> None:
        self.config: Dict[str, Any] = config or {}
        self.meta: StrategyMetadata = metadata or StrategyMetadata(
            name=self.__class__.__name__
        )

    @classmethod
    @abstractmethod
    def from_config(cls, cfg: Any, section: str) -> "BaseStrategy":
        """Factory-Methode: Erstellt Strategie-Instanz aus Config."""
        raise NotImplementedError

    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Muss von jeder Strategie implementiert werden.

        Args:
            data: OHLCV-DataFrame mit DatetimeIndex

        Returns:
            pd.Series mit Index = data.index, Werten in {-1, 0, 1}
        """
        raise NotImplementedError

    def prepare(self, data: pd.DataFrame) -> None:
        """
        Optionaler Pre-Processing-Schritt (Hook).
        Kann von Subklassen überschrieben werden.
        """
        return

    def prepare_once(self, data: pd.DataFrame) -> None:
        """
        Idempotenz-Guard: ruft `prepare(data)` höchstens einmal pro DataFrame aus.

        Hinweis: In Peak_Trade ist das "Once" **pro DataFrame-Objekt** (Objekt-Identität).
        """
        ...

    def run(self, data: pd.DataFrame) -> pd.Series:
        """
        Empfohlener Entry-Point:
        - `prepare_once(data)` (optional, aber standardisiert)
        - danach `generate_signals(data)`
        """
        ...
```

### 2.2 Wichtige Methoden

#### `generate_signals(data: pd.DataFrame) -> pd.Series`

**Muss implementiert werden!**

- Input: OHLCV-DataFrame
- Output: pd.Series mit {-1, 0, 1}
- Index muss mit `data.index` übereinstimmen

#### `prepare(data: pd.DataFrame) -> None`

**Optional überschreiben**

- Für teure Vorberechnungen (z.B. komplexe Indikatoren)
- **Hook-only**: Sollte nicht direkt als externer Entry-Point genutzt werden
- Wird über `prepare_once()` bzw. `run()` kontrolliert (idempotent pro DataFrame)

#### `prepare_once(data: pd.DataFrame) -> None`

**Optional nutzen (empfohlen, wenn du `generate_signals` direkt aufrufst)**

- Idempotenter Guard, der `prepare()` **max. einmal pro DataFrame** ausführt
- In Peak_Trade ist das „gleiches DataFrame“ über **Objekt-Identität** definiert

#### `run(data: pd.DataFrame) -> pd.Series`

**Empfohlen als Entry-Point**

- Ruft `prepare_once(data)` auf und danach `generate_signals(data)`

#### `from_config(cls, cfg, section) -> BaseStrategy`

**Empfohlen als Klassenmethode**

- Factory-Methode zum Erstellen aus Config
- Liest Parameter aus `config.toml`

---

### 2.3 Lifecycle / Empfohlener Aufruf

- **1) `signals = strategy.run(data)`** ✅ empfohlen
- **2) (Legacy/Advanced) `strategy.prepare_once(data)` dann `strategy.generate_signals(data)`** ✅ ok
- **3) `strategy.prepare(data)` direkt** ❌ nicht empfohlen (Hook-only)

```python
# Empfohlen
signals = strategy.run(df)

# Wenn du generate_signals direkt nutzen musst:
strategy.prepare_once(df)
signals = strategy.generate_signals(df)
```

---

## 3. Beispiel: MA Crossover Strategy

Schauen wir uns eine vollständige Implementierung an:

### 3.1 Klassendefinition

```python
# src/strategies/ma_crossover.py
from typing import Any, Dict, Optional
import pandas as pd
import numpy as np

from .base import BaseStrategy, StrategyMetadata

class MACrossoverStrategy(BaseStrategy):
    """
    Moving Average Crossover Strategy.

    Signale:
    - 1 (long): Fast MA > Slow MA (nach Crossover)
    - 0 (flat): Fast MA < Slow MA

    Args:
        fast_window: Periode für schnelle MA (default: 20)
        slow_window: Periode für langsame MA (default: 50)
        price_col: Spalte für Preisdaten (default: "close")
    """

    def __init__(
        self,
        fast_window: int = 20,
        slow_window: int = 50,
        price_col: str = "close",
        config: Optional[Dict[str, Any]] = None,
        metadata: Optional[StrategyMetadata] = None,
    ) -> None:
        # Config zusammenbauen
        initial_config = {
            "fast_window": fast_window,
            "slow_window": slow_window,
            "price_col": price_col,
        }

        # Config-Override falls übergeben
        if config:
            initial_config.update(config)

        # Default Metadata
        if metadata is None:
            metadata = StrategyMetadata(
                name="MA-Crossover",
                description="Moving Average Crossover Strategy",
                version="1.0.0",
                author="Peak_Trade",
            )

        super().__init__(config=initial_config, metadata=metadata)

        # Parameter extrahieren und validieren
        self.fast_window = self.config.get("fast_window", fast_window)
        self.slow_window = self.config.get("slow_window", slow_window)
        self.price_col = self.config.get("price_col", price_col)

        # Validierung
        self._validate_params()

    def _validate_params(self) -> None:
        """Validiert Parameter."""
        if self.fast_window >= self.slow_window:
            raise ValueError(
                f"fast_window ({self.fast_window}) muss < slow_window ({self.slow_window}) sein"
            )
        if self.fast_window < 2 or self.slow_window < 2:
            raise ValueError("MA-Perioden müssen >= 2 sein")
```

### 3.2 generate_signals() Implementierung

```python
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generiert Handelssignale aus OHLCV-Daten.

        Args:
            data: DataFrame mit OHLCV-Daten (mindestens self.price_col)

        Returns:
            Series mit Signalen (1=long, 0=flat, Index=data.index)

        Raises:
            ValueError: Wenn zu wenig Daten oder Spalte fehlt
        """
        # Validierung
        if self.price_col not in data.columns:
            raise ValueError(
                f"Spalte '{self.price_col}' nicht in DataFrame. "
                f"Verfügbar: {list(data.columns)}"
            )

        if len(data) < self.slow_window:
            raise ValueError(
                f"Brauche mind. {self.slow_window} Bars, habe nur {len(data)}"
            )

        # Kopie für Berechnungen
        df = data.copy()

        # MAs berechnen
        df["fast_ma"] = df[self.price_col].rolling(
            self.fast_window, min_periods=self.fast_window
        ).mean()
        df["slow_ma"] = df[self.price_col].rolling(
            self.slow_window, min_periods=self.slow_window
        ).mean()

        # Crossover-Logik
        ma_diff = df["fast_ma"] - df["slow_ma"]
        cross_up = (ma_diff > 0) & (ma_diff.shift(1) <= 0)
        cross_down = (ma_diff < 0) & (ma_diff.shift(1) >= 0)

        # Event-Signale
        events = pd.Series(0, index=df.index, dtype=int)
        events[cross_up] = 1
        events[cross_down] = -1

        # Event → State (1=long, 0=flat)
        state = events.replace({-1: 0})

        # State über die Zeit persistieren
        state = state.replace(0, pd.NA)
        state = state.ffill()
        state = state.fillna(0)
        state = state.infer_objects(copy=False).astype(int)

        return state
```

### 3.3 from_config() Factory-Methode

```python
    @classmethod
    def from_config(
        cls,
        cfg: "PeakConfigLike",
        section: str = "strategy.ma_crossover",
    ) -> MACrossoverStrategy:
        """
        Fabrikmethode für Core-Config.

        Args:
            cfg: Config-Objekt (PeakConfig)
            section: Dotted-Path zum Config-Abschnitt

        Returns:
            MACrossoverStrategy-Instanz

        Example:
            >>> from src.core.peak_config import load_config
            >>> config = load_config()
            >>> strategy = MACrossoverStrategy.from_config(config)
        """
        fast = cfg.get(f"{section}.fast_window", 20)
        slow = cfg.get(f"{section}.slow_window", 50)
        price = cfg.get(f"{section}.price_col", "close")
        return cls(fast_window=fast, slow_window=slow, price_col=price)
```

---

## 4. Neue Strategie Schritt-für-Schritt

### 4.1 Schritt 1: Strategie-Datei anlegen

Erstelle eine neue Datei in `src/strategies/`:

```bash
touch src/strategies/my_new_strategy.py
```

### 4.2 Schritt 2: BaseStrategy importieren & Klasse definieren

```python
# src/strategies/my_new_strategy.py
from typing import Any, Dict, Optional
import pandas as pd
import numpy as np

from .base import BaseStrategy, StrategyMetadata

class MyNewStrategy(BaseStrategy):
    """
    Kurzbeschreibung der Strategie.

    Signale:
    - 1 (long): [Beschreibung Entry-Bedingung]
    - 0 (flat): [Beschreibung Exit-Bedingung]

    Args:
        param1: [Beschreibung Parameter 1]
        param2: [Beschreibung Parameter 2]
    """

    def __init__(
        self,
        param1: int = 10,
        param2: float = 0.5,
        config: Optional[Dict[str, Any]] = None,
        metadata: Optional[StrategyMetadata] = None,
    ) -> None:
        # Config zusammenbauen
        initial_config = {
            "param1": param1,
            "param2": param2,
        }

        if config:
            initial_config.update(config)

        # Metadata
        if metadata is None:
            metadata = StrategyMetadata(
                name="My New Strategy",
                description="[Kurzbeschreibung]",
                version="0.1.0",
                author="[Dein Name]",
            )

        super().__init__(config=initial_config, metadata=metadata)

        # Parameter extrahieren
        self.param1 = self.config.get("param1", param1)
        self.param2 = self.config.get("param2", param2)
```

### 4.3 Schritt 3: generate_signals() implementieren

```python
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generiert Handelssignale.

        Args:
            data: OHLCV-DataFrame

        Returns:
            pd.Series mit Signalen (1=long, 0=flat)
        """
        # Validierung
        if len(data) < self.param1:
            raise ValueError(f"Brauche mind. {self.param1} Bars")

        # Kopie
        df = data.copy()

        # === DEINE STRATEGIE-LOGIK HIER ===

        # Beispiel: Einfache Momentum-Strategie
        df["momentum"] = df["close"].pct_change(self.param1)

        # Entry: Momentum > threshold
        df["entry"] = df["momentum"] > self.param2

        # Exit: Momentum < 0
        df["exit"] = df["momentum"] < 0

        # Events
        events = pd.Series(0, index=df.index, dtype=int)
        events[df["entry"]] = 1
        events[df["exit"]] = -1

        # Event → State
        state = events.replace({-1: 0})
        state = state.replace(0, pd.NA).ffill().fillna(0)
        state = state.infer_objects(copy=False).astype(int)

        return state
```

### 4.4 Schritt 4: from_config() implementieren

```python
    @classmethod
    def from_config(
        cls,
        cfg,
        section: str = "strategy.my_new_strategy",
    ):
        """Factory-Methode für Config."""
        param1 = cfg.get(f"{section}.param1", 10)
        param2 = cfg.get(f"{section}.param2", 0.5)
        return cls(param1=param1, param2=param2)
```

### 4.5 Schritt 5: In Registry registrieren

Öffne `src/strategies/registry.py` und füge hinzu:

```python
# src/strategies/registry.py

# 1. Import hinzufügen
from .my_new_strategy import MyNewStrategy

# 2. Registry-Eintrag hinzufügen
_STRATEGY_REGISTRY: Dict[str, StrategySpec] = {
    # ... bestehende Einträge ...

    "my_new_strategy": StrategySpec(
        key="my_new_strategy",
        cls=MyNewStrategy,
        config_section="strategy.my_new_strategy",
        description="[Kurzbeschreibung]",
        # Optional: R&D-Flags (für Research-Strategien)
        is_live_ready=True,  # Für Live-Trading freigegeben?
        tier="production",   # "production" oder "r_and_d"
        allowed_environments=("backtest", "offline_backtest", "paper", "live", "research"),
    ),
}
```

#### Registry-Flags Erklärung

**`is_live_ready`** (Default: `True`)
- `True` = Strategie kann in Live-Mode verwendet werden
- `False` = Strategie ist R&D-only, blockiert im Live-Mode

**`tier`** (Default: `"production"`)
- `"production"` = Produktionsreife Strategie
- `"r_and_d"` = Research-Strategie, benötigt `research.allow_r_and_d_strategies = true` in Config

**`allowed_environments`** (Default: alle Environments erlaubt)
- Tuple mit erlaubten Environment-Namen
- Standard: `("backtest", "offline_backtest", "paper", "live", "research")`
- R&D-Only Beispiel: `("backtest", "offline_backtest", "research")`

#### Beispiele

**Production-Ready Strategie:**
```python
"ma_crossover": StrategySpec(
    key="ma_crossover",
    cls=MACrossoverStrategy,
    config_section="strategy.ma_crossover",
    description="Moving Average Crossover (Trend-Following)",
    # Defaults sind ok: is_live_ready=True, tier="production"
)
```

**Research-Strategie (R&D-Only):**
```python
"ehlers_cycle_filter": StrategySpec(
    key="ehlers_cycle_filter",
    cls=EhlersCycleFilterStrategy,
    config_section="strategy.ehlers_cycle_filter",
    description="Ehlers DSP Cycle Filter (R&D-Only)",
    is_live_ready=False,  # Nicht für Live-Trading
    tier="r_and_d",
    allowed_environments=("backtest", "offline_backtest", "research"),
)
```

#### Gate-System

Die Registry prüft automatisch 3 Gates:

1. **Gate A: IS_LIVE_READY**
   - Wenn `is_live_ready=False` und `environment.mode=live` → ValueError

2. **Gate B: TIER**
   - Wenn `tier="r_and_d"` und `research.allow_r_and_d_strategies=false` → ValueError

3. **Gate C: ALLOWED_ENVIRONMENTS**
   - Wenn aktuelles Environment nicht in `allowed_environments` → ValueError

**Config für R&D-Strategien:**
```toml
[environment]
mode = "backtest"  # Nicht "live"!

[research]
allow_r_and_d_strategies = true  # Explizit erlauben
```

### 4.6 Schritt 6: Config-Block anlegen

Öffne `config.toml` und füge hinzu:

```toml
[strategy.my_new_strategy]
param1 = 20
param2 = 0.02
stop_pct = 0.02    # Stop-Loss (immer empfohlen!)
```

### 4.7 Schritt 7: Testen!

```bash
# Liste aller Strategien
python scripts/run_strategy_from_config.py --list-strategies

# Deine neue Strategie testen
python scripts/run_strategy_from_config.py --strategy my_new_strategy
```

---

## 5. Best Practices

### 5.1 Signal-Generierung

✅ **Do's:**

```python
# Signale deterministisch machen
np.random.seed(42) # Falls randomness nötig

# Vektorisierung bevorzugen
df["sma"] = df["close"].rolling(20).mean()  # ✅ Schnell

# NaN-Handling explizit
df["sma"] = df["sma"].fillna(method="bfill")
```

❌ **Don'ts:**

```python
# Keine Python-Loops über Bars
for i in range(len(df)):  # ❌ Langsam!
    df.loc[i, "sma"] = df["close"].iloc[i-20:i].mean()

# Kein I/O in Strategie
with open("trades.csv", "a") as f:  # ❌ Gehört nicht hierher!
    f.write(f"{signal}\n")
```

### 5.2 Parameter-Handling

✅ **Do's:**

```python
# Parameter aus Config laden
self.window = self.config.get("window", 20)

# Parameter validieren
if self.window < 2:
    raise ValueError("window muss >= 2 sein")

# Defaults setzen
def __init__(self, window: int = 20, ...):
    ...
```

❌ **Don'ts:**

```python
# Keine Magic Numbers
df["sma"] = df["close"].rolling(42).mean()  # ❌ Warum 42?

# Parameter nicht hart-kodieren
if df["rsi"] > 70:  # ❌ Sollte aus Config kommen
    ...
```

### 5.3 State-Management

✅ **Do's:**

```python
# Event → State Conversion
events = pd.Series(0, index=df.index)
events[cross_up] = 1
events[cross_down] = -1

# State persistieren
state = events.replace({-1: 0})
state = state.replace(0, pd.NA).ffill().fillna(0)
```

❌ **Don'ts:**

```python
# Keine isolierten Events zurückgeben
signals = pd.Series(0, index=df.index)
signals[cross_up] = 1  # ❌ Nur Events, keine States!
return signals
```

### 5.4 Performance

✅ **Do's:**

```python
# Pandas/NumPy nutzen
df["returns"] = df["close"].pct_change()

# Zwischenergebnisse cachen (in prepare())
def prepare(self, data):
    self._cached_indicator = self._compute_expensive(data)

# Best Practice: generate_signals bleibt möglichst "pure"/vektorisiert.
# prepare() ist der Hook für teure Vorberechnungen; run()/prepare_once() sorgen dafür,
# dass diese Vorberechnungen idempotent pro DataFrame ausgeführt werden.
```

❌ **Don'ts:**

```python
# Keine teuren Berechnungen in jedem generate_signals()
def generate_signals(self, data):
    # ❌ Wird bei jedem Backtest neu berechnet!
    indicator = self._very_expensive_computation(data)
```

---

## 6. Debugging & Tests

### 6.1 Unit-Tests

Erstelle Tests in `tests/test_strategies.py`:

```python
import pytest
import pandas as pd
import numpy as np
from src.strategies.my_new_strategy import MyNewStrategy

def test_my_new_strategy_basic():
    """Test basic signal generation."""
    # Arrange
    df = pd.DataFrame({
        "open": [100, 101, 102, 103, 104],
        "high": [101, 102, 103, 104, 105],
        "low": [99, 100, 101, 102, 103],
        "close": [100, 101, 102, 103, 104],
        "volume": [1000, 1100, 1200, 1300, 1400],
    }, index=pd.date_range("2024-01-01", periods=5, freq="1h"))

    strategy = MyNewStrategy(param1=2, param2=0.01)

    # Act
    signals = strategy.generate_signals(df)

    # Assert
    assert isinstance(signals, pd.Series)
    assert len(signals) == len(df)
    assert signals.isin([0, 1, -1]).all()

def test_my_new_strategy_from_config():
    """Test strategy creation from config."""
    from src.core.peak_config import load_config

    cfg = load_config()
    strategy = MyNewStrategy.from_config(cfg, "strategy.my_new_strategy")

    assert strategy.param1 == 20
    assert strategy.param2 == 0.02

@pytest.mark.smoke
def test_my_new_strategy_smoke():
    """Smoke test: Quick sanity check."""
    from src.strategies.registry import create_strategy_from_config
    from src.core.peak_config import load_config

    cfg = load_config()
    strategy = create_strategy_from_config("my_new_strategy", cfg)

    # Minimal data
    df = pd.DataFrame({
        "close": [100, 101, 102],
    }, index=pd.date_range("2024-01-01", periods=3, freq="1h"))

    signals = strategy.generate_signals(df)

    # Smoke test: No crashes, valid output
    assert isinstance(signals, pd.Series)
    assert len(signals) == 3
```

**Smoke Tests ausführen:**
```bash
# Nur Smoke Tests (schnell, ~1 Sekunde)
pytest -m smoke -q

# Alle Tests (vollständig)
pytest -q
```

### 6.2 Interaktive Tests

```python
# Jupyter Notebook / IPython
from src.core.peak_config import load_config
from src.strategies.my_new_strategy import MyNewStrategy
import pandas as pd
import matplotlib.pyplot as plt

# Strategie laden
cfg = load_config()
strategy = MyNewStrategy.from_config(cfg)

# Dummy-Daten
df = create_dummy_data(n_bars=200)

# Signale generieren
signals = strategy.generate_signals(df)

# Visualisieren
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

# Preis & Signale
ax1.plot(df.index, df["close"], label="Close")
ax1.scatter(df.index[signals == 1], df["close"][signals == 1],
            marker="^", c="green", s=100, label="Long Entry")
ax1.legend()
ax1.set_title("Signals")

# Signal-Serie
ax2.plot(df.index, signals, drawstyle="steps-post")
ax2.set_ylim(-0.5, 1.5)
ax2.set_yticks([0, 1])
ax2.set_title("Signal States")

plt.tight_layout()
plt.show()

# Stats
print(f"Total Bars: {len(df)}")
print(f"Long Bars: {(signals == 1).sum()}")
print(f"Flat Bars: {(signals == 0).sum()}")
print(f"Long %: {(signals == 1).sum() / len(signals):.1%}")
```

### 6.3 Backtest-Debugging

```python
from src.backtest.engine import BacktestEngine
from src.core.position_sizing import build_position_sizer_from_config
from src.core.risk import build_risk_manager_from_config

# Setup
cfg = load_config()
strategy = MyNewStrategy.from_config(cfg)
position_sizer = build_position_sizer_from_config(cfg)
risk_manager = build_risk_manager_from_config(cfg)

# Backtest
engine = BacktestEngine(
    core_position_sizer=position_sizer,
    risk_manager=risk_manager
)

def strategy_signal_fn(df, params):
    return strategy.generate_signals(df)

result = engine.run_realistic(
    df=df,
    strategy_signal_fn=strategy_signal_fn,
    strategy_params={"stop_pct": 0.02}
)

# Debug-Output
print(f"Total Return: {result.stats['total_return']:.2%}")
print(f"Total Trades: {result.stats['total_trades']}")
print(f"Blocked Trades: {result.blocked_trades}")
print(f"Win Rate: {result.stats['win_rate']:.2%}")

# Trades inspizieren
if result.trades:
    for i, trade in enumerate(result.trades[:5], 1):
        print(f"\nTrade {i}:")
        print(f"  Entry: {trade.entry_time} @ ${trade.entry_price:,.2f}")
        print(f"  Exit:  {trade.exit_time} @ ${trade.exit_price:,.2f}")
        print(f"  PnL:   ${trade.pnl:,.2f} ({trade.exit_reason})")
```

---

## 7. Erweiterte Konzepte

### 7.1 Multi-Timeframe-Strategien

```python
class MultiTFStrategy(BaseStrategy):
    """Strategie mit mehreren Timeframes."""

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        # Höheres Timeframe berechnen
        df_4h = data.resample("4h").agg({
            "open": "first",
            "high": "max",
            "low": "min",
            "close": "last",
            "volume": "sum",
        })

        # Trend auf 4h bestimmen
        df_4h["sma_200"] = df_4h["close"].rolling(200).mean()
        df_4h["trend"] = df_4h["close"] > df_4h["sma_200"]

        # Zurück auf 1h reindexen
        trend_1h = df_4h["trend"].reindex(data.index, method="ffill")

        # Entry nur in Trendrichtung
        df = data.copy()
        df["fast_ma"] = df["close"].rolling(10).mean()
        df["slow_ma"] = df["close"].rolling(30).mean()

        cross_up = (df["fast_ma"] > df["slow_ma"]) & (df["fast_ma"].shift(1) <= df["slow_ma"].shift(1))

        signals = pd.Series(0, index=df.index)
        signals[cross_up & trend_1h] = 1  # Nur long wenn 4h-Trend up

        # State-Conversion
        state = signals.replace(0, pd.NA).ffill().fillna(0).astype(int)
        return state
```

### 7.2 Regime-Aware-Strategien

```python
class RegimeAwareStrategy(BaseStrategy):
    """Strategie die sich an Marktregime anpasst."""

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        df = data.copy()

        # Regime-Detektion (z.B. Volatility)
        df["returns"] = df["close"].pct_change()
        df["volatility"] = df["returns"].rolling(20).std()
        df["avg_vol"] = df["volatility"].rolling(100).mean()

        df["high_vol"] = df["volatility"] > df["avg_vol"] * 1.5

        # Verschiedene Strategien je Regime
        # High-Vol: Mean-Reversion
        df["rsi"] = self._compute_rsi(df["close"], 14)
        df["mean_rev_long"] = df["rsi"] < 30

        # Low-Vol: Trend-Following
        df["fast_ma"] = df["close"].rolling(10).mean()
        df["slow_ma"] = df["close"].rolling(30).mean()
        df["trend_long"] = df["fast_ma"] > df["slow_ma"]

        # Regime-basierte Signal-Auswahl
        signals = pd.Series(0, index=df.index)
        signals[df["high_vol"] & df["mean_rev_long"]] = 1
        signals[~df["high_vol"] & df["trend_long"]] = 1

        # State-Conversion
        state = signals.replace(0, pd.NA).ffill().fillna(0).astype(int)
        return state

    def _compute_rsi(self, prices, window=14):
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
```

### 7.3 Machine-Learning-Strategien

```python
class MLStrategy(BaseStrategy):
    """Strategie mit ML-Modell."""

    def __init__(self, model_path: str = "models/my_model.pkl", **kwargs):
        super().__init__(**kwargs)
        self.model_path = model_path
        self.model = None

    def prepare(self, data: pd.DataFrame) -> None:
        """Lädt ML-Modell einmalig."""
        import joblib
        self.model = joblib.load(self.model_path)

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        if self.model is None:
            raise RuntimeError("Model not loaded. Call prepare() first!")

        # Features berechnen
        df = data.copy()
        df["returns"] = df["close"].pct_change()
        df["sma_10"] = df["close"].rolling(10).mean()
        df["sma_30"] = df["close"].rolling(30).mean()
        df["rsi"] = self._compute_rsi(df["close"], 14)

        # Feature-Matrix
        features = df[["returns", "sma_10", "sma_30", "rsi"]].fillna(0)

        # Prediction
        predictions = self.model.predict(features)

        # Predictions zu Signals
        signals = pd.Series(predictions, index=df.index).astype(int)
        return signals
```

---

## 8. Checkliste: Neue Strategie

Vor dem Backtest:

- [ ] `generate_signals()` implementiert
- [ ] `from_config()` implementiert
- [ ] Parameter validiert
- [ ] In Registry registriert
- [ ] Config-Block in `config.toml` angelegt
- [ ] Stop-Loss in Config gesetzt (`stop_pct`)
- [ ] Unit-Tests geschrieben
- [ ] Mit Dummy-Daten getestet
- [ ] Signale visualisiert

Vor dem Live-Trading:

- [ ] Mind. 6 Monate Backtest-Daten
- [ ] Sharpe Ratio >= 1.5
- [ ] Min. 50 Trades im Backtest
- [ ] Profit Factor >= 1.3
- [ ] Max Drawdown < 20%
- [ ] Win Rate dokumentiert
- [ ] Parameter-Sensitivität getestet
- [ ] Walk-Forward-Validation durchgeführt

---

## 9. Häufige Fehler

### 9.1 "Strategy returns events, not states"

❌ **Problem:**
```python
signals = pd.Series(0, index=df.index)
signals[cross_up] = 1  # Nur an Crossover-Punkten 1, sonst 0
return signals  # ❌ Engine denkt "flat" nach einem Bar
```

✅ **Lösung:**
```python
# State über Zeit persistieren
state = signals.replace(0, pd.NA).ffill().fillna(0)
return state  # ✅ Bleibt long bis Exit-Signal
```

### 9.2 "Not enough data"

❌ **Problem:**
```python
df["sma_200"] = df["close"].rolling(200).mean()
# ValueError: Need at least 200 bars, have only 100
```

✅ **Lösung:**
```python
def generate_signals(self, data):
    if len(data) < 200:
        raise ValueError(f"Need min. 200 bars, have only {len(data)}")
    # ... rest of code
```

### 9.3 "Index mismatch"

❌ **Problem:**
```python
signals = pd.Series([1, 0, 1, 0, 1])  # ❌ Kein Index!
return signals
```

✅ **Lösung:**
```python
signals = pd.Series([1, 0, 1, 0, 1], index=data.index)  # ✅ Index setzen
return signals
```

---

## 10. Weiterführende Ressourcen

### Dokumentation

- **Architektur-Übersicht:** `docs/PEAK_TRADE_OVERVIEW.md`
- **Backtest-Engine:** `docs/BACKTEST_ENGINE.md`
- **Config-System:** `docs/project_docs/CONFIG_SYSTEM.md`
- **Risk-Management:** `docs/project_docs/RISK_MANAGEMENT.md`

### Beispiel-Strategien

**Originale OOP-Strategien:**
- `src/strategies/ma_crossover.py` – Einfache Trend-Following (`KEY="ma_crossover"`)
- `src/strategies/rsi_reversion.py` – Mean-Reversion (`KEY="rsi_reversion"`)
- `src/strategies/breakout_donchian.py` – Breakout-Strategie (`KEY="breakout_donchian"`)

**Migrierte Legacy-Strategien (Phase 7):**
- `src/strategies/momentum.py` – Momentum-basierte Strategie (`KEY="momentum_1h"`)
- `src/strategies/bollinger.py` – Bollinger Bands Mean-Reversion (`KEY="bollinger_bands"`)
- `src/strategies/macd.py` – MACD Trend-Following (`KEY="macd"`)

### Übersicht: Alle OOP-Strategien

| KEY | Klasse | Typ | Regime | Beschreibung |
|-----|--------|-----|--------|--------------|
| `ma_crossover` | `MACrossoverStrategy` | Trend | trending | Fast/Slow MA Crossover |
| `rsi_reversion` | `RsiReversionStrategy` | Mean-Rev | ranging | RSI Oversold/Overbought |
| `breakout_donchian` | `DonchianBreakoutStrategy` | Breakout | trending | Donchian Channel Breakout |
| `momentum_1h` | `MomentumStrategy` | Trend | trending | Momentum über N Perioden |
| `bollinger_bands` | `BollingerBandsStrategy` | Mean-Rev | ranging | Bollinger Bands Mean-Rev |
| `macd` | `MACDStrategy` | Trend | trending | MACD Signal-Linie Crossover |

### Tools & Libraries

- **Pandas:** Datenverarbeitung
- **NumPy:** Numerische Berechnungen
- **TA-Lib:** Technische Indikatoren (optional)
- **Backtrader:** Alternative Backtest-Library (Vergleich)

---

## Related Docs

### Core Documentation
- 🚪 **[Documentation Frontdoor](README.md)** – Navigate all docs by audience & topic
- 📖 **[Peak Trade Overview](PEAK_TRADE_OVERVIEW.md)** – Architecture, modules, data flow
- 🔬 **[Backtest Engine](BACKTEST_ENGINE.md)** – Engine contract, execution modes, extension hooks

### Research & Portfolio
- 📊 **[Research → Live Playbook](PLAYBOOK_RESEARCH_TO_LIVE_PORTFOLIOS.md)** – Research-to-production workflow
- 🎯 **[Portfolio Recipes](PORTFOLIO_RECIPES_AND_PRESETS.md)** – Portfolio configurations

### Technical Guides
- [Position Sizing & Overlays](../src/core/position_sizing.py) – Position sizing implementation
- [Config System](project_docs/CONFIG_SYSTEM.md) – Configuration deep dive *(if exists)*

---

**Happy Trading! 🚀**

**Erstellt:** Dezember 2024
**Letztes Update:** Januar 2026
**Status:** Produktionsreif für Backtesting
