"""CLI tests for run_clock_trust_and_expiry_v1."""

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
    "tests.meta.ai_promotion_assessment_v1_fixtures",
    "tests.meta.versioned_strategy_model_parameter_artifact_v1_fixtures",
    "tests.meta.handoff_trust_policy_v1_fixtures",
    "tests.meta.authority_lease_and_revocation_v1_fixtures",
    "tests.meta.secure_handoff_envelope_v1_fixtures",
    "tests.meta.handoff_atomic_claim_consume_v1_fixtures",
    "tests.meta.clock_trust_and_expiry_v1_fixtures",
]

from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256
from scripts.run_clock_trust_and_expiry_v1 import (
    EXIT_CONTRACT_ERROR,
    EXIT_OK,
    EXIT_USAGE_ERROR,
    main,
)
from src.meta.learning_loop.clock_trust_and_expiry_v1 import ARTIFACT_REL, SELF_VERIFICATION_REL
from tests.meta.clock_trust_and_expiry_v1_fixtures import produce_clock_trust_and_expiry_fixture


@pytest.fixture(autouse=True)
def _allow_tmp_output(monkeypatch: pytest.MonkeyPatch) -> None:
    targets = (
        "src.meta.learning_loop.clock_trust_and_expiry_v1.is_under_tmp",
        "src.meta.learning_loop.handoff_atomic_claim_consume_v1.is_under_tmp",
        "src.meta.learning_loop.secure_handoff_envelope_v1.is_under_tmp",
        "src.meta.learning_loop.authority_lease_and_revocation_v1.is_under_tmp",
        "src.meta.learning_loop.handoff_trust_policy_v1.is_under_tmp",
        "src.meta.learning_loop.versioned_strategy_model_parameter_artifact_v1.is_under_tmp",
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
        "src.experiments.experiment_identity_manifest_v1.is_under_tmp",
    )
    for target in targets:
        monkeypatch.setattr(target, lambda _path: False)


def _durable_output(tmp_path: Path, name: str = "cli_clock_trust_out") -> Path:
    root = tmp_path / "evidence_root"
    root.mkdir(exist_ok=True)
    return root / name


def test_cli_happy_path(tmp_path, ssot_durable_output_dir, capsys) -> None:
    fixture = produce_clock_trust_and_expiry_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    out = _durable_output(tmp_path)
    rc = main(
        [
            "--secure-handoff-envelope-bundle-dir",
            str(fixture.secure_handoff_envelope_bundle_dir),
            "--handoff-atomic-claim-consume-bundle-dir",
            str(fixture.handoff_atomic_claim_consume_bundle_dir),
            "--authority-lease-bundle-dir",
            str(fixture.authority_lease_bundle_dir),
            "--evaluation-time",
            "2026-06-29T12:00:00+00:00",
            "--maximum-clock-skew-seconds",
            "3600",
            "--maximum-evidence-age-seconds",
            "86400",
            "--output-dir",
            str(out),
        ]
    )
    assert rc == EXIT_OK
    captured = capsys.readouterr()
    assert "clock_trust_and_expiry_v1] OK" in captured.out
    ok, msg = verify_manifest_sha256(out)
    assert ok, msg
    assert (out / ARTIFACT_REL).is_file()
    assert (out / SELF_VERIFICATION_REL).is_file()


def test_cli_missing_bundle(tmp_path, capsys) -> None:
    rc = main(
        [
            "--secure-handoff-envelope-bundle-dir",
            str(tmp_path / "missing_envelope"),
            "--handoff-atomic-claim-consume-bundle-dir",
            str(tmp_path / "missing_claim"),
            "--authority-lease-bundle-dir",
            str(tmp_path / "missing_lease"),
            "--maximum-clock-skew-seconds",
            "3600",
            "--maximum-evidence-age-seconds",
            "86400",
            "--output-dir",
            str(tmp_path / "out"),
        ]
    )
    assert rc == EXIT_USAGE_ERROR


def test_cli_expired_evaluation_time(tmp_path, ssot_durable_output_dir, capsys) -> None:
    fixture = produce_clock_trust_and_expiry_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    out = _durable_output(tmp_path, "expired_out")
    rc = main(
        [
            "--secure-handoff-envelope-bundle-dir",
            str(fixture.secure_handoff_envelope_bundle_dir),
            "--handoff-atomic-claim-consume-bundle-dir",
            str(fixture.handoff_atomic_claim_consume_bundle_dir),
            "--authority-lease-bundle-dir",
            str(fixture.authority_lease_bundle_dir),
            "--evaluation-time",
            "2026-06-30T00:00:00+00:00",
            "--maximum-clock-skew-seconds",
            "86400",
            "--maximum-evidence-age-seconds",
            "86400",
            "--output-dir",
            str(out),
        ]
    )
    assert rc == EXIT_OK
    captured = capsys.readouterr()
    assert "contract_status=CLOCK_TRUST_EXPIRED" in captured.out


def test_cli_missing_policy(tmp_path, ssot_durable_output_dir, capsys) -> None:
    fixture = produce_clock_trust_and_expiry_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    out = _durable_output(tmp_path, "policy_out")
    rc = main(
        [
            "--secure-handoff-envelope-bundle-dir",
            str(fixture.secure_handoff_envelope_bundle_dir),
            "--handoff-atomic-claim-consume-bundle-dir",
            str(fixture.handoff_atomic_claim_consume_bundle_dir),
            "--authority-lease-bundle-dir",
            str(fixture.authority_lease_bundle_dir),
            "--output-dir",
            str(out),
        ]
    )
    assert rc == EXIT_CONTRACT_ERROR
