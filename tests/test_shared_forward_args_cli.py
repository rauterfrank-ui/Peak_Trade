"""Smoke: gemeinsame Forward-/Portfolio-OHLCV-CLI (J1 Config-Klarheit)."""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(SCRIPTS))

from _shared_forward_args import (  # noqa: E402
    DEFAULT_FORWARD_N_BARS,
    DEFAULT_OHLCV_TIMEFRAME,
    OHLCV_TIMEFRAME_CHOICES,
    parse_symbols_cli_arg,
)


def test_parse_symbols_cli_arg():
    assert parse_symbols_cli_arg(None) is None
    assert parse_symbols_cli_arg("") is None
    assert parse_symbols_cli_arg("  ") is None
    assert parse_symbols_cli_arg("BTC/EUR, ETH/EUR") == ["BTC/EUR", "ETH/EUR"]


@pytest.mark.smoke
def test_generate_forward_signals_parse_has_shared_defaults():
    import generate_forward_signals as gen

    ns = gen.parse_args(
        ["--strategy", "ma_crossover", "--symbols", "BTC/EUR", "--config-path", "config.toml"]
    )
    assert ns.n_bars == DEFAULT_FORWARD_N_BARS
    assert ns.timeframe == DEFAULT_OHLCV_TIMEFRAME
    assert ns.timeframe in OHLCV_TIMEFRAME_CHOICES


@pytest.mark.smoke
def test_evaluate_forward_signals_parse_has_shared_defaults():
    import evaluate_forward_signals as ev

    ns = ev.parse_args(["dummy.csv"])
    assert ns.n_bars == DEFAULT_FORWARD_N_BARS
    assert ns.timeframe == DEFAULT_OHLCV_TIMEFRAME


@pytest.mark.smoke
def test_run_portfolio_parse_args_timeframe_and_symbols():
    from run_portfolio_backtest_v2 import parse_args

    ns = parse_args(
        ["--timeframe", "4h", "--symbols", "BTC/EUR,ETH/EUR", "--ohlcv-source", "dummy"]
    )
    assert ns.timeframe == "4h"
    assert ns.symbols == "BTC/EUR,ETH/EUR"
    assert ns.bars == DEFAULT_FORWARD_N_BARS
