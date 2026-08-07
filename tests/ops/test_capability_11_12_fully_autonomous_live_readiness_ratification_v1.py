"""Tests for CAPABILITY_11_12 Fully autonomous Live readiness ratification."""

from __future__ import annotations

import pytest

from src.ops.capability_11_12_fully_autonomous_live_readiness_ratification_v1.autonomy_closure_standard_field_contract_v1 import (
    AutonomyClosureStandardFieldError,
    build_autonomy_closure_standard_field_record_v1,
    prove_autonomy_closure_standard_field_contract_v1,
    refuse_autonomy_closure_field_activation_v1,
    refuse_autonomy_closure_proven_overclaim_v1,
)
from src.ops.capability_11_12_fully_autonomous_live_readiness_ratification_v1.constants_v1 import (
    AUTONOMY_CLOSURE_REQUIRED_FALSE_FIELDS,
    AUTONOMY_CLOSURE_REQUIRED_TRUE_FIELDS,
)
from src.ops.capability_11_12_fully_autonomous_live_readiness_ratification_v1.dependency_and_ownership_v1 import (
    prove_capability_11_1_dependency_retained_v1,
    prove_capability_11_10_dependency_retained_v1,
    prove_capability_11_11_dependency_retained_v1,
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
from src.ops.capability_11_12_fully_autonomous_live_readiness_ratification_v1.fully_autonomous_live_readiness_ratification_contract_v1 import (
    FullyAutonomousLiveReadinessRatificationError,
    build_fully_autonomous_live_readiness_ratification_record_v1,
    evaluate_fully_autonomous_live_readiness_v1,
    prove_fully_autonomous_live_readiness_ratification_contract_v1,
    refuse_cap_11_13_live_activation_v1,
    refuse_fully_autonomous_live_trading_active_v1,
    refuse_fully_autonomous_live_trading_ready_overclaim_v1,
    refuse_live_readiness_credential_access_v1,
    refuse_live_readiness_network_session_v1,
    refuse_live_readiness_order_submit_v1,
    refuse_live_readiness_ratification_activation_v1,
)
from src.ops.capability_11_12_fully_autonomous_live_readiness_ratification_v1.reachability_and_parity_v1 import (
    prove_core_logic_parity_v1,
    prove_negative_reachability_v1,
)
from src.ops.capability_11_12_fully_autonomous_live_readiness_ratification_v1.verifier_v1 import (
    verify_capability_11_12_v1,
)


def test_autonomy_closure_standard_field_contract_fail_closed() -> None:
    record = build_autonomy_closure_standard_field_record_v1(
        field_name="LIVE_ORDER_LIFECYCLE_PROVEN"
    )
    assert record.source == "FIXTURE_ONLY"
    assert record.contract_bound is True
    assert record.proven_claimed is False
    assert record.current_value is False
    with pytest.raises(AutonomyClosureStandardFieldError, match="UNKNOWN_AUTONOMY_CLOSURE_FIELD"):
        build_autonomy_closure_standard_field_record_v1(
            field_name="LIVE_END_TO_END_EVIDENCE_PROVEN"
        )
    with pytest.raises(AutonomyClosureStandardFieldError, match="PROVEN_OVERCLAIM_FORBIDDEN"):
        refuse_autonomy_closure_proven_overclaim_v1(field_name="LIVE_ORDER_LIFECYCLE_PROVEN")
    with pytest.raises(AutonomyClosureStandardFieldError, match="ACTIVATION_FORBIDDEN"):
        refuse_autonomy_closure_field_activation_v1(claimed_action="mark_proven")
    proof = prove_autonomy_closure_standard_field_contract_v1()
    assert proof["ok"] is True
    assert proof["FULLY_AUTONOMOUS_LIVE_TRADING_READY"] is False
    assert proof["LIVE_ORDER_LIFECYCLE_PROVEN"] is False
    assert proof["OWNER_INTERVENTION_REQUIRED_FOR_ROUTINE_OPERATION"] is True


def test_fully_autonomous_live_readiness_ratification_fail_closed() -> None:
    record = build_fully_autonomous_live_readiness_ratification_record_v1()
    assert record.source == "FIXTURE_ONLY"
    assert record.activated is False
    assert record.readiness_satisfied is False
    assert record.ready_claimed is False
    assert record.active_claimed is False
    with pytest.raises(FullyAutonomousLiveReadinessRatificationError, match="NON_FIXTURE"):
        build_fully_autonomous_live_readiness_ratification_record_v1(source="LIVE_NETWORK")
    with pytest.raises(
        FullyAutonomousLiveReadinessRatificationError, match="READY_OVERCLAIM_FORBIDDEN"
    ):
        build_fully_autonomous_live_readiness_ratification_record_v1(ready_claimed=True)
    with pytest.raises(FullyAutonomousLiveReadinessRatificationError, match="ACTIVE_FORBIDDEN"):
        build_fully_autonomous_live_readiness_ratification_record_v1(active_claimed=True)
    with pytest.raises(
        FullyAutonomousLiveReadinessRatificationError, match="READY_OVERCLAIM_FORBIDDEN"
    ):
        refuse_fully_autonomous_live_trading_ready_overclaim_v1()
    with pytest.raises(
        FullyAutonomousLiveReadinessRatificationError,
        match="CAPABILITY_11_13_ACTIVATION_CLAIM_FORBIDDEN",
    ):
        refuse_fully_autonomous_live_trading_active_v1(
            claimed_field="FULLY_AUTONOMOUS_LIVE_TRADING_ACTIVE"
        )
    with pytest.raises(
        FullyAutonomousLiveReadinessRatificationError, match="CAPABILITY_11_13_SURFACE_FORBIDDEN"
    ):
        refuse_cap_11_13_live_activation_v1(claimed_surface="FULLY_AUTONOMOUS_LIVE_TRADING_ACTIVE")
    with pytest.raises(FullyAutonomousLiveReadinessRatificationError, match="ACTIVATION_FORBIDDEN"):
        refuse_live_readiness_ratification_activation_v1(claimed_action="activate")
    with pytest.raises(
        FullyAutonomousLiveReadinessRatificationError, match="ORDER_SUBMIT_FORBIDDEN"
    ):
        refuse_live_readiness_order_submit_v1(client_order_id="pt-coid-demo")
    with pytest.raises(
        FullyAutonomousLiveReadinessRatificationError, match="NETWORK_SESSION_FORBIDDEN"
    ):
        refuse_live_readiness_network_session_v1(session_id="session-demo")
    with pytest.raises(
        FullyAutonomousLiveReadinessRatificationError, match="CREDENTIAL_ACCESS_FORBIDDEN"
    ):
        refuse_live_readiness_credential_access_v1(claimed_action="load_api_key")

    evaluation = evaluate_fully_autonomous_live_readiness_v1()
    assert evaluation["readiness_satisfied"] is False
    all_green = evaluate_fully_autonomous_live_readiness_v1(
        field_values={
            **{name: True for name in AUTONOMY_CLOSURE_REQUIRED_TRUE_FIELDS},
            **{name: False for name in AUTONOMY_CLOSURE_REQUIRED_FALSE_FIELDS},
        }
    )
    assert all_green["readiness_satisfied"] is True
    green_record = build_fully_autonomous_live_readiness_ratification_record_v1(
        field_values={
            **{name: True for name in AUTONOMY_CLOSURE_REQUIRED_TRUE_FIELDS},
            **{name: False for name in AUTONOMY_CLOSURE_REQUIRED_FALSE_FIELDS},
        },
        ready_claimed=True,
    )
    assert green_record.readiness_satisfied is True
    assert green_record.ready_claimed is True
    assert green_record.activated is False

    proof = prove_fully_autonomous_live_readiness_ratification_contract_v1()
    assert proof["ok"] is True
    assert proof["FULLY_AUTONOMOUS_LIVE_TRADING_READY"] is False
    assert proof["FULLY_AUTONOMOUS_LIVE_TRADING_ACTIVE"] is False
    assert proof["CAPABILITY_11_13_STARTED"] is False


def test_capability_11_1_to_11_11_dependencies_retained() -> None:
    dep_11_1 = prove_capability_11_1_dependency_retained_v1()
    dep_11_2 = prove_capability_11_2_dependency_retained_v1()
    dep_11_3 = prove_capability_11_3_dependency_retained_v1()
    dep_11_4 = prove_capability_11_4_dependency_retained_v1()
    dep_11_5 = prove_capability_11_5_dependency_retained_v1()
    dep_11_6 = prove_capability_11_6_dependency_retained_v1()
    dep_11_7 = prove_capability_11_7_dependency_retained_v1()
    dep_11_8 = prove_capability_11_8_dependency_retained_v1()
    dep_11_9 = prove_capability_11_9_dependency_retained_v1()
    dep_11_10 = prove_capability_11_10_dependency_retained_v1()
    dep_11_11 = prove_capability_11_11_dependency_retained_v1()
    assert dep_11_1["ok"] is True
    assert dep_11_2["ok"] is True
    assert dep_11_3["ok"] is True
    assert dep_11_4["ok"] is True
    assert dep_11_5["ok"] is True
    assert dep_11_6["ok"] is True
    assert dep_11_7["ok"] is True
    assert dep_11_8["ok"] is True
    assert dep_11_9["ok"] is True
    assert dep_11_10["ok"] is True
    assert dep_11_11["ok"] is True
    assert dep_11_11["CAPABILITY_11_11_NOT_ACTIVATED_RETAINED"] is True


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
    assert reach["CAPABILITY_11_12_STARTED"] is True
    assert reach["FULLY_AUTONOMOUS_LIVE_TRADING_READY"] is False
    assert reach["FULLY_AUTONOMOUS_LIVE_TRADING_ACTIVE"] is False
    assert reach["CAPABILITY_11_13_STARTED"] is False
    parity = prove_core_logic_parity_v1()
    assert parity["ok"] is True
    assert parity["CORE_LOGIC_CHANGE"] is False
    assert parity["DASHBOARD_AUTHORITY_EFFECT"] == "NONE"
    ownership = prove_state_ownership_matrix_v1()
    assert ownership["ok"] is True
    assert ownership["FULLY_AUTONOMOUS_LIVE_READINESS_RATIFICATION_OWNER"].endswith(
        "capability_11_12_fully_autonomous_live_readiness_ratification_v1"
    )
    matrix_fields = {row["field"] for row in ownership["matrix"]}
    assert "autonomy_closure_standard_fields" in matrix_fields
    assert "fully_autonomous_live_readiness_ratification" in matrix_fields


def test_capability_verifier_pass() -> None:
    result = verify_capability_11_12_v1()
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
    assert claims["LIVE_ORDER_SUBMIT_PERFORMED_IN_CAPABILITY_11_12"] is False
    assert claims["LIVE_ORDER_EXECUTION_PERFORMED_IN_CAPABILITY_11_12"] is False
    assert claims["FULLY_AUTONOMOUS_LIVE_TRADING_READY"] is False
    assert claims["FULLY_AUTONOMOUS_LIVE_TRADING_ACTIVE"] is False
    assert claims["CAPABILITY_11_12_STARTED"] is True
    assert claims["CAPABILITY_11_12_FULLY_AUTONOMOUS_LIVE_READINESS_STARTED"] is True
    assert claims["CAPABILITY_11_13_STARTED"] is False
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
    assert claims["CAPABILITY_11_10_DEPENDENCY_SATISFIED"] is True
    assert claims["CAPABILITY_11_11_DEPENDENCY_SATISFIED"] is True
    assert claims["AUTONOMY_CLOSURE_STANDARD_FIELD_CONTRACT_BOUND"] is True
    assert claims["FULLY_AUTONOMOUS_LIVE_READINESS_RATIFICATION_CONTRACT_BOUND"] is True
    assert claims["FULLY_AUTONOMOUS_LIVE_READINESS_RATIFICATION_CONTRACT_ACTIVATED"] is False
