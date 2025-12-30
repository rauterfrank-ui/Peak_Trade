# Evidence Chain Integration Guide

**Version:** 1.0
**Last Updated:** 2025-12-18
**Status:** Production

## Overview

The Evidence Chain module (`src/experiments/evidence_chain.py`) creates standardized, reproducible artifacts for every research and backtest run in Peak_Trade. This document explains what the Evidence Chain produces, where output lives, and how it integrates with the broader reporting ecosystem.

## What Evidence Chain Produces

### Artifact Structure

Each run creates a timestamped directory under `results/<run_id>/` with standardized files:

```
results/<run_id>/
├── config_snapshot.json    # Meta + Params
├── stats.json              # Performance metrics
├── equity.csv              # Equity curve (timestamp, equity)
├── trades.parquet          # Optional: trade log (if parquet engine available)
├── report_snippet.md       # Markdown summary
└── report/                 # Optional: rendered reports (if Quarto enabled)
    └── backtest.html       # HTML report with visualizations
```

### Core Artifacts (Always Created)

| File | Content | Format | Purpose |
|------|---------|--------|---------|
| `config_snapshot.json` | Run metadata + strategy parameters | JSON | Reproducibility: captures exact run configuration |
| `stats.json` | Performance metrics (Sharpe, max DD, win rate, etc.) | JSON | Quick access to key metrics for analysis |
| `equity.csv` | Equity curve timeseries | CSV | Lightweight format for plotting/analysis |
| `report_snippet.md` | Human-readable summary | Markdown | Can be included in larger reports |

### Optional Artifacts (Graceful Degradation)

| File | Requires | Fallback Behavior |
|------|----------|-------------------|
| `trades.parquet` | `pyarrow` or `fastparquet` | Silently skipped if parquet engine unavailable |
| `report/backtest.html` | `quarto` CLI tool | Warning logged, report skipped |

## Where Output Lives

### Results Directory (gitignored)

All Evidence Chain output goes to `results/` (gitignored by default):

```bash
results/
├── 20241218_143022_abc123/    # Auto-generated run ID
├── exp_ma_v2_001/              # Custom run ID
└── backtest_rsi_btc/           # Another custom run ID
```

**Key Points:**
- `results/` is in `.gitignore` – never tracked in version control
- Each run is isolated in its own directory
- Run IDs can be auto-generated (timestamp + short hash) or user-specified
- Artifacts are immutable once written (no overwriting)

### Templates Directory (tracked)

Quarto report templates live in `templates/quarto/` (version-controlled):

```bash
templates/quarto/
├── backtest_report.qmd         # Main backtest report template
└── smoke.qmd                   # Smoke test template
```

**Key Points:**
- Templates are tracked in git (policy-compliant)
- Templates use `execute: enabled: false` (no code execution during rendering)
- Templates load pre-computed data from `results/<run_id>/`
- Rendered output goes to `results/<run_id>/report/` (gitignored)

## Integration with Existing Reporting Ecosystem

### src/reporting/ Modules

Evidence Chain **complements** (not replaces) the existing `src/reporting/` modules:

| Module | Purpose | Evidence Chain Integration |
|--------|---------|---------------------------|
| `src/reporting/backtest_report.py` | Generate backtest stats/plots | Evidence Chain calls this to populate `stats.json` |
| `src/reporting/plots.py` | Create equity/drawdown plots | Quarto templates use these plots via `src/reporting/` |
| `src/reporting/execution_reports.py` | Trade execution analysis | Future: `trades.parquet` can feed into this |
| `src/reporting/live_status_report.py` | Live session monitoring | Independent (not affected by Evidence Chain) |

**Design Principle:** Evidence Chain is a **thin artifact layer** that captures output from existing reporting modules. It does not replace or duplicate `src/reporting/` logic.

### Quarto Templates

Quarto templates (`templates/quarto/`) render Evidence Chain artifacts into HTML reports:

**Flow:**
1. Runner (e.g., `run_backtest.py`) calls Evidence Chain functions
2. Evidence Chain writes artifacts to `results/<run_id>/`
3. (Optional) Runner calls `scripts/render_last_report.sh`
4. Quarto loads artifacts from `results/<run_id>/` and renders HTML
5. HTML output written to `results/<run_id>/report/backtest.html`

**Template Features:**
- `execute: enabled: false` – No Python execution, only data loading
- `embed-resources: true` – Self-contained HTML (no external deps)
- Loads JSON/CSV directly from `../` relative path
- Uses `src/reporting/plots.py` for visualizations (via pre-generated images)

### CI Guards

CI ensures Evidence Chain output never leaks into version control:

| Guard | Location | Purpose |
|-------|----------|---------|
| `.gitignore` | Root | Ignores `results/`, `reports/`, `*.html` |
| Pre-commit hook | `scripts/ci/validate_git_state.sh` | Blocks commits with generated files |
| GitHub Action | `.github/workflows/test.yml` | Verifies no tracked reports in PR diffs |

## Optional Dependencies Behavior

### Without MLflow

**Behavior:**
- `get_optional_tracker()` returns `NullTracker` (no-op implementation)
- All tracker calls (`log_params`, `log_metrics`, etc.) silently succeed
- No MLflow UI, but artifacts still created

**Use Case:** Lightweight runs, CI environments, users who don't need MLflow

### Without Quarto

**Behavior:**
- Report rendering step logs warning: `[WARN] quarto not installed, skipping report`
- All other artifacts created normally
- User can manually render later after installing Quarto

**Use Case:** Fast iteration, batch jobs, environments without Quarto

### Without Parquet Engine

**Behavior:**
- `write_trades_parquet_optional()` returns `None`
- No `trades.parquet` file created
- All other artifacts created normally

**Use Case:** Minimal Python environments, users who only need CSV output

## Usage Patterns

### Pattern 1: Full Evidence Chain (Backtest Runner)

```python
from src.experiments.evidence_chain import (
    ensure_run_dir,
    write_config_snapshot,
    write_stats_json,
    write_equity_csv,
    write_trades_parquet_optional,
    write_report_snippet_md,
)

# Setup
run_id = generate_run_id()
run_dir = ensure_run_dir(run_id)

# After backtest completes
write_config_snapshot(run_dir, meta, params)
write_stats_json(run_dir, result.stats)
write_equity_csv(run_dir, result.equity_curve)
write_trades_parquet_optional(run_dir, result.trades)
write_report_snippet_md(run_dir, summary)

# Optional: Render report
if not args.no_report:
    render_quarto_report(run_id)
```

### Pattern 2: Minimal Evidence Chain (Research CLI)

```python
from src.experiments.evidence_chain import (
    ensure_run_dir,
    write_minimal_evidence_chain,
)

# Quick research run
run_dir = ensure_run_dir(run_id)
meta = {"run_id": run_id, "stage": "research", "strategy": "ma_crossover"}
stats = {"sharpe": 1.5, "max_dd": -0.12}

write_minimal_evidence_chain(run_dir, meta, stats)
# Creates: config_snapshot.json, stats.json, report_snippet.md
```

### Pattern 3: Batch Processing (No Reports)

```bash
# Run multiple backtests without reports
for strategy in ma_crossover rsi breakout; do
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

## Troubleshooting

### Problem: Report rendering fails

**Symptom:**
```
[WARN] quarto is not installed or not in PATH
```

**Solutions:**
1. Install Quarto: https://quarto.org/docs/get-started/
2. Or skip report: `python scripts/run_backtest.py --no-report`
3. Or render later: `bash scripts/render_last_report.sh <run_id>`

### Problem: trades.parquet not created

**Symptom:**
```
⊘ trades.parquet (skipped)
```

**Cause:** No parquet engine installed

**Solutions:**
1. Install pyarrow: `pip install pyarrow`
2. Or accept CSV-only workflow (no action needed)

### Problem: MLflow UI shows no runs

**Cause:** MLflow not configured or `--tracker null` used

**Solutions:**
1. Check MLflow setup: `mlflow ui` (should start server)
2. Verify tracker mode: `python scripts/run_backtest.py --tracker auto`
3. Or accept local artifacts only (no MLflow needed for reproducibility)

## Best Practices

### 1. Always Use Meaningful Run IDs

```bash
# Good
python scripts/run_backtest.py --run-id exp_ma_v2_btc_2024q4

# Auto-generated (OK for quick tests)
python scripts/run_backtest.py
# Creates: results/20241218_143022_abc123/
```

### 2. Keep Evidence Chain Enabled

Don't disable artifact creation – costs are minimal, benefits huge:
- Disk space: ~100KB per run (JSON/CSV)
- Runtime overhead: <100ms per run
- Reproducibility value: Priceless

### 3. Sync results/ for Team Sharing

```bash
# Option 1: Cloud sync
aws s3 sync results/ s3://my-bucket/peak-trade-results/

# Option 2: Git LFS (for small teams)
git lfs track "results/**/*.parquet"
git add .gitattributes results/
```

### 4. Use Git SHA for Reproducibility

Evidence Chain automatically captures git SHA in `config_snapshot.json`:

```json
{
  "meta": {
    "run_id": "exp_ma_v2_001",
    "git_sha": "312b0fea6e0eb2ccb14dcda9646e1b633f3d948e",
    "timestamp": "2024-12-18T14:30:22Z"
  }
}
```

This links every run to the exact code version.

## Migration Guide

### From Manual Results Tracking

**Before:**
```python
# Old code (manual CSV writes)
with open(f"results_{strategy}_{date}.csv", "w") as f:
    writer = csv.writer(f)
    writer.writerows(equity_data)
```

**After:**
```python
# New code (Evidence Chain)
from src.experiments.evidence_chain import ensure_run_dir, write_equity_csv

run_dir = ensure_run_dir(f"{strategy}_{date}")
write_equity_csv(run_dir, equity_data)
```

**Benefits:**
- Standardized directory structure
- Automatic metadata capture
- No path manipulation errors

### From Custom Report Generators

**Before:**
```python
# Old code (custom HTML generation)
html = f"<html><body><h1>{strategy}</h1>..."
with open(f"report_{run_id}.html", "w") as f:
    f.write(html)
```

**After:**
```python
# New code (Quarto templates)
write_minimal_evidence_chain(run_dir, meta, stats)
# Optionally: bash scripts/render_last_report.sh
```

**Benefits:**
- Professional templates with visualizations
- Separation of data and presentation
- Easier to maintain and extend

## Next Steps

- 📖 Read [REPORTING_QUICKSTART.md](./REPORTING_QUICKSTART.md) for CLI examples
- 🧪 Check [tests/test_evidence_chain.py](../../tests/test_evidence_chain.py) for API usage
- 📊 Customize [templates/quarto/backtest_report.qmd](../../templates/quarto/backtest_report.qmd)
- 🏗️ See [ADR_0001_Peak_Tool_Stack.md](../adr/ADR_0001_Peak_Tool_Stack.md) for architecture decisions
