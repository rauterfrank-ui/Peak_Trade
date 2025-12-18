"""
Stability Smoke Test (Wave B) - Deterministic E2E
==================================================
Fast end-to-end test (<10s) that validates all Wave A+B stability features:

Wave A:
- Error taxonomy
- Data contracts
- Atomic cache writes
- Reproducibility framework

Wave B:
- Cache manifest
- Metadata helpers (git SHA, config hash)
- Full deterministic roundtrip

Test Flow:
1. Create dummy data
2. Validate with contracts
3. Write to cache atomically
4. Track in manifest
5. Validate manifest
6. Read back and verify determinism
"""
import os
import tempfile
from pathlib import Path

import pandas as pd
import pytest

# Wave A imports
from src.core.errors import DataContractError
from src.core.repro import ReproContext, set_global_seed, verify_determinism
from src.data.cache_atomic import atomic_read, atomic_write
from src.data.contracts import validate_ohlcv

# Wave B imports
from src.core.repro import get_git_sha, stable_hash_dict
from src.data.cache_manifest import CacheManifest


@pytest.fixture
def temp_cache_dir():
    """Create temporary cache directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_ohlcv():
    """Create sample OHLCV DataFrame."""
    dates = pd.date_range("2024-01-01", periods=100, freq="1h", tz="UTC")
    df = pd.DataFrame(
        {
            "open": [100.0 + i * 0.1 for i in range(100)],
            "high": [101.0 + i * 0.1 for i in range(100)],
            "low": [99.0 + i * 0.1 for i in range(100)],
            "close": [100.5 + i * 0.1 for i in range(100)],
            "volume": [1000.0 + i * 10 for i in range(100)],
        },
        index=dates,
    )
    return df


def test_stability_smoke_full_e2e(temp_cache_dir, sample_ohlcv):
    """
    Full E2E smoke test for Wave A+B stability features.

    Steps:
    1. Create reproducibility context
    2. Validate data contracts
    3. Write cache atomically
    4. Track in manifest
    5. Validate manifest
    6. Read back and verify
    """
    # === Step 1: Create repro context ===
    config = {"strategy": "test_strategy", "seed": 42}
    ctx = ReproContext.create(seed=42, config_dict=config)

    assert ctx.seed == 42
    assert ctx.run_id is not None
    assert len(ctx.config_hash) == 16

    # Set global seed for determinism
    set_global_seed(42)

    # === Step 2: Validate data contracts ===
    # Should not raise (valid OHLCV)
    validate_ohlcv(sample_ohlcv)

    # === Step 3: Write cache atomically with checksum ===
    cache_file = os.path.join(temp_cache_dir, "data.parquet")
    atomic_write(sample_ohlcv, cache_file, checksum=True)

    # Verify checksum file exists
    checksum_file = cache_file + ".sha256"
    assert os.path.exists(checksum_file)

    # === Step 4: Track in manifest ===
    manifest = CacheManifest.load_or_create(
        cache_dir=temp_cache_dir,
        run_id=ctx.run_id,
        git_sha=get_git_sha(),
        config_hash=stable_hash_dict(config),
    )

    manifest.add_file(cache_file, schema_version="v1")
    manifest.save()

    # Verify manifest saved
    manifest_path = os.path.join(temp_cache_dir, "manifest.json")
    assert os.path.exists(manifest_path)

    # === Step 5: Validate manifest ===
    # Load and validate all files
    loaded_manifest = CacheManifest.load(manifest_path)
    loaded_manifest.validate()  # Should not raise

    # Verify metadata
    assert loaded_manifest.run_id == ctx.run_id
    assert loaded_manifest.git_sha == get_git_sha()
    assert loaded_manifest.config_hash == stable_hash_dict(config)
    assert len(loaded_manifest.files) == 1

    # === Step 6: Read back and verify ===
    # Read with checksum verification
    df_loaded = atomic_read(cache_file, verify_checksum=True)

    # Verify data integrity (check_freq=False to ignore timezone freq differences)
    pd.testing.assert_frame_equal(df_loaded, sample_ohlcv, check_freq=False)


def test_stability_smoke_contract_violation():
    """Test that contract violations are caught."""
    # Create invalid OHLCV (missing column)
    dates = pd.date_range("2024-01-01", periods=10, freq="1h", tz="UTC")
    invalid_df = pd.DataFrame(
        {
            "open": range(10),
            "high": range(10),
            # Missing 'low', 'close', 'volume'
        },
        index=dates,
    )

    with pytest.raises(DataContractError) as exc_info:
        validate_ohlcv(invalid_df)

    assert "missing required" in str(exc_info.value).lower()


def test_stability_smoke_cache_corruption_detection(temp_cache_dir, sample_ohlcv):
    """Test that cache corruption is detected via checksum."""
    from src.core.errors import CacheCorruptionError

    # Write file with checksum
    cache_file = os.path.join(temp_cache_dir, "data.parquet")
    atomic_write(sample_ohlcv, cache_file, checksum=True)

    # Corrupt file by directly overwriting (bypassing atomic_write)
    corrupted_df = sample_ohlcv * 2
    # Use pandas directly to corrupt, not atomic_write
    import pandas as pd
    corrupted_df.to_parquet(cache_file, compression="snappy", index=True)

    # Reading with checksum verification should fail
    with pytest.raises(CacheCorruptionError) as exc_info:
        atomic_read(cache_file, verify_checksum=True)

    assert "checksum mismatch" in str(exc_info.value).lower()


def test_stability_smoke_deterministic_run():
    """Test that runs with same seed produce identical results."""

    def random_computation():
        """Simple random computation."""
        import random

        return sum(random.random() for _ in range(100))

    # Run 1
    set_global_seed(42)
    result1 = random_computation()

    # Run 2 with same seed
    set_global_seed(42)
    result2 = random_computation()

    # Should be identical
    assert result1 == result2

    # Run 3 with different seed
    set_global_seed(43)
    result3 = random_computation()

    # Should be different
    assert result1 != result3


def test_stability_smoke_manifest_multi_file(temp_cache_dir, sample_ohlcv):
    """Test manifest with multiple files."""
    manifest = CacheManifest.load_or_create(
        cache_dir=temp_cache_dir,
        run_id="test_multi_file",
        git_sha="abc1234",
        config_hash="def5678",
    )

    # Add multiple files
    for i in range(3):
        filepath = os.path.join(temp_cache_dir, f"data_{i}.parquet")
        atomic_write(sample_ohlcv, filepath, checksum=True)
        manifest.add_file(filepath, schema_version=f"v{i+1}")

    manifest.save()

    # Validate all files
    manifest.validate()

    # Verify
    assert len(manifest.files) == 3
    for i, entry in enumerate(manifest.files):
        assert entry.schema_version == f"v{i+1}"


def test_stability_smoke_config_hash_stability():
    """Test that config hash is stable across runs."""
    config = {
        "strategy": "ma_crossover",
        "fast_period": 10,
        "slow_period": 20,
        "symbol": "BTC/USDT",
    }

    # Hash 1
    hash1 = stable_hash_dict(config)

    # Hash 2 (same config)
    hash2 = stable_hash_dict(config)

    # Should be identical
    assert hash1 == hash2

    # Hash 3 (different key order, same values)
    config_reordered = {
        "symbol": "BTC/USDT",
        "strategy": "ma_crossover",
        "slow_period": 20,
        "fast_period": 10,
    }
    hash3 = stable_hash_dict(config_reordered)

    # Should still be identical (key-order independent)
    assert hash1 == hash3


def test_stability_smoke_reproducibility_context_roundtrip():
    """Test ReproContext serialization roundtrip."""
    config = {"seed": 42, "strategy": "test"}
    ctx = ReproContext.create(seed=42, config_dict=config)

    # Serialize to dict
    ctx_dict = ctx.to_dict()

    # Verify all fields present
    assert "run_id" in ctx_dict
    assert "seed" in ctx_dict
    assert "config_hash" in ctx_dict
    assert "git_sha" in ctx_dict
    assert "python_version" in ctx_dict
    assert "platform" in ctx_dict

    # Serialize to JSON
    ctx_json = ctx.to_json()
    assert isinstance(ctx_json, str)
    assert ctx.run_id in ctx_json


# === Performance Check ===
def test_stability_smoke_performance_check(temp_cache_dir, sample_ohlcv):
    """
    Performance check: full E2E should run in < 1 second.

    This ensures the smoke test stays fast.
    """
    import time

    start = time.perf_counter()

    # Full E2E flow
    ctx = ReproContext.create(seed=42)
    validate_ohlcv(sample_ohlcv)

    cache_file = os.path.join(temp_cache_dir, "perf_test.parquet")
    atomic_write(sample_ohlcv, cache_file, checksum=True)

    manifest = CacheManifest.load_or_create(
        cache_dir=temp_cache_dir,
        run_id=ctx.run_id,
    )
    manifest.add_file(cache_file)
    manifest.save()
    manifest.validate()

    df_loaded = atomic_read(cache_file, verify_checksum=True)
    pd.testing.assert_frame_equal(df_loaded, sample_ohlcv, check_freq=False)

    elapsed = time.perf_counter() - start

    # Should complete in < 1 second
    assert elapsed < 1.0, f"Smoke test took {elapsed:.2f}s (expected < 1.0s)"
