"""Tests für Dummy-OHLCV (J1 Slice 1)."""

import pandas as pd
import pytest

from src.data import REQUIRED_OHLCV_COLUMNS
from src.data.dummy_ohlcv import load_dummy_ohlcv_bars


@pytest.mark.smoke
def test_load_dummy_ohlcv_bars_shape_and_columns():
    df = load_dummy_ohlcv_bars("BTC/EUR", n_bars=50)
    assert len(df) == 50
    assert list(df.columns) == REQUIRED_OHLCV_COLUMNS
    assert isinstance(df.index, pd.DatetimeIndex)


def test_load_dummy_ohlcv_bars_high_low_consistent_with_ohlc():
    df = load_dummy_ohlcv_bars("ETH/EUR", n_bars=100)
    o, h, l, c = df["open"], df["high"], df["low"], df["close"]
    assert (h >= o).all() and (h >= c).all()
    assert (l <= o).all() and (l <= c).all()
