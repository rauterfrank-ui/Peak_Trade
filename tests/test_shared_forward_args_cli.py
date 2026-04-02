"""Smoke: gemeinsame Forward-/Portfolio-OHLCV-CLI (J1 Config-Klarheit)."""

import subprocess
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
def test_evaluate_forward_signals_ohlcv_source_case_insensitive():
    import evaluate_forward_signals as ev

    ns = ev.parse_args(["dummy.csv", "--ohlcv-source", "KRaken"])
    assert ns.ohlcv_source == "kraken"


@pytest.mark.smoke
def test_run_portfolio_parse_args_timeframe_and_symbols():
    from run_portfolio_backtest_v2 import parse_args

    ns = parse_args(
        ["--timeframe", "4h", "--symbols", "BTC/EUR,ETH/EUR", "--ohlcv-source", "dummy"]
    )
    assert ns.timeframe == "4h"
    assert ns.symbols == "BTC/EUR,ETH/EUR"
    assert ns.bars == DEFAULT_FORWARD_N_BARS


@pytest.mark.smoke
def test_generate_forward_signals_ohlcv_source_case_insensitive():
    import generate_forward_signals as gen

    ns = gen.parse_args(
        ["--strategy", "ma_crossover", "--symbols", "BTC/EUR", "--ohlcv-source", "DUMMY"]
    )
    assert ns.ohlcv_source == "dummy"
    ns2 = gen.parse_args(
        ["--strategy", "ma_crossover", "--symbols", "BTC/EUR", "--ohlcv-source", "Kraken"]
    )
    assert ns2.ohlcv_source == "kraken"


@pytest.mark.smoke
def test_forward_pipeline_scripts_help_contains_j1_no_live_scope():
    """--help listet gemeinsamen J1/NO-LIVE-Scope (Epilog + --ohlcv-source)."""
    for name in (
        "generate_forward_signals.py",
        "evaluate_forward_signals.py",
        "run_portfolio_backtest_v2.py",
    ):
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / name), "--help"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, (name, result.stderr)
        out = result.stdout
        assert "NO-LIVE" in out
        assert "keine Order" in out or "Keine Orders" in out
        assert "--ohlcv-source" in out
