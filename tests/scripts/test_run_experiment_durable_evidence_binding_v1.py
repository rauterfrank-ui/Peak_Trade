"""CLI tests for Package E21 offline EXPERIMENT durable evidence binding v1."""

from __future__ import annotations

import json
import shutil
import uuid
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from scripts.run_experiment_durable_evidence_binding_v1 import (
    EXIT_BINDING_ERROR,
    EXIT_OK,
    EXIT_USAGE_ERROR,
    main,
)
from src.experiments.base import ExperimentConfig, ParamSweep
from src.experiments.experiment_identity_manifest_v1 import ARTIFACT_FILENAME
from src.experiments.experiment_identity_manifest_v1 import produce_experiment_identity_manifest_v1
from src.governance.promotion_loop.experiment_lineage_ref_producer_v1 import (
    produce_experiment_lineage_ref_v1,
    write_experiment_lineage_ref_v1_atomic,
)
from src.meta.learning_loop.experiment_durable_evidence_binding_v1 import INDEX_ARTIFACT_REL

REPO_ROOT = Path(__file__).resolve().parents[2]
_DURABLE_OUTPUT_ROOT = REPO_ROOT / ".package_e21_cli_pytest_outputs"
_durable_paths: list[Path] = []


@pytest.fixture(autouse=True)
def _allow_tmp_output(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "src.meta.learning_loop.experiment_durable_evidence_binding_v1.is_under_tmp",
        lambda _path: False,
    )


@pytest.fixture(autouse=True)
def _cleanup_durable_paths() -> None:
    yield
    for path in _durable_paths:
        if path.exists():
            shutil.rmtree(path, ignore_errors=True)
    _durable_paths.clear()
    for staging in _DURABLE_OUTPUT_ROOT.glob(".experiment_durable_evidence_staging_*"):
        shutil.rmtree(staging, ignore_errors=True)
    for staging in _DURABLE_OUTPUT_ROOT.glob(".experiment_identity_staging_*"):
        shutil.rmtree(staging, ignore_errors=True)


def _next_durable_output() -> Path:
    _DURABLE_OUTPUT_ROOT.mkdir(exist_ok=True)
    path = _DURABLE_OUTPUT_ROOT / uuid.uuid4().hex
    _durable_paths.append(path)
    return path


def _sample_config(**overrides: Any) -> ExperimentConfig:
    base = ExperimentConfig(
        name="MA Optimization",
        strategy_name="ma_crossover",
        param_sweeps=[
            ParamSweep("slow", [50, 100], description="ignored in identity"),
            ParamSweep("fast", [5, 10]),
        ],
        symbols=["ETH/EUR", "BTC/EUR"],
        timeframe="1h",
        start_date="2024-01-01",
        end_date="2024-06-01",
        initial_capital=10000.0,
        base_params={"window": 3},
    )
    for key, value in overrides.items():
        setattr(base, key, value)
    return base


def _write_inputs(tmp_path: Path) -> tuple[Path, Path, Path]:
    manifest_dir = _next_durable_output()
    produce_experiment_identity_manifest_v1(_sample_config(), manifest_dir)
    ref_path = tmp_path / "experiment_ref.json"
    ref_path.parent.mkdir(parents=True, exist_ok=True)
    result = produce_experiment_lineage_ref_v1(manifest_dir=manifest_dir)
    write_experiment_lineage_ref_v1_atomic(result.ref, ref_path)
    out_root = _DURABLE_OUTPUT_ROOT
    return manifest_dir, ref_path, out_root


def test_cli_successful_run(tmp_path: Path) -> None:
    manifest_dir, ref_path, _out_root = _write_inputs(tmp_path)
    out = _next_durable_output()
    rc = main(
        [
            "--manifest-dir",
            str(manifest_dir),
            "--experiment-lineage-ref",
            str(ref_path),
            "--output-dir",
            str(out),
        ]
    )
    assert rc == EXIT_OK
    assert (out / INDEX_ARTIFACT_REL).is_file()
    assert (out / ARTIFACT_FILENAME).is_file()


def test_cli_requires_all_paths() -> None:
    with pytest.raises(SystemExit):
        main([])


def test_cli_missing_manifest_dir_usage_error(tmp_path: Path) -> None:
    _, ref_path, out_root = _write_inputs(tmp_path)
    rc = main(
        [
            "--manifest-dir",
            str(tmp_path / "missing"),
            "--experiment-lineage-ref",
            str(ref_path),
            "--output-dir",
            str(_next_durable_output()),
        ]
    )
    assert rc == EXIT_USAGE_ERROR


def test_cli_missing_lineage_ref_usage_error(tmp_path: Path) -> None:
    manifest_dir, _, out_root = _write_inputs(tmp_path)
    rc = main(
        [
            "--manifest-dir",
            str(manifest_dir),
            "--experiment-lineage-ref",
            str(tmp_path / "missing.json"),
            "--output-dir",
            str(_next_durable_output()),
        ]
    )
    assert rc == EXIT_USAGE_ERROR


def test_cli_ref_id_mismatch_binding_error(tmp_path: Path) -> None:
    manifest_dir, ref_path, out_root = _write_inputs(tmp_path)
    payload = json.loads(ref_path.read_text(encoding="utf-8"))
    payload["ref_id"] = "0" * 64
    ref_path.write_text(json.dumps(payload), encoding="utf-8")
    rc = main(
        [
            "--manifest-dir",
            str(manifest_dir),
            "--experiment-lineage-ref",
            str(ref_path),
            "--output-dir",
            str(_next_durable_output()),
        ]
    )
    assert rc == EXIT_BINDING_ERROR


def test_cli_digest_mismatch_binding_error(tmp_path: Path) -> None:
    manifest_dir, ref_path, out_root = _write_inputs(tmp_path)
    payload = json.loads(ref_path.read_text(encoding="utf-8"))
    payload["digest"] = "0" * 64
    ref_path.write_text(json.dumps(payload), encoding="utf-8")
    rc = main(
        [
            "--manifest-dir",
            str(manifest_dir),
            "--experiment-lineage-ref",
            str(ref_path),
            "--output-dir",
            str(_next_durable_output()),
        ]
    )
    assert rc == EXIT_BINDING_ERROR


def test_cli_existing_output_binding_error(tmp_path: Path) -> None:
    manifest_dir, ref_path, out_root = _write_inputs(tmp_path)
    out = _next_durable_output()
    out.mkdir()
    rc = main(
        [
            "--manifest-dir",
            str(manifest_dir),
            "--experiment-lineage-ref",
            str(ref_path),
            "--output-dir",
            str(out),
        ]
    )
    assert rc == EXIT_BINDING_ERROR


def test_cli_stderr_has_no_manifest_payload_dump(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    manifest_dir, ref_path, out_root = _write_inputs(tmp_path)
    payload = json.loads(ref_path.read_text(encoding="utf-8"))
    payload["digest"] = "0" * 64
    ref_path.write_text(json.dumps(payload), encoding="utf-8")
    rc = main(
        [
            "--manifest-dir",
            str(manifest_dir),
            "--experiment-lineage-ref",
            str(ref_path),
            "--output-dir",
            str(_next_durable_output()),
        ]
    )
    assert rc == EXIT_BINDING_ERROR
    err = capsys.readouterr().err
    assert "ma_crossover" not in err
    assert "param_sweeps" not in err
    assert len(err) < 500


def test_cli_no_network_side_effects(tmp_path: Path) -> None:
    manifest_dir, ref_path, out_root = _write_inputs(tmp_path)
    out = _next_durable_output()
    with patch("urllib.request.urlopen", side_effect=AssertionError("network forbidden")):
        rc = main(
            [
                "--manifest-dir",
                str(manifest_dir),
                "--experiment-lineage-ref",
                str(ref_path),
                "--output-dir",
                str(out),
            ]
        )
    assert rc == EXIT_OK


def test_cli_deterministic_output(tmp_path: Path) -> None:
    manifest_dir, ref_path, out_root = _write_inputs(tmp_path)
    out1 = _next_durable_output()
    out2 = _next_durable_output()
    assert (
        main(
            [
                "--manifest-dir",
                str(manifest_dir),
                "--experiment-lineage-ref",
                str(ref_path),
                "--output-dir",
                str(out1),
            ]
        )
        == EXIT_OK
    )
    assert (
        main(
            [
                "--manifest-dir",
                str(manifest_dir),
                "--experiment-lineage-ref",
                str(ref_path),
                "--output-dir",
                str(out2),
            ]
        )
        == EXIT_OK
    )
    assert (out1 / INDEX_ARTIFACT_REL).read_bytes() == (out2 / INDEX_ARTIFACT_REL).read_bytes()
