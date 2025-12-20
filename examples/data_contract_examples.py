#!/usr/bin/env python3
"""
Example: Data Contract Validation in Peak_Trade

Demonstrates how to use data contracts to validate OHLCV data at loader boundaries.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd

from src.data.contracts import (
    validate_ohlcv,
    check_ohlcv,
    OHLCVContract,
    StrictnessLevel,
    CONTRACT_VERSION,
)
from src.data import ParquetCache
from src.core.errors import DataContractError


def example_1_basic_validation():
    """Example 1: Basic validation with tuple return."""
    print("=" * 70)
    print("Example 1: Basic Validation (Tuple Return)")
    print("=" * 70)
    
    # Create valid OHLCV data
    df = pd.DataFrame(
        {
            "open": [100.0, 101.0, 102.0],
            "high": [105.0, 106.0, 107.0],
            "low": [99.0, 100.0, 101.0],
            "close": [103.0, 104.0, 105.0],
            "volume": [1000.0, 1100.0, 1200.0],
        },
        index=pd.date_range("2024-01-01", periods=3, freq="1h", tz="UTC"),
    )
    
    # Validate
    is_valid, errors = validate_ohlcv(df, strict=True, require_tz=True)
    
    if is_valid:
        print("✅ Data validation passed!")
    else:
        print(f"❌ Data validation failed with {len(errors)} errors:")
        for error in errors:
            print(f"   - {error}")
    
    print()


def example_2_exception_based():
    """Example 2: Exception-based validation."""
    print("=" * 70)
    print("Example 2: Exception-based Validation")
    print("=" * 70)
    
    # Create invalid OHLCV data (high < low)
    df = pd.DataFrame(
        {
            "open": [100.0, 101.0, 102.0],
            "high": [90.0, 91.0, 92.0],  # Invalid!
            "low": [99.0, 100.0, 101.0],
            "close": [95.0, 96.0, 97.0],
            "volume": [1000.0, 1100.0, 1200.0],
        },
        index=pd.date_range("2024-01-01", periods=3, freq="1h", tz="UTC"),
    )
    
    try:
        check_ohlcv(df, strict=True)
        print("✅ Data validation passed!")
    except DataContractError as e:
        print("❌ Data validation failed!")
        print(f"   Error: {e.message}")
        print(f"   Hint: {e.hint}")
        print(f"   Context: {e.context}")
    
    print()


def example_3_strictness_levels():
    """Example 3: Different strictness levels."""
    print("=" * 70)
    print("Example 3: Strictness Levels")
    print("=" * 70)
    
    # Create unsorted data
    df = pd.DataFrame(
        {
            "open": [102.0, 101.0, 100.0],  # Unsorted
            "high": [107.0, 106.0, 105.0],
            "low": [101.0, 100.0, 99.0],
            "close": [105.0, 104.0, 103.0],
            "volume": [1200.0, 1100.0, 1000.0],
        },
        index=pd.date_range("2024-01-03", periods=3, freq="-1h", tz="UTC"),
    )
    
    # Test different strictness levels
    for level in [StrictnessLevel.PERMISSIVE, StrictnessLevel.NORMAL, StrictnessLevel.STRICT]:
        contract = OHLCVContract(strictness=level)
        is_valid, errors = contract.validate(df)
        
        status = "✅ PASS" if is_valid else "❌ FAIL"
        print(f"{level.value.upper():12s}: {status}")
        if errors:
            print(f"              Errors: {errors[0][:50]}...")
    
    print()


def example_4_cache_with_validation():
    """Example 4: Using cache with validation enabled."""
    print("=" * 70)
    print("Example 4: Cache with Validation")
    print("=" * 70)
    
    # Create valid data
    df = pd.DataFrame(
        {
            "open": [100.0, 101.0, 102.0],
            "high": [105.0, 106.0, 107.0],
            "low": [99.0, 100.0, 101.0],
            "close": [103.0, 104.0, 105.0],
            "volume": [1000.0, 1100.0, 1200.0],
        },
        index=pd.date_range("2024-01-01", periods=3, freq="1h", tz="UTC"),
    )
    
    # Create cache with validation enabled
    cache = ParquetCache(
        cache_dir="/tmp/example_cache",
        validate_on_save=True,
        validate_on_load=True,
    )
    
    print("Saving data to cache with validation...")
    try:
        cache.save(df, "example_data")
        print("✅ Data saved successfully (validation passed)")
    except DataContractError as e:
        print(f"❌ Save failed: {e.message}")
    
    print("\nLoading data from cache with validation...")
    try:
        loaded_df = cache.load("example_data")
        print(f"✅ Data loaded successfully (validation passed)")
        print(f"   Shape: {loaded_df.shape}")
    except DataContractError as e:
        print(f"❌ Load failed: {e.message}")
    
    # Cleanup
    cache.clear("example_data")
    
    print()


def example_5_ohlc_relationships():
    """Example 5: OHLC relationship validation."""
    print("=" * 70)
    print("Example 5: OHLC Relationship Validation")
    print("=" * 70)
    
    # Create data with high < open (invalid relationship)
    df = pd.DataFrame(
        {
            "open": [100.0, 101.0, 102.0],
            "high": [95.0, 96.0, 97.0],  # high < open!
            "low": [90.0, 91.0, 92.0],
            "close": [93.0, 94.0, 95.0],
            "volume": [1000.0, 1100.0, 1200.0],
        },
        index=pd.date_range("2024-01-01", periods=3, freq="1h", tz="UTC"),
    )
    
    # Test without OHLC relationship checks
    contract_basic = OHLCVContract(
        strictness=StrictnessLevel.STRICT,
        check_ohlc_relationships=False
    )
    is_valid, errors = contract_basic.validate(df)
    print(f"Without OHLC checks: {'✅ PASS' if is_valid else '❌ FAIL'}")
    if errors:
        print(f"   Errors: {len(errors)}")
    
    # Test with OHLC relationship checks
    contract_strict = OHLCVContract(
        strictness=StrictnessLevel.STRICT,
        check_ohlc_relationships=True
    )
    is_valid, errors = contract_strict.validate(df)
    print(f"With OHLC checks:    {'✅ PASS' if is_valid else '❌ FAIL'}")
    if errors:
        print(f"   Errors: {len(errors)}")
        for error in errors[:2]:  # Show first 2 errors
            print(f"   - {error}")
    
    print()


def main():
    """Run all examples."""
    print("\n")
    print("=" * 70)
    print("Peak_Trade Data Contract Examples")
    print(f"Contract Version: {CONTRACT_VERSION}")
    print("=" * 70)
    print()
    
    example_1_basic_validation()
    example_2_exception_based()
    example_3_strictness_levels()
    example_4_cache_with_validation()
    example_5_ohlc_relationships()
    
    print("=" * 70)
    print("All examples completed!")
    print("=" * 70)
    print()


if __name__ == "__main__":
    main()
