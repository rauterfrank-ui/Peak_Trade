"""CLI tests for run_ai_promotion_assessment_v1."""

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
    "tests.meta.comparison_config_patch_manifest_cross_domain_lineage_binding_v1_fixtures",
    "tests.meta.comparison_promotion_candidate_input_v1_fixtures",
    "tests.meta.comparison_eligibility_promotion_policy_input_binding_v1_fixtures",
    "tests.meta.comparison_promotion_policy_input_evidence_v1_fixtures",
    "tests.meta.comparison_promotion_policy_decision_v1_fixtures",
]

from scripts.run_ai_promotion_assessment_v1 import (
    EXIT_ASSESSMENT_ERROR,
    EXIT_OK,
    EXIT_USAGE_ERROR,
    main,
)
from src.meta.learning_loop.ai_promotion_assessment_v1 import ARTIFACT_REL
from tests.meta.comparison_promotion_policy_decision_v1_fixtures import (
    produce_policy_decision_fixture,
)


@pytest.fixture(autouse=True)
def _allow_tmp_output(monkeypatch: pytest.MonkeyPatch) -> None:
    targets = (
        "src.meta.learning_loop.ai_promotion_assessment_v1.is_under_tmp",
        "src.meta.learning_loop.comparison_promotion_policy_decision_v1.is_under_tmp",
        "src.meta.learning_loop.comparison_promotion_policy_input_evidence_v1.is_under_tmp",
        "src.meta.learning_loop.comparison_eligibility_promotion_policy_input_binding_v1.is_under_tmp",
        "src.meta.learning_loop.comparison_promotion_candidate_input_v1.is_under_tmp",
        "src.meta.learning_loop.comparison_config_patch_manifest_cross_domain_lineage_binding_v1.is_under_tmp",
        "src.meta.learning_loop.comparison_promotion_candidate_model_parameter_identity_binding_v1.is_under_tmp",
        "src.meta.learning_loop.comparison_promotion_candidate_eligibility_evidence_v1.is_under_tmp",
        "src.meta.learning_loop.comparison_promotion_candidate_identity_binding_v1.is_under_tmp",
        "src.meta.learning_loop.comparison_completion_promotion_input_binding_v1.is_under_tmp",
        "src.meta.learning_loop.comparison_completion_research_validity_binding_v1.is_under_tmp",
    )
    for target in targets:
        monkeypatch.setattr(target, lambda _path: False)


def _durable_output(tmp_path: Path, name: str = "cli_out") -> Path:
    root = tmp_path / "evidence_root"
    root.mkdir(exist_ok=True)
    return root / name


def test_cli_happy_path(tmp_path, ssot_durable_output_dir, capsys) -> None:
    decision = produce_policy_decision_fixture(tmp_path, ssot_durable_output_dir)
    assert decision.promotion_policy_decision_bundle_dir is not None
    out = _durable_output(tmp_path)
    rc = main(
        [
            "--policy-decision-bundle-dir",
            str(decision.promotion_policy_decision_bundle_dir),
            "--output-dir",
            str(out),
        ]
    )
    assert rc == EXIT_OK
    captured = capsys.readouterr()
    assert "OK" in captured.out
    assert "assessment_result=SUPPORTS_DECISION" in captured.out
    assert (out / ARTIFACT_REL).is_file()


def test_cli_missing_policy_decision(tmp_path, capsys) -> None:
    out = _durable_output(tmp_path)
    rc = main(
        [
            "--policy-decision-bundle-dir",
            str(tmp_path / "missing"),
            "--output-dir",
            str(out),
        ]
    )
    assert rc == EXIT_USAGE_ERROR


def test_cli_invalid_policy_decision_manifest(tmp_path, ssot_durable_output_dir, capsys) -> None:
    decision = produce_policy_decision_fixture(tmp_path, ssot_durable_output_dir)
    assert decision.promotion_policy_decision_bundle_dir is not None
    (decision.promotion_policy_decision_bundle_dir / "MANIFEST.sha256").write_text(
        "invalid", encoding="utf-8"
    )
    out = _durable_output(tmp_path)
    rc = main(
        [
            "--policy-decision-bundle-dir",
            str(decision.promotion_policy_decision_bundle_dir),
            "--output-dir",
            str(out),
        ]
    )
    assert rc == EXIT_ASSESSMENT_ERROR
    captured = capsys.readouterr()
    assert "ERROR" in captured.err
