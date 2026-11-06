"""Contract tests for independent_pre_trade_safety_kernel_v1."""

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
    "tests.meta.venue_capability_snapshot_v1_fixtures",
    "tests.meta.independent_pre_trade_safety_kernel_v1_fixtures",
]

from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256
from src.meta.learning_loop.comparison_metric_input_v1.io import read_manifest
from src.meta.learning_loop.contract_safety_v1 import deterministic_json_dumps
from src.meta.learning_loop.independent_pre_trade_safety_kernel_v1 import (
    ARTIFACT_REL,
    INDEPENDENT_PRE_TRADE_SAFETY_KERNEL_AUTHORITY_INVARIANTS,
    IndependentPreTradeSafetyKernelInputs,
    InlineSnapshotBinding,
    build_default_kill_switch_snapshot_body,
    build_default_margin_snapshot_body,
    build_default_market_data_snapshot_body,
    build_default_open_orders_snapshot_body,
    build_default_position_snapshot_body,
    build_default_risk_snapshot_body,
    build_independent_pre_trade_safety_kernel_v1,
    default_pre_trade_safety_evaluation_request,
    produce_independent_pre_trade_safety_kernel_v1,
    reverify_independent_pre_trade_safety_kernel_v1,
    serialize_independent_pre_trade_safety_kernel_v1,
    verify_authority_lease_bundle,
    verify_clock_trust_and_expiry_bundle,
    verify_order_intent_idempotency_bundle,
    verify_runtime_state_reconciliation_bundle,
    verify_trading_core_decision_attestation_bundle,
    verify_venue_capability_snapshot_bundle,
)
from src.meta.learning_loop.independent_pre_trade_safety_kernel_v1 import (
    _inline_binding_from_body,
    _trading_session_from_attestation,
)
from tests.meta.independent_pre_trade_safety_kernel_v1_fixtures import (
    produce_independent_pre_trade_safety_kernel_fixture,
)

_NON_EXEC_FLAGS = (
    "single_use_permission_created",
    "submission_authorized",
    "runtime_mutation_performed",
    "order_action_performed",
    "adapter_invoked",
    "exchange_request_sent",
    "network_side_effect_created",
    "execution_permission_created",
    "execution_permission_consumed",
    "order_created",
    "order_submission_requested",
    "order_submitted",
    "order_cancel_requested",
    "order_amend_requested",
    "order_state_mutated",
    "position_state_mutated",
    "runtime_state_mutated",
    "venue_capability_discovery_executed",
    "venue_capability_refresh_executed",
    "files_transferred_to_runtime",
    "queue_message_created",
    "database_mutated",
    "lock_acquired",
    "reservation_created",
    "authority_activated",
    "lease_activated",
    "revocation_executed",
    "reconciliation_executed",
    "scheduler_started",
    "live_authorized",
    "orders_allowed",
    "scheduler_runtime_allowed",
)


@pytest.fixture(autouse=True)
def _allow_tmp_output(monkeypatch: pytest.MonkeyPatch) -> None:
    targets = (
        "src.meta.learning_loop.independent_pre_trade_safety_kernel_v1.is_under_tmp",
        "src.meta.learning_loop.venue_capability_snapshot_v1.is_under_tmp",
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


def _durable_output(tmp_path: Path, name: str = "safety_kernel_out") -> Path:
    root = tmp_path / "evidence_root"
    root.mkdir(exist_ok=True)
    return root / name


def _rebind(body: dict, ref: str, domain: str) -> InlineSnapshotBinding:
    return _inline_binding_from_body(ref=ref, domain=domain, body=body)


def _fixture_context(fixture):
    idempotency = verify_order_intent_idempotency_bundle(
        fixture.order_intent_idempotency_bundle_dir
    )
    reconciliation = verify_runtime_state_reconciliation_bundle(
        fixture.runtime_state_reconciliation_bundle_dir
    )
    attestation = verify_trading_core_decision_attestation_bundle(
        fixture.trading_core_decision_attestation_bundle_dir
    )
    venue_capability = verify_venue_capability_snapshot_bundle(
        fixture.venue_capability_snapshot_bundle_dir
    )
    authority_lease = verify_authority_lease_bundle(fixture.authority_lease_bundle_dir)
    clock_trust = verify_clock_trust_and_expiry_bundle(fixture.clock_trust_and_expiry_bundle_dir)
    trading_session = _trading_session_from_attestation(attestation)
    request = default_pre_trade_safety_evaluation_request(
        idempotency=idempotency,
        reconciliation=reconciliation,
        attestation=attestation,
        venue_capability=venue_capability,
        authority_lease=authority_lease,
        clock_trust=clock_trust,
    )
    return (
        idempotency,
        reconciliation,
        attestation,
        venue_capability,
        authority_lease,
        clock_trust,
        trading_session,
        request,
    )


def _build(fixture, *, reconciliation=None, **kwargs):
    (
        idempotency,
        reconciliation_bundle,
        attestation,
        venue_capability,
        authority_lease,
        clock_trust,
        trading_session,
        request,
    ) = _fixture_context(fixture)
    request = replace(request, **kwargs) if kwargs else request
    return build_independent_pre_trade_safety_kernel_v1(
        request=request,
        idempotency=idempotency,
        reconciliation=reconciliation or reconciliation_bundle,
        attestation=attestation,
        venue_capability=venue_capability,
        authority_lease=authority_lease,
        clock_trust=clock_trust,
        trading_session=trading_session,
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


def _kill_switch_kwargs(*, state: str, revocation_epoch: str) -> dict[str, str]:
    body = build_default_kill_switch_snapshot_body(
        kill_switch_state=state,
        revocation_epoch=revocation_epoch,
    )
    binding = _rebind(body, state, "kill_switch_state_v1")
    return {
        "kill_switch_state_ref": state,
        "kill_switch_state_digest": binding.digest,
    }


def test_valid_approve_path(tmp_path, ssot_durable_output_dir) -> None:
    contract = _build(
        produce_independent_pre_trade_safety_kernel_fixture(
            tmp_path, ssot_durable_output_dir, produce_output=False
        )
    )
    assert contract["decision"] == "APPROVE"
    assert contract["contract_status"] == "INDEPENDENT_PRE_TRADE_SAFETY_KERNEL_APPROVED"
    assert contract["evidence_status"] == "VALID"


def test_deterministic_serialization(tmp_path, ssot_durable_output_dir) -> None:
    contract = _build(
        produce_independent_pre_trade_safety_kernel_fixture(
            tmp_path, ssot_durable_output_dir, produce_output=False
        )
    )
    serialized = serialize_independent_pre_trade_safety_kernel_v1(contract)
    assert serialized == deterministic_json_dumps(contract)
    assert '"contract_name":"independent_pre_trade_safety_kernel_v1"' in serialized


def test_identical_inputs_identical_digest(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_independent_pre_trade_safety_kernel_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    (
        idempotency,
        reconciliation,
        attestation,
        venue_capability,
        authority_lease,
        clock_trust,
        trading_session,
        request,
    ) = _fixture_context(fixture)
    first = build_independent_pre_trade_safety_kernel_v1(
        request=request,
        idempotency=idempotency,
        reconciliation=reconciliation,
        attestation=attestation,
        venue_capability=venue_capability,
        authority_lease=authority_lease,
        clock_trust=clock_trust,
        trading_session=trading_session,
    )
    second = build_independent_pre_trade_safety_kernel_v1(
        request=request,
        idempotency=idempotency,
        reconciliation=reconciliation,
        attestation=attestation,
        venue_capability=venue_capability,
        authority_lease=authority_lease,
        clock_trust=clock_trust,
        trading_session=trading_session,
    )
    assert first["output_digest"] == second["output_digest"]


def test_missing_canonical_order_intent_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    contract = _build(
        produce_independent_pre_trade_safety_kernel_fixture(
            tmp_path, ssot_durable_output_dir, produce_output=False
        ),
        canonical_order_intent_digest="",
    )
    assert contract["contract_status"] == "INDEPENDENT_PRE_TRADE_SAFETY_KERNEL_REJECTED"
    assert "MISSING_CANONICAL_ORDER_INTENT_DIGEST" in _factor_ids(contract)


def test_tampered_intent_digest_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    contract = _build(
        produce_independent_pre_trade_safety_kernel_fixture(
            tmp_path, ssot_durable_output_dir, produce_output=False
        ),
        canonical_order_intent_digest="tampered-intent-digest",
    )
    assert contract["contract_status"] == "INDEPENDENT_PRE_TRADE_SAFETY_KERNEL_REJECTED"
    assert "CANONICAL_ORDER_INTENT_DIGEST_MISMATCH" in _factor_ids(contract)


def test_missing_attestation_chain_digest_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    contract = _build(
        produce_independent_pre_trade_safety_kernel_fixture(
            tmp_path, ssot_durable_output_dir, produce_output=False
        ),
        trading_core_attestation_chain_digest="",
    )
    assert contract["contract_status"] == "INDEPENDENT_PRE_TRADE_SAFETY_KERNEL_REJECTED"
    assert "MISSING_TRADING_CORE_ATTESTATION_CHAIN_DIGEST" in _factor_ids(contract)


def test_tampered_attestation_chain_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    contract = _build(
        produce_independent_pre_trade_safety_kernel_fixture(
            tmp_path, ssot_durable_output_dir, produce_output=False
        ),
        trading_core_attestation_chain_digest="tampered-attestation-chain-digest",
    )
    assert contract["contract_status"] == "INDEPENDENT_PRE_TRADE_SAFETY_KERNEL_REJECTED"
    assert "ATTESTATION_CHAIN_DIGEST_MISMATCH" in _factor_ids(contract)


def test_missing_venue_capability_digest_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    contract = _build(
        produce_independent_pre_trade_safety_kernel_fixture(
            tmp_path, ssot_durable_output_dir, produce_output=False
        ),
        venue_capability_snapshot_digest="",
    )
    assert contract["contract_status"] == "INDEPENDENT_PRE_TRADE_SAFETY_KERNEL_REJECTED"
    assert "MISSING_VENUE_CAPABILITY_SNAPSHOT_DIGEST" in _factor_ids(contract)


def test_venue_capability_digest_mismatch_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    contract = _build(
        produce_independent_pre_trade_safety_kernel_fixture(
            tmp_path, ssot_durable_output_dir, produce_output=False
        ),
        venue_capability_snapshot_digest="tampered-venue-capability-digest",
    )
    assert contract["contract_status"] == "INDEPENDENT_PRE_TRADE_SAFETY_KERNEL_REJECTED"
    assert "VENUE_CAPABILITY_DIGEST_MISMATCH" in _factor_ids(contract)


def test_authority_expired_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    contract = _build(
        produce_independent_pre_trade_safety_kernel_fixture(
            tmp_path, ssot_durable_output_dir, produce_output=False
        ),
        evaluation_timestamp="2030-01-01T00:00:00+00:00",
    )
    assert contract["contract_status"] == "INDEPENDENT_PRE_TRADE_SAFETY_KERNEL_BLOCKED"
    assert "AUTHORITY_LEASE_EXPIRED" in _factor_ids(contract)


def test_revocation_epoch_mismatch_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    contract = _build(
        produce_independent_pre_trade_safety_kernel_fixture(
            tmp_path, ssot_durable_output_dir, produce_output=False
        ),
        revocation_epoch="revocation-epoch-mismatch",
    )
    assert contract["contract_status"] == "INDEPENDENT_PRE_TRADE_SAFETY_KERNEL_BLOCKED"
    assert "REVOCATION_EPOCH_MISMATCH" in _factor_ids(contract)


def test_trading_epoch_mismatch_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    contract = _build(
        produce_independent_pre_trade_safety_kernel_fixture(
            tmp_path, ssot_durable_output_dir, produce_output=False
        ),
        trading_epoch="trading-epoch-mismatch",
    )
    assert contract["contract_status"] == "INDEPENDENT_PRE_TRADE_SAFETY_KERNEL_BLOCKED"
    assert "TRADING_EPOCH_MISMATCH" in _factor_ids(contract)


def test_executor_epoch_mismatch_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    contract = _build(
        produce_independent_pre_trade_safety_kernel_fixture(
            tmp_path, ssot_durable_output_dir, produce_output=False
        ),
        executor_epoch="executor-epoch-mismatch",
    )
    assert contract["contract_status"] == "INDEPENDENT_PRE_TRADE_SAFETY_KERNEL_BLOCKED"
    assert "EXECUTOR_EPOCH_MISMATCH" in _factor_ids(contract)


def test_kill_switch_not_armed_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_independent_pre_trade_safety_kernel_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    idempotency = verify_order_intent_idempotency_bundle(
        fixture.order_intent_idempotency_bundle_dir
    )
    contract = _build(
        fixture,
        **_kill_switch_kwargs(
            state="DISARMED",
            revocation_epoch=idempotency.revocation_epoch,
        ),
    )
    assert contract["contract_status"] == "INDEPENDENT_PRE_TRADE_SAFETY_KERNEL_BLOCKED"
    assert "KILL_SWITCH_NOT_ARMED" in _factor_ids(contract)


def test_kill_switch_stale_fail_closed(
    tmp_path, ssot_durable_output_dir, monkeypatch: pytest.MonkeyPatch
) -> None:
    def _stale_kill_switch(**kwargs):
        body = build_default_kill_switch_snapshot_body(**kwargs)
        body["kill_switch_is_fresh"] = False
        return body

    monkeypatch.setattr(
        "src.meta.learning_loop.independent_pre_trade_safety_kernel_v1.build_default_kill_switch_snapshot_body",
        _stale_kill_switch,
    )
    contract = _build(
        produce_independent_pre_trade_safety_kernel_fixture(
            tmp_path, ssot_durable_output_dir, produce_output=False
        )
    )
    assert contract["contract_status"] == "INDEPENDENT_PRE_TRADE_SAFETY_KERNEL_BLOCKED"
    assert "KILL_SWITCH_NOT_FRESH" in _factor_ids(contract)


def test_reconciliation_not_clean_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_independent_pre_trade_safety_kernel_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    reconciliation = verify_runtime_state_reconciliation_bundle(
        fixture.runtime_state_reconciliation_bundle_dir
    )
    contract = _build(
        fixture,
        reconciliation=replace(reconciliation, reconciliation_state="UNCLEAN"),
    )
    assert contract["contract_status"] == "INDEPENDENT_PRE_TRADE_SAFETY_KERNEL_BLOCKED"
    assert "RECONCILIATION_NOT_CLEAN" in _factor_ids(contract)


def test_market_data_stale_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_independent_pre_trade_safety_kernel_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    _, _, _, _, _, _, _, request = _fixture_context(fixture)
    instrument = request.instrument
    market_body = build_default_market_data_snapshot_body(
        instrument=instrument,
        orderbook_age_ms="6000",
    )
    contract = _build(
        fixture,
        market_data_snapshot=_rebind(
            market_body,
            f"market-data-snapshot/{instrument}",
            "market_data_snapshot_v1",
        ),
    )
    assert contract["contract_status"] == "INDEPENDENT_PRE_TRADE_SAFETY_KERNEL_REJECTED"
    assert "MARKET_DATA_STALE" in _factor_ids(contract)


def test_clock_untrusted_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    contract = _build(
        produce_independent_pre_trade_safety_kernel_fixture(
            tmp_path, ssot_durable_output_dir, produce_output=False
        ),
        clock_trust_status="UNTRUSTED",
    )
    assert contract["contract_status"] == "INDEPENDENT_PRE_TRADE_SAFETY_KERNEL_BLOCKED"
    assert "CLOCK_UNTRUSTED" in _factor_ids(contract)


def test_mark_index_divergence_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_independent_pre_trade_safety_kernel_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    _, _, _, _, _, _, _, request = _fixture_context(fixture)
    instrument = request.instrument
    market_body = build_default_market_data_snapshot_body(
        instrument=instrument,
        mark_price="100.00",
        index_price="103.00",
    )
    contract = _build(
        fixture,
        market_data_snapshot=_rebind(
            market_body,
            f"market-data-snapshot/{instrument}",
            "market_data_snapshot_v1",
        ),
    )
    assert contract["contract_status"] == "INDEPENDENT_PRE_TRADE_SAFETY_KERNEL_REJECTED"
    assert "MARK_INDEX_DIVERGENCE_EXCEEDED" in _factor_ids(contract)


def test_spread_exceeded_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_independent_pre_trade_safety_kernel_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    _, _, _, _, _, _, _, request = _fixture_context(fixture)
    instrument = request.instrument
    market_body = build_default_market_data_snapshot_body(
        instrument=instrument,
        spread_bps="60",
    )
    contract = _build(
        fixture,
        market_data_snapshot=_rebind(
            market_body,
            f"market-data-snapshot/{instrument}",
            "market_data_snapshot_v1",
        ),
    )
    assert contract["contract_status"] == "INDEPENDENT_PRE_TRADE_SAFETY_KERNEL_REJECTED"
    assert "SPREAD_EXCEEDED" in _factor_ids(contract)


def test_orderbook_depth_insufficient_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_independent_pre_trade_safety_kernel_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    _, _, _, _, _, _, _, request = _fixture_context(fixture)
    instrument = request.instrument
    market_body = build_default_market_data_snapshot_body(
        instrument=instrument,
        orderbook_depth="5",
    )
    contract = _build(
        fixture,
        market_data_snapshot=_rebind(
            market_body,
            f"market-data-snapshot/{instrument}",
            "market_data_snapshot_v1",
        ),
    )
    assert contract["contract_status"] == "INDEPENDENT_PRE_TRADE_SAFETY_KERNEL_REJECTED"
    assert "ORDERBOOK_DEPTH_INSUFFICIENT" in _factor_ids(contract)


def test_market_impact_exceeded_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_independent_pre_trade_safety_kernel_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    _, _, _, _, _, _, _, request = _fixture_context(fixture)
    instrument = request.instrument
    market_body = build_default_market_data_snapshot_body(
        instrument=instrument,
        expected_market_impact_bps="30",
    )
    contract = _build(
        fixture,
        market_data_snapshot=_rebind(
            market_body,
            f"market-data-snapshot/{instrument}",
            "market_data_snapshot_v1",
        ),
    )
    assert contract["contract_status"] == "INDEPENDENT_PRE_TRADE_SAFETY_KERNEL_REJECTED"
    assert "EXPECTED_MARKET_IMPACT_EXCEEDED" in _factor_ids(contract)


def test_signal_expired_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    contract = _build(
        produce_independent_pre_trade_safety_kernel_fixture(
            tmp_path, ssot_durable_output_dir, produce_output=False
        ),
        signal_timestamp="1970-01-01T00:00:00+00:00",
        evaluation_timestamp="1970-01-01T01:00:00+00:00",
    )
    assert contract["contract_status"] == "INDEPENDENT_PRE_TRADE_SAFETY_KERNEL_REJECTED"
    assert "SIGNAL_EXPIRED" in _factor_ids(contract)


def test_duplicate_intent_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_independent_pre_trade_safety_kernel_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    _, _, _, _, _, _, _, request = _fixture_context(fixture)
    instrument = request.instrument
    open_orders_body = build_default_open_orders_snapshot_body(
        instrument=instrument,
        duplicate_intent_detected=True,
    )
    contract = _build(
        fixture,
        open_orders_snapshot=_rebind(
            open_orders_body,
            f"open-orders-snapshot/{instrument}",
            "open_orders_snapshot_v1",
        ),
    )
    assert contract["contract_status"] == "INDEPENDENT_PRE_TRADE_SAFETY_KERNEL_REJECTED"
    assert "DUPLICATE_INTENT_DETECTED" in _factor_ids(contract)


def test_position_limit_exceeded_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_independent_pre_trade_safety_kernel_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    _, _, _, _, _, _, _, request = _fixture_context(fixture)
    instrument = request.instrument
    position_body = build_default_position_snapshot_body(
        instrument=instrument,
        position_quantity="99",
    )
    contract = _build(
        fixture,
        quantity="2.0000",
        position_snapshot=_rebind(
            position_body,
            f"position-snapshot/{instrument}",
            "position_snapshot_v1",
        ),
    )
    assert contract["contract_status"] == "INDEPENDENT_PRE_TRADE_SAFETY_KERNEL_REJECTED"
    assert "POSITION_LIMIT_EXCEEDED" in _factor_ids(contract)


def test_gross_exposure_limit_exceeded_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_independent_pre_trade_safety_kernel_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    _, _, _, _, _, _, _, request = _fixture_context(fixture)
    account = request.account_scope
    risk_body = build_default_risk_snapshot_body(gross_exposure="499")
    contract = _build(
        fixture,
        quantity="2.0000",
        risk_snapshot=_rebind(
            risk_body,
            f"risk-snapshot/{account}",
            "risk_snapshot_v1",
        ),
    )
    assert contract["contract_status"] == "INDEPENDENT_PRE_TRADE_SAFETY_KERNEL_REJECTED"
    assert "GROSS_EXPOSURE_LIMIT_EXCEEDED" in _factor_ids(contract)


def test_order_notional_limit_exceeded_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    contract = _build(
        produce_independent_pre_trade_safety_kernel_fixture(
            tmp_path, ssot_durable_output_dir, produce_output=False
        ),
        quantity="1.0000",
        limit_price="100.00",
    )
    assert contract["contract_status"] == "INDEPENDENT_PRE_TRADE_SAFETY_KERNEL_REJECTED"
    assert "ORDER_NOTIONAL_LIMIT_EXCEEDED" in _factor_ids(contract)


def test_daily_loss_limit_reached_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_independent_pre_trade_safety_kernel_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    _, _, _, _, _, _, _, request = _fixture_context(fixture)
    account = request.account_scope
    risk_body = build_default_risk_snapshot_body(daily_loss="25")
    contract = _build(
        fixture,
        risk_snapshot=_rebind(
            risk_body,
            f"risk-snapshot/{account}",
            "risk_snapshot_v1",
        ),
    )
    assert contract["contract_status"] == "INDEPENDENT_PRE_TRADE_SAFETY_KERNEL_REJECTED"
    assert "DAILY_LOSS_LIMIT_REACHED" in _factor_ids(contract)


def test_leverage_limit_exceeded_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_independent_pre_trade_safety_kernel_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    _, _, _, _, _, _, _, request = _fixture_context(fixture)
    instrument = request.instrument
    position_body = build_default_position_snapshot_body(
        instrument=instrument,
        leverage="6",
    )
    contract = _build(
        fixture,
        position_snapshot=_rebind(
            position_body,
            f"position-snapshot/{instrument}",
            "position_snapshot_v1",
        ),
    )
    assert contract["contract_status"] == "INDEPENDENT_PRE_TRADE_SAFETY_KERNEL_REJECTED"
    assert "LEVERAGE_LIMIT_EXCEEDED" in _factor_ids(contract)


def test_margin_buffer_insufficient_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_independent_pre_trade_safety_kernel_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    _, _, _, _, _, _, _, request = _fixture_context(fixture)
    account = request.account_scope
    margin_body = build_default_margin_snapshot_body(
        available_margin="1",
        margin_used="100",
    )
    contract = _build(
        fixture,
        margin_snapshot=_rebind(
            margin_body,
            f"margin-snapshot/{account}",
            "margin_snapshot_v1",
        ),
    )
    assert contract["contract_status"] == "INDEPENDENT_PRE_TRADE_SAFETY_KERNEL_REJECTED"
    assert "MARGIN_BUFFER_INSUFFICIENT" in _factor_ids(contract)


def test_price_collar_violated_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    contract = _build(
        produce_independent_pre_trade_safety_kernel_fixture(
            tmp_path, ssot_durable_output_dir, produce_output=False
        ),
        limit_price="200.00",
    )
    assert contract["contract_status"] == "INDEPENDENT_PRE_TRADE_SAFETY_KERNEL_REJECTED"
    assert "PRICE_COLLAR_VIOLATED" in _factor_ids(contract)


def test_open_order_limit_exceeded_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_independent_pre_trade_safety_kernel_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    _, _, _, _, _, _, _, request = _fixture_context(fixture)
    instrument = request.instrument
    open_orders_body = build_default_open_orders_snapshot_body(
        instrument=instrument,
        open_order_count="20",
    )
    contract = _build(
        fixture,
        open_orders_snapshot=_rebind(
            open_orders_body,
            f"open-orders-snapshot/{instrument}",
            "open_orders_snapshot_v1",
        ),
    )
    assert contract["contract_status"] == "INDEPENDENT_PRE_TRADE_SAFETY_KERNEL_REJECTED"
    assert "OPEN_ORDER_LIMIT_EXCEEDED" in _factor_ids(contract)


def test_message_rate_limit_exceeded_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_independent_pre_trade_safety_kernel_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    _, _, _, _, _, _, _, request = _fixture_context(fixture)
    account = request.account_scope
    risk_body = build_default_risk_snapshot_body(messages_last_minute="61")
    contract = _build(
        fixture,
        risk_snapshot=_rebind(
            risk_body,
            f"risk-snapshot/{account}",
            "risk_snapshot_v1",
        ),
    )
    assert contract["contract_status"] == "INDEPENDENT_PRE_TRADE_SAFETY_KERNEL_REJECTED"
    assert "MESSAGE_RATE_LIMIT_EXCEEDED" in _factor_ids(contract)


def test_approve_non_authorizing_flags_remain_false(tmp_path, ssot_durable_output_dir) -> None:
    contract = _build(
        produce_independent_pre_trade_safety_kernel_fixture(
            tmp_path, ssot_durable_output_dir, produce_output=False
        )
    )
    assert contract["decision"] == "APPROVE"
    _assert_non_execution(contract)


def test_no_adapter_network_or_runtime_mutation_on_produce(
    tmp_path, ssot_durable_output_dir
) -> None:
    fixture = produce_independent_pre_trade_safety_kernel_fixture(tmp_path, ssot_durable_output_dir)
    assert fixture.independent_pre_trade_safety_kernel_bundle_dir is not None
    payload = read_manifest(fixture.independent_pre_trade_safety_kernel_bundle_dir / ARTIFACT_REL)
    _assert_non_execution(payload)


def test_futures_market_type_accepted(tmp_path, ssot_durable_output_dir) -> None:
    contract = _build(
        produce_independent_pre_trade_safety_kernel_fixture(
            tmp_path,
            ssot_durable_output_dir,
            produce_output=False,
            instrument_type="FUTURES",
        ),
        market_type="FUTURES",
    )
    assert contract["market_type"] == "FUTURES"
    assert contract["contract_status"] == "INDEPENDENT_PRE_TRADE_SAFETY_KERNEL_APPROVED"


def test_spot_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    contract = _build(
        produce_independent_pre_trade_safety_kernel_fixture(
            tmp_path,
            ssot_durable_output_dir,
            produce_output=False,
        ),
        market_type="SPOT",
    )
    assert contract["contract_status"] == "INDEPENDENT_PRE_TRADE_SAFETY_KERNEL_REJECTED"
    assert "MARKET_TYPE_NOT_FUTURES" in _factor_ids(contract)


def test_synthetic_spot_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    contract = _build(
        produce_independent_pre_trade_safety_kernel_fixture(
            tmp_path,
            ssot_durable_output_dir,
            produce_output=False,
        ),
        market_type="SYNTHETIC_SPOT",
    )
    assert contract["contract_status"] == "INDEPENDENT_PRE_TRADE_SAFETY_KERNEL_REJECTED"
    assert "MARKET_TYPE_NOT_FUTURES" in _factor_ids(contract)


def test_unknown_market_type_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    contract = _build(
        produce_independent_pre_trade_safety_kernel_fixture(
            tmp_path, ssot_durable_output_dir, produce_output=False
        ),
        market_type="UNKNOWN_MARKET",
    )
    assert contract["contract_status"] == "INDEPENDENT_PRE_TRADE_SAFETY_KERNEL_REJECTED"
    assert "MARKET_TYPE_NOT_FUTURES" in _factor_ids(contract)


def test_missing_market_type_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    contract = _build(
        produce_independent_pre_trade_safety_kernel_fixture(
            tmp_path, ssot_durable_output_dir, produce_output=False
        ),
        market_type="",
    )
    assert contract["contract_status"] == "INDEPENDENT_PRE_TRADE_SAFETY_KERNEL_REJECTED"
    assert "MISSING_MARKET_TYPE" in _factor_ids(contract)


def test_replay_produces_identical_artifact(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_independent_pre_trade_safety_kernel_fixture(
        tmp_path, ssot_durable_output_dir, produce_output=False
    )
    (
        idempotency,
        reconciliation,
        attestation,
        venue_capability,
        authority_lease,
        clock_trust,
        _trading_session,
        request,
    ) = _fixture_context(fixture)
    inputs = IndependentPreTradeSafetyKernelInputs(
        runtime_state_reconciliation_bundle_dir=fixture.runtime_state_reconciliation_bundle_dir,
        order_intent_idempotency_bundle_dir=fixture.order_intent_idempotency_bundle_dir,
        trading_core_decision_attestation_bundle_dir=(
            fixture.trading_core_decision_attestation_bundle_dir
        ),
        venue_capability_snapshot_bundle_dir=fixture.venue_capability_snapshot_bundle_dir,
        clock_trust_and_expiry_bundle_dir=fixture.clock_trust_and_expiry_bundle_dir,
        authority_lease_bundle_dir=fixture.authority_lease_bundle_dir,
        request=request,
    )
    out_a = _durable_output(tmp_path, "a")
    out_b = _durable_output(tmp_path, "b")
    produce_independent_pre_trade_safety_kernel_v1(inputs=inputs, output_dir=out_a)
    produce_independent_pre_trade_safety_kernel_v1(inputs=inputs, output_dir=out_b)
    assert (out_a / ARTIFACT_REL).read_text() == (out_b / ARTIFACT_REL).read_text()


def test_manifest_and_self_verification(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_independent_pre_trade_safety_kernel_fixture(tmp_path, ssot_durable_output_dir)
    assert fixture.independent_pre_trade_safety_kernel_bundle_dir is not None
    out = fixture.independent_pre_trade_safety_kernel_bundle_dir
    ok, msg = verify_manifest_sha256(out)
    assert ok, msg
    reverify_independent_pre_trade_safety_kernel_v1(output_dir=out)


def test_authority_invariants(tmp_path, ssot_durable_output_dir) -> None:
    fixture = produce_independent_pre_trade_safety_kernel_fixture(tmp_path, ssot_durable_output_dir)
    assert fixture.independent_pre_trade_safety_kernel_bundle_dir is not None
    payload = read_manifest(fixture.independent_pre_trade_safety_kernel_bundle_dir / ARTIFACT_REL)
    assert (
        payload["independent_pre_trade_safety_kernel_authority_invariants"]
        == INDEPENDENT_PRE_TRADE_SAFETY_KERNEL_AUTHORITY_INVARIANTS
    )
    _assert_non_execution(payload)


def test_defer_pending_evidence_refresh(tmp_path, ssot_durable_output_dir) -> None:
    contract = _build(
        produce_independent_pre_trade_safety_kernel_fixture(
            tmp_path, ssot_durable_output_dir, produce_output=False
        ),
        pending_evidence_refresh=True,
    )
    assert contract["decision"] == "DEFER"
    assert contract["contract_status"] == "INDEPENDENT_PRE_TRADE_SAFETY_KERNEL_DEFERRED"
    assert contract["evidence_status"] == "VALID"
    assert "PENDING_EVIDENCE_REFRESH" in contract.get("contract_reason_codes", [])
