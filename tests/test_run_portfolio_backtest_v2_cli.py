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


def test_run_portfolio_backtest_v2_accepts_local_csv_source_smoke(tmp_path):
    import subprocess
    import sys
    from pathlib import Path

    import pandas as pd

    repo_root = Path(__file__).resolve().parents[1]
    config_src = repo_root / "config" / "config.test.toml"
    assert config_src.exists(), "config/config.test.toml is required for portfolio CLI smoke"

    (tmp_path / "config.toml").write_text(
        config_src.read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    csv_path = tmp_path / "BTC_EUR.csv"
    frame = pd.DataFrame(
        {
            "timestamp": pd.date_range("2024-01-01T00:00:00Z", periods=80, freq="min"),
            "open": [100.0 + i for i in range(80)],
            "high": [101.0 + i for i in range(80)],
            "low": [99.0 + i for i in range(80)],
            "close": [100.5 + i for i in range(80)],
            "volume": [1.0 + (i / 100.0) for i in range(80)],
        }
    )
    frame.to_csv(csv_path, index=False)

    result = subprocess.run(
        [
            sys.executable,
            str(repo_root / "scripts" / "run_portfolio_backtest_v2.py"),
            "--symbols",
            "BTC/EUR",
            "--ohlcv-source",
            "csv",
            "--ohlcv-csv",
            str(csv_path),
            "--n-bars",
            "80",
            "--no-report",
        ],
        cwd=tmp_path,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    combined_output = result.stdout + result.stderr
    assert "csv" in combined_output.lower()
    assert "BTC/EUR" in combined_output
    assert "OHLCV-Quelle" in combined_output
    assert "--no-report" in combined_output or "nicht geschrieben" in combined_output.lower()
    assert not (tmp_path / "reports").exists()
