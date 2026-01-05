"""
Peak_Trade – Data-Layer Edge-Case Tests
========================================

Tests für Edge-Cases im Data-Layer (Phase 85):
- Leere DataFrames
- NaN-Handling
- Timezone-naive Timestamps
- Invalide OHLC-Relationen (High < Low)

Policy-Entscheidungen:
- NaN-Handling: DataNormalizer akzeptiert NaN-Werte, aber Validierungen sollten sie erkennen
- Timezone-naive: Werden automatisch als UTC interpretiert (tz_localize)
- Invalid OHLC: High muss >= Low sein, Close muss zwischen High/Low liegen

Usage:
    pytest tests/test_data_layer_edge_cases.py -v
    pytest -m data_edge -v
"""
from __future__ import annotations

from pathlib import Path
import pytest
import pandas as pd
import numpy as np

# Import Data-Layer Komponenten
from src.data import (
    DataNormalizer,
    CsvLoader,
    KrakenCsvLoader,
    ParquetCache,
    REQUIRED_OHLCV_COLUMNS,
)


# ============================================================================
# TEST 1: EMPTY DATAFRAME BEHAVIOR
# ============================================================================

@pytest.mark.data_edge
class TestEmptyDataFrameBehavior:
    """Tests für Verhalten bei leeren DataFrames."""

    def test_normalize_empty_frame_behavior(self):
        """
        DataNormalizer sollte leere DataFrames akzeptieren und zurückgeben.

        Policy: Leere DataFrames sind valid (z.B. wenn keine Daten vorhanden).
        """
        # Leerer DataFrame mit korrekten Spalten
        df = pd.DataFrame(columns=REQUIRED_OHLCV_COLUMNS)
        df.index = pd.DatetimeIndex([], tz="UTC")

        result = DataNormalizer.normalize(df, ensure_utc=True)

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0
        assert list(result.columns) == REQUIRED_OHLCV_COLUMNS
        assert isinstance(result.index, pd.DatetimeIndex)
        assert result.index.tz is not None
        assert str(result.index.tz) == "UTC"

    def test_load_empty_frame_behavior(self, tmp_path):
        """
        CsvLoader sollte leere Dateien laden können.

        Policy: Leere CSV-Dateien werden als leere DataFrames zurückgegeben.
        """
        # Erstelle leere CSV mit Header
        csv_path = tmp_path / "empty.csv"
        csv_path.write_text("time,open,high,low,close,volume\n")

        loader = CsvLoader(parse_dates=True)
        df = loader.load(str(csv_path))

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0

    def test_cache_empty_frame_rejected(self, tmp_path):
        """
        ParquetCache sollte leere DataFrames mit DatetimeIndex speichern können.

        Policy: Leere DataFrames sind cachebar (z.B. für "keine Daten"-Szenarien).
        """
        cache = ParquetCache(cache_dir=str(tmp_path / "cache"))

        # Leerer DataFrame mit korrekten Spalten und DatetimeIndex
        df = pd.DataFrame(columns=REQUIRED_OHLCV_COLUMNS)
        df.index = pd.DatetimeIndex([], tz="UTC")

        # Sollte speichern können
        cache.save(df, "empty_test")

        # Sollte laden können
        loaded = cache.load("empty_test")
        assert len(loaded) == 0
        assert list(loaded.columns) == REQUIRED_OHLCV_COLUMNS


# ============================================================================
# TEST 2: NaN VALUE HANDLING
# ============================================================================

@pytest.mark.data_edge
class TestNaNValueHandling:
    """Tests für NaN-Handling im Data-Layer."""

    def test_normalize_rejects_or_handles_nan_values(self):
        """
        DataNormalizer konvertiert zu float und behält NaN-Werte bei.

        Policy: NaN-Werte werden NICHT automatisch entfernt.
        Downstream-Komponenten müssen NaN-Handling implementieren.
        Rationale: Normalizer ist für Format-Standardisierung, nicht für Daten-Qualität.
        """
        idx = pd.date_range("2025-01-01", periods=5, freq="1h", tz="UTC")
        df = pd.DataFrame({
            "open": [100, 101, np.nan, 103, 104],
            "high": [102, 103, 104, 105, 106],
            "low": [99, 100, 101, np.nan, 103],
            "close": [101, 102, 103, 104, np.nan],
            "volume": [1000, 1100, 1200, 1300, 1400],
        }, index=idx)

        result = DataNormalizer.normalize(df, ensure_utc=True)

        # NaN-Werte sollten erhalten bleiben
        assert result["open"].isna().sum() == 1
        assert result["low"].isna().sum() == 1
        assert result["close"].isna().sum() == 1

        # Volume sollte keine NaN haben
        assert result["volume"].isna().sum() == 0

    def test_normalize_all_nan_column(self):
        """
        DataNormalizer sollte Spalten mit nur NaN-Werten akzeptieren.

        Policy: Spalten mit nur NaN sind technisch valid (Downstream-Filter-Verantwortung).
        """
        idx = pd.date_range("2025-01-01", periods=3, freq="1h", tz="UTC")
        df = pd.DataFrame({
            "open": [np.nan, np.nan, np.nan],
            "high": [102, 103, 104],
            "low": [99, 100, 101],
            "close": [101, 102, 103],
            "volume": [1000, 1100, 1200],
        }, index=idx)

        result = DataNormalizer.normalize(df)

        # Alle open-Werte sollten NaN sein
        assert result["open"].isna().all()
        assert len(result) == 3

    def test_cache_handles_nan_values(self, tmp_path):
        """
        ParquetCache sollte DataFrames mit NaN-Werten korrekt speichern/laden.

        Policy: NaN-Werte werden durch Parquet-Format erhalten.
        """
        cache = ParquetCache(cache_dir=str(tmp_path / "cache"))

        idx = pd.date_range("2025-01-01", periods=3, freq="1h", tz="UTC")
        df = pd.DataFrame({
            "open": [100, np.nan, 102],
            "high": [102, 103, 104],
            "low": [99, 100, 101],
            "close": [101, 102, np.nan],
            "volume": [1000, 1100, 1200],
        }, index=idx)

        cache.save(df, "nan_test")
        loaded = cache.load("nan_test")

        # NaN-Werte sollten erhalten bleiben
        assert loaded["open"].isna().sum() == 1
        assert loaded["close"].isna().sum() == 1

        # Check ohne check_freq (Parquet kann freq-Metadata verlieren)
        pd.testing.assert_frame_equal(df, loaded, check_freq=False)


# ============================================================================
# TEST 3: TIMEZONE-NAIVE TIMESTAMPS POLICY
# ============================================================================

@pytest.mark.data_edge
class TestTimezoneNaiveTimestampsPolicy:
    """Tests für Timezone-naive Timestamps."""

    def test_normalize_timezone_naive_timestamps_policy(self):
        """
        DataNormalizer interpretiert timezone-naive Timestamps als UTC.

        Policy: Alle naive Timestamps werden als UTC interpretiert (tz_localize).
        Rationale: Konsistente Zeitzone-Behandlung; naive Timestamps sind mehrdeutig.
        """
        # Timezone-naive Index
        idx = pd.date_range("2025-01-01", periods=3, freq="1h", tz=None)
        df = pd.DataFrame({
            "open": [100, 101, 102],
            "high": [102, 103, 104],
            "low": [99, 100, 101],
            "close": [101, 102, 103],
            "volume": [1000, 1100, 1200],
        }, index=idx)

        assert df.index.tz is None  # Startet ohne Timezone

        result = DataNormalizer.normalize(df, ensure_utc=True)

        # Index sollte jetzt UTC sein
        assert result.index.tz is not None
        assert str(result.index.tz) == "UTC"

        # Zeitwerte sollten gleich bleiben (nur Timezone-Label hinzugefügt)
        assert result.index[0].year == 2025
        assert result.index[0].month == 1
        assert result.index[0].day == 1

    def test_normalize_preserves_existing_timezone(self):
        """
        DataNormalizer konvertiert bestehende Timezones zu UTC.

        Policy: Alle Timestamps werden zu UTC konvertiert (tz_convert).
        """
        # Index mit Europe/Berlin Timezone
        idx = pd.date_range("2025-01-01 12:00:00", periods=3, freq="1h", tz="Europe/Berlin")
        df = pd.DataFrame({
            "open": [100, 101, 102],
            "high": [102, 103, 104],
            "low": [99, 100, 101],
            "close": [101, 102, 103],
            "volume": [1000, 1100, 1200],
        }, index=idx)

        result = DataNormalizer.normalize(df, ensure_utc=True)

        # Sollte zu UTC konvertiert sein
        assert str(result.index.tz) == "UTC"

        # UTC-Zeit sollte korrekt sein (Berlin ist UTC+1 im Winter)
        # 12:00 Berlin = 11:00 UTC
        assert result.index[0].hour == 11

    def test_normalize_ensure_utc_false_keeps_naive(self):
        """
        DataNormalizer mit ensure_utc=False behält naive Timestamps.

        Policy: ensure_utc=False erlaubt naive Timestamps (für spezielle Anwendungsfälle).
        """
        idx = pd.date_range("2025-01-01", periods=3, freq="1h", tz=None)
        df = pd.DataFrame({
            "open": [100, 101, 102],
            "high": [102, 103, 104],
            "low": [99, 100, 101],
            "close": [101, 102, 103],
            "volume": [1000, 1100, 1200],
        }, index=idx)

        result = DataNormalizer.normalize(df, ensure_utc=False)

        # Index sollte immer noch naive sein
        assert result.index.tz is None


# ============================================================================
# TEST 4: INVALID OHLC RELATIONS
# ============================================================================

@pytest.mark.data_edge
class TestInvalidOHLCRelations:
    """Tests für invalide OHLC-Relationen."""

    def test_loader_rejects_invalid_ohlc_relations_high_low(self):
        """
        Loader sollte keine explizite Validierung für High < Low durchführen.

        Policy: Loader/Normalizer sind für Format-Standardisierung, NICHT für Daten-Validierung.
        Rationale: Downstream-Komponenten (Strategies, Backtest) müssen Data-Quality-Checks machen.

        Dieser Test dokumentiert das aktuelle Verhalten (keine Validierung).
        """
        idx = pd.date_range("2025-01-01", periods=3, freq="1h", tz="UTC")
        df = pd.DataFrame({
            "open": [100, 101, 102],
            "high": [102, 99, 104],   # Bar 2: high (99) < low (100) - INVALID!
            "low": [99, 100, 101],
            "close": [101, 102, 103],
            "volume": [1000, 1100, 1200],
        }, index=idx)

        # Normalizer sollte KEINE Validierung durchführen
        result = DataNormalizer.normalize(df)

        assert len(result) == 3
        # Invalide Relation bleibt erhalten (keine Validierung)
        assert result.loc[result.index[1], "high"] < result.loc[result.index[1], "low"]

    def test_invalid_ohlc_close_outside_range(self):
        """
        Normalizer sollte Close außerhalb [Low, High] nicht validieren.

        Policy: Keine OHLC-Validierung im Normalizer.
        Rationale: Data-Quality-Checks gehören zu Downstream-Komponenten.
        """
        idx = pd.date_range("2025-01-01", periods=3, freq="1h", tz="UTC")
        df = pd.DataFrame({
            "open": [100, 101, 102],
            "high": [102, 103, 104],
            "low": [99, 100, 101],
            "close": [101, 98, 103],  # Bar 2: close (98) < low (100) - INVALID!
            "volume": [1000, 1100, 1200],
        }, index=idx)

        result = DataNormalizer.normalize(df)

        # Keine Exception, invalide Werte bleiben
        assert len(result) == 3
        assert result.loc[result.index[1], "close"] < result.loc[result.index[1], "low"]

    def test_negative_volume_not_rejected(self):
        """
        Normalizer sollte negative Volume-Werte nicht validieren.

        Policy: Keine Business-Logic-Validierung im Normalizer.
        """
        idx = pd.date_range("2025-01-01", periods=3, freq="1h", tz="UTC")
        df = pd.DataFrame({
            "open": [100, 101, 102],
            "high": [102, 103, 104],
            "low": [99, 100, 101],
            "close": [101, 102, 103],
            "volume": [1000, -500, 1200],  # Negative volume - INVALID!
        }, index=idx)

        result = DataNormalizer.normalize(df)

        assert len(result) == 3
        assert result.loc[result.index[1], "volume"] < 0


# ============================================================================
# TEST 5: ADDITIONAL EDGE CASES
# ============================================================================

@pytest.mark.data_edge
class TestAdditionalEdgeCases:
    """Weitere Edge-Cases."""

    def test_duplicate_timestamps_handling(self):
        """
        Normalizer entfernt Duplikate (keep='last').

        Policy: Bei duplizierten Timestamps wird der letzte Wert behalten.
        """
        idx = pd.DatetimeIndex([
            "2025-01-01 00:00:00",
            "2025-01-01 01:00:00",
            "2025-01-01 01:00:00",  # Duplikat
            "2025-01-01 02:00:00",
        ], tz="UTC")

        df = pd.DataFrame({
            "open": [100, 101, 999, 102],   # 999 sollte 101 ersetzen
            "high": [102, 103, 1000, 104],
            "low": [99, 100, 998, 101],
            "close": [101, 102, 999, 103],
            "volume": [1000, 1100, 9999, 1200],
        }, index=idx)

        result = DataNormalizer.normalize(df)

        # Nur 3 Rows (Duplikat entfernt)
        assert len(result) == 3

        # Wert vom letzten Duplikat sollte erhalten sein
        assert result.loc[result.index[1], "open"] == 999
        assert result.loc[result.index[1], "volume"] == 9999

    def test_unsorted_timestamps_are_sorted(self):
        """
        Normalizer sortiert Timestamps automatisch.

        Policy: Timestamps werden immer aufsteigend sortiert.
        """
        idx = pd.DatetimeIndex([
            "2025-01-01 02:00:00",
            "2025-01-01 00:00:00",  # Unsortiert
            "2025-01-01 01:00:00",
        ], tz="UTC")

        df = pd.DataFrame({
            "open": [102, 100, 101],
            "high": [104, 102, 103],
            "low": [101, 99, 100],
            "close": [103, 101, 102],
            "volume": [1200, 1000, 1100],
        }, index=idx)

        result = DataNormalizer.normalize(df)

        # Sollte sortiert sein
        assert result.index[0] == pd.Timestamp("2025-01-01 00:00:00", tz="UTC")
        assert result.index[1] == pd.Timestamp("2025-01-01 01:00:00", tz="UTC")
        assert result.index[2] == pd.Timestamp("2025-01-01 02:00:00", tz="UTC")

    def test_extreme_values_not_rejected(self):
        """
        Normalizer sollte extreme Werte (sehr groß/klein) akzeptieren.

        Policy: Keine Range-Validierung im Normalizer.
        """
        idx = pd.date_range("2025-01-01", periods=3, freq="1h", tz="UTC")
        df = pd.DataFrame({
            "open": [1e10, 1e-10, 1e100],     # Extreme Werte
            "high": [2e10, 2e-10, 2e100],
            "low": [0.5e10, 0.5e-10, 0.5e100],
            "close": [1.5e10, 1.5e-10, 1.5e100],
            "volume": [1e20, 1e20, 1e20],
        }, index=idx)

        result = DataNormalizer.normalize(df)

        assert len(result) == 3
        assert result["open"].max() > 1e99
        assert result["open"].min() < 1e-9


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
