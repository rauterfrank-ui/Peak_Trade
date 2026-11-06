"""Contract tests for unknown_execution_outcome_recovery_v1."""

from __future__ import annotations

from dataclasses import replace
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

from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256
from src.meta.learning_loop.comparison_ssot_v1.io import read_manifest
from src.meta.learning_loop.contract_safety_v1 import deterministic_json_dumps
from src.meta.learning_loop.unknown_execution_outcome_recovery_v1 import (
    ARTIFACT_REL,
    CONTRACT_NAME,
    CONTRACT_VERSION,
    RECOVERY_CONTRACT_VERSION,
    UNKNOWN_EXECUTION_OUTCOME_RECOVERY_AUTHORITY_INVARIANTS,
    RecoveryEvidenceSignals,
    RecoverySnapshotBinding,
    UnknownExecutionRecoveryInputs,
    build_unknown_execution_outcome_recovery_v1,
    default_unknown_execution_recovery_request,
    produce_unknown_execution_outcome_recovery_v1,
    reverify_unknown_execution_outcome_recovery_v1,
    verify_order_intent_idempotency_bundle,
    verify_runtime_state_reconciliation_bundle,
)
from tests.meta.unknown_execution_outcome_recovery_v1_fixtures import (
    produce_unknown_execution_outcome_recovery_fixture,
)

_NON_EXEC_FLAGS = (
    "order_created",
    "order_submission_requested",
    "order_submitted",
    "order_state_mutated",
    "adapter_invoked",
    "exchange_request_sent",
    "network_side_effect_created",
    "database_mutated",
    "lock_acquired",
    "reservation_created",
    "runtime_state_mutated",
    "recovery_action_executed",
    "order_resubmitted",
    "new_client_order_id_created",
    "live_authorized",
    "orders_allowed",
    "scheduler_runtime_allowed",
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


def _durable_output(tmp_path: Path, name: str = "recovery_out") -> Path:
    root = tmp_path / "evidence_root"
    root.mkdir(exist_ok=True)
    return root / name


def _fixture_context(fixture):
    reconciliation = verify_runtime_state_reconciliation_bundle(
        fixture.runtime_state_reconciliation_bundle_dir
    )
    idempotency = verify_order_intent_idempotency_bundle(
        fixture.order_intent_idempotency_bundle_dir
    )
    request = default_unknown_execution_recovery_request(
        reconciliation=reconciliation,
        idempotency=idempotency,
    )
    return reconciliation, idempotency, request


def _build(fixture, **kwargs):
    reconciliation, idempotency, request = _fixture_context(fixture)
    request = replace(request, **kwargs) if kwargs else request
    return build_unknown_execution_outcome_recovery_v1(
        reconciliation=reconciliation,
        idempotency=idempotency,
        request=request,
    )


def _assert_non_execution(payload: dict) -> None:
    for flag in _NON_EXEC_FLAGS:
        assert payload.get(flag) is False, flag
    assert payload.get("resubmit_allowed") is False
    assert payload.get("new_client_order_id_allowed") is False


def test_valid_unknown_outcome_contract(tmp_path, ssot_durable_output_dir) -> None:
    contract = _build(
        produce_unknown_execution_outcome_recovery_fixture(
            tmp_path, ssot_durable_output_dir, produce_output=False
        )
    )
    assert contract["contract_status"] == "UNKNOWN_EXECUTION_OUTCOME_RECOVERY_VALID"
    assert contract["recovery_classification"] == "FILLED"
    assert contract["contract_name"] == CONTRACT_NAME
    assert contract["contract_version"] == CONTRACT_VERSION
    assert contract["recovery_contract_version"] == RECOVERY_CONTRACT_VERSION


def test_deterministic_serialization(tmp_path, ssot_durable_output_dir) -> None:
    from src.meta.learning_loop.unknown_execution_outcome_recovery_v1 import (
        serialize_unknown_execution_outcome_recovery_v1,
    )

    contract = _build(
        produce_unknown_execution_outcome_recovery_fixture(
            tmp_path, ssot_durable_output_dir, produce_output=False
        )
    )
    serialized = serialize_unknown_execution_outcome_recovery_v1(contract)
    assert serialized == deterministic_json_dumps(contract)
    assert '"contract_name":"unknown_execution_outcome_recovery_v1"' in serialized


def test_identical_inputs_identical_digest(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_unknown_execution_outcome_recovery_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    reconciliation, idempotency, request = _fixture_context(fixture)
    first = build_unknown_execution_outcome_recovery_v1(
        reconciliation=reconciliation,
        idempotency=idempotency,
        request=request,
    )
    second = build_unknown_execution_outcome_recovery_v1(
        reconciliation=reconciliation,
        idempotency=idempotency,
        request=request,
    )
    assert first["output_digest"] == second["output_digest"]


def test_transport_timeout_no_resubmit(tmp_path, ssot_durable_output_dir) -> None:
    contract = _build(
        produce_unknown_execution_outcome_recovery_fixture(
            tmp_path, ssot_durable_output_dir, produce_output=False
        ),
        transport_outcome="TRANSPORT_TIMEOUT_AFTER_POSSIBLE_TRANSMISSION",
        unknown_outcome_reason="TRANSPORT_TIMEOUT_AFTER_POSSIBLE_TRANSMISSION",
        venue_acknowledgement_known=False,
    )
    assert contract["resubmit_allowed"] is False
    assert contract["transport_outcome"] == "TRANSPORT_TIMEOUT_AFTER_POSSIBLE_TRANSMISSION"


def test_transport_timeout_cannot_claim_not_submitted(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_unknown_execution_outcome_recovery_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    reconciliation, idempotency, request = _fixture_context(fixture)
    tampered = replace(request, transport_claims_not_submitted=True)
    contract = build_unknown_execution_outcome_recovery_v1(
        reconciliation=reconciliation,
        idempotency=idempotency,
        request=tampered,
    )
    assert contract["contract_status"] == "UNKNOWN_EXECUTION_OUTCOME_RECOVERY_INVALID"


def test_new_client_order_id_rejected(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_unknown_execution_outcome_recovery_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    reconciliation, idempotency, request = _fixture_context(fixture)
    tampered = replace(request, new_client_order_id_proposed=True)
    contract = build_unknown_execution_outcome_recovery_v1(
        reconciliation=reconciliation,
        idempotency=idempotency,
        request=tampered,
    )
    assert contract["contract_status"] == "UNKNOWN_EXECUTION_OUTCOME_RECOVERY_INVALID"
    assert contract["new_client_order_id_allowed"] is False


def test_missing_open_orders_snapshot_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_unknown_execution_outcome_recovery_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    reconciliation, idempotency, request = _fixture_context(fixture)
    tampered = replace(
        request,
        open_orders_snapshot=RecoverySnapshotBinding(snapshot_ref="", snapshot_digest=""),
    )
    contract = build_unknown_execution_outcome_recovery_v1(
        reconciliation=reconciliation,
        idempotency=idempotency,
        request=tampered,
    )
    assert contract["contract_status"] == "UNKNOWN_EXECUTION_OUTCOME_RECOVERY_MISSING_BINDINGS"


def test_missing_recent_orders_snapshot_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_unknown_execution_outcome_recovery_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    reconciliation, idempotency, request = _fixture_context(fixture)
    tampered = replace(
        request,
        recent_orders_snapshot=RecoverySnapshotBinding(snapshot_ref="", snapshot_digest=""),
    )
    contract = build_unknown_execution_outcome_recovery_v1(
        reconciliation=reconciliation,
        idempotency=idempotency,
        request=tampered,
    )
    assert contract["contract_status"] == "UNKNOWN_EXECUTION_OUTCOME_RECOVERY_MISSING_BINDINGS"


def test_missing_fill_snapshot_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_unknown_execution_outcome_recovery_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    reconciliation, idempotency, request = _fixture_context(fixture)
    tampered = replace(
        request,
        fill_snapshot=RecoverySnapshotBinding(snapshot_ref="", snapshot_digest=""),
    )
    contract = build_unknown_execution_outcome_recovery_v1(
        reconciliation=reconciliation,
        idempotency=idempotency,
        request=tampered,
    )
    assert contract["contract_status"] == "UNKNOWN_EXECUTION_OUTCOME_RECOVERY_MISSING_BINDINGS"


def test_missing_position_snapshot_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_unknown_execution_outcome_recovery_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    reconciliation, idempotency, request = _fixture_context(fixture)
    tampered = replace(
        request,
        position_snapshot=RecoverySnapshotBinding(snapshot_ref="", snapshot_digest=""),
    )
    contract = build_unknown_execution_outcome_recovery_v1(
        reconciliation=reconciliation,
        idempotency=idempotency,
        request=tampered,
    )
    assert contract["contract_status"] == "UNKNOWN_EXECUTION_OUTCOME_RECOVERY_MISSING_BINDINGS"


def test_missing_margin_snapshot_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_unknown_execution_outcome_recovery_fixture(
        tmp_path,
        ssot_durable_output_dir,
        produce_output=False,
        margin_snapshot_required=True,
        recovery_classification="FILLED",
    )
    reconciliation, idempotency, _ = _fixture_context(fixture)
    request = default_unknown_execution_recovery_request(
        reconciliation=reconciliation,
        idempotency=idempotency,
        recovery_classification="FILLED",
        margin_snapshot_required=True,
    )
    tampered = replace(request, margin_snapshot=None)
    contract = build_unknown_execution_outcome_recovery_v1(
        reconciliation=reconciliation,
        idempotency=idempotency,
        request=tampered,
    )
    assert contract["contract_status"] == "UNKNOWN_EXECUTION_OUTCOME_RECOVERY_MISSING_BINDINGS"


def test_tampered_snapshot_digest_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_unknown_execution_outcome_recovery_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    reconciliation, idempotency, request = _fixture_context(fixture)
    tampered = replace(
        request,
        fill_snapshot=RecoverySnapshotBinding(
            snapshot_ref=request.fill_snapshot.snapshot_ref,
            snapshot_digest="tampered",
        ),
        declared_recovery_classification="STILL_UNKNOWN",
        evidence_signals=RecoveryEvidenceSignals(
            open_orders_classification="FILLED",
            recent_orders_classification="STILL_UNKNOWN",
            fill_classification="FILLED",
            position_classification="FILLED",
        ),
    )
    contract = build_unknown_execution_outcome_recovery_v1(
        reconciliation=reconciliation,
        idempotency=idempotency,
        request=tampered,
    )
    assert contract["contract_status"] == "UNKNOWN_EXECUTION_OUTCOME_RECOVERY_STILL_UNKNOWN"


def test_tampered_intent_digest_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_unknown_execution_outcome_recovery_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    reconciliation, idempotency, request = _fixture_context(fixture)
    tampered = replace(request, order_intent_digest="tampered")
    contract = build_unknown_execution_outcome_recovery_v1(
        reconciliation=reconciliation,
        idempotency=idempotency,
        request=tampered,
    )
    assert contract["contract_status"] == "UNKNOWN_EXECUTION_OUTCOME_RECOVERY_DIGEST_MISMATCH"


def test_tampered_submission_attempt_digest_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_unknown_execution_outcome_recovery_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    reconciliation, idempotency, request = _fixture_context(fixture)
    tampered = replace(request, submission_attempt_digest="tampered")
    contract = build_unknown_execution_outcome_recovery_v1(
        reconciliation=reconciliation,
        idempotency=idempotency,
        request=tampered,
    )
    assert contract["contract_status"] == "UNKNOWN_EXECUTION_OUTCOME_RECOVERY_DIGEST_MISMATCH"


def test_client_order_id_mismatch_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_unknown_execution_outcome_recovery_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    reconciliation, idempotency, request = _fixture_context(fixture)
    tampered = replace(request, client_order_id="mismatched-client-order-id")
    contract = build_unknown_execution_outcome_recovery_v1(
        reconciliation=reconciliation,
        idempotency=idempotency,
        request=tampered,
    )
    assert (
        contract["contract_status"] == "UNKNOWN_EXECUTION_OUTCOME_RECOVERY_CLIENT_ORDER_ID_MISMATCH"
    )


def test_trading_epoch_mismatch_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_unknown_execution_outcome_recovery_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    reconciliation, idempotency, request = _fixture_context(fixture)
    tampered = replace(request, trading_epoch="epoch-mismatch")
    contract = build_unknown_execution_outcome_recovery_v1(
        reconciliation=reconciliation,
        idempotency=idempotency,
        request=tampered,
    )
    assert contract["contract_status"] == "UNKNOWN_EXECUTION_OUTCOME_RECOVERY_EPOCH_MISMATCH"


def test_executor_epoch_mismatch_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_unknown_execution_outcome_recovery_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    reconciliation, idempotency, request = _fixture_context(fixture)
    tampered = replace(request, executor_epoch="executor-epoch-mismatch")
    contract = build_unknown_execution_outcome_recovery_v1(
        reconciliation=reconciliation,
        idempotency=idempotency,
        request=tampered,
    )
    assert contract["contract_status"] == "UNKNOWN_EXECUTION_OUTCOME_RECOVERY_EPOCH_MISMATCH"


def test_contradictory_snapshot_evidence_still_unknown(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_unknown_execution_outcome_recovery_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    reconciliation, idempotency, request = _fixture_context(fixture)
    tampered = replace(
        request,
        declared_recovery_classification="STILL_UNKNOWN",
        evidence_signals=RecoveryEvidenceSignals(
            open_orders_classification="FILLED",
            recent_orders_classification="CANCELLED",
            fill_classification="FILLED",
            position_classification="FILLED",
        ),
    )
    contract = build_unknown_execution_outcome_recovery_v1(
        reconciliation=reconciliation,
        idempotency=idempotency,
        request=tampered,
    )
    assert contract["recovery_classification"] == "STILL_UNKNOWN"
    assert contract["reconciliation_required"] is True


def test_terminal_evidence_allows_matching_classification(
    tmp_path, ssot_durable_output_dir
) -> None:
    contract = _build(
        produce_unknown_execution_outcome_recovery_fixture(
            tmp_path,
            ssot_durable_output_dir,
            produce_output=False,
            recovery_classification="CANCELLED",
        ),
        declared_recovery_classification="CANCELLED",
        evidence_signals=RecoveryEvidenceSignals(
            open_orders_classification="CANCELLED",
            recent_orders_classification="CANCELLED",
            fill_classification="CANCELLED",
            position_classification="CANCELLED",
        ),
    )
    assert contract["contract_status"] == "UNKNOWN_EXECUTION_OUTCOME_RECOVERY_VALID"
    assert contract["recovery_classification"] == "CANCELLED"


def test_not_found_with_negative_evidence(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_unknown_execution_outcome_recovery_fixture(
        tmp_path,
        ssot_durable_output_dir,
        produce_output=False,
        recovery_classification="NOT_FOUND_WITH_SUFFICIENT_NEGATIVE_EVIDENCE",
    )
    reconciliation, idempotency, _ = _fixture_context(fixture)
    request = default_unknown_execution_recovery_request(
        reconciliation=reconciliation,
        idempotency=idempotency,
        recovery_classification="NOT_FOUND_WITH_SUFFICIENT_NEGATIVE_EVIDENCE",
    )
    contract = build_unknown_execution_outcome_recovery_v1(
        reconciliation=reconciliation,
        idempotency=idempotency,
        request=request,
    )
    assert contract["recovery_classification"] == "NOT_FOUND_WITH_SUFFICIENT_NEGATIVE_EVIDENCE"


def test_no_adapter_network_or_runtime_mutation(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_unknown_execution_outcome_recovery_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.unknown_execution_outcome_recovery_bundle_dir / ARTIFACT_REL)
    _assert_non_execution(payload)


def test_futures_market_type_accepted(tmp_path, ssot_durable_output_dir) -> None:
    contract = _build(
        produce_unknown_execution_outcome_recovery_fixture(
            tmp_path, ssot_durable_output_dir, produce_output=False, instrument_type="FUTURES"
        )
    )
    assert contract["instrument_type"] == "FUTURES"
    assert contract["contract_status"] == "UNKNOWN_EXECUTION_OUTCOME_RECOVERY_VALID"


def test_spot_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    contract = _build(
        produce_unknown_execution_outcome_recovery_fixture(
            tmp_path, ssot_durable_output_dir, produce_output=False, instrument_type="SPOT"
        ),
        instrument_type="SPOT",
    )
    assert (
        contract["contract_status"]
        == "UNKNOWN_EXECUTION_OUTCOME_RECOVERY_FUTURES_MARKET_TYPE_CONFLICT"
    )


def test_synthetic_spot_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    contract = _build(
        produce_unknown_execution_outcome_recovery_fixture(
            tmp_path,
            ssot_durable_output_dir,
            produce_output=False,
            instrument_type="SYNTHETIC_SPOT",
        ),
        instrument_type="SYNTHETIC_SPOT",
    )
    assert (
        contract["contract_status"]
        == "UNKNOWN_EXECUTION_OUTCOME_RECOVERY_FUTURES_MARKET_TYPE_CONFLICT"
    )


def test_unknown_market_type_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    contract = _build(
        produce_unknown_execution_outcome_recovery_fixture(
            tmp_path,
            ssot_durable_output_dir,
            produce_output=False,
            instrument_type="UNKNOWN_MARKET",
        ),
        instrument_type="UNKNOWN_MARKET",
    )
    assert (
        contract["contract_status"]
        == "UNKNOWN_EXECUTION_OUTCOME_RECOVERY_FUTURES_MARKET_TYPE_CONFLICT"
    )


def test_missing_market_type_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    contract = _build(
        produce_unknown_execution_outcome_recovery_fixture(
            tmp_path, ssot_durable_output_dir, produce_output=False, instrument_type=""
        ),
        instrument_type="",
    )
    assert (
        contract["contract_status"]
        == "UNKNOWN_EXECUTION_OUTCOME_RECOVERY_FUTURES_MARKET_TYPE_CONFLICT"
    )


def test_replay_produces_identical_artifact(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_unknown_execution_outcome_recovery_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    reconciliation, idempotency, request = _fixture_context(fixture)
    inputs = UnknownExecutionRecoveryInputs(
        runtime_state_reconciliation_bundle_dir=fixture.runtime_state_reconciliation_bundle_dir,
        order_intent_idempotency_bundle_dir=fixture.order_intent_idempotency_bundle_dir,
        recovery_request=request,
    )
    out_a = _durable_output(tmp_path, "a")
    out_b = _durable_output(tmp_path, "b")
    produce_unknown_execution_outcome_recovery_v1(inputs=inputs, output_dir=out_a)
    produce_unknown_execution_outcome_recovery_v1(inputs=inputs, output_dir=out_b)
    assert (out_a / ARTIFACT_REL).read_text() == (out_b / ARTIFACT_REL).read_text()


def test_manifest_and_self_verification(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_unknown_execution_outcome_recovery_fixture(tmp_path, ssot_durable_output_dir)
    out = fixture.unknown_execution_outcome_recovery_bundle_dir
    ok, msg = verify_manifest_sha256(out)
    assert ok, msg
    reverify_unknown_execution_outcome_recovery_v1(output_dir=out)


def test_authority_invariants(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_unknown_execution_outcome_recovery_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.unknown_execution_outcome_recovery_bundle_dir / ARTIFACT_REL)
    assert (
        payload["unknown_execution_outcome_recovery_authority_invariants"]
        == UNKNOWN_EXECUTION_OUTCOME_RECOVERY_AUTHORITY_INVARIANTS
    )
    _assert_non_execution(payload)


def test_stable_digest_tamper_on_reverify(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_unknown_execution_outcome_recovery_fixture(tmp_path, ssot_durable_output_dir)
    out = fixture.unknown_execution_outcome_recovery_bundle_dir
    artifact_path = out / ARTIFACT_REL
    artifact_path.write_text(
        artifact_path.read_text().replace("FILLED", "TAMPERED"),
        encoding="utf-8",
    )
    with pytest.raises(Exception):
        reverify_unknown_execution_outcome_recovery_v1(output_dir=out)


def test_step18_regression_still_passes(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_unknown_execution_outcome_recovery_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    payload = read_manifest(
        fixture.runtime_state_reconciliation_bundle_dir / "runtime_state_reconciliation_v1.json"
    )
    assert payload["contract_status"] == "RUNTIME_STATE_RECONCILIATION_VALID"
