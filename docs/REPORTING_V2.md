# Peak_Trade Reporting v2: HTML-Dashboards & CLI-UX

## Phase 21 – Übersicht

Das **Reporting v2** Modul erweitert Peak_Trade um professionelle HTML-Reports für
Experiment- und Sweep-Ergebnisse. Es baut auf dem Experiment Explorer (Phase 22) auf
und bietet:

- **HTML-Experiment-Reports**: Detaillierte Berichte für einzelne Backtest-Runs
- **HTML-Sweep-Reports**: Aggregierte Übersichten für Hyperparameter-Sweeps
- **CLI-Tools**: Einfache Kommandozeilen-Werkzeuge für Report-Generierung
- **Inline-Visualisierungen**: Equity-Kurven, Drawdown-Charts, Metrik-Verteilungen

---

## Architektur

### Neue Komponenten

| Datei | Beschreibung |
|-------|-------------|
| `src/reporting/html_reports.py` | Core-Modul für HTML-Report-Generierung |
| `scripts/report_experiment.py` | CLI-Tool für Experiment-Reports |
| `scripts/report_sweep.py` | CLI-Tool für Sweep-Reports |
| `docs/REPORTING_V2.md` | Diese Dokumentation |
| `tests/test_reporting_v2.py` | Unit-Tests für Reporting v2 |

### Integration in bestehende Architektur

```
┌─────────────────────────────────────────────────────────────┐
│                    Peak_Trade                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐    ┌─────────────────┐                │
│  │ Backtest Engine │    │  Sweep Engine   │                │
│  │   (Phase 1-17)  │    │   (Phase 20)    │                │
│  └────────┬────────┘    └────────┬────────┘                │
│           │                      │                          │
│           ▼                      ▼                          │
│  ┌─────────────────────────────────────────┐               │
│  │        Experiment Registry              │               │
│  │      src/core/experiments.py            │               │
│  └────────────────────┬────────────────────┘               │
│                       │                                     │
│                       ▼                                     │
│  ┌─────────────────────────────────────────┐               │
│  │        Experiment Explorer              │ ◄── Phase 22  │
│  │      src/analytics/explorer.py          │               │
│  └────────────────────┬────────────────────┘               │
│                       │                                     │
│                       ▼                                     │
│  ┌─────────────────────────────────────────┐               │
│  │        Reporting v2                     │ ◄── Phase 21  │
│  │      src/reporting/html_reports.py      │               │
│  │                                         │               │
│  │  - ReportFigure, ReportTable            │               │
│  │  - ReportSection, HtmlReport            │               │
│  │  - HtmlReportBuilder                    │               │
│  │  - Plot-Funktionen                      │               │
│  └─────────────────────────────────────────┘               │
│                       │                                     │
│                       ▼                                     │
│  ┌─────────────────────────────────────────┐               │
│  │    CLI-Tools                            │               │
│  │  - report_experiment.py                 │               │
│  │  - report_sweep.py                      │               │
│  └─────────────────────────────────────────┘               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Quickstart

### 1. Experiment-Report generieren

```bash
# Report für ein einzelnes Experiment
python3 scripts/report_experiment.py --id abc12345-6789-...

# Report im Browser öffnen
python3 scripts/report_experiment.py --id abc12345 --open

# Nur Text-Summary (kein HTML)
python3 scripts/report_experiment.py --id abc12345 --text-only
```

### 2. Sweep-Report generieren

```bash
# Verfügbare Sweeps auflisten
python3 scripts/report_sweep.py --list-sweeps

# Sweep-Report generieren
python3 scripts/report_sweep.py --sweep-name ma_crossover_opt_v1

# Mit spezifischer Metrik und Top-N
python3 scripts/report_sweep.py --sweep-name ma_opt_v1 --metric sharpe --top-n 20

# Report im Browser öffnen
python3 scripts/report_sweep.py --sweep-name ma_opt_v1 --open
```

### 3. Programmatische Nutzung

```python
from src.analytics.explorer import ExperimentExplorer
from src.reporting.html_reports import HtmlReportBuilder

# Explorer und Builder initialisieren
explorer = ExperimentExplorer()
builder = HtmlReportBuilder(output_dir=Path("reports"))

# Experiment-Report
summary = explorer.get_experiment_details("abc12345-...")
report_path = builder.build_experiment_report(summary)
print(f"Report: {report_path}")

# Sweep-Report
overview = explorer.summarize_sweep("ma_crossover_opt_v1", metric="sharpe", top_n=20)
report_path = builder.build_sweep_report(overview, overview.best_runs, metric="sharpe")
print(f"Report: {report_path}")
```

---

## API-Referenz

### Dataclasses

#### ReportFigure

Repräsentiert eine Abbildung im Report:

```python
@dataclass
class ReportFigure:
    title: str                          # Titel der Abbildung
    description: Optional[str] = None   # Optionale Beschreibung
    image_path: str = ""                # Pfad zur Bilddatei
```

#### ReportTable

Repräsentiert eine Tabelle im Report:

```python
@dataclass
class ReportTable:
    title: str                          # Titel der Tabelle
    description: Optional[str] = None   # Optionale Beschreibung
    headers: List[str]                  # Spaltenüberschriften
    rows: List[List[str]]               # Tabellenzeilen
```

#### ReportSection

Eine Sektion des Reports:

```python
@dataclass
class ReportSection:
    title: str                          # Sektionstitel
    description: Optional[str] = None   # Optionale Beschreibung
    figures: List[ReportFigure]         # Abbildungen in dieser Sektion
    tables: List[ReportTable]           # Tabellen in dieser Sektion
    extra_html: Optional[str] = None    # Zusätzliches HTML
```

#### HtmlReport

Der vollständige Report:

```python
@dataclass
class HtmlReport:
    title: str                          # Report-Titel
    experiment_id: Optional[str]        # Experiment-ID (bei Experiment-Reports)
    sweep_name: Optional[str]           # Sweep-Name (bei Sweep-Reports)
    created_at: datetime                # Erstellungszeitpunkt
    sections: List[ReportSection]       # Report-Sektionen
    metadata: Dict[str, Any]            # Zusätzliche Metadaten
```

### HtmlReportBuilder

Die Hauptklasse für Report-Generierung:

```python
class HtmlReportBuilder:
    def __init__(self, output_dir: Path = Path("reports")):
        """Initialisiert den Builder mit Output-Verzeichnis."""

    def build_experiment_report(
        self,
        summary: ExperimentSummary,
        equity_curve: Optional[pd.DataFrame] = None,
        extra_sections: Optional[List[ReportSection]] = None,
    ) -> Path:
        """Generiert HTML-Report für ein Experiment."""

    def build_sweep_report(
        self,
        overview: SweepOverview,
        top_runs: List[RankedExperiment],
        metric: str = "sharpe",
        extra_sections: Optional[List[ReportSection]] = None,
    ) -> Path:
        """Generiert HTML-Report für einen Sweep."""
```

### Plot-Funktionen

```python
def plot_equity_curve(
    equity: pd.DataFrame,
    output_path: Path,
    title: str = "Equity Curve",
) -> None:
    """Erstellt Equity-Kurven-Plot."""

def plot_drawdown(
    equity: pd.DataFrame,
    output_path: Path,
    title: str = "Drawdown",
) -> None:
    """Erstellt Drawdown-Plot."""

def plot_metric_distribution(
    values: List[float],
    output_path: Path,
    metric_name: str = "Metric",
    title: Optional[str] = None,
) -> None:
    """Erstellt Histogramm für Metrik-Verteilung."""

def plot_sweep_scatter(
    runs: List[RankedExperiment],
    x_metric: str,
    y_metric: str,
    output_path: Path,
    title: Optional[str] = None,
) -> None:
    """Erstellt Scatter-Plot für zwei Metriken."""
```

### Convenience-Funktionen

```python
def build_quick_experiment_report(
    experiment_id: str,
    output_dir: Path = Path("reports"),
) -> Optional[Path]:
    """Schnelle Report-Generierung für ein Experiment."""

def build_quick_sweep_report(
    sweep_name: str,
    metric: str = "sharpe",
    top_n: int = 20,
    output_dir: Path = Path("reports"),
) -> Optional[Path]:
    """Schnelle Report-Generierung für einen Sweep."""
```

---

## Report-Inhalte

### Experiment-Report

Ein typischer Experiment-Report enthält:

1. **Header**
   - Report-Titel mit Experiment-ID
   - Erstellungszeitpunkt
   - Strategie-Name und Symbol

2. **Overview-Sektion**
   - Run-ID, Run-Type, Run-Name
   - Strategie, Symbol, Erstellungsdatum
   - Sweep-Zugehörigkeit (falls Teil eines Sweeps)
   - Tags

3. **Metrics-Sektion**
   - Total Return, Sharpe Ratio, Max Drawdown
   - CAGR, Sortino, Calmar
   - Win Rate, Profit Factor, Total Trades

4. **Parameters-Sektion**
   - Alle Strategie-Parameter als Tabelle

5. **Charts-Sektion** (optional)
   - Equity-Kurve
   - Drawdown-Chart

### Sweep-Report

Ein typischer Sweep-Report enthält:

1. **Header**
   - Report-Titel mit Sweep-Name
   - Erstellungszeitpunkt
   - Strategie-Key

2. **Overview-Sektion**
   - Sweep-Name, Strategie
   - Anzahl Runs

3. **Metric Statistics-Sektion**
   - Min, Max, Mean, Median, Std Dev für Ranking-Metrik

4. **Parameter Ranges-Sektion**
   - Wertebereiche pro Parameter
   - Anzahl distinkte Werte

5. **Top Runs-Sektion**
   - Ranking-Tabelle mit Top-N Runs
   - Sortiert nach gewählter Metrik
   - Zeigt Return, Max Drawdown, wichtigste Parameter

6. **Charts-Sektion** (optional)
   - Metrik-Verteilung (Histogramm)
   - Scatter-Plot (z.B. Sharpe vs. Return)

---

## CLI-Referenz

### report_experiment.py

```
usage: report_experiment.py [-h] --id ID [--out-dir OUT_DIR] [--open]
                            [--text-only] [--no-charts]

Peak_Trade: Generiert HTML-Report für ein Experiment.

required arguments:
  --id ID              Run-ID des Experiments (UUID)

optional arguments:
  --out-dir OUT_DIR    Output-Verzeichnis für den Report (default: reports)
  --open               Report nach Generierung im Browser öffnen
  --text-only          Nur Text-Summary ausgeben, kein HTML generieren
  --no-charts          Report ohne Charts generieren
```

### report_sweep.py

```
usage: report_sweep.py [-h] [--sweep-name SWEEP_NAME] [--metric METRIC]
                       [--top-n TOP_N] [--out-dir OUT_DIR] [--open]
                       [--text-only] [--list-sweeps] [--no-charts]

Peak_Trade: Generiert HTML-Report für einen Sweep.

optional arguments:
  --sweep-name NAME    Name des Sweeps
  --metric METRIC      Metrik für Ranking (default: sharpe)
  --top-n TOP_N        Anzahl Top-Runs im Report (default: 20)
  --out-dir OUT_DIR    Output-Verzeichnis (default: reports)
  --open               Report im Browser öffnen
  --text-only          Nur Text-Summary ohne HTML
  --list-sweeps        Alle verfügbaren Sweeps auflisten
  --no-charts          Report ohne Charts generieren
```

---

## Typische Workflows

### Workflow 1: Einzelnes Experiment analysieren

```bash
# 1. Experiment-ID finden
python3 scripts/experiments_explorer.py list --strategy ma_crossover --limit 10

# 2. Report generieren
python3 scripts/report_experiment.py --id abc12345-6789-... --open

# 3. Report liegt in reports/experiment_abc12345_YYYYMMDD_HHMMSS.html
```

### Workflow 2: Sweep auswerten

```bash
# 1. Sweep durchführen (Phase 20)
python3 scripts/run_sweep_strategy.py --strategy ma_crossover --config config/sweeps/ma_crossover.toml

# 2. Sweep-Report generieren
python3 scripts/report_sweep.py --sweep-name ma_crossover_opt_v1 --metric sharpe --open

# 3. Report zeigt Top-20 Parameterkombinationen
```

### Workflow 3: Vergleich mehrerer Sweeps

```bash
# 1. Reports für verschiedene Sweeps generieren
python3 scripts/report_sweep.py --sweep-name ma_crossover_v1 --metric sharpe
python3 scripts/report_sweep.py --sweep-name rsi_reversion_v1 --metric sharpe
python3 scripts/report_sweep.py --sweep-name trend_following_v1 --metric sharpe

# 2. Ergebnisse vergleichen (Phase 22 Explorer)
python3 scripts/experiments_explorer.py compare \
    --sweeps ma_crossover_v1,rsi_reversion_v1,trend_following_v1 \
    --metric sharpe
```

### Workflow 4: Programmatische Report-Generierung

```python
from pathlib import Path
from src.reporting import build_quick_experiment_report, build_quick_sweep_report

# Experiment-Report
path = build_quick_experiment_report("abc12345-...", output_dir=Path("reports/custom"))
if path:
    print(f"Experiment report: {path}")

# Sweep-Report
path = build_quick_sweep_report("ma_crossover_opt_v1", metric="sharpe", top_n=15)
if path:
    print(f"Sweep report: {path}")
```

---

## Best Practices

### 1. Report-Verzeichnis organisieren

```
reports/
├── experiments/           # Automatisch von Registry genutzt
│   └── experiments.csv
├── experiment_*.html      # Experiment-Reports
├── sweep_*.html           # Sweep-Reports
└── custom/                # Benutzerdefinierte Reports
```

### 2. Metriken für Ranking wählen

| Metrik | Verwendung |
|--------|-----------|
| `sharpe` | Standard für risikoadjustierte Performance |
| `total_return` | Absolute Rendite priorisieren |
| `max_drawdown` | Risiko-fokussierte Analyse (mit `--ascending`) |
| `sortino` | Downside-risikoadjustierte Performance |
| `calmar` | Rendite relativ zu Max Drawdown |

### 3. Top-N anpassen

```bash
# Für schnelle Übersicht
python3 scripts/report_sweep.py --sweep-name my_sweep --top-n 5

# Für detaillierte Analyse
python3 scripts/report_sweep.py --sweep-name my_sweep --top-n 50
```

### 4. Text-Only für Scripts

```bash
# In Automatisierung: Nur Text-Output
python3 scripts/report_experiment.py --id abc12345 --text-only | grep "Sharpe"

# Für interaktive Arbeit: HTML mit Browser
python3 scripts/report_experiment.py --id abc12345 --open
```

---

## Grenzen & Safety

### Read-Only

Das Reporting-Modul arbeitet **rein lesend**:

- Keine Schreiboperationen auf der Experiment-Registry
- Keine Order-/Trade-Aktivierung
- Kein Einfluss auf Live-Trading-Path

### Keine Live-Funktionalität

- Kein Zugriff auf Live-/Testnet-Executors
- Keine Änderungen an TradingEnvironment oder SafetyGuard
- Reine Analyse- und Reporting-Phase

### Abhängigkeiten

- **Matplotlib**: Für Plot-Generierung (optional via `--no-charts`)
- **Pandas**: Für Datenverarbeitung
- **Explorer (Phase 22)**: Für Daten-Zugriff

---

## Troubleshooting

### "Keine Experiment-Registry gefunden"

Die CSV-Datei existiert nicht:

```bash
# Prüfen
ls reports/experiments/experiments.csv

# Falls nicht vorhanden: Backtest durchführen
python3 scripts/run_backtest.py --strategy ma_crossover
```

### "Experiment nicht gefunden"

Die Run-ID existiert nicht oder ist falsch:

```bash
# Verfügbare Experimente listen
python3 scripts/experiments_explorer.py list --limit 20

# Mit korrekter ID erneut versuchen
python3 scripts/report_experiment.py --id KORREKTE_ID
```

### "Sweep nicht gefunden"

Der angegebene Sweep-Name existiert nicht:

```bash
# Alle Sweeps listen
python3 scripts/report_sweep.py --list-sweeps

# Mit korrektem Namen erneut versuchen
python3 scripts/report_sweep.py --sweep-name KORREKTER_NAME
```

### Plot-Fehler

Falls Matplotlib-Probleme auftreten:

```bash
# Report ohne Charts generieren
python3 scripts/report_experiment.py --id abc12345 --no-charts
python3 scripts/report_sweep.py --sweep-name my_sweep --no-charts
```

---

## Changelog

### Phase 21 (2024-12)

- Initiale Implementierung von Reporting v2
- `src/reporting/html_reports.py` mit HtmlReportBuilder
- Plot-Funktionen für Equity, Drawdown, Verteilungen
- CLI-Tools: `report_experiment.py`, `report_sweep.py`
- Inline CSS für selbständige HTML-Reports
- Integration mit Experiment Explorer (Phase 22)
- Dokumentation und Tests
