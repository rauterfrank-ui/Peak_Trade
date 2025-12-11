# Phase 43 – Visualisierung & Sweep-Dashboards

## Status

**Phase 43 ist vollständig implementiert und getestet.**

Phase 43 erweitert das Reporting-System um **automatische Visualisierungen** für Strategy-Sweep-Ergebnisse. Die Visualisierungen helfen bei der schnellen Identifikation von optimalen Parameter-Kombinationen und dem Verständnis von Parameter-Sensitivitäten.

**Track:** Research & Backtest (keine Live-Execution)

---

## 1. Ziel & Kontext

### Warum Phase 43?

Nach Phase 41 (Strategy-Sweeps) und Phase 42 (Top-N Promotion) fehlte eine **visuelle Auswertung** der Sweep-Ergebnisse. Phase 43 schließt diese Lücke:

- **Schnelle Identifikation** optimaler Parameter-Kombinationen durch visuelle Darstellung
- **Verständnis von Parameter-Sensitivitäten** durch Scatter-Plots und Heatmaps
- **Integration in bestehende Reports** (Markdown/HTML) für nahtlosen Workflow

### Integration in Peak_Trade

Phase 43 baut auf zwei vorherigen Phasen auf:

1. **Phase 30 – Reporting & Visualisierung**
   - Grundlegende Plot-Funktionen (`src/reporting/plots.py`)
   - Report-Generierung (`src/reporting/experiment_report.py`)
   - Siehe `docs/PHASE_30_REPORTING_AND_VISUALIZATION.md` für Details

2. **Phase 41 – Strategy-Sweeps & Research-Playground**
   - Sweep-Definition und -Ausführung
   - Ergebnis-Speicherung unter `reports/experiments/`
   - Siehe `docs/PHASE_41_STRATEGY_SWEEPS_AND_RESEARCH_PLAYGROUND.md` für Details zur Sweep-Definition und -Ausführung

Phase 43 nutzt die bestehenden Reporting- und Plot-Funktionen aus Phase 30 und erweitert sie um **sweep-spezifische Visualisierungen**.

---

## Wie du das v1.0 Dashboard liest

- **Einstieg (3–5 Minuten):** Starte mit der **Top-Kennzahlen-Tabelle** im Report (Sharpe, Total Return, Max Drawdown) und der **Haupt-Heatmap** für den Parameter-Raum. Diese geben dir den schnellsten Überblick über die besten Konfigurationen.

- **Equity & Drawdown verstehen:** Die 1D-Plots (Parameter vs. Metrik) zeigen, wie sensitiv eine Metrik auf Parameteränderungen reagiert. Flache Kurven = robuste Parameter; steile Kurven = instabil. Drawdown-Heatmaps helfen, stabile Regionen mit moderatem Risk zu identifizieren.

- **Heatmaps interpretieren:** 2D-Heatmaps zeigen Interaktionen zwischen zwei Parametern. Suche nach „Inseln" hoher Performance – isolierte Maxima sind fragiler als breite Plateaus.

- **Warnsignale erkennen:** Sehr tiefe Drawdowns (< -30%), stark schwankende Performance über kleine Parameteränderungen, oder wenige gültige Datenpunkte (NaN-Warnungen) sind Red Flags. Details zu Go/No-Go-Grenzwerten findest du in [`PLAYBOOK_RESEARCH_TO_LIVE_PORTFOLIOS.md`](PLAYBOOK_RESEARCH_TO_LIVE_PORTFOLIOS.md).

- **Rollen-Fokus:**
  - *Research/Quant:* Fokus auf Parameter-Heatmaps, Sensitivitäts-Plots und Metrik-Verteilungen für Optimierung.
  - *Operator/Ops:* Fokus auf Drawdown-Heatmaps und Top-N-Tabellen für aktuelle Performance-Einschätzung.
  - *Reviewer/Risk:* Fokus auf Drawdown-Analysen, Extrem-Werte und Robustheits-Indikatoren (breite vs. schmale Optima).

- **Einbettung in v1.0-Workflow:** Das Dashboard dient der **visuellen Ersteinschätzung**. Für fundierte Go/No-Go-Entscheidungen lies die zugehörigen Reports und Dokus:
  - [`PEAK_TRADE_V1_OVERVIEW_FULL.md`](PEAK_TRADE_V1_OVERVIEW_FULL.md) – v1.0 Gesamtübersicht
  - [`PEAK_TRADE_STATUS_OVERVIEW.md`](PEAK_TRADE_STATUS_OVERVIEW.md) – Projekt-Status
  - [`PLAYBOOK_RESEARCH_TO_LIVE_PORTFOLIOS.md`](PLAYBOOK_RESEARCH_TO_LIVE_PORTFOLIOS.md) – Research → Live Playbook

---

## 2. Komponentenübersicht

### Module

| Modul | Datei | Beschreibung |
|-------|-------|--------------|
| **Sweep Visualization** | `src/reporting/sweep_visualization.py` | Spezifische Plot-Funktionen für Sweeps |
| **Plot Helpers** | `src/reporting/plots.py` | Basis-Plot-Funktionen (Scatter, Heatmap, Histogram) |
| **Report Generator** | `scripts/generate_strategy_sweep_report.py` | CLI-Script mit `--with-plots` Flag |

### Hauptfunktionen

| Funktion | Beschreibung |
|----------|--------------|
| `plot_metric_vs_single_param()` | 1D-Plot: Parameter vs. Metrik (Scatter + Trend) |
| `plot_metric_heatmap_two_params()` | 2D-Heatmap: Zwei Parameter vs. Metrik |
| `create_drawdown_heatmap()` | 2D-Heatmap speziell für Drawdown-Metriken (z. B. Max-Drawdown) |
| `generate_default_sweep_plots()` | Automatische Standard-Plot-Kollektion (inkl. Drawdown-Heatmaps) |

### Tests

**Datei:** `tests/test_sweep_visualization.py`

**12 Tests** in 3 Kategorien:
- `TestPlotMetricVsSingleParam` (5 Tests)
- `TestPlotMetricHeatmapTwoParams` (3 Tests)
- `TestGenerateDefaultSweepPlots` (4 Tests)

**Status:** ✅ Alle Tests grün

Ausführen:
```bash
pytest tests/test_sweep_visualization.py -v
```

---

## 3. Workflow: Von Sweep zu Report mit Plots

### Übersicht

Der Workflow besteht aus zwei Schritten:

1. **Sweep ausführen** (Phase 41) → Ergebnisse unter `reports/experiments/`
2. **Report mit Plots generieren** (Phase 43) → Reports + Plots unter `reports/sweeps/`

### Schritt-für-Schritt Anleitung

#### Schritt 1: Virtual Environment aktivieren

```bash
cd ~/Peak_Trade
source .venv/bin/activate
```

#### Schritt 2: Sweep ausführen

**Hinweis:** Für Details zur Sweep-Definition und -Ausführung siehe `docs/PHASE_41_STRATEGY_SWEEPS_AND_RESEARCH_PLAYGROUND.md`.

```bash
# Beispiel: rsi_reversion_basic mit max. 5 Runs (für schnellen Test)
python scripts/run_strategy_sweep.py \
  --sweep-name rsi_reversion_basic \
  --config config/config.toml \
  --max-runs 5

# Vollständiger Sweep (alle Kombinationen)
python scripts/run_strategy_sweep.py \
  --sweep-name rsi_reversion_basic \
  --config config/config.toml
```

**Erwartete Ausgabe:**
- Sweep läuft durch ohne Exceptions
- Erfolgreiche Runs werden angezeigt (z.B. "27 erfolgreich, 0 fehlgeschlagen")
- Ergebnisse werden gespeichert unter `reports/experiments/`
- Dateinamen enthalten den Sweep-Namen: `{sweep_name}_{experiment_id}_{timestamp}.csv`

#### Schritt 3: Report mit Visualisierungen generieren

```bash
# Markdown + HTML Report mit Plots (inkl. Drawdown-Heatmaps)
python scripts/generate_strategy_sweep_report.py \
  --sweep-name rsi_reversion_basic \
  --format both \
  --with-plots \
  --plot-metric metric_total_return

# Nur Markdown mit Plots
python scripts/generate_strategy_sweep_report.py \
  --sweep-name rsi_reversion_basic \
  --format markdown \
  --with-plots
```

**Hinweis:** Drawdown-Heatmaps werden automatisch erzeugt und im Report verlinkt, wenn im Sweep-Ergebnis eine entsprechende Drawdown-Metrik (z. B. `metric_max_drawdown`) vorhanden ist. Falls keine Drawdown-Metrik vorhanden ist, wird der Report trotzdem erstellt (nur ohne Drawdown-Heatmaps).

**Erwartete Ausgabe:**
- Kein Fehler "Keine Ergebnisse gefunden"
- Report-Dateien werden erzeugt:
  - `reports/sweeps/{sweep_name}_report_{timestamp}.md`
  - `reports/sweeps/{sweep_name}_report_{timestamp}.html` (falls `--format both`)
- **Plots werden erzeugt** unter `reports/sweeps/images/`
- Report enthält Markdown-Bildlinks zu den Plots

#### Schritt 4: Ergebnisse finden

- **Sweep-Ergebnisse**: `reports/experiments/{sweep_name}_*.csv` (oder `.parquet`)
- **Reports**: `reports/sweeps/{sweep_name}_report_*.md` (oder `.html`)
- **Visualisierungen**: `reports/sweeps/images/`

---

## 4. Plots & Report-Inhalt

### Plot-Typen

#### 1D-Plots (Parameter vs. Metrik)
- **Scatter-Plot** mit Trendlinie
- Zeigt Sensitivität einer Metrik gegenüber einem Parameter
- Automatische NaN-Filterung
- **Dateiname:** `{sweep_name}_{param}_vs_{metric}.png`

#### 2D-Heatmaps (Zwei Parameter vs. Metrik)
- **Pivot-basierte Heatmap**
- Zeigt Interaktion zweier Parameter
- Automatische Annotation bei kleinen Heatmaps (≤100 Zellen)
- **Dateiname:** `{sweep_name}_heatmap_{param_x}_x_{param_y}_{metric}.png`

#### Drawdown-Heatmaps (Max-Drawdown über Parameter-Raum)
- **Spezielle 2D-Heatmap für Drawdown-Metriken**
- Neben Performance-Metriken wie Sharpe-Ratio ist der maximale Drawdown ein zentrales Robustness-Kriterium
- Zeigt zwei Parameterachsen (z. B. Lookback-Periode und Threshold) gegen den Max-Drawdown
- Verwendet eine invertierte Colormap (Reds) für bessere Visualisierung negativer Drawdown-Werte
- **Automatische Erzeugung:** Wird automatisch erzeugt, wenn im Sweep-Ergebnis eine Drawdown-Metrik (z. B. `metric_max_drawdown`) vorhanden ist
- **Dateiname:** `heatmap_drawdown_{param_x}_vs_{param_y}.png`
- **Besonders nützlich:** Hilft, stabile Parameterregionen mit moderaten Drawdowns zu identifizieren, besonders für aggressivere Strategien

#### Histogramme (Metrik-Verteilung)
- **Verteilungs-Histogramm** einer Metrik
- Zeigt Mittelwert und Median
- Wird automatisch von `build_experiment_report()` erzeugt (Phase 30)
- **Dateiname:** `{sweep_name}_{metric}_distribution.png`

### Verzeichnisstruktur

```
reports/sweeps/
├── {sweep_name}_report_{timestamp}.md
├── {sweep_name}_report_{timestamp}.html
└── images/
    ├── {sweep_name}_{param1}_vs_{metric}.png
    ├── {sweep_name}_{param2}_vs_{metric}.png
    ├── {sweep_name}_{param3}_vs_{metric}.png
    ├── {sweep_name}_heatmap_{param_x}_x_{param_y}_{metric}.png
    └── heatmap_drawdown_{param_x}_vs_{param_y}.png  # Falls max_drawdown vorhanden
```

**Beispiel:**
```
reports/sweeps/
├── rsi_reversion_basic_report_20251207_002140.md
├── rsi_reversion_basic_report_20251207_002140.html
└── images/
    ├── rsi_reversion_basic_rsi_period_vs_total_return.png
    ├── rsi_reversion_basic_oversold_level_vs_total_return.png
    ├── rsi_reversion_basic_overbought_level_vs_total_return.png
    └── rsi_reversion_basic_heatmap_rsi_period_x_oversold_level_total_return.png
```

### Report-Inhalt

Die generierten Reports enthalten eine **Visualizations-Section** mit Markdown-Bildlinks:

```markdown
## Visualizations

### Rsi Period vs Metrik
![Rsi Period vs Metrik](images/rsi_reversion_basic_rsi_period_vs_total_return.png)

### Oversold Level vs Metrik
![Oversold Level vs Metrik](images/rsi_reversion_basic_oversold_level_vs_total_return.png)

### Overbought Level vs Metrik
![Overbought Level vs Metrik](images/rsi_reversion_basic_overbought_level_vs_total_return.png)

### Parameter Heatmap (2D)
![Parameter Heatmap](images/rsi_reversion_basic_heatmap_rsi_period_x_oversold_level_total_return.png)

### Drawdown-Heatmaps (Max-Drawdown über Parameter-Raum)

#### Drawdown-Heatmap: Rsi Period × Oversold Level
![Drawdown-Heatmap: Rsi Period × Oversold Level](images/heatmap_drawdown_rsi_period_vs_oversold_level.png)
```

HTML-Reports enthalten die Plots als `<img>`-Tags mit relativen Pfaden.

---

## 5. CLI-Optionen

### Unified Research-CLI (Empfohlen)

Alternativ zur direkten Verwendung von `generate_strategy_sweep_report.py` kann die Report-Generierung über die Unified Research-CLI gestartet werden:

```bash
python scripts/research_cli.py report \
  --sweep-name rsi_reversion_basic \
  --format both \
  --with-plots
```

### generate_strategy_sweep_report.py

```bash
python scripts/generate_strategy_sweep_report.py \
  --sweep-name rsi_reversion_basic \
  --format both \                    # markdown, html, oder both
  --with-plots \                     # Aktiviert Visualisierungen
  --plot-metric metric_sharpe_ratio \ # Metrik für Plots (default: metric_sharpe_ratio)
  --sort-metric metric_total_return    # Metrik für Sortierung
```

**Wichtige Flags:**
- `--with-plots`: Aktiviert automatische Plot-Generierung
- `--plot-metric`: Primäre Metrik für Plots (Fallback: `metric_total_return`)
- `--sort-metric`: Metrik für Sortierung im Report (default: `metric_sharpe_ratio`)

**Vollständige Optionen:**
- `--sweep-name` / `-s`: Name des Sweeps (oder `--input` / `-i` für direkten Dateipfad)
- `--format` / `-f`: Output-Format (`markdown`, `html`, `both`)
- `--output-dir` / `-o`: Ausgabe-Verzeichnis (default: `reports/sweeps`)
- `--top-n`: Anzahl Top-Runs im Report (default: 20)
- `--heatmap-params`: Zwei Parameter für Heatmap (optional)

---

## 6. Programmatische Verwendung

### Einzelne Plots erzeugen

```python
from pathlib import Path
from src.reporting.sweep_visualization import (
    plot_metric_vs_single_param,
    plot_metric_heatmap_two_params,
    generate_default_sweep_plots,
)

# 1D-Plot: Parameter vs. Metrik
plot_metric_vs_single_param(
    df=sweep_results,
    param_name="rsi_period",
    metric_name="total_return",
    sweep_name="rsi_reversion_basic",
    output_dir=Path("reports/sweeps/images"),
)

# 2D-Heatmap: Zwei Parameter vs. Metrik
plot_metric_heatmap_two_params(
    df=sweep_results,
    param_x="oversold_level",
    param_y="overbought_level",
    metric_name="sharpe_ratio",
    sweep_name="rsi_reversion_basic",
    output_dir=Path("reports/sweeps/images"),
)

# Drawdown-Heatmap: Max-Drawdown über zwei Parameter
create_drawdown_heatmap(
    df=sweep_results,
    param_x="rsi_period",
    param_y="oversold_level",
    metric_col="max_drawdown",
    sweep_name="rsi_reversion_basic",
    output_dir=Path("reports/sweeps/images"),
)

# Automatische Standard-Plots (empfohlen, inkl. Drawdown-Heatmaps)
plots = generate_default_sweep_plots(
    df=sweep_results,
    sweep_name="rsi_reversion_basic",
    output_dir=Path("reports/sweeps/images"),
    param_candidates=["rsi_period", "oversold_level", "overbought_level"],
    metric_primary="metric_sharpe_ratio",
    metric_fallback="metric_total_return",
)
```

### Integration in Reports

Die Plots werden automatisch in den Report eingebunden, wenn `--with-plots` gesetzt ist:

```python
from src.reporting.experiment_report import build_experiment_report, load_experiment_results
from src.reporting.sweep_visualization import generate_default_sweep_plots
from pathlib import Path

# Sweep-Ergebnisse laden
df = load_experiment_results("reports/experiments/rsi_reversion_basic_*.csv")

# Report erstellen
report = build_experiment_report(
    title="RSI Reversion Sweep",
    df=df,
    sort_metric="metric_sharpe_ratio",
)

# Plots erzeugen
output_dir = Path("reports/sweeps/images")
plots = generate_default_sweep_plots(
    df=df,
    sweep_name="rsi_reversion_basic",
    output_dir=output_dir,
)

# Plots zum Report hinzufügen (wird automatisch gemacht wenn --with-plots gesetzt)
# Die Visualizations-Section wird automatisch eingefügt
```

---

## 7. Technische Details

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
- Plot wird nicht erzeugt wenn keine gültigen Daten vorhanden

### Parameter-Erkennung

- Automatische Erkennung von `param_*` Spalten
- Erste 3 Parameter werden standardmäßig für Plots verwendet
- Heatmap wird nur erzeugt wenn mindestens 2 Parameter vorhanden

### Dateinamen-Konvention

| Plot-Typ | Dateiname |
|----------|-----------|
| 1D Parameter-Plot | `{sweep_name}_{param}_vs_{metric}.png` |
| 2D Heatmap | `{sweep_name}_heatmap_{param_x}_x_{param_y}_{metric}.png` |
| Drawdown-Heatmap | `heatmap_drawdown_{param_x}_vs_{param_y}.png` |

---

## 8. Troubleshooting

### Problem: Keine Sweep-Ergebnisse gefunden

**Symptom:**
```
Fehler: Keine Ergebnisse gefunden für Sweep 'rsi_reversion_basic'
```

**Lösung:**
1. Prüfe, ob Sweep ausgeführt wurde: `ls reports/experiments/*rsi_reversion*`
2. Führe Sweep aus: `python scripts/run_strategy_sweep.py --sweep-name rsi_reversion_basic`
3. Prüfe Dateinamen: Der Sweep-Name muss im Dateinamen enthalten sein

### Problem: Plots werden nicht erzeugt

**Symptom:**
- Report wird erstellt, aber keine Plots unter `reports/sweeps/images/`

**Lösung:**
1. Prüfe, ob `--with-plots` Flag gesetzt wurde
2. Prüfe Logs auf Warnungen (z.B. "Keine Parameter-Spalten gefunden")
3. Prüfe, ob Matplotlib verfügbar ist: `python -c "import matplotlib; print('OK')"`
4. Prüfe, ob DataFrame Parameter-Spalten enthält: `df.columns[df.columns.str.startswith('param_')]`

### Problem: Bilder nicht im Report eingebunden

**Symptom:**
- Plots existieren, aber Markdown zeigt `![...](images/...)` ohne Bild

**Lösung:**
1. Prüfe relative Pfade: Bilder sollten relativ zum Report-Verzeichnis sein
2. Prüfe, ob `images/` Verzeichnis existiert: `ls reports/sweeps/images/`
3. Prüfe Report-Inhalt: `grep -A 2 "Visualizations" reports/sweeps/*.md`

### Problem: Reports/Plots werden in Git angezeigt

**Symptom:**
- `git status` zeigt `reports/sweeps/` oder `reports/experiments/`

**Lösung:**
- Reports und Plots sind **Artefakte** und sollten nicht ins Repo
- Prüfe `.gitignore`: Sollte `reports/sweeps/` und `reports/experiments/` enthalten
- Falls nötig, füge hinzu:
  ```gitignore
  # Reports & Visualizations (generierte Artefakte)
  reports/sweeps/
  reports/experiments/
  reports/sweeps/images/
  ```

---

## 9. Zusammenfassung & Ausblick

### Was Phase 43 leistet

Phase 43 erweitert den Research-Track um **visuelle Auswertung** von Sweep-Ergebnissen:

- **Automatische Plot-Generierung** für Parameter-Sensitivitäten
- **Integration in Reports** (Markdown/HTML) für nahtlosen Workflow
- **Robuste Fehlerbehandlung** (NaN-Filterung, Fallback-Logik)
- **Vollständige Test-Abdeckung** (12 Tests)

### Ausblick

Phase 43 bildet die Grundlage für:

1. **Walk-Forward-Testing** (Phase 44)
   - Out-of-Sample-Validierung der Top-N-Konfigurationen
   - **Siehe:** `docs/PHASE_44_WALKFORWARD_TESTING.md` für Details

2. **Interaktive Dashboards** (Phase 60+)
   - Plotly-basierte interaktive Visualisierungen
   - Web-basierte Dashboards für Live-Monitoring

3. **Deep-Research-Track Integration** (Phase 60+)
   - Regime-basierte Visualisierungen
   - Feature-Importance-Plots
   - Walk-Forward-Analysen

3. **Automatische Top-N-Promotion** (Phase 42)
   - Beste Konfigurationen automatisch in Config-Registry übernehmen
   - Integration mit Strategy-Registry für "Production-Ready"-Strategien

4. **Weitere Plot-Typen**
   - 3D-Visualisierungen für drei Parameter
   - Zeitreihen-Plots für Walk-Forward-Analysen
   - Korrelations-Matrizen zwischen Parametern

5. **Automatisierte Nightly-Sweeps**
   - Regelmäßige Sweeps mit automatischer Report-Generierung
   - E-Mail-Benachrichtigungen bei neuen Top-Kandidaten

---

## Siehe auch

- [Phase 30 – Reporting & Visualisierung](PHASE_30_REPORTING_AND_VISUALIZATION.md) – Grundlegende Reporting- und Plot-Funktionen
- [Phase 41 – Strategy Sweeps & Research-Playground](PHASE_41_STRATEGY_SWEEPS_AND_RESEARCH_PLAYGROUND.md) – Sweep-Definition und -Ausführung
- [Phase 42 – Top-N Promotion](PHASE_42_TOPN_PROMOTION.md) – Automatische Auswahl der besten Konfigurationen
- [Phase 44 – Walk-Forward Testing](PHASE_44_WALKFORWARD_TESTING.md) – Out-of-Sample-Validierung der Top-N-Konfigurationen
- [Reporting V2](REPORTING_V2.md) – Übersicht über das Reporting-System
- [Deep Research Backoffice Overview](DEEP_RESEARCH_BACKOFFICE_OVERVIEW.md) – Langfristiger Research-Track

---

*Phase 43 – Visualisierung & Sweep-Dashboards*  
*Peak_Trade Framework*
