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


def _run_sweep_strategy_common_mocks(monkeypatch, tmp_path, *, summary=None, engine_error=None):
    """Shared offline mocks for run_sweep_strategy contract tests."""
    import pandas as pd
    from unittest.mock import MagicMock

    import run_sweep_strategy as rss

    cfg = ROOT / "config" / "config.test.toml"
    if not cfg.is_file():
        pytest.skip(f"fehlt: {cfg}")

    index = pd.date_range("2024-01-01", periods=10, freq="1h", tz="UTC")
    dummy_data = pd.DataFrame(
        {
            "open": [100.0] * 10,
            "high": [101.0] * 10,
            "low": [99.0] * 10,
            "close": [100.5] * 10,
            "volume": [500.0] * 10,
        },
        index=index,
    )

    if summary is None:
        from src.sweeps.engine import SweepResult, SweepSummary

        best = SweepResult(
            params={"fast_window": 20},
            stats={
                "total_return": 0.05,
                "sharpe": 1.2,
                "max_drawdown": -0.1,
                "total_trades": 3,
            },
            run_id="test_run",
            success=True,
        )
        summary = SweepSummary(
            sweep_id="sweep_test",
            sweep_name="ma_crossover_sweep_test",
            strategy_key="ma_crossover",
            symbol="BTC/EUR",
            timeframe="1h",
            total_combinations=1,
            runs_executed=1,
            successful_runs=1,
            failed_runs=0,
            results=[best],
            best_result=best,
            duration_seconds=0.1,
            started_at="2024-01-01T00:00:00Z",
            completed_at="2024-01-01T00:00:01Z",
        )

    captured_configs: list = []

    class MockEngine:
        def __init__(self, verbose=False, progress_callback=None):
            self.verbose = verbose
            self.progress_callback = progress_callback

        def run_sweep(self, config, data, skip_registry=False, diagnostics_callback=None):
            captured_configs.append(config)
            if engine_error is not None:
                raise engine_error
            if self.progress_callback:
                self.progress_callback(1, 1, {"fast_window": 20})
            return summary

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(rss, "SweepEngine", MockEngine)
    monkeypatch.setattr(rss, "load_ohlcv_data", lambda **_kw: dummy_data)
    return rss, cfg, captured_configs


def test_run_sweep_strategy_quiet_flag_parsed() -> None:
    import run_sweep_strategy as rss

    args = rss.parse_args(["--quiet", "--strategy", "ma_crossover", "--param", "fast_window=20"])
    assert args.quiet is True
    args_short = rss.parse_args(["-q", "--strategy", "ma_crossover", "--param", "fast_window=20"])
    assert args_short.quiet is True


def test_run_sweep_strategy_default_mode_preserves_progress_output(
    tmp_path, monkeypatch, capsys
) -> None:
    rss, cfg, _ = _run_sweep_strategy_common_mocks(monkeypatch, tmp_path)

    code = rss.main(
        [
            "--strategy",
            "ma_crossover",
            "--param",
            "fast_window=20",
            "--config",
            str(cfg),
            "--no-registry",
            "--max-runs",
            "1",
        ]
    )
    assert code == 0
    out = capsys.readouterr().out
    assert "[1/4] Parameter-Grid laden" in out
    assert "Fortschritt:" in out or "[1/1]" in out


def test_run_sweep_strategy_quiet_mode_suppresses_high_frequency_output(
    tmp_path, monkeypatch, capsys
) -> None:
    rss, cfg, _ = _run_sweep_strategy_common_mocks(monkeypatch, tmp_path)

    code = rss.main(
        [
            "--strategy",
            "ma_crossover",
            "--param",
            "fast_window=20",
            "--config",
            str(cfg),
            "--no-registry",
            "--max-runs",
            "1",
            "--quiet",
        ]
    )
    assert code == 0
    captured = capsys.readouterr()
    assert "[1/4] Parameter-Grid laden" not in captured.out
    assert "Fortschritt:" not in captured.out
    assert "[4/4] Sweep ausführen" not in captured.out


def test_run_sweep_strategy_quiet_mode_preserves_completion_output(
    tmp_path, monkeypatch, capsys
) -> None:
    rss, cfg, _ = _run_sweep_strategy_common_mocks(monkeypatch, tmp_path)

    code = rss.main(
        [
            "--strategy",
            "ma_crossover",
            "--param",
            "fast_window=20",
            "--config",
            str(cfg),
            "--no-registry",
            "--max-runs",
            "1",
            "--quiet",
        ]
    )
    assert code == 0
    out = capsys.readouterr().out
    assert "SWEEP ABGESCHLOSSEN" in out
    assert "TOP" in out


def test_run_sweep_strategy_quiet_mode_preserves_export_path_output(
    tmp_path, monkeypatch, capsys
) -> None:
    rss, cfg, _ = _run_sweep_strategy_common_mocks(monkeypatch, tmp_path)
    export_path = tmp_path / "results.csv"

    code = rss.main(
        [
            "--strategy",
            "ma_crossover",
            "--param",
            "fast_window=20",
            "--config",
            str(cfg),
            "--no-registry",
            "--max-runs",
            "1",
            "--quiet",
            "--export",
            str(export_path),
        ]
    )
    assert code == 0
    out = capsys.readouterr().out
    assert "Ergebnisse exportiert nach:" in out
    assert str(export_path) in out


def test_run_sweep_strategy_quiet_mode_preserves_errors(tmp_path, monkeypatch, capsys) -> None:
    rss, cfg, _ = _run_sweep_strategy_common_mocks(
        monkeypatch, tmp_path, engine_error=RuntimeError("simulated sweep failure")
    )

    code = rss.main(
        [
            "--strategy",
            "ma_crossover",
            "--param",
            "fast_window=20",
            "--config",
            str(cfg),
            "--no-registry",
            "--max-runs",
            "1",
            "--quiet",
        ]
    )
    assert code == 1
    out = capsys.readouterr().out
    assert "FEHLER beim Sweep: simulated sweep failure" in out


def test_run_sweep_strategy_quiet_mode_restores_logging_after_success() -> None:
    import logging
    from unittest.mock import patch

    import run_sweep_strategy as rss
    from src.sweeps.engine import logger as sweep_logger

    baseline = sweep_logger.level
    with patch.object(rss, "_run_main", return_value=0):
        assert rss.main(["--quiet", "--list-strategies"]) == 0
    assert sweep_logger.level == baseline


def test_run_sweep_strategy_quiet_mode_restores_logging_after_exception() -> None:
    import logging
    from unittest.mock import patch

    import run_sweep_strategy as rss
    from src.sweeps.engine import logger as sweep_logger

    baseline = sweep_logger.level
    with patch.object(rss, "_run_main", side_effect=RuntimeError("boom")):
        with pytest.raises(RuntimeError, match="boom"):
            rss.main(["--quiet", "--list-strategies"])
    assert sweep_logger.level == baseline


def test_run_sweep_strategy_multiple_quiet_calls_do_not_duplicate_handlers() -> None:
    import logging
    from unittest.mock import patch

    import run_sweep_strategy as rss
    from src.sweeps.engine import logger as sweep_logger

    baseline_handlers = len(sweep_logger.handlers)
    with patch.object(rss, "_run_main", return_value=0):
        rss.main(["--quiet", "--list-strategies"])
        rss.main(["--quiet", "--list-strategies"])
    assert len(sweep_logger.handlers) == baseline_handlers


def test_run_sweep_strategy_quiet_does_not_change_sweep_config(
    tmp_path, monkeypatch, capsys
) -> None:
    rss, cfg, captured_default = _run_sweep_strategy_common_mocks(monkeypatch, tmp_path)
    rss.main(
        [
            "--strategy",
            "ma_crossover",
            "--param",
            "fast_window=20",
            "--config",
            str(cfg),
            "--no-registry",
            "--max-runs",
            "1",
        ]
    )
    capsys.readouterr()

    rss2, cfg2, captured_quiet = _run_sweep_strategy_common_mocks(monkeypatch, tmp_path)
    rss2.main(
        [
            "--strategy",
            "ma_crossover",
            "--param",
            "fast_window=20",
            "--config",
            str(cfg2),
            "--no-registry",
            "--max-runs",
            "1",
            "--quiet",
        ]
    )
    capsys.readouterr()

    assert len(captured_default) == 1
    assert len(captured_quiet) == 1
    default_cfg = captured_default[0]
    quiet_cfg = captured_quiet[0]
    assert default_cfg.strategy_key == quiet_cfg.strategy_key
    assert default_cfg.param_grid == quiet_cfg.param_grid
    assert default_cfg.symbol == quiet_cfg.symbol
    assert default_cfg.timeframe == quiet_cfg.timeframe
    assert default_cfg.max_runs == quiet_cfg.max_runs
    assert default_cfg.sort_by == quiet_cfg.sort_by
    assert default_cfg.sort_ascending == quiet_cfg.sort_ascending
    assert default_cfg.config_path == quiet_cfg.config_path


def test_run_sweep_strategy_quiet_warning_visible_via_logger(caplog) -> None:
    import logging

    from src.sweeps.engine import (
        apply_sweep_run_logging,
        logger as sweep_logger,
        restore_sweep_run_logging,
    )

    previous = apply_sweep_run_logging(quiet=True)
    try:
        with caplog.at_level(logging.WARNING, logger=sweep_logger.name):
            sweep_logger.warning("quiet-mode-warning-check")
    finally:
        restore_sweep_run_logging(previous)

    assert any("quiet-mode-warning-check" in r.message for r in caplog.records)
