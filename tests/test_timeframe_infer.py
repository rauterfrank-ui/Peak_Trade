import pandas as pd
import pytest

from scripts.run_shadow_execution import infer_timeframe_from_index


@pytest.mark.parametrize(
    "freq, expected",
    [
        ("1min", "1m"),
        ("5min", "5m"),
        ("15min", "15m"),
        ("30min", "30m"),
        ("1h", "1h"),
        ("4h", "4h"),
        ("1d", "1d"),
        ("1W", "1w"),
    ],
)
def test_infer_timeframe_from_index_known_buckets(freq: str, expected: str) -> None:
    idx = pd.date_range("2020-01-01", periods=50, freq=freq)
    assert infer_timeframe_from_index(idx) == expected


def test_infer_timeframe_from_index_irregular_raises() -> None:
    idx = pd.to_datetime(
        [
            "2020-01-01 00:00:00",
            "2020-01-01 00:01:00",
            "2020-01-01 00:10:00",
            "2020-01-01 00:11:00",
        ]
    )
    with pytest.raises(ValueError, match="irregular index"):
        infer_timeframe_from_index(pd.DatetimeIndex(idx))


def test_infer_timeframe_from_index_too_short_raises() -> None:
    idx = pd.date_range("2020-01-01", periods=2, freq="1h")
    with pytest.raises(ValueError, match="at least 3"):
        infer_timeframe_from_index(idx)
