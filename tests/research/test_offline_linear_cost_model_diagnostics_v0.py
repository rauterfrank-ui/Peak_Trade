from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from src.research.linear_evidence.feature_matrix import build_feature_matrix_binding
from src.research.linear_evidence.fitters import fit_ols_lstsq


def test_feature_matrix_blocks_random_validation_split() -> None:
    with pytest.raises(ValueError, match="RANDOM_VALIDATION_SPLIT_BLOCKED"):
        build_feature_matrix_binding(
            [{"decision_time": "2026-01-01T00:00:00Z", "x": 1.0, "y": 2.0}],
            feature_names=("x",),
            target_name="y",
            validation_policy="RANDOM",
        )


def test_ols_evidence_is_authority_neutral() -> None:
    rows = [
        {
            "decision_time": f"2026-01-01T0{i}:00:00Z",
            "x": float(i),
            "z": float(i + 1),
            "y": float(2 * i + 1),
        }
        for i in range(8)
    ]
    x, y, binding = build_feature_matrix_binding(rows, feature_names=("x", "z"), target_name="y")
    evidence = fit_ols_lstsq(x, y, binding)

    assert evidence.solver == "numpy.linalg.lstsq"
    assert evidence.authority_effect == "NONE"
    assert evidence.runtime_effect == "NONE"
    assert evidence.cost_policy_output == "diagnostic_only"
    assert evidence.validation_policy == "TIME_ORDERED"


def test_offline_linear_cost_model_diagnostics_cli_fail_closed_without_materialized_rows(
    tmp_path: Path,
) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/research/offline_linear_cost_model_diagnostics_v0.py",
            "--out",
            str(tmp_path),
        ],
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, result.stderr
    report = json.loads((tmp_path / "offline_linear_cost_model_diagnostics_v0.json").read_text())
    assert report["offline_only"] is True
    assert report["runtime_authority"] is False
    assert report["order_authority"] is False
    assert report["promotion_pass_authority"] is False
    assert report["backtest_cost_default_change"] is False
    assert report["n_productive_samples"] == 0
    assert report["ols_executed"] is False
    assert report["verdict"] == "OFFLINE_LINEAR_COST_MODEL_DIAGNOSTICS_V0_FAIL_CLOSED"


def test_offline_linear_cost_model_diagnostics_fixture_scaffold_cli(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/research/offline_linear_cost_model_diagnostics_v0.py",
            "--out",
            str(tmp_path),
            "--fixture-scaffold",
        ],
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, result.stderr
    report = json.loads((tmp_path / "offline_linear_cost_model_diagnostics_v0.json").read_text())
    assert report["offline_only"] is True
    assert report["fixture_scaffold_only"] is True
    assert report["n_productive_samples"] == 0
    assert report["calibration"]["calibrated_cost_policy"] == "CONSERVATIVE_NOT_MEAN"
