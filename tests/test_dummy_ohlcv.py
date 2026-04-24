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
    OHLCV_SOURCE_CSV,
    OHLCV_SOURCE_DUMMY,
    OHLCV_SOURCE_KRAKEN,
    load_csv_ohlcv,
    load_dummy_ohlcv,
    load_kraken_ohlcv,
    load_ohlcv,
    load_ohlcv_with_meta,
    normalize_ohlcv_source,
    resolve_ohlcv_csv_path,
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
    assert meta["kraken_bars_shortfall"] is None
    assert meta["ohlcv_csv_resolved"] is None
    assert meta["csv_bars_shortfall"] is None


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
    assert meta["kraken_bars_shortfall"] is False
    assert meta["ohlcv_csv_resolved"] is None
    assert meta["csv_bars_shortfall"] is None


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
    assert meta["kraken_bars_shortfall"] is False
    assert meta["ohlcv_csv_resolved"] is None
    assert meta["csv_bars_shortfall"] is None


def test_load_ohlcv_with_meta_kraken_shortfall_warning_and_meta():
    """Weniger Bars als angefordert: UserWarning + Meta-Flag (kein Stillschweigen)."""
    idx = pd.date_range("2024-06-01", periods=12, freq="1h", tz="UTC")
    raw = pd.DataFrame(
        {
            "open": [1.0] * 12,
            "high": [2.0] * 12,
            "low": [0.5] * 12,
            "close": [1.5] * 12,
            "volume": [100.0] * 12,
        },
        index=idx,
    )
    with patch("src.data.kraken.fetch_ohlcv_df", return_value=raw.copy()):
        with pytest.warns(UserWarning, match="nur 12"):
            df, meta = load_ohlcv_with_meta(
                "ETH/EUR", n_bars=50, source=OHLCV_SOURCE_KRAKEN, timeframe="1h"
            )
    assert len(df) == 12
    assert meta["n_bars_requested"] == 50
    assert meta["bars_loaded"] == 12
    assert meta["kraken_bars_shortfall"] is True
    assert meta["kraken_pagination_used"] is False
    assert meta["ohlcv_csv_resolved"] is None
    assert meta["csv_bars_shortfall"] is None


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


def test_load_kraken_ohlcv_warns_on_shortfall():
    idx = pd.date_range("2024-01-01", periods=7, freq="1h", tz="UTC")
    raw = pd.DataFrame(
        {
            "open": [100.0] * 7,
            "high": [102.0] * 7,
            "low": [99.0] * 7,
            "close": [100.5] * 7,
            "volume": [1.0] * 7,
        },
        index=idx,
    )
    with patch("src.data.kraken.fetch_ohlcv_df", return_value=raw.copy()):
        with pytest.warns(UserWarning, match="nur 7"):
            out = load_kraken_ohlcv("BTC/EUR", n_bars=40, timeframe="1h")
    assert len(out) == 7


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


def _write_minimal_ohlcv_csv(path: Path, n: int = 30) -> None:
    idx = pd.date_range("2024-06-01", periods=n, freq="1h", tz="UTC")
    df = pd.DataFrame(
        {
            "timestamp": idx.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "open": [100.0 + i * 0.1 for i in range(n)],
            "high": [101.0 + i * 0.1 for i in range(n)],
            "low": [99.0 + i * 0.1 for i in range(n)],
            "close": [100.5 + i * 0.1 for i in range(n)],
            "volume": [10.0] * n,
        }
    )
    df.to_csv(path, index=False)


def test_load_csv_ohlcv_respects_n_bars_tail(tmp_path):
    p = tmp_path / "s.csv"
    _write_minimal_ohlcv_csv(p, n=50)
    df = load_csv_ohlcv(p, "BTC/EUR", n_bars=20)
    assert len(df) == 20
    assert list(df.columns) == REQUIRED_OHLCV_COLUMNS


def test_load_ohlcv_with_meta_csv(tmp_path):
    p = tmp_path / "s.csv"
    _write_minimal_ohlcv_csv(p, n=25)
    df, meta = load_ohlcv_with_meta(
        "BTC/EUR",
        n_bars=10,
        source=OHLCV_SOURCE_CSV,
        timeframe="1h",
        ohlcv_csv_path=p,
    )
    assert len(df) == 10
    assert meta["ohlcv_source"] == OHLCV_SOURCE_CSV
    assert meta["bars_loaded"] == 10
    assert meta["n_bars_requested"] == 10
    assert meta["csv_bars_shortfall"] is False
    assert meta["ohlcv_csv_resolved"] == str(p.resolve())


def test_load_ohlcv_csv_shortfall_warns(tmp_path):
    p = tmp_path / "s.csv"
    _write_minimal_ohlcv_csv(p, n=5)
    with pytest.warns(UserWarning, match="nur 5"):
        df, meta = load_ohlcv_with_meta(
            "ETH/EUR",
            n_bars=100,
            source=OHLCV_SOURCE_CSV,
            ohlcv_csv_path=p,
        )
    assert len(df) == 5
    assert meta["csv_bars_shortfall"] is True


def test_load_csv_duplicate_timestamp_fails(tmp_path):
    p = tmp_path / "bad.csv"
    idx = pd.date_range("2024-06-01", periods=5, freq="1h", tz="UTC")
    ts = list(idx.strftime("%Y-%m-%dT%H:%M:%S%z"))
    ts[2] = ts[1]
    pd.DataFrame(
        {
            "timestamp": ts,
            "open": [1.0] * 5,
            "high": [2.0] * 5,
            "low": [0.5] * 5,
            "close": [1.5] * 5,
            "volume": [1.0] * 5,
        }
    ).to_csv(p, index=False)
    with pytest.raises(ValueError, match="doppelte"):
        load_csv_ohlcv(p, "BTC/EUR", n_bars=10)


def test_load_csv_high_lt_low_fails(tmp_path):
    p = tmp_path / "bad2.csv"
    idx = pd.date_range("2024-06-01", periods=3, freq="1h", tz="UTC")
    pd.DataFrame(
        {
            "timestamp": idx.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "open": [10.0, 10.0, 10.0],
            "high": [9.0, 10.0, 10.0],
            "low": [10.0, 9.0, 9.0],
            "close": [10.0, 10.0, 10.0],
            "volume": [1.0, 1.0, 1.0],
        }
    ).to_csv(p, index=False)
    from src.data.contracts import DataContractError

    with pytest.raises(DataContractError, match="high < low"):
        load_csv_ohlcv(p, "BTC/EUR", n_bars=10)


def test_resolve_ohlcv_csv_path_symbol_placeholder(tmp_path):
    sub = tmp_path / "data"
    sub.mkdir()
    target = sub / "BTC_EUR.csv"
    target.write_text("x", encoding="utf-8")
    resolved = resolve_ohlcv_csv_path(str(tmp_path / "data" / "{symbol}.csv"), "BTC/EUR")
    assert resolved == target.resolve()


def test_normalize_fixture_alias_is_csv():
    assert normalize_ohlcv_source("fixture") == OHLCV_SOURCE_CSV
    assert normalize_ohlcv_source("FiXtUrE") == OHLCV_SOURCE_CSV


def test_load_ohlcv_csv_requires_path():
    with pytest.raises(ValueError, match="ohlcv_csv_path"):
        load_ohlcv("BTC/EUR", source=OHLCV_SOURCE_CSV, n_bars=10)
