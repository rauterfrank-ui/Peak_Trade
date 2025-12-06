# Phase 28: Regime Detection & Strategy Switching

## Übersicht

Phase 28 implementiert einen **Regime-Layer**, der Marktphasen erkennt und darauf basierend Strategien umschaltet oder gewichtet. Der Layer arbeitet ausschließlich im **Research/Backtest/Shadow-Kontext** und baut auf Phase 26 (Portfolio-Layer) und Phase 27 (Strategy-Research-Track) auf.

### Workflow

```
Data → RegimeDetector → StrategySwitchingPolicy → Strategies → Portfolio → Backtest → Stats
```

## Regime-Konzepte

### Regime-Labels

| Label      | Beschreibung                                    | Typische Strategien          |
|------------|------------------------------------------------|------------------------------|
| `breakout` | Hohe Volatilität, Range-Ausbrüche              | vol_breakout                 |
| `ranging`  | Seitwärts, niedrige Volatilität                | mean_reversion_channel, rsi_reversion |
| `trending` | Starke Trendphasen (positiv oder negativ)      | trend_following, ma_crossover |
| `unknown`  | Zu wenig Historie oder unklare Signale         | ma_crossover (Fallback)      |

### Regime-Erkennung

Der **VolatilityRegimeDetector** erkennt Regime basierend auf:

1. **ATR (Average True Range)**: Misst die Volatilität
2. **ATR-Perzentil**: Relative Volatilität im rollierenden Fenster
3. **MA-Slope**: Trend-Richtung und -Stärke

Logik:
- `breakout`: ATR-Perzentil > `vol_percentile_breakout` (z.B. 0.75)
- `ranging`: ATR-Perzentil < `vol_percentile_ranging` (z.B. 0.30)
- `trending`: Mittlere Vol + signifikanter MA-Slope
- `unknown`: Warmup-Phase (zu wenig Historie)

## Package-Struktur

```
src/regime/
├── __init__.py           # Public API
├── base.py               # Core Types (RegimeLabel, RegimeContext, Protocols)
├── config.py             # RegimeDetectorConfig, StrategySwitchingConfig
├── detectors.py          # VolatilityRegimeDetector, RangeCompressionRegimeDetector
└── switching.py          # SimpleRegimeMappingPolicy
```

## API-Referenz

### Core Types (`src/regime/base.py`)

```python
from src.regime import RegimeLabel, RegimeContext, StrategySwitchDecision

# RegimeLabel ist ein Literal-Typ
RegimeLabel = Literal["breakout", "ranging", "trending", "unknown"]

# RegimeContext für einzelne Regime-Entscheidungen
@dataclass
class RegimeContext:
    timestamp: pd.Timestamp
    window: pd.DataFrame      # Lokaler OHLCV-Ausschnitt
    symbol: str | None = None
    features: Dict[str, Any] | None = None

# Ergebnis einer Switching-Entscheidung
@dataclass
class StrategySwitchDecision:
    regime: RegimeLabel
    active_strategies: List[str]              # Strategy-Namen
    weights: Dict[str, float] | None = None   # Optionale Gewichte
```

### RegimeDetector

```python
from src.regime import make_regime_detector, RegimeDetectorConfig

# Config erstellen
config = RegimeDetectorConfig(
    enabled=True,
    detector_name="volatility_breakout",  # oder "range_compression"
    lookback_window=50,
    min_history_bars=100,
    vol_window=20,
    vol_percentile_breakout=0.75,
    vol_percentile_ranging=0.30,
)

# Detector erstellen
detector = make_regime_detector(config)

# Regime für komplette Serie berechnen
regimes: pd.Series = detector.detect_regimes(df)

# Oder für einzelnen Kontext
context = RegimeContext(timestamp=df.index[-1], window=df)
regime: RegimeLabel = detector.detect_regime(context)
```

### StrategySwitchingPolicy

```python
from src.regime import make_switching_policy, StrategySwitchingConfig

# Config erstellen
config = StrategySwitchingConfig(
    enabled=True,
    policy_name="simple_regime_mapping",
    regime_to_strategies={
        "breakout": ["vol_breakout"],
        "ranging": ["mean_reversion_channel", "rsi_reversion"],
        "trending": ["trend_following"],
        "unknown": ["ma_crossover"],
    },
    regime_to_weights={
        "ranging": {"mean_reversion_channel": 0.6, "rsi_reversion": 0.4},
    },
    default_strategies=["ma_crossover"],
)

# Policy erstellen
policy = make_switching_policy(config)

# Entscheidung treffen
available = ["vol_breakout", "mean_reversion_channel", "rsi_reversion"]
decision = policy.decide(regime="ranging", available_strategies=available)

print(decision.active_strategies)  # ['mean_reversion_channel', 'rsi_reversion']
print(decision.weights)            # {'mean_reversion_channel': 0.6, 'rsi_reversion': 0.4}
print(decision.primary_strategy)   # 'mean_reversion_channel'
```

## Konfiguration (`config.toml`)

### Regime Detection

```toml
[regime]
# Master-Schalter
enabled = false

# Detector-Typ: "volatility_breakout" oder "range_compression"
detector_name = "volatility_breakout"

# Allgemeine Parameter
lookback_window = 50       # Lookback für Regime-Berechnung
min_history_bars = 100     # Minimum Bars bevor Regime berechnet wird

# Volatility Detector Parameter
vol_window = 20                 # Fenster für ATR-Berechnung
vol_percentile_breakout = 0.75  # Perzentil-Schwelle für Breakout (0.0-1.0)
vol_percentile_ranging = 0.30   # Perzentil-Schwelle für Ranging (0.0-1.0)

# Trending Detection
trending_ma_window = 50         # MA-Fenster für Trend-Erkennung
trending_slope_threshold = 0.0002  # Slope-Schwelle für Trending
```

### Strategy Switching

```toml
[strategy_switching]
# Master-Schalter
enabled = false

# Policy-Typ: "simple_regime_mapping"
policy_name = "simple_regime_mapping"

# Fallback-Strategien
default_strategies = ["ma_crossover"]

# Mapping: Regime -> Strategien
[strategy_switching.regime_to_strategies]
breakout = ["vol_breakout"]
ranging = ["mean_reversion_channel", "rsi_reversion"]
trending = ["trend_following", "ma_crossover"]
unknown = ["ma_crossover"]

# Optionale Gewichte
[strategy_switching.regime_to_weights.ranging]
mean_reversion_channel = 0.6
rsi_reversion = 0.4
```

## Strategien und Regime-Metadaten

Die Strategien haben `regime`-Metadaten in ihrer `StrategyMetadata`:

| Strategie                  | Regime    |
|----------------------------|-----------|
| `VolBreakoutStrategy`      | breakout  |
| `MeanReversionChannelStrategy` | ranging |
| `RsiReversionStrategy`     | ranging   |
| `TrendFollowingStrategy`   | trending  |
| `MACrossoverStrategy`      | any       |

## Workflow-Beispiele

### Beispiel 1: Breakout-Regime

```python
# Hohe Volatilität erkannt
regime = "breakout"

# Policy entscheidet
decision = policy.decide(regime, available_strategies)
# -> active_strategies = ["vol_breakout"]

# VolBreakoutStrategy wird verwendet
# - Erkennt Range-Ausbrüche
# - Nutzt ATR für Entry-/Exit-Levels
```

### Beispiel 2: Ranging-Regime

```python
# Niedrige Volatilität, Seitwärtsbewegung
regime = "ranging"

# Policy entscheidet
decision = policy.decide(regime, available_strategies)
# -> active_strategies = ["mean_reversion_channel", "rsi_reversion"]
# -> weights = {"mean_reversion_channel": 0.6, "rsi_reversion": 0.4}

# Gewichtete Kombination von Mean-Reversion-Strategien
# - mean_reversion_channel: 60% Gewicht
# - rsi_reversion: 40% Gewicht
```

### Beispiel 3: Backtest mit Regime-Layer

```python
from src.regime import make_regime_detector, make_switching_policy

# 1. Detector und Policy erstellen
detector = make_regime_detector(detector_config)
policy = make_switching_policy(switching_config)

# 2. Regime vorab berechnen (effizient)
regimes = detector.detect_regimes(df)

# 3. Pro Bar: Strategie basierend auf Regime wählen
for i, row in df.iterrows():
    regime = regimes.loc[i]
    decision = policy.decide(regime, available_strategies)

    # Verwende decision.active_strategies für Signalgenerierung
    for strategy_name in decision.active_strategies:
        weight = decision.get_weight(strategy_name)
        # Signal generieren und gewichten
        ...
```

## Demo-Script

```bash
# Mit Regime-Layer aktiviert
python scripts/demo_regime_switching.py --use-regime-layer

# Ohne Regime-Layer (klassischer Modus)
python scripts/demo_regime_switching.py --no-regime-layer

# Mit mehr Bars
python scripts/demo_regime_switching.py --use-regime-layer --bars 1000
```

## Tests

```bash
# Alle Regime-Tests ausführen
pytest tests/test_regime*.py -v

# Einzelne Test-Dateien
pytest tests/test_regime_detection.py -v     # Detector-Tests
pytest tests/test_strategy_switching.py -v   # Switching-Tests
pytest tests/test_regime_integration.py -v   # Integration-Tests
```

## Abgrenzung

### Was Phase 28 MACHT

- Regime-Erkennung basierend auf Volatilität/Range
- Strategy-Switching basierend auf Regime-Labels
- Integration in Research/Backtest/Shadow-Kontext
- Non-breaking Defaults (`enabled = false`)

### Was Phase 28 NICHT MACHT

- Live-Trading mit Regime-Switching
- Automatische Live-Switches zwischen Strategien
- Änderungen am Live-Order-Flow
- Echtzeit-Regime-Erkennung für Live-Trading

## Nächste Schritte

Mögliche Erweiterungen für zukünftige Phasen:

1. **Weitere Detectors**: ADX-basiert, Trend-Strength, Momentum
2. **ML-basierte Regime-Erkennung**: Hidden Markov Models, etc.
3. **Regime-Prognose**: Vorhersage von Regime-Wechseln
4. **Backtest-Engine Integration**: Vollständige Integration in BacktestEngine
5. **Performance-Analyse**: Regime-spezifische Performance-Metriken
