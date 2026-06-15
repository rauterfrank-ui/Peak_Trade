"""Exit-Codes und Run-Manifest fuer sweep_parameters (NO-LIVE)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))


def test_sweep_parameters_exit_1_missing_config(tmp_path, monkeypatch) -> None:
    import sweep_parameters as sp

    monkeypatch.chdir(tmp_path)
    code = sp.main(["--config-path", str(tmp_path / "missing.toml")])
    assert code == 1
    man = tmp_path / "reports" / "sweeps" / "sweep_parameters_run_manifest.json"
    assert man.is_file()
    payload = json.loads(man.read_text(encoding="utf-8"))
    assert payload["exit_code"] == 1
    assert payload["script_name"] == "sweep_parameters.py"
    assert "run_id" in payload and len(payload["run_id"]) == 64
    assert payload.get("generated_at_utc") and isinstance(payload["generated_at_utc"], str)
    assert payload["generated_at_utc"].endswith("Z")
    assert payload["config_path"] == str(tmp_path / "missing.toml")


def test_sweep_parameters_exit_1_no_successful_runs(tmp_path, monkeypatch, capsys) -> None:
    """Grid ok, aber jeder Backtest schlaegt fehl -> keine Zeilen -> Exit 1."""
    import sweep_parameters as sp

    cfg = ROOT / "config" / "config.test.toml"
    if not cfg.is_file():
        pytest.skip(f"fehlt: {cfg}")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        sp,
        "build_param_grid",
        lambda _cfg, strategy_key: (["fast_window"], [(20,)]),
    )
    monkeypatch.setattr(
        sp,
        "run_backtest_for_params",
        lambda **_kw: (_ for _ in ()).throw(RuntimeError("simulated")),
    )

    code = sp.main(
        [
            "--config-path",
            str(cfg),
            "--strategy",
            "ma_crossover",
            "--symbol",
            "BTC/EUR",
            "--run-name",
            "contract_fail",
            "--top-k-reports",
            "0",
            "--max-runs",
            "2",
        ]
    )
    assert code == 1
    man = tmp_path / "reports" / "sweeps" / "sweep_ma_crossover_contract_fail_run_manifest.json"
    assert man.is_file()
    payload = json.loads(man.read_text(encoding="utf-8"))
    assert payload["exit_code"] == 1
    assert "error" in payload
    assert "run_id" in payload and len(payload["run_id"]) == 64
    assert payload.get("generated_at_utc") and isinstance(payload["generated_at_utc"], str)
    assert payload["generated_at_utc"].endswith("Z")
    assert payload["config_path"] == str(cfg)
    assert payload["strategy"] == "ma_crossover"
    assert payload["symbols"] == ["BTC/EUR"]
    out = capsys.readouterr().out
    assert "  - run_id:" in out
    assert payload["run_id"] in out


def test_sweep_parameters_script_file_is_valid_utf8() -> None:
    """Keine U+FFFD-/Encoding-Bruchstücke im Sweep-Skript (Regression)."""
    path = ROOT / "scripts" / "sweep_parameters.py"
    text = path.read_bytes().decode("utf-8")
    assert "\ufffd" not in text
    assert "für" in text


def test_sweep_parameters_help_prints_utf8_german(capsys: pytest.CaptureFixture[str]) -> None:
    """Smoke: --help gibt lesbare Umlaute aus (CLI-String-Hygiene)."""
    import sweep_parameters as sp

    with pytest.raises(SystemExit) as exc_info:
        sp.parse_args(["--help"])
    assert exc_info.value.code == 0
    out = capsys.readouterr().out
    assert "für" in out
    assert "Überschreibt" in out


def test_sweep_parameters_quiet_flag_parsed() -> None:
    import sweep_parameters as sp

    args = sp.parse_args(["--quiet"])
    assert args.quiet is True
    args_short = sp.parse_args(["-q"])
    assert args_short.quiet is True


def test_sweep_parameters_default_mode_preserves_progress_output(
    tmp_path, monkeypatch, capsys
) -> None:
    import sweep_parameters as sp

    cfg = ROOT / "config" / "config.test.toml"
    if not cfg.is_file():
        pytest.skip(f"fehlt: {cfg}")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        sp,
        "build_param_grid",
        lambda _cfg, strategy_key: (["fast_window"], [(20,)]),
    )
    monkeypatch.setattr(
        sp,
        "run_backtest_for_params",
        lambda **_kw: (_ for _ in ()).throw(RuntimeError("simulated")),
    )

    code = sp.main(
        [
            "--config-path",
            str(cfg),
            "--strategy",
            "ma_crossover",
            "--symbol",
            "BTC/EUR",
            "--run-name",
            "default_progress",
            "--top-k-reports",
            "0",
            "--max-runs",
            "1",
        ]
    )
    assert code == 1
    out = capsys.readouterr().out
    assert "=== Run 1/" in out
    assert "  - run_id:" in out


def test_sweep_parameters_quiet_mode_suppresses_high_frequency_output(
    tmp_path, monkeypatch, capsys
) -> None:
    import sweep_parameters as sp

    cfg = ROOT / "config" / "config.test.toml"
    if not cfg.is_file():
        pytest.skip(f"fehlt: {cfg}")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        sp,
        "build_param_grid",
        lambda _cfg, strategy_key: (["fast_window"], [(20,)]),
    )
    monkeypatch.setattr(
        sp,
        "run_backtest_for_params",
        lambda **_kw: (_ for _ in ()).throw(RuntimeError("simulated")),
    )

    code = sp.main(
        [
            "--config-path",
            str(cfg),
            "--strategy",
            "ma_crossover",
            "--symbol",
            "BTC/EUR",
            "--run-name",
            "quiet_progress",
            "--top-k-reports",
            "0",
            "--max-runs",
            "1",
            "--quiet",
        ]
    )
    assert code == 1
    captured = capsys.readouterr()
    assert "=== Run 1/" not in captured.out
    assert "  - run_id:" not in captured.out
    assert "Lade Konfiguration" not in captured.out


def test_sweep_parameters_quiet_mode_preserves_stderr_errors(tmp_path, monkeypatch, capsys) -> None:
    import sweep_parameters as sp

    cfg = ROOT / "config" / "config.test.toml"
    if not cfg.is_file():
        pytest.skip(f"fehlt: {cfg}")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        sp,
        "build_param_grid",
        lambda _cfg, strategy_key: (["fast_window"], [(20,)]),
    )
    monkeypatch.setattr(
        sp,
        "run_backtest_for_params",
        lambda **_kw: (_ for _ in ()).throw(RuntimeError("simulated")),
    )

    code = sp.main(
        [
            "--config-path",
            str(cfg),
            "--strategy",
            "ma_crossover",
            "--symbol",
            "BTC/EUR",
            "--run-name",
            "quiet_errors",
            "--top-k-reports",
            "0",
            "--max-runs",
            "1",
            "--quiet",
        ]
    )
    assert code == 1
    captured = capsys.readouterr()
    assert "FEHLER: simulated" in captured.err
    assert "Keine erfolgreichen Backtests" in captured.err


def test_sweep_parameters_quiet_mode_success_writes_csv_without_progress_noise(
    tmp_path, monkeypatch, capsys
) -> None:
    import sweep_parameters as sp
    from unittest.mock import MagicMock

    cfg = ROOT / "config" / "config.test.toml"
    if not cfg.is_file():
        pytest.skip(f"fehlt: {cfg}")

    mock_result = MagicMock()
    mock_result.stats = {
        "total_return": 0.05,
        "sharpe": 1.2,
        "max_drawdown": -0.1,
        "total_trades": 3,
    }
    mock_result.metadata = {"params": {"fast_window": 20}}

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        sp,
        "build_param_grid",
        lambda _cfg, strategy_key: (["fast_window"], [(20,)]),
    )
    monkeypatch.setattr(
        sp,
        "run_backtest_for_params",
        lambda **_kw: mock_result,
    )
    monkeypatch.setattr(sp, "log_experiment_from_result", lambda **_kw: None)

    code = sp.main(
        [
            "--config-path",
            str(cfg),
            "--strategy",
            "ma_crossover",
            "--symbol",
            "BTC/EUR",
            "--run-name",
            "quiet_success",
            "--top-k-reports",
            "0",
            "--max-runs",
            "1",
            "--quiet",
        ]
    )
    assert code == 0
    captured = capsys.readouterr()
    assert "=== Run 1/" not in captured.out
    assert "Parameter Sweep abgeschlossen!" in captured.out
    assert "Sweep-Ergebnis gespeichert:" in captured.out
    csv_path = tmp_path / "reports" / "sweeps" / "sweep_ma_crossover_quiet_success.csv"
    assert csv_path.is_file()


def test_sweep_run_logging_restore_isolates_logger_level() -> None:
    import logging

    from src.sweeps.engine import (
        apply_sweep_run_logging,
        logger as sweep_logger,
        restore_sweep_run_logging,
    )

    baseline = sweep_logger.level
    previous = apply_sweep_run_logging(quiet=True)
    assert sweep_logger.level == logging.WARNING
    restore_sweep_run_logging(previous)
    assert sweep_logger.level == baseline

    previous_again = apply_sweep_run_logging(quiet=False)
    restore_sweep_run_logging(previous_again)
    assert sweep_logger.level == baseline


def test_sweep_run_output_mode_info_suppressed_when_quiet(capsys) -> None:
    from src.sweeps.engine import SweepRunOutputMode

    quiet = SweepRunOutputMode(quiet=True)
    quiet.info("should-not-appear")
    assert capsys.readouterr().out == ""

    normal = SweepRunOutputMode(quiet=False)
    normal.info("should-appear")
    assert "should-appear" in capsys.readouterr().out


def test_load_sweep_ohlcv_data_quiet_suppresses_info_but_keeps_warning(
    caplog,
) -> None:
    import logging
    from unittest.mock import MagicMock

    import pandas as pd

    from src.core.errors import CacheCorruptionError
    from src.sweeps.engine import load_sweep_ohlcv_data

    sample = pd.DataFrame({"close": [1.0, 2.0]})
    cache = MagicMock()
    cache.exists.return_value = True
    cache.load.side_effect = CacheCorruptionError("bad cache")
    cache.clear.return_value = None
    cache.save.return_value = None

    with caplog.at_level(logging.DEBUG):
        df, outcome = load_sweep_ohlcv_data(
            symbol="BTC/EUR",
            timeframe="1h",
            n_bars=2,
            loader=lambda: sample,
            cache=cache,
            use_cache=True,
            quiet=True,
        )

    assert outcome == "fallback"
    assert df.equals(sample)
    info_messages = [r.message for r in caplog.records if r.levelno == logging.INFO]
    warning_messages = [r.message for r in caplog.records if r.levelno == logging.WARNING]
    assert not any("Sweep data cache hit" in msg for msg in info_messages)
    assert not any("Sweep data cache miss" in msg for msg in info_messages)
    assert any("Sweep data cache corrupt" in msg for msg in warning_messages)
