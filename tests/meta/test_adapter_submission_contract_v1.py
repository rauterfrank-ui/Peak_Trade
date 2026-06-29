"""Contract tests for adapter_submission_contract_v1."""

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
    "tests.meta.adapter_submission_contract_v1_fixtures",
]

from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256
from src.meta.learning_loop.adapter_submission_contract_v1 import (
    ARTIFACT_REL,
    ADAPTER_SUBMISSION_AUTHORITY_INVARIANTS,
    AdapterSubmissionInputs,
    build_adapter_submission_contract_v1,
    build_normalized_adapter_payload_v1,
    default_adapter_submission_request,
    produce_adapter_submission_contract_v1,
    reverify_adapter_submission_contract_v1,
    serialize_adapter_submission_contract_v1,
    verify_order_intent_idempotency_bundle,
    verify_runtime_state_reconciliation_bundle,
    verify_trading_core_decision_attestation_bundle,
)
from src.meta.learning_loop.comparison_metric_input_v1.io import read_manifest
from src.meta.learning_loop.contract_safety_v1 import deterministic_json_dumps
from tests.meta.adapter_submission_contract_v1_fixtures import (
    produce_adapter_submission_contract_fixture,
)

_NON_EXEC_FLAGS = (
    "adapter_invoked",
    "exchange_request_sent",
    "network_side_effect_created",
    "order_submission_requested",
    "order_submitted",
    "order_created",
    "permission_consumed",
    "submission_claim_consumed",
    "runtime_state_mutated",
    "position_state_mutated",
    "authority_activated",
    "lease_activated",
    "live_authorized",
    "orders_allowed",
    "scheduler_runtime_allowed",
    "adapter_may_submit_order",
    "adapter_may_amend_order",
    "adapter_may_cancel_order",
    "adapter_may_mutate_runtime_state",
)


@pytest.fixture(autouse=True)
def _allow_tmp_output(monkeypatch: pytest.MonkeyPatch) -> None:
    targets = (
        "src.meta.learning_loop.adapter_submission_contract_v1.is_under_tmp",
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


def _durable_output(tmp_path: Path, name: str = "adapter_out") -> Path:
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
    attestation = verify_trading_core_decision_attestation_bundle(
        fixture.trading_core_decision_attestation_bundle_dir
    )
    request = default_adapter_submission_request(
        idempotency=idempotency,
        reconciliation=reconciliation,
        attestation=attestation,
    )
    return reconciliation, idempotency, attestation, request


def _build(fixture, **kwargs):
    reconciliation, idempotency, attestation, request = _fixture_context(fixture)
    request = replace(request, **kwargs) if kwargs else request
    return build_adapter_submission_contract_v1(
        reconciliation=reconciliation,
        idempotency=idempotency,
        attestation=attestation,
        request=request,
    )


def _factor_ids(contract: dict) -> set[str]:
    factor_ids: set[str] = set()
    for field in ("blocking_facts", "missing_preconditions", "contradictions"):
        for item in contract.get(field, []):
            if isinstance(item, dict):
                factor_id = item.get("factor_id")
                if factor_id:
                    factor_ids.add(str(factor_id))
    return factor_ids


def _assert_non_execution(payload: dict) -> None:
    for flag in _NON_EXEC_FLAGS:
        assert payload.get(flag) is False, flag


def test_valid_submission_contract(tmp_path, ssot_durable_output_dir) -> None:
    contract = _build(
        produce_adapter_submission_contract_fixture(
            tmp_path, ssot_durable_output_dir, produce_output=False
        )
    )
    assert contract["contract_status"] == "ADAPTER_SUBMISSION_CONTRACT_VALID"
    assert contract["evidence_status"] == "VALID"


def test_valid_semantic_neutral_normalization(tmp_path, ssot_durable_output_dir) -> None:
    contract = _build(
        produce_adapter_submission_contract_fixture(
            tmp_path, ssot_durable_output_dir, produce_output=False
        )
    )
    normalized = build_normalized_adapter_payload_v1(contract=contract)
    assert normalized is not None
    assert normalized["semantic_equivalence_verified"] is True
    assert normalized["quantity_increased"] is False
    assert normalized["order_type_changed"] is False
    assert normalized["runtime_mutation_performed"] is False


def test_deterministic_serialization(tmp_path, ssot_durable_output_dir) -> None:
    contract = _build(
        produce_adapter_submission_contract_fixture(
            tmp_path, ssot_durable_output_dir, produce_output=False
        )
    )
    serialized = serialize_adapter_submission_contract_v1(contract)
    assert serialized == deterministic_json_dumps(contract)
    assert '"contract_name":"adapter_submission_contract_v1"' in serialized


def test_identical_inputs_identical_digest(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_adapter_submission_contract_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    reconciliation, idempotency, attestation, request = _fixture_context(fixture)
    first = build_adapter_submission_contract_v1(
        reconciliation=reconciliation,
        idempotency=idempotency,
        attestation=attestation,
        request=request,
    )
    second = build_adapter_submission_contract_v1(
        reconciliation=reconciliation,
        idempotency=idempotency,
        attestation=attestation,
        request=request,
    )
    assert first["output_digest"] == second["output_digest"]


def test_missing_canonical_order_intent_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    contract = _build(
        produce_adapter_submission_contract_fixture(
            tmp_path, ssot_durable_output_dir, produce_output=False
        ),
        canonical_order_intent_digest="",
    )
    assert contract["contract_status"] == "ADAPTER_SUBMISSION_CONTRACT_MISSING_BINDINGS"


def test_tampered_intent_digest_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    contract = _build(
        produce_adapter_submission_contract_fixture(
            tmp_path, ssot_durable_output_dir, produce_output=False
        ),
        canonical_order_intent_digest="tampered-intent-digest",
    )
    assert contract["contract_status"] != "ADAPTER_SUBMISSION_CONTRACT_VALID"
    assert "CANONICAL_ORDER_INTENT_DIGEST_MISMATCH" in _factor_ids(contract)


def test_missing_execution_permission_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    contract = _build(
        produce_adapter_submission_contract_fixture(
            tmp_path, ssot_durable_output_dir, produce_output=False
        ),
        execution_permission_digest="",
    )
    assert contract["contract_status"] == "ADAPTER_SUBMISSION_CONTRACT_MISSING_BINDINGS"


def test_tampered_permission_digest_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    contract = _build(
        produce_adapter_submission_contract_fixture(
            tmp_path, ssot_durable_output_dir, produce_output=False
        ),
        execution_permission_digest="tampered-permission-digest",
    )
    assert contract["contract_status"] != "ADAPTER_SUBMISSION_CONTRACT_VALID"


def test_expired_permission_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    contract = _build(
        produce_adapter_submission_contract_fixture(
            tmp_path, ssot_durable_output_dir, produce_output=False
        ),
        execution_permission_expires_at="1970-01-01T00:00:00+00:00",
    )
    assert contract["contract_status"] == "ADAPTER_SUBMISSION_CONTRACT_PERMISSION_EXPIRED"


def test_permission_not_single_use_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    contract = _build(
        produce_adapter_submission_contract_fixture(
            tmp_path, ssot_durable_output_dir, produce_output=False
        ),
        execution_permission_single_use=False,
    )
    assert contract["contract_status"] == "ADAPTER_SUBMISSION_CONTRACT_BLOCKED"
    assert "PERMISSION_NOT_SINGLE_USE" in _factor_ids(contract)


def test_missing_submission_claim_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    contract = _build(
        produce_adapter_submission_contract_fixture(
            tmp_path, ssot_durable_output_dir, produce_output=False
        ),
        submission_claim_digest="",
    )
    assert contract["contract_status"] == "ADAPTER_SUBMISSION_CONTRACT_MISSING_BINDINGS"


def test_tampered_claim_digest_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    contract = _build(
        produce_adapter_submission_contract_fixture(
            tmp_path, ssot_durable_output_dir, produce_output=False
        ),
        submission_claim_digest="tampered-claim-digest",
    )
    assert contract["contract_status"] != "ADAPTER_SUBMISSION_CONTRACT_VALID"


def test_invalid_authority_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    contract = _build(
        produce_adapter_submission_contract_fixture(
            tmp_path, ssot_durable_output_dir, produce_output=False
        ),
        authority_active=False,
    )
    assert contract["contract_status"] == "ADAPTER_SUBMISSION_CONTRACT_BLOCKED"
    assert "AUTHORITY_INACTIVE" in _factor_ids(contract)


def test_revocation_epoch_mismatch_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    contract = _build(
        produce_adapter_submission_contract_fixture(
            tmp_path, ssot_durable_output_dir, produce_output=False
        ),
        revocation_epoch="revocation-epoch-mismatch",
    )
    assert contract["contract_status"] == "ADAPTER_SUBMISSION_CONTRACT_EPOCH_MISMATCH"


def test_trading_epoch_mismatch_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    contract = _build(
        produce_adapter_submission_contract_fixture(
            tmp_path, ssot_durable_output_dir, produce_output=False
        ),
        trading_epoch="trading-epoch-mismatch",
    )
    assert contract["contract_status"] == "ADAPTER_SUBMISSION_CONTRACT_EPOCH_MISMATCH"


def test_executor_epoch_mismatch_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    contract = _build(
        produce_adapter_submission_contract_fixture(
            tmp_path, ssot_durable_output_dir, produce_output=False
        ),
        executor_epoch="executor-epoch-mismatch",
    )
    assert contract["contract_status"] == "ADAPTER_SUBMISSION_CONTRACT_EPOCH_MISMATCH"


def test_kill_switch_not_armed_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    contract = _build(
        produce_adapter_submission_contract_fixture(
            tmp_path, ssot_durable_output_dir, produce_output=False
        ),
        kill_switch_state="DISARMED",
    )
    assert contract["contract_status"] == "ADAPTER_SUBMISSION_CONTRACT_KILL_SWITCH_BLOCKED"


def test_kill_switch_stale_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    contract = _build(
        produce_adapter_submission_contract_fixture(
            tmp_path, ssot_durable_output_dir, produce_output=False
        ),
        kill_switch_is_fresh=False,
    )
    assert contract["contract_status"] == "ADAPTER_SUBMISSION_CONTRACT_KILL_SWITCH_BLOCKED"


def test_reconciliation_not_clean_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    contract = _build(
        produce_adapter_submission_contract_fixture(
            tmp_path, ssot_durable_output_dir, produce_output=False
        ),
        reconciliation_state="DIRTY",
    )
    assert contract["contract_status"] == "ADAPTER_SUBMISSION_CONTRACT_RECONCILIATION_BLOCKED"


def test_venue_binding_mismatch_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    contract = _build(
        produce_adapter_submission_contract_fixture(
            tmp_path, ssot_durable_output_dir, produce_output=False
        ),
        venue="GENERIC-FUTURES-VENUE-MISMATCH",
    )
    assert contract["contract_status"] == "ADAPTER_SUBMISSION_CONTRACT_BLOCKED"
    assert "VENUE_BINDING_MISMATCH" in _factor_ids(contract)


def test_account_binding_mismatch_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    contract = _build(
        produce_adapter_submission_contract_fixture(
            tmp_path, ssot_durable_output_dir, produce_output=False
        ),
        account_scope="GENERIC-FUTURES-ACCOUNT-MISMATCH",
    )
    assert contract["contract_status"] == "ADAPTER_SUBMISSION_CONTRACT_BLOCKED"
    assert "ACCOUNT_SCOPE_BINDING_MISMATCH" in _factor_ids(contract)


def test_instrument_binding_mismatch_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    contract = _build(
        produce_adapter_submission_contract_fixture(
            tmp_path, ssot_durable_output_dir, produce_output=False
        ),
        instrument="GENERIC-FUTURES-INSTRUMENT-MISMATCH",
    )
    assert contract["contract_status"] == "ADAPTER_SUBMISSION_CONTRACT_BLOCKED"
    assert "INSTRUMENT_BINDING_MISMATCH" in _factor_ids(contract)


def test_spot_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    contract = _build(
        produce_adapter_submission_contract_fixture(
            tmp_path,
            ssot_durable_output_dir,
            produce_output=False,
        ),
        market_type="SPOT",
    )
    assert contract["contract_status"] == "ADAPTER_SUBMISSION_CONTRACT_MARKET_TYPE_BLOCKED"


def test_synthetic_spot_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    contract = _build(
        produce_adapter_submission_contract_fixture(
            tmp_path,
            ssot_durable_output_dir,
            produce_output=False,
        ),
        market_type="SYNTHETIC_SPOT",
    )
    assert contract["contract_status"] == "ADAPTER_SUBMISSION_CONTRACT_MARKET_TYPE_BLOCKED"


def test_unknown_market_type_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    contract = _build(
        produce_adapter_submission_contract_fixture(
            tmp_path, ssot_durable_output_dir, produce_output=False
        ),
        market_type="UNKNOWN_MARKET",
    )
    assert contract["contract_status"] == "ADAPTER_SUBMISSION_CONTRACT_MARKET_TYPE_BLOCKED"


def test_missing_market_type_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    contract = _build(
        produce_adapter_submission_contract_fixture(
            tmp_path, ssot_durable_output_dir, produce_output=False
        ),
        market_type="",
    )
    assert contract["contract_status"] != "ADAPTER_SUBMISSION_CONTRACT_VALID"


def test_client_order_id_change_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    contract = _build(
        produce_adapter_submission_contract_fixture(
            tmp_path, ssot_durable_output_dir, produce_output=False
        ),
        client_order_id="generic-futures-client-order-mismatch",
    )
    assert contract["contract_status"] == "ADAPTER_SUBMISSION_CONTRACT_BLOCKED"
    assert "CLIENT_ORDER_ID_MISMATCH" in _factor_ids(contract)


def test_quantity_round_up_fail_closed(
    tmp_path, ssot_durable_output_dir, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "src.meta.learning_loop.adapter_submission_contract_v1._normalize_quantity",
        lambda _quantity: ("2", True),
    )
    contract = _build(
        produce_adapter_submission_contract_fixture(
            tmp_path, ssot_durable_output_dir, produce_output=False
        ),
        quantity="1.0000",
    )
    assert contract["contract_status"] == "ADAPTER_SUBMISSION_CONTRACT_SEMANTIC_MUTATION_BLOCKED"


def test_quantity_over_approved_fail_closed(
    tmp_path, ssot_durable_output_dir, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "src.meta.learning_loop.adapter_submission_contract_v1._normalize_quantity",
        lambda _quantity: ("100.0001", True),
    )
    contract = _build(
        produce_adapter_submission_contract_fixture(
            tmp_path, ssot_durable_output_dir, produce_output=False
        ),
        quantity="100.0000",
    )
    assert contract["contract_status"] == "ADAPTER_SUBMISSION_CONTRACT_SEMANTIC_MUTATION_BLOCKED"


def test_order_type_change_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    contract = _build(
        produce_adapter_submission_contract_fixture(
            tmp_path, ssot_durable_output_dir, produce_output=False
        ),
        order_type="POST_ONLY",
    )
    assert contract["contract_status"] == "ADAPTER_SUBMISSION_CONTRACT_BLOCKED"
    assert "INVALID_ORDER_TYPE" in _factor_ids(contract)


@pytest.mark.skip(reason="reduce_only/position_mode drift is not enforced in v1 yet")
def test_reduce_only_removal(tmp_path, ssot_durable_output_dir) -> None:
    _build(
        produce_adapter_submission_contract_fixture(
            tmp_path, ssot_durable_output_dir, produce_output=False
        ),
        reduce_only=False,
        position_mode="HEDGE",
    )


def test_unknown_outcome_retry_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    contract = _build(
        produce_adapter_submission_contract_fixture(
            tmp_path, ssot_durable_output_dir, produce_output=False
        ),
        unknown_outcome_retry_requested=True,
    )
    assert contract["contract_status"] == "ADAPTER_SUBMISSION_CONTRACT_BLOCKED"
    assert "UNKNOWN_OUTCOME_RETRY_REQUESTED" in _factor_ids(contract)


def test_permission_already_consumed_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    contract = _build(
        produce_adapter_submission_contract_fixture(
            tmp_path, ssot_durable_output_dir, produce_output=False
        ),
        permission_consumed=True,
    )
    assert contract["contract_status"] == "ADAPTER_SUBMISSION_CONTRACT_BLOCKED"
    assert "PERMISSION_ALREADY_CONSUMED" in _factor_ids(contract)


def test_submission_already_started_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    contract = _build(
        produce_adapter_submission_contract_fixture(
            tmp_path, ssot_durable_output_dir, produce_output=False
        ),
        submission_started_or_consumed=True,
    )
    assert contract["contract_status"] == "ADAPTER_SUBMISSION_CONTRACT_BLOCKED"
    assert "SUBMISSION_ALREADY_STARTED_OR_CONSUMED" in _factor_ids(contract)


def test_no_adapter_network_or_runtime_mutation(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_adapter_submission_contract_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.adapter_submission_contract_bundle_dir / ARTIFACT_REL)
    _assert_non_execution(payload)


def test_futures_market_type_accepted(tmp_path, ssot_durable_output_dir) -> None:
    contract = _build(
        produce_adapter_submission_contract_fixture(
            tmp_path,
            ssot_durable_output_dir,
            produce_output=False,
            instrument_type="FUTURES",
        ),
        market_type="FUTURES",
    )
    assert contract["market_type"] == "FUTURES"
    assert contract["contract_status"] == "ADAPTER_SUBMISSION_CONTRACT_VALID"


def test_replay_produces_identical_artifact(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_adapter_submission_contract_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    reconciliation, idempotency, attestation, request = _fixture_context(fixture)
    inputs = AdapterSubmissionInputs(
        runtime_state_reconciliation_bundle_dir=fixture.runtime_state_reconciliation_bundle_dir,
        order_intent_idempotency_bundle_dir=fixture.order_intent_idempotency_bundle_dir,
        trading_core_decision_attestation_bundle_dir=fixture.trading_core_decision_attestation_bundle_dir,
        request=request,
    )
    out_a = _durable_output(tmp_path, "a")
    out_b = _durable_output(tmp_path, "b")
    produce_adapter_submission_contract_v1(inputs=inputs, output_dir=out_a)
    produce_adapter_submission_contract_v1(inputs=inputs, output_dir=out_b)
    assert (out_a / ARTIFACT_REL).read_text() == (out_b / ARTIFACT_REL).read_text()


def test_manifest_and_self_verification(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_adapter_submission_contract_fixture(tmp_path, ssot_durable_output_dir)
    out = fixture.adapter_submission_contract_bundle_dir
    ok, msg = verify_manifest_sha256(out)
    assert ok, msg
    reverify_adapter_submission_contract_v1(output_dir=out)


def test_authority_invariants(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_adapter_submission_contract_fixture(tmp_path, ssot_durable_output_dir)
    payload = read_manifest(fixture.adapter_submission_contract_bundle_dir / ARTIFACT_REL)
    assert (
        payload["adapter_submission_authority_invariants"]
        == ADAPTER_SUBMISSION_AUTHORITY_INVARIANTS
    )
    _assert_non_execution(payload)
