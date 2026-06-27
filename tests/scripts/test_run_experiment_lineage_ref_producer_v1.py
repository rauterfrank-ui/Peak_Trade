"""CLI tests for Package M offline EXPERIMENT LineageRef producer."""

from __future__ import annotations

import json
import os
import shutil
import stat
import uuid
from pathlib import Path
from typing import Any, Callable
from unittest.mock import patch

import pytest

from scripts.run_experiment_lineage_ref_producer_v1 import (
    EXIT_OK,
    EXIT_PRODUCER_ERROR,
    main,
)
from src.experiments.base import ExperimentConfig, ParamSweep
from src.experiments.experiment_identity_manifest_v1 import (
    ARTIFACT_FILENAME,
    produce_experiment_identity_manifest_v1,
)
from src.governance.promotion_loop.experiment_lineage_ref_producer_v1 import (
    ExperimentLineageRefProducerError,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
_DURABLE_OUTPUT_ROOT = REPO_ROOT / ".package_m_cli_pytest_outputs"


@pytest.fixture
def durable_output_dir() -> Callable[[], Path]:
    _DURABLE_OUTPUT_ROOT.mkdir(exist_ok=True)
    created: list[Path] = []

    def _make() -> Path:
        path = _DURABLE_OUTPUT_ROOT / uuid.uuid4().hex
        created.append(path)
        return path

    yield _make

    for path in created:
        if path.exists():
            shutil.rmtree(path, ignore_errors=True)
    for staging in _DURABLE_OUTPUT_ROOT.glob(".experiment_identity_staging_*"):
        shutil.rmtree(staging, ignore_errors=True)


def _sample_config(**overrides: Any) -> ExperimentConfig:
    base = ExperimentConfig(
        name="MA Optimization",
        strategy_name="ma_crossover",
        param_sweeps=[ParamSweep("fast", [5, 10])],
        symbols=["ETH/EUR"],
        timeframe="1h",
        start_date="2024-01-01",
        end_date="2024-06-01",
        initial_capital=10000.0,
        base_params={"window": 3},
    )
    for key, value in overrides.items():
        setattr(base, key, value)
    return base


def _write_manifest_dir(durable_output_dir: Callable[[], Path]) -> tuple[Path, dict[str, Any]]:
    manifest_dir = durable_output_dir()
    produce_experiment_identity_manifest_v1(_sample_config(), manifest_dir)
    manifest = json.loads((manifest_dir / ARTIFACT_FILENAME).read_text(encoding="utf-8"))
    return manifest_dir, manifest


def test_cli_successful_run(
    tmp_path: Path,
    durable_output_dir: Callable[[], Path],
) -> None:
    manifest_dir, manifest = _write_manifest_dir(durable_output_dir)
    output_path = tmp_path / "ref.json"
    rc = main(["--manifest-dir", str(manifest_dir), "--output", str(output_path)])
    assert rc == EXIT_OK
    assert output_path.is_file()
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["ref_id"] == manifest["experiment_identity_id"]
    assert payload["ref_type"] == "experiment"
    assert payload["relation"] == "sources"
    assert payload["owner_domain"] == "experiments/base"


def test_cli_deterministic_output(
    tmp_path: Path,
    durable_output_dir: Callable[[], Path],
) -> None:
    manifest_dir, _manifest = _write_manifest_dir(durable_output_dir)
    output_a = tmp_path / "a.json"
    output_b = tmp_path / "b.json"
    assert main(["--manifest-dir", str(manifest_dir), "--output", str(output_a)]) == EXIT_OK
    assert main(["--manifest-dir", str(manifest_dir), "--output", str(output_b)]) == EXIT_OK
    assert output_a.read_text(encoding="utf-8") == output_b.read_text(encoding="utf-8")


def test_cli_requires_explicit_manifest_dir_and_output(
    tmp_path: Path,
    durable_output_dir: Callable[[], Path],
) -> None:
    manifest_dir, _manifest = _write_manifest_dir(durable_output_dir)
    with pytest.raises(SystemExit):
        main(["--output", str(tmp_path / "out.json")])
    with pytest.raises(SystemExit):
        main(["--manifest-dir", str(manifest_dir)])


def test_cli_invalid_input_is_producer_error(tmp_path: Path, capsys) -> None:
    manifest_dir = tmp_path / "empty-dir"
    manifest_dir.mkdir()
    output_path = tmp_path / "out.json"
    rc = main(["--manifest-dir", str(manifest_dir), "--output", str(output_path)])
    assert rc == EXIT_PRODUCER_ERROR
    assert not output_path.exists()
    assert "ERROR:" in capsys.readouterr().err


def test_cli_missing_input_manifest_fail_closed(tmp_path: Path, capsys) -> None:
    manifest_dir = tmp_path / "missing-manifest"
    manifest_dir.mkdir()
    output_path = tmp_path / "out.json"
    rc = main(["--manifest-dir", str(manifest_dir), "--output", str(output_path)])
    assert rc == EXIT_PRODUCER_ERROR
    assert not output_path.exists()
    assert ARTIFACT_FILENAME in capsys.readouterr().err


def test_cli_existing_output_fail_closed(
    tmp_path: Path,
    durable_output_dir: Callable[[], Path],
    capsys,
) -> None:
    manifest_dir, _manifest = _write_manifest_dir(durable_output_dir)
    output_path = tmp_path / "out.json"
    output_path.write_text('{"stale": true}', encoding="utf-8")
    rc = main(["--manifest-dir", str(manifest_dir), "--output", str(output_path)])
    assert rc == EXIT_PRODUCER_ERROR
    assert output_path.read_text(encoding="utf-8") == '{"stale": true}'
    assert "already exists" in capsys.readouterr().err


def test_cli_non_writable_output_parent(
    tmp_path: Path,
    durable_output_dir: Callable[[], Path],
) -> None:
    manifest_dir, _manifest = _write_manifest_dir(durable_output_dir)
    readonly_dir = tmp_path / "readonly"
    readonly_dir.mkdir()
    output_path = readonly_dir / "out.json"
    os.chmod(readonly_dir, stat.S_IRUSR | stat.S_IXUSR)
    try:
        rc = main(["--manifest-dir", str(manifest_dir), "--output", str(output_path)])
    finally:
        os.chmod(readonly_dir, stat.S_IRWXU)
    assert rc == EXIT_PRODUCER_ERROR
    assert not output_path.exists()


def test_cli_no_partial_output_on_producer_error(
    tmp_path: Path,
    durable_output_dir: Callable[[], Path],
) -> None:
    manifest_dir, manifest = _write_manifest_dir(durable_output_dir)
    tampered = dict(manifest)
    tampered["run_id"] = "forbidden-backtest-run"
    (manifest_dir / ARTIFACT_FILENAME).write_text(json.dumps(tampered), encoding="utf-8")
    output_path = tmp_path / "out.json"
    rc = main(["--manifest-dir", str(manifest_dir), "--output", str(output_path)])
    assert rc == EXIT_PRODUCER_ERROR
    assert not output_path.exists()
    assert not output_path.with_name(output_path.name + ".tmp").exists()


def test_cli_atomic_writer_success(
    tmp_path: Path,
    durable_output_dir: Callable[[], Path],
) -> None:
    manifest_dir, _manifest = _write_manifest_dir(durable_output_dir)
    output_path = tmp_path / "nested" / "ref.json"
    rc = main(["--manifest-dir", str(manifest_dir), "--output", str(output_path)])
    assert rc == EXIT_OK
    assert output_path.is_file()
    assert not output_path.with_name(output_path.name + ".tmp").exists()


def test_cli_producer_error_reports_on_stderr(
    tmp_path: Path,
    durable_output_dir: Callable[[], Path],
    capsys,
    monkeypatch,
) -> None:
    manifest_dir, _manifest = _write_manifest_dir(durable_output_dir)
    output_path = tmp_path / "out.json"

    def _raise(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise ExperimentLineageRefProducerError("forced producer failure")

    monkeypatch.setattr(
        "scripts.run_experiment_lineage_ref_producer_v1.produce_experiment_lineage_ref_v1_to_path",
        _raise,
    )
    rc = main(["--manifest-dir", str(manifest_dir), "--output", str(output_path)])
    assert rc == EXIT_PRODUCER_ERROR
    assert "forced producer failure" in capsys.readouterr().err


def test_cli_stable_exit_codes(
    tmp_path: Path,
    durable_output_dir: Callable[[], Path],
) -> None:
    manifest_dir, _manifest = _write_manifest_dir(durable_output_dir)
    assert (
        main(["--manifest-dir", str(manifest_dir), "--output", str(tmp_path / "ok.json")])
        == EXIT_OK
    )
    assert (
        main(
            [
                "--manifest-dir",
                str(tmp_path / "missing"),
                "--output",
                str(tmp_path / "bad.json"),
            ]
        )
        == EXIT_PRODUCER_ERROR
    )


def test_cli_no_experiment_backtest_registry_or_mlflow_calls(
    tmp_path: Path,
    durable_output_dir: Callable[[], Path],
    monkeypatch,
) -> None:
    manifest_dir, _manifest = _write_manifest_dir(durable_output_dir)
    output_path = tmp_path / "out.json"

    def _forbidden(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("forbidden side-effect invocation")

    monkeypatch.setattr(
        "src.risk.validation.var_suite_backtest_wiring_v1.resolve_backtest_returns",
        _forbidden,
    )
    with patch("urllib.request.urlopen", side_effect=_forbidden):
        rc = main(["--manifest-dir", str(manifest_dir), "--output", str(output_path)])
    assert rc == EXIT_OK


def test_cli_explicit_paths_only_no_defaults(
    tmp_path: Path,
    durable_output_dir: Callable[[], Path],
) -> None:
    manifest_dir, _manifest = _write_manifest_dir(durable_output_dir)
    output_path = tmp_path / "explicit.json"
    rc = main(["--manifest-dir", str(manifest_dir), "--output", str(output_path)])
    assert rc == EXIT_OK
    assert output_path.is_file()


def test_cli_durable_output_path(durable_output_dir: Callable[[], Path]) -> None:
    manifest_dir, _manifest = _write_manifest_dir(durable_output_dir)
    output_path = durable_output_dir() / "ref.json"
    rc = main(["--manifest-dir", str(manifest_dir), "--output", str(output_path)])
    assert rc == EXIT_OK
    assert output_path.is_file()
