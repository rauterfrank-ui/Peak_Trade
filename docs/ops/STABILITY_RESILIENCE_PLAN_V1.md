# Peak_Trade Stability & Resilience Plan V1

**Status:** Wave A Complete ✅ | Wave B Pending | Wave C Pending

**Owner:** Staff Engineer + Reliability Lead
**Last Updated:** 2024-12-18

---

## Overview

This document tracks the phased implementation of the Stability & Resilience Plan for Peak_Trade. The plan is organized into three waves (A/B/C), each targeting specific reliability improvements with their own branch, PR, tests, and documentation.

**Design Principles:**
- **Fail-fast** with clear error messages
- **Deterministic** execution (same inputs → same outputs)
- **Every new feature has tests**
- **No unmotivated refactors** - only targeted changes per issue
- **Existing tests must stay green**

---

## Wave A: Correctness & Determinism (P0) ✅

**Branch:** `feat/stability-wave-a`
**Status:** Complete
**PR:** TBD

### Implemented Components

#### A1: Data Contract Gate ✅
**File:** `src/data/contracts.py`

Strict validation for OHLCV DataFrames with:
- Required columns check (open, high, low, close, volume)
- Timezone-aware DatetimeIndex enforcement
- Sorted, deduplicated timestamps
- NaN detection (configurable)
- Object dtype detection (prevents bad parsing)
- Price/volume sanity checks (positive prices, high >= low, volume >= 0)

**Usage:**
```python
from src.data.contracts import validate_ohlcv

# Basic validation
validate_ohlcv(df)

# Strict validation (production-ready)
validate_ohlcv(df, strict=True, require_tz=True)
```

**Tests:** `tests/test_data_contracts.py` (16 tests)

#### A2: Error Taxonomy ✅
**File:** `src/core/errors.py`

Structured error hierarchy with hints and context:
- `PeakTradeError` (base class)
- `DataContractError` (data validation failures)
- `ConfigError` (invalid configuration)
- `ProviderError` (external API failures)
- `CacheCorruptionError` (cache integrity issues)
- `BacktestInvariantError` (backtest engine violations)

**Usage:**
```python
from src.core.errors import ConfigError

raise ConfigError(
    "Unknown strategy key: 'foo'",
    hint="Available strategies: ['momentum', 'mean_reversion']",
    context={"key": "foo", "available": ["momentum", "mean_reversion"]}
)
```

**Tests:** `tests/test_error_taxonomy.py` (12 tests)

#### A3: Cache Atomic Writes + Corruption Detection ✅
**File:** `src/data/cache_atomic.py`

Atomic write operations with optional checksums:
- Write to temp file first
- `fsync()` to ensure data is on disk
- Atomic rename (POSIX guarantee)
- Optional SHA256 checksum with `.sha256` sidecar file
- Read with checksum verification

**Usage:**
```python
from src.data.cache_atomic import atomic_write, atomic_read

# Write with checksum
atomic_write(df, "path/to/file.parquet", checksum=True)

# Read with verification
df = atomic_read("path/to/file.parquet", verify_checksum=True)
```

**Tests:** `tests/test_cache_atomic.py` (12 tests)

#### A4: Repro Context & Seed Policy ✅
**File:** `src/core/repro.py`

Reproducibility context and deterministic execution:
- `ReproContext` captures environment state (seed, git SHA, config hash, Python version, platform, run_id)
- `set_global_seed()` sets seeds for random/numpy/torch
- Stable config hashing (canonical JSON)
- `verify_determinism()` helper for testing

**Usage:**
```python
from src.core.repro import ReproContext, set_global_seed

# Create repro context
ctx = ReproContext.create(seed=42, config_dict=my_config)
print(ctx.run_id)  # Unique run identifier

# Set global seeds (call once at start)
set_global_seed(42)
```

**Tests:** `tests/test_repro.py` (17 tests)

### Test Results

**Total Tests:** 61 passed
**Test Files:**
- `tests/test_data_contracts.py` (16 tests)
- `tests/test_error_taxonomy.py` (12 tests)
- `tests/test_cache_atomic.py` (12 tests)
- `tests/test_repro.py` (17 tests)
- `tests/test_basics.py` (4 tests - baseline)

**Baseline Compatibility:** All existing tests remain green ✅

### Breaking Changes

None. All new features are opt-in.

### Integration Points

Wave A components are designed to be gradually integrated:
- `validate_ohlcv()` can be added to Loader/Normalizer with config flag
- Error taxonomy can replace raw KeyErrors/ValueErrors incrementally
- `atomic_write()`/`atomic_read()` can coexist with existing `ParquetCache`
- `set_global_seed()` can be added to runner entry points

---

## Wave B: Operability & DX (P1) 🔜

**Branch:** `feat/stability-wave-b` (not yet created)
**Status:** Pending

### Planned Components

#### B1: Config Schema Validation
**File:** `src/core/config_schema.py`

- Validate config against schema before run
- Unknown keys → ConfigError with suggestions
- Type/range validation
- Integration with runner entry points

#### B2: Observability (Structured Logging)
**File:** `src/core/logging.py`

- Structured logger with run_id/trace_id
- Attach context to all logs (Loader, Engine, Stats)
- Lightweight integration

#### B3: Backtest Engine Invariants
**File:** `src/backtest/invariants.py`

- Check invariants during backtest run
- Violations → BacktestInvariantError with repro context
- Configurable strictness

#### B4: Strategy Registry Hardening
**File:** `src/backtest/registry_engine.py` updates

- Unknown strategy → ConfigError with available keys
- CLI: `--list-strategies`
- Better error messages

---

## Wave C: Resilience under Failure + CI Gate (P2) 🔜

**Branch:** `feat/stability-wave-c` (not yet created)
**Status:** Pending

### Planned Components

#### C1: Provider Resilience
**File:** `src/data/retry.py`

- RetryPolicy with exponential backoff
- Circuit breaker (in-memory)
- Integration in Provider layer only

#### C2: CI Smoke Gate
**Marker:** `@pytest.mark.smoke`

- Ultra-fast smoke tests (contracts, registry, invariants)
- GitHub Actions integration
- Documentation for local usage

---

## Migration Guide

### For Operators

**Wave A (now available):**

1. **Validate data quality:**
   ```python
   from src.data.contracts import validate_ohlcv
   validate_ohlcv(df, strict=True)
   ```

2. **Use atomic cache writes for critical data:**
   ```python
   from src.data.cache_atomic import atomic_write
   atomic_write(df, "cache/btc.parquet", checksum=True)
   ```

3. **Track runs with ReproContext:**
   ```python
   from src.core.repro import ReproContext
   ctx = ReproContext.create(seed=42, config_dict=config)
   print(f"Run ID: {ctx.run_id}")
   ```

### For Developers

**Wave A (now available):**

1. **Use structured errors:**
   ```python
   from src.core.errors import ConfigError
   raise ConfigError(message, hint=..., context={...})
   ```

2. **Test determinism:**
   ```python
   from src.core.repro import verify_determinism
   assert verify_determinism(my_func, seed=42)
   ```

---

## Rollout Status

| Wave | Status | Branch | PR | Tests | Docs |
|------|--------|--------|----|----|------|
| A    | ✅ Complete | `feat/stability-wave-a` | TBD | 61 passed | This doc |
| B    | 🔜 Pending | TBD | TBD | TBD | TBD |
| C    | 🔜 Pending | TBD | TBD | TBD | TBD |

---

## Risks & Mitigation

### Wave A Risks

1. **Risk:** New validation may catch existing data issues
   **Mitigation:** All validation is opt-in via function calls

2. **Risk:** Atomic writes may be slower
   **Mitigation:** Only use for critical artifacts; existing `ParquetCache` unchanged

3. **Risk:** Seed policy may conflict with existing randomness
   **Mitigation:** `set_global_seed()` only called explicitly by operators

### Wave B/C Risks

TBD when branches are created.

---

## Questions & Support

- **Bugs/Issues:** Create GitHub issue with `stability` label
- **Questions:** Tag `@staff-engineer` in Slack/Discord
- **Docs:** This file (`docs/ops/STABILITY_RESILIENCE_PLAN_V1.md`)

---

## Appendix: File Inventory

### Wave A Files

**New Files:**
- `src/core/errors.py`
- `src/core/repro.py`
- `src/data/contracts.py`
- `src/data/cache_atomic.py`
- `tests/test_error_taxonomy.py`
- `tests/test_repro.py`
- `tests/test_data_contracts.py`
- `tests/test_cache_atomic.py`

**Modified Files:**
- `src/core/__init__.py` (exports)
- `src/data/__init__.py` (exports)

**Total LOC Added:** ~1200 lines (including tests and docstrings)
