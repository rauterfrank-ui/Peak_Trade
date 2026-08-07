"""Tests for CAPABILITY_11_11 Live autonomous recovery and degradation evidence."""

from __future__ import annotations

import pytest

from src.ops.capability_11_11_live_autonomous_recovery_and_degradation_evidence_v1.dependency_and_ownership_v1 import (
    prove_capability_11_1_dependency_retained_v1,
    prove_capability_11_10_dependency_retained_v1,
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
from src.ops.capability_11_11_live_autonomous_recovery_and_degradation_evidence_v1.live_autonomous_degradation_contract_v1 import (
    LiveAutonomousDegradationError,
    build_live_operating_state_transition_record_v1,
    prove_live_autonomous_degradation_contract_v1,
    refuse_cap_11_12_live_readiness_v1,
    refuse_live_autonomous_degradation_activation_v1,
    refuse_live_autonomous_degradation_proven_overclaim_v1,
)
from src.ops.capability_11_11_live_autonomous_recovery_and_degradation_evidence_v1.live_autonomous_recovery_contract_v1 import (
    LiveAutonomousRecoveryError,
    build_live_autonomous_recovery_record_v1,
    prove_live_autonomous_recovery_contract_v1,
    refuse_autonomous_recovery_for_forbidden_condition_v1,
    refuse_live_autonomous_recovery_activation_v1,
    refuse_live_autonomous_recovery_credential_access_v1,
    refuse_live_autonomous_recovery_network_session_v1,
    refuse_live_autonomous_recovery_order_submit_v1,
    refuse_live_autonomous_recovery_proven_overclaim_v1,
)
from src.ops.capability_11_11_live_autonomous_recovery_and_degradation_evidence_v1.live_autonomous_recovery_evidence_ladder_contract_v1 import (
    LiveAutonomousRecoveryEvidenceLadderError,
    build_live_autonomous_recovery_evidence_ladder_field_record_v1,
    prove_live_autonomous_recovery_evidence_ladder_contract_v1,
    refuse_live_autonomous_recovery_evidence_activation_v1,
    refuse_live_end_to_end_and_beyond_claim_v1,
    refuse_live_restart_or_recovery_observed_overclaim_v1,
)
from src.ops.capability_11_11_live_autonomous_recovery_and_degradation_evidence_v1.reachability_and_parity_v1 import (
    prove_core_logic_parity_v1,
    prove_negative_reachability_v1,
)
from src.ops.capability_11_11_live_autonomous_recovery_and_degradation_evidence_v1.verifier_v1 import (
    verify_capability_11_11_v1,
)


def test_live_autonomous_degradation_contract_fail_closed() -> None:
    record = build_live_operating_state_transition_record_v1()
    assert record.source == "FIXTURE_ONLY"
    assert record.activated is False
    assert record.proven is False
    assert record.to_state == "DEGRADED_NO_NEW_ENTRY"
    with pytest.raises(LiveAutonomousDegradationError, match="NON_FIXTURE"):
        build_live_operating_state_transition_record_v1(source="LIVE_NETWORK")
    with pytest.raises(LiveAutonomousDegradationError, match="UNKNOWN_OPERATING_STATE"):
        build_live_operating_state_transition_record_v1(to_state="UNBOUNDED_AUTONOMY")
    with pytest.raises(
        LiveAutonomousDegradationError, match="UNKNOWN_OR_FORBIDDEN_LIVE_AUTONOMOUS_STAGE"
    ):
        build_live_operating_state_transition_record_v1(stage="LIVE_BOUNDED_SINGLE_FUTURE")
    with pytest.raises(LiveAutonomousDegradationError, match="ACTIVATION_FORBIDDEN"):
        refuse_live_autonomous_degradation_activation_v1(claimed_action="activate")
    with pytest.raises(LiveAutonomousDegradationError, match="PROVEN_OVERCLAIM_FORBIDDEN"):
        refuse_live_autonomous_degradation_proven_overclaim_v1(
            claimed_field="LIVE_AUTONOMOUS_DEGRADATION_PROVEN"
        )
    with pytest.raises(LiveAutonomousDegradationError, match="CAPABILITY_11_12_SURFACE_FORBIDDEN"):
        refuse_cap_11_12_live_readiness_v1(claimed_surface="FULLY_AUTONOMOUS_LIVE_TRADING_READY")
    proof = prove_live_autonomous_degradation_contract_v1()
    assert proof["ok"] is True
    assert proof["LIVE_AUTONOMOUS_DEGRADATION_ACTIVATED"] is False
    assert proof["LIVE_AUTONOMOUS_DEGRADATION_PROVEN"] is False
    assert proof["NO_AUTOMATIC_STAGE_PROMOTION"] is True


def test_live_autonomous_recovery_contract_fail_closed() -> None:
    record = build_live_autonomous_recovery_record_v1()
    assert record.source == "FIXTURE_ONLY"
    assert record.activated is False
    assert record.proven is False
    assert record.submitted is False
    assert record.root_cause_classified is True
    with pytest.raises(LiveAutonomousRecoveryError, match="NON_FIXTURE"):
        build_live_autonomous_recovery_record_v1(source="LIVE_NETWORK")
    with pytest.raises(LiveAutonomousRecoveryError, match="GATE_NOT_SATISFIED"):
        build_live_autonomous_recovery_record_v1(root_cause_classified=False)
    with pytest.raises(
        LiveAutonomousRecoveryError, match="AUTONOMOUS_RECOVERY_FORBIDDEN_REQUIRES_OWNER_LOCKED"
    ):
        refuse_autonomous_recovery_for_forbidden_condition_v1(condition="kill_switch_activation")
    with pytest.raises(LiveAutonomousRecoveryError, match="ACTIVATION_FORBIDDEN"):
        refuse_live_autonomous_recovery_activation_v1(claimed_action="activate")
    with pytest.raises(LiveAutonomousRecoveryError, match="ORDER_SUBMIT_FORBIDDEN"):
        refuse_live_autonomous_recovery_order_submit_v1(client_order_id="pt-coid-demo")
    with pytest.raises(LiveAutonomousRecoveryError, match="NETWORK_SESSION_FORBIDDEN"):
        refuse_live_autonomous_recovery_network_session_v1(session_id="session-demo")
    with pytest.raises(LiveAutonomousRecoveryError, match="CREDENTIAL_ACCESS_FORBIDDEN"):
        refuse_live_autonomous_recovery_credential_access_v1(claimed_action="load_api_key")
    with pytest.raises(LiveAutonomousRecoveryError, match="PROVEN_OVERCLAIM_FORBIDDEN"):
        refuse_live_autonomous_recovery_proven_overclaim_v1(
            claimed_field="LIVE_AUTONOMOUS_RECOVERY_PROVEN"
        )
    proof = prove_live_autonomous_recovery_contract_v1()
    assert proof["ok"] is True
    assert proof["LIVE_AUTONOMOUS_RECOVERY_ACTIVATED"] is False
    assert proof["LIVE_AUTONOMOUS_RECOVERY_PROVEN"] is False


def test_live_autonomous_recovery_evidence_ladder_no_observed_overclaim() -> None:
    record = build_live_autonomous_recovery_evidence_ladder_field_record_v1(
        field_name="LIVE_AUTONOMOUS_RECOVERY_OBSERVED"
    )
    assert record.contract_bound is True
    assert record.observed_claimed is False
    assert record.proven_claimed is False
    with pytest.raises(LiveAutonomousRecoveryEvidenceLadderError, match="UNKNOWN_LIVE_EVIDENCE"):
        build_live_autonomous_recovery_evidence_ladder_field_record_v1(
            field_name="TESTNET_EVIDENCE_VERIFIED"
        )
    with pytest.raises(
        LiveAutonomousRecoveryEvidenceLadderError, match="OBSERVED_OVERCLAIM_FORBIDDEN"
    ):
        refuse_live_restart_or_recovery_observed_overclaim_v1(
            field_name="LIVE_RESTART_RECONSTRUCTED"
        )
    with pytest.raises(
        LiveAutonomousRecoveryEvidenceLadderError, match="CAPABILITY_11_12_LADDER_CLAIM"
    ):
        refuse_live_end_to_end_and_beyond_claim_v1(field_name="LIVE_END_TO_END_EVIDENCE_PROVEN")
    with pytest.raises(LiveAutonomousRecoveryEvidenceLadderError, match="ACTIVATION_FORBIDDEN"):
        refuse_live_autonomous_recovery_evidence_activation_v1(claimed_action="mark_observed")
    proof = prove_live_autonomous_recovery_evidence_ladder_contract_v1()
    assert proof["ok"] is True
    assert proof["LIVE_RESTART_RECONSTRUCTED"] is False
    assert proof["LIVE_AUTONOMOUS_RECOVERY_OBSERVED"] is False
    assert proof["LIVE_END_TO_END_EVIDENCE_PROVEN"] is False
    assert proof["LIVE_AUTONOMOUS_RECOVERY_EVIDENCE_LADDER_CONTRACT_ACTIVATED"] is False


def test_capability_11_1_to_11_10_dependencies_retained() -> None:
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
    assert dep_11_10["CAPABILITY_11_10_NOT_ACTIVATED_RETAINED"] is True


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
    assert reach["CAPABILITY_11_11_STARTED"] is True
    assert reach["LIVE_AUTONOMOUS_DEGRADATION_ACTIVATED"] is False
    assert reach["LIVE_AUTONOMOUS_RECOVERY_ACTIVATED"] is False
    assert reach["LIVE_RESTART_RECONSTRUCTED"] is False
    assert reach["LIVE_AUTONOMOUS_RECOVERY_OBSERVED"] is False
    assert reach["CAPABILITY_11_12_STARTED"] is False
    parity = prove_core_logic_parity_v1()
    assert parity["ok"] is True
    assert parity["CORE_LOGIC_CHANGE"] is False
    assert parity["DASHBOARD_AUTHORITY_EFFECT"] == "NONE"
    ownership = prove_state_ownership_matrix_v1()
    assert ownership["ok"] is True
    assert ownership["LIVE_AUTONOMOUS_RECOVERY_OWNER"].endswith(
        "capability_11_11_live_autonomous_recovery_and_degradation_evidence_v1"
    )
    matrix_fields = {row["field"] for row in ownership["matrix"]}
    assert "live_autonomous_degradation" in matrix_fields
    assert "live_autonomous_recovery" in matrix_fields
    assert "live_autonomous_recovery_evidence_ladder" in matrix_fields


def test_capability_verifier_pass() -> None:
    result = verify_capability_11_11_v1()
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
    assert claims["LIVE_ORDER_SUBMIT_PERFORMED_IN_CAPABILITY_11_11"] is False
    assert claims["LIVE_ORDER_EXECUTION_PERFORMED_IN_CAPABILITY_11_11"] is False
    assert claims["LIVE_RESTART_RECONSTRUCTED"] is False
    assert claims["LIVE_AUTONOMOUS_RECOVERY_OBSERVED"] is False
    assert claims["CAPABILITY_11_11_STARTED"] is True
    assert claims["CAPABILITY_11_11_LIVE_AUTONOMOUS_RECOVERY_STARTED"] is True
    assert claims["LIVE_AUTONOMOUS_DEGRADATION_ACTIVATED"] is False
    assert claims["LIVE_AUTONOMOUS_RECOVERY_ACTIVATED"] is False
    assert claims["CAPABILITY_11_12_STARTED"] is False
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
    assert claims["LIVE_AUTONOMOUS_DEGRADATION_CONTRACT_BOUND"] is True
    assert claims["LIVE_AUTONOMOUS_RECOVERY_CONTRACT_BOUND"] is True
    assert claims["LIVE_AUTONOMOUS_RECOVERY_EVIDENCE_LADDER_CONTRACT_BOUND"] is True
    assert claims["LIVE_AUTONOMOUS_RECOVERY_CONTRACT_ACTIVATED"] is False
