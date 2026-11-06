# Phase 30 – Reporting & Visualisierung

> **Status:** Implementiert
> **Scope:** Research / Backtest / Shadow (kein Live-UI)

---

## 1. Einleitung

Der Reporting-Layer in Phase 30 ermöglicht die strukturierte Auswertung und Visualisierung von:

- **Einzel-Backtests** – Performance-Metriken, Equity-Curves, Trade-Statistiken
- **Portfolio-/Regime-Runs** – Multi-Asset-Ergebnisse mit Regime-Overlays
- **Parameter-Sweeps & Experiments (Phase 29)** – Aggregierte Ergebnisse über viele Runs

Der Layer erzeugt:
- **Markdown-Reports** für Versionierung im Repo
- **HTML-Reports** für schnelle visuelle Inspektion
- **PNG-Plots** für Equity-Curves, Drawdowns, Heatmaps

---

## 2. Architektur

```
src/reporting/
├── __init__.py              # Public API Exports
├── base.py                  # Report, ReportSection, Markdown-Helper
├── plots.py                 # Zentrale Plot-Funktionen (Matplotlib)
├── backtest_report.py       # Backtest-Report Builder
├── experiment_report.py     # Experiment/Sweep-Report Builder
├── execution_reports.py     # Execution-Stats (Phase 16D)
└── html_reports.py          # HTML-Report-Builder (Phase 21)

scripts/
├── generate_backtest_report.py     # CLI für Backtest-Reports
└── generate_experiment_report.py   # CLI für Experiment-Reports
```

---

## 3. Backtest-Reports

### 3.1 Workflow

1. **Backtest ausführen** (mit `BacktestEngine`)
2. **Metriken & Equity speichern** (Parquet/CSV)
3. **Report generieren** mit `generate_backtest_report.py`
4. **Output:** Markdown-Report + PNG-Plots

### 3.2 CLI-Beispiel

```bash
# Aus gespeichertem Result
python3 scripts/generate_backtest_report.py \
    --results-file results/btc_ma_crossover.parquet \
    --output reports/btc_ma_crossover.md

# Mit Equity-Curve aus separater Datei
python3 scripts/generate_backtest_report.py \
    --results-file results/stats.csv \
    --equity-file results/equity.parquet \
    --output reports/backtest_report.md

# HTML-Output
python3 scripts/generate_backtest_report.py \
    --results-file results/run.parquet \
    --output reports/report.html \
    --format html
```

### 3.3 Python API

```python
from src.reporting.backtest_report import build_backtest_report, save_backtest_report

# Report bauen
report = build_backtest_report(
    title="MA Crossover BTC/EUR",
    metrics={"sharpe": 1.5, "total_return": 0.15, "max_drawdown": -0.08},
    equity_curve=equity_series,
    params={"fast_period": 10, "slow_period": 50},
)

# Speichern
save_backtest_report(report, "reports/ma_crossover.md")
```

### 3.4 Report-Inhalt

Ein typischer Backtest-Report enthält:

| Section | Beschreibung |
|---------|--------------|
| **Performance Summary** | Kennzahlen-Tabelle (Return, Sharpe, Drawdown, etc.) |
| **Strategy Parameters** | Parameter-Tabelle |
| **Trade Statistics** | Win Rate, Avg Win/Loss, Profit Factor |
| **Charts** | Equity Curve, Drawdown (als PNG) |

---

## 4. Experiment-/Sweep-Reports

### 4.1 Workflow

1. **Sweep ausführen** (Phase 29: `run_experiment_sweep.py`)
2. **Results speichern** (CSV/Parquet mit `param_*` und `metric_*` Spalten)
3. **Report generieren** mit `generate_experiment_report.py`
4. **Output:** Markdown-Report + Heatmaps + Histogramme

### 4.2 CLI-Beispiel

```bash
# Basic Report
python3 scripts/generate_experiment_report.py \
    --input results/rsi_reversion_sweep.parquet \
    --output reports/rsi_reversion_sweep_report.md

# Mit Sortierung und Top-N
python3 scripts/generate_experiment_report.py \
    --input results/ma_sweep.csv \
    --output reports/ma_sweep_report.md \
    --sort-metric metric_sharpe \
    --top-n 30

# Mit Heatmap-Visualisierung
python3 scripts/generate_experiment_report.py \
    --input results/rsi_sweep.parquet \
    --output reports/rsi_sweep.md \
    --heatmap-params param_rsi_window param_lower_threshold
```

### 4.3 Python API

```python
from src.reporting.experiment_report import (
    build_experiment_report,
    summarize_experiment_results,
)

# Analysiere Ergebnisse
summary = summarize_experiment_results(
    df,
    top_n=20,
    sort_metric="metric_sharpe",
)
print(summary["top_runs"])

# Report bauen
report = build_experiment_report(
    title="RSI Sweep Analysis",
    df=results_df,
    sort_metric="metric_sharpe",
    top_n=20,
    heatmap_params=("param_rsi_window", "param_lower_threshold"),
)
```

### 4.4 Report-Inhalt

| Section | Beschreibung |
|---------|--------------|
| **Overview** | Total Runs, Parameter-Anzahl, Metriken |
| **Best Parameter Combination** | Beste Params mit allen Metriken |
| **Top N Runs** | Ranking nach Sort-Metrik |
| **Metric Statistics** | Min/Max/Mean/Std pro Metrik |
| **Visualizations** | Heatmap, Distribution, Scatter |
| **Correlations** | Parameter-Metrik Korrelationen |

---

## 5. Visualisierungen

### 5.1 Verfügbare Plots

| Plot | Funktion | Verwendung |
|------|----------|------------|
| **Equity Curve** | `save_equity_plot()` | Backtest-Reports |
| **Drawdown** | `save_drawdown_plot()` | Backtest-Reports |
| **Heatmap** | `save_heatmap()` | Parameter vs. Metrik |
| **Histogram** | `save_histogram()` | Metrik-Verteilungen |
| **Scatter** | `save_scatter_plot()` | Parameter vs. Metrik |
| **Equity + Regimes** | `save_equity_with_regimes()` | Regime-Backtests |

### 5.2 Beispiel: Heatmap

```python
from src.reporting.plots import save_heatmap
import pandas as pd

# Pivot-Table erstellen
pivot = df.pivot_table(
    values="metric_sharpe",
    index="param_slow_period",
    columns="param_fast_period",
    aggfunc="mean",
)

# Heatmap speichern
save_heatmap(
    pivot,
    "reports/images/sharpe_heatmap.png",
    title="Sharpe Ratio by Period Parameters",
    xlabel="Fast Period",
    ylabel="Slow Period",
    cbar_label="Sharpe",
)
```

**Interpretation:** Dunklere/hellere Farben zeigen höhere/niedrigere Sharpe-Werte. Dies hilft, optimale Parameter-Regionen zu identifizieren.

---

## 6. Beispiel-Auszüge

### 6.1 Top-N Block (Markdown)

```markdown
## Top 10 Runs by Sharpe

| rank | rsi_window | lower_threshold | sharpe | total_return | max_drawdown |
|------|------------|-----------------|--------|--------------|--------------|
| 1    | 14         | 30              | 1.82   | 18.5%        | -6.2%        |
| 2    | 20         | 25              | 1.75   | 16.8%        | -7.1%        |
| 3    | 14         | 35              | 1.68   | 15.2%        | -5.8%        |
| ...  | ...        | ...             | ...    | ...          | ...          |
```

### 6.2 Heatmap-Interpretation

In der Heatmap für `param_fast_period` vs. `param_slow_period`:
- **Dunkelgrün:** Höherer Sharpe (besser)
- **Dunkelrot:** Niedriger Sharpe (schlechter)
- **Muster:** Oft zeigt sich ein diagonales Band guter Performance

---

## 7. Best Practices

### 7.1 Kleine Sweeps zum Testen

Bevor große Sweeps gestartet werden:
```python
# Erst mit wenigen Kombinationen testen
config = ExperimentConfig(
    param_sweeps=[
        ParamSweep("fast", [5, 10]),  # nur 2 Werte
        ParamSweep("slow", [50, 100]),
    ],
    ...
)
```

### 7.2 Multi-Metrik-Sortierung

Für robustere Ergebnisse: Nicht nur nach Sharpe sortieren, sondern auch Drawdown berücksichtigen:

```python
# Top Runs nach Sharpe, aber nur mit Drawdown > -10%
df_filtered = df[df["metric_max_drawdown"] > -0.10]
summary = summarize_experiment_results(df_filtered, sort_metric="metric_sharpe")
```

### 7.3 Versionierung von Reports

Reports sollten datiert werden:
```
reports/
├── phase29_rsi_sweep_2024-12-04.md
├── phase29_rsi_sweep_2024-12-04/
│   └── images/
│       ├── heatmap.png
│       └── distribution.png
```

---

## 8. Abgrenzung

| Scope | Beschreibung |
|-------|--------------|
| **Research** | Reports für Strategie-Entwicklung |
| **Backtest** | Auswertung historischer Performance |
| **Shadow** | Paper-Trading Monitoring |
| **NICHT Live** | Kein Dashboard, kein Server |

Reports sind **Hilfsmittel für die Analyse**, keine automatischen Entscheidungsgeber. Die finale Bewertung und Freigabe für Live-Trading erfolgt manuell.

---

## 9. API-Referenz

### 9.1 Base Types

```python
from src.reporting import Report, ReportSection

# Section erstellen
section = ReportSection(
    title="Summary",
    content_markdown="| Metric | Value |\n|--------|-------|\n| Sharpe | 1.5 |",
)

# Report erstellen
report = Report(
    title="My Report",
    sections=[section],
    metadata={"strategy": "ma_crossover"},
)

# Export
print(report.to_markdown())
print(report.to_html())
```

### 9.2 Backtest Reports

```python
from src.reporting import (
    build_backtest_report,
    build_backtest_summary_section,
    save_backtest_report,
)
```

### 9.3 Experiment Reports

```python
from src.reporting import (
    build_experiment_report,
    summarize_experiment_results,
    find_best_params,
    save_experiment_report,
)
```

### 9.4 Plots

```python
from src.reporting import (
    save_line_plot,
    save_equity_plot,
    save_drawdown_plot,
    save_heatmap,
    save_scatter_plot,
    save_histogram,
    save_equity_with_regimes,
)
```

---

## 10. Tests

```bash
# Alle Reporting-Tests
python3 -m pytest tests/test_reporting_*.py -v

# Einzelne Module
python3 -m pytest tests/test_reporting_base.py -v
python3 -m pytest tests/test_reporting_backtest_report.py -v
python3 -m pytest tests/test_reporting_experiment_report.py -v
```

---

## 11. Zusammenfassung

Phase 30 liefert einen vollständigen Reporting-Layer für:

1. **Backtest-Reports** – Metriken, Equity-Curves, Trade-Stats
2. **Experiment-Reports** – Sweep-Aggregationen, Top-N, Heatmaps
3. **CLI-Integration** – Einfache Nutzung via Scripts
4. **Flexible Formate** – Markdown & HTML

Der Layer bleibt bewusst **low-tech** (Python + Pandas + Matplotlib) und **Research-fokussiert** – kein Live-Dashboard, keine automatischen Trading-Entscheidungen.
