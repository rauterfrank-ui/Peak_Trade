"""
Tests for Atomic Cache Operations (Wave A - Stability Plan)
"""
import os
import tempfile

import pandas as pd
import pytest

from src.core.errors import CacheCorruptionError
from src.data.cache_atomic import atomic_read, atomic_write


@pytest.fixture
def temp_dir():
    """Temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_df():
    """Sample OHLCV DataFrame for testing."""
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
    # Drop freq info to avoid assert_frame_equal issues with parquet roundtrip
    df.index = df.index._with_freq(None)
    return df


def test_atomic_write_creates_file(temp_dir, sample_df):
    """atomic_write creates file successfully."""
    filepath = os.path.join(temp_dir, "test.parquet")

    atomic_write(sample_df, filepath)

    assert os.path.exists(filepath)


def test_atomic_write_with_checksum(temp_dir, sample_df):
    """atomic_write with checksum=True creates .sha256 sidecar."""
    filepath = os.path.join(temp_dir, "test.parquet")

    atomic_write(sample_df, filepath, checksum=True)

    assert os.path.exists(filepath)
    assert os.path.exists(filepath + ".sha256")

    # Checksum file should contain hex string
    with open(filepath + ".sha256", "r") as f:
        checksum = f.read().strip()
    assert len(checksum) == 64  # SHA256 hex length
    assert all(c in "0123456789abcdef" for c in checksum)


def test_atomic_read_without_checksum(temp_dir, sample_df):
    """atomic_read loads data without checksum verification."""
    filepath = os.path.join(temp_dir, "test.parquet")
    atomic_write(sample_df, filepath)

    df = atomic_read(filepath, verify_checksum=False)

    pd.testing.assert_frame_equal(df, sample_df)


def test_atomic_read_with_checksum_valid(temp_dir, sample_df):
    """atomic_read with verify_checksum=True succeeds for valid file."""
    filepath = os.path.join(temp_dir, "test.parquet")
    atomic_write(sample_df, filepath, checksum=True)

    df = atomic_read(filepath, verify_checksum=True)

    pd.testing.assert_frame_equal(df, sample_df)


def test_atomic_read_checksum_missing(temp_dir, sample_df):
    """atomic_read raises CacheCorruptionError if .sha256 missing."""
    filepath = os.path.join(temp_dir, "test.parquet")
    atomic_write(sample_df, filepath, checksum=False)  # No checksum

    with pytest.raises(CacheCorruptionError) as exc_info:
        atomic_read(filepath, verify_checksum=True)

    assert "Checksum file missing" in str(exc_info.value)
    assert exc_info.value.hint is not None


def test_atomic_read_checksum_mismatch(temp_dir, sample_df):
    """atomic_read raises CacheCorruptionError if checksum mismatches."""
    filepath = os.path.join(temp_dir, "test.parquet")
    atomic_write(sample_df, filepath, checksum=True)

    # Corrupt the file
    with open(filepath, "ab") as f:
        f.write(b"CORRUPTED")

    with pytest.raises(CacheCorruptionError) as exc_info:
        atomic_read(filepath, verify_checksum=True)

    assert "Checksum mismatch" in str(exc_info.value)
    assert "expected" in exc_info.value.context
    assert "actual" in exc_info.value.context
    assert exc_info.value.context["expected"] != exc_info.value.context["actual"]


def test_atomic_read_file_not_found(temp_dir):
    """atomic_read raises FileNotFoundError if file doesn't exist."""
    filepath = os.path.join(temp_dir, "nonexistent.parquet")

    with pytest.raises(FileNotFoundError):
        atomic_read(filepath)


def test_atomic_write_overwrites_existing(temp_dir, sample_df):
    """atomic_write overwrites existing file atomically."""
    filepath = os.path.join(temp_dir, "test.parquet")

    # Write first version
    atomic_write(sample_df, filepath)
    df1 = atomic_read(filepath)

    # Write second version
    sample_df_v2 = sample_df.copy()
    sample_df_v2["close"] = sample_df_v2["close"] * 2
    atomic_write(sample_df_v2, filepath)
    df2 = atomic_read(filepath)

    # Verify overwrite happened
    pd.testing.assert_frame_equal(df2, sample_df_v2)
    assert not df1["close"].equals(df2["close"])


def test_atomic_write_creates_directory(temp_dir, sample_df):
    """atomic_write creates parent directories if they don't exist."""
    filepath = os.path.join(temp_dir, "subdir", "nested", "test.parquet")

    atomic_write(sample_df, filepath)

    assert os.path.exists(filepath)


def test_atomic_write_checksum_deterministic(temp_dir, sample_df):
    """Same data produces same checksum."""
    filepath1 = os.path.join(temp_dir, "test1.parquet")
    filepath2 = os.path.join(temp_dir, "test2.parquet")

    atomic_write(sample_df, filepath1, checksum=True)
    atomic_write(sample_df, filepath2, checksum=True)

    with open(filepath1 + ".sha256", "r") as f:
        checksum1 = f.read().strip()
    with open(filepath2 + ".sha256", "r") as f:
        checksum2 = f.read().strip()

    assert checksum1 == checksum2


def test_atomic_read_corrupted_parquet(temp_dir):
    """atomic_read raises CacheCorruptionError for corrupted Parquet file."""
    filepath = os.path.join(temp_dir, "corrupted.parquet")

    # Write garbage data
    with open(filepath, "wb") as f:
        f.write(b"NOT A VALID PARQUET FILE")

    with pytest.raises(CacheCorruptionError) as exc_info:
        atomic_read(filepath)

    assert "Failed to read cache file" in str(exc_info.value)
    assert exc_info.value.hint is not None


def test_cache_corruption_error_attributes():
    """CacheCorruptionError preserves message, hint, and context."""
    error = CacheCorruptionError(
        "Test corruption",
        hint="Delete cache",
        context={"file": "test.parquet"},
    )

    assert error.message == "Test corruption"
    assert error.hint == "Delete cache"
    assert error.context == {"file": "test.parquet"}
    assert "Test corruption" in str(error)
    assert "Delete cache" in str(error)
