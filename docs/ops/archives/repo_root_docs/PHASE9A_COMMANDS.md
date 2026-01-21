# Phase 9A Commands

## Testing

```bash
# Run Duration Diagnostic Tests
cd /Users/frnkhrz/Peak_Trade
python3 -m pytest tests/risk_layer/var_backtest/test_duration_diagnostics.py -v

# Run all VaR Backtest Tests
python3 -m pytest tests/risk_layer/var_backtest/ -v

# Run with coverage
python3 -m pytest tests/risk_layer/var_backtest/test_duration_diagnostics.py --cov=src/risk_layer/var_backtest/duration_diagnostics --cov-report=term-missing
```

## Linting

```bash
# Check Duration Diagnostics
ruff check src/risk_layer/var_backtest/duration_diagnostics.py

# Check Tests
ruff check tests/risk_layer/var_backtest/test_duration_diagnostics.py

# Check __init__.py
ruff check src/risk_layer/var_backtest/__init__.py
```

## Import Verification

```bash
# Verify imports work
python3 -c "
from src.risk_layer.var_backtest import (
    DurationDiagnosticResult,
    ExponentialTestResult,
    extract_exceedance_durations,
    duration_independence_diagnostic,
    format_duration_diagnostic,
)
print('✅ All imports successful')
"
```

## Quick Demo

```bash
python3 << 'EOF'
from src.risk_layer.var_backtest import duration_independence_diagnostic

# Example: Clustered violations
exceedances = [False] * 100 + [True, False, True, False, True] + [False] * 100

result = duration_independence_diagnostic(
    exceedances,
    expected_rate=0.01,
)

print(f"Mean Duration: {result.mean_duration:.2f}")
print(f"Expected Duration: {result.expected_duration:.2f}")
print(f"Duration Ratio: {result.duration_ratio:.4f}")
print(f"Clustering? {result.is_suspicious()}")
print(result.notes)
EOF
```

## Expected Output (Demo)

```
Mean Duration: 2.00
Expected Duration: 33.33
Duration Ratio: 0.0600
Clustering? True
⚠️  DIAGNOSTIC: Duration ratio < 0.5 suggests potential clustering. Verify with Christoffersen Independence Test.
```

## Integration Example

```bash
python3 << 'EOF'
from src.risk_layer.var_backtest import (
    VaRBacktestRunner,
    christoffersen_independence_test,
    duration_independence_diagnostic,
)
import pandas as pd

# Generate sample data
dates = pd.date_range("2024-01-01", periods=250, freq="D")
returns = pd.Series([-0.01] * 247 + [-0.03] * 3, index=dates)
var_estimates = pd.Series([-0.02] * 250, index=dates)

# Run VaR Backtest
runner = VaRBacktestRunner(confidence_level=0.99)
backtest_result = runner.run(returns, var_estimates, symbol="EXAMPLE")

# Christoffersen Test
violations = backtest_result.violations.violations.tolist()
christoffersen_result = christoffersen_independence_test(violations)

# Duration Diagnostic (optional)
duration_result = duration_independence_diagnostic(
    violations,
    expected_rate=0.01,
    timestamps=backtest_result.violations.dates,
)

# Report
print(f"Kupiec POF:       {'PASS' if backtest_result.kupiec.is_valid else 'FAIL'}")
print(f"Christoffersen:   {'PASS' if christoffersen_result.passed else 'FAIL'}")
print(f"Duration Ratio:   {duration_result.duration_ratio:.4f}")
print(f"Clustering:       {'YES' if duration_result.is_suspicious() else 'NO'}")
EOF
```

## File Locations

```bash
# Core Implementation
cat src/risk_layer/var_backtest/duration_diagnostics.py

# Tests
cat tests/risk_layer/var_backtest/test_duration_diagnostics.py

# Documentation
cat docs/risk/DURATION_DIAGNOSTIC_GUIDE.md

# API Exports
cat src/risk_layer/var_backtest/__init__.py | grep -A5 "Phase 9A"
```
