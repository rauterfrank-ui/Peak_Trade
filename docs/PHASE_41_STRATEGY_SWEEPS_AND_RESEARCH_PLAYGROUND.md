# Phase 41 – Strategy-Sweeps & Research-Playground

## Implementation Status

Phase 41 ist **vollständig implementiert und getestet**:

- ✅ Strategy-Sweeps sind implementiert und funktionsfähig
- ✅ `rsi_reversion_basic` ist als Beispiel-Sweep lauffähig (27 Kombinationen)
- ✅ Sweep-Ergebnisse werden unter `reports/experiments/` abgelegt (Dateinamen enthalten Sweep-Namen)
- ✅ Reports werden unter `reports/sweeps/` abgelegt (Markdown + HTML)
- ✅ Alle Tests sind grün (~1495 passed, 4 skipped)

**End-to-End Workflow funktioniert stabil** – Sweep-Ausführung → Ergebnis-Speicherung → Report-Generierung.

---

## Zusammenfassung

Phase 41 erweitert Peak_Trade um einen **Research-Playground** für systematisches Strategy-Testing:

- **Parameter-Sweeps** mit Constraint-Filterung
- **Vordefinierte Sweep-Definitionen** für alle Strategien
- **Portfolio-Sweeps** für Composite-Strategien
- **CLI-Scripts** für Batch-Execution und Reporting
- **Aggregations-Reports** mit Rankings und Visualisierungen

---

## Neue Komponenten

### 1. Research-Playground-Modul

**Datei:** `src/experiments/research_playground.py`

Zentrale Schnittstelle für Strategy-Sweeps mit:

- `StrategySweepConfig`: Erweiterte Sweep-Definition mit Constraints
- `ParamConstraint`: Definiert Bedingungen zwischen Parametern
- Vordefinierte Sweeps für alle Strategien
- Batch-Execution-Helpers

```python
from src.experiments import (
    StrategySweepConfig,
    get_predefined_sweep,
    list_predefined_sweeps,
)

# Vordefinierte Sweeps nutzen
sweep = get_predefined_sweep("rsi_reversion_basic")
combos = sweep.generate_param_combinations()
print(f"{sweep.num_combinations} gültige Kombinationen")

# Eigene Sweeps definieren
custom = StrategySweepConfig(
    name="my_sweep",
    strategy_name="ma_crossover",
    param_grid={
        "fast_period": [5, 10, 20],
        "slow_period": [50, 100, 200],
    },
    constraints=[("fast_period", "<", "slow_period")],
)
```

### 2. Erweiterte Strategy-Sweeps

**Datei:** `src/experiments/strategy_sweeps.py`

Neue Sweep-Definitionen für Phase 41:

- `get_breakout_sweeps()`: Breakout-Strategie mit SL/TP/Trailing
- `get_vol_regime_filter_sweeps()`: Volatilitäts-Filter-Parameter

```python
from src.experiments import get_breakout_sweeps, get_vol_regime_filter_sweeps

# Breakout mit Stop-Loss und Take-Profit
breakout_sweeps = get_breakout_sweeps("medium", include_sl_tp=True)

# Vol Regime Filter
vol_sweeps = get_vol_regime_filter_sweeps("medium", include_percentile=True)
```

### 3. CLI-Scripts

#### run_strategy_sweep.py

**Datei:** `scripts/run_strategy_sweep.py`

```bash
# Vordefinierte Sweeps auflisten
python scripts/run_strategy_sweep.py --list-sweeps

# Sweep ausführen
python scripts/run_strategy_sweep.py --sweep-name rsi_reversion_basic

# Mit Optionen
python scripts/run_strategy_sweep.py \
    --sweep-name breakout_basic \
    --symbol BTC/EUR \
    --start 2024-01-01 \
    --end 2024-06-01 \
    --max-runs 50

# Dry-Run (nur Kombinationen anzeigen)
python scripts/run_strategy_sweep.py --sweep-name ma_crossover_fine --dry-run

# Automatischer Sweep für Strategie
python scripts/run_strategy_sweep.py --strategy ma_crossover --granularity medium
```

#### generate_strategy_sweep_report.py

**Datei:** `scripts/generate_strategy_sweep_report.py`

```bash
# Report generieren
python scripts/generate_strategy_sweep_report.py --sweep-name rsi_reversion_basic

# Mit Heatmap-Parametern
python scripts/generate_strategy_sweep_report.py \
    --sweep-name breakout_basic \
    --heatmap-params lookback_breakout stop_loss_pct

# Aus Datei
python scripts/generate_strategy_sweep_report.py \
    --input reports/experiments/my_sweep_results.csv
```

---

## Vordefinierte Sweeps

### MA Crossover

| Name | Kombinationen | Beschreibung |
|------|--------------|--------------|
| `ma_crossover_basic` | ~9 | Standard-Fenster (5/10/20 × 50/100/200) |
| `ma_crossover_fine` | ~48 | Fine-grained mit mehr Varianten |

### RSI Reversion

| Name | Kombinationen | Beschreibung |
|------|--------------|--------------|
| `rsi_reversion_basic` | 27 | RSI 7/14/21, Levels 20-30/70-80 |
| `rsi_reversion_aggressive` | 36 | Engere RSI, weitere Levels |
| `rsi_reversion_fine` | ~150 | Umfassender Sweep |

### Breakout

| Name | Kombinationen | Beschreibung |
|------|--------------|--------------|
| `breakout_basic` | 9 | Lookback + Stop-Loss |
| `breakout_with_tp` | ~48 | Mit Take-Profit |
| `breakout_trailing` | 12 | Mit Trailing-Stop |
| `breakout_fine` | ~500 | Umfassend mit allen Features |

### Vol Regime Filter

| Name | Kombinationen | Beschreibung |
|------|--------------|--------------|
| `vol_regime_percentile` | ~36 | Perzentil-basierter Filter |
| `vol_regime_atr` | 18 | ATR/STD-Varianten |

### Portfolio/Composite

| Name | Kombinationen | Beschreibung |
|------|--------------|--------------|
| `portfolio_2strat_weights` | 5 | 2-Strategy Weight-Sweep |
| `portfolio_3strat_equal` | 12 | 3-Strategy, verschiedene Aggregationen |
| `portfolio_phase40_v1` | 4 | Phase 40 Multi-Strategy |

---

## Constraint-System

Das Constraint-System filtert ungültige Parameter-Kombinationen automatisch:

```python
# Constraint: fast_period muss kleiner als slow_period sein
sweep = StrategySweepConfig(
    name="constrained",
    strategy_name="ma_crossover",
    param_grid={
        "fast_period": [5, 20, 50],
        "slow_period": [10, 50, 100],
    },
    constraints=[("fast_period", "<", "slow_period")],
)

# Ohne Constraint: 3 × 3 = 9 Kombinationen
# Mit Constraint: nur valide Kombinationen (z.B. 6)
print(f"Raw: {sweep.num_raw_combinations}")  # 9
print(f"Valid: {sweep.num_combinations}")     # 6
```

### Unterstützte Operatoren

| Operator | Beschreibung | Beispiel |
|----------|--------------|----------|
| `<` | Kleiner als | `("fast", "<", "slow")` |
| `>` | Größer als | `("high", ">", "low")` |
| `<=` | Kleiner gleich | `("exit", "<=", "entry")` |
| `>=` | Größer gleich | `("period", ">=", 5)` |
| `==` | Gleich | `("method", "==", "atr")` |
| `!=` | Ungleich | `("side", "!=", "short")` |

---

## Report-Output

Reports werden standardmäßig unter `reports/sweeps/` gespeichert:

```
reports/sweeps/
├── rsi_reversion_basic_report_20241206_143022.md
├── images/
│   ├── heatmap.png
│   ├── metric_distribution.png
│   └── param_vs_metric.png
```

### Report-Inhalt

1. **Overview**: Runs, Parameter, Metriken
2. **Best Parameters**: Optimale Konfiguration
3. **Top N Runs**: Ranking nach Sharpe/Return
4. **Metric Statistics**: Min/Max/Mean/Std
5. **Visualizations**: Heatmaps, Distributions
6. **Correlations**: Parameter-Metrik-Korrelationen
7. **Recommendations**: Empfehlungen mit Robustness-Check

---

## How-To: Sweep & Report ausführen

### Schritt-für-Schritt Anleitung

**1. Virtual Environment aktivieren**

```bash
cd ~/Peak_Trade
source .venv/bin/activate
```

**2. Sweep ausführen**

```bash
# Beispiel: rsi_reversion_basic mit max. 5 Runs (für schnellen Test)
python scripts/run_strategy_sweep.py \
  --sweep-name rsi_reversion_basic \
  --config config/config.toml \
  --max-runs 5  # Optional: Limit für schnellen Test

# Vollständiger Sweep (alle Kombinationen)
python scripts/run_strategy_sweep.py \
  --sweep-name rsi_reversion_basic \
  --config config/config.toml

# Mit Zeitraum-Filter
python scripts/run_strategy_sweep.py \
  --sweep-name breakout_basic \
  --start 2024-01-01 \
  --end 2024-12-01
```

**Erwartete Ausgabe:**
- Sweep läuft durch ohne Exceptions
- Erfolgreiche Runs werden angezeigt (z.B. "27 erfolgreich, 0 fehlgeschlagen")
- Ergebnisse werden gespeichert unter `reports/experiments/`
- Dateinamen enthalten den Sweep-Namen: `{sweep_name}_{experiment_id}_{timestamp}.csv`

**3. Report generieren**

```bash
# Markdown + HTML Report
python scripts/generate_strategy_sweep_report.py \
  --sweep-name rsi_reversion_basic \
  --format both

# Nur Markdown
python scripts/generate_strategy_sweep_report.py \
  --sweep-name rsi_reversion_basic \
  --format markdown
```

**Erwartete Ausgabe:**
- Kein Fehler "Keine Ergebnisse gefunden"
- Report-Dateien werden erzeugt:
  - `reports/sweeps/{sweep_name}_report_{timestamp}.md`
  - `reports/sweeps/{sweep_name}_report_{timestamp}.html` (falls `--format both`)
- Report enthält Tabelle mit Runs (Parameter + Kennzahlen)

**4. Ergebnisse finden**

- **Sweep-Ergebnisse**: `reports/experiments/{sweep_name}_*.csv` (oder `.parquet`)
- **Reports**: `reports/sweeps/{sweep_name}_report_*.md` (oder `.html`)
- **Visualisierungen**: `reports/sweeps/images/` (falls Heatmaps/Plots generiert wurden)

**5. Ergebnisse analysieren**

- Beste Parameter aus Report übernehmen
- Robustness prüfen (Varianz in Top-10)
- Out-of-Sample validieren

---

## Workflow (Programmatisch)

### 1. Sweep definieren oder laden

```python
# Option A: Vordefiniert
sweep = get_predefined_sweep("breakout_basic")

# Option B: Custom
sweep = StrategySweepConfig(
    name="custom_breakout",
    strategy_name="breakout",
    param_grid={
        "lookback_breakout": [15, 20, 30],
        "stop_loss_pct": [0.02, 0.03],
        "take_profit_pct": [0.05, 0.08],
    },
)
```

### 2. Sweep programmatisch ausführen

```python
from src.experiments import run_sweep_batch

result = run_sweep_batch(
    sweep_config=sweep,
    start_date="2024-01-01",
    end_date="2024-12-01",
    max_runs=50,
)
```

---

## API-Referenz

### StrategySweepConfig

```python
@dataclass
class StrategySweepConfig:
    name: str                                    # Sweep-Name
    strategy_name: str                           # Strategie aus Registry
    param_grid: Dict[str, List[Any]]            # Parameter → Werte
    constraints: List[ParamConstraint | Tuple]  # Filter-Bedingungen
    base_params: Dict[str, Any]                 # Feste Parameter
    description: Optional[str]                  # Beschreibung
    tags: List[str]                             # Kategorisierung
    symbols: List[str]                          # Trading-Symbole
    timeframe: str                              # Zeitrahmen
    portfolio_config: Optional[Dict]            # Portfolio-Optionen

    # Methoden
    def generate_param_combinations() -> List[Dict[str, Any]]
    def to_experiment_config(...) -> ExperimentConfig
    def to_dict() -> Dict[str, Any]

    # Properties
    @property
    def num_combinations -> int     # Nach Constraint-Filter
    @property
    def num_raw_combinations -> int # Vor Filter
```

### Registry-Funktionen

```python
# Sweeps abrufen
get_predefined_sweep(name: str) -> StrategySweepConfig
list_predefined_sweeps() -> List[str]
get_all_predefined_sweeps() -> Dict[str, StrategySweepConfig]

# Filtern
get_sweeps_for_strategy(strategy_name: str) -> List[StrategySweepConfig]
get_sweeps_by_tag(tag: str) -> List[StrategySweepConfig]

# Helpers
create_custom_sweep(name, strategy_name, param_grid, ...) -> StrategySweepConfig
print_sweep_catalog() -> str
```

---

## Tests

Tests für Phase 41 befinden sich in:

```
tests/test_research_playground.py
```

Ausführen:

```bash
pytest tests/test_research_playground.py -v
```

---

## Wichtige Hinweise

### Keine Live-Execution

Phase 41 ist **rein Research/Backtest-fokussiert**:
- Keine Live-/Testnet-Order-Ausführung
- Keine neuen Live-Endpoints
- Nur historische Daten

### Performance-Tipps

1. **max-runs limitieren** für erste Tests:
   ```bash
   python scripts/run_strategy_sweep.py --sweep-name rsi_reversion_fine --max-runs 20
   ```

2. **Coarse Granularität** für schnelle Exploration:
   ```bash
   python scripts/run_strategy_sweep.py --strategy ma_crossover --granularity coarse
   ```

3. **Parallel-Execution** für große Sweeps:
   ```bash
   python scripts/run_strategy_sweep.py --sweep-name breakout_fine --parallel --workers 8
   ```

### Ergebnis-Speicherorte

| Typ | Pfad |
|-----|------|
| Experiment-Ergebnisse | `reports/experiments/` |
| Sweep-Reports | `reports/sweeps/` |
| Report-Images | `reports/sweeps/images/` |
| Experiment-Registry | `reports/experiments/experiments.csv` |

---

## Bekannte Einschränkungen & Ausblick

### Aktuelle Einschränkungen

1. **Metrik-Namen-Varianten**: 
   - Beim Report-Generieren kann es zu Warnungen kommen, wenn `metric_sharpe_ratio` nicht gefunden wird
   - Automatischer Fallback auf `metric_total_return` funktioniert zuverlässig
   - Nicht kritisch, aber Metrik-Namen könnten konsistenter sein

2. **Pandas FutureWarnings**: 
   - In Tests erscheinen ~134 FutureWarnings bezüglich `.fillna()` Downcasting
   - Betrifft nicht die Sweep-Funktionalität, nur Test-Output
   - Kann in zukünftigen Pandas-Versionen behoben werden

3. **Sharpe-Ratio-Berechnung**: 
   - Bei sehr kurzen Backtest-Perioden oder geringer Varianz kann Sharpe-Ratio `NaN` sein
   - Report verwendet dann automatisch `total_return` als Sort-Metrik

### Mögliche zukünftige Erweiterungen

1. **Weitere Sweeps**: 
   - Zusätzliche vordefinierte Sweeps für weitere Strategien
   - Portfolio-Sweeps mit mehr Kombinationen

2. **Automatisches Top-N-Promoten**: 
   - Beste Konfigurationen automatisch in Config-Registry übernehmen
   - Integration mit Strategy-Registry für "Production-Ready"-Strategien

3. **Erweiterte Visualisierung**: 
   - Interaktive Dashboards (z.B. Plotly)
   - Parameter-Sensitivity-Analysen
   - Walk-Forward-Heatmaps

4. **Performance-Optimierung**: 
   - Caching von Backtest-Ergebnissen
   - Parallele Execution für große Sweeps (bereits implementiert, aber erweiterbar)

5. **Integration mit Live-System**: 
   - Beste Parameter automatisch in Testnet/Live übernehmen
   - Monitoring der Live-Performance vs. Backtest-Performance

---

## Phase 42 – Top-N Promotion

Phase 42 erweitert Phase 41 um eine **Top-N Promotion Pipeline**:

- Automatische Auswahl der besten Konfigurationen aus Sweep-Ergebnissen
- Export in maschinenlesbares TOML-Format
- Integration in den Sweep-Workflow

### Top-N Promotion Workflow

**1. Sweep ausführen**

```bash
python scripts/run_strategy_sweep.py \
  --sweep-name rsi_reversion_basic \
  --config config/config.toml \
  --max-runs 20
```

**2. Report generieren (optional)**

```bash
python scripts/generate_strategy_sweep_report.py \
  --sweep-name rsi_reversion_basic \
  --format both
```

**3. Top-N Kandidaten exportieren**

```bash
python scripts/promote_sweep_topn.py \
  --sweep-name rsi_reversion_basic \
  --metric metric_sharpe_ratio \
  --top-n 5
```

**Output:** `reports/sweeps/{sweep_name}_top_candidates.toml`

### TOML-Format

Die generierte TOML-Datei enthält:

```toml
[meta]
sweep_name = "rsi_reversion_basic"
metric_used = "metric_sharpe_ratio"
top_n = 5
generated_at = "2025-12-06T23:59:00"

[[candidates]]
rank = 1
sharpe_ratio = 2.0
total_return = 0.2
[candidates.params]
rsi_period = 14
oversold_level = 30
overbought_level = 70
```

### Verwendung der Top-Kandidaten

Die TOML-Datei kann verwendet werden für:

- **Neue Backtests**: Parameter direkt aus TOML übernehmen
- **Testnet-Profile**: Beste Konfigurationen als Basis für Testnet-Tests
- **Dokumentation**: Automatische Generierung von "Best Practices"
- **Weitere Analysen**: Maschinenlesbare Format für Scripts/Tools

### CLI-Optionen

```bash
python scripts/promote_sweep_topn.py \
  --sweep-name rsi_reversion_basic \
  --metric metric_sharpe_ratio \        # Primäre Metrik
  --fallback-metric metric_total_return \ # Fallback falls primary fehlt
  --top-n 5 \                             # Anzahl Top-Kandidaten
  --output reports/sweeps                 # Ausgabe-Verzeichnis
```

---

## Phase 43 – Visualisierung & Sweep-Dashboards

Phase 43 erweitert Phase 41/42 um **automatische Visualisierungen** für Sweep-Ergebnisse:

- 1D-Plots: Parameter vs. Kennzahl (z.B. `rsi_period` vs. `total_return`)
- 2D-Heatmaps: Zwei Parameter vs. Kennzahl (z.B. `fast_period` × `slow_period` vs. `sharpe_ratio`)
- Integration in Sweep-Reports (Markdown/HTML)

### Visualisierungs-Workflow

**1. Sweep ausführen**

```bash
python scripts/run_strategy_sweep.py \
  --sweep-name rsi_reversion_basic \
  --config config/config.toml \
  --max-runs 20
```

**2. Report mit Visualisierungen generieren**

```bash
python scripts/generate_strategy_sweep_report.py \
  --sweep-name rsi_reversion_basic \
  --format both \
  --with-plots \
  --plot-metric metric_total_return
```

**Output:**
- Markdown/HTML-Report mit eingebetteten Bildern
- PNG-Dateien unter `reports/sweeps/images/`

### Plot-Typen

**1D-Plots (Parameter vs. Metrik):**
- Scatter-Plot mit Trendlinie
- Automatisch für die ersten 3 Parameter erzeugt
- Dateiname: `{sweep_name}_{param}_vs_{metric}.png`

**2D-Heatmaps:**
- Heatmap über zwei Parameter
- Automatisch erzeugt wenn mindestens 2 Parameter vorhanden
- Dateiname: `{sweep_name}_heatmap_{param_x}_x_{param_y}_{metric}.png`

### CLI-Optionen

```bash
python scripts/generate_strategy_sweep_report.py \
  --sweep-name rsi_reversion_basic \
  --format both \
  --with-plots \                    # Aktiviert Visualisierungen
  --plot-metric metric_sharpe_ratio \  # Metrik für Plots (default: metric_sharpe_ratio)
  --sort-metric metric_total_return     # Metrik für Sortierung
```

### Verzeichnisstruktur

```
reports/sweeps/
├── {sweep_name}_report_{timestamp}.md
├── {sweep_name}_report_{timestamp}.html
└── images/
    ├── {sweep_name}_{param1}_vs_{metric}.png
    ├── {sweep_name}_{param2}_vs_{metric}.png
    └── {sweep_name}_heatmap_{param_x}_x_{param_y}_{metric}.png
```

### Hinweise

- **Matplotlib erforderlich**: Plots werden nur erzeugt wenn Matplotlib verfügbar ist
- **Automatische Parameter-Erkennung**: Die ersten 3 Parameter werden automatisch für Plots verwendet
- **NaN-Filterung**: Ungültige Werte werden automatisch gefiltert
- **Fehlerbehandlung**: Bei fehlenden Parametern/Metriken wird eine Warnung ausgegeben, der Report wird trotzdem erzeugt

---

## Nächste Schritte

Nach Phase 43:

1. **Walk-Forward-Analyse**: Out-of-Sample-Validierung der besten Parameter
   - **Siehe:** `docs/PHASE_44_WALKFORWARD_TESTING.md` für Details zum Walk-Forward-Workflow
2. **Monte-Carlo-Simulation**: Robustness-Testing
3. **Live-Deployment**: Beste Strategien in Testnet/Live übernehmen

---

*Phase 41 – Strategy-Sweeps & Research-Playground*  
*Phase 42 – Top-N Promotion*  
*Phase 43 – Visualisierung & Sweep-Dashboards*  
*Phase 44 – Walk-Forward Testing*  
*Peak_Trade Framework*
