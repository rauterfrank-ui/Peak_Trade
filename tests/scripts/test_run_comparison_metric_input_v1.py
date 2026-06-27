"""CLI tests for scripts/run_comparison_metric_input_v1.py."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.run_comparison_metric_input_v1 import build_parser, main
from src.meta.learning_loop.comparison_metric_input_v1.constants import ARTIFACT_FILENAME
from tests.meta.comparison_metric_input_v1_fixtures import (
    build_backtest_run_dir,
    build_experiment_bundle,
    build_var_suite_bundle,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CLI = REPO_ROOT / "scripts" / "run_comparison_metric_input_v1.py"


def _write_ref(path: Path, ref: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(ref), encoding="utf-8")


def test_build_parser_requires_source_domain_and_output_root() -> None:
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args([])


def test_cli_backtest_happy_path(tmp_path, durable_output_dir) -> None:
    run_dir, ref = build_backtest_run_dir(tmp_path)
    ref_path = tmp_path / "backtest_ref.json"
    _write_ref(ref_path, ref)
    rc = main(
        [
            "--source-domain",
            "BACKTEST",
            "--output-root",
            str(durable_output_dir),
            "--source-ref",
            str(ref_path),
            "--run-dir",
            str(run_dir),
        ]
    )
    assert rc == 0


def test_cli_experiment_happy_path(tmp_path, durable_output_dir) -> None:
    completed_dir, _ = build_backtest_run_dir(tmp_path / "completed")
    manifest_dir, exp_ref, completed = build_experiment_bundle(tmp_path, completed_dir)
    ref_path = tmp_path / "experiment_ref.json"
    _write_ref(ref_path, exp_ref)
    rc = main(
        [
            "--source-domain",
            "EXPERIMENT",
            "--output-root",
            str(durable_output_dir),
            "--source-ref",
            str(ref_path),
            "--manifest-dir",
            str(manifest_dir),
            "--completed-run-dir",
            str(completed),
        ]
    )
    assert rc == 0


def test_cli_var_suite_happy_path(tmp_path, durable_output_dir) -> None:
    run_dir, backtest_ref = build_backtest_run_dir(tmp_path)
    suite_dir, var_ref, _ = build_var_suite_bundle(
        tmp_path,
        companion_run_dir=run_dir,
        backtest_ref=backtest_ref,
    )
    var_ref_path = tmp_path / "var_ref.json"
    backtest_ref_path = tmp_path / "backtest_ref.json"
    _write_ref(var_ref_path, var_ref)
    _write_ref(backtest_ref_path, backtest_ref)
    rc = main(
        [
            "--source-domain",
            "VAR_SUITE",
            "--output-root",
            str(durable_output_dir),
            "--source-ref",
            str(var_ref_path),
            "--suite-report-dir",
            str(suite_dir),
            "--companion-run-dir",
            str(run_dir),
            "--backtest-source-ref",
            str(backtest_ref_path),
        ]
    )
    assert rc == 0


def test_cli_missing_run_dir_returns_error(tmp_path, durable_output_dir, capsys) -> None:
    run_dir, ref = build_backtest_run_dir(tmp_path)
    ref_path = tmp_path / "backtest_ref.json"
    _write_ref(ref_path, ref)
    rc = main(
        [
            "--source-domain",
            "BACKTEST",
            "--output-root",
            str(durable_output_dir / "missing-run"),
            "--source-ref",
            str(ref_path),
        ]
    )
    assert rc == 1
    assert "ERROR:" in capsys.readouterr().err


def test_cli_invalid_source_ref_json_returns_error(tmp_path, durable_output_dir, capsys) -> None:
    bad_ref = tmp_path / "bad_ref.json"
    bad_ref.write_text("[1, 2, 3]", encoding="utf-8")
    rc = main(
        [
            "--source-domain",
            "BACKTEST",
            "--output-root",
            str(durable_output_dir),
            "--source-ref",
            str(bad_ref),
            "--run-dir",
            str(tmp_path / "missing"),
        ]
    )
    assert rc == 1
    assert "ERROR:" in capsys.readouterr().err


def test_cli_module_entrypoint_runs_via_subprocess(tmp_path, durable_output_dir) -> None:
    run_dir, ref = build_backtest_run_dir(tmp_path)
    ref_path = tmp_path / "backtest_ref.json"
    _write_ref(ref_path, ref)
    proc = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "--source-domain",
            "BACKTEST",
            "--output-root",
            str(durable_output_dir),
            "--source-ref",
            str(ref_path),
            "--run-dir",
            str(run_dir),
        ],
        cwd=str(REPO_ROOT),
        env={**os.environ, "PYTHONPATH": str(REPO_ROOT)},
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    manifest_path = Path(proc.stdout.strip())
    assert manifest_path.name == ARTIFACT_FILENAME


def test_cli_backtest_prints_manifest_path(tmp_path, durable_output_dir, capsys) -> None:
    run_dir, ref = build_backtest_run_dir(tmp_path)
    ref_path = tmp_path / "backtest_ref.json"
    _write_ref(ref_path, ref)
    rc = main(
        [
            "--source-domain",
            "BACKTEST",
            "--output-root",
            str(durable_output_dir),
            "--source-ref",
            str(ref_path),
            "--run-dir",
            str(run_dir),
        ]
    )
    assert rc == 0
    out = capsys.readouterr().out.strip()
    assert out.endswith(ARTIFACT_FILENAME)
