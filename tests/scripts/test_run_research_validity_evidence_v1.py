"""CLI contract tests for run_research_validity_evidence_v1."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

pytest_plugins = ["tests.meta.comparison_ssot_v1_fixtures"]

from tests.meta.research_validity_evidence_v1_fixtures import produce_full_research_validity_inputs

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts/run_research_validity_evidence_v1.py"


@pytest.fixture(autouse=True)
def _allow_tmp_output(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "src.meta.learning_loop.research_validity_evidence_v1.is_under_tmp",
        lambda _path: False,
    )
    monkeypatch.setattr(
        "src.experiments.experiment_identity_manifest_v1.is_under_tmp",
        lambda _path: False,
    )
    for target in (
        "src.meta.learning_loop.comparison_checkpoint_v1.is_under_tmp",
        "src.meta.learning_loop.comparison_common_durable_evidence_binding_v1.is_under_tmp",
        "src.meta.learning_loop.comparison_metric_input_durable_evidence_binding_v1.is_under_tmp",
        "src.meta.learning_loop.comparison_ssot_definition_durable_evidence_binding_v1.is_under_tmp",
        "src.meta.learning_loop.comparison_ssot_result_durable_evidence_binding_v1.is_under_tmp",
    ):
        monkeypatch.setattr(target, lambda _path: False)


def _durable_output(tmp_path: Path) -> Path:
    root = tmp_path / "cli_evidence_root"
    root.mkdir(exist_ok=True)
    return root / "cli_out"


def test_cli_happy_path(tmp_path, ssot_durable_output_dir) -> None:
    inputs = produce_full_research_validity_inputs(
        tmp_path, ssot_durable_output_dir, all_domains_pass=True
    )
    out = _durable_output(tmp_path)
    cmd = [
        sys.executable,
        str(SCRIPT),
        "--checkpoint-bundle-dir",
        str(inputs.checkpoint_bundle_dir),
        "--experiment-identity-bundle-dir",
        str(inputs.experiment_identity_bundle_dir),
        "--dataset-identity-bundle-dir",
        str(inputs.dataset_identity_bundle_dir),
        "--partition-evidence-bundle-dir",
        str(inputs.partition_evidence_bundle_dir),
        "--selection-procedure-bundle-dir",
        str(inputs.selection_procedure_bundle_dir),
        "--walk-forward-result-bundle-dir",
        str(inputs.walk_forward_result_bundle_dir),
        "--cost-stress-result-bundle-dir",
        str(inputs.cost_stress_result_bundle_dir),
        "--slippage-stress-result-bundle-dir",
        str(inputs.slippage_stress_result_bundle_dir),
        "--funding-stress-result-bundle-dir",
        str(inputs.funding_stress_result_bundle_dir),
        "--parameter-stability-result-bundle-dir",
        str(inputs.parameter_stability_result_bundle_dir),
        "--regime-breakdown-bundle-dir",
        str(inputs.regime_breakdown_bundle_dir),
        "--overfitting-risk-result-bundle-dir",
        str(inputs.overfitting_risk_result_bundle_dir),
        "--output-dir",
        str(out),
    ]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)
    result = subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    assert result.returncode == 0, result.stderr
    assert "research_validity_status=PASS" in result.stdout


def test_cli_missing_bundle_usage_error(tmp_path) -> None:
    out = _durable_output(tmp_path)
    cmd = [
        sys.executable,
        str(SCRIPT),
        "--checkpoint-bundle-dir",
        str(tmp_path / "missing"),
        "--experiment-identity-bundle-dir",
        str(tmp_path / "missing"),
        "--dataset-identity-bundle-dir",
        str(tmp_path / "missing"),
        "--partition-evidence-bundle-dir",
        str(tmp_path / "missing"),
        "--selection-procedure-bundle-dir",
        str(tmp_path / "missing"),
        "--walk-forward-result-bundle-dir",
        str(tmp_path / "missing"),
        "--cost-stress-result-bundle-dir",
        str(tmp_path / "missing"),
        "--slippage-stress-result-bundle-dir",
        str(tmp_path / "missing"),
        "--funding-stress-result-bundle-dir",
        str(tmp_path / "missing"),
        "--parameter-stability-result-bundle-dir",
        str(tmp_path / "missing"),
        "--regime-breakdown-bundle-dir",
        str(tmp_path / "missing"),
        "--overfitting-risk-result-bundle-dir",
        str(tmp_path / "missing"),
        "--output-dir",
        str(out),
    ]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)
    result = subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    assert result.returncode == 2


def test_cli_produce_error(tmp_path, ssot_durable_output_dir) -> None:
    inputs = produce_full_research_validity_inputs(
        tmp_path, ssot_durable_output_dir, all_domains_pass=True
    )
    out = _durable_output(tmp_path)
    out.mkdir()
    cmd = [
        sys.executable,
        str(SCRIPT),
        "--checkpoint-bundle-dir",
        str(inputs.checkpoint_bundle_dir),
        "--experiment-identity-bundle-dir",
        str(inputs.experiment_identity_bundle_dir),
        "--dataset-identity-bundle-dir",
        str(inputs.dataset_identity_bundle_dir),
        "--partition-evidence-bundle-dir",
        str(inputs.partition_evidence_bundle_dir),
        "--selection-procedure-bundle-dir",
        str(inputs.selection_procedure_bundle_dir),
        "--walk-forward-result-bundle-dir",
        str(inputs.walk_forward_result_bundle_dir),
        "--cost-stress-result-bundle-dir",
        str(inputs.cost_stress_result_bundle_dir),
        "--slippage-stress-result-bundle-dir",
        str(inputs.slippage_stress_result_bundle_dir),
        "--funding-stress-result-bundle-dir",
        str(inputs.funding_stress_result_bundle_dir),
        "--parameter-stability-result-bundle-dir",
        str(inputs.parameter_stability_result_bundle_dir),
        "--regime-breakdown-bundle-dir",
        str(inputs.regime_breakdown_bundle_dir),
        "--overfitting-risk-result-bundle-dir",
        str(inputs.overfitting_risk_result_bundle_dir),
        "--output-dir",
        str(out),
    ]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)
    result = subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    assert result.returncode == 1
