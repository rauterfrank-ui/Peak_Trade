"""Evaluate historical Forward CSVs using explicit local price inputs."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))


@pytest.mark.smoke
@pytest.mark.integration
def test_evaluate_forward_signals_accepts_local_csv_source_smoke(tmp_path):
    """Evaluate-CLI liest eine vorliegende Signal-CSV und lokale Preise."""
    cfg_path = ROOT / "config" / "config.test.toml"
    if not cfg_path.is_file():
        pytest.skip(f"fehlt: {cfg_path}")

    csv_path = tmp_path / "BTC_EUR.csv"
    n = 80
    idx = pd.date_range("2024-06-01", periods=n, freq="1h", tz="UTC")
    pd.DataFrame(
        {
            "timestamp": idx.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "open": [100.0 + i * 0.1 for i in range(n)],
            "high": [101.0 + i * 0.1 for i in range(n)],
            "low": [99.0 + i * 0.1 for i in range(n)],
            "close": [100.5 + i * 0.1 for i in range(n)],
            "volume": [10.0] * n,
        }
    ).to_csv(csv_path, index=False)

    sig_path = tmp_path / "original_signals.csv"
    pd.DataFrame([{"symbol": "BTC/EUR", "as_of": idx[40].isoformat(), "direction": 1.0}]).to_csv(
        sig_path, index=False
    )

    eval_dir = tmp_path / "eval_out"
    ev = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "evaluate_forward_signals.py"),
            str(sig_path),
            "--horizon-bars",
            "1",
            "--config-path",
            str(cfg_path),
            "--output-dir",
            str(eval_dir),
            "--n-bars",
            str(n),
            "--ohlcv-source",
            "csv",
            "--ohlcv-csv",
            str(csv_path),
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert ev.returncode == 0, ev.stderr
    eval_files = list(eval_dir.glob("*_eval_*.csv"))
    assert len(eval_files) >= 1
    df_eval = pd.read_csv(eval_files[0])
    assert not df_eval.empty
    assert "return" in df_eval.columns
    combined = ev.stdout + ev.stderr
    assert "csv" in combined.lower()
    assert str(csv_path.resolve()) in combined


@pytest.mark.integration
def test_evaluate_forward_signals_csv_source_requires_csv_path_subprocess(tmp_path):
    """Negativ: Evaluate-CLI mit csv-Quelle ohne --ohlcv-csv → Validierung schlägt fehl."""
    cfg_path = ROOT / "config" / "config.test.toml"
    if not cfg_path.is_file():
        pytest.skip(f"fehlt: {cfg_path}")

    signals_path = tmp_path / "signals.csv"
    pd.DataFrame(
        [
            {
                "symbol": "BTC/EUR",
                "as_of": "2024-01-01T00:40:00+00:00",
                "direction": 1.0,
            }
        ]
    ).to_csv(signals_path, index=False)

    out_dir = tmp_path / "eval_negative"
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "evaluate_forward_signals.py"),
            str(signals_path),
            "--config-path",
            str(cfg_path),
            "--output-dir",
            str(out_dir),
            "--ohlcv-source",
            "csv",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 1
    combined = result.stdout + result.stderr
    assert "--ohlcv-csv" in combined
    assert "csv" in combined.lower()
