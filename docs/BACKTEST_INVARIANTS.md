# Backtest Invariants Documentation

## Overview

The backtest invariant checking system provides formal validation of backtest engine state to prevent silent data corruption, invalid states, and bad trading decisions.

**Risk without invariants:** Silent data corruption → invalid backtest results → bad trading decisions

**Solution:** Automated invariant checking with configurable check frequency and actionable error messages.

---

## Core Invariants

The system includes 5 core invariants that protect against common backtest engine failures:

### 1. `equity_non_negative`

**Rule:** Equity must never be negative.

**Why it matters:** Negative equity indicates severe bugs in commission handling, position sizing, or PnL calculation.

**Example violation:**
```python
# Engine state
engine.equity = -500.0  # ❌ VIOLATION

# What caused it:
# - Commission calculation bug
# - Position sizing error allowing over-leverage
# - PnL calculation error
```

**Error message:**
```
BacktestInvariantError: Invariant 'equity_non_negative' violated: Equity cannot be negative
Hint: Check for commission bugs or position sizing errors
Context: {'invariant': 'equity_non_negative', 'equity': -500.0, 'cash': 0.0, 'num_positions': 1}
```

---

### 2. `positions_valid`

**Rule:** Position list must be valid (no None values, no duplicate symbols).

**Why it matters:** Corrupted position lists cause incorrect exposure calculations and position management failures.

**Example violations:**
```python
# Case 1: None in positions list
engine.positions = [position1, None, position3]  # ❌ VIOLATION

# Case 2: Duplicate symbols
engine.positions = [
    Position(symbol="BTC/EUR", size=1.0),
    Position(symbol="BTC/EUR", size=0.5),  # ❌ VIOLATION (duplicate)
]

# Case 3: Positions is None
engine.positions = None  # ❌ VIOLATION
```

**Error message:**
```
BacktestInvariantError: Invariant 'positions_valid' violated: Position list corrupted (None or duplicates)
Hint: Check position add/remove logic
Context: {'invariant': 'positions_valid', 'equity': 10000.0, 'num_positions': 'unknown'}
```

---

### 3. `timestamps_monotonic`

**Rule:** Timestamps must be strictly increasing.

**Why it matters:** Out-of-order timestamps break time-series analysis and cause look-ahead bias.

**Example violation:**
```python
# Engine history
engine.history = [
    HistoryEntry(timestamp=pd.Timestamp("2024-01-01 00:00")),
    HistoryEntry(timestamp=pd.Timestamp("2024-01-01 02:00")),
    HistoryEntry(timestamp=pd.Timestamp("2024-01-01 01:00")),  # ❌ VIOLATION (out of order)
]
```

**Error message:**
```
BacktestInvariantError: Invariant 'timestamps_monotonic' violated: Timestamps are not monotonically increasing
Hint: Check data feed or time handling
Context: {'invariant': 'timestamps_monotonic', 'equity': 10000.0}
```

---

### 4. `cash_balance_valid`

**Rule:** Cash balance must be >= 0 (no margin violations).

**Why it matters:** Negative cash indicates the strategy is trading beyond available capital.

**Example violation:**
```python
# Engine state
engine.cash = -1000.0  # ❌ VIOLATION

# What caused it:
# - Position size exceeds available capital
# - Margin calculation error
# - Missing capital availability check
```

**Error message:**
```
BacktestInvariantError: Invariant 'cash_balance_valid' violated: Negative cash balance (margin violation)
Hint: Position size exceeds available capital
Context: {'invariant': 'cash_balance_valid', 'equity': 10000.0, 'cash': -1000.0}
```

---

### 5. `position_sizes_realistic`

**Rule:** Total position exposure must be within portfolio limits (max 10x leverage).

**Why it matters:** Excessive leverage indicates unrealistic position sizing or calculation errors.

**Example violation:**
```python
# Engine state
engine.equity = 10000.0
engine.positions = [
    Position(value=150000.0)  # ❌ VIOLATION (15x leverage > 10x limit)
]
```

**Error message:**
```
BacktestInvariantError: Invariant 'position_sizes_realistic' violated: Total position exposure exceeds limits
Hint: Check leverage calculation or position sizing
Context: {'invariant': 'position_sizes_realistic', 'equity': 10000.0, 'num_positions': 1}
```

---

## Check Modes

The invariant checker supports three modes with different performance/safety trade-offs:

### `CheckMode.START_END` (Default)

**When to check:** Only at backtest start and end.

**Performance:** Minimal overhead (~0.1% slowdown).

**Use case:** Production backtests, parameter sweeps.

**Example:**
```python
from src.backtest.engine import BacktestEngine

engine = BacktestEngine(check_mode="start_end")  # Default
result = engine.run_realistic(df, strategy_fn, params)
```

---

### `CheckMode.ALWAYS`

**When to check:** After every bar (inside the main loop).

**Performance:** Moderate overhead (~5-10% slowdown).

**Use case:** Development, debugging, testing new strategies.

**Example:**
```python
engine = BacktestEngine(check_mode="always")
result = engine.run_realistic(df, strategy_fn, params)
```

---

### `CheckMode.NEVER`

**When to check:** Never (disabled).

**Performance:** No overhead.

**Use case:** Performance-critical scenarios where invariants are pre-validated.

**Warning:** ⚠️ Not recommended! Only use if you're absolutely certain the engine state is valid.

**Example:**
```python
engine = BacktestEngine(check_mode="never")
result = engine.run_realistic(df, strategy_fn, params)
```

---

## Configuration

Invariant checking is configured in `config.toml`:

```toml
[backtest]
initial_cash = 10_000.0
results_dir = "results"

# Invariant checking configuration
invariant_check_mode = "start_end"  # always, start_end, never
enable_custom_invariants = true
```

---

## Custom Invariants

You can define and register custom invariants for domain-specific validation:

### Example 1: Maximum Drawdown Limit

```python
from src.backtest.invariants import Invariant, InvariantChecker
from src.backtest.engine import BacktestEngine

def max_drawdown_limit(engine) -> bool:
    """Custom: max drawdown must not exceed 50%."""
    if not engine.history or not hasattr(engine, 'equity_curve'):
        return True
    
    equity_curve = engine.equity_curve
    if not equity_curve:
        return True
    
    peak_equity = max(equity_curve)
    current_equity = engine.equity
    current_dd = (peak_equity - current_equity) / peak_equity
    return current_dd <= 0.5

# Create engine and register custom invariant
engine = BacktestEngine()
engine.invariant_checker.add_custom_invariant(
    Invariant(
        name="max_drawdown_50pct",
        check=max_drawdown_limit,
        error_message="Drawdown exceeded 50%",
        hint="Strategy is too risky, reduce position sizes"
    )
)

# Run backtest (will check custom invariant)
result = engine.run_realistic(df, strategy_fn, params)
```

### Example 2: Win Rate Floor

```python
def min_win_rate(engine) -> bool:
    """Custom: win rate must be at least 40%."""
    if not hasattr(engine, 'trades') or not engine.trades:
        return True  # No trades yet
    
    winning_trades = sum(1 for t in engine.trades if t.pnl > 0)
    total_trades = len(engine.trades)
    
    if total_trades == 0:
        return True
    
    win_rate = winning_trades / total_trades
    return win_rate >= 0.40

engine.invariant_checker.add_custom_invariant(
    Invariant(
        name="min_win_rate_40pct",
        check=min_win_rate,
        error_message="Win rate below 40%",
        hint="Strategy may not be profitable, review signal logic"
    )
)
```

### Example 3: Maximum Single Position Size

```python
def max_single_position_size(engine) -> bool:
    """Custom: no single position can exceed 25% of equity."""
    if not hasattr(engine, 'positions') or not engine.positions:
        return True
    
    max_allowed = engine.equity * 0.25
    
    for position in engine.positions:
        if hasattr(position, 'value') and abs(position.value) > max_allowed:
            return False
    
    return True

engine.invariant_checker.add_custom_invariant(
    Invariant(
        name="max_position_25pct",
        check=max_single_position_size,
        error_message="Single position exceeds 25% of equity",
        hint="Reduce position sizing or implement better diversification"
    )
)
```

---

## Advanced Usage

### Removing Built-in Invariants

If you need to disable a specific built-in invariant:

```python
engine = BacktestEngine()

# Remove the timestamps_monotonic check (not recommended!)
removed = engine.invariant_checker.remove_invariant("timestamps_monotonic")
assert removed is True

# List remaining invariants
print(engine.invariant_checker.get_invariant_names())
# Output: ['equity_non_negative', 'positions_valid', 'cash_balance_valid', 'position_sizes_realistic']
```

### Checking Invariants Manually

```python
from src.backtest.invariants import InvariantChecker, CheckMode

# Create checker
checker = InvariantChecker(mode=CheckMode.ALWAYS)

# Manually check at any point
try:
    checker.check_all(engine)
    print("✓ All invariants passed")
except BacktestInvariantError as e:
    print(f"✗ Invariant violation: {e.message}")
    print(f"  Hint: {e.hint}")
    print(f"  Context: {e.context}")
```

### Thread Safety

The invariant checker is **not** thread-safe. If running multiple backtests in parallel, create separate `BacktestEngine` instances:

```python
from concurrent.futures import ProcessPoolExecutor

def run_backtest_with_params(params):
    # Each process gets its own engine
    engine = BacktestEngine(check_mode="start_end")
    return engine.run_realistic(df, strategy_fn, params)

with ProcessPoolExecutor() as executor:
    results = list(executor.map(run_backtest_with_params, param_combinations))
```

---

## Performance Impact

Benchmark results on M2 Mac, 1000-bar backtest:

| Check Mode | Runtime | Overhead | Recommendation |
|------------|---------|----------|----------------|
| `NEVER` | 42ms | 0% | ⚠️ Not recommended |
| `START_END` | 42ms | ~0.1% | ✅ **Default (production)** |
| `ALWAYS` | 46ms | ~9.5% | 🔧 Development/debugging |

**Key takeaways:**
- `START_END` mode has negligible overhead → use in production
- `ALWAYS` mode adds ~10% overhead → use during development
- Overhead scales linearly with number of bars

---

## Troubleshooting

### Common Violation Scenarios

#### Negative Equity

**Symptoms:**
```
BacktestInvariantError: Equity cannot be negative
```

**Possible causes:**
1. Commission calculation error
2. Position sizing allows over-leverage
3. PnL calculation bug

**How to debug:**
```python
# Enable ALWAYS mode to catch exactly where it happens
engine = BacktestEngine(check_mode="always")

# Add logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Run backtest
result = engine.run_realistic(df, strategy_fn, params)
```

#### Negative Cash

**Symptoms:**
```
BacktestInvariantError: Negative cash balance (margin violation)
```

**Possible causes:**
1. Position size calculation doesn't account for available capital
2. Missing pre-trade capital check
3. Commission not included in capital requirements

**How to fix:**
- Add capital availability check before opening positions
- Include commission in position sizing calculation
- Reduce `max_position_size` in `config.toml`

#### Non-monotonic Timestamps

**Symptoms:**
```
BacktestInvariantError: Timestamps are not monotonically increasing
```

**Possible causes:**
1. Data feed is unsorted
2. Manual timestamp manipulation
3. Resampling bug

**How to fix:**
```python
# Sort data before backtest
df = df.sort_index()

# Verify monotonicity
assert df.index.is_monotonic_increasing
```

---

## Integration with Error Taxonomy

Invariant violations use the existing error taxonomy from `src/core/errors.py`:

```python
from src.core.errors import BacktestInvariantError

try:
    engine.run_realistic(df, strategy_fn, params)
except BacktestInvariantError as e:
    # Access structured error information
    print(f"Error: {e.message}")
    print(f"Hint: {e.hint}")
    print(f"Context: {e.context}")
    
    # Context includes:
    # - invariant: name of violated invariant
    # - equity: current equity
    # - cash: current cash
    # - num_positions: number of open positions
```

---

## Best Practices

1. **Always use `START_END` mode in production** → minimal overhead
2. **Use `ALWAYS` mode during development** → catch bugs early
3. **Never use `NEVER` mode unless absolutely necessary** → safety first
4. **Add custom invariants for domain-specific rules** → domain validation
5. **Test invariants in isolation** → unit test each check function
6. **Document custom invariants** → explain why they exist

---

## Examples

### Example 1: Basic Usage

```python
from src.backtest.engine import BacktestEngine

# Create engine with default settings
engine = BacktestEngine()  # Uses START_END mode from config

# Run backtest
result = engine.run_realistic(
    df=ohlcv_data,
    strategy_signal_fn=my_strategy,
    strategy_params={"fast": 10, "slow": 30},
)

print(f"Total return: {result.stats['total_return']:.2%}")
print(f"Sharpe ratio: {result.stats['sharpe']:.2f}")
```

### Example 2: Development with ALWAYS Mode

```python
# Development: check invariants after every bar
engine = BacktestEngine(check_mode="always")

result = engine.run_realistic(df, strategy_fn, params)
# If invariant violation occurs, you'll get exact bar where it happened
```

### Example 3: Custom Invariants

```python
def my_custom_check(engine) -> bool:
    """Ensure total trades don't exceed 100."""
    if not hasattr(engine, 'trades'):
        return True
    return len(engine.trades) <= 100

engine = BacktestEngine()
engine.invariant_checker.add_custom_invariant(
    Invariant(
        name="max_trades",
        check=my_custom_check,
        error_message="Exceeded 100 trades",
        hint="Strategy is overtrading, increase signal threshold"
    )
)

result = engine.run_realistic(df, strategy_fn, params)
```

---

## Related Documentation

- [Error Taxonomy](../src/core/errors.py) - Structured error handling
- [Backtest Engine](../src/backtest/engine.py) - Main backtest implementation
- [Risk Management](../docs/RISK_MANAGEMENT.md) - Position sizing and risk limits

---

## Changelog

- **2024-12-20:** Initial implementation with 5 core invariants
- **Future:** Add support for invariant severity levels (warning vs. error)

---

## FAQ

**Q: Why do I get "module not imported" warnings in coverage reports?**

A: This is a known issue with coverage.py and editable installs. The tests are running correctly, and the coverage report just has path resolution issues. You can safely ignore these warnings.

**Q: Can I use invariants with vectorized backtests?**

A: No, invariants are designed for realistic bar-by-bar backtests (`run_realistic()`). Vectorized backtests (`run_vectorized()`) don't have detailed state tracking.

**Q: What happens if an invariant check itself crashes?**

A: The checker treats this as a violation and raises a `BacktestInvariantError` with details about the check failure.

**Q: Are invariants checked during live trading?**

A: No, invariants are only for backtesting. Live trading has separate validation layers.

**Q: Can I contribute new core invariants?**

A: Yes! Submit a PR with:
1. Invariant implementation in `BacktestInvariants`
2. Entry in `CORE_INVARIANTS` list
3. Unit tests
4. Documentation update

---

## Support

For questions or issues:
- Open an issue on GitHub
- Check existing tests in `tests/test_backtest_invariants.py`
- Review error messages and hints
