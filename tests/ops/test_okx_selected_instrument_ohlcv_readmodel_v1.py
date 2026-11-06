"""OHLCV parse/identity contract tests for OKX selected-instrument readmodel."""

from __future__ import annotations

import pytest

from src.ops.okx_selected_instrument_ohlcv_readmodel_v1 import (
    OkxOhlcvReadmodelError,
    parse_okx_history_candles,
)


def test_parse_valid_candles_and_gap() -> None:
    rows = [
        ["1700000000000", "1", "2", "0.5", "1.5", "10", "10", "15", "1"],
        ["1700003600000", "1.5", "2.5", "1.0", "2.0", "11", "11", "16", "1"],
        ["1700010800000", "2.0", "3.0", "1.5", "2.5", "12", "12", "17", "1"],  # +2h gap
    ]
    bars, notes = parse_okx_history_candles(rows)
    assert len(bars) == 3
    assert any(n.startswith("GAP_COUNT:") for n in notes)
    assert bars[0].confirm is True


def test_duplicate_timestamp_rejected() -> None:
    rows = [
        ["1700000000000", "1", "2", "0.5", "1.5", "10", "10", "15", "1"],
        ["1700000000000", "1", "2", "0.5", "1.5", "10", "10", "15", "1"],
    ]
    with pytest.raises(OkxOhlcvReadmodelError):
        parse_okx_history_candles(rows)


def test_invalid_ohlc_rejected() -> None:
    rows = [
        ["1700000000000", "1", "0.5", "0.4", "1.5", "10", "10", "15", "1"],  # high < max(o,c)
    ]
    with pytest.raises(OkxOhlcvReadmodelError):
        parse_okx_history_candles(rows)
