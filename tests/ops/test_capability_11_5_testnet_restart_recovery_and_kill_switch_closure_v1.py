"""Tests for CAPABILITY_11_5 testnet restart, recovery and kill-switch closure."""

from __future__ import annotations

import pytest

from src.ops.capability_11_5_testnet_restart_recovery_and_kill_switch_closure_v1.autonomous_recovery_degradation_contract_v1 import (
    AutonomousRecoveryDegradationError,
    build_operating_state_transition_record_v1,
    prove_autonomous_recovery_degradation_contract_v1,
    refuse_autonomous_recovery_for_forbidden_condition_v1,
    refuse_cap_11_6_long_running_autonomous_testnet_v1,
)
from src.ops.capability_11_5_testnet_restart_recovery_and_kill_switch_closure_v1.dependency_and_ownership_v1 import (
    prove_capability_11_1_dependency_retained_v1,
    prove_capability_11_2_dependency_retained_v1,
    prove_capability_11_3_dependency_retained_v1,
    prove_capability_11_4_dependency_retained_v1,
    prove_state_ownership_matrix_v1,
)
from src.ops.capability_11_5_testnet_restart_recovery_and_kill_switch_closure_v1.kill_switch_and_emergency_control_contract_v1 import (
    KillSwitchEmergencyControlError,
    build_kill_switch_fixture_record_v1,
    prove_kill_switch_and_emergency_control_contract_v1,
    refuse_emergency_command_risk_increase_v1,
    refuse_kill_switch_side_effect_bypass_v1,
    refuse_runtime_kill_switch_clear_v1,
)
from src.ops.capability_11_5_testnet_restart_recovery_and_kill_switch_closure_v1.reachability_and_parity_v1 import (
    prove_core_logic_parity_v1,
    prove_negative_reachability_v1,
)
from src.ops.capability_11_5_testnet_restart_recovery_and_kill_switch_closure_v1.restart_with_open_order_position_contract_v1 import (
    RestartWithOpenOrderPositionError,
    prove_restart_with_open_order_position_contract_v1,
    refuse_restart_network_session_activation_v1,
    refuse_silent_reinitialization_v1,
    run_restart_recovery_fixture_path_v1,
)
from src.ops.capability_11_5_testnet_restart_recovery_and_kill_switch_closure_v1.unknown_submit_reconnect_recovery_contract_v1 import (
    UnknownSubmitReconnectRecoveryError,
    prove_unknown_submit_reconnect_recovery_contract_v1,
    refuse_unknown_submit_blind_retry_v1,
    refuse_unknown_submit_network_reconnect_activation_v1,
    run_unknown_submit_recovery_fixture_path_v1,
)
from src.ops.capability_11_5_testnet_restart_recovery_and_kill_switch_closure_v1.verifier_v1 import (
    verify_capability_11_5_v1,
)


def test_unknown_submit_reconnect_recovery_fixture_paths() -> None:
    for path_name in ("unknown_submit_query_before_retry", "reconnect_after_unknown_submit"):
        record = run_unknown_submit_recovery_fixture_path_v1(path_name=path_name)
        assert record.terminal_state == "EVIDENCED"
        assert record.blind_retry_blocked is True
        assert record.exchange_query_completed is True
        assert record.exchange_submit_performed is False
        assert record.source == "FIXTURE_ONLY"
    with pytest.raises(UnknownSubmitReconnectRecoveryError, match="PATH_FORBIDDEN"):
        run_unknown_submit_recovery_fixture_path_v1(path_name="long_running_autonomous_campaign")
    with pytest.raises(UnknownSubmitReconnectRecoveryError, match="BLIND_RETRY_FORBIDDEN"):
        refuse_unknown_submit_blind_retry_v1(client_order_id="pt-coid-demo")
    with pytest.raises(
        UnknownSubmitReconnectRecoveryError, match="NETWORK_RECONNECT_ACTIVATION_FORBIDDEN"
    ):
        refuse_unknown_submit_network_reconnect_activation_v1(session_id="session-demo")
    proof = prove_unknown_submit_reconnect_recovery_contract_v1()
    assert proof["ok"] is True
    assert proof["TESTNET_UNKNOWN_SUBMIT_RECOVERY_PROVEN"] is False
    assert proof["UNKNOWN_SUBMIT_RECONNECT_RECOVERY_CONTRACT_ACTIVATED"] is False


def test_restart_with_open_order_and_position_fixture_paths() -> None:
    for path_name in ("restart_with_open_order", "restart_with_open_position"):
        record = run_restart_recovery_fixture_path_v1(path_name=path_name)
        assert record.pre_restart_state == "OPEN"
        assert record.terminal_state == "EVIDENCED"
        assert record.reconciliation_before_alpha is True
        assert record.exchange_submit_performed is False
    with pytest.raises(RestartWithOpenOrderPositionError, match="UNKNOWN_RESTART_RECOVERY_PATH"):
        run_restart_recovery_fixture_path_v1(path_name="long_running_autonomous_campaign")
    with pytest.raises(
        RestartWithOpenOrderPositionError, match="RESTART_NETWORK_SESSION_ACTIVATION_FORBIDDEN"
    ):
        refuse_restart_network_session_activation_v1(session_id="session-restart")
    with pytest.raises(
        RestartWithOpenOrderPositionError, match="SILENT_REINITIALIZATION_FORBIDDEN"
    ):
        refuse_silent_reinitialization_v1(claimed_action="reset_to_zero")
    proof = prove_restart_with_open_order_position_contract_v1()
    assert proof["ok"] is True
    assert proof["TESTNET_RESTART_PROVEN"] is False
    assert proof["RESTART_WITH_OPEN_ORDER_POSITION_CONTRACT_ACTIVATED"] is False


def test_kill_switch_and_emergency_control_contract() -> None:
    record = build_kill_switch_fixture_record_v1(command="PERSISTENT_KILL")
    assert record.persisted is True
    assert record.survives_restart is True
    assert record.cleared_by_runtime is False
    assert record.alpha_dependent is False
    with pytest.raises(KillSwitchEmergencyControlError, match="UNKNOWN_EMERGENCY_COMMAND"):
        build_kill_switch_fixture_record_v1(command="ENABLE_LIVE_TRADING")
    with pytest.raises(KillSwitchEmergencyControlError, match="RUNTIME_CLEAR_FORBIDDEN"):
        refuse_runtime_kill_switch_clear_v1(actor="runtime_autonomy")
    with pytest.raises(KillSwitchEmergencyControlError, match="SIDE_EFFECT_BYPASS_FORBIDDEN"):
        refuse_kill_switch_side_effect_bypass_v1(claimed_side_effect="order_submit")
    with pytest.raises(KillSwitchEmergencyControlError, match="RISK_INCREASE_FORBIDDEN"):
        refuse_emergency_command_risk_increase_v1(command="PERSISTENT_KILL")
    proof = prove_kill_switch_and_emergency_control_contract_v1()
    assert proof["ok"] is True
    assert proof["TESTNET_KILL_SWITCH_PROVEN"] is False
    assert proof["KILL_SWITCH_CONTRACT_ACTIVATED"] is False
    assert proof["KILL_SWITCH_CANNOT_BE_CLEARED_BY_RUNTIME"] is True


def test_autonomous_recovery_degradation_and_cap_11_6_refusal() -> None:
    transition = build_operating_state_transition_record_v1(
        from_state="ACTIVE",
        to_state="EXIT_ONLY",
        reason_code="KILL_SWITCH",
        authority_source="owner_emergency_plane",
        persisted_timestamp="2026-08-07T00:00:00Z",
    )
    assert transition.source == "FIXTURE_ONLY"
    with pytest.raises(AutonomousRecoveryDegradationError, match="UNKNOWN_OPERATING_STATE"):
        build_operating_state_transition_record_v1(
            from_state="ACTIVE",
            to_state="UNBOUNDED",
            reason_code="x",
            authority_source="y",
            persisted_timestamp="2026-08-07T00:00:00Z",
        )
    with pytest.raises(AutonomousRecoveryDegradationError, match="REQUIRES_OWNER_LOCKED_OR_HALTED"):
        refuse_autonomous_recovery_for_forbidden_condition_v1(condition="kill_switch_activation")
    with pytest.raises(
        AutonomousRecoveryDegradationError, match="CAPABILITY_11_6_SURFACE_FORBIDDEN"
    ):
        refuse_cap_11_6_long_running_autonomous_testnet_v1(claimed_surface="campaign")
    proof = prove_autonomous_recovery_degradation_contract_v1()
    assert proof["ok"] is True
    assert proof["TESTNET_AUTONOMOUS_RECOVERY_PROVEN"] is False
    assert proof["CAPABILITY_11_6_LONG_RUNNING_AUTONOMOUS_TESTNET_STARTED"] is False


def test_capability_11_1_to_11_4_dependencies_retained() -> None:
    dep_11_1 = prove_capability_11_1_dependency_retained_v1()
    dep_11_2 = prove_capability_11_2_dependency_retained_v1()
    dep_11_3 = prove_capability_11_3_dependency_retained_v1()
    dep_11_4 = prove_capability_11_4_dependency_retained_v1()
    assert dep_11_1["ok"] is True
    assert dep_11_2["ok"] is True
    assert dep_11_3["ok"] is True
    assert dep_11_4["ok"] is True
    assert dep_11_4["CAPABILITY_11_4_NOT_ACTIVATED_RETAINED"] is True


def test_negative_reachability_parity_and_ownership() -> None:
    reach = prove_negative_reachability_v1()
    assert reach["ok"] is True
    assert reach["REAL_EXECUTION_ADAPTER_CONSTRUCTED"] is False
    assert reach["EXCHANGE_ORDER_SUBMIT_REACHABLE"] is False
    assert reach["EXCHANGE_CREDENTIAL_ACCESS_REACHABLE"] is False
    assert reach["NETWORK_SESSION_STARTED"] is False
    assert reach["TESTNET_EXECUTION_REACHABLE"] is False
    assert reach["LIVE_EXECUTION_REACHABLE"] is False
    assert reach["TESTNET_EXECUTION_ADAPTER_ACTIVATED"] is False
    assert reach["CAPABILITY_11_5_RESTART_RECOVERY_KILL_SWITCH_STARTED"] is True
    assert reach["KILL_SWITCH_CONTRACT_ACTIVATED"] is False
    assert reach["CAPABILITY_11_6_LONG_RUNNING_AUTONOMOUS_TESTNET_STARTED"] is False
    parity = prove_core_logic_parity_v1()
    assert parity["ok"] is True
    assert parity["CORE_LOGIC_CHANGE"] is False
    ownership = prove_state_ownership_matrix_v1()
    assert ownership["ok"] is True
    assert ownership["KILL_SWITCH_AND_EMERGENCY_CONTROL_OWNER"].endswith(
        "capability_11_5_testnet_restart_recovery_and_kill_switch_closure_v1"
    )
    matrix_fields = {row["field"] for row in ownership["matrix"]}
    assert "kill_switch_and_emergency_control" in matrix_fields


def test_capability_verifier_pass() -> None:
    result = verify_capability_11_5_v1()
    assert result["ok"] is True
    assert result["VERIFIER_RESULT"] == "PASS"
    claims = result["claims"]
    assert claims["CORE_LOGIC_CHANGE"] is False
    assert claims["ACTIVATION_STATE"] == "not_activated"
    assert claims["TESTNET_AUTHORIZED"] is False
    assert claims["LIVE_AUTHORIZED"] is False
    assert claims["EXCHANGE_CREDENTIAL_ACCESS_REACHABLE"] is False
    assert claims["NETWORK_SESSION_STARTED"] is False
    assert claims["TESTNET_ORDER_SUBMIT_PERFORMED_IN_CAPABILITY_11_5"] is False
    assert claims["TESTNET_RESTART_PROVEN"] is False
    assert claims["TESTNET_UNKNOWN_SUBMIT_RECOVERY_PROVEN"] is False
    assert claims["TESTNET_KILL_SWITCH_PROVEN"] is False
    assert claims["TESTNET_AUTONOMOUS_RECOVERY_PROVEN"] is False
    assert claims["CAPABILITY_11_5_RESTART_RECOVERY_KILL_SWITCH_STARTED"] is True
    assert claims["CAPABILITY_11_6_LONG_RUNNING_AUTONOMOUS_TESTNET_STARTED"] is False
    assert claims["CAPABILITY_11_1_DEPENDENCY_SATISFIED"] is True
    assert claims["CAPABILITY_11_2_DEPENDENCY_SATISFIED"] is True
    assert claims["CAPABILITY_11_3_DEPENDENCY_SATISFIED"] is True
    assert claims["CAPABILITY_11_4_DEPENDENCY_SATISFIED"] is True
    assert claims["UNKNOWN_SUBMIT_RECONNECT_RECOVERY_CONTRACT_BOUND"] is True
    assert claims["RESTART_WITH_OPEN_ORDER_POSITION_CONTRACT_BOUND"] is True
    assert claims["KILL_SWITCH_AND_EMERGENCY_CONTROL_CONTRACT_BOUND"] is True
    assert claims["AUTONOMOUS_RECOVERY_DEGRADATION_CONTRACT_BOUND"] is True
    assert claims["KILL_SWITCH_CONTRACT_ACTIVATED"] is False
