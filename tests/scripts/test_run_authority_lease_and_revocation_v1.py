"""CLI tests for run_authority_lease_and_revocation_v1."""

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
    "tests.meta.handoff_trust_policy_v1_fixtures",
    "tests.meta.authority_lease_and_revocation_v1_fixtures",
]

from scripts.run_authority_lease_and_revocation_v1 import (
    EXIT_LEASE_ERROR,
    EXIT_OK,
    EXIT_USAGE_ERROR,
    main,
)
from src.meta.learning_loop.authority_lease_and_revocation_v1 import ARTIFACT_REL
from tests.meta.handoff_trust_policy_v1_fixtures import produce_handoff_trust_policy_fixture


@pytest.fixture(autouse=True)
def _allow_tmp_output(monkeypatch: pytest.MonkeyPatch) -> None:
    targets = (
        "src.meta.learning_loop.authority_lease_and_revocation_v1.is_under_tmp",
        "src.meta.learning_loop.handoff_trust_policy_v1.is_under_tmp",
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
    handoff = produce_handoff_trust_policy_fixture(tmp_path, ssot_durable_output_dir)
    out = _durable_output(tmp_path)
    rc = main(
        [
            "--handoff-trust-policy-bundle-dir",
            str(handoff.handoff_trust_policy_bundle_dir),
            "--output-dir",
            str(out),
        ]
    )
    assert rc == EXIT_OK
    captured = capsys.readouterr()
    assert "OK" in captured.out
    assert "lease_status=LEASE_CONTRACT_VALID" in captured.out
    assert (out / ARTIFACT_REL).is_file()


def test_cli_missing_handoff_bundle(tmp_path, ssot_durable_output_dir, capsys) -> None:
    out = _durable_output(tmp_path)
    rc = main(
        [
            "--handoff-trust-policy-bundle-dir",
            "/nonexistent/handoff",
            "--output-dir",
            str(out),
        ]
    )
    assert rc == EXIT_USAGE_ERROR


def test_cli_invalid_handoff_manifest(tmp_path, ssot_durable_output_dir, capsys) -> None:
    handoff = produce_handoff_trust_policy_fixture(tmp_path, ssot_durable_output_dir)
    bundle_dir = handoff.handoff_trust_policy_bundle_dir
    (bundle_dir / "MANIFEST.sha256").write_text("invalid", encoding="utf-8")
    out = _durable_output(tmp_path, "cli_invalid")
    rc = main(
        [
            "--handoff-trust-policy-bundle-dir",
            str(bundle_dir),
            "--output-dir",
            str(out),
        ]
    )
    assert rc == EXIT_LEASE_ERROR
