"""
Peak_Trade – Data-Layer Performance Tests
==========================================

Performance-Tests für Data-Layer (Phase 85):
- Cache-Hit Performance
- Normalize Throughput
- Large Dataset Handling

Diese Tests sind standardmäßig GESKIPPT.

Usage:
    # Skip per default (via pytest marker)
    pytest tests/test_data_layer_performance.py -v  # Alle geskippt

    # Run explizit
    RUN_PERF=1 pytest tests/test_data_layer_performance.py -v
    pytest tests/test_data_layer_performance.py -v --run-perf

    # Nur Performance-Tests
    pytest -m data_perf -v --run-perf

Policy:
- Zeitbudgets großzügig gewählt (keine flakey thresholds)
- Tests sollten deterministisch sein (kein Netzwerk)
- Performance-Regressions-Detection, nicht Absolute-Benchmarks
"""

from __future__ import annotations

import os
import time
from pathlib import Path

import pytest
import pandas as pd
import numpy as np

from tests.utils.dt import normalize_dt_index
from src.data import (
    DataNormalizer,
    ParquetCache,
    REQUIRED_OHLCV_COLUMNS,
)


# ============================================================================
# SKIP LOGIC
# ============================================================================
# Skip logic is handled in tests/conftest.py via pytest_collection_modifyitems


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def large_dataset():
    """
    Erstellt großes OHLCV-Dataset für Performance-Tests.

    Returns:
        DataFrame mit 10.000 Bars (ca. 1 Jahr bei 1h)
    """
    n_bars = 10_000
    np.random.seed(42)

    idx = pd.date_range(
        start="2024-01-01 00:00:00",
        periods=n_bars,
        freq="1h",
        tz="UTC",
    )

    close_prices = 50000 * np.exp(np.cumsum(np.random.normal(0, 0.01, n_bars)))
    df = pd.DataFrame(index=idx)
    df["open"] = close_prices * (1 + np.random.uniform(-0.001, 0.001, n_bars))
    df["close"] = close_prices
    df["high"] = np.maximum(df["open"], df["close"]) * 1.005
    df["low"] = np.minimum(df["open"], df["close"]) * 0.995
    df["volume"] = np.random.uniform(100, 1000, n_bars)

    # Reorder columns to match REQUIRED_OHLCV_COLUMNS
    df = df[REQUIRED_OHLCV_COLUMNS]

    return df


@pytest.fixture
def cache_with_data(tmp_path, large_dataset):
    """
    Erstellt Cache mit vorgeladenen Daten.

    Returns:
        ParquetCache mit gespeichertem large_dataset
    """
    cache = ParquetCache(cache_dir=str(tmp_path / "cache"))
    cache.save(large_dataset, "perf_test")
    return cache


# ============================================================================
# TEST 1: CACHE HIT PERFORMANCE
# ============================================================================


@pytest.mark.data_perf
class TestCacheHitPerformance:
    """Tests für Cache-Hit-Performance."""

    def test_cache_hit_is_fast_and_fetch_called_once(self, cache_with_data, large_dataset):
        """
        Cache-Hit sollte schnell sein und Fetch nur einmal aufrufen.

        Budget: <100ms für 10k Bars aus Cache
        Rationale: Parquet-Loading ist optimiert; 100ms ist sehr großzügig
        """
        cache = cache_with_data

        # Warmup (falls Dateisystem-Cache cold start)
        _ = cache.load("perf_test")

        # Measure Cache-Hit Performance
        start_time = time.perf_counter()
        df = cache.load("perf_test")
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        # Assertions
        assert len(df) == len(large_dataset)
        assert elapsed_ms < 100, f"Cache-Hit dauerte {elapsed_ms:.1f}ms (Budget: 100ms)"

        # Verify DataFrame ist korrekt
        assert list(df.columns) == REQUIRED_OHLCV_COLUMNS
        assert isinstance(df.index, pd.DatetimeIndex)

    def test_cache_multiple_hits_consistent_performance(self, cache_with_data):
        """
        Mehrere Cache-Hits sollten konsistente Performance haben.

        Policy: Keine Performance-Degradation bei wiederholten Hits
        """
        cache = cache_with_data
        timings = []

        # 5 aufeinanderfolgende Cache-Hits
        for _ in range(5):
            start_time = time.perf_counter()
            df = cache.load("perf_test")
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            timings.append(elapsed_ms)

        # Alle sollten unter 100ms sein
        for i, t in enumerate(timings):
            assert t < 100, f"Hit {i + 1} dauerte {t:.1f}ms (Budget: 100ms)"

        # Variance sollte gering sein (kein Outlier > 2x Median)
        median_time = sorted(timings)[len(timings) // 2]
        for i, t in enumerate(timings):
            assert t < median_time * 2.5, (
                f"Hit {i + 1} ({t:.1f}ms) ist Outlier (Median: {median_time:.1f}ms)"
            )


# ============================================================================
# TEST 2: NORMALIZE THROUGHPUT
# ============================================================================


@pytest.mark.data_perf
class TestNormalizeThroughput:
    """Tests für Normalize-Throughput."""

    def test_normalize_throughput_under_budget(self, large_dataset):
        """
        Normalizer sollte großes Dataset schnell verarbeiten.

        Budget: <50ms für 10k Bars
        Rationale: Normalizer macht nur einfache Operationen (rename, sort, dedupe)
        """
        # Entferne Timezone für realistischen Test (wird oft so kommen)
        df = large_dataset.copy()
        df.index = df.index.tz_localize(None)

        start_time = time.perf_counter()
        result = DataNormalizer.normalize(df, ensure_utc=True)
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        # Assertions
        assert len(result) == len(large_dataset)
        assert elapsed_ms < 50, f"Normalize dauerte {elapsed_ms:.1f}ms (Budget: 50ms)"

        # Verify korrekte Normalisierung
        assert result.index.tz is not None
        assert str(result.index.tz) == "UTC"
        assert list(result.columns) == REQUIRED_OHLCV_COLUMNS

    def test_normalize_with_duplicates_throughput(self):
        """
        Normalizer sollte Duplikate effizient entfernen.

        Budget: <100ms für 10k Bars mit 10% Duplikaten
        """
        n_bars = 10_000
        n_dupes = 1_000

        # Erstelle Dataset mit Duplikaten
        idx_unique = pd.date_range("2024-01-01", periods=n_bars, freq="1h", tz="UTC")
        idx_dupes = pd.DatetimeIndex(np.random.choice(idx_unique, n_dupes))
        idx_combined = idx_unique.append(idx_dupes)

        df = pd.DataFrame(
            {
                "open": np.random.uniform(90000, 100000, len(idx_combined)),
                "high": np.random.uniform(95000, 105000, len(idx_combined)),
                "low": np.random.uniform(85000, 95000, len(idx_combined)),
                "close": np.random.uniform(90000, 100000, len(idx_combined)),
                "volume": np.random.uniform(100, 1000, len(idx_combined)),
            },
            index=idx_combined,
        )

        start_time = time.perf_counter()
        result = DataNormalizer.normalize(df)
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        # Assertions
        assert len(result) == n_bars  # Duplikate entfernt
        assert elapsed_ms < 100, (
            f"Normalize mit Duplikaten dauerte {elapsed_ms:.1f}ms (Budget: 100ms)"
        )

    def test_normalize_large_column_mapping_throughput(self, large_dataset):
        """
        Normalizer sollte große Column-Mappings effizient handhaben.

        Budget: <60ms für 10k Bars mit Column-Mapping
        """
        # Rename columns to non-standard names
        df = large_dataset.copy()
        df = df.rename(
            columns={
                "open": "Open",
                "high": "High",
                "low": "Low",
                "close": "Close",
                "volume": "Volume",
            }
        )

        column_mapping = {
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume",
        }

        start_time = time.perf_counter()
        result = DataNormalizer.normalize(df, column_mapping=column_mapping)
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        assert len(result) == len(large_dataset)
        assert elapsed_ms < 60, f"Normalize mit Mapping dauerte {elapsed_ms:.1f}ms (Budget: 60ms)"
        assert list(result.columns) == REQUIRED_OHLCV_COLUMNS


# ============================================================================
# TEST 3: CACHE SAVE PERFORMANCE
# ============================================================================


@pytest.mark.data_perf
class TestCacheSavePerformance:
    """Tests für Cache-Save-Performance."""

    def test_cache_save_throughput_under_budget(self, tmp_path, large_dataset):
        """
        Cache-Save sollte großes Dataset schnell speichern.

        Budget: <200ms für 10k Bars
        Rationale: Parquet-Kompression + Disk-IO; 200ms ist großzügig
        """
        cache = ParquetCache(cache_dir=str(tmp_path / "cache"))

        start_time = time.perf_counter()
        cache.save(large_dataset, "save_perf_test")
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        assert elapsed_ms < 200, f"Cache-Save dauerte {elapsed_ms:.1f}ms (Budget: 200ms)"

        # Verify File existiert
        assert cache.exists("save_perf_test")

    def test_cache_roundtrip_preserves_data_and_is_fast(self, tmp_path, large_dataset):
        """
        Cache Save -> Load Roundtrip sollte Daten erhalten und schnell sein.

        Budget: <300ms für 10k Bars (Save + Load)
        """
        cache = ParquetCache(cache_dir=str(tmp_path / "cache"))

        start_time = time.perf_counter()
        cache.save(large_dataset, "roundtrip_test")
        loaded = cache.load("roundtrip_test")
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        assert elapsed_ms < 300, f"Cache-Roundtrip dauerte {elapsed_ms:.1f}ms (Budget: 300ms)"

        # Verify Daten identisch (check_freq=False weil Parquet freq nicht erhält); Index ns für Roundtrip
        pd.testing.assert_frame_equal(
            normalize_dt_index(large_dataset, ensure_utc=True),
            normalize_dt_index(loaded, ensure_utc=True),
            check_freq=False,
        )


# ============================================================================
# TEST 4: MEMORY EFFICIENCY (Optional)
# ============================================================================


@pytest.mark.data_perf
class TestMemoryEfficiency:
    """Tests für Memory-Effizienz (optional)."""

    def test_normalize_does_not_cause_memory_explosion(self):
        """
        Normalizer sollte keine exzessive Memory-Kopien erstellen.

        Policy: Normalizer erstellt 1 Kopie (df.copy()), keine weiteren Deep-Copies
        Rationale: Performance + Memory-Footprint für große Datasets
        """
        n_bars = 50_000  # Größeres Dataset für Memory-Test
        idx = pd.date_range("2020-01-01", periods=n_bars, freq="1h", tz="UTC")

        df = pd.DataFrame(
            {
                "open": np.random.uniform(90000, 100000, n_bars),
                "high": np.random.uniform(95000, 105000, n_bars),
                "low": np.random.uniform(85000, 95000, n_bars),
                "close": np.random.uniform(90000, 100000, n_bars),
                "volume": np.random.uniform(100, 1000, n_bars),
            },
            index=idx,
        )

        # Normalizer sollte unter 100ms bleiben auch für 50k Bars
        start_time = time.perf_counter()
        result = DataNormalizer.normalize(df)
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        assert elapsed_ms < 100, (
            f"Normalize für 50k Bars dauerte {elapsed_ms:.1f}ms (Budget: 100ms)"
        )

        # Verify korrekte Anzahl Rows
        assert len(result) == n_bars


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "--run-perf"])
