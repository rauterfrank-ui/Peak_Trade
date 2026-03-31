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


def test_load_ohlcv_unknown_source():
    with pytest.raises(ValueError, match="Unbekannte OHLCV-Quelle"):
        load_ohlcv("BTC/EUR", source="nope")  # type: ignore[arg-type]


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
