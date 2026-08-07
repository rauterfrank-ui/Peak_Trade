"""Tests for CAPABILITY_11_10 Live bounded single-future continuity."""

from __future__ import annotations

import pytest

from src.ops.capability_11_10_live_bounded_single_future_continuity_v1.dependency_and_ownership_v1 import (
    prove_capability_11_1_dependency_retained_v1,
    prove_capability_11_2_dependency_retained_v1,
    prove_capability_11_3_dependency_retained_v1,
    prove_capability_11_4_dependency_retained_v1,
    prove_capability_11_5_dependency_retained_v1,
    prove_capability_11_6_dependency_retained_v1,
    prove_capability_11_7_dependency_retained_v1,
    prove_capability_11_8_dependency_retained_v1,
    prove_capability_11_9_dependency_retained_v1,
    prove_state_ownership_matrix_v1,
)
from src.ops.capability_11_10_live_bounded_single_future_continuity_v1.live_bounded_evidence_ladder_contract_v1 import (
    LiveBoundedEvidenceLadderError,
    build_live_bounded_evidence_ladder_field_record_v1,
    prove_live_bounded_evidence_ladder_contract_v1,
    refuse_live_bounded_evidence_activation_v1,
    refuse_live_fill_observed_overclaim_v1,
    refuse_live_restart_and_beyond_claim_v1,
)
from src.ops.capability_11_10_live_bounded_single_future_continuity_v1.live_bounded_order_lifecycle_continuity_contract_v1 import (
    LiveBoundedOrderLifecycleContinuityError,
    build_live_bounded_order_lifecycle_continuity_record_v1,
    prove_live_bounded_order_lifecycle_continuity_contract_v1,
    refuse_live_bounded_credential_access_v1,
    refuse_live_bounded_network_session_v1,
    refuse_live_bounded_order_lifecycle_activation_v1,
    refuse_live_bounded_order_submit_v1,
)
from src.ops.capability_11_10_live_bounded_single_future_continuity_v1.live_bounded_single_future_continuity_contract_v1 import (
    LiveBoundedSingleFutureContinuityError,
    build_live_bounded_single_future_continuity_record_v1,
    prove_live_bounded_single_future_continuity_contract_v1,
    refuse_cap_11_11_live_autonomous_v1,
    refuse_live_bounded_single_future_activation_v1,
)
from src.ops.capability_11_10_live_bounded_single_future_continuity_v1.reachability_and_parity_v1 import (
    prove_core_logic_parity_v1,
    prove_negative_reachability_v1,
)
from src.ops.capability_11_10_live_bounded_single_future_continuity_v1.verifier_v1 import (
    verify_capability_11_10_v1,
)


def test_live_bounded_single_future_continuity_contract_fail_closed() -> None:
    record = build_live_bounded_single_future_continuity_record_v1()
    assert record.source == "FIXTURE_ONLY"
    assert record.activated is False
    assert record.stage == "LIVE_BOUNDED_SINGLE_FUTURE"
    assert record.position_count_limit == 1
    assert record.single_future_only is True
    with pytest.raises(LiveBoundedSingleFutureContinuityError, match="NON_FIXTURE"):
        build_live_bounded_single_future_continuity_record_v1(source="LIVE_NETWORK")
    with pytest.raises(
        LiveBoundedSingleFutureContinuityError, match="CAPABILITY_11_11_SURFACE_FORBIDDEN"
    ):
        build_live_bounded_single_future_continuity_record_v1(stage="LIVE_BOUNDED_MULTI_SESSION")
    with pytest.raises(
        LiveBoundedSingleFutureContinuityError, match="POSITION_COUNT_LIMIT_FORBIDDEN"
    ):
        build_live_bounded_single_future_continuity_record_v1(position_count_limit=2)
    with pytest.raises(LiveBoundedSingleFutureContinuityError, match="ACTIVATION_FORBIDDEN"):
        refuse_live_bounded_single_future_activation_v1(claimed_action="activate")
    with pytest.raises(
        LiveBoundedSingleFutureContinuityError, match="CAPABILITY_11_11_SURFACE_FORBIDDEN"
    ):
        refuse_cap_11_11_live_autonomous_v1(claimed_surface="LIVE_AUTONOMOUS_SINGLE_FUTURE")
    proof = prove_live_bounded_single_future_continuity_contract_v1()
    assert proof["ok"] is True
    assert proof["LIVE_BOUNDED_SINGLE_FUTURE_CONTINUITY_ACTIVATED"] is False
    assert proof["NO_AUTOMATIC_STAGE_PROMOTION"] is True


def test_live_bounded_order_lifecycle_continuity_contract_fail_closed() -> None:
    record = build_live_bounded_order_lifecycle_continuity_record_v1(
        intent_id="intent-demo",
        order_plan_id="plan-demo",
        client_order_id="pt-coid-demo",
        instrument_id="BTC-USDT-SWAP",
        side="BUY",
        order_type="LIMIT",
        quantity="1",
    )
    assert record.source == "FIXTURE_ONLY"
    assert record.submitted is False
    assert record.execution_performed is False
    assert record.lifecycle_state == "RECONCILED"
    assert record.venue_native_bounded_payload.get("boundedSingleFuture") is True
    assert record.venue_native_bounded_payload.get("submit") is False
    with pytest.raises(LiveBoundedOrderLifecycleContinuityError, match="NON_FIXTURE"):
        build_live_bounded_order_lifecycle_continuity_record_v1(
            intent_id="intent-bad",
            order_plan_id="plan-bad",
            client_order_id="pt-coid-bad",
            instrument_id="BTC-USDT-SWAP",
            side="BUY",
            order_type="LIMIT",
            quantity="1",
            source="LIVE_NETWORK",
        )
    with pytest.raises(LiveBoundedOrderLifecycleContinuityError, match="EXECUTION_MODE_FORBIDDEN"):
        build_live_bounded_order_lifecycle_continuity_record_v1(
            intent_id="intent-live",
            order_plan_id="plan-live",
            client_order_id="pt-coid-live",
            instrument_id="BTC-USDT-SWAP",
            side="BUY",
            order_type="LIMIT",
            quantity="1",
            execution_mode="LIVE",
        )
    with pytest.raises(
        LiveBoundedOrderLifecycleContinuityError, match="AMEND_CANCEL_PENDING_LIFECYCLE_FORBIDDEN"
    ):
        build_live_bounded_order_lifecycle_continuity_record_v1(
            intent_id="intent-amend",
            order_plan_id="plan-amend",
            client_order_id="pt-coid-amend",
            instrument_id="BTC-USDT-SWAP",
            side="BUY",
            order_type="LIMIT",
            quantity="1",
            lifecycle_state="AMEND_PENDING",
        )
    with pytest.raises(
        LiveBoundedOrderLifecycleContinuityError, match="CAPABILITY_11_11_SURFACE_FORBIDDEN"
    ):
        build_live_bounded_order_lifecycle_continuity_record_v1(
            stage="LIVE_BOUNDED_MULTI_SESSION",
            intent_id="intent-multi",
            order_plan_id="plan-multi",
            client_order_id="pt-coid-multi",
            instrument_id="BTC-USDT-SWAP",
            side="BUY",
            order_type="LIMIT",
            quantity="1",
        )
    with pytest.raises(LiveBoundedOrderLifecycleContinuityError, match="ACTIVATION_FORBIDDEN"):
        refuse_live_bounded_order_lifecycle_activation_v1(claimed_action="activate")
    with pytest.raises(LiveBoundedOrderLifecycleContinuityError, match="ORDER_SUBMIT_FORBIDDEN"):
        refuse_live_bounded_order_submit_v1(client_order_id="pt-coid-demo")
    with pytest.raises(LiveBoundedOrderLifecycleContinuityError, match="NETWORK_SESSION_FORBIDDEN"):
        refuse_live_bounded_network_session_v1(session_id="session-demo")
    with pytest.raises(
        LiveBoundedOrderLifecycleContinuityError, match="CREDENTIAL_ACCESS_FORBIDDEN"
    ):
        refuse_live_bounded_credential_access_v1(claimed_action="load_api_key")
    proof = prove_live_bounded_order_lifecycle_continuity_contract_v1()
    assert proof["ok"] is True
    assert proof["LIVE_BOUNDED_ORDER_LIFECYCLE_CONTINUITY_ACTIVATED"] is False


def test_live_bounded_evidence_ladder_no_observed_overclaim() -> None:
    record = build_live_bounded_evidence_ladder_field_record_v1(field_name="LIVE_FILL_OBSERVED")
    assert record.contract_bound is True
    assert record.observed_claimed is False
    assert record.proven_claimed is False
    with pytest.raises(LiveBoundedEvidenceLadderError, match="UNKNOWN_LIVE_EVIDENCE_LADDER"):
        build_live_bounded_evidence_ladder_field_record_v1(field_name="TESTNET_EVIDENCE_VERIFIED")
    with pytest.raises(LiveBoundedEvidenceLadderError, match="OBSERVED_OVERCLAIM_FORBIDDEN"):
        refuse_live_fill_observed_overclaim_v1(field_name="LIVE_FILL_OBSERVED")
    with pytest.raises(LiveBoundedEvidenceLadderError, match="CAPABILITY_11_11_LADDER_CLAIM"):
        refuse_live_restart_and_beyond_claim_v1(field_name="LIVE_RESTART_RECONSTRUCTED")
    with pytest.raises(LiveBoundedEvidenceLadderError, match="ACTIVATION_FORBIDDEN"):
        refuse_live_bounded_evidence_activation_v1(claimed_action="mark_observed")
    proof = prove_live_bounded_evidence_ladder_contract_v1()
    assert proof["ok"] is True
    assert proof["LIVE_FILL_OBSERVED"] is False
    assert proof["LIVE_RESTART_RECONSTRUCTED"] is False
    assert proof["LIVE_BOUNDED_EVIDENCE_LADDER_CONTRACT_ACTIVATED"] is False


def test_capability_11_1_to_11_9_dependencies_retained() -> None:
    dep_11_1 = prove_capability_11_1_dependency_retained_v1()
    dep_11_2 = prove_capability_11_2_dependency_retained_v1()
    dep_11_3 = prove_capability_11_3_dependency_retained_v1()
    dep_11_4 = prove_capability_11_4_dependency_retained_v1()
    dep_11_5 = prove_capability_11_5_dependency_retained_v1()
    dep_11_6 = prove_capability_11_6_dependency_retained_v1()
    dep_11_7 = prove_capability_11_7_dependency_retained_v1()
    dep_11_8 = prove_capability_11_8_dependency_retained_v1()
    dep_11_9 = prove_capability_11_9_dependency_retained_v1()
    assert dep_11_1["ok"] is True
    assert dep_11_2["ok"] is True
    assert dep_11_3["ok"] is True
    assert dep_11_4["ok"] is True
    assert dep_11_5["ok"] is True
    assert dep_11_6["ok"] is True
    assert dep_11_7["ok"] is True
    assert dep_11_8["ok"] is True
    assert dep_11_9["ok"] is True
    assert dep_11_9["CAPABILITY_11_9_NOT_ACTIVATED_RETAINED"] is True


def test_negative_reachability_parity_and_ownership() -> None:
    reach = prove_negative_reachability_v1()
    assert reach["ok"] is True
    assert reach["REAL_EXECUTION_ADAPTER_CONSTRUCTED"] is False
    assert reach["EXCHANGE_ORDER_SUBMIT_REACHABLE"] is False
    assert reach["EXCHANGE_CREDENTIAL_ACCESS_REACHABLE"] is False
    assert reach["NETWORK_SESSION_STARTED"] is False
    assert reach["PRIVATE_NETWORK_SESSION_STARTED"] is False
    assert reach["TESTNET_EXECUTION_REACHABLE"] is False
    assert reach["LIVE_EXECUTION_REACHABLE"] is False
    assert reach["CAPABILITY_11_10_STARTED"] is True
    assert reach["LIVE_BOUNDED_SINGLE_FUTURE_ACTIVATED"] is False
    assert reach["LIVE_FILL_OBSERVED"] is False
    assert reach["CAPABILITY_11_11_STARTED"] is False
    parity = prove_core_logic_parity_v1()
    assert parity["ok"] is True
    assert parity["CORE_LOGIC_CHANGE"] is False
    assert parity["DASHBOARD_AUTHORITY_EFFECT"] == "NONE"
    ownership = prove_state_ownership_matrix_v1()
    assert ownership["ok"] is True
    assert ownership["LIVE_BOUNDED_ORDER_LIFECYCLE_CONTINUITY_OWNER"].endswith(
        "capability_11_10_live_bounded_single_future_continuity_v1"
    )
    matrix_fields = {row["field"] for row in ownership["matrix"]}
    assert "live_bounded_single_future_continuity" in matrix_fields
    assert "live_bounded_order_lifecycle_continuity" in matrix_fields
    assert "live_bounded_evidence_ladder" in matrix_fields


def test_capability_verifier_pass() -> None:
    result = verify_capability_11_10_v1()
    assert result["ok"] is True
    assert result["VERIFIER_RESULT"] == "PASS"
    claims = result["claims"]
    assert claims["CORE_LOGIC_CHANGE"] is False
    assert claims["ACTIVATION_STATE"] == "not_activated"
    assert claims["TESTNET_AUTHORIZED"] is False
    assert claims["LIVE_AUTHORIZED"] is False
    assert claims["EXCHANGE_CREDENTIAL_ACCESS_REACHABLE"] is False
    assert claims["NETWORK_SESSION_STARTED"] is False
    assert claims["PRIVATE_NETWORK_SESSION_STARTED"] is False
    assert claims["LIVE_ORDER_SUBMIT_PERFORMED_IN_CAPABILITY_11_10"] is False
    assert claims["LIVE_ORDER_EXECUTION_PERFORMED_IN_CAPABILITY_11_10"] is False
    assert claims["LIVE_FILL_OBSERVED"] is False
    assert claims["CAPABILITY_11_10_STARTED"] is True
    assert claims["CAPABILITY_11_10_LIVE_BOUNDED_SINGLE_FUTURE_STARTED"] is True
    assert claims["LIVE_BOUNDED_SINGLE_FUTURE_ACTIVATED"] is False
    assert claims["LIVE_BOUNDED_SINGLE_FUTURE_CONTINUITY_ACTIVATED"] is False
    assert claims["LIVE_BOUNDED_ORDER_LIFECYCLE_CONTINUITY_ACTIVATED"] is False
    assert claims["CAPABILITY_11_11_STARTED"] is False
    assert claims["DASHBOARD_AUTHORITY_EFFECT"] == "NONE"
    assert claims["CAPABILITY_11_1_DEPENDENCY_SATISFIED"] is True
    assert claims["CAPABILITY_11_2_DEPENDENCY_SATISFIED"] is True
    assert claims["CAPABILITY_11_3_DEPENDENCY_SATISFIED"] is True
    assert claims["CAPABILITY_11_4_DEPENDENCY_SATISFIED"] is True
    assert claims["CAPABILITY_11_5_DEPENDENCY_SATISFIED"] is True
    assert claims["CAPABILITY_11_6_DEPENDENCY_SATISFIED"] is True
    assert claims["CAPABILITY_11_7_DEPENDENCY_SATISFIED"] is True
    assert claims["CAPABILITY_11_8_DEPENDENCY_SATISFIED"] is True
    assert claims["CAPABILITY_11_9_DEPENDENCY_SATISFIED"] is True
    assert claims["LIVE_BOUNDED_SINGLE_FUTURE_CONTINUITY_CONTRACT_BOUND"] is True
    assert claims["LIVE_BOUNDED_ORDER_LIFECYCLE_CONTINUITY_CONTRACT_BOUND"] is True
    assert claims["LIVE_BOUNDED_EVIDENCE_LADDER_CONTRACT_BOUND"] is True
    assert claims["LIVE_BOUNDED_ORDER_LIFECYCLE_CONTINUITY_CONTRACT_ACTIVATED"] is False
