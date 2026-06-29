"""CLI tests for run_versioned_strategy_model_parameter_artifact_v1."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest_plugins = [
    "tests.meta.comparison_ssot_v1_fixtures",
    "tests.meta.comparison_completion_research_validity_binding_v1_fixtures",
    "tests.meta.comparison_completion_promotion_input_binding_v1_fixtures",
    "tests.meta.comparison_promotion_candidate_identity_binding_v1_fixtures",
    "tests.meta.comparison_promotion_candidate_eligibility_evidence_v1_fixtures",
    "tests.meta.comparison_promotion_candidate_model_parameter_identity_binding_v1_fixtures",
    "tests.meta.versioned_strategy_model_parameter_artifact_v1_fixtures",
]

from scripts.run_versioned_strategy_model_parameter_artifact_v1 import (
    EXIT_ARTIFACT_ERROR,
    EXIT_OK,
    EXIT_USAGE_ERROR,
    main,
)
from src.meta.learning_loop.comparison_promotion_candidate_identity_binding_v1 import (
    ARTIFACT_REL as CANDIDATE_IDENTITY_ARTIFACT_REL,
)
from src.meta.learning_loop.comparison_ssot_v1.io import read_manifest
from src.meta.learning_loop.contract_safety_v1 import deterministic_json_dumps
from src.meta.learning_loop.versioned_strategy_model_parameter_artifact_v1 import ARTIFACT_REL
from tests.meta.versioned_strategy_model_parameter_artifact_v1_fixtures import (
    produce_versioned_artifact_input_bundles,
)


@pytest.fixture(autouse=True)
def _allow_tmp_output(monkeypatch: pytest.MonkeyPatch) -> None:
    targets = (
        "src.meta.learning_loop.versioned_strategy_model_parameter_artifact_v1.is_under_tmp",
        "src.meta.learning_loop.comparison_promotion_candidate_model_parameter_identity_binding_v1.is_under_tmp",
        "src.meta.learning_loop.comparison_promotion_candidate_eligibility_evidence_v1.is_under_tmp",
        "src.meta.learning_loop.comparison_promotion_candidate_identity_binding_v1.is_under_tmp",
        "src.meta.learning_loop.comparison_completion_promotion_input_binding_v1.is_under_tmp",
        "src.meta.learning_loop.comparison_completion_research_validity_binding_v1.is_under_tmp",
        "src.experiments.experiment_identity_manifest_v1.is_under_tmp",
    )
    for target in targets:
        monkeypatch.setattr(target, lambda _path: False)


def _durable_output(tmp_path: Path, name: str = "cli_out") -> Path:
    root = tmp_path / "evidence_root"
    root.mkdir(exist_ok=True)
    return root / name


def test_cli_happy_path(tmp_path, ssot_durable_output_dir, capsys) -> None:
    bundles = produce_versioned_artifact_input_bundles(tmp_path, ssot_durable_output_dir)
    out = _durable_output(tmp_path)
    rc = main(
        [
            "--candidate-identity-binding-bundle-dir",
            str(bundles.candidate_identity_binding_bundle_dir),
            "--model-parameter-identity-binding-bundle-dir",
            str(bundles.model_parameter_identity_binding_bundle_dir),
            "--output-dir",
            str(out),
        ]
    )
    assert rc == EXIT_OK
    captured = capsys.readouterr()
    assert "OK" in captured.out
    assert "versioned_artifact_binding_status=PASS" in captured.out
    assert (out / ARTIFACT_REL).is_file()


def test_cli_missing_candidate_bundle(tmp_path, ssot_durable_output_dir, capsys) -> None:
    bundles = produce_versioned_artifact_input_bundles(tmp_path, ssot_durable_output_dir)
    out = _durable_output(tmp_path)
    rc = main(
        [
            "--candidate-identity-binding-bundle-dir",
            "/nonexistent/candidate",
            "--model-parameter-identity-binding-bundle-dir",
            str(bundles.model_parameter_identity_binding_bundle_dir),
            "--output-dir",
            str(out),
        ]
    )
    assert rc == EXIT_USAGE_ERROR


def test_cli_mismatched_bindings(tmp_path, ssot_durable_output_dir, capsys) -> None:
    bundles = produce_versioned_artifact_input_bundles(tmp_path, ssot_durable_output_dir)
    candidate_path = bundles.candidate_identity_binding_bundle_dir / CANDIDATE_IDENTITY_ARTIFACT_REL
    payload = read_manifest(candidate_path)
    payload["comparison_definition_id"] = "tampered-comparison-definition-id"
    candidate_path.write_text(deterministic_json_dumps(payload), encoding="utf-8")
    out = _durable_output(tmp_path, "cli_mismatch")
    rc = main(
        [
            "--candidate-identity-binding-bundle-dir",
            str(bundles.candidate_identity_binding_bundle_dir),
            "--model-parameter-identity-binding-bundle-dir",
            str(bundles.model_parameter_identity_binding_bundle_dir),
            "--output-dir",
            str(out),
        ]
    )
    assert rc == EXIT_ARTIFACT_ERROR
