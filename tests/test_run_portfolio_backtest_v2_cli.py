"""CLI-Smoke für run_portfolio_backtest_v2 (--bars / --n-bars)."""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))


@pytest.mark.smoke
def test_parse_args_n_bars_alias():
    from run_portfolio_backtest_v2 import parse_args

    assert parse_args(["--n-bars", "150"]).bars == 150
    assert parse_args(["--bars", "99"]).bars == 99
    assert parse_args([]).bars == 200


@pytest.mark.smoke
def test_parse_args_ohlcv_source():
    from run_portfolio_backtest_v2 import parse_args

    assert parse_args([]).ohlcv_source == "dummy"
    assert parse_args(["--ohlcv-source", "kraken"]).ohlcv_source == "kraken"
    assert parse_args(["--ohlcv-source", "KRAKEN"]).ohlcv_source == "kraken"
    assert parse_args(["--ohlcv-source", "  Dummy "]).ohlcv_source == "dummy"


@pytest.mark.smoke
def test_parse_args_defaults_timeframe():
    from run_portfolio_backtest_v2 import parse_args

    assert parse_args([]).timeframe == "1h"
