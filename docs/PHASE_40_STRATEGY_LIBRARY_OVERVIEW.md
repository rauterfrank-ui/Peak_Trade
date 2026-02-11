# Phase 40: Strategy Library & Portfolio-Track v1

## Übersicht

Phase 40 erweitert Peak_Trade um eine modulare **Strategy Library** mit drei neuen Komponenten:

1. **Breakout Strategy** – Trend-Following mit Stop-Loss/Take-Profit
2. **Vol Regime Filter** – Volatilitäts-basierter Trading-Filter
3. **Composite Strategy** – Multi-Strategy Portfolio-Combiner

Diese Komponenten können einzeln oder kombiniert verwendet werden, um flexible Portfolio-Strategien zu erstellen.

---

## Neue Strategien

### 1. Breakout Strategy (`src/strategies/breakout.py`)

**Zweck:** Trend-Following basierend auf N-Bar High/Low Breakouts.

**Konzept:**
- Long Entry: Close > N-Bar High (Breakout nach oben)
- Short Entry: Close < N-Bar Low (Breakout nach unten)
- Exit: Stop-Loss, Take-Profit oder Trailing-Stop

**Parameter:**

| Parameter | Typ | Default | Beschreibung |
|-----------|-----|---------|--------------|
| `lookback_breakout` | int | 20 | Lookback-Fenster für High/Low |
| `stop_loss_pct` | float | None | Stop-Loss in % (z.B. 0.03 = 3%) |
| `take_profit_pct` | float | None | Take-Profit in % |
| `trailing_stop_pct` | float | None | Trailing-Stop in % |
| `side` | str | "both" | "long", "short", oder "both" |

**Beispiel-Konfiguration:**

```toml
[strategy.breakout]
lookback_breakout = 20
stop_loss_pct = 0.03
take_profit_pct = 0.06
side = "both"
```

**Verwendung im Code:**

```python
from src.strategies.breakout import BreakoutStrategy

strategy = BreakoutStrategy(
    lookback_breakout=20,
    stop_loss_pct=0.03,
    take_profit_pct=0.06,
)
signals = strategy.generate_signals(df)
```

---

### 2. Vol Regime Filter (`src/strategies/vol_regime_filter.py`)

**Zweck:** Volatilitäts-basierter Filter für Trading-Entscheidungen.

**Konzept:**
- Berechnet ATR oder realized Volatility
- Erlaubt Trades nur wenn Volatilität in definiertem Bereich liegt
- Kann mit anderen Strategien kombiniert werden

**Parameter:**

| Parameter | Typ | Default | Beschreibung |
|-----------|-----|---------|--------------|
| `vol_window` | int | 20 | Volatilitäts-Berechnungsfenster |
| `vol_method` | str | "atr" | "atr", "std", oder "realized" |
| `vol_percentile_low` | float | None | Min. Volatilitäts-Perzentil |
| `vol_percentile_high` | float | None | Max. Volatilitäts-Perzentil |
| `min_vol` | float | None | Absoluter Min-Vol-Schwellwert |
| `max_vol` | float | None | Absoluter Max-Vol-Schwellwert |
| `atr_threshold` | float | None | ATR-Mindest-Schwellwert |
| `invert` | bool | False | Invertiert die Filter-Logik |

**Beispiel-Konfiguration:**

```toml
[strategy.vol_regime_filter]
vol_window = 14
vol_method = "atr"
vol_percentile_low = 25
vol_percentile_high = 75
```

**Verwendung im Code:**

```python
from src.strategies.vol_regime_filter import VolRegimeFilter
from src.strategies.rsi_reversion import RsiReversionStrategy

# Trading-Strategie
trading_strategy = RsiReversionStrategy(rsi_window=14)

# Filter
vol_filter = VolRegimeFilter(
    vol_window=14,
    vol_percentile_low=25,
    vol_percentile_high=75,
)

# Signale generieren und filtern
raw_signals = trading_strategy.generate_signals(df)
filtered_signals = vol_filter.apply_to_signals(df, raw_signals)
```

---

### 2b. Vol Regime Wrapper (universal)

**Zweck:** Beliebige Strategie nach Regime-Labels filtern (nur in erlaubten Regimes Signale/Positionen durchlassen). Für Backtest und Sweeps.

**Verwendung im Code:**

```python
import pandas as pd
from src.strategies.wrappers.vol_regime_wrapper import VolRegimeWrapper
from src.strategies.ma_crossover import MACrossoverStrategy

base = MACrossoverStrategy(fast=10, slow=20)
regime_labels = pd.Series(["low_vol", "high_vol", "low_vol"], index=df.index)  # an data index
wrapper = VolRegimeWrapper(
    base, regime_labels, allowed_regimes={"low_vol"}, mode="signals", allow_unknown=False
)
signals = wrapper.generate_signals(df)
```

---

### 3. Composite Strategy (`src/strategies/composite.py`)

**Zweck:** Kombiniert mehrere Strategien zu einem Portfolio.

**Konzept:**
- Aggregiert Signale mehrerer Sub-Strategien
- Unterstützt verschiedene Aggregationsmethoden
- Kann Filter integrieren

**Aggregationsmethoden:**

| Methode | Beschreibung |
|---------|--------------|
| `weighted` | Gewichtetes Mittel der Signale |
| `voting` | Mehrheitsentscheidung |
| `unanimous` | Alle müssen übereinstimmen |
| `any_long` | Long wenn mindestens eine Long ist |
| `any_short` | Short wenn mindestens eine Short ist |

**Parameter:**

| Parameter | Typ | Default | Beschreibung |
|-----------|-----|---------|--------------|
| `strategies` | list | - | Liste von (Strategy, Weight)-Tupeln |
| `aggregation` | str | "weighted" | Aggregationsmethode |
| `signal_threshold` | float | 0.3 | Schwelle für Long/Short-Entscheidung |
| `filter_strategy` | Strategy | None | Optional: Filter-Strategie |

**Beispiel-Konfiguration:**

```toml
[strategy.portfolio_phase40_example]
components = ["rsi_reversion", "breakout", "ma_crossover"]
weights = [0.4, 0.3, 0.3]
aggregation = "weighted"
signal_threshold = 0.25
```

**Verwendung im Code:**

```python
from src.strategies.composite import CompositeStrategy
from src.strategies.rsi_reversion import RsiReversionStrategy
from src.strategies.breakout import BreakoutStrategy
from src.strategies.ma_crossover import MACrossoverStrategy

composite = CompositeStrategy(
    strategies=[
        (RsiReversionStrategy(), 0.4),
        (BreakoutStrategy(), 0.3),
        (MACrossoverStrategy(), 0.3),
    ],
    aggregation="weighted",
    signal_threshold=0.3,
)

signals = composite.generate_signals(df)

# Komponenten-Signale analysieren
component_signals = composite.get_component_signals(df)
```

---

## Config-Beispiele

### Alle Strategien in `config/config.toml`:

```toml
# ============================================================================
# PHASE 40: STRATEGY LIBRARY
# ============================================================================

[strategy.breakout]
lookback_breakout = 20
stop_loss_pct = 0.03
take_profit_pct = 0.06
side = "both"

[strategy.vol_regime_filter]
vol_window = 14
vol_method = "atr"
vol_percentile_low = 25
vol_percentile_high = 75

[strategy.composite]
components = ["rsi_reversion", "breakout"]
weights = [0.5, 0.5]
aggregation = "weighted"
signal_threshold = 0.3

[strategy.portfolio_phase40_example]
components = ["rsi_reversion", "breakout", "ma_crossover"]
weights = [0.4, 0.3, 0.3]
aggregation = "weighted"
signal_threshold = 0.25
```

---

## Demo-Script

Das Demo-Script zeigt alle neuen Strategien in Aktion:

```bash
# Alle Strategien testen
python3 scripts/demo_phase40_portfolio_backtest.py

# Einzelne Strategie
python3 scripts/demo_phase40_portfolio_backtest.py --strategy breakout

# Mit Custom-Config
python3 scripts/demo_phase40_portfolio_backtest.py --config config/config.toml

# Report generieren
python3 scripts/demo_phase40_portfolio_backtest.py --report reports/my_report.md
```

**Optionen:**

| Option | Beschreibung |
|--------|--------------|
| `--config` | Pfad zur Config-Datei |
| `--strategy` | breakout, rsi_vol_filter, composite, all |
| `--bars` | Anzahl Bars für synthetische Daten |
| `--seed` | Random Seed für Reproduzierbarkeit |
| `--report` | Pfad für Markdown-Report |

---

## Registry-Integration

Die neuen Strategien sind automatisch in der Registry registriert:

```python
from src.strategies.registry import (
    get_available_strategy_keys,
    create_strategy_from_config,
    list_strategies,
)

# Verfügbare Strategien anzeigen
list_strategies(verbose=True)

# Strategie aus Config erstellen
from src.core.peak_config import load_config
cfg = load_config("config/config.toml")
strategy = create_strategy_from_config("breakout", cfg)
```

---

## Tests

Unit-Tests für alle neuen Komponenten:

```bash
# Alle Phase-40-Tests
python3 -m pytest tests/test_strategy_breakout.py -v
python3 -m pytest tests/test_strategy_vol_regime_filter.py -v
python3 -m pytest tests/test_strategy_composite.py -v

# Alle Strategy-Tests
python3 -m pytest tests/test_strategy*.py -v
```

---

## Dateien (Phase 40)

### Neue Dateien:

| Datei | Beschreibung |
|-------|--------------|
| `src/strategies/breakout.py` | Breakout Strategy |
| `src/strategies/vol_regime_filter.py` | Vol Regime Filter |
| `src/strategies/composite.py` | Composite Strategy |
| `tests/test_strategy_breakout.py` | Tests Breakout |
| `tests/test_strategy_vol_regime_filter.py` | Tests Vol Filter |
| `tests/test_strategy_composite.py` | Tests Composite |
| `scripts/demo_phase40_portfolio_backtest.py` | Demo-Script |
| `docs/PHASE_40_STRATEGY_LIBRARY_OVERVIEW.md` | Diese Dokumentation |

### Geänderte Dateien:

| Datei | Änderung |
|-------|----------|
| `src/strategies/registry.py` | Neue Strategien registriert |
| `src/strategies/__init__.py` | STRATEGY_REGISTRY erweitert |
| `config/config.toml` | Strategy-Konfigurationen hinzugefügt |

---

## Best Practices

### 1. Kombination von Strategien

```python
# RSI für Mean-Reversion + Vol-Filter für Sicherheit
rsi = RsiReversionStrategy(lower=25, upper=75)
vol_filter = VolRegimeFilter(vol_percentile_low=20, vol_percentile_high=80)

raw_signals = rsi.generate_signals(df)
safe_signals = vol_filter.apply_to_signals(df, raw_signals)
```

### 2. Portfolio-Diversifikation

```python
# Trend + Mean-Reversion kombinieren
composite = CompositeStrategy(
    strategies=[
        (BreakoutStrategy(side="long"), 0.3),        # Trend
        (RsiReversionStrategy(), 0.4),               # Mean-Reversion
        (MACrossoverStrategy(), 0.3),                # Trend
    ],
    aggregation="voting",  # Mehrheitsentscheidung
)
```

### 3. Risk Management

```python
# Breakout mit konservativem Risk
strategy = BreakoutStrategy(
    lookback_breakout=20,
    stop_loss_pct=0.02,       # Enger Stop
    take_profit_pct=0.04,     # 2:1 Risk/Reward
    trailing_stop_pct=0.015,  # Trailing für Gewinne
)
```

---

## 10. Abschluss Phase 40 & Baseline für Phase 41+

Ein umfassender Sanity-Check über Strategie-, Regime- und Experiment-Tests wurde ausgeführt:

```bash
python3 -m pytest tests/test_strategy*py tests/test_regime*py tests/test_experiments*py -q
```

Ergebnis:

* **446 passed in ca. 10.6 Sekunden**
* Keine Warnungen oder Fehler, alle relevanten Teilbereiche abgedeckt.

Die 446 grünen Tests in ~10s bestätigen u.a.:

* **RSI-Reversion**
  * Mean-Reversion-Logik ist stabil implementiert.
* **Breakout/Momentum**
  * Trend-Following-Strategie mit Stop-Loss/Take-Profit und ATR-Filter funktioniert wie erwartet.
* **Vol-Regime-Filter**
  * Filter-Mode und Regime-Mode arbeiten korrekt (Regime-Ermittlung + Skalierung der Exposure).
* **Composite/Portfolio**
  * Multi-Strategy-Aggregation läuft konsistent und integriert die neuen Strategien sauber.
* **Regime-Detection**
  * Marktregime-Erkennung ist integriert und spielt mit den Strategien zusammen.
* **Experiment-Sweeps**
  * Parameter-Sweeps und Optimierung für alle Strategien laufen durch und sind funktionsfähig.

**Fazit:**

* **Phase 40 – Strategy Library v1.1** ist abgeschlossen.
* Der aktuelle Codestand gilt als **stabile, getestete Baseline** für alle weiteren Arbeiten in **Phase 41+** (z.B. erweiterte Sweeps, Reporting, weitere Strategien oder Live-nahe Flows).

---

## Nächste Schritte (Phase 41+)

- [ ] Walk-Forward Optimierung für Composite-Strategien
- [ ] Correlation-Aware Portfolio-Weighting
- [ ] Dynamische Regime-Adaption
- [ ] Live-Integration der neuen Strategien
