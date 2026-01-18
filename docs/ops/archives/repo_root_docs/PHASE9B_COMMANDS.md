# Phase 9B Commands

## Testing

```bash
# Run Rolling Evaluation Tests
cd /Users/frnkhrz/Peak_Trade
python3 -m pytest tests/risk_layer/var_backtest/test_rolling_evaluation.py -v

# Run all VaR Backtest Tests (includes Phase 9A + 9B)
python3 -m pytest tests/risk_layer/var_backtest/ -v

# Run with coverage
python3 -m pytest tests/risk_layer/var_backtest/test_rolling_evaluation.py --cov=src/risk_layer/var_backtest/rolling_evaluation --cov-report=term-missing
```

## Linting

```bash
# Check Rolling Evaluation
ruff check src/risk_layer/var_backtest/rolling_evaluation.py

# Check Tests
ruff check tests/risk_layer/var_backtest/test_rolling_evaluation.py

# Check __init__.py
ruff check src/risk_layer/var_backtest/__init__.py
```

## Import Verification

```bash
# Verify imports work
python3 -c "
from src.risk_layer.var_backtest import (
    RollingEvaluationResult,
    RollingWindowResult,
    RollingSummary,
    rolling_evaluation,
    format_rolling_summary,
    get_failing_windows,
    get_worst_window,
)
print('✅ All imports successful')
"
```

## Quick Demo

```bash
python3 << 'EOF'
from src.risk_layer.var_backtest import rolling_evaluation, format_rolling_summary

# Example: 500 observations, ~1% violations evenly distributed
violations = []
for _ in range(5):  # 5 windows
    violations.extend([False] * 99 + [True])

result = rolling_evaluation(
    violations,
    window_size=100,
    step_size=100,  # Non-overlapping
    var_alpha=0.01,
)

print(f"Windows Evaluated: {result.summary.n_windows}")
print(f"All-Pass Rate: {result.summary.all_pass_rate:.1%}")
print(f"Worst p-value: {result.summary.worst_kupiec_p_value:.4f}")
print(result.summary.notes)
print("\n" + "="*70)
print(format_rolling_summary(result))
EOF
```

## Expected Output (Demo)

```
Windows Evaluated: 5
All-Pass Rate: 100.0%
Worst p-value: 0.3205
✅ STABLE: ≥90% of windows passed all tests. Model shows consistent performance over time.

======================================================================
ROLLING-WINDOW VAR BACKTEST EVALUATION
======================================================================
Configuration:
  Window Size:       100
  Step Size:         100
  Total Observations: 500
  Windows Evaluated:  5

Summary Statistics:
  Kupiec POF Pass Rate:       100.0%
  Independence Pass Rate:     100.0%
  Cond. Coverage Pass Rate:   100.0%
  ALL Tests Pass Rate:        100.0%

Worst p-values (across all windows):
  Kupiec POF:        0.3205
  Independence:      0.8421
  Cond. Coverage:    0.5130

Verdict Stability:  100.0%

Interpretation: ✅ STABLE: ≥90% of windows passed all tests...
======================================================================
```

## Integration Example

```bash
python3 << 'EOF'
from src.risk_layer.var_backtest import (
    VaRBacktestRunner,
    rolling_evaluation,
    get_failing_windows,
)
import pandas as pd

# Generate sample data
dates = pd.date_range("2024-01-01", periods=500, freq="D")
returns = pd.Series([-0.01] * 495 + [-0.03] * 5, index=dates)
var_estimates = pd.Series([-0.02] * 500, index=dates)

# Run VaR Backtest
runner = VaRBacktestRunner(confidence_level=0.99)
backtest_result = runner.run(returns, var_estimates, symbol="EXAMPLE")

# Rolling Evaluation
violations = backtest_result.violations.violations.tolist()
rolling_result = rolling_evaluation(
    violations,
    window_size=100,
    step_size=50,  # 50% overlap
    var_alpha=0.01,
)

# Report
print(f"Single-Period Kupiec: {'PASS' if backtest_result.kupiec.is_valid else 'FAIL'}")
print(f"Rolling Pass-Rate:    {rolling_result.summary.all_pass_rate:.1%}")
print(f"Verdict Stability:    {rolling_result.summary.verdict_stability:.1%}")

# Identify failing windows
failing = get_failing_windows(rolling_result)
if failing:
    print(f"\n⚠️  {len(failing)} windows failed:")
    for w in failing:
        print(f"  Window {w.window_id}: obs {w.start_idx}-{w.end_idx}")
else:
    print("\n✅ All windows passed!")
EOF
```

## DataFrame Export

```bash
python3 << 'EOF'
from src.risk_layer.var_backtest import rolling_evaluation
import pandas as pd

violations = [False] * 495 + [True] * 5

result = rolling_evaluation(
    violations,
    window_size=100,
    step_size=100,
    var_alpha=0.01,
)

# Convert to DataFrame
df = result.to_dataframe()

# Analyze
print("Window Results:")
print(df[['window_id', 'all_passed', 'kupiec_p_value', 'independence_p_value']])

# Find failing windows
failing = df[~df['all_passed']]
print(f"\nFailing windows: {len(failing)}")
EOF
```

## File Locations

```bash
# Core Implementation
cat src/risk_layer/var_backtest/rolling_evaluation.py

# Tests
cat tests/risk_layer/var_backtest/test_rolling_evaluation.py

# API Exports
cat src/risk_layer/var_backtest/__init__.py | grep -A10 "Phase 9B"
```
