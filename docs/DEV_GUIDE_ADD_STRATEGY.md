# Developer Guide: Neue Strategie hinzufügen

## Ziel

Neue Single-Strategie hinzufügen, die Backtest, Research-CLI und ggf. Portfolio-Layer nutzen kann.

---

## Voraussetzungen

Grundverständnis von:
- `src/strategies/*` – Bestehende Strategien als Referenz
- `src/backtest/engine.py` – BacktestEngine für Tests
- `src/experiments/*` – Für Sweeps und Portfolio-Integration
- `config/config.toml` – Strategie-Block-Konfiguration
- `src/strategies/base.py` – BaseStrategy-Klasse

---

## Schritt-für-Schritt-Workflow

### 1. Strategie-Datei anlegen

Erstelle eine neue Datei in `src/strategies/`, z.B.:
- `src/strategies/my_new_strategy.py`

**Minimal-Signatur:** Die Strategie sollte entweder:
- Von `BaseStrategy` erben (empfohlen für OOP-Strategien)
- Oder eine `generate_signals(df, params)` Funktion bereitstellen (funktionale Strategien)

**Beispiel-Template (OOP mit BaseStrategy):**

```python
"""
My New Strategy
===============
Kurze Beschreibung der Strategie.

Konzept:
- Entry: [Beschreibung]
- Exit: [Beschreibung]
"""
from __future__ import annotations

from typing import Any, Dict, Optional
import pandas as pd
import numpy as np

from .base import BaseStrategy, StrategyMetadata


class MyNewStrategy(BaseStrategy):
    """
    My New Strategy (OOP-Version).

    Signale:
    - 1 (long): [Bedingung]
    - -1 (exit): [Bedingung]
    - 0: Kein Signal

    Args:
        lookback: Lookback-Periode (default: 20)
        threshold: Entry-Schwelle (default: 1.5)
        config: Optional Config-Dict (überschreibt Konstruktor-Parameter)
        metadata: Optional StrategyMetadata

    Example:
        >>> strategy = MyNewStrategy(lookback=20, threshold=1.5)
        >>> signals = strategy.generate_signals(df)
    """

    KEY = "my_new_strategy"  # Muss mit Config-Key übereinstimmen

    def __init__(
        self,
        lookback: int = 20,
        threshold: float = 1.5,
        config: Optional[Dict[str, Any]] = None,
        metadata: Optional[StrategyMetadata] = None,
    ) -> None:
        """
        Initialisiert My New Strategy.

        Args:
            lookback: Lookback-Fenster
            threshold: Entry-Schwelle
            config: Optional Config-Dict (überschreibt Parameter)
            metadata: Optional Metadata
        """
        # Config überschreibt Parameter
        if config:
            lookback = config.get("lookback", lookback)
            threshold = config.get("threshold", threshold)

        super().__init__(metadata=metadata)
        self._lookback = lookback
        self._threshold = threshold

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        """
        Generiert Signale basierend auf Strategie-Logik.

        Args:
            df: DataFrame mit OHLCV-Daten (muss 'close' Spalte haben)

        Returns:
            Series mit Signalen:
            - 1: Long-Entry
            - -1: Exit
            - 0: Kein Signal
        """
        # Strategie-Logik hier implementieren
        signals = pd.Series(0, index=df.index, dtype=int)

        # Beispiel: Einfacher Moving Average Crossover
        fast_ma = df['close'].rolling(window=self._lookback // 2).mean()
        slow_ma = df['close'].rolling(window=self._lookback).mean()

        # Entry: Fast MA kreuzt über Slow MA
        entry_condition = (fast_ma > slow_ma) & (fast_ma.shift(1) <= slow_ma.shift(1))
        signals[entry_condition] = 1

        # Exit: Fast MA kreuzt unter Slow MA
        exit_condition = (fast_ma < slow_ma) & (fast_ma.shift(1) >= slow_ma.shift(1))
        signals[exit_condition] = -1

        return signals

    @classmethod
    def from_config(cls, config: Any, config_key: str) -> "MyNewStrategy":
        """
        Erstellt Strategie aus Config.

        Args:
            config: PeakConfig oder Dict
            config_key: Config-Key (z.B. "strategy.my_new_strategy")

        Returns:
            MyNewStrategy-Instanz
        """
        if hasattr(config, "get"):
            params = config.get(config_key, {})
        else:
            params = config.get(config_key, {}) if isinstance(config, dict) else {}

        return cls(**params)
```

**Beispiel-Template (funktional):**

```python
"""
My New Strategy (Functional)
============================
Funktionale Strategie-Variante.
"""
from typing import Dict
import pandas as pd


def generate_signals(df: pd.DataFrame, params: Dict) -> pd.Series:
    """
    Generiert Signale basierend auf Strategie-Logik.

    Args:
        df: DataFrame mit OHLCV-Daten
        params: Dict mit Strategie-Parametern

    Returns:
        Series mit Signalen (1 = Long, -1 = Exit, 0 = Neutral)
    """
    lookback = params.get("lookback", 20)
    threshold = params.get("threshold", 1.5)

    # Strategie-Logik hier implementieren
    signals = pd.Series(0, index=df.index, dtype=int)

    # ... Implementierung ...

    return signals
```

---

### 2. Strategie in Registry registrieren

Öffne `src/strategies/__init__.py` und füge einen Eintrag hinzu:

```python
STRATEGY_REGISTRY = {
    # ... bestehende Strategien ...
    "my_new_strategy": "my_new_strategy",  # Key muss mit Config-Key übereinstimmen
}
```

**Wichtig:**
- Der Key in `STRATEGY_REGISTRY` muss mit dem Config-Key in `config.toml` übereinstimmen
- Der Wert ist der Modul-Name (ohne `.py`)

---

### 3. Config in config/config.toml hinzufügen

Füge einen neuen Block in `config/config.toml` hinzu:

```toml
[strategy.my_new_strategy]
type = "my_new_strategy"
lookback = 20
threshold = 1.5
```

**Wichtig:**
- Der Key `[strategy.my_new_strategy]` muss mit dem Registry-Key übereinstimmen
- `type` sollte mit dem Registry-Key übereinstimmen (für Kompatibilität)

---

### 4. Integration in Backtests & Research

**Backtest-CLI:**
```bash
python scripts/run_backtest.py \
  --strategy my_new_strategy \
  --symbol BTC/EUR \
  --timeframe 1h \
  --bars 1000
```

**Research-CLI:**
```bash
python scripts/research_cli.py strategy \
  --strategy my_new_strategy \
  --symbol BTC/EUR \
  --timeframe 1h
```

**Sweeps (Parameter-Optimierung):**
Falls die Strategie in Sweeps verwendet werden soll, füge sie zu `src/experiments/strategy_sweeps.py` hinzu (falls vorhanden).

---

### 5. Tests schreiben

Erstelle eine neue Testdatei, z.B.:
- `tests/test_strategies_my_new_strategy.py`

**Minimal-Tests:**

```python
"""
Tests für My New Strategy
"""
from __future__ import annotations

import pandas as pd
import pytest

from src.strategies.my_new_strategy import MyNewStrategy


def test_my_new_strategy_generates_signals():
    """Testet dass Strategie Signale erzeugt ohne Exception."""
    # Dummy-Daten erstellen
    dates = pd.date_range("2025-01-01", periods=100, freq="1h")
    df = pd.DataFrame({
        "close": [100 + i * 0.1 for i in range(100)],
        "open": [100 + i * 0.1 for i in range(100)],
        "high": [101 + i * 0.1 for i in range(100)],
        "low": [99 + i * 0.1 for i in range(100)],
        "volume": [1000] * 100,
    }, index=dates)

    # Strategie erstellen
    strategy = MyNewStrategy(lookback=20, threshold=1.5)

    # Signale generieren
    signals = strategy.generate_signals(df)

    # Prüfen
    assert len(signals) == len(df)
    assert signals.dtype == int
    assert set(signals.unique()).issubset({-1, 0, 1})


def test_my_new_strategy_from_config():
    """Testet dass Strategie aus Config erstellt werden kann."""
    config = {
        "strategy.my_new_strategy": {
            "lookback": 30,
            "threshold": 2.0,
        }
    }

    strategy = MyNewStrategy.from_config(config, "strategy.my_new_strategy")

    assert strategy._lookback == 30
    assert strategy._threshold == 2.0
```

**Backtest-Integration-Test:**

```python
def test_my_new_strategy_backtest_integration():
    """Testet dass Strategie in BacktestEngine funktioniert."""
    from src.backtest.engine import BacktestEngine

    # Dummy-Daten erstellen
    dates = pd.date_range("2025-01-01", periods=200, freq="1h")
    df = pd.DataFrame({
        "close": [100 + i * 0.1 for i in range(200)],
        "open": [100 + i * 0.1 for i in range(200)],
        "high": [101 + i * 0.1 for i in range(200)],
        "low": [99 + i * 0.1 for i in range(200)],
        "volume": [1000] * 200,
    }, index=dates)

    # Strategie erstellen
    strategy = MyNewStrategy(lookback=20, threshold=1.5)

    # Backtest durchführen
    engine = BacktestEngine()
    result = engine.run_realistic(
        df=df,
        strategy_signal_fn=strategy.generate_signals,
        strategy_params={},
    )

    # Prüfen
    assert result is not None
    assert hasattr(result, "trades")
```

---

### 6. Dokumentation

**Optional: Update in:**
- `PEAK_TRADE_STATUS_OVERVIEW.md` (nur wenn die Strategie besonders wichtig ist)
- Eigene Mini-Sektion in einem Strategy-Overview (falls vorhanden)

**Empfohlen:**
- Docstring in der Strategie-Klasse/Funktion sollte klar sein
- Beispiel-Usage im Docstring (siehe Template oben)

---

## Best Practices & Safety

### ✅ DO

- **Parameter nur über Config**: Keine Hardcoded-Werte in der Strategie
- **Konsistente Signale**: Signale sollten `-1`, `0`, oder `1` sein
- **Dokumentation**: Klare Docstrings mit Beispielen
- **Tests**: Mindestens Smoke-Test und Backtest-Integration-Test

### ❌ DON'T

- **Keine Hardcoded-Markets**: Strategie sollte für alle Symbole funktionieren
- **Keine API-Keys**: Keine sensiblen Daten in der Strategie
- **Kein direkter Live-Order-Flow**: Strategien erzeugen nur Signale, keine Orders
- **Keine Side-Effects**: Strategie sollte keine Dateien schreiben oder externe Services aufrufen

---

## Beispiel-Strategien als Referenz

- **OOP-Strategien:**
  - `src/strategies/ma_crossover.py` – MA-Crossover mit BaseStrategy
  - `src/strategies/momentum.py` – Momentum-Strategie mit BaseStrategy
  - `src/strategies/rsi.py` – RSI-Strategie (funktional)

- **Funktionale Strategien:**
  - `src/strategies/ecm.py` – ECM-Strategie (funktional)

---

## Troubleshooting

**Problem:** Strategie wird nicht gefunden
- **Lösung:** Prüfe, ob Registry-Eintrag korrekt ist und Config-Key übereinstimmt

**Problem:** Signale werden nicht generiert
- **Lösung:** Prüfe, ob DataFrame die erwarteten Spalten hat (`close`, `open`, `high`, `low`, `volume`)

**Problem:** Backtest schlägt fehl
- **Lösung:** Prüfe, ob Signale das erwartete Format haben (`-1`, `0`, `1`)

---

## Siehe auch

- `ARCHITECTURE_OVERVIEW.md` – Architektur-Übersicht
- `src/strategies/base.py` – BaseStrategy-Klasse
- `src/strategies/__init__.py` – Strategy-Registry
- `PEAK_TRADE_STATUS_OVERVIEW.md` – Projekt-Status

