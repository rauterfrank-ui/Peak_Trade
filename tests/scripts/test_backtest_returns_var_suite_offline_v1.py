"""CLI tests for Package H offline backtest→VaR suite wiring v1."""

from __future__ import annotations

import json
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

from scripts.run_var_suite_from_backtest_run_v1 import (
    EXIT_OK,
    EXIT_USAGE_ERROR,
    EXIT_WIRING_ERROR,
    main,
)
from src.risk.validation.var_suite_backtest_wiring_v1 import SUITE_REPORT_JSON, SUITE_REPORT_MD


def _write_equity_csv(run_dir: Path, *, periods: int = 30) -> None:
    rng = np.random.default_rng(7)
    equity = 100.0 + np.cumsum(rng.normal(0.0, 0.4, size=periods))
    df = pd.DataFrame(
        {
            "date": pd.date_range("2024-02-01", periods=periods, freq="D", tz="UTC"),
            "equity": equity,
        }
    )
    df.to_csv(run_dir / "cli_equity.csv", index=False)


def test_cli_successful_run_dir_path(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    _write_equity_csv(run_dir)
    out = tmp_path / "suite_out"
    rc = main(["--run-dir", str(run_dir), "--output-dir", str(out)])
    assert rc == EXIT_OK
    assert (out / SUITE_REPORT_JSON).is_file()
    assert (out / SUITE_REPORT_MD).is_file()
    data = json.loads((out / SUITE_REPORT_JSON).read_text(encoding="utf-8"))
    assert data["overall_result"] in {"PASS", "FAIL"}


def test_cli_requires_output_dir(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    _write_equity_csv(run_dir)
    with pytest.raises(SystemExit) as exc_info:
        main(["--run-dir", str(run_dir)])
    assert exc_info.value.code == EXIT_USAGE_ERROR
    assert "required" in capsys.readouterr().err.lower()


def test_cli_missing_run_dir_fail_closed(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    out = tmp_path / "out"
    rc = main(["--run-dir", str(tmp_path / "missing"), "--output-dir", str(out)])
    assert rc == EXIT_WIRING_ERROR
    assert not out.exists()
    assert "ERROR:" in capsys.readouterr().err


def test_cli_existing_output_dir_fail_closed(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    _write_equity_csv(run_dir)
    out = tmp_path / "out"
    out.mkdir()
    rc = main(["--run-dir", str(run_dir), "--output-dir", str(out)])
    assert rc == EXIT_WIRING_ERROR
    assert not (out / SUITE_REPORT_JSON).exists()


def test_cli_manifest_requires_strategy_id(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    manifest = tmp_path / "returns.toml"
    manifest.write_text("[strategy_returns]\ndemo = 'run'\n", encoding="utf-8")
    out = tmp_path / "out"
    rc = main(
        [
            "--strategy-returns-manifest",
            str(manifest),
            "--output-dir",
            str(out),
        ]
    )
    assert rc == EXIT_USAGE_ERROR
    assert "strategy-id" in capsys.readouterr().err.lower()


def test_cli_manifest_success(tmp_path: Path) -> None:
    run_dir = tmp_path / "runs" / "r1"
    run_dir.mkdir(parents=True)
    _write_equity_csv(run_dir)
    manifest = tmp_path / "returns.toml"
    manifest.write_text('[strategy_returns]\ndemo = "runs/r1"\n', encoding="utf-8")
    out = tmp_path / "out"
    rc = main(
        [
            "--strategy-returns-manifest",
            str(manifest),
            "--strategy-id",
            "demo",
            "--manifest-base-dir",
            str(tmp_path),
            "--output-dir",
            str(out),
        ]
    )
    assert rc == EXIT_OK
    assert (out / SUITE_REPORT_JSON).is_file()


def test_cli_deterministic_output(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    _write_equity_csv(run_dir)
    out1 = tmp_path / "out1"
    out2 = tmp_path / "out2"
    assert main(["--run-dir", str(run_dir), "--output-dir", str(out1)]) == EXIT_OK
    assert main(["--run-dir", str(run_dir), "--output-dir", str(out2)]) == EXIT_OK
    assert (out1 / SUITE_REPORT_JSON).read_bytes() == (out2 / SUITE_REPORT_JSON).read_bytes()


def test_cli_no_backtest_or_network_side_effects(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    _write_equity_csv(run_dir)
    out = tmp_path / "out"
    with patch("subprocess.run") as subprocess_run:
        rc = main(["--run-dir", str(run_dir), "--output-dir", str(out)])
    assert rc == EXIT_OK
    subprocess_run.assert_not_called()


def test_cli_stderr_has_no_secrets(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    _write_equity_csv(run_dir)
    out = tmp_path / "out"
    main(["--run-dir", str(run_dir), "--output-dir", str(out)])
    err = capsys.readouterr().err
    for token in ("api_key", "secret", "password", "token="):
        assert token not in err.lower()
