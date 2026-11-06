"""CLI tests for run_comparison_promotion_candidate_eligibility_evidence_v1."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest_plugins = [
    "tests.meta.comparison_ssot_v1_fixtures",
    "tests.meta.comparison_completion_research_validity_binding_v1_fixtures",
    "tests.meta.comparison_completion_promotion_input_binding_v1_fixtures",
    "tests.meta.comparison_promotion_candidate_identity_binding_v1_fixtures",
    "tests.meta.comparison_promotion_candidate_eligibility_evidence_v1_fixtures",
]

from scripts.run_comparison_promotion_candidate_eligibility_evidence_v1 import (
    EXIT_EVIDENCE_ERROR,
    EXIT_OK,
    EXIT_USAGE_ERROR,
    main,
)
from src.meta.learning_loop.comparison_promotion_candidate_eligibility_evidence_v1 import (
    ARTIFACT_REL,
)
from tests.meta.comparison_promotion_candidate_eligibility_evidence_v1_fixtures import (
    produce_candidate_identity_binding_bundle,
)


@pytest.fixture(autouse=True)
def _allow_tmp_output(monkeypatch: pytest.MonkeyPatch) -> None:
    targets = (
        "src.meta.learning_loop.comparison_promotion_candidate_eligibility_evidence_v1.is_under_tmp",
        "src.meta.learning_loop.comparison_promotion_candidate_identity_binding_v1.is_under_tmp",
        "src.meta.learning_loop.comparison_completion_promotion_input_binding_v1.is_under_tmp",
        "src.meta.learning_loop.comparison_completion_research_validity_binding_v1.is_under_tmp",
        "src.meta.learning_loop.comparison_completion_evidence_v1.is_under_tmp",
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


def _durable_output(tmp_path: Path, name: str = "cli_out") -> Path:
    root = tmp_path / "evidence_root"
    root.mkdir(exist_ok=True)
    return root / name


def test_cli_happy_path(tmp_path, ssot_durable_output_dir, capsys) -> None:
    identity = produce_candidate_identity_binding_bundle(tmp_path, ssot_durable_output_dir)
    out = _durable_output(tmp_path)
    rc = main(
        [
            "--candidate-identity-binding-bundle-dir",
            str(identity.candidate_identity_binding_bundle_dir),
            "--output-dir",
            str(out),
        ]
    )
    assert rc == EXIT_OK
    captured = capsys.readouterr()
    assert "OK" in captured.out
    assert (out / ARTIFACT_REL).is_file()


def test_cli_missing_input(tmp_path, capsys) -> None:
    out = _durable_output(tmp_path)
    rc = main(
        [
            "--candidate-identity-binding-bundle-dir",
            str(tmp_path / "missing"),
            "--output-dir",
            str(out),
        ]
    )
    assert rc == EXIT_USAGE_ERROR
    assert "ERROR" in capsys.readouterr().err


def test_cli_evidence_error(tmp_path, ssot_durable_output_dir, capsys) -> None:
    identity = produce_candidate_identity_binding_bundle(tmp_path, ssot_durable_output_dir)
    out = _durable_output(tmp_path)
    out.mkdir()
    rc = main(
        [
            "--candidate-identity-binding-bundle-dir",
            str(identity.candidate_identity_binding_bundle_dir),
            "--output-dir",
            str(out),
        ]
    )
    assert rc == EXIT_EVIDENCE_ERROR
    assert "ERROR" in capsys.readouterr().err
