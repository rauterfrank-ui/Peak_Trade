# Peak Trade Reporting Guide

This guide covers experiment tracking, run comparison, and report generation in Peak Trade.

## Overview

Peak Trade provides graceful, optional experiment tracking with:

- **Local-first**: Works without MLflow or network access
- **Stable contract**: JSON summary format for comparability
- **CLI tools**: Fast run comparison and diff
- **Quarto reports**: Generate HTML reports from run data

## Quick Start

### 1. Track an Experiment

```python
from experiments.tracking import PeakTradeRun

# Basic usage (local tracking only)
with PeakTradeRun(experiment_name="my_experiment") as run:
    run.log_param("fast_period", 10)
    run.log_param("slow_period", 20)

    # ... run your backtest ...

    run.log_metric("sharpe_ratio", 1.5)
    run.log_metric("total_return", 0.25)
    run.log_metric("max_drawdown", -0.12)

# Summary JSON written to: results/run_summary_<run_id>.json
```

### 2. Compare Recent Runs

```bash
# Compare latest 10 runs
python scripts/dev/compare_runs.py --n 10

# Compare specific runs
python scripts/dev/compare_runs.py \
    --baseline abc123 \
    --candidate def456

# Output as JSON
python scripts/dev/compare_runs.py --format json --n 5
```

### 3. Generate Report

```bash
# Install Quarto (if not already installed)
# macOS: brew install quarto
# Linux: https://quarto.org/docs/get-started/

# Generate HTML report
cd reports/quarto
quarto render backtest_report.qmd

# View report
open backtest_report.html
```

## Configuration

### Precedence: CLI > ENV > Defaults

Peak Trade uses a clear configuration precedence:

1. **CLI arguments** (explicit parameters)
2. **Environment variables**
3. **Defaults** (null backend, local tracking only)

### Environment Variables

```bash
# Enable MLflow tracking (optional)
export PEAK_TRADE_MLFLOW_ENABLE=true
export MLFLOW_TRACKING_URI=http://localhost:5000
export MLFLOW_EXPERIMENT_NAME=peak_trade_experiments

# Disable MLflow (default)
unset PEAK_TRADE_MLFLOW_ENABLE
```

### MLflow Integration (Optional)

MLflow support is completely optional and graceful:

```python
# With MLflow enabled
with PeakTradeRun(
    experiment_name="strategy_sweep",
    mlflow_uri="http://localhost:5000",
    enable_mlflow=True,  # Explicit override
) as run:
    # Logs to both MLflow AND local JSON
    run.log_metric("sharpe", 1.5)
```

**Benefits of MLflow:**
- Centralized tracking across machines
- Web UI for exploration
- Advanced querying and filtering

**Works without MLflow:**
- Automatic fallback to null backend
- Local JSON summaries still generated
- No dependencies on external services

## Run Summary Contract

Every run generates a `run_summary.json` file with stable schema:

```json
{
  "run_id": "abc123-def456",
  "started_at_utc": "2025-01-15T10:00:00+00:00",
  "finished_at_utc": "2025-01-15T10:05:00+00:00",
  "status": "FINISHED",
  "tags": {
    "experiment": "rsi_sweep",
    "strategy": "rsi_reversion"
  },
  "params": {
    "fast_period": 10,
    "slow_period": 20,
    "threshold": 0.5
  },
  "metrics": {
    "sharpe_ratio": 1.5,
    "total_return": 0.25,
    "max_drawdown": -0.12
  },
  "artifacts": [
    "results/equity_curve.png",
    "results/trades.csv"
  ],
  "git_sha": "abc123def",
  "worktree": "clever-varahamihira",
  "hostname": "macbook-pro",
  "tracking_backend": "null"
}
```

### Status Values

- `FINISHED`: Run completed successfully
- `FAILED`: Run encountered error
- `RUNNING`: Run still in progress
- `KILLED`: Run was terminated

### Tracking Backends

- `null`: Local tracking only (default)
- `mlflow`: MLflow tracking enabled

## CLI Tools

### compare_runs.py

Compare runs locally without MLflow.

#### List Recent Runs

```bash
# Latest 10 runs
python scripts/dev/compare_runs.py

# Latest 5 runs
python scripts/dev/compare_runs.py --n 5

# Custom directory
python scripts/dev/compare_runs.py --dir /path/to/results
```

**Output:**
```
run_id   | started_at          | status   | git_sha  | worktree            | backend | sharpe  | total_return
---------|---------------------|----------|----------|---------------------|---------|---------|-------------
abc12345 | 2025-01-15T10:00:00 | FINISHED | def45678 | clever-varahamihira | null    | 1.5000  | 0.2500
xyz67890 | 2025-01-15T09:30:00 | FINISHED | def45678 | clever-varahamihira | null    | 1.4500  | 0.2300
```

#### Compare Two Runs (Diff)

```bash
python scripts/dev/compare_runs.py \
    --baseline abc123 \
    --candidate def456
```

**Output:**
```
Baseline:  abc123 (2025-01-15T10:00:00+00:00)
Candidate: def456 (2025-01-15T11:00:00+00:00)

Changed Parameters:
  fast_period: 10 -> 15

Metrics:
  Metric               Baseline        Candidate       Diff            % Change
  --------------------------------------------------------------------------------
  sharpe_ratio         1.5000          1.6500          +0.1500         +10.00%
  total_return         0.2500          0.2800          +0.0300         +12.00%
  max_drawdown         -0.1200         -0.1000         +0.0200         +16.67%
```

#### JSON Output

```bash
python scripts/dev/compare_runs.py --format json --n 3 | jq .
```

### Filtering Metrics

```bash
# Show only specific metrics
python scripts/dev/compare_runs.py \
    --metrics sharpe_ratio total_return
```

## Quarto Reports

### Prerequisites

Install Quarto: https://quarto.org/docs/get-started/

```bash
# macOS
brew install quarto

# Linux
# Download from https://quarto.org

# Verify installation
quarto --version
```

### Generate Report

```bash
cd reports/quarto

# Render single report
quarto render backtest_report.qmd

# Preview with live reload
quarto preview backtest_report.qmd

# Render all reports
quarto render
```

### Report Data Sources

Reports load data with graceful fallback:

1. **Preferred**: Local `run_summary.json` files
2. **Fallback**: MLflow (if configured)

The report automatically:
- Finds the most recent run summary
- Displays metadata, parameters, metrics
- Generates visualizations
- Works offline (with local summaries)

### Customize Reports

Edit `reports&#47;quarto&#47;backtest_report.qmd` to:
- Add custom visualizations
- Filter metrics
- Load specific runs
- Add analysis sections

## CI Integration

### Run Comparison in CI

```yaml
# .github/workflows/experiments.yml
- name: Compare with baseline
  run: |
    python scripts/dev/compare_runs.py \
      --baseline ${{ env.BASELINE_RUN_ID }} \
      --candidate ${{ env.CURRENT_RUN_ID }} \
      > comparison.txt

    # Post to PR comment
    gh pr comment ${{ github.event.number }} \
      --body-file comparison.txt
```

### Skip MLflow in CI

```bash
# CI runs without MLflow by default (null backend)
export PEAK_TRADE_MLFLOW_ENABLE=false

# Or simply don't set MLFLOW_TRACKING_URI
```

## Troubleshooting

### No Run Summaries Found

**Problem:**
```
No run summaries found in results/
```

**Solution:**
1. Check that you're using `PeakTradeRun` context manager
2. Verify `results&#47;` directory exists
3. Look for `run_summary_*.json` files:
   ```bash
   ls -lh results/run_summary_*.json
   ```

### MLflow Connection Failed

**Problem:**
```
WARNING: Failed to start MLflow run: Connection refused
```

**Solution:**
1. This is expected if MLflow is not running
2. Run falls back to null backend automatically
3. Local summary JSON still generated
4. To use MLflow, start server:
   ```bash
   mlflow server --host 0.0.0.0 --port 5000
   ```

### Quarto Not Found

**Problem:**
```
bash: quarto: command not found
```

**Solution:**
1. Install Quarto: https://quarto.org/docs/get-started/
2. Or skip report generation (optional)
3. CI can run without Quarto

### Import Errors in Report

**Problem:**
```
ImportError: No module named 'experiments.tracking'
```

**Solution:**
1. Ensure `src/` is in PYTHONPATH:
   ```python
   import sys
   sys.path.insert(0, "/path/to/src")
   ```
2. Or install package in development mode:
   ```bash
   pip install -e .
   ```

### Comparison Shows No Differences

**Problem:**
Diff output is empty even though runs differ.

**Solution:**
1. Check that runs have different parameters/metrics
2. Verify both runs loaded successfully:
   ```bash
   python scripts/dev/compare_runs.py --verbose
   ```

## Best Practices

### 1. Tag Your Runs

Use tags to organize experiments:

```python
with PeakTradeRun(experiment_name="strategy_sweep") as run:
    run.set_tags({
        "strategy": "rsi_reversion",
        "phase": "development",
        "researcher": "john",
        "ticket": "EXP-123",
    })
```

### 2. Log Context

Include reproducibility metadata:

```python
with PeakTradeRun(experiment_name="experiment") as run:
    run.log_param("data_start", "2024-01-01")
    run.log_param("data_end", "2024-12-31")
    run.log_param("symbols", ["BTCUSD", "ETHUSD"])
    run.log_param("strategy_version", "v2.1.0")
```

### 3. Archive Artifacts

Log important artifacts for later review:

```python
with PeakTradeRun(experiment_name="experiment") as run:
    # ... run backtest ...

    # Save results
    equity_curve.to_csv("results/equity_curve.csv")
    trades.to_csv("results/trades.csv")

    # Log as artifacts
    run.log_artifact("results/equity_curve.csv")
    run.log_artifact("results/trades.csv")
```

### 4. Compare Before Deployment

```bash
# Compare candidate run with current production baseline
python scripts/dev/compare_runs.py \
    --baseline production-baseline \
    --candidate new-candidate \
    > comparison.txt

# Review changes before deploying
cat comparison.txt
```

### 5. Version Your Configs

Include config version in params:

```python
run.log_param("config_version", "v3.2.1")
run.log_param("experiment_protocol", "EXP-PROTOCOL-v2")
```

## Advanced Usage

### Custom Results Directory

```python
with PeakTradeRun(
    experiment_name="experiment",
    results_dir="/custom/path/results",
) as run:
    # Summary written to /custom/path/results/
    pass
```

### Manual Run Summary

```python
from experiments.tracking.run_summary import RunSummary

# Load and inspect
summary = RunSummary.read_json("results/run_summary_abc123.json")
print(f"Status: {summary.status}")
print(f"Metrics: {summary.metrics}")

# Validate contract
errors = summary.validate_contract(strict=True)
if errors:
    print(f"Validation errors: {errors}")
```

### Programmatic Comparison

```python
from experiments.tracking.run_summary import RunSummary

baseline = RunSummary.read_json("results/run_summary_baseline.json")
candidate = RunSummary.read_json("results/run_summary_candidate.json")

# Compare metrics
for key in baseline.metrics:
    base_val = baseline.metrics[key]
    cand_val = candidate.metrics.get(key)

    if cand_val:
        diff = cand_val - base_val
        print(f"{key}: {base_val:.4f} -> {cand_val:.4f} ({diff:+.4f})")
```

## Next Steps

- See `src/experiments/tracking/` for implementation
- Run tests: `pytest tests&#47;test_run_summary_contract.py`
- Explore example experiments in `src/experiments/`
- Read Phase 16C spec for architectural details

## References

- [MLflow Documentation](https://mlflow.org/docs/latest/index.html)
- [Quarto Documentation](https://quarto.org/docs/guide/)
- Peak Trade experiment design patterns
- CI/CD integration examples
