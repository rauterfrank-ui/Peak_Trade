"""
Peak_Trade – Data-Layer Integration Tests
==========================================

Integration-Tests für den kompletten Data-Layer-Pipeline (Phase 85):
- Fetch → Cache → Normalize (deterministisch)
- Pipeline-to-Backtest Smoke-Test (optional)

Diese Tests nutzen KEINE externen APIs (kein Netzwerk).
Alle Tests sind deterministisch und schnell (<1s).

Usage:
    pytest tests/test_data_layer_integration.py -v
    pytest -m data_integration -v

Policy:
- Kein Netzwerk-Zugriff (nur lokale Fixtures)
- Deterministisch (feste Seeds, keine Time-Dependencies)
- Schnell (<1s pro Test)
"""

from __future__ import annotations

import os
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

from src.data import (
    DataNormalizer,
    CsvLoader,
    KrakenCsvLoader,
    ParquetCache,
    REQUIRED_OHLCV_COLUMNS,
    resample_ohlcv,
)


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def test_ohlcv_data():
    """
    Erstellt Test-OHLCV-Dataset.

    Returns:
        DataFrame mit 1000 Bars (deterministisch)
    """
    n_bars = 1000
    np.random.seed(42)

    idx = pd.date_range(
        start="2025-01-01 00:00:00",
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

    return df


@pytest.fixture
def raw_kraken_csv(tmp_path, test_ohlcv_data):
    """
    Erstellt Kraken-Format CSV für Tests.

    Returns:
        Path zur CSV-Datei
    """
    csv_path = tmp_path / "kraken_test.csv"

    # Konvertiere zu Kraken-Format (Unix-Timestamp)
    df = test_ohlcv_data.copy()
    df["time"] = (df.index.astype(int) // 10**9).astype(int)  # DatetimeIndex -> Unix-Timestamp
    df["vwap"] = (df["high"] + df["low"]) / 2  # Fake VWAP
    df["count"] = 100  # Fake trade count

    # Spalten-Reihenfolge wie Kraken
    df = df[["time", "open", "high", "low", "close", "vwap", "volume", "count"]]
    df = df.reset_index(drop=True)

    # Als CSV speichern
    df.to_csv(csv_path, index=False)

    return csv_path


# ============================================================================
# TEST 1: PIPELINE FETCH-CACHE-NORMALIZE DETERMINISTIC
# ============================================================================


@pytest.mark.data_integration
class TestPipelineFetchCacheNormalize:
    """Integration-Tests für vollständigen Data-Pipeline."""

    def test_pipeline_fetch_cache_normalize_is_deterministic(
        self, tmp_path, raw_kraken_csv, test_ohlcv_data
    ):
        """
        Vollständiger Pipeline-Test: Load → Normalize → Cache → Load.

        Pipeline:
        1. CSV-Loader lädt Kraken-CSV
        2. Normalizer konvertiert zu Peak_Trade-Format
        3. Cache speichert normalisierte Daten
        4. Cache lädt Daten wieder
        5. Verifiziere: Daten sind identisch (deterministisch)

        Policy: Pipeline muss deterministisch sein (keine Daten-Veränderung).
        """
        cache = ParquetCache(cache_dir=str(tmp_path / "cache"))

        # STEP 1: Load Kraken CSV
        loader = KrakenCsvLoader()
        raw_df = loader.load(str(raw_kraken_csv))

        # Verify Raw-Daten
        assert isinstance(raw_df.index, pd.DatetimeIndex)
        assert "open" in raw_df.columns
        assert "vwap" in raw_df.columns  # Kraken-spezifisch

        # STEP 2: Normalize
        normalized_df = DataNormalizer.normalize(
            raw_df,
            ensure_utc=True,
            drop_extra_columns=True,
        )

        # Verify Normalisierte Daten
        assert list(normalized_df.columns) == REQUIRED_OHLCV_COLUMNS
        assert normalized_df.index.tz is not None
        assert str(normalized_df.index.tz) == "UTC"
        assert len(normalized_df) == 1000

        # STEP 3: Cache speichern
        cache.save(normalized_df, "integration_test")
        assert cache.exists("integration_test")

        # STEP 4: Cache laden
        cached_df = cache.load("integration_test")

        # STEP 5: Verify Determinismus (Daten identisch)
        pd.testing.assert_frame_equal(normalized_df, cached_df, check_freq=False)

        # Zusätzliche Checks
        assert len(cached_df) == 1000
        assert list(cached_df.columns) == REQUIRED_OHLCV_COLUMNS

    def test_pipeline_with_column_mapping_and_cache(self, tmp_path):
        """
        Pipeline mit Custom-Column-Mapping.

        Scenario: Externe CSV mit anderen Spaltennamen → Normalizer → Cache
        """
        # STEP 1: Erstelle CSV mit Custom-Spalten
        csv_path = tmp_path / "custom.csv"
        n_bars = 100
        idx = pd.date_range("2025-01-01", periods=n_bars, freq="1h", tz="UTC")

        df_custom = pd.DataFrame(
            {
                "timestamp": idx,
                "Open": np.random.uniform(90000, 100000, n_bars),
                "High": np.random.uniform(95000, 105000, n_bars),
                "Low": np.random.uniform(85000, 95000, n_bars),
                "Close": np.random.uniform(90000, 100000, n_bars),
                "Vol": np.random.uniform(100, 1000, n_bars),
            }
        )
        df_custom.to_csv(csv_path, index=False)

        # STEP 2: Load mit CsvLoader
        loader = CsvLoader(parse_dates=True)
        raw_df = loader.load(str(csv_path))

        # STEP 3: Normalize mit Column-Mapping
        column_mapping = {
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Vol": "volume",
        }
        normalized_df = DataNormalizer.normalize(
            raw_df,
            column_mapping=column_mapping,
            ensure_utc=True,
        )

        # STEP 4: Cache
        cache = ParquetCache(cache_dir=str(tmp_path / "cache"))
        cache.save(normalized_df, "custom_test")

        # STEP 5: Verify
        cached_df = cache.load("custom_test")
        assert list(cached_df.columns) == REQUIRED_OHLCV_COLUMNS
        assert len(cached_df) == n_bars

    def test_pipeline_roundtrip_preserves_precision(self, tmp_path, test_ohlcv_data):
        """
        Pipeline Roundtrip sollte Float-Precision erhalten.

        Policy: Parquet sollte Float64-Precision erhalten (kein Precision-Loss).
        """
        cache = ParquetCache(cache_dir=str(tmp_path / "cache"))

        # Original-Daten
        original_df = test_ohlcv_data.copy()

        # Save → Load
        cache.save(original_df, "precision_test")
        loaded_df = cache.load("precision_test")

        # Verify Precision (exakte Float-Werte)
        pd.testing.assert_frame_equal(original_df, loaded_df, check_freq=False)

        # Specific Precision-Check
        assert original_df["close"].iloc[0] == loaded_df["close"].iloc[0]
        assert original_df["volume"].iloc[42] == loaded_df["volume"].iloc[42]


# ============================================================================
# TEST 2: RESAMPLE INTEGRATION
# ============================================================================


@pytest.mark.data_integration
class TestResampleIntegration:
    """Integration-Tests für Resample-Funktionalität."""

    def test_pipeline_resample_1h_to_4h_integration(self, test_ohlcv_data, tmp_path):
        """
        Resample 1h → 4h und cache das Resultat.

        Policy: Resample sollte OHLCV-Semantik korrekt handhaben.
        """
        # STEP 1: Resample
        df_4h = resample_ohlcv(test_ohlcv_data, freq="4h")

        # Verify Resample (ca. 1000/4, aber Resample kann Edge-Cases haben)
        assert 240 <= len(df_4h) <= 260  # Flexibler Check
        assert list(df_4h.columns) == REQUIRED_OHLCV_COLUMNS

        # STEP 2: Cache
        cache = ParquetCache(cache_dir=str(tmp_path / "cache"))
        cache.save(df_4h, "resample_4h")

        # STEP 3: Verify
        loaded = cache.load("resample_4h")
        pd.testing.assert_frame_equal(df_4h, loaded, check_freq=False)

    def test_resample_preserves_ohlc_semantics(self, test_ohlcv_data):
        """
        Resample sollte OHLC-Semantik korrekt handhaben.

        Policy:
        - high: >= max(open, close) für alle Bars
        - low: <= min(open, close) für alle Bars
        - volume: Sollte aggregiert werden (Summe > einzelne Werte)

        Dieser Test verifiziert grundlegende OHLC-Constraints, ohne sich
        auf exakte Intervall-Matching zu verlassen (label/closed-unabhängig).
        """
        df_1h = test_ohlcv_data.copy()

        # Resample zu 4h
        df_4h = resample_ohlcv(df_1h, freq="4h")

        # Verify OHLC-Constraints für alle resampled Bars
        for idx in range(len(df_4h)):
            row = df_4h.iloc[idx]

            # High sollte >= max(open, close) sein
            assert row["high"] >= max(row["open"], row["close"]), (
                f"High constraint verletzt bei {df_4h.index[idx]}"
            )

            # Low sollte <= min(open, close) sein
            assert row["low"] <= min(row["open"], row["close"]), (
                f"Low constraint verletzt bei {df_4h.index[idx]}"
            )

            # Volume sollte positiv sein
            assert row["volume"] > 0, f"Volume sollte positiv sein bei {df_4h.index[idx]}"

        # Verify Aggregation: Gesamtvolumen sollte erhalten bleiben
        assert df_4h["volume"].sum() == pytest.approx(df_1h["volume"].sum())


# ============================================================================
# TEST 3: CACHE ISOLATION
# ============================================================================


@pytest.mark.data_integration
class TestCacheIsolation:
    """Tests für Cache-Isolation (keine Interferenz zwischen Tests)."""

    def test_multiple_cache_keys_isolated(self, tmp_path, test_ohlcv_data):
        """
        Mehrere Cache-Keys sollten isoliert sein (keine Interferenz).

        Policy: Verschiedene Keys sollten verschiedene Daten speichern.
        """
        cache = ParquetCache(cache_dir=str(tmp_path / "cache"))

        # Save unter verschiedenen Keys
        df1 = test_ohlcv_data.iloc[:100].copy()
        df2 = test_ohlcv_data.iloc[100:200].copy()

        cache.save(df1, "key1")
        cache.save(df2, "key2")

        # Load und verify
        loaded1 = cache.load("key1")
        loaded2 = cache.load("key2")

        pd.testing.assert_frame_equal(df1, loaded1, check_freq=False)
        pd.testing.assert_frame_equal(df2, loaded2, check_freq=False)

        # Verify keine Interferenz
        assert len(loaded1) == 100
        assert len(loaded2) == 100
        assert not loaded1.equals(loaded2)

    def test_cache_clear_specific_key(self, tmp_path, test_ohlcv_data):
        """
        Cache-Clear sollte nur spezifischen Key löschen.

        Policy: clear(key) löscht nur einen Key, andere bleiben erhalten.
        """
        cache = ParquetCache(cache_dir=str(tmp_path / "cache"))

        # Save mehrere Keys
        cache.save(test_ohlcv_data, "keep")
        cache.save(test_ohlcv_data, "delete")

        assert cache.exists("keep")
        assert cache.exists("delete")

        # Clear nur "delete"
        cache.clear("delete")

        assert cache.exists("keep")
        assert not cache.exists("delete")

    def test_cache_clear_all(self, tmp_path, test_ohlcv_data):
        """
        Cache-Clear ohne Key sollte alle Caches löschen.

        Policy: clear() löscht alle Cache-Files.
        """
        cache = ParquetCache(cache_dir=str(tmp_path / "cache"))

        # Save mehrere Keys
        cache.save(test_ohlcv_data, "key1")
        cache.save(test_ohlcv_data, "key2")

        assert cache.exists("key1")
        assert cache.exists("key2")

        # Clear all
        cache.clear()

        assert not cache.exists("key1")
        assert not cache.exists("key2")


# ============================================================================
# TEST 4: PIPELINE TO BACKTEST SMOKE (Optional)
# ============================================================================


@pytest.mark.data_integration
class TestPipelineToBacktestSmoke:
    """Smoke-Tests für Pipeline → Backtest Integration (optional)."""

    def test_pipeline_to_backtest_smoke(self, tmp_path, test_ohlcv_data):
        """
        Smoke-Test: Pipeline → Backtest-kompatible Daten.

        Scenario: Verifiziere dass Pipeline-Output backtest-ready ist.

        Policy:
        - DatetimeIndex (UTC)
        - OHLCV-Spalten
        - Keine NaN in OHLC (Volume NaN ist OK)
        - Sortiert
        - Keine Duplikate

        Note: Dies ist ein minimaler Smoke-Test (<1s).
        Volle Backtest-Integration wird in separaten Tests geprüft.
        """
        cache = ParquetCache(cache_dir=str(tmp_path / "cache"))

        # Pipeline-Output simulieren
        normalized_df = DataNormalizer.normalize(test_ohlcv_data)
        cache.save(normalized_df, "backtest_ready")

        # Load als Backtest-Input
        backtest_input = cache.load("backtest_ready")

        # Verify Backtest-Ready Properties
        # 1. DatetimeIndex UTC
        assert isinstance(backtest_input.index, pd.DatetimeIndex)
        assert backtest_input.index.tz is not None
        assert str(backtest_input.index.tz) == "UTC"

        # 2. OHLCV-Spalten
        assert list(backtest_input.columns) == REQUIRED_OHLCV_COLUMNS

        # 3. Keine NaN in OHLC
        assert not backtest_input["open"].isna().any()
        assert not backtest_input["high"].isna().any()
        assert not backtest_input["low"].isna().any()
        assert not backtest_input["close"].isna().any()

        # 4. Sortiert
        assert backtest_input.index.is_monotonic_increasing

        # 5. Keine Duplikate
        assert not backtest_input.index.duplicated().any()

    def test_pipeline_output_works_with_pandas_operations(self, tmp_path, test_ohlcv_data):
        """
        Pipeline-Output sollte mit Standard-Pandas-Operationen funktionieren.

        Scenario: Simuliere typische Backtest-Operationen (Rolling, Shift, etc.)
        """
        cache = ParquetCache(cache_dir=str(tmp_path / "cache"))

        normalized_df = DataNormalizer.normalize(test_ohlcv_data)
        cache.save(normalized_df, "pandas_ops")
        df = cache.load("pandas_ops")

        # Typische Backtest-Operationen
        # 1. Rolling Mean (MA)
        df["sma_20"] = df["close"].rolling(20).mean()
        assert not df["sma_20"].iloc[20:].isna().all()  # Nach Warmup keine NaN

        # 2. Pct Change (Returns)
        df["returns"] = df["close"].pct_change()
        assert len(df["returns"]) == len(df)

        # 3. Shift (Lag)
        df["close_lag1"] = df["close"].shift(1)
        assert df["close_lag1"].iloc[1] == df["close"].iloc[0]

        # 4. Boolean Indexing
        high_volume = df[df["volume"] > df["volume"].median()]
        assert len(high_volume) > 0

        # All operations should work without errors
        assert True


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
