# Phase 10 Commands

## Basic Usage

```bash
# Help message
python3 scripts/risk/run_var_backtest_suite_snapshot.py --help

# Basic synthetic demo
python3 scripts/risk/run_var_backtest_suite_snapshot.py \\
    --use-synthetic \\
    --n-observations 500 \\
    --confidence 0.99

# With real data
python3 scripts/risk/run_var_backtest_suite_snapshot.py \\
    --returns-file data/portfolio_returns.csv \\
    --var-file data/var_estimates.csv \\
    --confidence 0.99
```

## With Phase 9A Duration Diagnostic

```bash
python3 scripts/risk/run_var_backtest_suite_snapshot.py \\
    --use-synthetic \\
    --n-observations 500 \\
    --confidence 0.99 \\
    --enable-duration-diagnostic
```

## With Phase 9B Rolling Evaluation

```bash
python3 scripts/risk/run_var_backtest_suite_snapshot.py \\
    --use-synthetic \\
    --n-observations 1000 \\
    --confidence 0.99 \\
    --enable-rolling \\
    --rolling-window-size 250 \\
    --rolling-step-size 50
```

## Full Diagnostics (9A + 9B)

```bash
python3 scripts/risk/run_var_backtest_suite_snapshot.py \\
    --use-synthetic \\
    --n-observations 1000 \\
    --confidence 0.99 \\
    --enable-duration-diagnostic \\
    --enable-rolling \\
    --rolling-window-size 250
```

## Console Output Only (No Report)

```bash
python3 scripts/risk/run_var_backtest_suite_snapshot.py \\
    --use-synthetic \\
    --n-observations 500 \\
    --confidence 0.99 \\
    --no-report
```

## Custom Output Directory

```bash
python3 scripts/risk/run_var_backtest_suite_snapshot.py \\
    --use-synthetic \\
    --n-observations 500 \\
    --confidence 0.99 \\
    --output-dir reports/var_backtest/$(date +%Y%m)
```

## Verbose Logging

```bash
python3 scripts/risk/run_var_backtest_suite_snapshot.py \\
    --use-synthetic \\
    --n-observations 500 \\
    --confidence 0.99 \\
    -v
```

## Testing

```bash
# Run all smoke tests
python3 -m pytest tests/scripts/test_run_var_backtest_suite_snapshot.py -v

# Run specific test class
python3 -m pytest tests/scripts/test_run_var_backtest_suite_snapshot.py::TestCLIOutput -v

# Run with coverage
python3 -m pytest tests/scripts/test_run_var_backtest_suite_snapshot.py --cov=scripts/risk
```

## Automation Examples

### Daily Validation Script

```bash
#!/bin/bash
# daily_var_validation.sh

DATE=$(date +%Y%m%d)
RETURNS="data/portfolio_returns_${DATE}.csv"
VAR="data/var_estimates_${DATE}.csv"

python3 scripts/risk/run_var_backtest_suite_snapshot.py \\
    --returns-file "$RETURNS" \\
    --var-file "$VAR" \\
    --confidence 0.99 \\
    --enable-duration-diagnostic \\
    --enable-rolling \\
    --rolling-window-size 250

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ VaR validation passed"
else
    echo "❌ VaR validation failed (exit code: $EXIT_CODE)"
    exit 1
fi
```

### CI/CD Integration

```yaml
# .github/workflows/var_validation.yml
name: VaR Model Validation

on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run VaR Backtest Suite
        run: |
          python3 scripts/risk/run_var_backtest_suite_snapshot.py \\
            --returns-file data/returns.csv \\
            --var-file data/var.csv \\
            --confidence 0.99 \\
            --enable-rolling \\
            --rolling-window-size 250
      - name: Upload Report
        if: always()
        uses: actions/upload-artifact@v2
        with:
          name: var-backtest-report
          path: reports/var_backtest/*.md
```

## Exit Codes

```bash
# Check exit code
python3 scripts/risk/run_var_backtest_suite_snapshot.py \\
    --use-synthetic \\
    --n-observations 500 \\
    --confidence 0.99

echo "Exit code: $?"

# Exit codes:
# 0 = All core tests passed
# 1 = At least one core test failed
# 2 = Error during execution
```
