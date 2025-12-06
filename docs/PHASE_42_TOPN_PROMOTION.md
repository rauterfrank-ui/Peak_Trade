# Phase 42 – Top-N Promotion Pipeline

## Überblick

Phase 42 implementiert eine automatische Pipeline zur Auswahl und Export der besten Konfigurationen aus Strategy-Sweep-Ergebnissen. Die Top-N Kandidaten werden in einem strukturierten TOML-Format exportiert, das direkt für weitere Analysen, Portfolio-Integration oder Live-Deployment verwendet werden kann.

---

## Komponenten

### 1. Core-Modul

**Datei:** `src/experiments/topn_promotion.py`

| Komponente | Beschreibung |
|------------|--------------|
| `TopNPromotionConfig` | Dataclass für Konfiguration (sweep_name, metric, top_n, paths) |
| `find_sweep_results()` | Sucht neueste Ergebnis-Datei für einen Sweep |
| `load_sweep_results()` | Lädt CSV/Parquet Sweep-Ergebnisse |
| `select_top_n()` | Wählt Top-N nach Metrik (mit Fallback) |
| `export_top_n()` | Exportiert in TOML-Format |

### 2. CLI-Script

**Datei:** `scripts/promote_sweep_topn.py`

```bash
python scripts/promote_sweep_topn.py --sweep-name rsi_reversion_basic
```

---

## Verwendung

### CLI

```bash
# Standard: Top-5 nach Sharpe-Ratio
python scripts/promote_sweep_topn.py --sweep-name rsi_reversion_basic

# Top-10 nach Total Return
python scripts/promote_sweep_topn.py \
    --sweep-name breakout_basic \
    --metric metric_total_return \
    --top-n 10

# Mit explizitem Fallback
python scripts/promote_sweep_topn.py \
    --sweep-name ma_crossover_basic \
    --metric metric_sharpe_ratio \
    --fallback-metric metric_total_return \
    --top-n 5

# Custom Output-Verzeichnis
python scripts/promote_sweep_topn.py \
    --sweep-name rsi_reversion_basic \
    --output custom/output/dir \
    --experiments-dir custom/experiments/dir
```

### Programmatisch

```python
from pathlib import Path
from src.experiments.topn_promotion import (
    TopNPromotionConfig,
    load_sweep_results,
    select_top_n,
    export_top_n,
)

# Konfiguration
config = TopNPromotionConfig(
    sweep_name="rsi_reversion_basic",
    metric_primary="metric_sharpe_ratio",
    metric_fallback="metric_total_return",
    top_n=5,
    output_path=Path("reports/sweeps"),
    experiments_dir=Path("reports/experiments"),
)

# Pipeline ausführen
df = load_sweep_results(config)
df_top, metric_used = select_top_n(df, config)
output_path = export_top_n(df_top, config)

print(f"Top-N exportiert: {output_path}")
```

---

## Output-Format (TOML)

**Datei:** `reports/sweeps/{sweep_name}_top_candidates.toml`

```toml
[meta]
sweep_name = "rsi_reversion_basic"
metric_used = "metric_sharpe_ratio"
top_n = 5
generated_at = "2025-12-07T00:11:24.834498"

[[candidates]]
rank = 1
experiment_id = "abc123def456"
sharpe_ratio = 1.85
total_return = 0.152
max_drawdown = -0.038
win_rate = 0.58

[candidates.params]
rsi_period = 14
oversold_level = 25
overbought_level = 75

[[candidates]]
rank = 2
# ... weitere Kandidaten
```

---

## CLI-Argumente

| Argument | Kurz | Default | Beschreibung |
|----------|------|---------|--------------|
| `--sweep-name` | `-s` | (required) | Name des Sweeps |
| `--metric` | `-m` | `metric_sharpe_ratio` | Primäre Sortier-Metrik |
| `--fallback-metric` | `-f` | `metric_total_return` | Fallback wenn primary fehlt |
| `--top-n` | `-n` | `5` | Anzahl Top-Kandidaten |
| `--output` | `-o` | `reports/sweeps` | Output-Verzeichnis |
| `--experiments-dir` | `-e` | `reports/experiments` | Ergebnis-Verzeichnis |
| `--verbose` | `-v` | `False` | Debug-Output |

---

## Technische Details

### Metrik-Fallback-Logik

1. Versucht primäre Metrik (`metric_sharpe_ratio`)
2. Fallback auf sekundäre Metrik (`metric_total_return`)
3. Bei beiden fehlend: Error mit Liste verfügbarer Metriken

### NaN-Handling

- Zeilen mit NaN in der Sortier-Metrik werden gefiltert
- Error wenn alle Werte NaN sind

### Datei-Suche

1. Sucht nach `*{sweep_name}*.csv`
2. Fallback auf `*{sweep_name}*.parquet`
3. Fallback auf Strategy-Name (ohne Suffix wie `_basic`)
4. Nimmt immer die neueste Datei (nach Modification Time)

---

## Tests

```bash
# Phase 42 Tests
.venv/bin/pytest tests/test_topn_promotion.py -v
```

**19 Tests** in 5 Kategorien:
- `TestTopNPromotionConfig` (3 Tests)
- `TestSelectTopN` (5 Tests)
- `TestExportTopN` (3 Tests)
- `TestFindSweepResults` (5 Tests)
- `TestLoadSweepResults` (3 Tests)

---

## Workflow-Integration

```
[Sweep ausführen]              [Top-N promoten]              [Kandidaten nutzen]
        │                              │                              │
        ▼                              ▼                              ▼
run_strategy_sweep.py  ─────►  promote_sweep_topn.py  ─────►  _top_candidates.toml
        │                              │                              │
        ▼                              ▼                              ▼
reports/experiments/           reports/sweeps/               Portfolio-Track
   *.csv / *.parquet              *.toml                     Live-Config
```

---

## Beispiel-Output

```
======================================================================
Top-N Promotion Summary
======================================================================
Sweep:           rsi_reversion_basic
Metric:          metric_total_return
Top N:           5
Output:          reports/sweeps/rsi_reversion_basic_top_candidates.toml

Top Konfigurationen:
----------------------------------------------------------------------
Rank            total_ret   Return  Params
----------------------------------------------------------------------
1               -0.0309    -3.09%  rsi_period=7, oversold_level=20, overbought_level=70
2               -0.0309    -3.09%  rsi_period=7, oversold_level=20, overbought_level=75
3               -0.0309    -3.09%  rsi_period=7, oversold_level=20, overbought_level=80
4               -0.0309    -3.09%  rsi_period=7, oversold_level=25, overbought_level=70
5               -0.0309    -3.09%  rsi_period=7, oversold_level=25, overbought_level=75
======================================================================

Top-N Kandidaten exportiert: reports/sweeps/rsi_reversion_basic_top_candidates.toml
```

---

## Siehe auch

- [Phase 41 – Strategy Sweeps](PHASE_41_STRATEGY_SWEEPS_AND_RESEARCH_PLAYGROUND.md)
- [Phase 43 – Sweep Visualization](PHASE_43_SWEEP_VISUALIZATION.md)
- [Strategy Library Overview](PHASE_40_STRATEGY_LIBRARY_OVERVIEW.md)
