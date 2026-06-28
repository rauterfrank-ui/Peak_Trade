"""CLI tests for run_research_validity_evidence_v1."""

from __future__ import annotations

import pytest

pytest_plugins = ["tests.meta.comparison_ssot_v1_fixtures"]

from scripts.run_research_validity_evidence_v1 import (
    EXIT_OK,
    EXIT_USAGE_ERROR,
    EXIT_VALIDITY_ERROR,
    main,
)
from src.meta.learning_loop.research_validity_evidence_v1 import ARTIFACT_REL
from tests.meta.research_validity_evidence_v1_fixtures import (
    produce_full_research_validity_inputs,
)


@pytest.fixture(autouse=True)
def _allow_tmp_output(monkeypatch: pytest.MonkeyPatch) -> None:
    targets = (
        "src.meta.learning_loop.research_validity_evidence_v1.is_under_tmp",
        "src.meta.learning_loop.comparison_checkpoint_v1.is_under_tmp",
        "src.meta.learning_loop.comparison_common_durable_evidence_binding_v1.is_under_tmp",
        "src.meta.learning_loop.comparison_metric_input_durable_evidence_binding_v1.is_under_tmp",
        "src.meta.learning_loop.comparison_ssot_definition_durable_evidence_binding_v1.is_under_tmp",
        "src.meta.learning_loop.comparison_ssot_result_durable_evidence_binding_v1.is_under_tmp",
        "src.experiments.experiment_identity_manifest_v1.is_under_tmp",
    )
    for target in targets:
        monkeypatch.setattr(target, lambda _path: False)


def test_cli_happy_path(tmp_path, ssot_durable_output_dir) -> None:
    inputs = produce_full_research_validity_inputs(
        tmp_path, ssot_durable_output_dir, all_domains_pass=True
    )
    out = ssot_durable_output_dir / "validity_cli"
    rc = main(
        [
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
    )
    assert rc == EXIT_OK
    assert (out / ARTIFACT_REL).is_file()


def test_cli_missing_bundle_usage_error(tmp_path) -> None:
    out = tmp_path / "evidence_root" / "out"
    rc = main(
        [
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
    )
    assert rc == EXIT_USAGE_ERROR


def test_cli_produce_error(tmp_path, ssot_durable_output_dir) -> None:
    inputs = produce_full_research_validity_inputs(
        tmp_path, ssot_durable_output_dir, all_domains_pass=True
    )
    out = ssot_durable_output_dir / "exists"
    out.mkdir()
    rc = main(
        [
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
    )
    assert rc == EXIT_VALIDITY_ERROR
