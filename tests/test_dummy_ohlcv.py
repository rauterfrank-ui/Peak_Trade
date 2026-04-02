"""Tests für scripts/_shared_ohlcv_loader (J1)."""

import sys
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

from src.data import REQUIRED_OHLCV_COLUMNS

_scripts = Path(__file__).resolve().parent.parent / "scripts"
if str(_scripts) not in sys.path:
    sys.path.insert(0, str(_scripts))

from _shared_ohlcv_loader import (  # noqa: E402
    OHLCV_SOURCE_DUMMY,
    OHLCV_SOURCE_KRAKEN,
    load_dummy_ohlcv,
    load_kraken_ohlcv,
    load_ohlcv,
    load_ohlcv_with_meta,
)


@pytest.mark.smoke
def test_load_dummy_ohlcv_shape_and_columns():
    df = load_dummy_ohlcv("BTC/EUR", n_bars=50)
    assert len(df) == 50
    assert list(df.columns) == REQUIRED_OHLCV_COLUMNS
    assert isinstance(df.index, pd.DatetimeIndex)
    assert df.index.tz is not None
    assert str(df.index.tz) == "UTC"


def test_load_dummy_ohlcv_high_low_consistent_with_ohlc():
    df = load_dummy_ohlcv("ETH/EUR", n_bars=100)
    o, h, l, c = df["open"], df["high"], df["low"], df["close"]
    assert (h >= o).all() and (h >= c).all()
    assert (l <= o).all() and (l <= c).all()


def test_load_ohlcv_dispatches_dummy():
    df = load_ohlcv("BTC/EUR", n_bars=30, source=OHLCV_SOURCE_DUMMY)
    assert len(df) == 30


def test_load_ohlcv_with_meta_dummy():
    df, meta = load_ohlcv_with_meta("BTC/EUR", n_bars=42, source=OHLCV_SOURCE_DUMMY, timeframe="1h")
    assert len(df) == 42
    assert meta["symbol"] == "BTC/EUR"
    assert meta["ohlcv_source"] == OHLCV_SOURCE_DUMMY
    assert meta["timeframe"] == "1h"
    assert meta["n_bars_requested"] == 42
    assert meta["bars_loaded"] == 42
    assert meta["kraken_pagination_used"] is None


def test_load_ohlcv_with_meta_kraken_single_request():
    idx = pd.date_range("2024-06-01", periods=10, freq="1h", tz="UTC")
    raw = pd.DataFrame(
        {
            "open": [1.0] * 10,
            "high": [2.0] * 10,
            "low": [0.5] * 10,
            "close": [1.5] * 10,
            "volume": [100.0] * 10,
        },
        index=idx,
    )
    with patch("src.data.kraken.fetch_ohlcv_df", return_value=raw.copy()):
        df, meta = load_ohlcv_with_meta(
            "ETH/EUR", n_bars=10, source=OHLCV_SOURCE_KRAKEN, timeframe="1h"
        )
    assert len(df) == 10
    assert meta["kraken_pagination_used"] is False


def test_load_ohlcv_with_meta_kraken_pagination_flag():
    recent = pd.date_range("2024-03-01", periods=720, freq="1h", tz="UTC")
    older = pd.date_range("2023-12-01", periods=720, freq="1h", tz="UTC")

    def fake_fetch(*args, **kwargs):
        since_ms = kwargs.get("since_ms")
        use_cache = kwargs.get("use_cache", True)
        assert use_cache is False
        if since_ms is None:
            return pd.DataFrame(
                {
                    "open": [100.0] * 720,
                    "high": [101.0] * 720,
                    "low": [99.0] * 720,
                    "close": [100.5] * 720,
                    "volume": [1.0] * 720,
                },
                index=recent,
            )
        return pd.DataFrame(
            {
                "open": [50.0] * 720,
                "high": [51.0] * 720,
                "low": [49.0] * 720,
                "close": [50.5] * 720,
                "volume": [1.0] * 720,
            },
            index=older,
        )

    with patch("src.data.kraken.fetch_ohlcv_df", side_effect=fake_fetch):
        df, meta = load_ohlcv_with_meta(
            "BTC/EUR", n_bars=1000, source=OHLCV_SOURCE_KRAKEN, timeframe="1h"
        )
    assert len(df) == 1000
    assert meta["kraken_pagination_used"] is True


def test_load_ohlcv_unknown_source():
    with pytest.raises(ValueError, match="Unbekannte OHLCV-Quelle"):
        load_ohlcv("BTC/EUR", source="nope")  # type: ignore[arg-type]


def test_load_dummy_ohlcv_n_bars_must_be_positive():
    with pytest.raises(ValueError, match="n_bars muss >= 1"):
        load_dummy_ohlcv("BTC/EUR", n_bars=0)
    with pytest.raises(ValueError, match="n_bars muss >= 1"):
        load_dummy_ohlcv("BTC/EUR", n_bars=-1)


def test_load_ohlcv_source_case_and_whitespace_insensitive():
    df1 = load_ohlcv("BTC/EUR", n_bars=5, source="DUMMY")
    df2 = load_ohlcv("BTC/EUR", n_bars=5, source="  dummy  ")
    assert len(df1) == len(df2) == 5


def test_load_ohlcv_source_must_be_str():
    with pytest.raises(TypeError, match="str"):
        load_ohlcv("BTC/EUR", source=123)  # type: ignore[arg-type]


def test_load_kraken_ohlcv_trims_tail_and_validates():
    idx = pd.date_range("2024-01-01", periods=80, freq="1h", tz="UTC")
    raw = pd.DataFrame(
        {
            "open": [100.0 + i * 0.01 for i in range(80)],
            "high": [102.0 + i * 0.01 for i in range(80)],
            "low": [99.0 + i * 0.01 for i in range(80)],
            "close": [100.5 + i * 0.01 for i in range(80)],
            "volume": [1.0] * 80,
        },
        index=idx,
    )

    with patch("src.data.kraken.fetch_ohlcv_df", return_value=raw.copy()):
        out = load_kraken_ohlcv("BTC/EUR", n_bars=50)

    assert len(out) == 50
    assert out.index[0] == idx[-50]


def test_load_ohlcv_kraken_path():
    idx = pd.date_range("2024-06-01", periods=10, freq="1h", tz="UTC")
    raw = pd.DataFrame(
        {
            "open": [1.0] * 10,
            "high": [2.0] * 10,
            "low": [0.5] * 10,
            "close": [1.5] * 10,
            "volume": [100.0] * 10,
        },
        index=idx,
    )
    with patch("src.data.kraken.fetch_ohlcv_df", return_value=raw.copy()):
        out = load_ohlcv("ETH/EUR", n_bars=10, source=OHLCV_SOURCE_KRAKEN)
    assert len(out) == 10
    assert list(out.columns) == REQUIRED_OHLCV_COLUMNS


def test_load_kraken_ohlcv_pagination_calls_fetch_twice():
    """n_bars > 720: mehrere fetch_ohlcv_df-Aufrufe, tail auf n_bars."""
    recent = pd.date_range("2024-03-01", periods=720, freq="1h", tz="UTC")
    older = pd.date_range("2023-12-01", periods=720, freq="1h", tz="UTC")

    def fake_fetch(*args, **kwargs):
        since_ms = kwargs.get("since_ms")
        use_cache = kwargs.get("use_cache", True)
        assert use_cache is False
        if since_ms is None:
            return pd.DataFrame(
                {
                    "open": [100.0] * 720,
                    "high": [101.0] * 720,
                    "low": [99.0] * 720,
                    "close": [100.5] * 720,
                    "volume": [1.0] * 720,
                },
                index=recent,
            )
        return pd.DataFrame(
            {
                "open": [50.0] * 720,
                "high": [51.0] * 720,
                "low": [49.0] * 720,
                "close": [50.5] * 720,
                "volume": [1.0] * 720,
            },
            index=older,
        )

    with patch("src.data.kraken.fetch_ohlcv_df", side_effect=fake_fetch):
        out = load_kraken_ohlcv("BTC/EUR", n_bars=1000, timeframe="1h")

    assert len(out) == 1000
    assert list(out.columns) == REQUIRED_OHLCV_COLUMNS


def test_timeframe_to_timedelta_invalid():
    from _shared_ohlcv_loader import _timeframe_to_timedelta

    with pytest.raises(ValueError, match="nicht unterstützt"):
        _timeframe_to_timedelta("2w")
