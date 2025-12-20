"""
Integration tests for data contract validation at loader boundaries.

Tests that validation is properly enforced at:
- Kraken loader (fetch_ohlcv_df)
- Cache (ParquetCache save/load)
- CSV loader (KrakenCsvLoader)
"""
import pandas as pd
import pytest
import tempfile
from pathlib import Path

from src.data.cache import ParquetCache
from src.data.loader import KrakenCsvLoader
from src.core.errors import DataContractError


@pytest.fixture
def valid_ohlcv_df():
    """Valid OHLCV DataFrame."""
    return pd.DataFrame(
        {
            "open": [100.0, 101.0, 102.0],
            "high": [105.0, 106.0, 107.0],
            "low": [99.0, 100.0, 101.0],
            "close": [103.0, 104.0, 105.0],
            "volume": [1000.0, 1100.0, 1200.0],
        },
        index=pd.date_range("2024-01-01", periods=3, freq="1h", tz="UTC"),
    )


@pytest.fixture
def invalid_ohlcv_df():
    """Invalid OHLCV DataFrame (high < low)."""
    return pd.DataFrame(
        {
            "open": [100.0, 101.0, 102.0],
            "high": [90.0, 91.0, 92.0],  # Invalid: high < low
            "low": [99.0, 100.0, 101.0],
            "close": [95.0, 96.0, 97.0],
            "volume": [1000.0, 1100.0, 1200.0],
        },
        index=pd.date_range("2024-01-01", periods=3, freq="1h", tz="UTC"),
    )


# ============================================================================
# Cache Integration Tests
# ============================================================================


def test_cache_save_with_validation_enabled_valid_data(valid_ohlcv_df):
    """Cache.save() with validation accepts valid data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = ParquetCache(cache_dir=tmpdir, validate_on_save=True)
        cache.save(valid_ohlcv_df, "test_key")
        
        # Should be saved successfully
        assert cache.exists("test_key")


def test_cache_save_with_validation_enabled_invalid_data(invalid_ohlcv_df):
    """Cache.save() with validation rejects invalid data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = ParquetCache(cache_dir=tmpdir, validate_on_save=True)
        
        with pytest.raises(DataContractError) as exc_info:
            cache.save(invalid_ohlcv_df, "test_key")
        
        assert "validation failed" in str(exc_info.value).lower()
        assert exc_info.value.context is not None
        assert "errors" in exc_info.value.context


def test_cache_load_with_validation_enabled_valid_data(valid_ohlcv_df):
    """Cache.load() with validation accepts valid data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Save without validation
        cache_no_val = ParquetCache(cache_dir=tmpdir, validate_on_save=False)
        cache_no_val.save(valid_ohlcv_df, "test_key")
        
        # Load with validation
        cache_val = ParquetCache(cache_dir=tmpdir, validate_on_load=True)
        df = cache_val.load("test_key")
        
        # Drop freq for comparison (parquet doesn't preserve freq)
        expected = valid_ohlcv_df.copy()
        expected.index = expected.index._with_freq(None)
        df.index = df.index._with_freq(None)
        
        pd.testing.assert_frame_equal(df, expected)


def test_cache_load_with_validation_enabled_invalid_data(invalid_ohlcv_df):
    """Cache.load() with validation rejects invalid data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Save invalid data without validation
        cache_no_val = ParquetCache(cache_dir=tmpdir, validate_on_save=False)
        cache_no_val.save(invalid_ohlcv_df, "test_key")
        
        # Load with validation should fail
        cache_val = ParquetCache(cache_dir=tmpdir, validate_on_load=True)
        
        with pytest.raises(DataContractError) as exc_info:
            cache_val.load("test_key")
        
        assert "validation failed" in str(exc_info.value).lower()
        assert "cache" in str(exc_info.value).lower()


def test_cache_validation_disabled_by_default(invalid_ohlcv_df):
    """Cache validation is disabled by default for backward compatibility."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = ParquetCache(cache_dir=tmpdir)
        
        # Should not raise even with invalid data
        cache.save(invalid_ohlcv_df, "test_key")
        df = cache.load("test_key")
        
        # Drop freq for comparison (parquet doesn't preserve freq)
        expected = invalid_ohlcv_df.copy()
        expected.index = expected.index._with_freq(None)
        df.index = df.index._with_freq(None)
        
        pd.testing.assert_frame_equal(df, expected)


# ============================================================================
# CSV Loader Integration Tests
# ============================================================================


def test_csv_loader_with_validation_enabled_valid_data(valid_ohlcv_df):
    """KrakenCsvLoader with validation accepts valid data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = Path(tmpdir) / "valid_data.csv"
        
        # Create CSV with time column
        df_with_time = valid_ohlcv_df.copy()
        df_with_time.insert(0, "time", df_with_time.index.astype(int) // 10**9)
        df_with_time.to_csv(csv_path, index=False)
        
        # Load with validation
        loader = KrakenCsvLoader(validate_contract=True)
        df = loader.load(str(csv_path))
        
        # Should load successfully
        assert len(df) == 3
        assert all(col in df.columns for col in ["open", "high", "low", "close", "volume"])


def test_csv_loader_with_validation_enabled_invalid_data(invalid_ohlcv_df):
    """KrakenCsvLoader with validation rejects invalid data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = Path(tmpdir) / "invalid_data.csv"
        
        # Create CSV with time column
        df_with_time = invalid_ohlcv_df.copy()
        df_with_time.insert(0, "time", df_with_time.index.astype(int) // 10**9)
        df_with_time.to_csv(csv_path, index=False)
        
        # Load with validation should fail
        loader = KrakenCsvLoader(validate_contract=True)
        
        with pytest.raises(DataContractError) as exc_info:
            loader.load(str(csv_path))
        
        assert "validation failed" in str(exc_info.value).lower()
        assert exc_info.value.context is not None
        assert "filepath" in exc_info.value.context


def test_csv_loader_validation_disabled_by_default(invalid_ohlcv_df):
    """CSV loader validation is disabled by default for backward compatibility."""
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = Path(tmpdir) / "invalid_data.csv"
        
        # Create CSV with time column
        df_with_time = invalid_ohlcv_df.copy()
        df_with_time.insert(0, "time", df_with_time.index.astype(int) // 10**9)
        df_with_time.to_csv(csv_path, index=False)
        
        # Load without validation
        loader = KrakenCsvLoader()
        df = loader.load(str(csv_path))
        
        # Should load even with invalid data
        assert len(df) == 3


# ============================================================================
# End-to-End Integration Tests
# ============================================================================


def test_e2e_valid_data_flow(valid_ohlcv_df):
    """End-to-end: valid data flows through all boundaries."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # 1. Save to CSV
        csv_path = Path(tmpdir) / "data.csv"
        df_with_time = valid_ohlcv_df.copy()
        df_with_time.insert(0, "time", df_with_time.index.astype(int) // 10**9)
        df_with_time.to_csv(csv_path, index=False)
        
        # 2. Load from CSV with validation
        csv_loader = KrakenCsvLoader(validate_contract=True)
        df_from_csv = csv_loader.load(str(csv_path))
        
        # 3. Save to cache with validation
        cache = ParquetCache(cache_dir=tmpdir, validate_on_save=True)
        cache.save(df_from_csv, "cached_data")
        
        # 4. Load from cache with validation
        cache_with_val = ParquetCache(cache_dir=tmpdir, validate_on_load=True)
        df_from_cache = cache_with_val.load("cached_data")
        
        # Should complete successfully
        assert len(df_from_cache) == 3


def test_e2e_invalid_data_caught_at_first_boundary(invalid_ohlcv_df):
    """End-to-end: invalid data is caught at first validation boundary."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # 1. Save to CSV
        csv_path = Path(tmpdir) / "data.csv"
        df_with_time = invalid_ohlcv_df.copy()
        df_with_time.insert(0, "time", df_with_time.index.astype(int) // 10**9)
        df_with_time.to_csv(csv_path, index=False)
        
        # 2. Load from CSV with validation should fail
        csv_loader = KrakenCsvLoader(validate_contract=True)
        
        with pytest.raises(DataContractError) as exc_info:
            csv_loader.load(str(csv_path))
        
        assert "validation failed" in str(exc_info.value).lower()


def test_validation_produces_actionable_errors(invalid_ohlcv_df):
    """Validation errors include hints and context for debugging."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = ParquetCache(cache_dir=tmpdir, validate_on_save=True)
        
        try:
            cache.save(invalid_ohlcv_df, "test_key")
            pytest.fail("Should have raised DataContractError")
        except DataContractError as e:
            # Check that error has useful information
            assert e.hint is not None
            assert len(e.hint) > 0
            assert e.context is not None
            assert "errors" in e.context
            assert "shape" in e.context
            assert "cache_key" in e.context
            
            # Check that errors are human-readable
            error_msg = str(e)
            assert "Hint:" in error_msg
            assert "Context:" in error_msg
