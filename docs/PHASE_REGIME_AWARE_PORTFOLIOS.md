# Phase: Regime-Aware Portfolio Strategy

**Datum:** 2024-12-XX  
**Status:** Implementiert  
**Bereich:** Research / Backtest / Shadow-Only

## Ziel dieser Phase

Implementierung einer **Regime-Aware Portfolio-Strategie**, die mehrere Sub-Strategien kombiniert und ihre Gewichte basierend auf Volatilitäts-Regime-Signalen skaliert.

Die Strategie nutzt:
- **Breakout-Strategie** (`breakout_basic`) und andere Sub-Strategien
- **Vol-Regime-Filter** (`vol_regime_basic`) für Regime-Klassifikation
- **Dynamische Gewichtung** je nach Regime (Risk-On / Neutral / Risk-Off)

## Implementierung

### 1. RegimeAwarePortfolioStrategy (`src/strategies/regime_aware_portfolio.py`)

Eine neue Strategy-Klasse, die von `BaseStrategy` erbt und mehrere Sub-Strategien kombiniert.

#### Konzept

1. **Sub-Strategien kombinieren:**
   - Lädt mehrere Sub-Strategien (z.B. `breakout_basic`, `rsi_reversion`)
   - Generiert Signale für jede Komponente
   - Kombiniert Signale mit Basisgewichten (gewichtetes Mittel)

2. **Regime-Skalierung:**
   - Lädt Regime-Signal aus Vol-Regime-Filter
   - Mappt Regime-Wert (1/0/-1) auf Skalierungsfaktor:
     - `1` (Risk-On) → `risk_on_scale` (z.B. 1.0)
     - `0` (Neutral) → `neutral_scale` (z.B. 0.5)
     - `-1` (Risk-Off) → `risk_off_scale` (z.B. 0.0)

3. **Finale Signale:**
   - Skaliert kombinierte Signale mit Regime-Faktor
   - Wendet Threshold an für Long/Short-Entscheidung

#### Parameter

- **`components`** (list[str]): Liste von Strategie-Namen (Config-Keys)
- **`base_weights`** (dict[str, float]): Basisgewichte pro Komponente
- **`regime_strategy`** (str): Name der Vol-Regime-Strategie (muss `regime_mode=True` haben)
- **`mode`** (str): Skalierungs-Modus
  - `"scale"`: Skaliert alle Gewichte je nach Regime
  - `"filter"`: Blockiert bei Risk-Off (alle Gewichte = 0)
- **`risk_on_scale`** (float, default: 1.0): Skalierungsfaktor für Risk-On
- **`neutral_scale`** (float, default: 0.5): Skalierungsfaktor für Neutral
- **`risk_off_scale`** (float, default: 0.0): Skalierungsfaktor für Risk-Off
- **`signal_threshold`** (float, default: 0.3): Schwelle für Long/Short-Entscheidung

#### Algorithmus

```python
# 1. Kombiniere Sub-Strategie-Signale
combined = sum(component_signal * base_weight for each component)

# 2. Hole Regime-Signal (1, 0, oder -1)
regime = regime_strategy.generate_signals(data)

# 3. Mappe Regime auf Scale
scale = {
    1: risk_on_scale,    # Risk-On
    0: neutral_scale,    # Neutral
    -1: risk_off_scale   # Risk-Off
}[regime]

# 4. Skaliere kombinierte Signale
scaled = combined * scale

# 5. Wende Threshold an
if scaled > threshold:
    signal = 1  # Long
elif scaled < -threshold:
    signal = -1  # Short
else:
    signal = 0  # Flat
```

#### Beispiel-Config

```toml
[portfolio.regime_aware_breakout_rsi]
type = "regime_aware_portfolio"
components = ["breakout_basic", "rsi_reversion"]
base_weights = { breakout_basic = 0.6, rsi_reversion = 0.4 }
regime_strategy = "vol_regime_basic"
mode = "scale"
risk_on_scale = 1.0
neutral_scale = 0.5
risk_off_scale = 0.0
signal_threshold = 0.3
```

## Verwendung

### Backtest mit Regime-Aware Portfolio

```bash
# Beispiel: Backtest mit Regime-Aware Portfolio
python scripts/research_cli.py backtest \
    --strategy regime_aware_portfolio \
    --config-section portfolio.regime_aware_breakout_rsi \
    --symbol BTC-EUR \
    --timeframe 1h \
    --start 2024-01-01 \
    --end 2024-12-01
```

### Programmatisch

```python
from src.strategies.regime_aware_portfolio import RegimeAwarePortfolioStrategy
from src.core.peak_config import load_config

config = load_config()
strategy = RegimeAwarePortfolioStrategy.from_config(
    config,
    section="portfolio.regime_aware_breakout_rsi"
)

signals = strategy.generate_signals(df)
```

## Tests

### Unit-Tests

Alle Features sind in `tests/test_regime_aware_portfolio.py` getestet:

- Basis-Initialisierung
- Gewichts-Normalisierung
- Regime-Scale-Mapping
- Risk-On / Neutral / Risk-Off Scaling
- Filter-Mode vs. Scale-Mode
- Multi-Komponenten-Kombination
- Integration mit Mock-Strategien

### Test-Ausführung

```bash
# Alle Regime-Aware Portfolio Tests
pytest tests/test_regime_aware_portfolio.py -v

# Alle Strategy-Tests
pytest tests/strategies/ -v
```

## Architektur

### Integration in Strategy-Layer

Die `RegimeAwarePortfolioStrategy` ist als normale `BaseStrategy` implementiert und kann:

- In Backtests verwendet werden (via `BacktestEngine`)
- In Sweeps und Experimenten verwendet werden
- Mit anderen Strategien kombiniert werden (z.B. in `CompositeStrategy`)

### Registry

Die Strategie ist in der Strategy-Registry registriert:

- **Key:** `regime_aware_portfolio`
- **Config-Section:** `portfolio.regime_aware_breakout_rsi` (oder ähnlich)
- **Beschreibung:** "Regime-Aware Portfolio Strategy (Breakout + RSI + Vol-Regime)"

## Beispiele

### Beispiel 1: Konservatives Portfolio

```toml
[portfolio.regime_aware_conservative]
type = "regime_aware_portfolio"
components = ["breakout_basic", "ma_crossover"]
base_weights = { breakout_basic = 0.5, ma_crossover = 0.5 }
regime_strategy = "vol_regime_basic"
mode = "filter"           # Filter-Mode: Risk-Off → Flat
risk_on_scale = 1.0
neutral_scale = 0.3       # Sehr reduziert bei Neutral
risk_off_scale = 0.0
signal_threshold = 0.25
```

**Verhalten:**
- Risk-On: Normale Gewichte (1.0)
- Neutral: Reduzierte Gewichte (0.3)
- Risk-Off: Keine Trades (0.0)

### Beispiel 2: Aggressives Portfolio

```toml
[portfolio.regime_aware_aggressive]
type = "regime_aware_portfolio"
components = ["breakout_basic", "rsi_reversion", "trend_following"]
base_weights = { breakout_basic = 0.4, rsi_reversion = 0.3, trend_following = 0.3 }
regime_strategy = "vol_regime_basic"
mode = "scale"
risk_on_scale = 1.0       # Volle Gewichte bei Risk-On
neutral_scale = 0.7       # Leicht reduziert bei Neutral
risk_off_scale = 0.2      # Minimales Trading auch bei Risk-Off
signal_threshold = 0.25
```

**Verhalten:**
- Risk-On: Volle Gewichte (1.0)
- Neutral: Leicht reduziert (0.7)
- Risk-Off: Minimales Trading (0.2)

## Ausblick

### Mögliche Erweiterungen (spätere Phasen)

1. **Regime-bewusste Position Sizing:**
   - Vol-basiertes Leverage je nach Regime
   - Dynamische Risk-Adjustment

2. **Multi-Regime-Portfolios:**
   - Verschiedene Strategien je Regime
   - Strategie-Switching basierend auf Regime

3. **Erweiterte Regime-Detection:**
   - Multi-Timeframe-Regime-Analyse
   - Trend-Regime + Vol-Regime Kombinationen

4. **Reporting-Integration:**
   - Regime-Heatmaps in Backtest-Reports
   - Equity-Curve pro Regime
   - Performance-Analyse je Regime

## Änderungen

### Dateien

**Neu:**
- `src/strategies/regime_aware_portfolio.py` - Haupt-Implementierung
- `tests/test_regime_aware_portfolio.py` - Tests
- `docs/PHASE_REGIME_AWARE_PORTFOLIOS.md` - Diese Dokumentation

**Erweitert:**
- `src/strategies/registry.py` - Neue Strategie registriert
- `config/config.toml` - Neue Config-Abschnitte

### Config-Einträge

Neue Config-Abschnitte in `config/config.toml`:

- `[portfolio.regime_aware_breakout_rsi]` - Standard-Regime-Aware Portfolio
- `[portfolio.regime_aware_conservative]` - Konservative Variante

## Zusammenfassung

Diese Phase implementiert eine **Regime-Aware Portfolio-Strategie**, die:

1. ✅ Mehrere Sub-Strategien kombiniert (z.B. Breakout + RSI)
2. ✅ Vol-Regime-Signale nutzt für Gewichts-Skalierung
3. ✅ Vollständig in Backtest-Engine und Research-Pipeline integriert ist
4. ✅ Getestet und dokumentiert ist

**Wichtig:** Diese Implementierung ist **Research-/Backtest-/Shadow-Only**. Keine Änderungen am Live-/Testnet-/Execution-Code.
