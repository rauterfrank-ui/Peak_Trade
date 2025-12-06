# Phase 43 – Sweep Visualization & Plots

## Überblick

Phase 43 erweitert das Reporting-System um automatische Visualisierungen für Strategy-Sweep-Ergebnisse. Die Visualisierungen helfen bei der schnellen Identifikation von optimalen Parameter-Kombinationen und dem Verständnis von Parameter-Sensitivitäten.

---

## Komponenten

### 1. Visualization-Modul

**Datei:** `src/reporting/sweep_visualization.py`

Hauptfunktionen:

| Funktion | Beschreibung |
|----------|--------------|
| `plot_metric_vs_single_param()` | 1D-Plot: Parameter vs. Metrik (Scatter + Trend) |
| `plot_metric_heatmap_two_params()` | 2D-Heatmap: Zwei Parameter vs. Metrik |
| `generate_default_sweep_plots()` | Automatische Standard-Plot-Kollektion |

### 2. Plot-Typen

#### 1D Parameter-Plots
- Scatter-Plot mit Trendlinie
- Zeigt Sensitivität einer Metrik gegenüber einem Parameter
- Automatische NaN-Filterung

#### 2D Heatmaps
- Pivot-basierte Heatmap
- Zeigt Interaktion zweier Parameter
- Automatische Annotation bei kleinen Heatmaps (≤100 Zellen)

---

## Verwendung

### Programmatisch

```python
from pathlib import Path
from src.reporting.sweep_visualization import (
    plot_metric_vs_single_param,
    plot_metric_heatmap_two_params,
    generate_default_sweep_plots,
)

# Einzelner 1D-Plot
plot_metric_vs_single_param(
    df=sweep_results,
    param_name="rsi_period",
    metric_name="total_return",
    sweep_name="rsi_reversion_basic",
    output_dir=Path("reports/sweeps/images"),
)

# 2D-Heatmap
plot_metric_heatmap_two_params(
    df=sweep_results,
    param_x="oversold_level",
    param_y="overbought_level",
    metric_name="sharpe_ratio",
    sweep_name="rsi_reversion_basic",
    output_dir=Path("reports/sweeps/images"),
)

# Automatische Standard-Plots
plots = generate_default_sweep_plots(
    df=sweep_results,
    sweep_name="rsi_reversion_basic",
    output_dir=Path("reports/sweeps/images"),
    metric_primary="metric_sharpe_ratio",
    metric_fallback="metric_total_return",
)
```

### CLI-Integration

```bash
# Report mit Plots generieren
python scripts/generate_strategy_sweep_report.py \
    --sweep-name rsi_reversion_basic \
    --with-plots \
    --plot-metric metric_total_return
```

---

## Output

### Dateinamen-Konvention

| Plot-Typ | Dateiname |
|----------|-----------|
| 1D Parameter-Plot | `{sweep_name}_{param}_vs_{metric}.png` |
| 2D Heatmap | `{sweep_name}_heatmap_{param_x}_x_{param_y}_{metric}.png` |

### Output-Verzeichnis

Standard: `reports/sweeps/images/`

---

## Technische Details

### Dependencies

- **matplotlib**: Basis-Plotting (bereits im Projekt vorhanden)
- Keine zusätzlichen Dependencies (kein seaborn/plotly)

### Fallback-Logik

1. Versucht primäre Metrik (`metric_sharpe_ratio`)
2. Fallback auf `metric_total_return`
3. Bei beiden fehlend: erste verfügbare `metric_*` Spalte

### NaN-Handling

- NaN-Werte werden automatisch vor dem Plotting gefiltert
- Warnung im Log wenn alle Werte NaN sind

---

## Tests

```bash
# Phase 43 Tests
.venv/bin/pytest tests/test_sweep_visualization.py -v
```

**12 Tests** in 3 Kategorien:
- `TestPlotMetricVsSingleParam` (5 Tests)
- `TestPlotMetricHeatmapTwoParams` (3 Tests)
- `TestGenerateDefaultSweepPlots` (4 Tests)

---

## Beispiel-Output

```
reports/sweeps/images/
├── rsi_reversion_basic_rsi_period_vs_total_return.png
├── rsi_reversion_basic_oversold_level_vs_total_return.png
├── rsi_reversion_basic_overbought_level_vs_total_return.png
└── rsi_reversion_basic_heatmap_rsi_period_x_oversold_level_total_return.png
```

---

## Siehe auch

- [Phase 41 – Strategy Sweeps](PHASE_41_STRATEGY_SWEEPS_AND_RESEARCH_PLAYGROUND.md)
- [Phase 42 – Top-N Promotion](PHASE_42_TOPN_PROMOTION.md) (falls vorhanden)
- [Reporting V2](REPORTING_V2.md)
