"""CLI tests for Package N experiment identity manifest producer v1."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import uuid
from collections.abc import Callable
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
CLI = REPO_ROOT / "scripts" / "run_experiment_identity_manifest_v1.py"
_DURABLE_OUTPUT_ROOT = REPO_ROOT / ".package_n_pytest_outputs"


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


def _write_config(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "name": "CLI Test",
                "strategy_name": "ma_crossover",
                "param_sweeps": [{"name": "fast", "values": [5, 10]}],
                "symbols": ["BTC/EUR"],
                "timeframe": "1h",
            }
        ),
        encoding="utf-8",
    )


def test_cli_success_exit_code(
    tmp_path: Path,
    durable_output_dir: Callable[[], Path],
) -> None:
    config = tmp_path / "config.json"
    out = durable_output_dir()
    _write_config(config)
    proc = subprocess.run(
        [sys.executable, str(CLI), "--config-json", str(config), "--output-dir", str(out)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    assert (out / "experiment_identity_manifest_v1.json").is_file()


def test_cli_usage_error_exit_code() -> None:
    proc = subprocess.run(
        [sys.executable, str(CLI)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 2


def test_cli_binding_error_exit_code(tmp_path: Path) -> None:
    config = tmp_path / "config.json"
    out = tmp_path / "output"
    config.write_text(json.dumps({"name": "missing strategy"}), encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(CLI), "--config-json", str(config), "--output-dir", str(out)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 1


def test_cli_output_dir_outside_tmp(tmp_path: Path) -> None:
    config = tmp_path / "config.json"
    _write_config(config)
    proc = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "--config-json",
            str(config),
            "--output-dir",
            "/tmp/pkg_n_forbidden",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 1
    assert "outside /tmp" in proc.stderr
