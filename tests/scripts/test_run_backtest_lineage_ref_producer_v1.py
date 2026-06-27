"""CLI tests for Package I offline BACKTEST LineageRef producer."""

from __future__ import annotations

import json
import os
import stat
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.run_backtest_lineage_ref_producer_v1 import (
    EXIT_OK,
    EXIT_PRODUCER_ERROR,
    main,
)
from src.governance.promotion_loop.backtest_lineage_ref_producer_v1 import (
    RUN_SUMMARY_REL_PATH,
    BacktestLineageRefProducerError,
)

RUN_ID = "cli-run-001"


def _minimal_run_summary_data(*, run_id: str = RUN_ID, status: str = "FINISHED") -> dict:
    return {
        "run_id": run_id,
        "started_at_utc": "2025-01-15T10:00:00+00:00",
        "finished_at_utc": "2025-01-15T10:05:00+00:00",
        "status": status,
        "tracking_backend": "null",
    }


def _write_run_dir(tmp_path: Path, data: dict | None = None) -> Path:
    run_dir = tmp_path / "completed-run"
    run_dir.mkdir()
    payload = data if data is not None else _minimal_run_summary_data()
    (run_dir / RUN_SUMMARY_REL_PATH).write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return run_dir


def test_cli_successful_run(tmp_path: Path) -> None:
    run_dir = _write_run_dir(tmp_path)
    output_path = tmp_path / "ref.json"
    rc = main(["--run-dir", str(run_dir), "--output", str(output_path)])
    assert rc == EXIT_OK
    assert output_path.is_file()
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["ref_id"] == RUN_ID
    assert payload["ref_type"] == "backtest"


def test_cli_deterministic_output(tmp_path: Path) -> None:
    run_dir = _write_run_dir(tmp_path)
    output_a = tmp_path / "a.json"
    output_b = tmp_path / "b.json"
    assert main(["--run-dir", str(run_dir), "--output", str(output_a)]) == EXIT_OK
    assert main(["--run-dir", str(run_dir), "--output", str(output_b)]) == EXIT_OK
    assert output_a.read_text(encoding="utf-8") == output_b.read_text(encoding="utf-8")


def test_cli_requires_explicit_run_dir_and_output(tmp_path: Path) -> None:
    run_dir = _write_run_dir(tmp_path)
    with pytest.raises(SystemExit):
        main(["--output", str(tmp_path / "out.json")])
    with pytest.raises(SystemExit):
        main(["--run-dir", str(run_dir)])


def test_cli_invalid_run_is_producer_error(tmp_path: Path, capsys) -> None:
    run_dir = tmp_path / "empty-run"
    run_dir.mkdir()
    output_path = tmp_path / "out.json"
    rc = main(["--run-dir", str(run_dir), "--output", str(output_path)])
    assert rc == EXIT_PRODUCER_ERROR
    assert not output_path.exists()
    assert "ERROR:" in capsys.readouterr().err


def test_cli_non_completed_run_is_producer_error(tmp_path: Path, capsys) -> None:
    run_dir = _write_run_dir(tmp_path, _minimal_run_summary_data(status="RUNNING"))
    output_path = tmp_path / "out.json"
    rc = main(["--run-dir", str(run_dir), "--output", str(output_path)])
    assert rc == EXIT_PRODUCER_ERROR
    assert not output_path.exists()
    assert "not completed" in capsys.readouterr().err


def test_cli_existing_output_fail_closed(tmp_path: Path, capsys) -> None:
    run_dir = _write_run_dir(tmp_path)
    output_path = tmp_path / "out.json"
    output_path.write_text('{"stale": true}', encoding="utf-8")
    rc = main(["--run-dir", str(run_dir), "--output", str(output_path)])
    assert rc == EXIT_PRODUCER_ERROR
    assert output_path.read_text(encoding="utf-8") == '{"stale": true}'
    assert "already exists" in capsys.readouterr().err


def test_cli_non_writable_output_parent(tmp_path: Path) -> None:
    run_dir = _write_run_dir(tmp_path)
    readonly_dir = tmp_path / "readonly"
    readonly_dir.mkdir()
    output_path = readonly_dir / "out.json"
    os.chmod(readonly_dir, stat.S_IRUSR | stat.S_IXUSR)
    try:
        rc = main(["--run-dir", str(run_dir), "--output", str(output_path)])
    finally:
        os.chmod(readonly_dir, stat.S_IRWXU)
    assert rc == EXIT_PRODUCER_ERROR
    assert not output_path.exists()


def test_cli_no_partial_output_on_producer_error(tmp_path: Path) -> None:
    run_dir = _write_run_dir(tmp_path, _minimal_run_summary_data(status="FAILED"))
    output_path = tmp_path / "out.json"
    rc = main(["--run-dir", str(run_dir), "--output", str(output_path)])
    assert rc == EXIT_PRODUCER_ERROR
    assert not output_path.exists()
    assert not output_path.with_name(output_path.name + ".tmp").exists()


def test_cli_atomic_writer_success(tmp_path: Path) -> None:
    run_dir = _write_run_dir(tmp_path)
    output_path = tmp_path / "nested" / "ref.json"
    rc = main(["--run-dir", str(run_dir), "--output", str(output_path)])
    assert rc == EXIT_OK
    assert output_path.is_file()
    assert not output_path.with_name(output_path.name + ".tmp").exists()


def test_cli_writer_error_before_replace(tmp_path: Path, monkeypatch) -> None:
    run_dir = _write_run_dir(tmp_path)
    output_path = tmp_path / "out.json"

    def _fail_write(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise OSError("forced write failure")

    monkeypatch.setattr(Path, "write_text", _fail_write)
    rc = main(["--run-dir", str(run_dir), "--output", str(output_path)])
    assert rc == EXIT_PRODUCER_ERROR
    assert not output_path.exists()


def test_cli_writer_error_on_replace(tmp_path: Path, monkeypatch) -> None:
    run_dir = _write_run_dir(tmp_path)
    output_path = tmp_path / "out.json"
    original = Path.replace

    def _fail_replace(self, target):  # type: ignore[no-untyped-def]
        if self.name.endswith(".tmp"):
            raise OSError("forced replace failure")
        return original(self, target)

    monkeypatch.setattr(Path, "replace", _fail_replace)
    rc = main(["--run-dir", str(run_dir), "--output", str(output_path)])
    assert rc == EXIT_PRODUCER_ERROR
    assert not output_path.exists()
    assert list(output_path.parent.glob("*.tmp")) == []


def test_cli_stderr_without_secrets_or_full_run_summary_payload(tmp_path: Path, capsys) -> None:
    run_dir = _write_run_dir(
        tmp_path,
        {
            **_minimal_run_summary_data(),
            "params": {"secret_token": "super-secret-value"},
            "metrics": {"sharpe": 9.9},
        },
    )
    output_path = tmp_path / "out.json"
    rc = main(["--run-dir", str(run_dir), "--output", str(output_path)])
    assert rc == EXIT_OK
    err = capsys.readouterr().err
    assert "super-secret-value" not in err
    assert "sharpe" not in err
    assert "secret" not in err.lower()


def test_cli_producer_error_reports_on_stderr(tmp_path: Path, capsys, monkeypatch) -> None:
    run_dir = _write_run_dir(tmp_path)
    output_path = tmp_path / "out.json"

    def _raise(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise BacktestLineageRefProducerError("forced producer failure")

    monkeypatch.setattr(
        "scripts.run_backtest_lineage_ref_producer_v1.produce_backtest_lineage_ref_v1_to_path",
        _raise,
    )
    rc = main(["--run-dir", str(run_dir), "--output", str(output_path)])
    assert rc == EXIT_PRODUCER_ERROR
    assert "forced producer failure" in capsys.readouterr().err


def test_cli_stable_exit_codes(tmp_path: Path) -> None:
    run_dir = _write_run_dir(tmp_path)
    assert main(["--run-dir", str(run_dir), "--output", str(tmp_path / "ok.json")]) == EXIT_OK
    assert (
        main(["--run-dir", str(tmp_path / "missing"), "--output", str(tmp_path / "bad.json")])
        == EXIT_PRODUCER_ERROR
    )


def test_cli_no_backtest_registry_or_network_calls(tmp_path: Path, monkeypatch) -> None:
    run_dir = _write_run_dir(tmp_path)
    output_path = tmp_path / "out.json"

    def _forbidden(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("forbidden side-effect invocation")

    monkeypatch.setattr(
        "src.risk.validation.var_suite_backtest_wiring_v1.resolve_backtest_returns",
        _forbidden,
    )
    with patch("urllib.request.urlopen", side_effect=_forbidden):
        rc = main(["--run-dir", str(run_dir), "--output", str(output_path)])
    assert rc == EXIT_OK
