# Data Contracts

## Overview

Data contracts enforce strict validation rules at all data loading boundaries in Peak_Trade to prevent corrupted or invalid data from propagating through the system. Invalid data can lead to incorrect signals, bad trades, and financial loss.

**Risk without contracts:** Invalid data → incorrect signals → bad trades → financial loss

## Contract Specification

### OHLCV Contract v1.0.0

The OHLCV contract validates time-series market data with the following requirements:

#### Required Columns
- `open`: Opening price
- `high`: Highest price in the period
- `low`: Lowest price in the period  
- `close`: Closing price
- `volume`: Trading volume

#### Optional Columns
- `trades`: Number of trades (if present, will be validated)
- `vwap`: Volume-weighted average price (if present, will be validated)

#### Validation Rules

The contract has three strictness levels with progressively stricter rules:

##### PERMISSIVE (Basic)
1. Index must be `pd.DatetimeIndex`
2. Index must be timezone-aware (if `require_tz=True`)
3. All required OHLCV columns must be present

##### NORMAL (Production Default)
All PERMISSIVE rules plus:
4. Index must be sorted in ascending order (monotonic increasing)
5. All OHLCV columns must have numeric dtypes (not object/string)
6. OHLC prices must be positive (> 0)
7. `high >= low` for all rows
8. Volume must be non-negative (>= 0)

##### STRICT (Maximum Safety)
All NORMAL rules plus:
9. No duplicate timestamps allowed
10. No NaN values in OHLC columns (volume NaNs allowed with `allow_partial_nans=True`)
11. OHLC price relationships (if `check_ohlc_relationships=True`):
    - `high >= open`
    - `high >= close`
    - `low <= open`
    - `low <= close`

## Usage

### Quick Start

```python
from src.data.contracts import validate_ohlcv, check_ohlcv

# Tuple-based validation (returns errors)
is_valid, errors = validate_ohlcv(df, strict=True, require_tz=True)
if not is_valid:
    print(f"Validation failed: {errors}")

# Exception-based validation (raises on error)
from src.core.errors import DataContractError
try:
    check_ohlcv(df, strict=True)
except DataContractError as e:
    print(f"Validation failed: {e.message}")
    print(f"Hint: {e.hint}")
    print(f"Context: {e.context}")
```

### Using OHLCVContract Class

```python
from src.data.contracts import OHLCVContract, StrictnessLevel

# Create contract with specific strictness
contract = OHLCVContract(
    strictness=StrictnessLevel.STRICT,
    require_tz=True,
    check_ohlc_relationships=True
)

# Validate data
is_valid, errors = contract.validate(df)
if not is_valid:
    for error in errors:
        print(f"- {error}")
```

### At Loader Boundaries

#### Kraken API Loader

```python
from src.data import fetch_ohlcv_df

# Enable validation for production use
df = fetch_ohlcv_df(
    "BTC/USD", 
    "1h", 
    limit=100,
    validate_contract=True  # Recommended for production
)
```

#### Cache

```python
from src.data import ParquetCache

# Enable validation for production use
cache = ParquetCache(
    cache_dir="./data_cache",
    validate_on_load=True,   # Validate when loading from cache
    validate_on_save=True    # Validate before saving to cache
)

# Save with validation
cache.save(df, "BTC_USD_1h")

# Load with validation
df = cache.load("BTC_USD_1h")
```

#### CSV Loader

```python
from src.data import KrakenCsvLoader

# Enable validation for production use
loader = KrakenCsvLoader(validate_contract=True)
df = loader.load("data.csv")
```

## Strictness Levels

### When to Use Each Level

**PERMISSIVE**: Use for exploratory analysis or when working with incomplete data
- Only checks basic structure (columns, index type, timezone)
- Does not enforce data quality constraints
- Fastest validation

**NORMAL**: Default for production data pipelines
- Balances validation coverage with performance
- Catches most common data quality issues
- Suitable for real-time data feeds

**STRICT**: Use for critical production systems and backtesting
- Maximum safety and determinism
- Zero tolerance for data quality issues
- Adds ~1-2ms overhead for 1K rows

### Configuring Strictness

```python
from src.data.contracts import OHLCVContract, StrictnessLevel

# Permissive (fast, minimal checks)
contract_permissive = OHLCVContract(strictness=StrictnessLevel.PERMISSIVE)

# Normal (balanced, recommended for production)
contract_normal = OHLCVContract(strictness=StrictnessLevel.NORMAL)

# Strict (maximum safety, for critical systems)
contract_strict = OHLCVContract(strictness=StrictnessLevel.STRICT)
```

## Error Handling

All validation errors are structured with:
- **Message**: Human-readable description of the problem
- **Hint**: Suggested fix or next steps
- **Context**: Additional debugging information (shape, columns, etc.)

```python
from src.core.errors import DataContractError

try:
    check_ohlcv(df, strict=True)
except DataContractError as e:
    print(f"Error: {e.message}")
    print(f"Hint: {e.hint}")
    print(f"Context: {e.context}")
    
    # Example output:
    # Error: OHLCV validation failed: Found 5 row(s) where high < low
    # Hint: Check data source for corruption
    # Context: {'errors': [...], 'shape': (100, 5), 'symbol': 'BTC/USD'}
```

## Performance

Contract validation is optimized for performance:

- **Validation overhead**: < 5ms for 1,000 rows
- **Typical overhead**: ~1ms for typical data sizes (100-1000 rows)
- **Caching**: Validation results are not cached (re-validates on each call)

Performance benchmarks (1,000 rows):
- PERMISSIVE: ~0.5ms
- NORMAL: ~2ms
- STRICT: ~3ms

## Contract Versioning

The current contract version is `1.0.0` (see `CONTRACT_VERSION` in `src/data/contracts.py`).

### Version History

**v1.0.0** (Current)
- Initial implementation
- Three strictness levels (PERMISSIVE, NORMAL, STRICT)
- OHLC relationship validation
- Support for optional columns

### Future Versions

Contract versions will be stored in cache manifests to enable:
- Backward compatibility when contracts evolve
- Automatic cache invalidation when contracts change
- Migration paths for existing cached data

## Integration Points

Data contracts are integrated at the following boundaries:

1. **Kraken API Loader** (`src/data/kraken.py`)
   - Validates data fetched from Kraken API
   - Validates data loaded from cache
   - Auto-clears corrupted cache and re-fetches

2. **Parquet Cache** (`src/data/cache.py`)
   - Validates data before saving to cache
   - Validates data after loading from cache
   - Prevents corrupted data from being cached

3. **CSV Loader** (`src/data/loader.py`)
   - Validates data after loading from CSV
   - Catches data quality issues early

All validation is **opt-in by default** for backward compatibility. Production systems should enable validation explicitly.

## Best Practices

### Development
```python
# Use permissive mode for exploratory analysis
from src.data.contracts import StrictnessLevel, OHLCVContract

contract = OHLCVContract(strictness=StrictnessLevel.PERMISSIVE)
```

### Testing
```python
# Use normal mode for unit tests
cache = ParquetCache(validate_on_save=True, validate_on_load=True)
# Strictness defaults to NORMAL when strict=True
```

### Production
```python
# Use strict mode for production backtesting
from src.data.contracts import StrictnessLevel, OHLCVContract

contract = OHLCVContract(
    strictness=StrictnessLevel.STRICT,
    require_tz=True,
    check_ohlc_relationships=True
)

# Enable validation at all boundaries
cache = ParquetCache(
    cache_dir="./data_cache",
    validate_on_load=True,
    validate_on_save=True
)

df = fetch_ohlcv_df("BTC/USD", "1h", validate_contract=True)
```

### Live Trading
```python
# Use normal mode for live trading (balance safety and latency)
contract = OHLCVContract(strictness=StrictnessLevel.NORMAL)

# Still validate, but with less overhead
df = fetch_ohlcv_df("BTC/USD", "1h", validate_contract=True)
```

## Troubleshooting

### Common Issues

#### "Index must be timezone-aware"
```python
# Fix: Add timezone to index
df.index = df.index.tz_localize('UTC')
# or
df.index = df.index.tz_convert('UTC')
```

#### "Index must be sorted"
```python
# Fix: Sort the DataFrame
df = df.sort_index()
```

#### "Columns contain NaN values"
```python
# Option 1: Drop rows with NaN
df = df.dropna()

# Option 2: Fill NaN values
df = df.fillna(method='ffill')

# Option 3: Allow partial NaNs (volume only)
is_valid, errors = validate_ohlcv(df, allow_partial_nans=True)
```

#### "high < low detected"
```python
# This indicates corrupted data - investigate source
# Check raw data and API responses
# May need to re-fetch or fix data source
```

### Debugging Validation Errors

```python
from src.data.contracts import validate_ohlcv

# Get detailed error information
is_valid, errors = validate_ohlcv(df, strict=True)

if not is_valid:
    print(f"Found {len(errors)} validation errors:")
    for i, error in enumerate(errors, 1):
        print(f"{i}. {error}")
    
    # Inspect data
    print(f"\nDataFrame shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")
    print(f"Index type: {type(df.index)}")
    print(f"Index timezone: {df.index.tz}")
    print(f"\nFirst few rows:")
    print(df.head())
```

## Testing

### Unit Tests

See `tests/test_data_contracts.py` for comprehensive unit tests covering:
- All validation rules
- All strictness levels
- Edge cases (empty DataFrame, single row, etc.)
- Performance benchmarks

### Integration Tests

See `tests/test_data_contract_integration.py` for integration tests covering:
- Validation at cache boundaries
- Validation at CSV loader boundaries
- End-to-end data flow with validation
- Error message quality and debugging support

### Running Tests

```bash
# Run all contract tests
pytest tests/test_data_contracts.py -v

# Run integration tests
pytest tests/test_data_contract_integration.py -v

# Run smoke tests only
pytest tests/test_data_contracts.py -m smoke -v
```

## Future Enhancements

Planned improvements for future versions:

1. **Contract Metadata in Cache Manifest**
   - Store contract version with cached data
   - Auto-invalidate cache when contract changes
   - Support contract migrations

2. **Metrics and Monitoring**
   - Track contract violation rates
   - Alert on repeated validation failures
   - Dashboard for data quality metrics

3. **Additional Validation Rules**
   - Outlier detection (Z-score, IQR)
   - Volume profile validation
   - Gap detection in time series
   - Correlation checks between OHLC values

4. **Custom Contracts**
   - User-defined validation rules
   - Contract composition and inheritance
   - Contract templates for different asset classes

## References

- Error taxonomy: `src/core/errors.py`
- Contract implementation: `src/data/contracts.py`
- Cache implementation: `src/data/cache.py`
- Kraken loader: `src/data/kraken.py`
- CSV loader: `src/data/loader.py`
