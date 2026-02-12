# Peak_Trade Experiment & Metrics Explorer

## Phase 22 – Übersicht

Der **Experiment Explorer** ist ein zentrales Werkzeug zum Durchsuchen, Filtern und Analysieren
aller Experiment-Runs in der Peak_Trade Registry. Er baut auf der bestehenden Infrastruktur
(Phase 18 Research-Playground, Phase 20 Hyperparameter-Sweeps) auf und ermöglicht:

- **Filtern** von Experimenten nach Run-Type, Strategie, Tags, Sweep-Name, Zeitraum
- **Ranking** nach beliebigen Metriken (Sharpe, Return, Drawdown, etc.)
- **Sweep-Auswertung** mit Top-N Parameterkombinationen und Statistiken
- **Export** in CSV und Markdown für Weiterverarbeitung

---

## Architektur

### Neue Komponenten

| Datei | Beschreibung |
|-------|-------------|
| `src/analytics/explorer.py` | Explorer-Modul mit Dataclasses und API |
| `scripts/experiments_explorer.py` | CLI-Tool mit Subcommands |
| `docs/EXPERIMENT_EXPLORER.md` | Diese Dokumentation |
| `tests/test_experiments_explorer.py` | Unit-Tests für Explorer |

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
│  │  (CSV: reports/experiments/experiments.csv)             │
│  └────────────────────┬────────────────────┘               │
│                       │                                     │
│                       ▼                                     │
│  ┌─────────────────────────────────────────┐               │
│  │        Experiment Explorer              │ ◄── Phase 22  │
│  │      src/analytics/explorer.py          │               │
│  │                                         │               │
│  │  - ExperimentFilter                     │               │
│  │  - ExperimentSummary                    │               │
│  │  - RankedExperiment                     │               │
│  │  - SweepOverview                        │               │
│  │  - ExperimentExplorer (Klasse)          │               │
│  └─────────────────────────────────────────┘               │
│                       │                                     │
│                       ▼                                     │
│  ┌─────────────────────────────────────────┐               │
│  │    CLI: experiments_explorer.py         │ ◄── Phase 22  │
│  │  (list, top, details, sweep-summary,    │               │
│  │   sweeps, compare, export)              │               │
│  └─────────────────────────────────────────┘               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## API-Referenz

### Dataclasses

#### ExperimentFilter

Filter-Kriterien für Experimente:

```python
@dataclass
class ExperimentFilter:
    run_types: Optional[List[str]] = None      # z.B. ["backtest", "sweep"]
    strategies: Optional[List[str]] = None     # z.B. ["ma_crossover"]
    tags: Optional[List[str]] = None           # z.B. ["dev-test"]
    sweep_names: Optional[List[str]] = None    # z.B. ["ma_opt_v1"]
    scan_names: Optional[List[str]] = None
    portfolios: Optional[List[str]] = None
    symbols: Optional[List[str]] = None        # z.B. ["BTC/EUR"]
    created_from: Optional[datetime] = None    # Zeitraum-Start
    created_to: Optional[datetime] = None      # Zeitraum-Ende
    limit: Optional[int] = None                # Max. Ergebnisse
```

#### ExperimentSummary

Zusammenfassung eines Experiments:

```python
@dataclass
class ExperimentSummary:
    experiment_id: str              # UUID
    run_type: str                   # backtest, sweep, etc.
    run_name: str
    strategy_name: Optional[str]
    sweep_name: Optional[str]
    symbol: Optional[str]
    tags: List[str]
    created_at: Optional[datetime]
    metrics: Dict[str, float]       # sharpe, total_return, max_drawdown, etc.
    params: Dict[str, Any]          # Strategie-Parameter
```

#### RankedExperiment

Experiment mit Ranking-Info:

```python
@dataclass
class RankedExperiment:
    summary: ExperimentSummary
    rank: int                       # 1-basiert
    sort_key: str                   # Metrik für Ranking
    sort_value: float               # Wert der Metrik
```

#### SweepOverview

Aggregierte Sweep-Übersicht:

```python
@dataclass
class SweepOverview:
    sweep_name: str
    strategy_key: str
    run_count: int
    best_runs: List[RankedExperiment]
    metric_stats: Dict[str, float]  # min, max, mean, std, median
    param_ranges: Dict[str, Dict]   # Wertebereiche pro Parameter
```

### ExperimentExplorer Klasse

```python
from src.analytics.explorer import ExperimentExplorer, ExperimentFilter

explorer = ExperimentExplorer()

# Experimente listen
flt = ExperimentFilter(run_types=["backtest"], strategies=["ma_crossover"])
experiments = explorer.list_experiments(flt)

# Ranking
top_sharpe = explorer.rank_experiments(flt, metric="sharpe", top_n=10)

# Sweep-Auswertung
overview = explorer.summarize_sweep("ma_crossover_opt_v1", metric="sharpe", top_n=10)

# Alle Sweeps listen
sweeps = explorer.list_sweeps()

# Sweeps vergleichen
comparisons = explorer.compare_sweeps(["sweep_a", "sweep_b"], metric="sharpe")

# Export
explorer.export_to_csv(flt, Path("out/export.csv"))
explorer.export_to_markdown(flt, Path("out/export.md"), metric="sharpe", top_n=20)
```

### Convenience-Funktionen

```python
from src.analytics.explorer import quick_list, quick_rank, quick_sweep_summary

# Schnelle Auflistung
experiments = quick_list(run_type="backtest", strategy="ma_crossover", limit=20)

# Schnelles Ranking
top = quick_rank(metric="sharpe", run_type="backtest", top_n=10)

# Schnelle Sweep-Summary
overview = quick_sweep_summary("my_sweep", metric="sharpe", top_n=10)
```

---

## CLI-Referenz

### Subcommands

| Command | Beschreibung |
|---------|-------------|
| `list` | Experimente auflisten mit Filtern |
| `top` | Top-N Experimente nach Metrik |
| `details` | Details zu einem einzelnen Experiment |
| `sweep-summary` | Übersicht für einen Sweep |
| `sweeps` | Alle verfügbaren Sweeps listen |
| `compare` | Mehrere Sweeps vergleichen |
| `export` | Export in CSV oder Markdown |

### Beispiele

#### 1. Experimente auflisten

```bash
# Alle Backtests der letzten 50
python3 scripts/experiments_explorer.py list --run-type backtest --limit 50

# Nur ma_crossover Strategie
python3 scripts/experiments_explorer.py list --strategy ma_crossover

# Mit Tag-Filter
python3 scripts/experiments_explorer.py list --tag dev-test

# Nach Sharpe sortiert
python3 scripts/experiments_explorer.py list --sort-by sharpe
```

#### 2. Top-N nach Metrik

```bash
# Top-10 nach Sharpe (alle Run-Types)
python3 scripts/experiments_explorer.py top --metric sharpe --top-n 10

# Top-10 Backtests nach Return
python3 scripts/experiments_explorer.py top --run-type backtest --metric total_return --top-n 10

# Top-10 mit niedrigstem Drawdown
python3 scripts/experiments_explorer.py top --metric max_drawdown --top-n 10 --ascending
```

#### 3. Experiment-Details

```bash
# Details zu einem Experiment anzeigen
python3 scripts/experiments_explorer.py details --id abc12345-6789-...
```

#### 4. Sweep-Auswertung

```bash
# Sweep-Übersicht mit Top-15 Runs
python3 scripts/experiments_explorer.py sweep-summary \
    --sweep-name ma_crossover_opt_v1 \
    --metric sharpe \
    --top-n 15

# Alle Sweeps listen
python3 scripts/experiments_explorer.py sweeps
```

#### 5. Sweep-Vergleich

```bash
# Zwei Sweeps vergleichen
python3 scripts/experiments_explorer.py compare \
    --sweeps ma_crossover_opt_v1,rsi_reversion_opt_v1 \
    --metric sharpe
```

#### 6. Export

```bash
# CSV-Export aller Sweeps
python3 scripts/experiments_explorer.py export \
    --run-type sweep \
    --metric sharpe \
    --csv out/all_sweeps.csv

# Markdown-Export für einen bestimmten Sweep
python3 scripts/experiments_explorer.py export \
    --sweep-name ma_crossover_opt_v1 \
    --metric sharpe \
    --markdown out/ma_sweep_report.md

# Beides gleichzeitig
python3 scripts/experiments_explorer.py export \
    --strategy my_strategy \
    --csv out/my_strategy.csv \
    --markdown out/my_strategy.md
```

---

## Typische Workflows

### Workflow 1: Nach Sweep die besten Parameter finden

```bash
# 1. Sweep durchführen (Phase 20)
python3 scripts/run_sweep_strategy.py --strategy ma_crossover --config config/sweeps/ma_crossover.toml

# 2. Sweep-Übersicht abrufen
python3 scripts/experiments_explorer.py sweep-summary \
    --sweep-name ma_crossover_opt_v1 \
    --metric sharpe \
    --top-n 10

# 3. Details zum besten Run
python3 scripts/experiments_explorer.py details --id <RUN_ID>

# 4. Export für weitere Analyse
python3 scripts/experiments_explorer.py export \
    --sweep-name ma_crossover_opt_v1 \
    --csv out/ma_sweep_results.csv
```

### Workflow 2: Backtest-Historie analysieren

```bash
# 1. Alle Backtests einer Strategie listen
python3 scripts/experiments_explorer.py list \
    --run-type backtest \
    --strategy trend_following \
    --limit 100

# 2. Top-20 nach Sharpe
python3 scripts/experiments_explorer.py top \
    --run-type backtest \
    --strategy trend_following \
    --metric sharpe \
    --top-n 20

# 3. Mit Tag für Zeitraum-Filter
python3 scripts/experiments_explorer.py list \
    --run-type backtest \
    --tag q4-2024
```

### Workflow 3: Strategien vergleichen

```bash
# 1. Alle Sweeps listen
python3 scripts/experiments_explorer.py sweeps

# 2. Sweeps verschiedener Strategien vergleichen
python3 scripts/experiments_explorer.py compare \
    --sweeps trend_following_v2,mean_reversion_v1,ma_crossover_v3 \
    --metric sharpe

# 3. Export für Präsentation
python3 scripts/experiments_explorer.py export \
    --run-type sweep \
    --markdown reports/strategy_comparison.md
```

---

## Integration mit anderen Tools

### Research-Playground (Phase 18)

Der Explorer ergänzt die Research-Scripts:

```bash
# Research-Script für neuen Backtest
python3 scripts/research_run_strategy.py --strategy ma_crossover --symbol BTC/EUR

# Explorer für Analyse der Ergebnisse
python3 scripts/experiments_explorer.py top --strategy ma_crossover --metric sharpe
```

### Hyperparameter-Sweeps (Phase 20)

Der Explorer ist das primäre Werkzeug zur Sweep-Auswertung:

```bash
# Sweep durchführen
python3 scripts/run_sweep_strategy.py --strategy my_strategy --config config/sweeps/my_strategy.toml

# Ergebnisse analysieren
python3 scripts/experiments_explorer.py sweep-summary --sweep-name my_strategy_opt_v1
```

### Notebooks & Excel

Exports für externe Analyse:

```bash
# CSV für Excel
python3 scripts/experiments_explorer.py export \
    --sweep-name my_sweep \
    --csv out/for_excel.csv

# Markdown für Dokumentation
python3 scripts/experiments_explorer.py export \
    --run-type backtest \
    --markdown reports/backtest_overview.md
```

---

## Grenzen & Safety

### Read-Only

Der Explorer arbeitet **rein lesend**:

- Keine Schreiboperationen auf der Registry
- Keine Order-/Trade-Aktivierung
- Kein Einfluss auf Live-Trading-Path

### Keine Live-Funktionalität

- Kein Zugriff auf Live-/Testnet-Executors
- Keine Änderungen an TradingEnvironment oder SafetyGuard
- Reine Analyse- und Reporting-Phase

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

### "Sweep nicht gefunden"

Der angegebene `sweep_name` existiert nicht:

```bash
# Alle Sweeps listen
python3 scripts/experiments_explorer.py sweeps

# Mit korrektem Namen erneut versuchen
python3 scripts/experiments_explorer.py sweep-summary --sweep-name RICHTIGER_NAME
```

### Leere Ergebnisse

Filter zu restriktiv:

```bash
# Ohne Filter testen
python3 scripts/experiments_explorer.py list --limit 10

# Filter schrittweise hinzufügen
python3 scripts/experiments_explorer.py list --run-type backtest
python3 scripts/experiments_explorer.py list --run-type backtest --strategy ma_crossover
```

---

## Changelog

### Phase 22 (2024-12)

- Initiale Implementierung des Experiment & Metrics Explorers
- `src/analytics/explorer.py` mit ExperimentExplorer Klasse
- `scripts/experiments_explorer.py` CLI-Tool
- Integration in bestehende Analytics-Module
- Dokumentation und Tests
