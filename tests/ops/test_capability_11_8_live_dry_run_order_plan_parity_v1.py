"""Tests for CAPABILITY_11_8 Live dry-run order-plan parity."""

from __future__ import annotations

import pytest

from src.ops.capability_11_8_live_dry_run_order_plan_parity_v1.dependency_and_ownership_v1 import (
    prove_capability_11_1_dependency_retained_v1,
    prove_capability_11_2_dependency_retained_v1,
    prove_capability_11_3_dependency_retained_v1,
    prove_capability_11_4_dependency_retained_v1,
    prove_capability_11_5_dependency_retained_v1,
    prove_capability_11_6_dependency_retained_v1,
    prove_capability_11_7_dependency_retained_v1,
    prove_state_ownership_matrix_v1,
)
from src.ops.capability_11_8_live_dry_run_order_plan_parity_v1.live_dry_run_order_plan_contract_v1 import (
    LiveDryRunOrderPlanError,
    build_live_dry_run_order_plan_record_v1,
    prove_live_dry_run_order_plan_contract_v1,
    refuse_cap_11_9_live_canary_v1,
    refuse_live_dry_run_credential_access_v1,
    refuse_live_dry_run_network_session_v1,
    refuse_live_dry_run_order_plan_activation_v1,
    refuse_live_dry_run_order_submit_v1,
)
from src.ops.capability_11_8_live_dry_run_order_plan_parity_v1.live_order_plan_evidence_ladder_contract_v1 import (
    LiveOrderPlanEvidenceLadderError,
    build_live_order_plan_evidence_ladder_field_record_v1,
    prove_live_order_plan_evidence_ladder_contract_v1,
    refuse_live_order_plan_evidence_activation_v1,
    refuse_live_order_plan_observed_overclaim_v1,
    refuse_live_submit_ack_and_beyond_claim_v1,
)
from src.ops.capability_11_8_live_dry_run_order_plan_parity_v1.live_order_plan_parity_contract_v1 import (
    LiveOrderPlanParityError,
    build_live_order_plan_parity_record_v1,
    prove_live_order_plan_parity_contract_v1,
    refuse_live_order_plan_parity_activation_v1,
)
from src.ops.capability_11_8_live_dry_run_order_plan_parity_v1.reachability_and_parity_v1 import (
    prove_core_logic_parity_v1,
    prove_negative_reachability_v1,
)
from src.ops.capability_11_8_live_dry_run_order_plan_parity_v1.verifier_v1 import (
    verify_capability_11_8_v1,
)


def test_live_dry_run_order_plan_contract_fail_closed() -> None:
    record = build_live_dry_run_order_plan_record_v1(
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
    assert record.venue_native_dry_run_payload.get("dry_run") is True
    assert record.venue_native_dry_run_payload.get("submit") is False
    with pytest.raises(LiveDryRunOrderPlanError, match="NON_FIXTURE"):
        build_live_dry_run_order_plan_record_v1(
            intent_id="intent-bad",
            order_plan_id="plan-bad",
            client_order_id="pt-coid-bad",
            instrument_id="BTC-USDT-SWAP",
            side="BUY",
            order_type="LIMIT",
            quantity="1",
            source="LIVE_NETWORK",
        )
    with pytest.raises(LiveDryRunOrderPlanError, match="EXECUTION_MODE_FORBIDDEN"):
        build_live_dry_run_order_plan_record_v1(
            intent_id="intent-live",
            order_plan_id="plan-live",
            client_order_id="pt-coid-live",
            instrument_id="BTC-USDT-SWAP",
            side="BUY",
            order_type="LIMIT",
            quantity="1",
            execution_mode="LIVE",
        )
    with pytest.raises(LiveDryRunOrderPlanError, match="SUBMIT_LIFECYCLE_FORBIDDEN"):
        build_live_dry_run_order_plan_record_v1(
            intent_id="intent-submit",
            order_plan_id="plan-submit",
            client_order_id="pt-coid-submit",
            instrument_id="BTC-USDT-SWAP",
            side="BUY",
            order_type="LIMIT",
            quantity="1",
            lifecycle_state="SUBMIT_PENDING",
        )
    with pytest.raises(LiveDryRunOrderPlanError, match="CAPABILITY_11_9_SURFACE_FORBIDDEN"):
        build_live_dry_run_order_plan_record_v1(
            stage="LIVE_CANARY_MINIMUM_EXPOSURE",
            intent_id="intent-canary",
            order_plan_id="plan-canary",
            client_order_id="pt-coid-canary",
            instrument_id="BTC-USDT-SWAP",
            side="BUY",
            order_type="LIMIT",
            quantity="1",
        )
    with pytest.raises(LiveDryRunOrderPlanError, match="ACTIVATION_FORBIDDEN"):
        refuse_live_dry_run_order_plan_activation_v1(claimed_action="activate")
    with pytest.raises(LiveDryRunOrderPlanError, match="ORDER_SUBMIT_FORBIDDEN"):
        refuse_live_dry_run_order_submit_v1(client_order_id="pt-coid-demo")
    with pytest.raises(LiveDryRunOrderPlanError, match="NETWORK_SESSION_FORBIDDEN"):
        refuse_live_dry_run_network_session_v1(session_id="session-demo")
    with pytest.raises(LiveDryRunOrderPlanError, match="CREDENTIAL_ACCESS_FORBIDDEN"):
        refuse_live_dry_run_credential_access_v1(claimed_action="load_api_key")
    with pytest.raises(LiveDryRunOrderPlanError, match="CAPABILITY_11_9_SURFACE_FORBIDDEN"):
        refuse_cap_11_9_live_canary_v1(claimed_surface="LIVE_CANARY_MINIMUM_EXPOSURE")
    proof = prove_live_dry_run_order_plan_contract_v1()
    assert proof["ok"] is True
    assert proof["LIVE_DRY_RUN_ORDER_PLAN_ACTIVATED"] is False


def test_live_order_plan_parity_contract_fail_closed() -> None:
    plan = build_live_dry_run_order_plan_record_v1(
        intent_id="intent-parity",
        order_plan_id="plan-parity",
        client_order_id="pt-coid-parity",
        instrument_id="BTC-USDT-SWAP",
        side="BUY",
        order_type="LIMIT",
        quantity="1",
    )
    match = build_live_order_plan_parity_record_v1(plan=plan)
    assert match.parity_pass is True
    mismatch = build_live_order_plan_parity_record_v1(
        plan=plan,
        expected_canonical_digest="0" * 64,
    )
    assert mismatch.parity_pass is False
    assert mismatch.divergence_reason == "CANONICAL_ORDER_PLAN_DIGEST_MISMATCH"
    with pytest.raises(LiveOrderPlanParityError, match="ACTIVATION_FORBIDDEN"):
        refuse_live_order_plan_parity_activation_v1(claimed_action="activate_parity")
    proof = prove_live_order_plan_parity_contract_v1()
    assert proof["ok"] is True
    assert proof["LIVE_ORDER_PLAN_PARITY_ACTIVATED"] is False
    assert proof["NO_AUTOMATIC_STAGE_PROMOTION"] is True


def test_live_order_plan_evidence_ladder_no_observed_overclaim() -> None:
    record = build_live_order_plan_evidence_ladder_field_record_v1(
        field_name="LIVE_ORDER_PLAN_OBSERVED"
    )
    assert record.contract_bound is True
    assert record.observed_claimed is False
    assert record.proven_claimed is False
    with pytest.raises(LiveOrderPlanEvidenceLadderError, match="UNKNOWN_LIVE_EVIDENCE_LADDER"):
        build_live_order_plan_evidence_ladder_field_record_v1(
            field_name="TESTNET_EVIDENCE_VERIFIED"
        )
    with pytest.raises(LiveOrderPlanEvidenceLadderError, match="OBSERVED_OVERCLAIM_FORBIDDEN"):
        refuse_live_order_plan_observed_overclaim_v1(field_name="LIVE_ORDER_PLAN_OBSERVED")
    with pytest.raises(LiveOrderPlanEvidenceLadderError, match="CAPABILITY_11_9_LADDER_CLAIM"):
        refuse_live_submit_ack_and_beyond_claim_v1(field_name="LIVE_SUBMIT_ACK_OBSERVED")
    with pytest.raises(LiveOrderPlanEvidenceLadderError, match="ACTIVATION_FORBIDDEN"):
        refuse_live_order_plan_evidence_activation_v1(claimed_action="mark_observed")
    proof = prove_live_order_plan_evidence_ladder_contract_v1()
    assert proof["ok"] is True
    assert proof["LIVE_ORDER_PLAN_OBSERVED"] is False
    assert proof["LIVE_SUBMIT_ACK_OBSERVED"] is False
    assert proof["LIVE_ORDER_PLAN_EVIDENCE_LADDER_CONTRACT_ACTIVATED"] is False


def test_capability_11_1_to_11_7_dependencies_retained() -> None:
    dep_11_1 = prove_capability_11_1_dependency_retained_v1()
    dep_11_2 = prove_capability_11_2_dependency_retained_v1()
    dep_11_3 = prove_capability_11_3_dependency_retained_v1()
    dep_11_4 = prove_capability_11_4_dependency_retained_v1()
    dep_11_5 = prove_capability_11_5_dependency_retained_v1()
    dep_11_6 = prove_capability_11_6_dependency_retained_v1()
    dep_11_7 = prove_capability_11_7_dependency_retained_v1()
    assert dep_11_1["ok"] is True
    assert dep_11_2["ok"] is True
    assert dep_11_3["ok"] is True
    assert dep_11_4["ok"] is True
    assert dep_11_5["ok"] is True
    assert dep_11_6["ok"] is True
    assert dep_11_7["ok"] is True
    assert dep_11_7["CAPABILITY_11_7_NOT_ACTIVATED_RETAINED"] is True


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
    assert reach["CAPABILITY_11_8_STARTED"] is True
    assert reach["LIVE_DRY_RUN_ORDER_PLAN_ACTIVATED"] is False
    assert reach["LIVE_ORDER_PLAN_OBSERVED"] is False
    assert reach["CAPABILITY_11_9_STARTED"] is False
    parity = prove_core_logic_parity_v1()
    assert parity["ok"] is True
    assert parity["CORE_LOGIC_CHANGE"] is False
    assert parity["DASHBOARD_AUTHORITY_EFFECT"] == "NONE"
    ownership = prove_state_ownership_matrix_v1()
    assert ownership["ok"] is True
    assert ownership["LIVE_DRY_RUN_ORDER_PLAN_OWNER"].endswith(
        "capability_11_8_live_dry_run_order_plan_parity_v1"
    )
    matrix_fields = {row["field"] for row in ownership["matrix"]}
    assert "live_dry_run_order_plan" in matrix_fields
    assert "live_order_plan_parity" in matrix_fields
    assert "live_order_plan_evidence_ladder" in matrix_fields


def test_capability_verifier_pass() -> None:
    result = verify_capability_11_8_v1()
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
    assert claims["LIVE_ORDER_SUBMIT_PERFORMED_IN_CAPABILITY_11_8"] is False
    assert claims["LIVE_ORDER_PLAN_OBSERVED"] is False
    assert claims["CAPABILITY_11_8_STARTED"] is True
    assert claims["CAPABILITY_11_8_LIVE_DRY_RUN_ORDER_PLAN_STARTED"] is True
    assert claims["LIVE_DRY_RUN_ORDER_PLAN_ACTIVATED"] is False
    assert claims["LIVE_ORDER_PLAN_PARITY_ACTIVATED"] is False
    assert claims["CAPABILITY_11_9_STARTED"] is False
    assert claims["DASHBOARD_AUTHORITY_EFFECT"] == "NONE"
    assert claims["CAPABILITY_11_1_DEPENDENCY_SATISFIED"] is True
    assert claims["CAPABILITY_11_2_DEPENDENCY_SATISFIED"] is True
    assert claims["CAPABILITY_11_3_DEPENDENCY_SATISFIED"] is True
    assert claims["CAPABILITY_11_4_DEPENDENCY_SATISFIED"] is True
    assert claims["CAPABILITY_11_5_DEPENDENCY_SATISFIED"] is True
    assert claims["CAPABILITY_11_6_DEPENDENCY_SATISFIED"] is True
    assert claims["CAPABILITY_11_7_DEPENDENCY_SATISFIED"] is True
    assert claims["LIVE_DRY_RUN_ORDER_PLAN_CONTRACT_BOUND"] is True
    assert claims["LIVE_ORDER_PLAN_PARITY_CONTRACT_BOUND"] is True
    assert claims["LIVE_ORDER_PLAN_EVIDENCE_LADDER_CONTRACT_BOUND"] is True
    assert claims["LIVE_DRY_RUN_ORDER_PLAN_CONTRACT_ACTIVATED"] is False
