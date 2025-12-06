# Peak_Trade Regime-Analyse (Phase 19)

## Einführung

### Was ist Regime-Analyse?

Regime-Analyse ist eine Technik zur Charakterisierung von Marktphasen basierend auf statistischen Eigenschaften der Preisdaten. Sie hilft dabei:

- **Robustheit zu evaluieren**: Wie performt eine Strategie in unterschiedlichen Marktbedingungen?
- **Overfitting zu erkennen**: Funktioniert die Strategie nur in bestimmten Marktphasen?
- **Parameter-Auswahl zu verbessern**: Welche Parameter-Kombinationen sind über alle Regimes hinweg stabil?

### Warum ist das wichtig?

Eine Strategie, die nur in steigenden Märkten mit niedriger Volatilität funktioniert, ist in der Praxis wenig nützlich. Regime-Analyse hilft:

1. **Strategie-Charakterisierung**: Verstehen, unter welchen Bedingungen eine Strategie funktioniert
2. **Risiko-Management**: Erkennen, wann eine Strategie anfällig ist
3. **Portfolio-Konstruktion**: Strategien kombinieren, die in unterschiedlichen Regimes performen

---

## Regime-Definition in Peak_Trade

Peak_Trade klassifiziert Marktregimes in zwei Dimensionen:

### Volatilitäts-Regimes

Basiert auf annualisierter Rolling-Standardabweichung der Log-Returns:

| Regime | Beschreibung | Typische Werte (Krypto) |
|--------|--------------|-------------------------|
| `low_vol` | Niedrige Volatilität | < 30% annualisiert |
| `mid_vol` | Mittlere Volatilität | 30-60% annualisiert |
| `high_vol` | Hohe Volatilität | > 60% annualisiert |

**Berechnung:**
```
log_returns = log(price_t / price_{t-1})
rolling_vol = std(log_returns, window=20)
annualized_vol = rolling_vol * sqrt(365)
```

### Trend-Regimes

Basiert auf der relativen Differenz zwischen kurzem und langem Moving Average:

| Regime | Beschreibung | Bedingung |
|--------|--------------|-----------|
| `uptrend` | Aufwärtstrend | MA_short > MA_long + threshold |
| `sideways` | Seitwärtsbewegung | MA_short ≈ MA_long |
| `downtrend` | Abwärtstrend | MA_short < MA_long - threshold |

**Berechnung:**
```
ma_short = SMA(price, 20)
ma_long = SMA(price, 50)
delta = (ma_short - ma_long) / ma_long

uptrend    wenn delta > +0.02
downtrend  wenn delta < -0.02
sideways   sonst
```

### Kombinierte Regimes

Die Regimes werden kombiniert zu 9 möglichen Zuständen:
- `low_vol_uptrend`, `low_vol_sideways`, `low_vol_downtrend`
- `mid_vol_uptrend`, `mid_vol_sideways`, `mid_vol_downtrend`
- `high_vol_uptrend`, `high_vol_sideways`, `high_vol_downtrend`

---

## Konfiguration

Die Regime-Parameter werden in `config/regimes.toml` definiert:

```toml
[volatility]
lookback = 20                    # Rolling-Window (Bars)
low_threshold = 0.30             # Schwelle für low_vol
high_threshold = 0.60            # Schwelle für high_vol
annualization_factor = 365       # Für Annualisierung

[trend]
short_window = 20                # Kurzer MA
long_window = 50                 # Langer MA
slope_threshold = 0.02           # Schwelle für Trend-Erkennung
```

### Parameter-Empfehlungen

| Asset-Klasse | vol_low | vol_high | slope_threshold |
|--------------|---------|----------|-----------------|
| Krypto       | 0.30    | 0.60     | 0.02            |
| Aktien       | 0.10    | 0.25     | 0.01            |
| Forex        | 0.05    | 0.12     | 0.005           |

---

## Technische Umsetzung

### Module

**`src/analytics/regimes.py`**

Haupt-Modul mit:

| Funktion | Beschreibung |
|----------|--------------|
| `load_regime_config()` | Lädt Konfiguration aus TOML |
| `detect_regimes()` | Erkennt Regimes in Preisdaten |
| `analyze_regimes_from_equity()` | Analysiert Performance pro Regime |
| `analyze_experiment_regimes()` | High-Level-Analyse für Experimente |
| `compute_sweep_robustness()` | Robustheits-Metriken für Sweeps |

### Dataclasses

```python
@dataclass
class RegimeConfig:
    vol_lookback: int
    vol_low_threshold: float
    vol_high_threshold: float
    # ...

@dataclass
class RegimeStats:
    regime: str           # z.B. "low_vol_uptrend"
    weight: float         # Anteil an Gesamtzeit
    bar_count: int
    return_mean: float
    sharpe: Optional[float]
    max_drawdown: Optional[float]

@dataclass
class RegimeAnalysisResult:
    experiment_id: Optional[str]
    strategy_name: Optional[str]
    regimes: List[RegimeStats]
    overall_return: float
    overall_sharpe: Optional[float]
```

### CLI-Tool

**`scripts/analyze_regimes.py`**

```bash
# Subcommands
python scripts/analyze_regimes.py single    # Einzelnes Experiment
python scripts/analyze_regimes.py strategy  # Strategie-Analyse
python scripts/analyze_regimes.py sweep     # Sweep-Robustheit
```

---

## Quickstart & Beispiele

### Beispiel 1: Einzelnes Experiment analysieren

```bash
python scripts/analyze_regimes.py single \
    --id abc12345-1234-5678-abcd-1234567890ab \
    --verbose
```

**Beispiel-Ausgabe:**
```
==========================================================================================
  Peak_Trade – Regime-Analyse: Experiment abc12345-...
==========================================================================================

Run-Type:  backtest
Run-Name:  backtest_ma_crossover_20251204_103000
Strategy:  ma_crossover
Symbol:    BTC/EUR

--- ALLGEMEIN ---
  Experiment-ID:  abc12345-...
  Strategy:       ma_crossover
  Overall Return: 15.32%
  Overall Sharpe: 1.45

--- REGIME-VERTEILUNG ---
  low_vol_sideways          35.2%
  mid_vol_uptrend           28.5%
  high_vol_downtrend        18.3%
  mid_vol_sideways          10.0%
  low_vol_uptrend            8.0%

--- PERFORMANCE PRO REGIME ---
Regime                    Weight     Bars  Return_mean    Sharpe    MaxDD
-------------------------------------------------------------------------
low_vol_sideways           35.2%    1287      0.0012      0.85    -5.2%
mid_vol_uptrend            28.5%    1042      0.0035      2.10    -8.3%
high_vol_downtrend         18.3%     669     -0.0021     -0.45   -15.8%
mid_vol_sideways           10.0%     366      0.0008      0.42    -4.1%
low_vol_uptrend             8.0%     292      0.0045      2.85    -3.2%

--- ZUSAMMENFASSUNG ---
  Bestes Regime:      low_vol_uptrend (Sharpe: 2.85)
  Schlechtestes:      high_vol_downtrend (Sharpe: -0.45)
```

### Beispiel 2: Strategie-Analyse über mehrere Backtests

```bash
python scripts/analyze_regimes.py strategy \
    --strategy ma_crossover \
    --run-type backtest \
    --limit 20
```

**Beispiel-Ausgabe:**
```
==========================================================================================
  Peak_Trade – Regime-Analyse: Strategie 'ma_crossover'
==========================================================================================

Gefunden: 20 Experiment(s)

--- AGGREGIERTE REGIME-STATISTIKEN ---

Regime                    Count  Sharpe (mean)  Sharpe (std)  Sharpe > 0
------------------------------------------------------------------------
low_vol_uptrend              20           2.15          0.45      20/20
mid_vol_uptrend              20           1.45          0.62      18/20
low_vol_sideways             20           0.72          0.38      15/20
mid_vol_sideways             20           0.35          0.51      12/20
high_vol_downtrend           20          -0.28          0.82       8/20
```

### Beispiel 3: Sweep-Robustheits-Check

```bash
python scripts/analyze_regimes.py sweep \
    --sweep-name ma_crossover_opt_v1 \
    --metric sharpe \
    --top-n 20 \
    --export-csv out/regime_sweep.csv
```

**Beispiel-Ausgabe:**
```
==========================================================================================
  Peak_Trade – Regime-Analyse: Sweep 'ma_crossover_opt_v1'
==========================================================================================

Analysiere Top-20 Runs nach sharpe

--- SWEEP ROBUSTHEIT ---
  Sweep-Name:       ma_crossover_opt_v1
  Runs analysiert:  20
  Robustness Score: 72.5%
  Bestes Regime:    low_vol_uptrend
  Schlechtestes:    high_vol_downtrend

--- REGIME KONSISTENZ (Runs mit Sharpe > 0) ---
  low_vol_uptrend            20/20
  mid_vol_uptrend            18/20
  low_vol_sideways           15/20
  mid_vol_sideways           12/20
  high_vol_downtrend          4/20

--- TOP 3 RUNS DETAILS ---

  [1] Rank 1: sharpe=2.35
      Run-ID: 1234abcd...
      - low_vol_uptrend: Sharpe=3.12, Weight=25.0%
      - mid_vol_uptrend: Sharpe=2.45, Weight=30.0%
      - low_vol_sideways: Sharpe=1.20, Weight=20.0%
```

### Beispiel 4: Export für weitere Analyse

```bash
# CSV-Export
python scripts/analyze_regimes.py strategy \
    --strategy rsi_reversion \
    --export-csv out/rsi_regime_analysis.csv

# JSON-Export
python scripts/analyze_regimes.py single \
    --id abc12345-... \
    --export-json out/experiment_regime.json
```

---

## Best Practices

### Interpretation der Ergebnisse

1. **Robustness Score > 70%**: Strategie ist relativ robust über Regimes
2. **Einzelne Regime-Schwächen**: Akzeptabel wenn das Regime selten auftritt (Weight < 15%)
3. **Konsistente Underperformance**: Regime mit Sharpe < 0 in > 50% der Runs sollte untersucht werden

### Zusammenspiel mit anderen Phasen

**Phase 20 (Sweeps)**:
```bash
# Erst Sweep laufen lassen
python scripts/run_sweep_strategy.py --strategy ma_crossover

# Dann Robustheits-Check
python scripts/analyze_regimes.py sweep --sweep-name ma_crossover_opt_v1
```

**Phase 22 (Explorer)**:
```bash
# Top-Runs nach Sharpe finden
python scripts/experiments_explorer.py top --metric sharpe --top-n 10

# Dann einzeln analysieren
python scripts/analyze_regimes.py single --id <run-id>
```

**Phase 21 (Reporting v2)**:
Regime-Analyse-Ergebnisse können in Reports eingebunden werden:
```python
from src.analytics.regimes import analyze_experiment_regimes
result = analyze_experiment_regimes(prices, equity)
# result.to_dict() für JSON-Export
```

### Typische Analyse-Workflow

1. **Initial-Check**: Backtest laufen lassen und Overall-Sharpe prüfen
2. **Regime-Breakdown**: `analyze_regimes.py single` für detaillierte Analyse
3. **Parameter-Robustheit**: Sweep durchführen und mit `analyze_regimes.py sweep` prüfen
4. **Strategie-Vergleich**: Mehrere Strategien mit `analyze_regimes.py strategy` vergleichen
5. **Portfolio-Design**: Strategien kombinieren, die in unterschiedlichen Regimes performen

---

## Safety-Hinweise

Phase 19 ist **rein analytisch**:

- Nur Lesen aus Registry und Backtest-Daten
- Keine Änderungen an `TradingEnvironment`
- Keine Änderungen an `SafetyGuard`
- Keine Live-/Testnet-Aktivierung
- Keine Order-/Execution-Pfade

Das Regime-Analyse-Modul dient ausschließlich der Auswertung und Charakterisierung von Strategien.

---

## API-Referenz

### load_regime_config

```python
def load_regime_config(path: Optional[Path] = None) -> RegimeConfig:
    """
    Lädt Regime-Konfiguration aus TOML-Datei.

    Args:
        path: Pfad zur Config (default: config/regimes.toml)

    Returns:
        RegimeConfig mit geladenen Parametern
    """
```

### detect_regimes

```python
def detect_regimes(
    prices: pd.DataFrame,
    cfg: RegimeConfig,
    price_col: str = "close",
) -> pd.DataFrame:
    """
    Erkennt Marktregimes in einer Preiszeitreihe.

    Args:
        prices: DataFrame mit DatetimeIndex und Preis-Spalte
        cfg: RegimeConfig mit Parametern
        price_col: Name der Preis-Spalte

    Returns:
        DataFrame mit zusätzlichen Spalten:
        - 'vol_regime', 'trend_regime', 'regime'
        - 'volatility', 'ma_delta'
    """
```

### analyze_regimes_from_equity

```python
def analyze_regimes_from_equity(
    equity: pd.Series,
    regimes: pd.DataFrame,
    annualization_factor: int = 365,
) -> List[RegimeStats]:
    """
    Analysiert Performance pro Regime basierend auf Equity-Curve.

    Args:
        equity: Equity-Curve mit DatetimeIndex
        regimes: DataFrame mit 'regime' Spalte
        annualization_factor: Faktor für Sharpe-Annualisierung

    Returns:
        Liste von RegimeStats für jedes Regime
    """
```

### analyze_experiment_regimes

```python
def analyze_experiment_regimes(
    prices: pd.DataFrame,
    equity: pd.Series,
    cfg: Optional[RegimeConfig] = None,
    experiment_id: Optional[str] = None,
    strategy_name: Optional[str] = None,
) -> RegimeAnalysisResult:
    """
    High-Level Regime-Analyse für ein Experiment.

    Args:
        prices: OHLCV-DataFrame
        equity: Equity-Curve des Backtests
        cfg: RegimeConfig (default: aus config/regimes.toml)
        experiment_id: Optionale Experiment-ID
        strategy_name: Optionaler Strategie-Name

    Returns:
        RegimeAnalysisResult mit vollständiger Analyse
    """
```

---

## Changelog

- **Phase 19** (2025-12): Initial-Implementation
  - Regime-Erkennung (Volatilität + Trend)
  - Performance-Analyse pro Regime
  - CLI-Tool für Einzel-, Strategie- und Sweep-Analyse
  - Integration mit Explorer (Phase 22)
