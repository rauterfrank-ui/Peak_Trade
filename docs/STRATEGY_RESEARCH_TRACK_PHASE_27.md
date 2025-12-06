# Peak_Trade Phase 27: Strategy Research Track

## Übersicht

Phase 27 erweitert die Strategie-Bibliothek um drei neue Research-Strategien für verschiedene Marktregime. Alle Strategien folgen dem etablierten `BaseStrategy`-Contract und sind vollständig in die bestehende Infrastruktur integriert.

**WICHTIG**: Alle Strategien sind ausschließlich für **Research/Backtest/Shadow** - NICHT für Live-Trading!

## Neue Strategien

### 1. VolBreakoutStrategy (vol_breakout)

**Konzept**: ATR-basierte Volatility Breakout Strategy nach dem "Coiled Spring"-Prinzip.

**Idee**: Nach Phasen niedriger Volatilität (Konsolidierung) folgen oft starke Ausbrüche. Die Strategie identifiziert diese Breakouts und nutzt einen Volatilitäts-Filter, um falsche Signale in ruhigen Märkten zu vermeiden.

**Parameter**:
| Parameter | Default | Beschreibung |
|-----------|---------|--------------|
| `lookback_breakout` | 20 | Lookback für n-Bar Hoch/Tief |
| `vol_window` | 14 | Fenster für ATR-Berechnung |
| `vol_percentile` | 50.0 | Vol-Perzentil für Filter (0-100) |
| `atr_multiple` | 1.5 | ATR-Multiple für Breakout-Bestätigung |
| `side` | "both" | Trading-Richtung ("long", "short", "both") |

**Signale**:
- `1` (Long): Close > n-Bar-High UND Vol > Perzentil
- `-1` (Short): Close < n-Bar-Low UND Vol > Perzentil
- `0`: Position halten

**Geeignet für**: Märkte mit klaren Konsolidierungs- und Ausbruchsphasen.

```python
from src.strategies.vol_breakout import VolBreakoutStrategy

strategy = VolBreakoutStrategy(
    lookback_breakout=20,
    vol_window=14,
    vol_percentile=60.0,
    side="both",
)
signals = strategy.generate_signals(df)
```

---

### 2. MeanReversionChannelStrategy (mean_reversion_channel)

**Konzept**: Bollinger-ähnliche Kanal-Reversion-Strategie.

**Idee**: In Seitwärtsmärkten tendieren Preise dazu, zu ihrem Mittelwert zurückzukehren. Die Strategie nutzt Übertreibungen (Preis außerhalb der Bänder) für Einstiege.

**Parameter**:
| Parameter | Default | Beschreibung |
|-----------|---------|--------------|
| `window` | 20 | Lookback für MA und Std-Berechnung |
| `num_std` | 2.0 | Anzahl Standardabweichungen für Bänder |
| `exit_at_mean` | True | Exit bei Rückkehr zum Mean (sonst: zum Band) |
| `max_holding_bars` | None | Max. Haltedauer (None = unbegrenzt) |
| `price_col` | "close" | Preis-Spalte für Berechnung |

**Signale**:
- `1` (Long): Close < Lower Band (überverkauft)
- `-1` (Short): Close > Upper Band (überkauft)
- `0`: Exit wenn Preis zurück zum Mean/Band

**Geeignet für**: Seitwärtsmärkte (Ranging Markets).

```python
from src.strategies.mean_reversion_channel import MeanReversionChannelStrategy

strategy = MeanReversionChannelStrategy(
    window=20,
    num_std=2.0,
    exit_at_mean=True,
)
signals = strategy.generate_signals(df)
```

---

### 3. RsiReversionStrategy (rsi_reversion) - ENHANCED

**Konzept**: RSI Mean-Reversion mit optionalem Trendfilter (Phase 27 erweitert).

**Idee**: RSI-Extreme (überverkauft/überkauft) deuten auf potenzielle Umkehrpunkte hin. Die Strategie nutzt diese Signale, optional gefiltert durch einen Trendindikator.

**Neue Features (Phase 27)**:
- **Wilder-Smoothing**: Stabilere RSI-Berechnung (EMA-basiert, wie von Welles Wilder erfunden)
- **Trendfilter**: Nur Long wenn Preis > MA, nur Short wenn Preis < MA
- **Exit-Levels**: Konfigurierbare Exit-Schwellen für neutralen Bereich

**Parameter**:
| Parameter | Default | Beschreibung |
|-----------|---------|--------------|
| `rsi_window` | 14 | RSI-Berechnungsperiode |
| `lower` | 30.0 | Oversold-Level (Long Entry) |
| `upper` | 70.0 | Overbought-Level (Short Entry) |
| `exit_lower` | 50.0 | RSI-Level für Long-Exit |
| `exit_upper` | 50.0 | RSI-Level für Short-Exit |
| `use_trend_filter` | False | MA-Trendfilter aktivieren |
| `trend_ma_window` | 50 | MA-Periode für Trendfilter |
| `use_wilder` | True | Wilder-Smoothing verwenden |
| `price_col` | "close" | Preis-Spalte |

**Signale**:
- `1` (Long): RSI < lower (überverkauft) + optional Preis > MA
- `-1` (Short): RSI > upper (überkauft) + optional Preis < MA
- `0`: Exit wenn RSI in neutralen Bereich zurückkehrt

**Geeignet für**: Seitwärtsmärkte mit klaren Übertreibungen.

```python
from src.strategies.rsi_reversion import RsiReversionStrategy

# Standard mit Wilder-Smoothing
strategy = RsiReversionStrategy(
    rsi_window=14,
    lower=30.0,
    upper=70.0,
    use_wilder=True,
)

# Mit Trendfilter
strategy_trend = RsiReversionStrategy(
    rsi_window=14,
    lower=30.0,
    upper=70.0,
    use_trend_filter=True,
    trend_ma_window=50,
)
signals = strategy_trend.generate_signals(df)
```

---

## Config-Integration

Alle neuen Strategien können über `config.toml` konfiguriert werden:

```toml
[strategy.vol_breakout]
lookback_breakout = 20
vol_window = 14
vol_percentile = 50.0
atr_multiple = 1.5
side = "both"

[strategy.mean_reversion_channel]
window = 20
num_std = 2.0
exit_at_mean = true
max_holding_bars = 50
price_col = "close"

[strategy.rsi_reversion]
rsi_window = 14
lower = 30.0
upper = 70.0
exit_lower = 50.0
exit_upper = 50.0
use_trend_filter = false
trend_ma_window = 50
use_wilder = true
price_col = "close"
```

---

## Registry-Integration

Alle Strategien sind in `STRATEGY_REGISTRY` registriert:

```python
STRATEGY_REGISTRY = {
    # ... bestehende Strategien ...
    # Phase 27: Strategy Research Track
    "vol_breakout": "vol_breakout",
    "mean_reversion_channel": "mean_reversion_channel",
    "rsi_reversion": "rsi_reversion",
}
```

Verwendung über Registry:

```python
from src.strategies import load_strategy

generate_signals = load_strategy("vol_breakout")
signals = generate_signals(df, params)
```

Oder über OOP-API:

```python
from src.strategies.registry import create_strategy_from_config
from src.core.peak_config import load_config

cfg = load_config()
strategy = create_strategy_from_config("vol_breakout", cfg)
signals = strategy.generate_signals(df)
```

---

## API-Contract

Alle Strategien implementieren:

```python
class BaseStrategy(ABC):
    KEY: str  # Registry-Key

    def __init__(self, config=None, metadata=None): ...

    @classmethod
    def from_config(cls, cfg, section: str) -> "BaseStrategy": ...

    def generate_signals(self, data: pd.DataFrame) -> pd.Series: ...

    def validate(self) -> None: ...
```

**Signal-Konvention**:
- `1` = Long-Position
- `-1` = Short-Position
- `0` = Flat (keine Position)

**Input**: DataFrame mit OHLCV-Daten (mindestens `close`-Spalte)

**Output**: `pd.Series` mit Index = data.index, Werten in `{-1, 0, 1}`

---

## Metadata

Jede Strategie hat `StrategyMetadata` mit:

```python
@dataclass
class StrategyMetadata:
    name: str           # "Volatility Breakout"
    description: str    # Ausführliche Beschreibung
    version: str        # "1.0.0"
    author: str         # "Peak_Trade"
    regime: str         # "breakout", "ranging", "any"
    tags: List[str]     # ["breakout", "volatility", "atr"]
```

Regime-Tags:
- `vol_breakout`: `regime="breakout"`
- `mean_reversion_channel`: `regime="ranging"`
- `rsi_reversion`: `regime="ranging"`

---

## Tests

Tests in `tests/test_strategies_phase27.py`:

```bash
.venv/bin/pytest tests/test_strategies_phase27.py -v
```

31 Tests abdecken:
- Basis-Initialisierung
- Custom-Parameter
- Signalgenerierung
- Validation-Errors
- Legacy-API
- Metadata
- Integration

---

## Demo

Demo-Script: `scripts/demo_strategy_research.py`

```bash
.venv/bin/python scripts/demo_strategy_research.py
```

---

## Verwendungshinweise

### Marktregime-Auswahl

| Strategie | Regime | Wann verwenden |
|-----------|--------|----------------|
| vol_breakout | Breakout | Nach Konsolidierungsphasen, bei steigender Vol |
| mean_reversion_channel | Ranging | In Seitwärtsmärkten, bei stabilen Bändern |
| rsi_reversion | Ranging | Bei klaren Übertreibungen, Seitwärtstrend |

### Performance-Hinweise

- **Vol Breakout**: Funktioniert besser in volatilen Märkten mit klaren Trends
- **Mean Reversion**: Funktioniert besser in stabilen Seitwärtsmärkten
- **RSI Reversion**: Wilder-Smoothing reduziert Whipsaws, Trendfilter vermeidet Gegen-Trend-Trades

### Bekannte Einschränkungen

1. **Lookback-Requirements**: Alle Strategien benötigen Mindestanzahl an Bars für Warm-up
2. **State-Tracking**: RSI und Mean Reversion Channel tracken Position intern
3. **Vol-Filter**: Vol Breakout kann in sehr ruhigen Märkten wenig Signale generieren

---

## Nächste Schritte

1. **Backtests**: Systematische Backtests mit historischen Daten
2. **Regime Detection**: Integration mit Regime-Erkennung für automatische Strategie-Auswahl
3. **Parameter-Optimierung**: Hyperparameter-Sweeps für optimale Parameter
4. **Portfolio-Integration**: Kombination mehrerer Strategien im Portfolio

---

**Stand**: Phase 27 (Dezember 2024)
**Autor**: Peak_Trade Team
