"""Tests für scripts/_shared_ohlcv_loader (J1)."""

import sys
from pathlib import Path

import pandas as pd
import pytest

from src.data import REQUIRED_OHLCV_COLUMNS

_scripts = Path(__file__).resolve().parent.parent / "scripts"
if str(_scripts) not in sys.path:
    sys.path.insert(0, str(_scripts))

from _shared_ohlcv_loader import load_dummy_ohlcv


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
