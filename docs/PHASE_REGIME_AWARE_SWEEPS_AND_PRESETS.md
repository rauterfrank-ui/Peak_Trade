# Phase: Regime-Aware Portfolio Sweeps & Presets

**Datum:** 2024-12-XX  
**Status:** Implementiert  
**Bereich:** Research / Backtest / Shadow-Only

## Ziel dieser Phase

Auf Basis der Regime-Aware Portfolio-Strategien werden **vordefinierte Sweep-Presets** bereitgestellt, mit denen Regime-Aware Portfolios systematisch untersucht werden können.

**Outcome:**
- 3 klar definierte Sweep-Presets (Aggressiv, Konservativ, Vol-Metrik-Vergleich)
- Integration in bestehende Sweep-/Experiment-Infrastruktur
- CLI-Kommandos zum schnellen Starten von Sweeps
- Automatisierte Reports mit Kennzahlen

## Implementierung

### 1. Sweep-Preset-Funktionen (`src/experiments/regime_aware_portfolio_sweeps.py`)

Neues Modul mit vordefinierten Sweep-Funktionen:

- `get_regime_aware_portfolio_sweeps()`: Basis-Sweeps für Portfolio-Parameter
- `get_regime_aware_aggressive_sweeps()`: Aggressives Preset
- `get_regime_aware_conservative_sweeps()`: Konservatives Preset
- `get_regime_aware_volmetric_sweeps()`: Vol-Metrik-Vergleich Preset
- `get_regime_aware_combined_sweeps()`: Kombinierte Sweeps (Portfolio + Vol-Regime)

#### Parameter-Grids

Jede Funktion unterstützt Granularität `"coarse"`, `"medium"`, `"fine"`:

**Aggressives Preset (Medium):**
- `risk_on_scale`: [1.0] (volle Gewichte)
- `neutral_scale`: [0.4, 0.5, 0.6, 0.7, 0.8] (moderate Reduktion)
- `risk_off_scale`: [0.0, 0.05, 0.1, 0.15, 0.2] (minimale Aktivität)
- `signal_threshold`: [0.25, 0.3, 0.35]

**Konservatives Preset (Medium):**
- `risk_on_scale`: [1.0]
- `neutral_scale`: [0.2, 0.25, 0.3, 0.35, 0.4] (stark reduziert)
- `risk_off_scale`: [0.0] (komplett aus)
- `mode`: ["filter"] (Filter-Mode)
- `signal_threshold`: [0.2, 0.25, 0.3]

**Vol-Metrik-Vergleich (Medium):**
- `vol_metric`: ["atr", "std", "realized", "range"]
- `low_vol_threshold`: [0.4, 0.5, 0.6, 0.8]
- `high_vol_threshold`: [1.5, 2.0, 2.5]
- `vol_lookback`: [14, 20]

### 2. Vordefinierte Sweeps (`src/experiments/research_playground.py`)

Die Presets sind als vordefinierte Sweeps registriert:

- `regime_aware_portfolio_aggressive`: Breakout + RSI, aggressives Scaling
- `regime_aware_portfolio_conservative`: Breakout + MA, konservatives Filtering
- `regime_aware_portfolio_volmetric`: Vol-Metrik-Vergleich mit fixem Portfolio

### 3. TOML-Sweep-Configs (`config/sweeps/`)

Für einfache Nutzung wurden TOML-Configs erstellt:

- `config/sweeps/regime_aware_portfolio_aggressive.toml`
- `config/sweeps/regime_aware_portfolio_conservative.toml`
- `config/sweeps/regime_aware_portfolio_volmetric.toml`

Diese können direkt mit `scripts/run_strategy_sweep.py` verwendet werden.

## Verwendung

### CLI-Kommandos

#### Preset A – Aggressiv

```bash
# Vordefinierten Sweep ausführen
python scripts/run_strategy_sweep.py \
    --sweep-name regime_aware_portfolio_aggressive \
    --symbol BTC-EUR \
    --timeframe 1h \
    --start 2024-01-01 \
    --end 2024-12-01

# Mit TOML-Config
python scripts/run_strategy_sweep.py \
    --config config/sweeps/regime_aware_portfolio_aggressive.toml \
    --symbol BTC-EUR
```

#### Preset B – Konservativ

```bash
python scripts/run_strategy_sweep.py \
    --sweep-name regime_aware_portfolio_conservative \
    --symbol BTC-EUR \
    --timeframe 1h \
    --start 2024-01-01 \
    --end 2024-12-01
```

#### Preset C – Vol-Metrik-Vergleich

```bash
python scripts/run_strategy_sweep.py \
    --sweep-name regime_aware_portfolio_volmetric \
    --symbol BTC-EUR \
    --timeframe 1h
```

### Programmatisch

```python
from src.experiments.research_playground import get_predefined_sweep
from src.experiments import ExperimentRunner

# Sweep laden
sweep = get_predefined_sweep("regime_aware_portfolio_aggressive")

# Zu ExperimentConfig konvertieren
exp_config = sweep.to_experiment_config(
    start_date="2024-01-01",
    end_date="2024-12-01"
)

# Ausführen
runner = ExperimentRunner()
results = runner.run(exp_config)

# Top-5 nach Sharpe
best = results.get_best_by_metric("sharpe", top_n=5)
for result in best:
    print(f"Sharpe: {result.metrics['sharpe']:.2f}, Params: {result.params}")
```

### Granularität variieren

```python
from src.experiments.regime_aware_portfolio_sweeps import (
    get_regime_aware_aggressive_sweeps
)

# Coarse (weniger Kombinationen, schneller)
sweeps_coarse = get_regime_aware_aggressive_sweeps("coarse")

# Fine (mehr Kombinationen, langsamer)
sweeps_fine = get_regime_aware_aggressive_sweeps("fine")
```

## Preset-Beschreibungen

### Preset A – Aggressiv (Risk-On Fokus)

**Ziel:** Maximale Aktivität in Risk-On-Phasen, reduzierte Aktivität in anderen Regimes.

**Portfolio:**
- Komponenten: `breakout_basic` (60%) + `rsi_reversion` (40%)
- Mode: `"scale"` (kontinuierliche Skalierung)

**Parameter-Variationen:**
- `risk_on_scale`: 1.0 (volle Gewichte)
- `neutral_scale`: 0.4 - 0.8 (5 Varianten)
- `risk_off_scale`: 0.0 - 0.2 (5 Varianten)
- `signal_threshold`: 0.25, 0.3, 0.35

**Typische Fragestellung:**
- Welche Neutral/Risk-Off-Skalierung bietet beste Risk-Adjusted-Returns?
- Wie robust ist die Strategie bei verschiedenen Signal-Thresholds?

### Preset B – Konservativ (Kapitalerhalt)

**Ziel:** Kapitalerhalt durch strenge Regime-Filterung.

**Portfolio:**
- Komponenten: `breakout_basic` (50%) + `ma_crossover` (50%)
- Mode: `"filter"` (binäres An/Aus bei Risk-Off)

**Parameter-Variationen:**
- `risk_on_scale`: 1.0
- `neutral_scale`: 0.2 - 0.4 (5 Varianten)
- `risk_off_scale`: 0.0 (komplett aus)
- `signal_threshold`: 0.2, 0.25, 0.3

**Typische Fragestellung:**
- Wie viel Exposure in Neutral-Phasen ist optimal für Kapitalerhalt?
- Vergleich Filter-Mode vs. Scale-Mode (außerhalb dieses Presets).

### Preset C – Vol-Metrik-Vergleich

**Ziel:** Vergleich verschiedener Volatilitäts-Metriken für Regime-Detection.

**Portfolio (fix):**
- Komponenten: `breakout_basic` (50%) + `rsi_reversion` (50%)
- `risk_on_scale`: 1.0, `neutral_scale`: 0.5, `risk_off_scale`: 0.0
- Mode: `"scale"`

**Parameter-Variationen:**
- `vol_metric`: ATR, STD, REALIZED, RANGE (4 Varianten)
- `low_vol_threshold`: 0.4, 0.5, 0.6, 0.8 (4 Varianten)
- `high_vol_threshold`: 1.5, 2.0, 2.5 (3 Varianten)
- `vol_lookback`: 14, 20 (2 Varianten)

**Typische Fragestellung:**
- Welche Vol-Metrik liefert die beste Regime-Klassifikation?
- Wie sensitiv ist die Performance auf Vol-Thresholds?

## Ergebnis-Interpretation

### Wichtige Kennzahlen

Für jeden Sweep-Run werden folgende Metriken gesammelt:

- **Performance:**
  - `total_return`, `annualized_return` (CAGR)
  - `sharpe_ratio`
  - `max_drawdown`, `drawdown_duration`

- **Trading:**
  - `total_trades`, `win_rate`
  - `avg_trade_pnl`, `avg_win`, `avg_loss`

- **Exposure:**
  - `avg_position_size`, `max_exposure`
  - `time_in_market`

### Regime-spezifische Auswertung (Ausblick)

In späteren Phasen könnte die Auswertung erweitert werden um:

- Performance nur in Risk-On-Phasen
- Drawdown-Profile in High-Vol-Phasen
- Regime-Transition-Analyse

## Tests

Alle Sweep-Funktionen sind in `tests/test_regime_aware_portfolio_sweeps.py` getestet:

- Basis-Sweeps mit verschiedenen Granularitäten
- Preset-Sweeps enthalten erwartete Parameter
- Registry-Zugriff funktioniert
- Vordefinierte Sweeps sind registriert und valide
- Parameter-Kombinationen werden korrekt generiert

### Test-Ausführung

```bash
# Alle Regime-Aware Sweep-Tests
pytest tests/test_regime_aware_portfolio_sweeps.py -v

# Alle Experiment-Tests
pytest tests/test_experiments*.py -v
```

## Integration mit Reporting

### Automatisierte Reports

Die Sweeps integrieren sich nahtlos in die bestehende Reporting-Infrastruktur:

```bash
# Sweep ausführen und Report generieren
python scripts/run_strategy_sweep.py \
    --sweep-name regime_aware_portfolio_aggressive \
    --symbol BTC-EUR \
    --with-plots \
    --format both

# Report separat generieren
python scripts/generate_experiment_report.py \
    --experiment-dir reports/experiments/regime_aware_portfolio_aggressive_*
```

### Report-Inhalte

- **Performance-Heatmaps:** Scales vs. Sharpe/MaxDD
- **Parameter-Sensitivity:** Welche Parameter haben größten Impact?
- **Top-N-Konfigurationen:** Beste Ergebnisse nach verschiedenen Metriken
- **Regime-Analyse:** (optional) Performance je Regime

## Ordnerstruktur

Ergebnisse werden unter folgender Struktur gespeichert:

```
reports/experiments/
├── regime_aware_portfolio_aggressive_{id}_{timestamp}/
│   ├── results.csv
│   ├── results.parquet
│   ├── summary.json
│   └── report.html
├── regime_aware_portfolio_conservative_{id}_{timestamp}/
└── regime_aware_portfolio_volmetric_{id}_{timestamp}/
```

## Typische Workflows

### Workflow 1: Schneller Vergleich der Presets

```bash
# Alle drei Presets nacheinander ausführen
for preset in aggressive conservative volmetric; do
    python scripts/run_strategy_sweep.py \
        --sweep-name regime_aware_portfolio_${preset} \
        --symbol BTC-EUR \
        --timeframe 1h \
        --max-runs 50  # Limit für schnellen Test
done

# Ergebnisse vergleichen
python scripts/compare_sweep_results.py \
    --experiment-dirs reports/experiments/regime_aware_portfolio_*
```

### Workflow 2: Deep-Dive in Aggressives Preset

```bash
# Fine-Granularität für detaillierte Analyse
python scripts/run_strategy_sweep.py \
    --sweep-name regime_aware_portfolio_aggressive \
    --symbol BTC-EUR \
    --timeframe 1h \
    --start 2024-01-01 \
    --end 2024-12-01

# Top-10 nach Sharpe identifizieren
python scripts/analyze_sweep_results.py \
    --experiment-dir reports/experiments/regime_aware_portfolio_aggressive_* \
    --metric sharpe \
    --top-n 10
```

### Workflow 3: Multi-Symbol-Sweep

```bash
# Sweep über mehrere Symbole
for symbol in BTC-EUR ETH-EUR; do
    python scripts/run_strategy_sweep.py \
        --sweep-name regime_aware_portfolio_conservative \
        --symbol ${symbol} \
        --timeframe 1h
done
```

## Ausblick

### Mögliche Erweiterungen (spätere Phasen)

1. **Regime-spezifische Metriken:**
   - Performance nur in Risk-On-Phasen
   - Drawdown-Profile pro Regime

2. **Erweiterte Presets:**
   - Multi-Timeframe-Regime-Analyse
   - Adaptive Thresholds (historische Perzentile)

3. **Portfolio-Variationen:**
   - Sweeps über Komponenten-Gewichte
   - Alternative Komponenten-Kombinationen

4. **Automatisierte Optimierung:**
   - Walk-Forward-Optimization für Regime-Aware Portfolios
   - Monte-Carlo-Robustness-Analyse

## Änderungen

### Dateien

**Neu:**
- `src/experiments/regime_aware_portfolio_sweeps.py` - Sweep-Funktionen
- `config/sweeps/regime_aware_portfolio_aggressive.toml` - Aggressives Preset
- `config/sweeps/regime_aware_portfolio_conservative.toml` - Konservatives Preset
- `config/sweeps/regime_aware_portfolio_volmetric.toml` - Vol-Metrik-Vergleich
- `tests/test_regime_aware_portfolio_sweeps.py` - Tests
- `docs/PHASE_REGIME_AWARE_SWEEPS_AND_PRESETS.md` - Diese Dokumentation

**Erweitert:**
- `src/experiments/__init__.py` - Neue Sweep-Funktionen exportiert
- `src/experiments/research_playground.py` - Vordefinierte Sweeps registriert

## Zusammenfassung

Diese Phase stellt **Sweep-Presets für Regime-Aware Portfolios** bereit:

1. ✅ **3 vordefinierte Presets:** Aggressiv, Konservativ, Vol-Metrik-Vergleich
2. ✅ **Integration in Sweep-Infrastruktur:** Funktioniert mit bestehender CLI und Reports
3. ✅ **Parametrisierbare Granularität:** Coarse/Medium/Fine für verschiedene Use-Cases
4. ✅ **TOML-Configs:** Einfache Nutzung via Sweep-Skripte
5. ✅ **Tests & Doku:** Vollständig getestet und dokumentiert

**Wichtig:** Diese Implementierung ist **Research-/Backtest-/Shadow-Only**. Keine Änderungen am Live-/Testnet-/Execution-Code.

Die Presets können direkt für systematische Untersuchungen von Regime-Aware Portfolios verwendet werden und integrieren sich nahtlos in die bestehende Research-Pipeline.
