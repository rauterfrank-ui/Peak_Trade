# Configuration Guide - Pydantic Validation

## Overview

Peak_Trade uses **Pydantic V2** for runtime configuration validation, ensuring invalid configurations are caught early before execution starts. This prevents runtime crashes and wasted compute time.

## Benefits

✅ **Type Safety**: All config values are validated at load time  
✅ **Clear Error Messages**: Get actionable hints when config is invalid  
✅ **IDE Support**: Full autocomplete and type hints  
✅ **Cross-Field Validation**: Complex rules like `end_date > start_date`  
✅ **Backward Compatible**: Works with existing `config.toml` files  

---

## Quick Start

### Basic Usage

```python
from src.config import ConfigRegistry

# Load and validate config
registry = ConfigRegistry()
config = registry.load(Path("config.toml"))

# Type-safe access
backtest = registry.get_backtest_config()
print(backtest.initial_capital)  # Type: float, validated > 0
```

### Migration from Old Code

```python
# Before (no validation, type: Any)
initial_capital = config["backtest"]["initial_capital"]

# After (validated, type: float)
backtest_cfg = registry.get_backtest_config()
initial_capital = backtest_cfg.initial_capital  # Guaranteed > 0
```

---

## Configuration Models

### BacktestConfig

Backtest configuration with validation.

**Fields:**
- `initial_capital: float` - Initial capital (must be > 0)
- `start_date: Optional[str]` - Start date in YYYY-MM-DD format
- `end_date: Optional[str]` - End date in YYYY-MM-DD format (must be after start_date)
- `max_drawdown: Optional[float]` - Maximum drawdown as fraction (0-1)
- `commission: float` - Trading commission (0-0.1, default: 0.001)
- `results_dir: str` - Results directory (default: "results")

**Aliases:**
- `initial_cash` → `initial_capital` (backward compatibility)

**Example:**

```python
from src.config.models import BacktestConfig

config = BacktestConfig(
    initial_capital=10000.0,
    start_date="2024-01-01",
    end_date="2024-12-31",
    max_drawdown=0.25,
    commission=0.001
)
```

**Validation Rules:**
- ✅ `initial_capital > 0`
- ✅ Dates match pattern `YYYY-MM-DD`
- ✅ `end_date > start_date`
- ✅ `0 <= max_drawdown <= 1`
- ✅ `0 <= commission <= 0.1`

---

### DataConfig

Data loading configuration.

**Fields:**
- `provider: Literal["kraken", "csv", "cache"]` - Data provider (default: "kraken")
- `cache_enabled: bool` - Enable caching (default: True)
- `cache_ttl: int` - Cache TTL in seconds (default: 3600, must be > 0)
- `symbols: Optional[List[str]]` - Trading symbols (min 1 item)
- `default_timeframe: str` - Default timeframe (default: "1h")
- `data_dir: str` - Data directory (default: "data")
- `cache_format: str` - Cache format (default: "parquet")

**Aliases:**
- `use_cache` → `cache_enabled` (backward compatibility)

**Example:**

```python
from src.config.models import DataConfig

config = DataConfig(
    provider="kraken",
    cache_enabled=True,
    cache_ttl=3600,
    symbols=["BTC/USD", "ETH/USD"]
)
```

**Validation Rules:**
- ✅ Provider must be one of: "kraken", "csv", "cache"
- ✅ `cache_ttl > 0`
- ✅ Symbols list must have at least 1 item (if provided)

---

### RiskConfig

Risk management configuration.

**Fields:**
- `max_position_size: float` - Max position size as fraction (0-1, default: 0.1)
- `max_portfolio_leverage: float` - Max leverage (1-10, default: 1.0)
- `stop_loss_pct: Optional[float]` - Stop loss percentage (0-1, optional)
- `risk_per_trade: float` - Risk per trade (default: 0.01, max: 0.05)
- `max_daily_loss: float` - Max daily loss (default: 0.03, max: 0.10)
- `max_positions: int` - Max concurrent positions (default: 2, min: 1)
- `min_position_value: float` - Min position value USD (default: 50.0, min: 0)
- `min_stop_distance: float` - Min stop distance (default: 0.005, must be > 0)

**Example:**

```python
from src.config.models import RiskConfig

config = RiskConfig(
    max_position_size=0.1,
    max_portfolio_leverage=1.5,
    stop_loss_pct=0.02,
    risk_per_trade=0.01
)
```

**Validation Rules:**
- ✅ `0 < max_position_size <= 1`
- ✅ `1 <= max_portfolio_leverage <= 10`
- ✅ `0 <= stop_loss_pct <= 1` (if provided)
- ✅ `0 < risk_per_trade <= 0.05`
- ✅ `0 < max_daily_loss <= 0.10`
- ✅ `max_positions >= 1`

---

### PeakTradeConfig

Root configuration model combining all sections.

**Example:**

```python
from src.config.models import PeakTradeConfig

config = PeakTradeConfig(
    backtest={
        "initial_capital": 10000.0,
        "start_date": "2024-01-01",
        "end_date": "2024-12-31"
    },
    data={
        "provider": "kraken",
        "symbols": ["BTC/USD"]
    },
    risk={
        "max_position_size": 0.2
    }
)
```

---

## ConfigRegistry API

### Loading Configuration

```python
from src.config import ConfigRegistry
from pathlib import Path

# Option 1: Explicit path
registry = ConfigRegistry(Path("custom_config.toml"))
config = registry.load()

# Option 2: Environment variable
import os
os.environ["PEAK_TRADE_CONFIG"] = "/path/to/config.toml"
registry = ConfigRegistry()
config = registry.load()

# Option 3: Default (config.toml in current directory)
registry = ConfigRegistry()
config = registry.load()
```

### Type-Safe Accessors

```python
# Get validated subsections
backtest = registry.get_backtest_config()  # Returns BacktestConfig
data = registry.get_data_config()          # Returns DataConfig
risk = registry.get_risk_config()          # Returns RiskConfig

# All fields are type-safe
initial_capital: float = backtest.initial_capital
provider: str = data.provider
max_size: float = risk.max_position_size
```

### Singleton Pattern

```python
from src.config import get_registry, reset_registry

# Get global singleton
registry = get_registry()

# Force reload
registry = get_registry(force_reload=True)

# Reset (useful for tests)
reset_registry()
```

---

## Error Handling

### Invalid Configuration

When validation fails, you get clear error messages with context:

```python
from src.config import ConfigRegistry
from src.core.errors import ConfigError

registry = ConfigRegistry()
try:
    config = registry.load(Path("config.toml"))
except ConfigError as e:
    print(e.message)  # "Config validation failed: backtest -> initial_capital: ..."
    print(e.hint)     # "Check config.toml for: initial_capital must be positive"
    print(e.context)  # {"file": "config.toml", "errors": [...]}
```

### Common Validation Errors

**Negative Capital:**
```
ConfigError: Config validation failed: backtest -> initial_capital: Input should be greater than 0
Hint: Check config.toml for: backtest -> initial_capital: Input should be greater than 0
```

**Invalid Date:**
```
ConfigError: Config validation failed: backtest -> start_date: String should match pattern '^\d{4}-\d{2}-\d{2}$'
Hint: Check config.toml for: start_date must be in YYYY-MM-DD format
```

**End Date Before Start Date:**
```
ConfigError: Config validation failed: backtest -> end_date: end_date must be after start_date
Hint: Check config.toml for: end_date must be after start_date
```

**Invalid Provider:**
```
ConfigError: Config validation failed: data -> provider: Input should be 'kraken', 'csv' or 'cache'
Hint: Check config.toml for: provider must be one of ['kraken', 'csv', 'cache']
```

---

## Example config.toml

```toml
[backtest]
initial_capital = 10000.0
start_date = "2024-01-01"
end_date = "2024-12-31"
max_drawdown = 0.25
commission = 0.001
results_dir = "results"

[data]
provider = "kraken"
cache_enabled = true
cache_ttl = 3600
symbols = ["BTC/USD", "ETH/USD"]
default_timeframe = "1h"
data_dir = "data"
cache_format = "parquet"

[risk]
max_position_size = 0.1
max_portfolio_leverage = 1.0
stop_loss_pct = 0.02
risk_per_trade = 0.01
max_daily_loss = 0.03
max_positions = 2
min_position_value = 50.0
min_stop_distance = 0.005
```

---

## Testing

### Unit Tests

Run config validation tests:

```bash
pytest tests/config/ -v
```

### Coverage

Check test coverage (should be >90%):

```bash
pytest tests/config/ --cov=src/config --cov-report=term-missing
```

### Test Your Config

```python
from src.config import ConfigRegistry
from pathlib import Path

# Test your config file
registry = ConfigRegistry()
try:
    config = registry.load(Path("config.toml"))
    print("✅ Config is valid!")
except Exception as e:
    print(f"❌ Config error: {e}")
```

---

## Best Practices

### ✅ DO's

1. **Validate Early**: Load config at startup, not during execution
2. **Use Type-Safe Accessors**: Use `registry.get_backtest_config()` instead of dict access
3. **Handle ConfigError**: Always catch and handle `ConfigError` at application entry points
4. **Set Environment Variables**: Use `PEAK_TRADE_CONFIG` for different environments
5. **Test Config Changes**: Run tests after modifying config values

### ❌ DON'Ts

1. **Don't Skip Validation**: Always use ConfigRegistry, not raw TOML loading
2. **Don't Ignore Errors**: ConfigError means your config is invalid - fix it!
3. **Don't Use Extreme Values**: Stay within recommended ranges (e.g., `risk_per_trade <= 0.02`)
4. **Don't Bypass Type Safety**: Use the validated models, not raw dicts

---

## Migration Guide

### From Old Config System

**Step 1: Import New Registry**

```python
# Old
from src.core.config_registry import get_config

# New
from src.config import ConfigRegistry
```

**Step 2: Load Config**

```python
# Old
config = get_config()
initial_capital = config["backtest"]["initial_capital"]

# New
registry = ConfigRegistry()
config = registry.load()
initial_capital = config.backtest.initial_capital
```

**Step 3: Use Type-Safe Accessors**

```python
# Old
backtest = config["backtest"]
risk_per_trade = config["risk"]["risk_per_trade"]

# New
backtest = registry.get_backtest_config()
risk = registry.get_risk_config()
risk_per_trade = risk.risk_per_trade
```

### Backward Compatibility

The new system is fully backward compatible:
- ✅ Works with existing `config.toml` files
- ✅ Supports old field aliases (`initial_cash`, `use_cache`)
- ✅ Allows extra fields for compatibility
- ✅ Old code continues to work (but consider migrating)

---

## Technical Details

### Pydantic V2 Features

- **Field Validators**: Custom validation logic with `@field_validator`
- **ConfigDict**: Modern configuration using `model_config = ConfigDict(...)`
- **Type Safety**: Full static type checking support
- **Alias Support**: Backward compatibility with `alias="old_name"`
- **Cross-Field Validation**: Validators can access other fields via `info.data`

### Error Taxonomy Integration

ConfigRegistry integrates with Peak_Trade's error taxonomy:

```python
from src.core.errors import ConfigError

# All config errors are ConfigError instances
try:
    config = registry.load()
except ConfigError as e:
    # Access structured error information
    print(e.message)  # Human-readable message
    print(e.hint)     # Actionable hint
    print(e.context)  # Dict with details
```

---

## Troubleshooting

### Problem: "Config file not found"

**Solution:**
1. Check file path: `ls -l config.toml`
2. Set environment variable: `export PEAK_TRADE_CONFIG=/path/to/config.toml`
3. Use explicit path: `ConfigRegistry(Path("config.toml"))`

### Problem: "Validation failed: initial_capital must be positive"

**Solution:** Update `config.toml`:
```toml
[backtest]
initial_capital = 10000.0  # Must be > 0
```

### Problem: "end_date must be after start_date"

**Solution:** Check date order in `config.toml`:
```toml
[backtest]
start_date = "2024-01-01"
end_date = "2024-12-31"  # Must be after start_date
```

---

## References

- **Pydantic V2 Docs**: https://docs.pydantic.dev/latest/
- **Error Taxonomy**: `src/core/errors.py`
- **Existing Config System**: `src/core/config_pydantic.py`
- **Tests**: `tests/config/`

---

**Version**: 1.0  
**Last Updated**: December 2024  
**Author**: Peak_Trade Core Team
