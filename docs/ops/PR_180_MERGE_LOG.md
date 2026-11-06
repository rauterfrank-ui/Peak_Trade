# PR 180 – Error Taxonomy Implementation (Merged)

**PR:** #180  
**Status:** ✅ Merged  
**Date:** 2024-12-20  
**Author:** Peak_Trade Team

---

## Summary

Comprehensive error taxonomy implementation providing structured, actionable error handling across Peak_Trade. Introduces 9 specialized error categories, all inheriting from `PeakTradeError` base class with consistent message/hint/context/cause pattern.

**Goals:**
- ✅ Clear, actionable error messages with hints
- ✅ Rich context for debugging
- ✅ Exception chaining via `cause` parameter
- ✅ Type-safe error handling
- ✅ Consistent error reporting across modules

---

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

**Core Pattern:**
```python
raise DataContractError(
    "Missing required OHLCV columns",
    hint="DataFrame must contain: ['open', 'high', 'low', 'close', 'volume']",
    context={"missing_columns": ["high", "low"]},
    cause=original_exception  # Optional chaining
)
```

---

## Key Changes

### 1. Core Error Module

**File:** `src/core/errors.py`

**New Classes:**
- `PeakTradeError` (base)
- 9 specialized error types (see hierarchy above)
- Consistent `__init__` signature: `(message, hint, context, cause)`
- Rich `__str__` formatting with context display

---

### 2. Migrated Modules

Four critical modules fully migrated to new taxonomy:

#### A) Data Contracts ("src\/data\/data_contracts.py" (historical path))
- ✅ All validation errors → `DataContractError`
- ✅ Rich context on OHLCV validation failures
- ✅ Clear hints for timezone, missing columns, NaN handling

#### B) Backtest Engine ("src\/backtest\/backtest_engine.py" (historical path))
- ✅ Invariant violations → `BacktestInvariantError`
- ✅ Operational errors → `BacktestError`
- ✅ Strategy initialization → `StrategyError`
- ✅ Context includes state snapshots (cash, positions, prices)

#### C) Strategy Base ("src\/strategies\/strategy_base.py" (historical path))
- ✅ Strategy errors → `StrategyError`
- ✅ Signal validation → `DataContractError`
- ✅ Context includes signal details, OHLCV snapshots

#### D) Cache Layer ("src\/data\/parquet_cache.py" (historical path))
- ✅ Cache operations → `CacheError`
- ✅ Corruption detection → `CacheCorruptionError`
- ✅ Context includes cache paths, lock states, checksums

---

### 3. Tests & Coverage

**New Tests:** `tests/test_error_taxonomy.py`

**Coverage:**
- ✅ All 9 error types instantiate correctly
- ✅ Message/hint/context/cause preserved
- ✅ `__str__` formatting verified
- ✅ Exception chaining works (via `cause` → `__cause__`)
- ✅ Integration tests for migrated modules

**Test Results:**
```bash
python3 -m pytest tests/test_error_taxonomy.py -v
# 30 passed
```

**Full Suite:**
```bash
python3 -m pytest -q
# 4200 passed, 13 skipped, 3 xfailed
```

---

## Documentation

**New Guide:** [`docs/ERROR_HANDLING_GUIDE.md`](../ERROR_HANDLING_GUIDE.md)

**Contents:**
- Error hierarchy overview
- Usage examples for each error type
- Best practices (when to raise/wrap)
- Migration guide for legacy code
- Integration with logging/monitoring

**Quick Reference:**
```python
# Raise with hint + context
raise DataContractError(
    "Invalid DataFrame",
    hint="Check column names",
    context={"cols": df.columns}
)

# Chain exceptions
try:
    risky_operation()
except ValueError as e:
    raise ConfigError("Config load failed", hint="...", cause=e)
```

---

## CI Results

### Linter ✅
```bash
ruff check src tests scripts
# All checks passed (after PR #193 follow-up)
```

### Tests ✅
```bash
python3 -m pytest -q
# 4200 passed, 13 skipped, 3 xfailed
```

### Type Checking ✅
- No mypy errors introduced
- All error classes properly typed

### Integration ✅
- Backtest smoke tests passed
- Strategy profile tests passed
- Cache operations verified

### CI Health Gate ✅
- All checks passed
- PR merged to main

---

## Follow-ups

**Opportunistic Adoption:**
- Remaining modules can adopt taxonomy as they're touched
- No forced migration required
- Script for audit: TBD in hardening PR

**Future Enhancements:**
- Structured logging integration (Phase 17+)
- Monitoring/alerting hooks
- Sentry/telemetry integration

---

## Migration Checklist

For future module migrations:

```python
# ❌ Old pattern
raise Exception("Something failed")

# ✅ New pattern
raise ConfigError(
    "Config validation failed",
    hint="Check config.toml syntax",
    context={"path": config_path, "line": 42}
)

# ❌ Old pattern
except Exception:
    pass

# ✅ New pattern
except ConfigError as e:
    logger.error(f"{e.message} | Hint: {e.hint}", extra=e.context)
    handle_error(e)
```

**Key Principles:**
1. Use most specific error type
2. Always provide actionable `hint`
3. Include relevant `context` (paths, values, state)
4. Chain via `cause` when wrapping

---

## Verification Commands

```bash
# Verify error imports
rg "from src.core.errors import" src/

# Run error taxonomy tests
python3 -m pytest tests/test_error_taxonomy.py -v

# Check ERROR_HANDLING_GUIDE.md
cat docs/ERROR_HANDLING_GUIDE.md

# Verify migrated modules
python3 -m pytest tests/test_data_contracts.py -v
python3 -m pytest tests/test_backtest_smoke.py -v
```

---

## Related PRs

- **PR #193** – Ruff lint fixes (follow-up)
- **PR #194** – UV lock refresh (dependency updates)

---

**Status:** ✅ Merged and operational. Error taxonomy is now the standard for all new code and recommended for opportunistic migration of existing code.
