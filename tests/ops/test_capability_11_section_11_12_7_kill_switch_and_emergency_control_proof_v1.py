"""Tests for Cap 11 §11.12.7 kill-switch and emergency control proof."""

from __future__ import annotations

import pytest

from src.ops.capability_11_section_11_12_7_kill_switch_and_emergency_control_proof_v1.constants_v1 import (
    ALLOWED_SECTION_11_12_7_COMMANDS,
    CAPABILITY_11_5_STARTED,
    CAPABILITY_11_13_STARTED,
    KILL_SWITCH_CONTRACT_ACTIVATED,
    LIFECYCLE_NETWORK_EFFECT,
    NETWORK_WRITES_AUTHORIZED,
    ORDER_SEND_DISABLED,
    ORDERS_AUTHORIZED,
    PATH_CLASS,
    SECTION_11_12_8_STARTED,
    TESTNET_KILL_SWITCH_PROVEN,
    TESTNET_ORDER_LIFECYCLE_PROVEN,
    TESTNET_RESTART_PROVEN,
    TESTNET_UNKNOWN_SUBMIT_RECOVERY_PROVEN,
)
from src.ops.capability_11_section_11_12_7_kill_switch_and_emergency_control_proof_v1.section_11_12_7_v1 import (
    Section11127KillSwitchAndEmergencyControlProofError,
    execute_section_11_12_7_kill_switch_and_emergency_control_proof_v1,
    mark_section_11_12_6_predecessor_bound_v1,
    prove_section_11_12_7_kill_switch_and_emergency_control_proof_v1,
    refuse_cap_11_5_adapter_activation_v1,
    refuse_cap_11_13_live_activation_v1,
    refuse_emergency_risk_increase_v1,
    refuse_kill_switch_contract_activation_v1,
    refuse_network_submit_v1,
    refuse_network_write_v1,
    refuse_order_send_v1,
    refuse_runtime_clear_v1,
    refuse_section_11_12_8_v1,
    refuse_side_effect_bypass_v1,
    reuse_cap_11_5_section_11_12_7_kill_switch_command_v1,
)
from src.ops.capability_11_section_11_12_7_kill_switch_and_emergency_control_proof_v1.verifier_v1 import (
    verify_capability_11_section_11_12_7_kill_switch_and_emergency_control_proof_v1,
)

_SHA = "2de0a4973e726f56c74a881f327130cc73706b17"
_CFG = "cfg-" + ("d" * 64)


def _complete_kwargs(**overrides):
    bound, pred_digest = mark_section_11_12_6_predecessor_bound_v1(
        repository_sha=_SHA, config_digest=_CFG
    )
    base = {
        "runtime_mode": "TESTNET",
        "venue": "OKX",
        "account_identity": "acct-uid-demo",
        "instrument_scope": ("BTC-USDT-SWAP",),
        "repository_sha": _SHA,
        "config_digest": _CFG,
        "expected_repository_sha": _SHA,
        "expected_config_digest": _CFG,
        "expected_account_identity": "acct-uid-demo",
        "expected_venue": "OKX",
        "section_11_12_6_predecessor_bound": bound,
        "section_11_12_6_execution_binding_digest": pred_digest,
        "client_order_id_prefix": "pt-coid-section-11-12-7-test",
    }
    base.update(overrides)
    return base


def test_productive_kill_switch_binds_predecessor() -> None:
    record = execute_section_11_12_7_kill_switch_and_emergency_control_proof_v1(
        **_complete_kwargs()
    )
    assert record.kill_switch_and_emergency_control_proof_performed is True
    assert record.cap_11_5_kill_switch_and_emergency_control_contract_reused is True
    assert record.network_effect == "NONE"
    assert record.exchange_submit_performed is False
    assert record.lifecycle_source == "FIXTURE_ONLY"
    assert record.commands_completed == ALLOWED_SECTION_11_12_7_COMMANDS
    assert len(record.command_results) == 6
    assert all(r.network_effect == "NONE" for r in record.command_results)
    assert all(r.exchange_submit_performed is False for r in record.command_results)
    assert all(r.persisted is True for r in record.command_results)
    assert all(r.survives_restart is True for r in record.command_results)
    assert all(r.cleared_by_runtime is False for r in record.command_results)
    assert all(r.alpha_dependent is False for r in record.command_results)
    assert record.path_class == PATH_CLASS
    assert record.order_send_disabled is True
    assert record.orders_authorized is False
    assert record.network_writes_authorized is False
    assert record.network_write_performed is False
    assert record.exchange_order_submit_reachable is False
    assert record.testnet_order_submit_performed is False
    assert record.cap_11_5_adapter_activated is False
    assert record.kill_switch_contract_activated is False
    assert record.section_11_12_8_started is False
    assert record.cap_11_13_started is False
    assert record.testnet_order_lifecycle_proven is False
    assert record.testnet_unknown_submit_recovery_proven is False
    assert record.testnet_restart_proven is False
    assert record.testnet_kill_switch_proven is False
    assert record.reference_only is False
    assert bool(record.execution_binding_digest)
    assert bool(record.section_11_12_6_execution_binding_digest)
    assert ORDER_SEND_DISABLED is True
    assert ORDERS_AUTHORIZED is False
    assert NETWORK_WRITES_AUTHORIZED is False
    assert LIFECYCLE_NETWORK_EFFECT == "NONE"
    assert TESTNET_ORDER_LIFECYCLE_PROVEN is False
    assert TESTNET_UNKNOWN_SUBMIT_RECOVERY_PROVEN is False
    assert TESTNET_RESTART_PROVEN is False
    assert TESTNET_KILL_SWITCH_PROVEN is False
    assert KILL_SWITCH_CONTRACT_ACTIVATED is False


def test_incomplete_preconditions_fail_closed() -> None:
    with pytest.raises(
        Section11127KillSwitchAndEmergencyControlProofError,
        match="SECTION_11_12_7_NOT_ADMISSIBLE",
    ):
        execute_section_11_12_7_kill_switch_and_emergency_control_proof_v1(
            **_complete_kwargs(section_11_12_6_predecessor_bound=False)
        )


def test_order_send_and_network_writes_hard_rejected() -> None:
    with pytest.raises(
        Section11127KillSwitchAndEmergencyControlProofError,
        match="ORDER_SEND_MUST_REMAIN_DISABLED",
    ):
        execute_section_11_12_7_kill_switch_and_emergency_control_proof_v1(
            **_complete_kwargs(order_send_disabled=False)
        )
    with pytest.raises(
        Section11127KillSwitchAndEmergencyControlProofError,
        match="ORDER_SEND_MUST_REMAIN_DISABLED",
    ):
        execute_section_11_12_7_kill_switch_and_emergency_control_proof_v1(
            **_complete_kwargs(orders_authorized=True)
        )
    with pytest.raises(
        Section11127KillSwitchAndEmergencyControlProofError,
        match="NETWORK_WRITES_FORBIDDEN",
    ):
        execute_section_11_12_7_kill_switch_and_emergency_control_proof_v1(
            **_complete_kwargs(network_writes_authorized=True)
        )


def test_cap_11_5_reuse_negatives_and_command_refusal() -> None:
    with pytest.raises(
        Section11127KillSwitchAndEmergencyControlProofError,
        match="SECTION_11_12_7_COMMAND_FORBIDDEN",
    ):
        reuse_cap_11_5_section_11_12_7_kill_switch_command_v1(
            command="long_running_autonomous_campaign"
        )
    with pytest.raises(
        Section11127KillSwitchAndEmergencyControlProofError,
        match="SECTION_11_12_7_COMMAND_FORBIDDEN",
    ):
        reuse_cap_11_5_section_11_12_7_kill_switch_command_v1(command="ENABLE_LIVE_TRADING")
    with pytest.raises(
        Section11127KillSwitchAndEmergencyControlProofError,
        match="SECTION_11_12_7_COMMAND_FORBIDDEN",
    ):
        reuse_cap_11_5_section_11_12_7_kill_switch_command_v1(command="restart_with_open_order")
    for command in ALLOWED_SECTION_11_12_7_COMMANDS:
        life = reuse_cap_11_5_section_11_12_7_kill_switch_command_v1(command=command)
        assert life.command == command
        assert life.persisted is True
        assert life.survives_restart is True
        assert life.cleared_by_runtime is False
        assert life.alpha_dependent is False
        assert life.network_effect == "NONE"
        assert life.exchange_submit_performed is False


def test_downstream_and_activation_refusals() -> None:
    with pytest.raises(
        Section11127KillSwitchAndEmergencyControlProofError, match="ORDER_SEND_FORBIDDEN"
    ):
        refuse_order_send_v1()
    with pytest.raises(
        Section11127KillSwitchAndEmergencyControlProofError, match="NETWORK_WRITE_FORBIDDEN"
    ):
        refuse_network_write_v1(method="POST")
    with pytest.raises(
        Section11127KillSwitchAndEmergencyControlProofError, match="NETWORK_SUBMIT_FORBIDDEN"
    ):
        refuse_network_submit_v1()
    with pytest.raises(
        Section11127KillSwitchAndEmergencyControlProofError,
        match="KILL_SWITCH_RUNTIME_CLEAR_FORBIDDEN",
    ):
        refuse_runtime_clear_v1(actor="runtime_autonomy")
    with pytest.raises(
        Section11127KillSwitchAndEmergencyControlProofError,
        match="KILL_SWITCH_SIDE_EFFECT_BYPASS_FORBIDDEN",
    ):
        refuse_side_effect_bypass_v1(claimed_side_effect="order_submit")
    with pytest.raises(
        Section11127KillSwitchAndEmergencyControlProofError,
        match="EMERGENCY_COMMAND_RISK_INCREASE_FORBIDDEN",
    ):
        refuse_emergency_risk_increase_v1(command="PERSISTENT_KILL")
    with pytest.raises(
        Section11127KillSwitchAndEmergencyControlProofError, match="SECTION_11_12_8"
    ):
        refuse_section_11_12_8_v1(path_name="long_running_autonomous_campaign")
    with pytest.raises(
        Section11127KillSwitchAndEmergencyControlProofError,
        match="CAPABILITY_11_5_TESTNET_ADAPTER_ACTIVATION_FORBIDDEN",
    ):
        refuse_cap_11_5_adapter_activation_v1()
    with pytest.raises(
        Section11127KillSwitchAndEmergencyControlProofError,
        match="KILL_SWITCH_CONTRACT_ACTIVATION_FORBIDDEN",
    ):
        refuse_kill_switch_contract_activation_v1()
    with pytest.raises(
        Section11127KillSwitchAndEmergencyControlProofError,
        match="CAPABILITY_11_13_LIVE_ACTIVATION_FORBIDDEN",
    ):
        refuse_cap_11_13_live_activation_v1()
    assert CAPABILITY_11_5_STARTED is False
    assert SECTION_11_12_8_STARTED is False
    assert CAPABILITY_11_13_STARTED is False
    assert KILL_SWITCH_CONTRACT_ACTIVATED is False
    assert TESTNET_KILL_SWITCH_PROVEN is False


def test_prove_and_verifier_pass() -> None:
    proof = prove_section_11_12_7_kill_switch_and_emergency_control_proof_v1()
    assert proof["ok"] is True
    assert proof["kill_switch_and_emergency_control_proof_performed"] is True
    assert proof["cap_11_5_kill_switch_and_emergency_control_contract_reused"] is True
    assert proof["network_effect"] == "NONE"
    assert proof["exchange_submit_performed"] is False
    assert proof["section_11_12_8_started"] is False
    assert proof["kill_switch_contract_activated"] is False
    assert proof["testnet_kill_switch_proven"] is False
    assert proof["testnet_order_lifecycle_proven"] is False
    assert proof["testnet_unknown_submit_recovery_proven"] is False
    assert proof["testnet_restart_proven"] is False
    assert proof["commands_completed"] == list(ALLOWED_SECTION_11_12_7_COMMANDS)
    verification = verify_capability_11_section_11_12_7_kill_switch_and_emergency_control_proof_v1()
    assert verification["ok"] is True
    assert verification["VERIFIER_RESULT"] == "PASS"
    assert verification["claims"]["ORDER_SEND_DISABLED"] is True
    assert verification["claims"]["ORDERS_AUTHORIZED"] is False
    assert verification["claims"]["NETWORK_WRITES_AUTHORIZED"] is False
    assert verification["claims"]["NETWORK_WRITE_PERFORMED"] is False
    assert verification["claims"]["KILL_SWITCH_AND_EMERGENCY_CONTROL_PROOF_PERFORMED"] is True
    assert verification["claims"]["SECTION_11_12_8_STARTED"] is False
    assert verification["claims"]["CAPABILITY_11_13_STARTED"] is False
    assert verification["claims"]["CAPABILITY_11_5_STARTED"] is False
    assert verification["claims"]["KILL_SWITCH_CONTRACT_ACTIVATED"] is False
    assert verification["claims"]["TESTNET_KILL_SWITCH_PROVEN"] is False
    assert verification["claims"]["TESTNET_ORDER_LIFECYCLE_PROVEN"] is False
    assert verification["claims"]["TESTNET_UNKNOWN_SUBMIT_RECOVERY_PROVEN"] is False
    assert verification["claims"]["TESTNET_RESTART_PROVEN"] is False
    assert verification["claims"]["RUNTIME_CLEAR_BLOCKED"] is True
    assert verification["claims"]["SIDE_EFFECT_BYPASS_BLOCKED"] is True
    assert verification["claims"]["RISK_INCREASE_BLOCKED"] is True
    assert verification["claims"]["KILL_SWITCH_PERSISTED"] is True
    assert verification["claims"]["NETWORK_EFFECT"] == "NONE"
