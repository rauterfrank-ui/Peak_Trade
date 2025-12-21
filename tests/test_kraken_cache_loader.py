"""
Peak_Trade – Tests fuer Kraken-Cache-Loader (Phase 79)
======================================================

Tests fuer den Kraken-Cache-Loader mit Data-Quality-Control.

Test-Kategorien:
1. Happy-Path: Gueltige Daten werden korrekt geladen
2. Missing-File: Fehlende Dateien werden korrekt gemeldet
3. Too-Few-Bars: Zu wenige Bars werden erkannt
4. Empty-File: Leere Dateien werden erkannt
5. Config-Tests: Config-Loader funktioniert

Usage:
    pytest tests/test_kraken_cache_loader.py -v
"""

from __future__ import annotations

from pathlib import Path
from datetime import datetime, timedelta

import pytest
import pandas as pd
import numpy as np


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def kraken_cache_fixture(tmp_path) -> Path:
    """
    Erstellt temporaeres Verzeichnis mit gueltigen Test-Cache-Daten.

    Returns:
        Path zum Cache-Verzeichnis
    """
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir(parents=True)

    # Gueltige OHLCV-Daten erstellen (720 Bars = 30 Tage bei 1h)
    n_bars = 720
    np.random.seed(42)
    idx = pd.date_range(
        start="2025-10-01 00:00:00",
        periods=n_bars,
        freq="1h",
        tz="UTC",
    )
    close_prices = 90000 * np.exp(np.cumsum(np.random.normal(0, 0.01, n_bars)))
    df = pd.DataFrame(index=idx)
    df["open"] = close_prices * (1 + np.random.uniform(-0.001, 0.001, n_bars))
    df["close"] = close_prices
    df["high"] = np.maximum(df["open"], df["close"]) * 1.005
    df["low"] = np.minimum(df["open"], df["close"]) * 0.995
    df["volume"] = np.random.uniform(50, 500, n_bars)

    # Als Parquet speichern
    df.to_parquet(cache_dir / "BTC_EUR_1h.parquet")

    return cache_dir


@pytest.fixture
def small_cache_fixture(tmp_path) -> Path:
    """
    Erstellt Cache mit nur 10 Bars (fuer too_few_bars Tests).

    Returns:
        Path zum Cache-Verzeichnis
    """
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir(parents=True)

    n_bars = 10
    np.random.seed(42)
    idx = pd.date_range(
        start="2025-11-01 00:00:00",
        periods=n_bars,
        freq="1h",
        tz="UTC",
    )
    df = pd.DataFrame(index=idx)
    df["open"] = np.random.uniform(80000, 100000, n_bars)
    df["close"] = df["open"] * (1 + np.random.uniform(-0.01, 0.01, n_bars))
    df["high"] = np.maximum(df["open"], df["close"]) * 1.005
    df["low"] = np.minimum(df["open"], df["close"]) * 0.995
    df["volume"] = np.random.uniform(50, 500, n_bars)

    df.to_parquet(cache_dir / "SMALL_EUR_1h.parquet")

    return cache_dir


@pytest.fixture
def empty_cache_fixture(tmp_path) -> Path:
    """
    Erstellt Cache mit leerer Parquet-Datei.

    Returns:
        Path zum Cache-Verzeichnis
    """
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir(parents=True)

    # Leerer DataFrame mit korrekten Spalten
    df = pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
    df.index = pd.DatetimeIndex([], tz="UTC")
    df.to_parquet(cache_dir / "EMPTY_EUR_1h.parquet")

    return cache_dir


# ============================================================================
# TEST 1: HAPPY PATH
# ============================================================================


class TestKrakenCacheLoaderHappyPath:
    """Tests fuer erfolgreiche Daten-Ladung."""

    def test_load_kraken_cache_window_success(self, kraken_cache_fixture):
        """Gueltige Daten werden korrekt geladen."""
        from src.data.kraken_cache_loader import load_kraken_cache_window

        df, health = load_kraken_cache_window(
            base_path=kraken_cache_fixture,
            market="BTC/EUR",
            timeframe="1h",
            min_bars=500,
            n_bars=600,
        )

        assert health.status == "ok"
        assert health.is_ok
        assert health.num_bars == 600
        assert health.start_ts is not None
        assert health.end_ts is not None
        assert health.file_path is not None
        assert "BTC_EUR_1h.parquet" in health.file_path

        # DataFrame pruefen
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 600
        assert list(df.columns) == ["open", "high", "low", "close", "volume"]
        assert isinstance(df.index, pd.DatetimeIndex)

    def test_load_kraken_cache_window_with_lookback_days(self, kraken_cache_fixture):
        """Lookback-Days werden korrekt in Bars umgerechnet."""
        from src.data.kraken_cache_loader import load_kraken_cache_window

        df, health = load_kraken_cache_window(
            base_path=kraken_cache_fixture,
            market="BTC/EUR",
            timeframe="1h",
            lookback_days=10,  # 10 Tage * 24h = 240 Bars
            min_bars=200,
        )

        assert health.is_ok
        # min_bars ist mindestens 200, lookback_days 10 -> 240
        # required_bars = max(240, 200) = 240
        assert health.num_bars == 240

    def test_health_lookback_days_actual(self, kraken_cache_fixture):
        """lookback_days_actual wird korrekt berechnet."""
        from src.data.kraken_cache_loader import load_kraken_cache_window

        df, health = load_kraken_cache_window(
            base_path=kraken_cache_fixture,
            market="BTC/EUR",
            timeframe="1h",
            n_bars=720,  # 30 Tage
            min_bars=200,
        )

        assert health.is_ok
        # 720 Bars bei 1h = ca. 30 Tage
        assert health.lookback_days_actual is not None
        assert 29 < health.lookback_days_actual < 31

    def test_health_to_dict(self, kraken_cache_fixture):
        """KrakenDataHealth.to_dict() funktioniert."""
        from src.data.kraken_cache_loader import load_kraken_cache_window

        df, health = load_kraken_cache_window(
            base_path=kraken_cache_fixture,
            market="BTC/EUR",
            timeframe="1h",
            min_bars=200,
        )

        d = health.to_dict()
        assert isinstance(d, dict)
        assert d["status"] == "ok"
        assert d["num_bars"] > 0
        assert d["start_ts"] is not None
        assert d["end_ts"] is not None


# ============================================================================
# TEST 2: MISSING FILE
# ============================================================================


class TestKrakenCacheLoaderMissingFile:
    """Tests fuer fehlende Dateien."""

    def test_missing_file_returns_status(self, tmp_path):
        """Fehlende Datei gibt status='missing_file' zurueck."""
        from src.data.kraken_cache_loader import load_kraken_cache_window

        cache_dir = tmp_path / "empty_cache"
        cache_dir.mkdir(parents=True)

        df, health = load_kraken_cache_window(
            base_path=cache_dir,
            market="NONEXISTENT/PAIR",
            timeframe="1h",
            min_bars=100,
        )

        assert health.status == "missing_file"
        assert not health.is_ok
        assert health.num_bars == 0
        assert health.notes is not None
        assert "nicht gefunden" in health.notes.lower() or "not found" in health.notes.lower()

        # DataFrame ist leer
        assert len(df) == 0

    def test_missing_cache_directory(self, tmp_path):
        """Nicht existierendes Cache-Verzeichnis."""
        from src.data.kraken_cache_loader import load_kraken_cache_window

        nonexistent_dir = tmp_path / "does_not_exist"

        df, health = load_kraken_cache_window(
            base_path=nonexistent_dir,
            market="BTC/EUR",
            timeframe="1h",
            min_bars=100,
        )

        assert health.status == "missing_file"
        assert not health.is_ok


# ============================================================================
# TEST 3: TOO FEW BARS
# ============================================================================


class TestKrakenCacheLoaderTooFewBars:
    """Tests fuer zu wenige Bars."""

    def test_too_few_bars_status(self, small_cache_fixture):
        """Zu wenige Bars gibt status='too_few_bars' zurueck."""
        from src.data.kraken_cache_loader import load_kraken_cache_window

        df, health = load_kraken_cache_window(
            base_path=small_cache_fixture,
            market="SMALL/EUR",
            timeframe="1h",
            min_bars=100,  # Benoetige 100, habe nur 10
        )

        assert health.status == "too_few_bars"
        assert not health.is_ok
        assert health.num_bars == 10
        assert health.notes is not None
        assert "10" in health.notes  # "only 10 bars"
        assert "100" in health.notes  # "min_bars=100"

        # DataFrame enthaelt trotzdem die Daten
        assert len(df) == 10

    def test_min_bars_threshold(self, small_cache_fixture):
        """min_bars Threshold wird korrekt geprueft."""
        from src.data.kraken_cache_loader import load_kraken_cache_window

        # small_cache_fixture hat nur 10 Bars, min_bars=50 -> too_few_bars
        df, health = load_kraken_cache_window(
            base_path=small_cache_fixture,
            market="SMALL/EUR",
            timeframe="1h",
            min_bars=50,
        )

        assert health.status == "too_few_bars"
        assert health.num_bars == 10


# ============================================================================
# TEST 4: EMPTY FILE
# ============================================================================


class TestKrakenCacheLoaderEmptyFile:
    """Tests fuer leere Dateien."""

    def test_empty_file_status(self, empty_cache_fixture):
        """Leere Datei gibt status='empty' zurueck."""
        from src.data.kraken_cache_loader import load_kraken_cache_window

        df, health = load_kraken_cache_window(
            base_path=empty_cache_fixture,
            market="EMPTY/EUR",
            timeframe="1h",
            min_bars=100,
        )

        assert health.status == "empty"
        assert not health.is_ok
        assert health.num_bars == 0


# ============================================================================
# TEST 5: CONFIG
# ============================================================================


class TestKrakenCacheConfig:
    """Tests fuer Config-Loading."""

    def test_get_real_market_smokes_config_defaults(self):
        """get_real_market_smokes_config gibt sane Defaults zurueck."""
        from src.data.kraken_cache_loader import get_real_market_smokes_config

        # Mit nicht existierender Config -> Defaults
        cfg = get_real_market_smokes_config("nonexistent.toml")

        assert cfg["base_path"] == "data/cache"
        assert cfg["test_base_path"] == "tests/data/kraken_smoke"
        assert cfg["default_market"] == "BTC/EUR"
        assert cfg["default_timeframe"] == "1h"
        assert cfg["min_bars"] == 500
        assert "BTC/EUR" in cfg["markets"]

    def test_get_real_market_smokes_config_from_file(self):
        """get_real_market_smokes_config laedt aus config.toml."""
        from src.data.kraken_cache_loader import get_real_market_smokes_config

        cfg = get_real_market_smokes_config("config/config.toml")

        # Config sollte existieren (wurde in Phase 79 erweitert)
        assert "base_path" in cfg
        assert "min_bars" in cfg

    def test_list_available_cache_files(self, kraken_cache_fixture):
        """list_available_cache_files listet Dateien korrekt auf."""
        from src.data.kraken_cache_loader import list_available_cache_files

        files = list_available_cache_files(kraken_cache_fixture)

        assert "BTC_EUR_1h.parquet" in files
        assert files["BTC_EUR_1h.parquet"]["size_kb"] > 0
        assert files["BTC_EUR_1h.parquet"]["modified"] is not None

    def test_list_available_cache_files_empty_dir(self, tmp_path):
        """list_available_cache_files mit leerem Verzeichnis."""
        from src.data.kraken_cache_loader import list_available_cache_files

        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        files = list_available_cache_files(empty_dir)
        assert files == {}

    def test_list_available_cache_files_nonexistent(self, tmp_path):
        """list_available_cache_files mit nicht existierendem Verzeichnis."""
        from src.data.kraken_cache_loader import list_available_cache_files

        files = list_available_cache_files(tmp_path / "does_not_exist")
        assert files == {}


# ============================================================================
# TEST 6: CHECK DATA HEALTH ONLY
# ============================================================================


class TestCheckDataHealthOnly:
    """Tests fuer check_data_health_only Funktion."""

    def test_check_data_health_only_ok(self, kraken_cache_fixture):
        """check_data_health_only gibt OK bei gueltigen Daten."""
        from src.data.kraken_cache_loader import check_data_health_only

        health = check_data_health_only(
            base_path=kraken_cache_fixture,
            market="BTC/EUR",
            timeframe="1h",
            min_bars=500,
        )

        assert health.is_ok
        assert health.status == "ok"
        assert health.num_bars >= 500

    def test_check_data_health_only_missing(self, tmp_path):
        """check_data_health_only bei fehlender Datei."""
        from src.data.kraken_cache_loader import check_data_health_only

        health = check_data_health_only(
            base_path=tmp_path,
            market="NONEXISTENT/PAIR",
            timeframe="1h",
            min_bars=100,
        )

        assert not health.is_ok
        assert health.status == "missing_file"


# ============================================================================
# TEST 7: EDGE CASES
# ============================================================================


class TestKrakenCacheLoaderEdgeCases:
    """Edge-Case-Tests."""

    def test_symbol_slash_replacement(self, kraken_cache_fixture):
        """Symbol mit Slash wird korrekt in Dateiname umgewandelt."""
        from src.data.kraken_cache_loader import _build_cache_path

        path = _build_cache_path(
            base_path=kraken_cache_fixture,
            market="BTC/EUR",
            timeframe="1h",
        )

        assert "BTC_EUR_1h.parquet" in str(path)
        assert "/" not in path.name

    def test_different_timeframes(self, tmp_path):
        """Verschiedene Timeframes werden korrekt gehandhabt."""
        from src.data.kraken_cache_loader import _timeframe_to_hours

        assert _timeframe_to_hours("1m") == 1 / 60
        assert _timeframe_to_hours("5m") == 5 / 60
        assert _timeframe_to_hours("15m") == 0.25
        assert _timeframe_to_hours("1h") == 1.0
        assert _timeframe_to_hours("4h") == 4.0
        assert _timeframe_to_hours("1d") == 24.0

    def test_utc_timezone_handling(self, kraken_cache_fixture):
        """UTC-Timezone wird korrekt gesetzt."""
        from src.data.kraken_cache_loader import load_kraken_cache_window

        df, health = load_kraken_cache_window(
            base_path=kraken_cache_fixture,
            market="BTC/EUR",
            timeframe="1h",
            min_bars=100,
        )

        assert health.is_ok
        assert df.index.tz is not None
        assert str(df.index.tz) == "UTC"


# ============================================================================
# TEST 8: INTEGRATION WITH DIAGNOSTICS
# ============================================================================


class TestKrakenCacheIntegration:
    """Integration-Tests mit diagnostics.py."""

    def test_run_strategy_smoke_tests_with_qc(self, kraken_cache_fixture, tmp_path):
        """run_strategy_smoke_tests nutzt Data-QC korrekt."""
        from src.strategies.diagnostics import run_strategy_smoke_tests

        # Temporaere Config erstellen
        config_path = tmp_path / "config.toml"
        config_content = f"""
[real_market_smokes]
base_path = "{kraken_cache_fixture}"
test_base_path = "{kraken_cache_fixture}"
default_market = "BTC/EUR"
default_timeframe = "1h"
min_bars = 200

[data]
data_dir = "{tmp_path / "data"}"
"""
        config_path.write_text(config_content)

        results = run_strategy_smoke_tests(
            strategy_names=["ma_crossover"],
            config_path=str(config_path),
            market="BTC/EUR",
            timeframe="1h",
            n_bars=300,
            data_source="kraken_cache",
            min_bars=200,
        )

        assert len(results) == 1
        result = results[0]

        # Data-Health sollte gesetzt sein
        assert result.data_health is not None
        assert result.data_source == "kraken_cache"
        assert result.symbol == "BTC/EUR"
        assert result.timeframe == "1h"

    def test_run_strategy_smoke_tests_data_qc_fail(self, tmp_path):
        """run_strategy_smoke_tests bei Data-QC-Fehler."""
        from src.strategies.diagnostics import run_strategy_smoke_tests

        # Leeres Cache-Verzeichnis
        cache_dir = tmp_path / "empty_cache"
        cache_dir.mkdir(parents=True)

        config_path = tmp_path / "config.toml"
        config_content = f"""
[real_market_smokes]
base_path = "{cache_dir}"
min_bars = 100

[data]
data_dir = "{tmp_path / "data"}"
"""
        config_path.write_text(config_content)

        results = run_strategy_smoke_tests(
            strategy_names=["ma_crossover", "rsi_reversion"],
            config_path=str(config_path),
            market="NONEXISTENT/PAIR",
            timeframe="1h",
            data_source="kraken_cache",
        )

        # Alle Strategien sollten FAIL sein mit Data-Health-Info
        assert len(results) == 2
        for r in results:
            assert r.status == "fail"
            assert r.data_health is not None
            assert r.data_health in ["missing_file", "other"]


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
