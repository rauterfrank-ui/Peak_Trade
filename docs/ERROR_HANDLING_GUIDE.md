# Peak_Trade Error Handling Guide

## Overview

Peak_Trade uses a comprehensive error taxonomy to provide clear, actionable error messages with context. All errors inherit from `PeakTradeError` and include:

- **Message**: Human-readable description of what went wrong
- **Hint**: Actionable suggestion for fixing the problem
- **Context**: Dictionary with debugging information
- **Cause**: Original exception that triggered the error (for chaining)

## Error Hierarchy

```
PeakTradeError (base)
├── DataContractError      - Data validation failures
├── ConfigError            - Configuration issues
├── ProviderError          - External API/data source failures
├── CacheCorruptionError   - Data integrity issues in cache
├── CacheError             - Cache operation failures
├── BacktestInvariantError - Backtest engine invariant violations
├── BacktestError          - Backtest operation failures
├── StrategyError          - Strategy logic/initialization failures
└── RiskError              - Risk limit violations
```

## Error Types

### DataContractError

**Use when**: Data fails validation or doesn't meet contract requirements.

**Examples**:
- Missing required OHLCV columns
- Timezone-naive datetime index
- NaN values in strict validation mode
- Unsorted or duplicate timestamps
- Invalid price/volume values

```python
from src.core.errors import DataContractError

raise DataContractError(
    "Missing required OHLCV columns",
    hint="DataFrame must contain: ['open', 'high', 'low', 'close', 'volume']",
    context={
        "missing_columns": ["high", "low"],
        "available_columns": ["open", "close", "volume"]
    }
)
```

### ConfigError

**Use when**: Configuration is invalid, incomplete, or malformed.

**Examples**:
- Unknown configuration keys
- Missing required fields
- Invalid value types or ranges
- TOML parsing errors

```python
from src.core.errors import ConfigError

raise ConfigError(
    f"Unknown strategy key: '{strategy_name}'",
    hint="Available strategies: ['momentum', 'mean_reversion', 'breakout']",
    context={
        "requested_strategy": strategy_name,
        "config_file": "config.toml",
        "available_strategies": ["momentum", "mean_reversion", "breakout"]
    }
)
```

### ProviderError

**Use when**: External data providers or APIs fail.

**Examples**:
- API timeout or network errors
- Rate limit exceeded
- Invalid API credentials
- Unexpected response format

```python
from src.core.errors import ProviderError

raise ProviderError(
    "Kraken API rate limit exceeded",
    hint="Wait 60 seconds before retrying or reduce request frequency",
    context={
        "symbol": "BTC/USD",
        "timeframe": "1h",
        "retry_after": 60
    }
)
```

### CacheError

**Use when**: Cache operations fail (not data integrity issues).

**Examples**:
- Cache write failures
- Cache read failures  
- Permission issues
- Directory creation failures

```python
from src.core.errors import CacheError

raise CacheError(
    f"Failed to write cache file: {cache_path}",
    hint="Check disk space and file permissions",
    context={
        "cache_path": str(cache_path),
        "symbol": symbol,
        "disk_free_gb": disk_free_gb
    }
)
```

### CacheCorruptionError

**Use when**: Cached data fails integrity checks.

**Examples**:
- Checksum mismatch
- Incomplete/partial writes
- Corrupted file format

```python
from src.core.errors import CacheCorruptionError

raise CacheCorruptionError(
    "Cache checksum mismatch",
    hint="Clear cache with clear_cache() or verify data integrity",
    context={
        "expected_checksum": expected,
        "actual_checksum": actual,
        "cache_file": str(cache_path)
    }
)
```

### StrategyError

**Use when**: Strategy logic or initialization fails.

**Examples**:
- Invalid strategy parameters
- Strategy initialization failures
- Signal generation errors
- Missing required indicators or data

```python
from src.core.errors import StrategyError

raise StrategyError(
    "Lookback period must be positive",
    hint="Set lookback_period > 0 in strategy configuration",
    context={
        "lookback_period": lookback_period,
        "strategy": "ma_crossover",
        "valid_range": "> 0"
    }
)
```

### BacktestError

**Use when**: Backtest engine operations fail.

**Examples**:
- Invalid backtest configuration
- Data loading failures during backtest
- Engine state corruption
- Result calculation errors

```python
from src.core.errors import BacktestError

raise BacktestError(
    "Failed to load market data for backtest",
    hint="Verify data files exist and are readable",
    context={
        "symbol": symbol,
        "start_date": start_date,
        "end_date": end_date
    }
)
```

### BacktestInvariantError

**Use when**: Backtest engine detects invariant violations.

**Examples**:
- NaN in equity curve
- Negative positions without shorting enabled
- Timestamp misalignment
- Negative equity

```python
from src.core.errors import BacktestInvariantError

raise BacktestInvariantError(
    "Equity curve contains NaN values",
    hint="Check for data gaps or invalid price data",
    context={
        "first_nan_index": first_nan_idx,
        "timestamp": str(timestamp)
    }
)
```

### RiskError

**Use when**: Risk limits are violated or risk management fails.

**Examples**:
- Position size exceeds limits
- Drawdown threshold breached
- Daily loss limit exceeded
- Portfolio leverage constraints violated

```python
from src.core.errors import RiskError

raise RiskError(
    f"Position size ${size} exceeds daily risk limit",
    hint="Reduce position size or increase risk_pct in configuration",
    context={
        "requested_size": size,
        "daily_limit": daily_limit,
        "risk_pct": risk_pct,
        "account_balance": balance
    }
)
```

## Error Chaining

Use `chain_error()` to wrap lower-level exceptions with higher-level context:

```python
from src.core.errors import chain_error

try:
    load_data_from_file()
except IOError as e:
    raise chain_error(
        e,
        "Failed to load market data",
        hint="Check data source credentials in .env",
        context={"symbol": "BTC/USD", "file": data_file}
    )
```

This preserves the original stack trace while adding contextual information.

## Context Enrichment

Add runtime context to errors after creation:

```python
from src.core.errors import BacktestError, add_backtest_context
import pandas as pd

error = BacktestError("Something went wrong")
add_backtest_context(
    error,
    run_id="bt_12345",
    timestamp=pd.Timestamp("2024-01-15", tz="UTC")
)
raise error
```

The error message will now include the backtest run ID and timestamp.

## Best Practices

### 1. Always Provide Hints

Every error should include a hint for how to fix it:

```python
# ❌ Bad: No hint
raise ConfigError("Invalid config")

# ✅ Good: Clear actionable hint
raise ConfigError(
    "Invalid config key: 'foo'",
    hint="Available keys: ['backtest', 'data', 'risk']"
)
```

### 2. Include Relevant Context

Add context that will help debug the issue:

```python
# ❌ Bad: No context
raise ProviderError("API failed")

# ✅ Good: Rich context
raise ProviderError(
    "API request failed",
    hint="Check network connection",
    context={
        "endpoint": "/api/v3/ohlcv",
        "status_code": 429,
        "retry_after": 60
    }
)
```

### 3. Use Error Chaining

Preserve the original exception when wrapping:

```python
# ❌ Bad: Loses original exception
try:
    risky_operation()
except Exception as e:
    raise ConfigError("Config failed")

# ✅ Good: Preserves stack trace
try:
    risky_operation()
except Exception as e:
    raise chain_error(e, "Config failed", hint="Check syntax")
```

### 4. Choose the Right Error Type

Use the most specific error type that fits:

```python
# ❌ Bad: Too generic
raise PeakTradeError("Strategy failed")

# ✅ Good: Specific error type
raise StrategyError(
    "Failed to initialize MA Crossover",
    hint="Check lookback_period parameter"
)
```

### 5. Make Hints Actionable

Hints should tell users exactly what to do:

```python
# ❌ Bad: Vague hint
raise CacheError("Cache failed", hint="Fix the cache")

# ✅ Good: Specific action
raise CacheError(
    "Cache write failed",
    hint="Run 'python scripts/clear_cache.py' or check disk space with 'df -h'"
)
```

## Testing Error Handling

Test that your code raises the correct errors:

```python
import pytest
from src.core.errors import ConfigError

def test_invalid_config_raises_error():
    """Test that invalid config raises ConfigError."""
    with pytest.raises(ConfigError) as exc_info:
        load_config(invalid_path)
    
    # Check error message
    assert "not found" in str(exc_info.value)
    
    # Check hint is present
    assert exc_info.value.hint is not None
    
    # Check context
    assert "config_path" in exc_info.value.context
```

## Migration Guide

When updating existing code to use the new error taxonomy:

### Before
```python
def load_data():
    if not file.exists():
        raise ValueError(f"File not found: {file}")
```

### After
```python
def load_data():
    if not file.exists():
        raise ProviderError(
            f"Data file not found: {file}",
            hint="Check data directory path in configuration",
            context={"file": str(file), "expected_dir": data_dir}
        )
```

## Adding New Error Types

To add a new error type:

1. **Define the class** in `src/core/errors.py`:
```python
class MyNewError(PeakTradeError):
    """
    Raised when something specific happens.
    
    Examples:
        - Situation 1
        - Situation 2
    """
    pass
```

2. **Add tests** in `tests/test_error_taxonomy.py`:
```python
def test_my_new_error_inheritance():
    """MyNewError inherits from PeakTradeError."""
    error = MyNewError("Test", hint="Fix it")
    assert isinstance(error, PeakTradeError)
    assert "MyNewError: Test" in str(error)
```

3. **Update documentation** in this file with examples

4. **Use it** in your code with clear hints and context

## Common Error Scenarios

### Invalid Configuration
```python
raise ConfigError(
    f"Unknown config key: '{key}'",
    hint="Available keys: ['backtest', 'data', 'risk']",
    context={"key": key, "config_file": config_path}
)
```

### API Rate Limit
```python
raise ProviderError(
    "API rate limit exceeded",
    hint="Wait 60 seconds before retrying",
    context={"retry_after": 60, "endpoint": endpoint}
)

```

### Missing Data
```python
raise DataContractError(
    "Missing required columns",
    hint="DataFrame must contain: ['open', 'high', 'low', 'close', 'volume']",
    context={"missing": missing_cols, "available": df.columns.tolist()}
)
```

### Invalid Strategy Parameters
```python
raise StrategyError(
    "Parameter out of valid range",
    hint=f"Set {param_name} between {min_val} and {max_val}",
    context={
        "parameter": param_name,
        "value": value,
        "valid_range": f"[{min_val}, {max_val}]"
    }
)
```

## Summary

- **Always use specific error types** from the taxonomy
- **Include actionable hints** that tell users what to do
- **Add relevant context** for debugging
- **Use error chaining** to preserve stack traces
- **Test error handling** in your code
- **Update documentation** when adding new error types

For more examples, see `tests/test_error_taxonomy.py` and the docstrings in `src/core/errors.py`.
