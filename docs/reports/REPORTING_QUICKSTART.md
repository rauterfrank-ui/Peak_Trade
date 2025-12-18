# Reporting Quickstart – P1 Evidence Chain

## Overview

Peak_Trade's **P1 Evidence Chain** creates standardized artifacts for every backtest/research run:

```
results/<run_id>/
├── config_snapshot.json    # Meta + Params
├── stats.json              # Performance metrics
├── equity.csv              # Equity curve (timestamp, equity)
├── trades.parquet          # Optional: trade log (wenn parquet engine verfügbar)
├── report_snippet.md       # Markdown summary
└── report/
    └── backtest.html       # Optional: rendered Quarto report
```

## Quick Start

### 1. Run a Backtest with Evidence Chain

```bash
# Basic run (auto-generates run_id)
python scripts/run_backtest.py --strategy ma_crossover

# With custom run_id
python scripts/run_backtest.py --strategy ma_crossover --run-id my_run_001

# Without Quarto report rendering
python scripts/run_backtest.py --strategy ma_crossover --no-report

# With null tracker (no mlflow)
python scripts/run_backtest.py --strategy ma_crossover --tracker null
```

### 2. View Artifacts

All artifacts are in `results/<run_id>/`:

```bash
# View config snapshot
cat results/<run_id>/config_snapshot.json | jq

# View stats
cat results/<run_id>/stats.json | jq

# View equity curve
head -20 results/<run_id>/equity.csv

# View report snippet
cat results/<run_id>/report_snippet.md
```

### 3. Render Quarto Report (Manual)

If you skipped the automatic report rendering (via `--no-report`), you can render it manually:

```bash
# Render latest run
bash scripts/render_last_report.sh

# Render specific run
bash scripts/render_last_report.sh <run_id>
```

Output: `results/<run_id>/report/backtest.html`

Open in browser:

```bash
open results/<run_id>/report/backtest.html
```

## Graceful Degradation

The Evidence Chain is designed to work without optional dependencies:

### Without MLflow

```bash
# No mlflow installed -> Uses NullTracker (no error)
python scripts/run_backtest.py --tracker auto

# Force null tracker
python scripts/run_backtest.py --tracker null
```

### Without Quarto

```bash
# quarto not installed -> WARN + skip report rendering (no error)
python scripts/run_backtest.py

# Explicitly skip report
python scripts/run_backtest.py --no-report
```

### Without Parquet Engine (pyarrow/fastparquet)

The `trades.parquet` file is optional and will be skipped if the parquet engine is not available. All other artifacts will still be created.

## CLI Arguments

### run_backtest.py

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--run-id` | str | auto-generated | Run-ID für Evidence Chain |
| `--results-dir` | str | `results` | Basis-Verzeichnis für Results |
| `--tracker` | str | `auto` | Tracker-Typ (auto, null, mlflow) |
| `--no-report` | flag | false | Quarto-Report-Rendering überspringen |

## Report Template

The Quarto report template is in `reports/quarto/backtest_report.qmd`.

**Key features:**

- `execute: enabled: false` – No code execution during rendering
- Loads pre-computed data from `_run/` directory
- Embedded resources (single HTML file)
- Includes equity curve visualization

## Customizing the Report

### Edit Template

Edit `reports/quarto/backtest_report.qmd` to customize:

- Sections
- Metrics display
- Visualizations
- Styling

### Re-render

```bash
bash scripts/render_last_report.sh <run_id>
```

## Integration with Other Runners

### research_cli.py (Minimal Evidence Chain)

The research_cli.py uses a minimal evidence chain (config + stats + snippet only):

```python
from src.experiments.evidence_chain import (
    ensure_run_dir,
    write_minimal_evidence_chain,
)

# In your runner
run_dir = ensure_run_dir(run_id)
meta = {"run_id": run_id, "stage": "research", ...}
stats = {"sharpe": 1.5, ...}
write_minimal_evidence_chain(run_dir, meta, stats)
```

### live_ops.py (Minimal Evidence Chain)

Similar to research_cli.py, live_ops.py can use the minimal evidence chain for tracking operations.

## Troubleshooting

### Report rendering fails

**Symptom:**
```
[WARN] quarto is not installed or not in PATH
```

**Solution:**
Install Quarto from https://quarto.org/docs/get-started/ or skip rendering with `--no-report`.

### trades.parquet not created

**Symptom:**
```
⊘ trades.parquet (skipped)
```

**Cause:** No parquet engine (pyarrow or fastparquet) installed.

**Solution (optional):**
```bash
pip install pyarrow
# or
pip install fastparquet
```

### MLflow tracker fails

**Symptom:**
```
⊘ Tracker failed (graceful degradation): No module named 'mlflow'
```

**Solution (if you want mlflow):**
```bash
pip install mlflow
```

**Or:** Use `--tracker null` to disable tracking.

## Best Practices

1. **Always keep Evidence Chain enabled** – Costs are minimal, benefits are huge for reproducibility
2. **Use meaningful run-ids** – Easier to find runs later (e.g., `--run-id exp_rsi_v2_20241215`)
3. **Don't skip reports** unless you have a good reason – HTML reports are great for sharing results
4. **Store results/ in version control** (optional) – Or sync to S3/cloud storage for team access
5. **Use git SHA in meta** – Automatically captured, helps link results to code versions

## Examples

### Example 1: Quick MA Crossover Test

```bash
python scripts/run_backtest.py \
  --strategy ma_crossover \
  --run-id quick_ma_test_001 \
  --bars 1000
```

Output:
```
results/quick_ma_test_001/
├── config_snapshot.json
├── stats.json
├── equity.csv
├── report_snippet.md
└── report/backtest.html
```

### Example 2: RSI Strategy with Real Data

```bash
python scripts/run_backtest.py \
  --strategy rsi_strategy \
  --data-file data/btc_eur_1h.csv \
  --start-date 2023-01-01 \
  --end-date 2023-12-31 \
  --run-id rsi_2023_full
```

### Example 3: Batch Testing (No Reports)

```bash
for strategy in ma_crossover rsi_strategy breakout; do
  python scripts/run_backtest.py \
    --strategy $strategy \
    --no-report \
    --run-id batch_${strategy}_$(date +%Y%m%d)
done

# Render all reports after batch completes
for run_dir in results/batch_*; do
  bash scripts/render_last_report.sh $(basename $run_dir)
done
```

## Next Steps

- 📖 Read [P1 Evidence Chain Spec](../../docs/stability/P1_EVIDENCE_CHAIN.md) for design details
- 🧪 Check [tests/test_evidence_chain.py](../../tests/test_evidence_chain.py) for usage examples
- 📊 Customize [reports/quarto/backtest_report.qmd](../../reports/quarto/backtest_report.qmd) for your needs
