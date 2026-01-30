# Phase: Strategy Library Expansion (Breakout & Vol-Regime)

**Datum:** 2024-12-XX  
**Status:** Implementiert  
**Bereich:** Research / Backtest / Shadow-Only

## Ziel dieser Phase

Erweiterung der Strategy-Library um zwei klar definierte Bausteine:

1. **Breakout-Strategie** (Trend-/Momentum-Fokus)
   - Klassischer Donchian-/High-Low-Breakout auf Basis von N-Bars
   - Optionaler ATR-/Volatilitäts-Filter zur Vermeidung von „Noise-Breakouts“

2. **Volatilitäts-Regime-Filter** (Risk-On/Risk-Off-Signal)
   - Eine „Meta-Strategie“/Signalquelle, die Regime („Low Vol“, „High Vol“) klassifiziert
   - Dient als Filter für andere Strategien (z. B. nur handeln in bestimmten Regimes)

## Implementierung

### 1. Breakout-Strategie (`src/strategies/breakout.py`)

Die bestehende Breakout-Strategie wurde um folgende Features erweitert:

#### Neue Parameter

- **`lookback_high`** (int, optional): Separates Lookback-Fenster für Long-Breakout-Level
- **`lookback_low`** (int, optional): Separates Lookback-Fenster für Short-Breakout-Level
  - Falls nicht gesetzt, wird `lookback_breakout` verwendet (rückwärtskompatibel)

- **`atr_lookback`** (int, default: 14): ATR-Fenster für Filter-Berechnung
- **`atr_multiplier`** (float, optional): Mindest-ATR-Level für validen Breakout
  - Breakout nur valid, wenn: `ATR >= atr_multiplier * ATR-Baseline`
- **`use_atr_filter`** (bool, default: False): ATR-Filter aktivieren/deaktivieren

- **`exit_on_opposite_breakout`** (bool, default: True): Exit bei gegenteiligem Breakout
  - Bei Long-Position: Exit wenn Short-Breakout erkannt wird
  - Bei Short-Position: Exit wenn Long-Breakout erkannt wird

- **`risk_mode`** (str, default: "symmetric"): Trading-Modus
  - `"symmetric"`: Long und Short erlaubt
  - `"long_only"`: Nur Long-Trades
  - `"short_only"`: Nur Short-Trades
  - Legacy: Parameter `side` wird automatisch zu `risk_mode` gemappt

#### Logik

**Long-Entry:**
- `Close > rolling_max(high, lookback_high)`
- Optional: Aktuelle ATR >= `atr_multiplier * ATR-Baseline` (wenn `use_atr_filter=True`)

**Short-Entry:**
- `Close < rolling_min(low, lookback_low)`
- Optional: ATR-Filter (analog zu Long)

**Exit:**
- Stop-Loss / Take-Profit / Trailing-Stop (bestehende Features)
- Bei `exit_on_opposite_breakout=True`: Exit bei gegenteiligem Breakout

#### Beispiel-Config

```toml
[strategy.breakout_basic]
type = "breakout"
lookback_high = 20
lookback_low = 20
atr_lookback = 14
atr_multiplier = 1.0
use_atr_filter = true
exit_on_opposite_breakout = true
risk_mode = "symmetric"
```

### 2. Vol-Regime-Filter (`src/strategies/vol_regime_filter.py`)

Die bestehende Vol-Regime-Filter-Strategie wurde um einfache Threshold-basierte Regime-Klassifikation erweitert.

#### Neue Parameter

- **`vol_metric`** / **`vol_method`** (str, default: "atr"): Volatilitäts-Metrik
  - `"atr"`: Average True Range
  - `"std"`: Standard-Abweichung der Returns
  - `"realized"`: Annualisierte Realized Volatility
  - `"range"`: High-Low Range

- **`low_vol_threshold`** (float, optional): Low-Vol-Schwellwert
  - Wenn `Vol < low_vol_threshold` → Regime = **1** (Risk-On / Low-Vol)

- **`high_vol_threshold`** (float, optional): High-Vol-Schwellwert
  - Wenn `Vol > high_vol_threshold` → Regime = **-1** (Risk-Off / High-Vol)

- **`min_bars`** (int, default: 30): Minimum an Bars vor Klassifikation
  - Vor `min_bars`: Regime = 0 (Neutral)

- **`regime_mode`** (bool, default: False): Aktiviert Regime-Modus
  - `False`: Filter-Mode (1=Trading erlaubt, 0=blockiert)
  - `True`: Regime-Mode (1=Low-Vol, -1=High-Vol, 0=Neutral)
  - Auto-Detection: Wenn `low_vol_threshold` oder `high_vol_threshold` gesetzt sind, wird `regime_mode=True` automatisch aktiviert

#### Logik

**Regime-Klassifikation:**
1. Berechne Volatilität über `vol_lookback` (alias: `vol_window`)
2. Wenn `Vol < low_vol_threshold` → Regime = **1** (Risk-On)
3. Wenn `Vol > high_vol_threshold` → Regime = **-1** (Risk-Off)
4. Dazwischen oder vor `min_bars` → Regime = **0** (Neutral)

**Filter-Mode (bestehend):**
- Gibt weiterhin 1/0 zurück (Trading erlaubt/blockiert)
- Kompatibel mit bestehender Verwendung

**Regime-Mode (neu):**
- Gibt 1/-1/0 zurück (Low-Vol/High-Vol/Neutral)
- Kann als eigenständige Strategie verwendet werden
- Kann in späteren Phasen als Filter/Overlay für andere Strategien genutzt werden

#### Beispiel-Config

```toml
[strategy.vol_regime_basic]
type = "vol_regime_filter"
vol_lookback = 20
vol_metric = "atr"
low_vol_threshold = 0.5
high_vol_threshold = 2.0
min_bars = 30
regime_mode = true
```

## Verwendung

### Backtest mit Breakout-Strategie

```bash
# Beispiel: Backtest mit erweiterter Breakout-Strategie
python3 scripts/research_cli.py backtest \
    --strategy breakout_basic \
    --symbol BTC-EUR \
    --timeframe 1h \
    --start 2024-01-01 \
    --end 2024-12-01
```

### Backtest mit Vol-Regime-Filter

```bash
# Beispiel: Regime-Signale analysieren
python3 scripts/research_cli.py backtest \
    --strategy vol_regime_basic \
    --symbol BTC-EUR \
    --timeframe 1h \
    --start 2024-01-01 \
    --end 2024-12-01
```

### Sweep-Parameter

```toml
# config/sweeps/breakout_sweep.toml
[sweep.breakout_atr_filter]
strategy = "breakout_basic"
params = {
    lookback_high = [15, 20, 25],
    lookback_low = [15, 20, 25],
    atr_multiplier = [0.8, 1.0, 1.2],
    use_atr_filter = [true, false]
}
```

## Tests

### Breakout-Tests

Alle neuen Features sind in `tests/test_strategy_breakout.py` getestet:

- Separate Lookbacks für Long/Short
- ATR-Filter verhindert Noise-Breakouts
- Risk-Modes (long_only, short_only, symmetric)
- Exit bei gegenteiligem Breakout
- Legacy-Kompatibilität (`side` → `risk_mode`)

### Vol-Regime-Filter-Tests

Alle neuen Features sind in `tests/test_strategy_vol_regime_filter.py` getestet:

- Low-Vol-Threshold erkennt Risk-On-Regime
- High-Vol-Threshold erkennt Risk-Off-Regime
- Regime-Klassifikation (1/-1/0)
- `min_bars` wird respektiert
- Range-Volatilitäts-Methode
- Unterschied zwischen Regime-Mode und Filter-Mode

### Test-Ausführung

```bash
# Alle Breakout-Tests
python3 -m pytest tests/test_strategy_breakout.py -v

# Alle Vol-Regime-Filter-Tests
python3 -m pytest tests/test_strategy_vol_regime_filter.py -v

# Alle Strategy-Tests
python3 -m pytest tests/strategies/ -v
```

## Rückwärtskompatibilität

### Breakout-Strategie

- Bestehende Configs mit `side` funktionieren weiterhin
- `side="long"` → automatisch `risk_mode="long_only"`
- `side="short"` → automatisch `risk_mode="short_only"`
- `side="both"` → automatisch `risk_mode="symmetric"`
- `lookback_breakout` wird weiterhin verwendet, wenn `lookback_high`/`lookback_low` nicht gesetzt sind

### Vol-Regime-Filter

- Bestehende Filter-Configs funktionieren weiterhin
- Perzentil-basierte Filter bleiben unverändert
- Neue Threshold-Parameter sind optional
- `regime_mode=False` (Standard) gibt weiterhin Filter-Signale (1/0) zurück

## Ausblick

### Kombination mit anderen Strategien

Der Vol-Regime-Filter kann in späteren Phasen als Filter/Overlay für andere Strategien verwendet werden:

```python
# Beispiel (zukünftig):
from src.strategies.breakout import BreakoutStrategy
from src.strategies.vol_regime_filter import VolRegimeFilter

breakout = BreakoutStrategy(lookback_breakout=20)
vol_filter = VolRegimeFilter(
    low_vol_threshold=0.5,
    high_vol_threshold=2.0,
    regime_mode=True
)

raw_signals = breakout.generate_signals(df)
regime = vol_filter.generate_signals(df)

# Nur handeln wenn Regime = 1 (Low-Vol/Risk-On)
filtered_signals = raw_signals * (regime == 1).astype(int)
```

### Portfolio-Integration

- Vol-Regime-Filter als Meta-Signalquelle in Portfolio-Layer
- Dynamische Regime-Erkennung mit automatischer Strategie-Auswahl
- Regime-basierte Risikoanpassung

### Weitere Erweiterungen

- Adaptive Thresholds (z. B. basierend auf historischen Perzentilen)
- Multi-Timeframe-Regime-Analyse
- Regime-Transition-Detection (Frühwarnung bei Regimewechsel)

## Änderungen

### Dateien

**Erweitert:**
- `src/strategies/breakout.py` - Neue Parameter und ATR-Filter-Logik
- `src/strategies/vol_regime_filter.py` - Threshold-basierte Regime-Klassifikation
- `config/config.toml` - Neue Config-Abschnitte
- `tests/test_strategy_breakout.py` - Tests für neue Features
- `tests/test_strategy_vol_regime_filter.py` - Tests für neue Features

**Neu:**
- `docs/PHASE_STRATEGY_EXPANSION_BREAKOUT_VOL_REGIME.md` - Diese Dokumentation

### Config-Einträge

Neue Config-Abschnitte in `config/config.toml`:

- `[strategy.breakout_basic]` - Erweiterte Breakout-Strategie mit ATR-Filter
- `[strategy.vol_regime_basic]` - Threshold-basierter Vol-Regime-Filter

Bestehende Einträge wurden erweitert:
- `[strategy.breakout]` - Unterstützt nun neue Parameter
- `[strategy.vol_regime_filter]` - Unterstützt nun Threshold-Parameter

## Zusammenfassung

Diese Phase erweitert die Strategy-Library um zwei mächtige Bausteine:

1. **Breakout-Strategie** mit ATR-Filter und erweiterten Exit-Optionen
2. **Vol-Regime-Filter** mit einfacher Threshold-basierter Klassifikation

Beide Strategien sind vollständig kompatibel mit der bestehenden Backtest-Engine und Research-Pipeline. Sie können in Sweeps, Backtests und Reports verwendet werden.

**Wichtig:** Diese Erweiterungen sind **Research-/Backtest-/Shadow-Only**. Keine Änderungen am Live-/Testnet-/Execution-Code.
