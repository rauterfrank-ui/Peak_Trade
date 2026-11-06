"""Contract tests for run_unknown_execution_outcome_recovery_v1 script."""

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
    "tests.meta.trading_session_single_writer_v1_fixtures",
    "tests.meta.canonical_order_lifecycle_v1_fixtures",
    "tests.meta.order_intent_idempotency_v1_fixtures",
    "tests.meta.trading_core_decision_attestation_v1_fixtures",
    "tests.meta.trading_logic_semantic_diff_evidence_v1_fixtures",
    "tests.meta.runtime_state_reconciliation_v1_fixtures",
    "tests.meta.unknown_execution_outcome_recovery_v1_fixtures",
]

from scripts.run_unknown_execution_outcome_recovery_v1 import (
    EXIT_CONTRACT_ERROR,
    EXIT_OK,
    EXIT_USAGE_ERROR,
    main,
)
from tests.meta.unknown_execution_outcome_recovery_v1_fixtures import (
    produce_unknown_execution_outcome_recovery_fixture,
)


@pytest.fixture(autouse=True)
def _allow_tmp_output(monkeypatch: pytest.MonkeyPatch) -> None:
    targets = (
        "src.meta.learning_loop.unknown_execution_outcome_recovery_v1.is_under_tmp",
        "src.meta.learning_loop.runtime_state_reconciliation_v1.is_under_tmp",
        "src.meta.learning_loop.trading_logic_semantic_diff_evidence_v1.is_under_tmp",
        "src.meta.learning_loop.trading_core_decision_attestation_v1.is_under_tmp",
        "src.meta.learning_loop.order_intent_idempotency_v1.is_under_tmp",
        "src.meta.learning_loop.canonical_order_lifecycle_v1.is_under_tmp",
        "src.meta.learning_loop.trading_session_single_writer_v1.is_under_tmp",
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


def test_script_happy_path(tmp_path, ssot_durable_output_dir, capsys) -> None:
    fixture = produce_unknown_execution_outcome_recovery_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    out = tmp_path / "evidence_root" / "script_recovery"
    rc = main(
        [
            "--runtime-state-reconciliation-bundle-dir",
            str(fixture.runtime_state_reconciliation_bundle_dir),
            "--order-intent-idempotency-bundle-dir",
            str(fixture.order_intent_idempotency_bundle_dir),
            "--output-dir",
            str(out),
        ]
    )
    assert rc == EXIT_OK
    captured = capsys.readouterr()
    assert "UNKNOWN_EXECUTION_OUTCOME_RECOVERY_VALID" in captured.out


def test_script_missing_reconciliation_bundle(tmp_path) -> None:
    rc = main(
        [
            "--runtime-state-reconciliation-bundle-dir",
            str(tmp_path / "missing"),
            "--order-intent-idempotency-bundle-dir",
            str(tmp_path / "also-missing"),
            "--output-dir",
            str(tmp_path / "out"),
        ]
    )
    assert rc == EXIT_USAGE_ERROR


def test_script_spot_produces_fail_closed_contract(
    tmp_path, ssot_durable_output_dir, capsys
) -> None:
    fixture = produce_unknown_execution_outcome_recovery_fixture(
        tmp_path,
        ssot_durable_output_dir,
        produce_output=False,
        instrument_type="SPOT",
    )
    out = tmp_path / "evidence_root" / "script_spot_recovery"
    rc = main(
        [
            "--runtime-state-reconciliation-bundle-dir",
            str(fixture.runtime_state_reconciliation_bundle_dir),
            "--order-intent-idempotency-bundle-dir",
            str(fixture.order_intent_idempotency_bundle_dir),
            "--instrument-type",
            "SPOT",
            "--output-dir",
            str(out),
        ]
    )
    assert rc == EXIT_OK
    captured = capsys.readouterr()
    assert "UNKNOWN_EXECUTION_OUTCOME_RECOVERY_FUTURES_MARKET_TYPE_CONFLICT" in captured.out
